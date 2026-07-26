# Implements: ADR-011/012 (Phase 6.4c) — fingerprint-verified working-set reconstruction & review
# recovery. THE TRUST BOUNDARY of the whole product lives here.
#
# NON-NEGOTIABLE: a stored path is only a reconstruction HINT; the recorded fingerprint is the source
# IDENTITY. Reconstruction NEVER trusts a path merely because a file exists there. It NEVER silently
# updates identity, accepts changed bytes, re-verifies, re-analyzes, advances workflow state, or
# installs a partial working set. It FAILS LOUDLY (a typed recovery status) rather than succeeding
# ambiguously. Reconstruction is read-and-rebuild only: it performs NO durable writes.
#
# Threading: load_inputs() reads the DB (UI thread); reconstruct() is pure compute over the loaded
# inputs + source bytes (worker thread, no DB); the caller installs the candidate on success (UI
# thread, build-then-swap). apply_rebind() is the only durable write here (path hint + audit, atomic).
from __future__ import annotations
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from finsight.domain.review_cycle import CycleState, has_reached
from finsight.application.review_session import ReviewSession
from finsight.application.analysis import verified_dataset_fingerprint
from finsight.application.pipeline import EXTRACTOR_VERSION
from finsight.application.source_format import is_supported as _is_supported_source

REQUIRED_DOCS = ("GED", "BUDGET")


class RecoveryStatus(str, Enum):
    """Every outcome of opening/resuming a review is exactly ONE of these — never a free-text guess."""
    READY_FROM_CACHE = "READY_FROM_CACHE"                 # in-memory working set already valid
    RECONSTRUCTED_MATCH = "RECONSTRUCTED_MATCH"           # rebuilt from a fingerprint-verified source
    NO_SOURCE_REQUIRED = "NO_SOURCE_REQUIRED"             # pre-intake review; nothing to reconstruct
    MISSING_BINDING = "MISSING_BINDING"                   # no source binding (legacy/pre-6.4c review)
    MISSING_SOURCE = "MISSING_SOURCE"                     # bound path does not exist
    MOVED_SOURCE_CANDIDATE = "MOVED_SOURCE_CANDIDATE"     # re-selected file matches the source identity
    CHANGED_SOURCE = "CHANGED_SOURCE"                     # file bytes differ from the recorded identity
    UNREADABLE_SOURCE = "UNREADABLE_SOURCE"               # file exists but bytes cannot be read
    UNSUPPORTED_SOURCE = "UNSUPPORTED_SOURCE"             # re-selected file is not a supported workbook
    EXTRACTION_FAILED = "EXTRACTION_FAILED"               # byte-matched source no longer extracts
    VERIFIED_DATA_MISMATCH = "VERIFIED_DATA_MISMATCH"     # rebuilt verified data != certified data
    EXTRACTOR_VERSION_MISMATCH = "EXTRACTOR_VERSION_MISMATCH"   # extractor changed vs the basis
    LEGACY_METADATA_INCOMPLETE = "LEGACY_METADATA_INCOMPLETE"   # legacy generation not reproducible

# Statuses that represent a successfully usable (or empty-by-design) working set.
_OK = {RecoveryStatus.READY_FROM_CACHE, RecoveryStatus.RECONSTRUCTED_MATCH,
       RecoveryStatus.NO_SOURCE_REQUIRED}

# Divergence: the selected/bound source is not equivalent to the certified basis. A permanent audit
# fact worth recording exactly once (never re-emitted on every navigation/refresh).
DIVERGENCE_STATUSES = {RecoveryStatus.CHANGED_SOURCE, RecoveryStatus.VERIFIED_DATA_MISMATCH,
                       RecoveryStatus.EXTRACTOR_VERSION_MISMATCH}


@dataclass(frozen=True)
class RecoveryMessage:
    """Presentation-neutral, four-part honest message. Contains NO full paths and NO raw fingerprints
    (filenames only). The UI renders it; it is NEVER sent to Ask Fin, an AI journal, or an export."""
    what_happened: str
    remains_valid: str
    cannot_continue: str
    action_required: str


@dataclass(frozen=True)
class RecoveryResult:
    status: RecoveryStatus
    cycle_id: str
    message: RecoveryMessage
    document_type: Optional[str] = None
    filename: Optional[str] = None                        # basename only, never a full path
    recorded_fingerprint_short: Optional[str] = None      # first 12 chars, for a Details view only
    current_fingerprint_short: Optional[str] = None
    recorded_fingerprint: Optional[str] = field(default=None, repr=False)   # full — audit identity only
    current_fingerprint: Optional[str] = field(default=None, repr=False)    # full — audit identity only
    session: Optional[object] = field(default=None, repr=False)   # candidate working set (OK only)

    @property
    def ok(self) -> bool:
        return self.status in _OK

    @property
    def usable_session(self):
        return self.session if self.status == RecoveryStatus.RECONSTRUCTED_MATCH else None


@dataclass(frozen=True)
class ReconstructionInputs:
    """Everything reconstruct() needs, loaded from the DB on the UI thread so the worker touches no
    database. Plain data only (safe to hand to a worker thread)."""
    cycle: object                                         # ReviewCycle (plain dataclass)
    state: CycleState
    bindings: Dict[str, object]                           # doc_type -> SourceBinding
    recorded_verified_fingerprint: Optional[str]
    recorded_extractor_version: Optional[str]
    legacy_metadata_incomplete: bool
    overrides: Optional[Dict] = None                       # effective corrections, pre-fetched (UI thread)


def _short(fp: Optional[str]) -> Optional[str]:
    return fp[:12] if fp else None


def ready_from_cache(cycle_id: str) -> RecoveryResult:
    """The result for an in-memory cache hit — no reconstruction was needed."""
    return RecoveryResult(RecoveryStatus.READY_FROM_CACHE, cycle_id,
                          RecoveryMessage("This review is ready to continue.", "", "", ""))


def no_source_required(cycle_id: str) -> RecoveryResult:
    """The result for a pre-intake review — there is no source to reconstruct yet."""
    return RecoveryResult(RecoveryStatus.NO_SOURCE_REQUIRED, cycle_id,
                          RecoveryMessage("This review has no source data yet.", "", "",
                                          "Select source files to begin."))


class ReviewReconstructionService:
    """Fingerprint-verified reconstruction + recovery classification. Holds only compute collaborators
    (via the deterministic engine) plus the source-binding repo; performs no durable write except the
    explicit, audited path re-bind."""

    def __init__(self, engine, source_binding_repo, review_generation_repo=None):
        self._e = engine
        self._bindings = source_binding_repo
        self._gens = review_generation_repo   # optional: supplies extractor_version + legacy flag

    # ---------- UI thread: load persisted inputs (cheap DB reads) ----------
    def load_inputs(self, cycle_id: str) -> Optional[ReconstructionInputs]:
        cycle = self._e.cycle_repo.get(cycle_id)
        if cycle is None:
            return None
        bindings = {b.document_type: b for b in self._bindings.list_for_cycle(cycle_id)}
        run = self._e.run_repo.get_by_cycle(cycle_id) or {}
        recorded_vfp = run.get("input_fingerprint")           # verified-data fp (ANALYZED+)
        extractor_version, legacy_incomplete = None, False
        if self._gens is not None:
            gen = self._gens.published_generation(cycle_id) or self._gens.working_generation(cycle_id)
            if gen is not None:
                extractor_version = gen.extractor_version
                legacy_incomplete = bool(gen.legacy_metadata_incomplete)
                if recorded_vfp is None:
                    recorded_vfp = gen.verified_fingerprint
        # Pre-fetch the effective corrections here (UI thread), so the worker reconstruction reproduces
        # the CERTIFIED (corrected) verified dataset without touching the thread-bound DB connection.
        override_repo = getattr(self._e, "extraction_override_repo", None)
        overrides = override_repo.effective(cycle_id) if override_repo is not None else {}
        return ReconstructionInputs(cycle, cycle.state, bindings, recorded_vfp, extractor_version,
                                    legacy_incomplete, overrides)

    # ---------- worker thread: pure reconstruction (NO database) ----------
    def reconstruct(self, inputs: ReconstructionInputs) -> RecoveryResult:
        cid = inputs.cycle.cycle_id
        if not has_reached(inputs.state, CycleState.INTAKE):
            return self._result(RecoveryStatus.NO_SOURCE_REQUIRED, cid,
                                 "This review has no source data yet.", "", "", "Select source files to begin.")

        # 1) Bindings must exist. Absent binding == not reconstructable from persisted identity.
        missing_binding = [d for d in REQUIRED_DOCS if d not in inputs.bindings]
        if missing_binding:
            if inputs.legacy_metadata_incomplete:
                return self._legacy_incomplete(cid, inputs.state)
            return self._missing_binding(cid, inputs.state, missing_binding)

        # 2) Fingerprint-verify every bound source BEFORE any use (identity, not location).
        paths = {}
        for doc in REQUIRED_DOCS:
            b = inputs.bindings[doc]
            paths[doc] = b.last_known_path
            fname = os.path.basename(b.last_known_path)
            try:
                probe = self._e.hasher.probe(b.last_known_path)
            except Exception:
                return self._unreadable(cid, doc, fname)
            if not probe["exists"]:
                return self._missing_source(cid, inputs.state, doc, fname)
            if probe["sha256"] != b.source_fingerprint:
                return self._changed_source(cid, doc, fname, b.source_fingerprint, probe["sha256"])

        # 3) Bytes match the certified identity -> re-extract deterministically.
        extracted = self._e.extract(paths["GED"], paths["BUDGET"])
        verified = has_reached(inputs.state, CycleState.VERIFIED)
        if verified and not extracted.get("available"):
            # A byte-identical certified source must still extract; if it does not, fail loudly.
            return self._extraction_failed(cid)

        # 4) Verified reviews: rebuild the verified dataset and prove it equals the certified data.
        vds = None
        if verified:
            vds = self._e.build_verified(cid, extracted, approve=True, overrides=inputs.overrides)
            if inputs.recorded_verified_fingerprint is not None:
                computed = verified_dataset_fingerprint(vds)
                if computed != inputs.recorded_verified_fingerprint:
                    return self._verified_mismatch(cid, inputs, computed)

        session = self._build_session(inputs, paths, extracted, vds)
        return self._result(RecoveryStatus.RECONSTRUCTED_MATCH, cid,
                            "The review was resumed from its verified source.",
                            "All prior work remains valid.", "", "", session=session)

    def _build_session(self, inputs, paths, extracted, vds) -> ReviewSession:
        # Build-then-return a candidate; the manager installs it only on success. No durable writes.
        provenance, _missing = self._e.build_provenance(inputs.cycle, paths["GED"], paths["BUDGET"])
        s = ReviewSession(inputs.cycle.cycle_id)
        s.ctx["paths"] = {"GED": paths["GED"], "BUDGET": paths["BUDGET"]}
        s.ctx["provenance"] = provenance
        s.ctx["extracted"] = extracted
        s.ctx["readiness"] = extracted.get("readiness")
        s.ctx["rejected"] = None if extracted.get("available") else extracted.get("reason")
        if vds is not None:
            s.ctx["vds"] = vds
        return s

    # ---------- moved/changed classification for an explicitly re-selected candidate ----------
    def classify_candidate(self, cycle_id: str, document_type: str, new_path: str) -> RecoveryResult:
        """Classify a reviewer-chosen replacement file against the bound source identity. Pure compute
        (no DB write). MOVED == identity preserved (offer a path-hint update); CHANGED == divergent."""
        binding = self._bindings.get(cycle_id, document_type)
        if binding is None:
            return self._missing_binding(cycle_id, None, [document_type])
        fname = os.path.basename(new_path)
        if not _is_supported_source(new_path):       # shared authoritative format policy
            return self._unsupported(cycle_id, document_type, fname)
        try:
            probe = self._e.hasher.probe(new_path)
        except Exception:
            return self._unreadable(cycle_id, document_type, fname)
        if not probe["exists"]:
            return self._missing_source(cycle_id, None, document_type, fname)
        if probe["sha256"] == binding.source_fingerprint:
            return self._moved_candidate(cycle_id, document_type, new_path, fname, binding.source_fingerprint)
        return self._changed_source(cycle_id, document_type, fname, binding.source_fingerprint,
                                    probe["sha256"])

    # ---------- UI thread: divergence audit, idempotent PER FINGERPRINT PAIR ----------
    def record_divergence(self, cycle_id: str, result: "RecoveryResult") -> bool:
        """Record a permanent 'source_divergence_detected' audit fact, idempotent per
        (document_type, recorded_fingerprint, observed_fingerprint). Re-detecting the SAME unresolved
        divergence (navigation/refresh) appends nothing; a NEW transition (e.g. F2→F3, or a divergence
        in the other document) appends a distinct event. Idempotency is persisted (checks the audit
        trail), so it holds across restarts. Returns True only when a new event was appended."""
        if result.status not in DIVERGENCE_STATUSES:
            return False
        doc = result.document_type or "verified_dataset"
        recorded = result.recorded_fingerprint or ""
        observed = result.current_fingerprint or ""
        for e in self._e.audit.events(cycle_id):
            if e.get("action") == "source_divergence_detected":
                d = e.get("detail") or {}
                if (d.get("document_type") == doc and d.get("recorded_fingerprint") == recorded
                        and d.get("observed_fingerprint") == observed):
                    return False                                # same unresolved pair — do not flood
        with self._e.uow.atomic():
            self._e.audit_event(cycle_id, "source_divergence_detected",
                                {"kind": result.status.value, "document_type": doc,
                                 "recorded_fingerprint": recorded, "observed_fingerprint": observed})
        return True

    # ---------- UI thread: the only durable write — path-hint re-bind + audit, atomic ----------
    def apply_rebind(self, cycle_id: str, document_type: str, new_path: str) -> RecoveryResult:
        """Update ONLY the path hint after a verified MOVED match, atomically with an audit event.
        The source fingerprint (identity) and all prior work are preserved. Rejects a non-matching
        candidate rather than silently changing identity."""
        from finsight.domain.lifecycle import SourceBinding
        classified = self.classify_candidate(cycle_id, document_type, new_path)
        if classified.status != RecoveryStatus.MOVED_SOURCE_CANDIDATE:
            return classified                                   # never rebind a divergent/invalid file
        binding = self._bindings.get(cycle_id, document_type)
        with self._e.uow.atomic():
            # Guarded path-rebind: bind() carries the SAME fingerprint, so only the path hint changes;
            # a different fingerprint would be refused (it can never reach here — classify guards it).
            self._bindings.bind(SourceBinding(
                cycle_id, document_type, new_path, binding.source_fingerprint,
                self._e.clock.now(), self._e.actor))
            self._e.audit_event(cycle_id, "source_rebound",
                                {"document_type": document_type, "fingerprint_unchanged": True})
        return self._moved_candidate(cycle_id, document_type, new_path,
                                     os.path.basename(new_path), binding.source_fingerprint,
                                     rebound=True)

    # ---------- result builders (each message: what / remains valid / cannot continue / action) ----------
    def _result(self, status, cid, what, remains, cannot, action, **kw) -> RecoveryResult:
        return RecoveryResult(status, cid, RecoveryMessage(what, remains, cannot, action), **kw)

    def _missing_binding(self, cid, state, docs) -> RecoveryResult:
        analyzed = state is not None and has_reached(state, CycleState.ANALYZED)
        remains = ("Previously analyzed findings and exports remain viewable." if analyzed else "")
        return self._result(
            RecoveryStatus.MISSING_BINDING, cid,
            "This review has no recorded source binding (a legacy or pre-recovery review).",
            remains, "It cannot be reconstructed from a stored source.",
            "Re-select the source files to continue.", document_type=",".join(docs))

    def _legacy_incomplete(self, cid, state) -> RecoveryResult:
        return self._result(
            RecoveryStatus.LEGACY_METADATA_INCOMPLETE, cid,
            "This legacy review's verification metadata is incomplete.",
            "Its recorded findings and exports remain viewable as history.",
            "It cannot be reproduced or re-verified confidently.",
            "Re-select the sources only if you need to continue source-derived work.")

    def _missing_source(self, cid, state, doc, fname) -> RecoveryResult:
        analyzed = state is not None and has_reached(state, CycleState.ANALYZED)
        remains = ("Previously analyzed results remain viewable." if analyzed else "")
        return self._result(
            RecoveryStatus.MISSING_SOURCE, cid,
            "The %s source file '%s' could not be found at its last known location." % (doc, fname),
            remains, "Source-derived work cannot continue until it is located.",
            "Locate the file or re-select the source.", document_type=doc, filename=fname)

    def _unreadable(self, cid, doc, fname) -> RecoveryResult:
        return self._result(
            RecoveryStatus.UNREADABLE_SOURCE, cid,
            "The %s source file '%s' exists but its contents could not be read." % (doc, fname),
            "", "It cannot be used until it is readable.",
            "Check the file, then retry or re-select it.", document_type=doc, filename=fname)

    def _unsupported(self, cid, doc, fname) -> RecoveryResult:
        return self._result(
            RecoveryStatus.UNSUPPORTED_SOURCE, cid,
            "The selected %s file '%s' is not a supported workbook." % (doc, fname),
            "", "It cannot be used as a source.",
            "Select a supported .xlsx workbook.", document_type=doc, filename=fname)

    def _changed_source(self, cid, doc, fname, recorded, current) -> RecoveryResult:
        return self._result(
            RecoveryStatus.CHANGED_SOURCE, cid,
            "The selected %s source '%s' differs from the previously verified source." % (doc, fname),
            "Existing findings remain valid for the previously verified version.",
            "The changed source cannot be analyzed as current without re-verification.",
            "Re-verify the changed source to analyze it, or restore the verified file.",
            document_type=doc, filename=fname,
            recorded_fingerprint_short=_short(recorded), current_fingerprint_short=_short(current),
            recorded_fingerprint=recorded, current_fingerprint=current)

    def _moved_candidate(self, cid, doc, new_path, fname, fingerprint, rebound=False) -> RecoveryResult:
        what = ("The %s source was re-bound to its new location (identity unchanged)." % doc
                if rebound else
                "The selected %s file '%s' matches the previously verified source." % (doc, fname))
        return self._result(
            RecoveryStatus.MOVED_SOURCE_CANDIDATE, cid, what,
            "Verification and findings remain valid; only the file location changed.", "",
            "" if rebound else "Confirm to update the stored location and resume.",
            document_type=doc, filename=fname, recorded_fingerprint_short=_short(fingerprint))

    def _extraction_failed(self, cid) -> RecoveryResult:
        return self._result(
            RecoveryStatus.EXTRACTION_FAILED, cid,
            "The source matched its recorded identity but could not be extracted.",
            "Prior recorded results remain viewable.",
            "A working set cannot be rebuilt from it.",
            "Re-select and re-process the source to continue.")

    def _verified_mismatch(self, cid, inputs, computed) -> RecoveryResult:
        extractor_changed = (inputs.recorded_extractor_version is not None
                             and inputs.recorded_extractor_version != EXTRACTOR_VERSION)
        status = (RecoveryStatus.EXTRACTOR_VERSION_MISMATCH if extractor_changed
                  else RecoveryStatus.VERIFIED_DATA_MISMATCH)
        what = ("The extractor changed and can no longer reproduce the certified verified data."
                if extractor_changed else
                "The rebuilt verified data does not match the previously certified verified data.")
        return self._result(
            status, cid, what,
            "Existing findings remain valid for the previously certified data.",
            "This review cannot be analyzed as current without explicit re-verification.",
            "Re-process and re-verify the source under the current software to continue.",
            recorded_fingerprint_short=_short(inputs.recorded_verified_fingerprint),
            current_fingerprint_short=_short(computed),
            recorded_fingerprint=inputs.recorded_verified_fingerprint, current_fingerprint=computed)
