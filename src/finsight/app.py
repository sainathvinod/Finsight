# Implements: F-02-02 (composition root - wires ports; FindingsCommandPort injected ONLY into the engine)
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, TYPE_CHECKING
from finsight.infrastructure.persistence import (Dal, SqliteUnitOfWork, ReviewCycleRepoSqlite,
    IngestedFileRepoSqlite, FindingRepoSqlite, RuleRunRepoSqlite, ConfigRepoSqlite)
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
    from finsight.application.ai import (
        ConversationService, ReviewMemoryService, PreferencesService, GroundingQueryService)
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
                        pipeline, verification, analysis, reporting, export, clock)
    return Container(dal=dal, uow=uow, orch=orch, cycle_repo=cycle_repo, ingested_repo=ingested_repo,
                     run_repo=run_repo, finding_repo=finding_repo, config_repo=config_repo,
                     audit=audit, config=active, clock=clock)


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


def build_query_services(db_path: str, clock=None) -> "AppServices":
    """Composition root for the desktop UI: wires the read-only query services and the review
    workflow command service (which drives the shared TransitionEngine). A production SystemClock
    is injected here (the domain never reads a wall clock)."""
    from finsight.infrastructure.clock import SystemClock
    from finsight.application.read_models.queries import (
        ReviewQueryService, FindingsQueryService, AuditQueryService, SummaryQueryService)
    from finsight.application.workflow import ReviewWorkflowService
    container = build_app(db_path, clock or SystemClock())
    reporting = ReportingService()
    return AppServices(
        reviews=ReviewQueryService(container.cycle_repo, container.finding_repo),
        findings=FindingsQueryService(container.finding_repo),
        audit=AuditQueryService(container.audit),
        summary=SummaryQueryService(container.cycle_repo, container.finding_repo, container.run_repo, reporting),
        workflow=ReviewWorkflowService(container.orch.engine),
        ai=build_ai_services(container),
    )
