# Implements: FR-005/006, FR-001/003/010, FR-007, FR-026, FR-084..089, NFR-005/006/019/057/062, F-02-02
# Batch/convenience façade over the shared TransitionEngine. run_review()/resume() compose the same
# public transition methods that the interactive ReviewWorkflowService uses — one rule set, no dup.
from __future__ import annotations
from typing import Any, Dict
from finsight.domain.review_cycle import ReviewCycle, CycleState
from finsight.application.transition_engine import TransitionEngine


class Orchestrator:
    def __init__(self, cycle_repo, ingested_repo, run_repo, finding_repo, audit, uow, hasher,
                 pipeline, verification, analysis, reporting, export, clock, actor="local-user",
                 source_binding_repo=None, cycle_lifecycle_repo=None, review_generation_repo=None,
                 export_artifact_repo=None, extraction_override_repo=None):
        self._engine = TransitionEngine(cycle_repo, ingested_repo, run_repo, finding_repo, audit, uow,
                                        hasher, pipeline, verification, analysis, reporting, export,
                                        clock, actor, source_binding_repo=source_binding_repo,
                                        cycle_lifecycle_repo=cycle_lifecycle_repo,
                                        review_generation_repo=review_generation_repo,
                                        export_artifact_repo=export_artifact_repo,
                                        extraction_override_repo=extraction_override_repo)

    @property
    def engine(self) -> TransitionEngine:
        return self._engine

    # Proxy `audit` so existing crash-safety tests can replace/intercept the audit collaborator
    # after construction (they do `orch.audit = FaultyAudit(...)`); the engine reads it dynamically.
    @property
    def audit(self):
        return self._engine.audit

    @audit.setter
    def audit(self, value):
        self._engine.audit = value

    def run_review(self, cycle_id, month, year, ged_path, budget_path, approve=True) -> Dict[str, Any]:
        cycle = ReviewCycle(cycle_id, month, year, CycleState.CREATED)
        self._engine.setup(cycle)
        ctx = self._engine.prepare(cycle, ged_path, budget_path, approve)
        self._engine.drive(cycle, ctx)
        return self._engine.result(cycle, ctx)

    def resume(self, cycle_id, ged_path, budget_path, approve=True) -> Dict[str, Any]:
        cycle = self._engine.cycle_repo.get(cycle_id)
        if cycle is None:
            raise LookupError("No persisted cycle to resume: " + cycle_id)
        self._engine.mark_resume(cycle)
        ctx = self._engine.prepare(cycle, ged_path, budget_path, approve)
        self._engine.drive(cycle, ctx)
        return self._engine.result(cycle, ctx)
