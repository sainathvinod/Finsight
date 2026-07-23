# Implements: F-02-02 (composition root - wires ports; FindingsCommandPort injected ONLY into the engine)
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
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

CONFIG = {  # synthetic ConfigVersion (values pending OQ-8; DEC-019: configuration, not code)
    "config_version": "cfg-synthetic-1",
    "materiality_pct": 20,
    "severity_bands": {"critical": 50, "high": 30, "medium": 20},
    "period": "",
}

def build_app(db_path: str, clock, reader=None):
    dal = Dal(db_path)
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
    return {"dal": dal, "uow": uow, "orch": orch, "cycle_repo": cycle_repo, "finding_repo": finding_repo,
            "run_repo": run_repo, "ingested_repo": ingested_repo, "config_repo": config_repo,
            "audit": audit, "config": active}


@dataclass(frozen=True)
class AppServices:
    """Application services handed to the desktop UI. Read-only query services plus the
    step-oriented review workflow command service. No repositories or storage objects are
    exposed; the UI depends only on these composed services and there is no global service
    locator."""
    reviews: "ReviewQueryService"
    findings: "FindingsQueryService"
    audit: "AuditQueryService"
    summary: "SummaryQueryService"
    workflow: "ReviewWorkflowService"


def build_query_services(db_path: str, clock=None) -> "AppServices":
    """Composition root for the desktop UI: wires the read-only query services and the review
    workflow command service. The workflow service drives the same Orchestrator transition logic.
    A production SystemClock is injected here (the domain never reads a wall clock)."""
    from finsight.infrastructure.clock import SystemClock
    from finsight.application.reporting import ReportingService
    from finsight.application.read_models.queries import (
        ReviewQueryService, FindingsQueryService, AuditQueryService, SummaryQueryService)
    from finsight.application.workflow import ReviewWorkflowService
    app = build_app(db_path, clock or SystemClock())
    reporting = ReportingService()
    return AppServices(
        reviews=ReviewQueryService(app["cycle_repo"], app["finding_repo"]),
        findings=FindingsQueryService(app["finding_repo"]),
        audit=AuditQueryService(app["audit"]),
        summary=SummaryQueryService(app["cycle_repo"], app["finding_repo"], app["run_repo"], reporting),
        workflow=ReviewWorkflowService(app["orch"]),
    )
