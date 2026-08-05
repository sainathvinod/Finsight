# Implements: F-02-02 (composition root - wires ports; FindingsCommandPort injected ONLY into the engine)
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, TYPE_CHECKING
from finsight.infrastructure.persistence import (Dal, SqliteUnitOfWork, ReviewCycleRepoSqlite,
    IngestedFileRepoSqlite, FindingRepoSqlite, RuleRunRepoSqlite, ConfigRepoSqlite)
from finsight.infrastructure.lifecycle_repositories import (
    SourceBindingRepoSqlite, CycleLifecycleRepoSqlite, ReviewGenerationRepoSqlite,
    ExportArtifactRepoSqlite)
from finsight.infrastructure.audit import AuditStoreSqlite
from finsight.infrastructure.readers import ExcelReader
from finsight.infrastructure.files import FileHasher
from finsight.application.pipeline import ExtractionPipeline
from finsight.application.verification import VerificationService
from finsight.application.analysis import AnalysisService
from finsight.application.reporting import ReportingService
from finsight.application.export import ExportService
from finsight.application.orchestrator import Orchestrator
from finsight.domain.rules import RulesEngine
from finsight.diagnostics import get_logger
from finsight.infrastructure.authorization_source import (
    AuthorizationSourceConfigurationError,
)

if TYPE_CHECKING:  # type-only imports for the service-container annotations (kept lazy at runtime)
    from finsight.application.read_models.queries import (
        ReviewQueryService, FindingsQueryService, AuditQueryService, SummaryQueryService)
    from finsight.application.workflow import ReviewWorkflowService
    from finsight.application.reconstruction import ReviewReconstructionService
    from finsight.application.abandonment import AbandonmentService
    from finsight.application.ai import (
        ConversationService, ReviewMemoryService, PreferencesService, GroundingQueryService)
    from finsight.application.ai.ask_fin import AskFinService
    from finsight.application.ai.contracts import ProviderStatus
    from finsight.infrastructure.ai.repositories import AiInteractionJournalSqlite
    from finsight.application.ai.private_ask_fin import PrivateAskFinService

_log = get_logger("composition")

CONFIG = {  # synthetic ConfigVersion (values pending OQ-8; DEC-019: configuration, not code)
    "config_version": "cfg-synthetic-1",
    "materiality_pct": 20,
    "severity_bands": {"critical": 50, "high": 30, "medium": 20},
    "period": "",
}


def load_private_ask_fin_runtime_settings(*, env=None):
    """Resolve local-only Ask Fin settings at the composition boundary."""

    from finsight.infrastructure.ai.private_config import (
        load_private_ask_fin_settings,
    )

    return load_private_ask_fin_settings(env=env)


@dataclass
class Container:
    """Typed composition container — the discoverable result of build_app(). Attribute access is the
    primary API. Repositories/DAL/UnitOfWork live here for the composition root and the application
    layer only; they are NEVER handed to the UI (the UI receives AppServices)."""
    dal: Any
    uow: Any
    orch: Orchestrator
    cycle_repo: Any
    ingested_repo: Any
    run_repo: Any
    finding_repo: Any
    config_repo: Any
    audit: Any
    config: Dict[str, Any]
    clock: Any
    source_binding_repo: Any = None
    cycle_lifecycle_repo: Any = None
    review_management_repo: Any = None
    source_intake_repo: Any = None
    financial_review_repo: Any = None
    audit_stream: Any = None
    disposal_registry: Any = None
    startup_admission: Any = None

    def __getitem__(self, key: str):
        """DEPRECATED string-key access, retained only for backward compatibility with existing
        tests (e.g. container["orch"]). New code must use typed attributes; do not add new callers."""
        if not isinstance(key, str):
            raise TypeError("Container keys are attribute-name strings")
        return getattr(self, key)

    def __contains__(self, key) -> bool:
        return isinstance(key, str) and hasattr(self, key)


def build_app(
    db_path: str,
    clock,
    reader=None,
    *,
    key_provider=None,
    registry_root=None,
    startup_actor_id="local-user",
    prepared_authorization=None,
) -> Container:
    # AC-07: the external registry is admitted before the protected database is opened. Key
    # material is resolved once, then passed into the DAL without a plaintext fallback.
    import os
    import uuid
    from finsight.infrastructure.secure_store import (
        ResolvedStoreKeyProvider,
        platform_key_provider,
    )
    from finsight.infrastructure.disposal_registry import FilesystemDisposalRegistry

    provider = key_provider or platform_key_provider()
    key_material = provider.load_or_create(db_path)
    registry_path = registry_root or (os.path.abspath(db_path) + ".registry")
    registry = FilesystemDisposalRegistry(
        registry_path,
        protection_key=key_material.registry_key,
        clock=clock,
        id_factory=lambda: uuid.uuid4().hex,
        machine_shared=not key_material.provider.startswith("TEST"),
    )
    if os.path.exists(registry_path):
        startup_admission = registry.admit_startup()
    else:
        startup_admission = registry.create_fresh(key_material.store_id, startup_actor_id)
    if prepared_authorization is not None:
        verified = prepared_authorization.verified
        registry.advance_authorization_manifest_anchor(
            verified.manifest_version,
            verified.snapshot.fingerprint,
            verified.key_id,
            startup_actor_id,
        )
    try:
        dal = Dal(
            db_path,
            key_provider=ResolvedStoreKeyProvider(key_material),
        )   # runs versioned migrations on first open
    except Exception as e:
        _log.error("database initialization/migration failed for %s: %s", db_path,
                   type(e).__name__, exc_info=True)
        raise
    uow = SqliteUnitOfWork(dal)
    cycle_repo = ReviewCycleRepoSqlite(dal)
    ingested_repo = IngestedFileRepoSqlite(dal)
    finding_repo = FindingRepoSqlite(dal)
    run_repo = RuleRunRepoSqlite(dal)
    config_repo = ConfigRepoSqlite(dal)
    source_binding_repo = SourceBindingRepoSqlite(dal)       # Phase 6.4c reconstruction hint + identity
    cycle_lifecycle_repo = CycleLifecycleRepoSqlite(dal)     # intake_stage on the current candidate
    review_generation_repo = ReviewGenerationRepoSqlite(dal)  # Phase 6.4cA: verification basis at VERIFIED
    export_artifact_repo = ExportArtifactRepoSqlite(dal)     # R1-M3: immutable export identity (ADR-015)
    audit = AuditStoreSqlite(dal, clock)
    from finsight.infrastructure.review_management_repository import (
        ReviewManagementRepositorySqlite,
    )
    from finsight.infrastructure.source_intake_repository import (
        SqliteSourceIntakeRepository,
    )
    from finsight.infrastructure.financial_review_repository import (
        FinancialReviewRepositorySqlite,
    )
    from finsight.infrastructure.audit_stream import AuditStreamSqlite

    review_management_repo = ReviewManagementRepositorySqlite(dal)
    source_intake_repo = SqliteSourceIntakeRepository(dal)
    financial_review_repo = FinancialReviewRepositorySqlite(dal)
    audit_stream = AuditStreamSqlite(
        dal,
        key_material.audit_key,
        clock,
        lambda: uuid.uuid4().hex,
        anchor_registry=registry,
        after_commit=uow.after_commit,
    )
    audit_stream.verify_all(reconcile_committed_gap=True)
    hasher = FileHasher()
    reader = reader or ExcelReader()

    # Persist the active ConfigVersion (T-005): versioned, bound to each run via config_version.
    active = config_repo.active()
    if active is None:
        with uow.atomic():
            config_repo.save({**CONFIG, "created_ts": clock.now()})
        active = config_repo.active()
    engine_cfg = {"materiality_pct": active["materiality_pct"],
                  "severity_bands": active["severity_bands"], "period": active["period"]}

    pipeline = ExtractionPipeline(reader)
    verification = VerificationService()
    engine = RulesEngine(add_finding=finding_repo.add, config=engine_cfg)   # command port wired ONLY here
    analysis = AnalysisService(engine, ruleset_version="R1.0", config_version=active["config_version"])
    reporting = ReportingService()
    export = ExportService()
    orch = Orchestrator(cycle_repo, ingested_repo, run_repo, finding_repo, audit, uow, hasher,
                        pipeline, verification, analysis, reporting, export, clock,
                        actor=startup_actor_id,
                        source_binding_repo=source_binding_repo,
                        cycle_lifecycle_repo=cycle_lifecycle_repo,
                        review_generation_repo=review_generation_repo,
                        export_artifact_repo=export_artifact_repo)
    return Container(dal=dal, uow=uow, orch=orch, cycle_repo=cycle_repo, ingested_repo=ingested_repo,
                     run_repo=run_repo, finding_repo=finding_repo, config_repo=config_repo,
                     audit=audit, config=active, clock=clock, source_binding_repo=source_binding_repo,
                     cycle_lifecycle_repo=cycle_lifecycle_repo,
                     review_management_repo=review_management_repo,
                     source_intake_repo=source_intake_repo,
                     financial_review_repo=financial_review_repo,
                     audit_stream=audit_stream,
                     disposal_registry=registry,
                     startup_admission=startup_admission)


@dataclass(frozen=True)
class AiServices:
    """Typed AI Platform services (Phase 4B). Composed explicitly; the deterministic engine does not
    depend on these. No hidden service locator. Repositories remain infrastructure-only and are not
    exposed here (only services + the read-only grounding query + append/read interaction journal)."""
    conversations: "ConversationService"
    memory: "ReviewMemoryService"
    preferences: "PreferencesService"
    grounding: "GroundingQueryService"
    interaction_journal: "AiInteractionJournalSqlite"


@dataclass(frozen=True)
class AppServices:
    """Application services handed to the desktop UI. Read-only query services, the step-oriented
    review workflow command service, and the AI Platform façade. No repositories or storage objects
    are exposed; the UI depends only on these composed services and there is no global service locator."""
    reviews: "ReviewQueryService"
    findings: "FindingsQueryService"
    audit: "AuditQueryService"
    summary: "SummaryQueryService"
    workflow: "ReviewWorkflowService"
    recovery: "ReviewReconstructionService"
    abandonment: "AbandonmentService"
    ai: "AiServices"
    review_management: Any = None
    source_intake: Any = None
    financial_review: Any = None
    rule_management: Any = None
    identity_resolution: Any = None


@dataclass(frozen=True)
class IdentityPreflight:
    """Resolved composition input used to keep an unidentified process away from protected storage."""

    provider: Any
    resolution: Any


def prepare_local_identity() -> IdentityPreflight:
    """Resolve the replaceable local identity adapter without opening review storage."""

    from finsight.infrastructure.identity import DefaultLocalIdentityProvider

    provider = DefaultLocalIdentityProvider()
    return IdentityPreflight(provider=provider, resolution=provider.resolve_current_actor())


def qualified_machine_runtime_paths():
    """Expose approved runtime locations without leaking infrastructure into delivery."""

    from finsight.infrastructure.runtime_paths import machine_runtime_paths

    return machine_runtime_paths()


AuthorizationConfigurationError = AuthorizationSourceConfigurationError


def authorization_configuration_preflight() -> None:
    """Compatibility seam: validate production configuration without opening storage."""

    from finsight.infrastructure.authorization_source import (
        configuration_from_environment,
    )

    configuration_from_environment()


def build_ai_services(container: Container, new_id=None) -> AiServices:
    """Compose the AI Platform services from the shared DAL/UnitOfWork/clock and the deterministic
    read-model query services (grounding). Repositories stay inside this composition; only services
    are returned. Adding AI persistence does not alter the deterministic engine's composition."""
    import uuid
    from finsight.infrastructure.ai.repositories import (
        ConversationRepoSqlite, MessageRepoSqlite, ReviewMemoryRepoSqlite,
        UserPreferencesRepoSqlite, AiInteractionJournalSqlite)
    from finsight.application.ai import (
        ConversationService, ReviewMemoryService, PreferencesService, GroundingQueryService)
    from finsight.application.read_models.queries import (
        ReviewQueryService, FindingsQueryService, AuditQueryService, SummaryQueryService,
        RuleRunQueryService, ProvenanceQueryService)

    nid = new_id or (lambda: uuid.uuid4().hex)
    dal, uow, clock = container.dal, container.uow, container.clock
    journal = AiInteractionJournalSqlite(dal)
    prefs = PreferencesService(UserPreferencesRepoSqlite(dal), journal, uow, clock, nid)
    conversations = ConversationService(ConversationRepoSqlite(dal), MessageRepoSqlite(dal),
                                        journal, prefs, uow, clock, nid)
    memory = ReviewMemoryService(ReviewMemoryRepoSqlite(dal), journal, uow, clock, nid)
    reporting = ReportingService()
    grounding = GroundingQueryService(
        reviews=ReviewQueryService(container.cycle_repo, container.finding_repo),
        findings=FindingsQueryService(container.finding_repo),
        summary=SummaryQueryService(container.cycle_repo, container.finding_repo, container.run_repo, reporting),
        audit=AuditQueryService(container.audit),
        rule_runs=RuleRunQueryService(container.run_repo),
        provenance=ProvenanceQueryService(container.ingested_repo),
    )
    return AiServices(conversations=conversations, memory=memory, preferences=prefs,
                      grounding=grounding, interaction_journal=journal)


@dataclass(frozen=True)
class AiExplanationServices:
    """Typed bundle for the Ask Fin explanation pipeline (Phase 4C.6). Composed explicitly with an
    INJECTED authorization policy — there is no production consent source yet, so this is built only
    where an authorization policy is supplied (never from build_query_services). `provider_status` is
    the bounded startup status used for selection (diagnostics-safe; non-sensitive)."""
    ask_fin: "AskFinService"
    provider_status: "ProviderStatus"


@dataclass(frozen=True)
class PrivateAskFinServices:
    """Stage 2 local-only Ask Fin composition.

    Unlike the preserved legacy explanation pipeline, this service grounds
    exclusively from sealed V2 FinancialReviewService projections.
    """

    ask_fin: "PrivateAskFinService"


def _select_ai_providers(settings, opener):
    """Choose (active, fallback, provider_status) from provider selection. Status needs no database.
    provider=none → Null/Null/provider_disabled; provider=ollama → Ollama when generation-available,
    else Null; fallback is always NullProvider (per-call degrade lives in AiProviderRuntime)."""
    from finsight.application.ai.contracts import ProviderStatus
    from finsight.infrastructure.ai.providers.null import NullProvider
    if settings.provider == "ollama":
        from finsight.infrastructure.ai.providers.ollama import OllamaProvider
        ollama = OllamaProvider(settings.provider_config, status_timeout=settings.status_timeout_seconds,
                                enabled=True, opener=opener)
        status = ollama.status()
        return (ollama if status.generation_available else NullProvider()), NullProvider(), status
    return NullProvider(), NullProvider(), ProviderStatus(True, False, "provider_disabled")


def build_ai_explanation_service(container: Container, ai_services: AiServices, *, authorization,
                                 settings=None, sleeper=None, monotonic=None, opener=None,
                                 new_id=None) -> AiExplanationServices:
    """Wire AskFinService from the existing AI services + deterministic grounding. Provider is chosen
    from FINSIGHT_AI_PROVIDER (none|ollama); authorization is injected and independent of provider
    selection/availability. No provider is constructed inside AskFinService; no service locator."""
    import uuid
    from finsight.application.ai.ask_fin import (
        AskFinService, AiContextSources, AiPipeline, AiOrchestrationInfra)
    from finsight.application.ai.citations import CitationVerifier
    from finsight.application.ai.masking import MaskingService
    from finsight.application.ai.prompt.budget import ContextBudget
    from finsight.application.ai.prompt.builder import PromptBuilder
    from finsight.application.ai.runtime import AiProviderRuntime
    from finsight.application.ai.validation import ResponseValidator
    from finsight.infrastructure.ai.config import load_ai_runtime_settings
    from finsight.infrastructure.timing import RealSleeper, monotonic as real_monotonic

    settings = settings or load_ai_runtime_settings()
    nid = new_id or (lambda: uuid.uuid4().hex)

    # Provider/runtime selection — provider availability and authorization stay independent.
    active, fallback, status = _select_ai_providers(settings, opener)
    runtime = AiProviderRuntime(active, fallback, settings.provider_config)

    ask_fin = AskFinService(
        authorization=authorization,
        context=AiContextSources(grounding=ai_services.grounding, conversations=ai_services.conversations,
                                 memory=ai_services.memory, preferences=ai_services.preferences),
        pipeline=AiPipeline(masking=MaskingService(), prompt_builder=PromptBuilder(ContextBudget()),
                            provider_runtime=runtime,
                            validator=ResponseValidator(settings.validation_limits),
                            verifier=CitationVerifier()),
        infra=AiOrchestrationInfra(journal=ai_services.interaction_journal,
                                   retry_policy=settings.retry_policy,
                                   sleeper=sleeper or RealSleeper(), clock=container.clock, new_id=nid,
                                   monotonic=monotonic or real_monotonic),
    )
    return AiExplanationServices(ask_fin=ask_fin, provider_status=status)


def build_demo_ai_explanation_service(container: Container, ai_services: AiServices, *,
                                      settings=None, opener=None, new_id=None) -> AiExplanationServices:
    """LOCAL/DEMO-ONLY convenience wiring: constructs the fail-closed DevelopmentAiAuthorizationPolicy
    from settings (FINSIGHT_AI_DEMO_AUTHORIZED) and delegates to build_ai_explanation_service. This is
    NOT production consent and is never called by build_query_services — a caller must opt in
    explicitly. Production stays fail-closed unless an authorization policy is supplied directly."""
    from finsight.infrastructure.ai.authorization import DevelopmentAiAuthorizationPolicy
    from finsight.infrastructure.ai.config import load_ai_runtime_settings
    settings = settings or load_ai_runtime_settings()
    authorization = DevelopmentAiAuthorizationPolicy.from_settings(settings)
    return build_ai_explanation_service(container, ai_services, authorization=authorization,
                                        settings=settings, opener=opener, new_id=new_id)


def build_private_ask_fin_service(
    container: Container,
    financial_review,
    *,
    authorization,
    settings=None,
    opener=None,
    active_review_id=None,
    monotonic=None,
    id_factory=None,
) -> PrivateAskFinServices:
    """Compose Stage 2 Ask Fin with local Ollama and the encrypted local audit.

    There is intentionally no provider selector and no fallback.  The private
    settings loader rejects every non-loopback endpoint before a provider is
    constructed.
    """

    from finsight.application.ai.private_ask_fin import PrivateAskFinService
    from finsight.application.ai.private_grounding import (
        V2FinancialGroundingService,
    )
    from finsight.infrastructure.ai.private_audit import (
        PrivateAskFinAuditRepositorySqlite,
    )
    from finsight.infrastructure.ai.private_config import (
        load_private_ask_fin_settings,
    )
    from finsight.infrastructure.ai.providers.ollama import OllamaProvider
    from finsight.infrastructure.timing import monotonic as real_monotonic

    resolved = settings or load_private_ask_fin_settings()
    provider = OllamaProvider(
        resolved.provider_configuration,
        status_timeout=resolved.status_timeout_seconds,
        enabled=True,
        opener=opener,
        forbid_redirects=True,
        private_local=True,
        approved_model_digest=resolved.approved_model_digest,
        approved_model_profile_id=resolved.approved_model_profile_id,
    )
    audit = PrivateAskFinAuditRepositorySqlite(
        container.dal,
        container.uow,
        id_factory=id_factory,
    )
    service = PrivateAskFinService(
        authorization=authorization,
        grounding=V2FinancialGroundingService(financial_review),
        provider=provider,
        provider_configuration=resolved.provider_configuration,
        audit=audit,
        clock=container.clock,
        active_review_id=active_review_id,
        monotonic=monotonic or real_monotonic,
    )
    return PrivateAskFinServices(ask_fin=service)


class WorkerLocalAskFinBackend:
    """Off-UI-thread Ask Fin backend (Phase 4C.7). Each call builds a FRESH Dal — its own SQLite
    connection created ON THE CALLING (worker) thread — plus the demo AI stack over it, runs, and
    CLOSES the connection. This preserves SQLite's default thread affinity: no connection is ever
    shared across threads. WAL (already enabled) lets this coexist with the UI thread's Dal. The
    caller (AppController) runs these via run_async and enforces one active request at a time.

    Provider status needs no database, so it builds only the provider (bounded status timeout)."""

    def __init__(self, db_path: str, *, settings=None, opener=None, clock_factory=None):
        self._db_path = db_path
        self._settings = settings
        self._opener = opener
        self._clock_factory = clock_factory

    def _resolved_settings(self):
        if callable(self._settings):
            return self._settings()
        if self._settings is not None:
            return self._settings
        from finsight.infrastructure.ai.config import load_ai_runtime_settings
        return load_ai_runtime_settings()

    def _clock(self):
        if self._clock_factory is not None:
            return self._clock_factory()
        from finsight.infrastructure.clock import SystemClock
        return SystemClock()

    def provider_status(self):
        """Bounded provider status, DB-free. Runs on the calling (worker) thread."""
        _active, _fallback, status = _select_ai_providers(self._resolved_settings(), self._opener)
        return status

    def explain(self, request):
        """Build a worker-local Dal + demo AI stack on THIS thread, run the full pipeline, close."""
        container = build_app(self._db_path, self._clock())
        try:
            ai = build_ai_services(container)
            explanation = build_demo_ai_explanation_service(
                container, ai, settings=self._resolved_settings(), opener=self._opener)
            return explanation.ask_fin.explain(request)
        finally:
            try:
                container.dal.conn.close()          # close the worker-local connection on its thread
            except Exception:
                pass


def build_ask_fin_backend(db_path: str, *, settings=None, opener=None,
                          clock_factory=None) -> WorkerLocalAskFinBackend:
    """Composition helper: the Ask Fin backend the desktop controller runs off the UI thread."""
    return WorkerLocalAskFinBackend(db_path, settings=settings, opener=opener,
                                    clock_factory=clock_factory)


class _ManagedReviewPrivateAskFinAuthorization:
    """Bind Stage 2 AI reads to the current OS actor and live REVIEW_READ policy."""

    def __init__(self, services):
        self._services = services
        self._actor_id = services.identity_resolution.require_actor().actor_id

    def authorize(self, *, user_id: str, review_id: str) -> None:
        if user_id != self._actor_id:
            raise PermissionError("Ask Fin actor is not authorized.")
        from finsight.domain.identity import Permission

        self._services.review_management.require_permission(
            Permission.REVIEW_READ
        )


class WorkerLocalPrivateAskFinBackend:
    """Worker-safe V2 Ask Fin backend with one fresh encrypted connection per call.

    The desktop may invoke this object off its UI thread.  No SQLite connection
    crosses a thread boundary, and every call closes its connection in ``finally``.
    """

    def __init__(
        self,
        db_path: str,
        *,
        settings=None,
        opener=None,
        clock_factory=None,
        identity_provider=None,
        identity_resolution=None,
        role_assignment_source=None,
        key_provider=None,
        registry_root=None,
        active_review_id=None,
    ):
        self._db_path = db_path
        self._settings = settings
        self._opener = opener
        self._clock_factory = clock_factory
        self._identity_provider = identity_provider
        self._identity_resolution = identity_resolution
        self._role_assignment_source = role_assignment_source
        self._key_provider = key_provider
        self._registry_root = registry_root
        self._active_review_id = active_review_id

    def _resolved_settings(self):
        if self._settings is not None:
            return self._settings
        from finsight.infrastructure.ai.private_config import (
            load_private_ask_fin_settings,
        )

        return load_private_ask_fin_settings()

    def set_settings(self, settings) -> None:
        """Replace the local-only runtime configuration for future calls."""

        self._settings = settings

    def setup_status(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        approved_model_digest: str | None = None,
        installation_available: bool | None = None,
    ):
        """Probe local Ollama setup without opening the financial store."""

        from dataclasses import replace

        from finsight.infrastructure.ai.providers.ollama import OllamaProvider

        settings = self._resolved_settings()
        provider_configuration = settings.provider_configuration
        if base_url is not None or model is not None:
            provider_configuration = replace(
                provider_configuration,
                base_url=(
                    provider_configuration.base_url
                    if base_url is None
                    else base_url
                ),
                model=(
                    provider_configuration.model
                    if model is None
                    else model
                ),
            )
        digest = (
            settings.approved_model_digest
            if approved_model_digest is None
            else approved_model_digest
        )
        return OllamaProvider(
            provider_configuration,
            status_timeout=settings.status_timeout_seconds,
            enabled=True,
            opener=self._opener,
            forbid_redirects=True,
            private_local=True,
            approved_model_digest=digest,
            approved_model_profile_id=settings.approved_model_profile_id,
        ).setup_status(installation_available=installation_available)

    def _clock(self):
        if self._clock_factory is not None:
            return self._clock_factory()
        from finsight.infrastructure.clock import SystemClock

        return SystemClock()

    def _active_scope(self, requested_review_id: str):
        if callable(self._active_review_id):
            return self._active_review_id
        if self._active_review_id is not None:
            return lambda: self._active_review_id
        # A caller that does not maintain a separate active-review pointer is
        # still explicitly scoped by the immutable request review identifier.
        return lambda: requested_review_id

    def provider_status(self):
        """Bounded, database-free status for the loopback Ollama runtime."""

        from finsight.infrastructure.ai.providers.ollama import OllamaProvider

        settings = self._resolved_settings()
        return OllamaProvider(
            settings.provider_configuration,
            status_timeout=settings.status_timeout_seconds,
            enabled=True,
            opener=self._opener,
            forbid_redirects=True,
            private_local=True,
            approved_model_digest=settings.approved_model_digest,
            approved_model_profile_id=settings.approved_model_profile_id,
        ).status()

    def session(self, *, user_id, review_id, context=None):
        return self._with_service(
            review_id,
            lambda service: service.session(
                user_id=user_id,
                review_id=review_id,
                context=context,
            ),
        )

    def ask(self, request):
        return self._with_service(
            request.review_id,
            lambda service: service.ask(request),
        )

    def explain(self, request):
        """Compatibility-friendly name for asynchronous delivery adapters."""

        return self.ask(request)

    def _with_service(self, review_id: str, operation):
        # A pre-resolved actor is the stronger worker-thread identity input.
        # When composition provides both forms, use the immutable resolution
        # rather than asking the provider to resolve the OS account again.
        identity_provider = (
            None
            if self._identity_resolution is not None
            else self._identity_provider
        )
        services = build_query_services(
            self._db_path,
            clock=self._clock(),
            identity_provider=identity_provider,
            identity_resolution=self._identity_resolution,
            role_assignment_source=self._role_assignment_source,
            key_provider=self._key_provider,
            registry_root=self._registry_root,
        )
        dal = services.ai.interaction_journal.dal
        try:
            # The composition root is allowed to recover its own infrastructure
            # collaborators; these are never exposed to the delivery layer.
            local_container = type(
                "_PrivateAskFinLocalContainer",
                (),
                {
                    "dal": dal,
                    "uow": services.financial_review._uow,
                    "clock": services.financial_review._clock,
                },
            )()
            composed = build_private_ask_fin_service(
                local_container,
                services.financial_review,
                authorization=_ManagedReviewPrivateAskFinAuthorization(services),
                settings=self._resolved_settings(),
                opener=self._opener,
                active_review_id=self._active_scope(review_id),
            )
            return operation(composed.ask_fin)
        finally:
            try:
                dal.conn.close()
            except Exception:
                pass


def build_private_ask_fin_backend(
    db_path: str,
    *,
    settings=None,
    opener=None,
    clock_factory=None,
    identity_provider=None,
    identity_resolution=None,
    role_assignment_source=None,
    key_provider=None,
    registry_root=None,
    active_review_id=None,
) -> WorkerLocalPrivateAskFinBackend:
    """Compose the worker-local Stage 2 backend used by desktop delivery."""

    return WorkerLocalPrivateAskFinBackend(
        db_path,
        settings=settings,
        opener=opener,
        clock_factory=clock_factory,
        identity_provider=identity_provider,
        identity_resolution=identity_resolution,
        role_assignment_source=role_assignment_source,
        key_provider=key_provider,
        registry_root=registry_root,
        active_review_id=active_review_id,
    )


def acquire_single_instance(db_path: str):
    """Composition-root helper (ADR-013 §3): acquire the advisory single-instance lock for a database.
    Returns the HELD SingleInstanceLock, or None when another live instance already holds it (the caller
    must then refuse to open the database). Delivery calls this instead of importing infrastructure."""
    from finsight.infrastructure.single_instance import SingleInstanceLock
    lock = SingleInstanceLock(db_path + ".lock")
    return lock if lock.acquire() else None


class _RegistryManifestAnchor:
    def __init__(self, registry):
        self._registry = registry

    def current(self):
        from finsight.infrastructure.authorization_manifest import (
            ManifestVersionRecord,
        )

        value = self._registry.authorization_manifest_anchor()
        return ManifestVersionRecord(*value) if value is not None else None

    def advance(self, value, actor_id: str) -> None:
        self._registry.advance_authorization_manifest_anchor(
            value.version,
            value.fingerprint,
            value.key_id,
            actor_id,
        )


def _load_authorization_source(container, prepared_authorization, actor):
    """Accept the pre-store proof and compose a per-operation reloading source."""

    from finsight.infrastructure.authorization_source import (
        ReloadingSignedRoleAssignmentSource,
    )

    source = ReloadingSignedRoleAssignmentSource(
        configuration=prepared_authorization.configuration,
        repository=container.review_management_repo,
        prepared=prepared_authorization,
        rollback_anchor=_RegistryManifestAnchor(container.disposal_registry),
        audit_stream=container.audit_stream,
    )
    with container.uow.atomic():
        source.accept_prepared(container.clock.now(), actor)
    return source


def build_query_services(
    db_path: str,
    clock=None,
    *,
    identity_provider=None,
    identity_resolution=None,
    role_assignment_source=None,
    key_provider=None,
    registry_root=None,
) -> "AppServices":
    """Composition root for the desktop UI: wires the read-only query services and the review
    workflow command service (which drives the shared TransitionEngine). A production SystemClock
    is injected here (the domain never reads a wall clock)."""
    from finsight.infrastructure.clock import SystemClock
    from finsight.infrastructure.identity import DefaultLocalIdentityProvider, FixedIdentityProvider
    from finsight.application.security import AuthorizationService
    from finsight.application.review_management import ReviewManagementService, _utc_datetime
    from finsight.application.source_intake import SourceIntakeCoordinator
    from finsight.application.financial_review import FinancialReviewService
    from finsight.application.rule_management import RuleManagementService
    from finsight.domain.financial_validation import CoreFinancialValidationEngine
    from finsight.infrastructure.slv001_extractor import Slv001Extractor
    from finsight.application.read_models.queries import (
        ReviewQueryService, FindingsQueryService, AuditQueryService, SummaryQueryService)
    from finsight.application.workflow import ReviewWorkflowService
    from finsight.application.reconstruction import ReviewReconstructionService
    from finsight.application.abandonment import AbandonmentService
    from finsight.infrastructure.lifecycle_repositories import ReviewGenerationRepoSqlite
    effective_clock = clock or SystemClock()
    if identity_provider is not None and identity_resolution is not None:
        raise ValueError("Provide identity_provider or identity_resolution, not both.")
    effective_identity = (
        FixedIdentityProvider(identity_resolution)
        if identity_resolution is not None
        else (identity_provider or DefaultLocalIdentityProvider())
    )
    resolved_identity = effective_identity.resolve_current_actor()
    actor = resolved_identity.require_actor()  # fail closed before registry/store admission
    evaluated_at = _utc_datetime(effective_clock.now())
    prepared_authorization = None
    if role_assignment_source is None:
        from finsight.infrastructure.authorization_source import (
            prepare_authorization_source,
        )

        prepared_authorization = prepare_authorization_source(evaluated_at)
    container = build_app(
        db_path,
        effective_clock,
        key_provider=key_provider,
        registry_root=registry_root,
        startup_actor_id=actor.actor_id,
        prepared_authorization=prepared_authorization,
    )
    assignments = role_assignment_source or _load_authorization_source(
        container,
        prepared_authorization,
        actor,
    )
    slv001 = Slv001Extractor()
    source_intake = SourceIntakeCoordinator(slv001)
    review_management = ReviewManagementService(
        repository=container.review_management_repo,
        audit_stream=container.audit_stream,
        uow=container.uow,
        identity_provider=effective_identity,
        assignment_source=assignments,
        authorization=AuthorizationService(),
        clock=container.clock,
        source_intake_repository=container.source_intake_repo,
        source_intake_coordinator=source_intake,
    )
    reporting = ReportingService()
    financial_engine = CoreFinancialValidationEngine()
    financial_review = FinancialReviewService(
        repository=container.financial_review_repo,
        review_repository=container.review_management_repo,
        source_repository=container.source_intake_repo,
        generation_repository=ReviewGenerationRepoSqlite(container.dal),
        cycle_lifecycle_repository=container.cycle_lifecycle_repo,
        audit_stream=container.audit_stream,
        unit_of_work=container.uow,
        extractor=slv001,
        engine=financial_engine,
        actor=actor,
        clock=container.clock,
        authorizer=review_management.require_permission,
    )
    rule_management = RuleManagementService(
        repository=container.financial_review_repo,
        unit_of_work=container.uow,
        audit_stream=container.audit_stream,
        engine=financial_engine,
        actor=actor,
        clock=container.clock,
        authorizer=review_management.require_permission,
        authorization_executor=review_management.execute_authorized,
    )
    return AppServices(
        reviews=ReviewQueryService(container.cycle_repo, container.finding_repo),
        findings=FindingsQueryService(container.finding_repo),
        audit=AuditQueryService(container.audit),
        summary=SummaryQueryService(container.cycle_repo, container.finding_repo, container.run_repo, reporting),
        workflow=ReviewWorkflowService(container.orch.engine),
        recovery=ReviewReconstructionService(container.orch.engine, container.source_binding_repo,
                                             ReviewGenerationRepoSqlite(container.dal)),
        abandonment=AbandonmentService(container.cycle_repo, container.cycle_lifecycle_repo,
                                       container.audit, container.uow, container.clock,
                                       actor=actor.actor_id),
        ai=build_ai_services(container),
        review_management=review_management,
        source_intake=source_intake,
        financial_review=financial_review,
        rule_management=rule_management,
        identity_resolution=resolved_identity,
    )
