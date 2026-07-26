# Implements: FR-005/006, FR-001/003/010, FR-007, FR-026, FR-084..089, NFR-005/006/019/057/062, F-02-02
# The single source of review-cycle transition rules: atomic (data + audit + state advancement),
# resume-gated (no-duplicate), rejection safe-stop. Both Orchestrator (batch run_review/resume) and
# ReviewWorkflowService (interactive, step-by-step) drive THESE public methods — neither reaches
# into the other's internals. No UI framework, no PySide6.
from __future__ import annotations
from typing import Any, Dict
from finsight.domain.review_cycle import CycleState, has_reached
from finsight.domain.lifecycle import (
    SourceBinding, IntakeStage, ReviewGeneration, AnalyticalState, CreationReason, ExportArtifact,
)
from finsight.application import intake as INTAKE
from finsight.application.analysis import verified_dataset_fingerprint
from finsight.diagnostics import get_logger

_log = get_logger("transition")


class TransitionEngine:
    def __init__(self, cycle_repo, ingested_repo, run_repo, finding_repo, audit, uow, hasher,
                 pipeline, verification, analysis, reporting, export, clock, actor="local-user",
                 source_binding_repo=None, cycle_lifecycle_repo=None, review_generation_repo=None,
                 export_artifact_repo=None):
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
        # Phase 6.4c lifecycle persistence (optional; wired by composition, None in direct-construction
        # tests). Source binding = the reconstruction hint (path) + source identity (fingerprint).
        self.source_binding_repo = source_binding_repo
        self.cycle_lifecycle_repo = cycle_lifecycle_repo
        # Phase 6.4cA: verification persists its complete verification basis by creating the WORKING
        # generation at analytical_state=VERIFIED (INITIAL_VERIFICATION). Optional/None in direct tests.
        self.review_generation_repo = review_generation_repo
        # R1-M3: immutable export identity (ADR-015). Optional; None in direct-construction tests.
        self.export_artifact_repo = export_artifact_repo

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
    def build_provenance(self, cycle, ged_path, budget_path, invoice_path=None):
        # INVOICE is an OPTIONAL captured source (target-product §6): fingerprinted for provenance +
        # audit like any untrusted inbound file (NFR-012), but it is NOT extracted or analyzed — no
        # invoice rule catalog exists (E-12 / Phase 3). Reconstruction ignores non-required bindings
        # (reconstruction.REQUIRED_DOCS = GED, BUDGET), so capturing it never perturbs the trusted core.
        paths = {"GED": ged_path, "BUDGET": budget_path}
        if invoice_path:
            paths["INVOICE"] = invoice_path
        return INTAKE.build_provenance(
            cycle, paths, self.hasher, self.clock, self.actor, optional=("INVOICE",))

    def extract(self, ged_path, budget_path):
        return self.pipeline.run(ged_path, budget_path)

    def build_verified(self, cycle_id, extracted, approve):
        return self.verification.build(cycle_id, extracted, approved=approve)

    # ---- individual transitions (public; the shared rules) ----
    def do_intake(self, cycle, ctx):
        cid = cycle.cycle_id
        paths = ctx.get("paths") or {}

        def body():
            for f in ctx["provenance"]:
                self.ingested_repo.save(f)
            # Persist the source binding (reconstruction hint + identity) atomically with provenance +
            # audit. Only after successful fingerprinting/acceptance, and only when a path is known.
            # The path is a hint; the fingerprint is the source identity (ADR-012). Bytes are never
            # stored. The upload_ged/upload_budget events ARE the "source bound" audit facts.
            if self.source_binding_repo is not None:
                for f in ctx["provenance"]:
                    path = paths.get(f.doc_type)
                    if path:
                        # Guarded write: initial bind here; never overwrites a trusted identity.
                        self.source_binding_repo.bind(SourceBinding(
                            cid, f.doc_type, path, f.fingerprint, self.clock.now(), self.actor))
            if self.cycle_lifecycle_repo is not None:
                self.cycle_lifecycle_repo.set_intake_stage(cid, IntakeStage.SOURCE_BOUND)
            for f in ctx["provenance"]:
                # upload_ged / upload_budget / upload_invoice — the "source bound" audit facts.
                self.audit_event(cid, "upload_" + f.doc_type.lower(),
                                 {"name": f.name, "fingerprint": f.fingerprint, "period": f.period})
            # §7: the explicit "Continue anyway" decision to proceed without a source is a material
            # action — record which sources were knowingly omitted so it is auditable and disclosable.
            acknowledged = ctx.get("acknowledged_missing") or []
            if acknowledged:
                self.audit_event(cid, "missing_source_acknowledged", {"missing": sorted(acknowledged)})
        self.transition(cycle, CycleState.INTAKE, body)

    def do_processed(self, cycle, ctx):
        cid = cycle.cycle_id

        def body():
            self.audit_event(cid, "validate", {"readiness": ctx["readiness"]})
            ex = ctx["extracted"] or {}
            self.audit_event(cid, "extract", {"ged_valid": len(ex.get("ged_valid", [])),
                             "quarantined": len(ex.get("ged_quarantined", [])) + len(ex.get("budget_quarantined", [])),
                             "rejected": bool(ctx["rejected"])})
            if self.cycle_lifecycle_repo is not None:   # candidate now processed (ADR-011 §7 intake)
                self.cycle_lifecycle_repo.set_intake_stage(cid, IntakeStage.PROCESSED)
        self.transition(cycle, CycleState.PROCESSED, body)

    def do_verified(self, cycle, ctx):
        cid = cycle.cycle_id

        def body():
            gen_id = self._create_initial_verification_generation(cid, ctx)
            detail = {"approved": True}
            if gen_id is not None:
                detail.update({"generation_id": gen_id, "creation_reason": "INITIAL_VERIFICATION"})
            self.audit_event(cid, "verify", detail)
        self.transition(cycle, CycleState.VERIFIED, body)

    def _create_initial_verification_generation(self, cid, ctx):
        """Persist the verification basis (Phase 6.4cA): create the WORKING generation at VERIFIED with
        the verified-DATASET fingerprint + extractor version + human actor/timestamp, and point the
        cycle's working generation at it. INITIAL_VERIFICATION only (first generation of the review);
        SOURCE_/EXTRACTOR_REVERIFICATION belong to the deferred explicit re-verification flow. Runs
        INSIDE the do_verified transaction, so it is atomic with the state advance + audit.

        Returns the new generation_id, or None when generation persistence is not wired (direct tests)
        or a generation already exists (legacy/backfilled review — verification basis unchanged)."""
        if self.review_generation_repo is None or self.cycle_lifecycle_repo is None:
            return None
        if ctx.get("vds") is None:
            return None
        if self.review_generation_repo.list_for_cycle(cid):
            return None                                  # not the first generation -> deferred flow
        vfp = verified_dataset_fingerprint(ctx["vds"])
        now = self.clock.now()
        seq = self.review_generation_repo.next_sequence_number(cid)
        gen_id = "%s-gen-%d" % (cid, seq)
        self.review_generation_repo.insert(ReviewGeneration(
            generation_id=gen_id, cycle_id=cid, sequence_number=seq,
            analytical_state=AnalyticalState.VERIFIED, creation_reason=CreationReason.INITIAL_VERIFICATION,
            based_on_generation_id=None, verification_basis_generation_id=None,
            verified_fingerprint=vfp, extractor_version=getattr(self.pipeline, "extractor_version", None),
            verification_actor=self.actor, verified_at=now, created_by=self.actor, created_at=now))
        self.cycle_lifecycle_repo.set_working_generation(cid, gen_id)   # working, NOT published
        return gen_id

    def _advance_current_generation(self, cid, new_state, publish=False):
        """Progress the CURRENT (working) generation's analytical_state in lockstep with the workflow
        (ADR-011 §7), so cycles.state — written by transition() to the same target — stays a faithful
        DERIVED MIRROR of the generation (no duplicate analytical truth). At ANALYZED the FIRST
        generation auto-publishes (ADR-011 §8). Only the WORKING generation is touched (which, once
        published, equals the published pointer), so this stays interpretation-neutral w.r.t. the
        working/published derived-mirror question — which is a RED CARD and never reached without a
        second generation (re-verification, R2-deferred)."""
        if self.review_generation_repo is None or self.cycle_lifecycle_repo is None:
            return
        working = self.review_generation_repo.working_generation(cid)
        if working is None:
            return   # legacy/backfilled or generation-less review — nothing to advance
        self.review_generation_repo.advance_analytical_state(working.generation_id, new_state)
        if publish and self.review_generation_repo.published_generation(cid) is None:
            self.cycle_lifecycle_repo.set_published_generation(cid, working.generation_id)  # first-gen auto-publish

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
            self._link_generation_lineage(cid, run["run_id"])   # run + findings -> current generation
            self._advance_current_generation(cid, AnalyticalState.ANALYZED, publish=True)
        self.transition(cycle, CycleState.ANALYZED, body)

    def _link_generation_lineage(self, cid, run_id):
        """R1-M2 (ADR-011 §3/§8): bind the rule run and the cycle's findings to the current (working)
        generation, so every result belongs to exactly one generation lineage. Run first, then findings
        (the migration 0003 finding⇒run trigger requires the run to already carry the generation).
        No-op for legacy/generation-less reviews (nothing to link)."""
        if self.review_generation_repo is None:
            return
        working = self.review_generation_repo.working_generation(cid)
        if working is None:
            return
        self.run_repo.set_generation(run_id, working.generation_id)
        self.finding_repo.set_generation_for_cycle(cid, working.generation_id)

    def do_summarized(self, cycle, ctx):
        cid = cycle.cycle_id

        def body():
            fdicts = self.finding_repo.list(cid)
            run = self.run_repo.get_by_cycle(cid) or {}
            summary = self.reporting.summary(cycle, fdicts, run)
            self.audit_event(cid, "summarize", {"status": summary["status_label"], "findings": summary["finding_count"]})
            ctx["summary"] = summary
            self._advance_current_generation(cid, AnalyticalState.SUMMARIZED)
        self.transition(cycle, CycleState.SUMMARIZED, body)

    def do_exported(self, cycle, ctx):
        cid = cycle.cycle_id

        def body():
            run = self.run_repo.get_by_cycle(cid) or {}
            summary = ctx.get("summary") or self.reporting.summary(cycle, self.finding_repo.list(cid), run)
            gen = self._current_generation(cid)
            manifest = self._export_manifest(cid, cycle, gen, run) if gen else None
            export = self.export.build(cycle, summary, run, data_as_of=self.clock.now(), manifest=manifest)
            self.audit_event(cid, "export", {"period": export["period"]})
            ctx["export"] = export
            self._advance_current_generation(cid, AnalyticalState.EXPORTED)
            self._persist_export_artifact(cid, gen, run, export)
        self.transition(cycle, CycleState.EXPORTED, body)

    def _current_generation(self, cid):
        if self.review_generation_repo is None:
            return None
        return (self.review_generation_repo.published_generation(cid)
                or self.review_generation_repo.working_generation(cid))

    def _export_manifest(self, cid, cycle, gen, run):
        """ADR-015 §3 manifest, embedded in the export content: identifies the exact generation, run,
        versions, and verified basis that produced the export. R1 is single-generation, so status is
        always 'current' (no supersession). The 'verified-source fingerprint' is the generation's
        verified-DATASET fingerprint (ADR-015 §3, architect-confirmed)."""
        return {"cycle_id": cid, "period": cycle.month + " " + cycle.year,
                "generation_id": gen.generation_id, "sequence_number": gen.sequence_number,
                "verified_source_fingerprint": gen.verified_fingerprint,
                "extractor_version": gen.extractor_version, "creation_reason": gen.creation_reason.value,
                "run_id": run.get("run_id"), "ruleset_version": run.get("ruleset_version"),
                "config_version": run.get("config_version"), "input_fingerprint": run.get("input_fingerprint"),
                "status": "current", "exported_at": self.clock.now()}

    def _persist_export_artifact(self, cid, gen, run, export):
        """Persist an IMMUTABLE export identity record (ADR-015 §3). Append-only (migration 0003 blocks
        update/delete); one export per generation in R1. Idempotent: skipped if already recorded, so a
        resume never duplicates it. Requires the run to be generation-linked (R1-M2) so the export
        cycle/generation/run agreement trigger passes."""
        if self.export_artifact_repo is None or gen is None or not run.get("run_id"):
            return
        export_id = "exp-" + gen.generation_id
        if self.export_artifact_repo.get(export_id) is not None:
            return
        self.export_artifact_repo.insert(ExportArtifact(
            export_id=export_id, cycle_id=cid, generation_id=gen.generation_id, run_id=run["run_id"],
            export_path="%s-%s.json" % (cid, gen.generation_id), export_fingerprint=self.export.fingerprint(export),
            created_at=self.clock.now(), actor=self.actor))

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
