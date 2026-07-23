# Implements: FR-005/006, FR-001/003/010, FR-007, FR-026, FR-084..089, NFR-005/006/019/057/062, F-02-02
# The single source of review-cycle transition rules: atomic (data + audit + state advancement),
# resume-gated (no-duplicate), rejection safe-stop. Both Orchestrator (batch run_review/resume) and
# ReviewWorkflowService (interactive, step-by-step) drive THESE public methods — neither reaches
# into the other's internals. No UI framework, no PySide6.
from __future__ import annotations
from typing import Any, Dict
from finsight.domain.review_cycle import CycleState, has_reached
from finsight.application import intake as INTAKE
from finsight.diagnostics import get_logger

_log = get_logger("transition")


class TransitionEngine:
    def __init__(self, cycle_repo, ingested_repo, run_repo, finding_repo, audit, uow, hasher,
                 pipeline, verification, analysis, reporting, export, clock, actor="local-user"):
        self.cycle_repo = cycle_repo
        self.ingested_repo = ingested_repo
        self.run_repo = run_repo
        self.finding_repo = finding_repo
        self.audit = audit          # mutable: crash-safety tests replace this to inject a fault
        self.uow = uow
        self.hasher = hasher
        self.pipeline = pipeline
        self.verification = verification
        self.analysis = analysis
        self.reporting = reporting
        self.export = export
        self.clock = clock
        self.actor = actor

    # ---- primitives ----
    def audit_event(self, cycle_id: str, action: str, detail: Dict[str, Any]) -> None:
        self.audit.emit(cycle_id, action, self.actor, detail)

    def transition(self, cycle, target: CycleState, fn) -> None:
        if has_reached(cycle.state, target):
            return  # already done in a prior (possibly crashed-then-resumed) run - skip, no duplicate
        with self.uow.atomic():          # all-or-nothing: data + audit + state advance together
            fn()
            cycle.state = target
            self.cycle_repo.save(cycle)

    def setup(self, cycle) -> None:
        with self.uow.atomic():
            self.cycle_repo.save(cycle)
            self.audit_event(cycle.cycle_id, "setup", {"month": cycle.month, "year": cycle.year})

    def mark_resume(self, cycle) -> None:
        with self.uow.atomic():
            self.audit_event(cycle.cycle_id, "resume", {"from_state": cycle.state.value})

    # ---- deterministic recompute helpers (pure: no DB writes, no audit) ----
    def build_provenance(self, cycle, ged_path, budget_path):
        return INTAKE.build_provenance(
            cycle, {"GED": ged_path, "BUDGET": budget_path}, self.hasher, self.clock, self.actor)

    def extract(self, ged_path, budget_path):
        return self.pipeline.run(ged_path, budget_path)

    def build_verified(self, cycle_id, extracted, approve):
        return self.verification.build(cycle_id, extracted, approved=approve)

    # ---- individual transitions (public; the shared rules) ----
    def do_intake(self, cycle, ctx):
        cid = cycle.cycle_id

        def body():
            for f in ctx["provenance"]:
                self.ingested_repo.save(f)
            for f in ctx["provenance"]:
                self.audit_event(cid, "upload_ged" if f.doc_type == "GED" else "upload_budget",
                                 {"name": f.name, "fingerprint": f.fingerprint, "period": f.period})
        self.transition(cycle, CycleState.INTAKE, body)

    def do_processed(self, cycle, ctx):
        cid = cycle.cycle_id

        def body():
            self.audit_event(cid, "validate", {"readiness": ctx["readiness"]})
            ex = ctx["extracted"] or {}
            self.audit_event(cid, "extract", {"ged_valid": len(ex.get("ged_valid", [])),
                             "quarantined": len(ex.get("ged_quarantined", [])) + len(ex.get("budget_quarantined", [])),
                             "rejected": bool(ctx["rejected"])})
        self.transition(cycle, CycleState.PROCESSED, body)

    def do_verified(self, cycle, ctx):
        cid = cycle.cycle_id
        self.transition(cycle, CycleState.VERIFIED, lambda: self.audit_event(cid, "verify", {"approved": True}))

    def do_analyzed(self, cycle, ctx):
        cid = cycle.cycle_id

        def body():
            findings, run = self.analysis.run(ctx["vds"])   # engine writes findings via command port
            run["cycle_id"] = cid
            self.run_repo.save(run)
            self.audit_event(cid, "analyze", {"run_id": run["run_id"], "config_version": run["config_version"],
                             "input_fingerprint": run["input_fingerprint"]})
            for f in findings:
                self.audit_event(cid, "finding", {"id": f.id, "account": f.account,
                                 "severity": f.severity, "type": f.finding_type})
            ctx["findings"] = findings
            ctx["run"] = run
        self.transition(cycle, CycleState.ANALYZED, body)

    def do_summarized(self, cycle, ctx):
        cid = cycle.cycle_id

        def body():
            fdicts = self.finding_repo.list(cid)
            run = self.run_repo.get_by_cycle(cid) or {}
            summary = self.reporting.summary(cycle, fdicts, run)
            self.audit_event(cid, "summarize", {"status": summary["status_label"], "findings": summary["finding_count"]})
            ctx["summary"] = summary
        self.transition(cycle, CycleState.SUMMARIZED, body)

    def do_exported(self, cycle, ctx):
        cid = cycle.cycle_id

        def body():
            run = self.run_repo.get_by_cycle(cid) or {}
            summary = ctx.get("summary") or self.reporting.summary(cycle, self.finding_repo.list(cid), run)
            export = self.export.build(cycle, summary, run, data_as_of=self.clock.now())
            self.audit_event(cid, "export", {"period": export["period"]})
            ctx["export"] = export
        self.transition(cycle, CycleState.EXPORTED, body)

    # ---- batch recompute + drive (used by Orchestrator) ----
    def new_ctx(self, ged_path, budget_path) -> Dict[str, Any]:
        return {"provenance": None, "paths": {"GED": ged_path, "BUDGET": budget_path},
                "rejected": None, "extracted": None, "readiness": None,
                "vds": None, "findings": None, "run": None}

    def prepare(self, cycle, ged_path, budget_path, approve) -> Dict[str, Any]:
        provenance, missing = self.build_provenance(cycle, ged_path, budget_path)
        ctx = self.new_ctx(ged_path, budget_path)
        ctx["provenance"] = provenance
        if missing:
            ctx["rejected"] = "Required file(s) missing or unreadable: " + ", ".join(missing) + "."
            ctx["readiness"] = {"Budget Analysis": "Unavailable - " + ctx["rejected"]}
            return ctx
        extracted = self.extract(ged_path, budget_path)
        ctx["extracted"] = extracted
        ctx["readiness"] = extracted["readiness"]
        if not extracted["available"]:
            ctx["rejected"] = extracted["reason"]
            return ctx
        ctx["vds"] = self.build_verified(cycle.cycle_id, extracted, approve)
        return ctx

    def drive(self, cycle, ctx) -> None:
        self.do_intake(cycle, ctx)
        self.do_processed(cycle, ctx)
        if ctx["rejected"]:
            return  # safe stop: no verification, no rule ever runs (NFR-062/AC-3)
        self.do_verified(cycle, ctx)
        self.do_analyzed(cycle, ctx)
        self.do_summarized(cycle, ctx)
        self.do_exported(cycle, ctx)

    def result(self, cycle, ctx) -> Dict[str, Any]:
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
