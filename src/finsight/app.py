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

_log = get_logger("composition")

CONFIG = {  # synthetic ConfigVersion (values pending OQ-8; DEC-019: configuration, not code)
    "config_version": "cfg-synthetic-1",
    "materiality_pct": 20,
    "severity_bands": {"critical": 50, "high": 30, "medium": 20},
    "period": "",
}


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

    def __getitem__(self, key: str):
        """DEPRECATED string-key access, retained only for backward compatibility with existing
        tests (e.g. container["orch"]). New code must use typed attributes; do not add new callers."""
        if not isinstance(key, str):
            raise TypeError("Container keys are attribute-name strings")
        return getattr(self, key)

    def __contains__(self, key) -> bool:
        return isinstance(key, str) and hasattr(self, key)


def build_app(db_path: str, clock, reader=None) -> Container:
    try:
        dal = Dal(db_path)   # runs versioned migrations on first open
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
                        source_binding_repo=source_binding_repo,
                        cycle_lifecycle_repo=cycle_lifecycle_repo,
                        review_generation_repo=review_generation_repo,
                        export_artifact_repo=export_artifact_repo)
    return Container(dal=dal, uow=uow, orch=orch, cycle_repo=cycle_repo, ingested_repo=ingested_repo,
                     run_repo=run_repo, finding_repo=finding_repo, config_repo=config_repo,
                     audit=audit, config=active, clock=clock, source_binding_repo=source_binding_repo,
                     cycle_lifecycle_repo=cycle_lifecycle_repo)


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


def build_query_services(db_path: str, clock=None) -> "AppServices":
    """Composition root for the desktop UI: wires the read-only query services and the review
    workflow command service (which drives the shared TransitionEngine). A production SystemClock
    is injected here (the domain never reads a wall clock)."""
    from finsight.infrastructure.clock import SystemClock
    from finsight.application.read_models.queries import (
        ReviewQueryService, FindingsQueryService, AuditQueryService, SummaryQueryService)
    from finsight.application.workflow import ReviewWorkflowService
    from finsight.application.reconstruction import ReviewReconstructionService
    from finsight.application.abandonment import AbandonmentService
    from finsight.infrastructure.lifecycle_repositories import ReviewGenerationRepoSqlite
    container = build_app(db_path, clock or SystemClock())
    reporting = ReportingService()
    return AppServices(
        reviews=ReviewQueryService(container.cycle_repo, container.finding_repo),
        findings=FindingsQueryService(container.finding_repo),
        audit=AuditQueryService(container.audit),
        summary=SummaryQueryService(container.cycle_repo, container.finding_repo, container.run_repo, reporting),
        workflow=ReviewWorkflowService(container.orch.engine),
        recovery=ReviewReconstructionService(container.orch.engine, container.source_binding_repo,
                                             ReviewGenerationRepoSqlite(container.dal)),
        abandonment=AbandonmentService(container.cycle_repo, container.cycle_lifecycle_repo,
                                       container.audit, container.uow, container.clock),
        ai=build_ai_services(container),
    )
