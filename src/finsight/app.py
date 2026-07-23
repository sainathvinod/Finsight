# Implements: F-02-02 (composition root - wires ports; FindingsCommandPort injected ONLY into the engine)
from __future__ import annotations
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
