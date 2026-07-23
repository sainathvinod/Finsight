# Implements: FR-005/006, FR-001/003/010, FR-007, FR-026, FR-084..089, NFR-005/006/019/057/062, F-02-02
from __future__ import annotations
from typing import Dict, Any, Optional
from finsight.domain.review_cycle import ReviewCycle, CycleState
from finsight.application import intake as INTAKE

# Ordered cycle states (index used only for resume gating; not a new state model - ADR-006)
ORDER = [CycleState.CREATED, CycleState.INTAKE, CycleState.PROCESSED, CycleState.VERIFIED,
         CycleState.ANALYZED, CycleState.SUMMARIZED, CycleState.EXPORTED]

def _idx(state: CycleState) -> int:
    return ORDER.index(state)

class Orchestrator:
    def __init__(self, cycle_repo, ingested_repo, run_repo, finding_repo, audit, uow, hasher,
                 pipeline, verification, analysis, reporting, export, clock, actor="local-user"):
        self.cycle_repo = cycle_repo; self.ingested_repo = ingested_repo; self.run_repo = run_repo
        self.finding_repo = finding_repo; self.audit = audit; self.uow = uow; self.hasher = hasher
        self.pipeline = pipeline; self.verification = verification; self.analysis = analysis
        self.reporting = reporting; self.export = export; self.clock = clock; self.actor = actor

    # ---- public entry points ----
    def run_review(self, cycle_id, month, year, ged_path, budget_path, approve=True) -> Dict[str, Any]:
        cycle = ReviewCycle(cycle_id, month, year, CycleState.CREATED)
        with self.uow.atomic():                                   # setup transition (atomic)
            self.cycle_repo.save(cycle)
            self._audit(cycle_id, "setup", {"month": month, "year": year})
        ctx = self._prepare(cycle, ged_path, budget_path, approve)
        self._drive(cycle, ctx)
        return self._result(cycle, ctx)

    def resume(self, cycle_id, ged_path, budget_path, approve=True) -> Dict[str, Any]:
        cycle = self.cycle_repo.get(cycle_id)
        if cycle is None:
            raise LookupError("No persisted cycle to resume: " + cycle_id)
        with self.uow.atomic():
            self._audit(cycle_id, "resume", {"from_state": cycle.state.value})
        ctx = self._prepare(cycle, ged_path, budget_path, approve)  # deterministic recompute (no writes)
        self._drive(cycle, ctx)
        return self._result(cycle, ctx)

    # ---- deterministic recompute (pure: no DB writes, no audit) ----
    def _prepare(self, cycle, ged_path, budget_path, approve) -> Dict[str, Any]:
        provenance, missing = INTAKE.build_provenance(
            cycle, {"GED": ged_path, "BUDGET": budget_path}, self.hasher, self.clock, self.actor)
        ctx = {"provenance": provenance, "paths": {"GED": ged_path, "BUDGET": budget_path},
               "rejected": None, "extracted": None, "vds": None, "findings": None, "run": None}
        if missing:
            ctx["rejected"] = "Required file(s) missing or unreadable: " + ", ".join(missing) + "."
            ctx["readiness"] = {"Budget Analysis": "Unavailable - " + ctx["rejected"]}
            return ctx
        extracted = self.pipeline.run(ged_path, budget_path)
        ctx["extracted"] = extracted
        ctx["readiness"] = extracted["readiness"]
        if not extracted["available"]:
            ctx["rejected"] = extracted["reason"]
            return ctx
        ctx["vds"] = self.verification.build(cycle.cycle_id, extracted, approved=approve)
        return ctx

    # ---- persist + audit only the not-yet-done transitions, each atomic ----
    def _drive(self, cycle, ctx):
        cid = cycle.cycle_id

        def intake():
            for f in ctx["provenance"]:
                self.ingested_repo.save(f)
            for f in ctx["provenance"]:
                self._audit(cid, "upload_ged" if f.doc_type == "GED" else "upload_budget",
                            {"name": f.name, "fingerprint": f.fingerprint, "period": f.period})
        self._transition(cycle, CycleState.INTAKE, intake)

        def processed():
            self._audit(cid, "validate", {"readiness": ctx["readiness"]})
            ex = ctx["extracted"] or {}
            self._audit(cid, "extract", {"ged_valid": len(ex.get("ged_valid", [])),
                        "quarantined": len(ex.get("ged_quarantined", [])) + len(ex.get("budget_quarantined", [])),
                        "rejected": bool(ctx["rejected"])})
        self._transition(cycle, CycleState.PROCESSED, processed)

        if ctx["rejected"]:
            return  # safe stop: no verification, no rule ever runs (NFR-062/AC-3)

        self._transition(cycle, CycleState.VERIFIED, lambda: self._audit(cid, "verify", {"approved": True}))

        def analyzed():
            findings, run = self.analysis.run(ctx["vds"])   # engine writes findings via command port
            run["cycle_id"] = cid
            self.run_repo.save(run)                          # RuleRun persisted (AC-6)
            self._audit(cid, "analyze", {"run_id": run["run_id"], "config_version": run["config_version"],
                        "input_fingerprint": run["input_fingerprint"]})
            for f in findings:
                self._audit(cid, "finding", {"id": f.id, "account": f.account,
                            "severity": f.severity, "type": f.finding_type})
            ctx["findings"] = findings; ctx["run"] = run
        self._transition(cycle, CycleState.ANALYZED, analyzed)

        def summarized():
            fdicts = self.finding_repo.list(cid)
            run = self.run_repo.get_by_cycle(cid) or {}
            summary = self.reporting.summary(cycle, fdicts, run)
            self._audit(cid, "summarize", {"status": summary["status_label"], "findings": summary["finding_count"]})
            ctx["summary"] = summary
        self._transition(cycle, CycleState.SUMMARIZED, summarized)

        def exported():
            run = self.run_repo.get_by_cycle(cid) or {}
            summary = ctx.get("summary") or self.reporting.summary(cycle, self.finding_repo.list(cid), run)
            export = self.export.build(cycle, summary, run, data_as_of=self.clock.now())
            self._audit(cid, "export", {"period": export["period"]})
            ctx["export"] = export
        self._transition(cycle, CycleState.EXPORTED, exported)

    def _transition(self, cycle, target: CycleState, fn):
        if _idx(cycle.state) >= _idx(target):
            return  # already done in a prior (possibly crashed-then-resumed) run - skip, no duplicate
        with self.uow.atomic():          # all-or-nothing: data + audit + state advance together
            fn()
            cycle.state = target
            self.cycle_repo.save(cycle)

    def _audit(self, cid, action, detail):
        self.audit.emit(cid, action, self.actor, detail)

    def _result(self, cycle, ctx) -> Dict[str, Any]:
        cid = cycle.cycle_id
        run = self.run_repo.get_by_cycle(cid) or {}
        fdicts = self.finding_repo.list(cid)
        summary = ctx.get("summary") or self.reporting.summary(cycle, fdicts, run)
        export = ctx.get("export")
        if export is None and not ctx["rejected"]:
            export = self.export.build(cycle, summary, run, data_as_of=self.clock.now())
        return {"cycle": cycle, "extracted": ctx["extracted"], "provenance": ctx["provenance"],
                "rejected": ctx["rejected"], "readiness": ctx.get("readiness"),
                "findings": ctx.get("findings") or [], "finding_records": fdicts,
                "run": run, "summary": summary, "export": export}
