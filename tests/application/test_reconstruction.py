# Verifies: Phase 6.4c — fingerprint-verified reconstruction & review recovery (ADR-011/012).
# THE TRUST CORE. Reconstruction must fail LOUDLY (a typed status) rather than succeed ambiguously,
# must never trust a path over a fingerprint, and must never mutate durable state or install partial
# working sets. Common flows use a real container + real .xlsx files; exotic branches use a fake
# engine so every RecoveryStatus is reachable and asserted.
import os
import shutil

import pytest

from finsight.app import build_app
from finsight.application.review_session import ReviewSession
from finsight.application.review_working_set import ReviewWorkingSetManager
from finsight.application.reconstruction import (
    ReviewReconstructionService, ReconstructionInputs, RecoveryStatus,
)
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.pipeline import EXTRACTOR_VERSION
from finsight.infrastructure.lifecycle_repositories import ReviewGenerationRepoSqlite
from finsight.domain.review_cycle import ReviewCycle, CycleState
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget


# ============================ real-container integration harness ============================
def _files(tmp_path, tag=""):
    ged = os.path.join(str(tmp_path), "ged%s.xlsx" % tag)
    bud = os.path.join(str(tmp_path), "budget%s.xlsx" % tag)
    build_synthetic_ged(ged)
    build_synthetic_budget(bud)
    return ged, bud


def _open(tmp_path):
    return build_app(os.path.join(str(tmp_path), "fs.db"), FixedClock())


def _svc(container):
    return ReviewReconstructionService(container.orch.engine, container.source_binding_repo,
                                       ReviewGenerationRepoSqlite(container.dal))


def _drive(container, cid, ged, bud, target):
    """Drive a review through the real interactive workflow to `target` state, in one session."""
    wf = ReviewWorkflowService(container.orch.engine)
    wf.create_review(cid, "May", "2026")
    if target == CycleState.CREATED:
        return
    session = ReviewSession(cid)
    wf.upload(session, ged, bud)
    if target == CycleState.INTAKE:
        return
    wf.process(session)
    if target == CycleState.PROCESSED:
        return
    wf.verify(session)
    if target == CycleState.VERIFIED:
        return
    wf.analyze(session)
    if target == CycleState.ANALYZED:
        return
    wf.summarize(session)
    wf.export(session)


def _reconstruct(container, cid):
    svc = _svc(container)
    inputs = svc.load_inputs(cid)
    return svc.reconstruct(inputs)


# ---- source binding write behavior ----
def test_upload_writes_source_binding_with_path_and_fingerprint(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.INTAKE)
    b = c.source_binding_repo.get("A", "GED")
    assert b is not None and b.last_known_path == ged and b.source_fingerprint
    # fingerprint is the source identity; it equals the recorded provenance fingerprint
    prov = {p["doc_type"]: p for p in c.ingested_repo.list("A")}
    assert b.source_fingerprint == prov["GED"]["fingerprint"]


def test_binding_does_not_store_bytes_or_rows(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.INTAKE)
    b = c.source_binding_repo.get("A", "GED")
    # only a hint + identity are stored
    assert set(vars(b).keys()) == {"cycle_id", "document_type", "last_known_path",
                                   "source_fingerprint", "selected_at", "actor"}


def test_failed_upload_writes_no_binding(tmp_path):
    c = _open(tmp_path)
    ged, _bud = _files(tmp_path)
    wf = ReviewWorkflowService(c.orch.engine)
    wf.create_review("A", "May", "2026")
    from finsight.application.errors import MissingFileError
    with pytest.raises(MissingFileError):
        wf.upload(ReviewSession("A"), ged, os.path.join(str(tmp_path), "missing.xlsx"))
    assert c.source_binding_repo.list_for_cycle("A") == []      # nothing bound on failure


def test_upload_sets_intake_stage_and_processing_advances_it(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.INTAKE)
    assert c.cycle_lifecycle_repo.pointers("A")[0] == "SOURCE_BOUND"
    _drive(c, "B", *(_files(tmp_path, "b")), target=CycleState.PROCESSED)
    assert c.cycle_lifecycle_repo.pointers("B")[0] == "PROCESSED"


# ---- restart recovery by workflow state (simulated by reopening the container) ----
@pytest.mark.parametrize("state", [CycleState.PROCESSED, CycleState.VERIFIED,
                                   CycleState.ANALYZED, CycleState.EXPORTED])
def test_restart_reconstructs_match_from_verified_source(tmp_path, state):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, state)
    c2 = _open(tmp_path)                                        # fresh process: in-memory session gone
    result = _reconstruct(c2, "A")
    assert result.status == RecoveryStatus.RECONSTRUCTED_MATCH
    s = result.usable_session
    assert s.ctx["extracted"]["available"] is True
    if state in (CycleState.VERIFIED, CycleState.ANALYZED, CycleState.EXPORTED):
        assert s.ctx["vds"] is not None                        # verified dataset rebuilt


def test_restart_at_created_needs_no_reconstruction(tmp_path):
    c = _open(tmp_path)
    _drive(c, "A", None, None, CycleState.CREATED)
    result = _reconstruct(_open(tmp_path), "A")
    assert result.status == RecoveryStatus.NO_SOURCE_REQUIRED


def test_reconstructed_verified_review_can_be_analyzed(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.VERIFIED)
    c2 = _open(tmp_path)
    result = _reconstruct(c2, "A")
    wf2 = ReviewWorkflowService(c2.orch.engine)
    out = wf2.analyze(result.usable_session)                   # continues from the rebuilt working set
    assert out.finding_count >= 1


# ---- moved / changed / missing ----
def test_missing_source_when_bound_file_deleted(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.VERIFIED)
    os.remove(ged)
    result = _reconstruct(_open(tmp_path), "A")
    assert result.status == RecoveryStatus.MISSING_SOURCE and result.document_type == "GED"


def test_changed_source_detected_not_reconstructed(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.VERIFIED)
    build_synthetic_budget(ged)                                # overwrite GED with different bytes
    result = _reconstruct(_open(tmp_path), "A")
    assert result.status == RecoveryStatus.CHANGED_SOURCE
    assert result.recorded_fingerprint_short != result.current_fingerprint_short
    assert "re-verif" in result.message.action_required.lower()  # requires explicit re-verification


def test_moved_source_matches_and_rebind_updates_path_only(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.VERIFIED)
    moved = os.path.join(str(tmp_path), "moved", "ged.xlsx")
    os.makedirs(os.path.dirname(moved))
    shutil.move(ged, moved)
    c2 = _open(tmp_path)
    svc = _svc(c2)
    assert svc.load_inputs("A") and svc.reconstruct(svc.load_inputs("A")).status == RecoveryStatus.MISSING_SOURCE
    classified = svc.classify_candidate("A", "GED", moved)
    assert classified.status == RecoveryStatus.MOVED_SOURCE_CANDIDATE      # identity preserved
    original_fp = c2.source_binding_repo.get("A", "GED").source_fingerprint
    rebind = svc.apply_rebind("A", "GED", moved)
    assert rebind.status == RecoveryStatus.MOVED_SOURCE_CANDIDATE
    b = c2.source_binding_repo.get("A", "GED")
    assert b.last_known_path == moved and b.source_fingerprint == original_fp   # path only changed
    assert "source_rebound" in c2.audit.timeline("A")
    # now reconstruction succeeds from the new location
    assert svc.reconstruct(svc.load_inputs("A")).status == RecoveryStatus.RECONSTRUCTED_MATCH


def test_rebind_refuses_a_changed_file(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.VERIFIED)
    wrong = os.path.join(str(tmp_path), "wrong.xlsx")
    build_synthetic_budget(wrong)                              # different bytes
    svc = _svc(_open(tmp_path))
    result = svc.apply_rebind("A", "GED", wrong)
    assert result.status == RecoveryStatus.CHANGED_SOURCE       # never silently rebinds a different file


# ---- historical results survive a missing source (ANALYZED+) ----
def test_missing_source_after_analysis_keeps_findings_viewable(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.ANALYZED)
    os.remove(ged)
    os.remove(bud)
    c2 = _open(tmp_path)
    result = _reconstruct(c2, "A")
    assert result.status == RecoveryStatus.MISSING_SOURCE
    assert result.message.remains_valid                        # states results remain viewable
    assert len(c2.finding_repo.list("A")) >= 1                 # persisted findings still readable


# ---- verified-data / extractor mismatch (real source bytes, bogus recorded fingerprint) ----
def test_verified_data_mismatch_when_recorded_fingerprint_differs(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.VERIFIED)
    svc = _svc(_open(tmp_path))
    base = svc.load_inputs("A")
    bogus = ReconstructionInputs(base.cycle, base.state, base.bindings,
                                 recorded_verified_fingerprint="deadbeef" * 8,
                                 recorded_extractor_version=None, legacy_metadata_incomplete=False)
    assert svc.reconstruct(bogus).status == RecoveryStatus.VERIFIED_DATA_MISMATCH


def test_extractor_version_mismatch_classified_distinctly(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.VERIFIED)
    svc = _svc(_open(tmp_path))
    base = svc.load_inputs("A")
    bogus = ReconstructionInputs(base.cycle, base.state, base.bindings,
                                 recorded_verified_fingerprint="deadbeef" * 8,
                                 recorded_extractor_version="extractor-OLD",
                                 legacy_metadata_incomplete=False)
    assert bogus.recorded_extractor_version != EXTRACTOR_VERSION
    assert svc.reconstruct(bogus).status == RecoveryStatus.EXTRACTOR_VERSION_MISMATCH


# ---- cross-cycle isolation ----
def test_two_reviews_reconstruct_independently(tmp_path):
    c = _open(tmp_path)
    ga, ba = _files(tmp_path, "a")
    gb, bb = _files(tmp_path, "b")
    _drive(c, "A", ga, ba, CycleState.VERIFIED)
    _drive(c, "B", gb, bb, CycleState.VERIFIED)
    os.remove(ga)                                              # break A only
    c2 = _open(tmp_path)
    ra = _reconstruct(c2, "A")
    rb = _reconstruct(c2, "B")
    assert ra.status == RecoveryStatus.MISSING_SOURCE          # A fails
    assert rb.status == RecoveryStatus.RECONSTRUCTED_MATCH     # B unaffected
    assert rb.usable_session.ctx["paths"]["GED"] == gb         # B keeps its own path, not A's


def test_manager_install_rejects_wrong_cycle_session():
    mgr = ReviewWorkingSetManager()
    with pytest.raises(ValueError):
        mgr.install("A", ReviewSession("B"))                   # no cross-cycle install


def test_failed_reconstruction_leaves_cached_working_set_untouched(tmp_path):
    c = _open(tmp_path)
    ged, bud = _files(tmp_path)
    _drive(c, "A", ged, bud, CycleState.VERIFIED)
    c2 = _open(tmp_path)
    mgr = ReviewWorkingSetManager()
    svc = _svc(c2)
    good = svc.reconstruct(svc.load_inputs("A"))
    mgr.install("A", good.usable_session)                      # valid cached working set
    cached = mgr.get("A").session
    os.remove(ged)
    result = svc.reconstruct(svc.load_inputs("A"))             # now fails
    assert result.status == RecoveryStatus.MISSING_SOURCE
    assert result.usable_session is None                       # nothing to install
    assert mgr.get("A").session is cached                      # build-then-swap: cache untouched


# ============================ fake-engine unit harness (exotic branches) ============================
class _FakeHasher:
    def __init__(self, mapping, raise_for=()):
        self._m = mapping            # path -> sha256 (or None => not exists)
        self._raise = set(raise_for)

    def probe(self, path):
        if path in self._raise:
            raise IOError("unreadable")
        sha = self._m.get(path)
        return {"exists": sha is not None, "sha256": sha, "size": 1, "name": os.path.basename(path)}


class _FakeEngine:
    def __init__(self, hasher, extract_result=None):
        self.hasher = hasher
        self._extract = extract_result or {"available": True, "readiness": {}, "reason": ""}

    def extract(self, ged, bud):
        return self._extract

    def build_provenance(self, cycle, ged, bud):
        return [], []       # candidate session provenance not needed for these branch tests


def _binding(doc, path, fp):
    from finsight.domain.lifecycle import SourceBinding
    return SourceBinding("A", doc, path, fp, "t", "actor")


def _inputs(state, bindings, vfp=None, ext=None, legacy=False):
    cycle = ReviewCycle("A", "May", "2026", state)
    return ReconstructionInputs(cycle, state, bindings, vfp, ext, legacy)


def test_unreadable_source_when_probe_raises():
    hasher = _FakeHasher({"/g": "x", "/b": "y"}, raise_for=("/g",))
    svc = ReviewReconstructionService(_FakeEngine(hasher), source_binding_repo=None)
    result = svc.reconstruct(_inputs(CycleState.VERIFIED,
                                     {"GED": _binding("GED", "/g", "x"), "BUDGET": _binding("BUDGET", "/b", "y")}))
    assert result.status == RecoveryStatus.UNREADABLE_SOURCE and result.document_type == "GED"


def test_extraction_failed_when_bytes_match_but_extract_unavailable():
    hasher = _FakeHasher({"/g": "x", "/b": "y"})
    engine = _FakeEngine(hasher, extract_result={"available": False, "reason": "corrupt", "readiness": {}})
    svc = ReviewReconstructionService(engine, source_binding_repo=None)
    result = svc.reconstruct(_inputs(CycleState.VERIFIED,
                                     {"GED": _binding("GED", "/g", "x"), "BUDGET": _binding("BUDGET", "/b", "y")}))
    assert result.status == RecoveryStatus.EXTRACTION_FAILED


def test_missing_binding_when_no_bindings():
    svc = ReviewReconstructionService(_FakeEngine(_FakeHasher({})), source_binding_repo=None)
    result = svc.reconstruct(_inputs(CycleState.PROCESSED, {}))
    assert result.status == RecoveryStatus.MISSING_BINDING


def test_legacy_incomplete_when_flagged_and_no_binding():
    svc = ReviewReconstructionService(_FakeEngine(_FakeHasher({})), source_binding_repo=None)
    result = svc.reconstruct(_inputs(CycleState.ANALYZED, {}, legacy=True))
    assert result.status == RecoveryStatus.LEGACY_METADATA_INCOMPLETE
    assert result.message.remains_valid                        # history remains viewable


def test_processed_rejected_review_reconstructs_without_vds():
    hasher = _FakeHasher({"/g": "x", "/b": "y"})
    engine = _FakeEngine(hasher, extract_result={"available": False, "reason": "not ready",
                                                 "readiness": {"Budget Analysis": "Unavailable"}})
    svc = ReviewReconstructionService(engine, source_binding_repo=None)
    result = svc.reconstruct(_inputs(CycleState.PROCESSED,
                                     {"GED": _binding("GED", "/g", "x"), "BUDGET": _binding("BUDGET", "/b", "y")}))
    # a PROCESSED (not verified) review that was rejected rebuilds its rejected preview, not a failure
    assert result.status == RecoveryStatus.RECONSTRUCTED_MATCH
    assert result.usable_session.ctx["rejected"] == "not ready"


def test_messages_carry_no_full_paths_or_raw_fingerprints():
    hasher = _FakeHasher({"/secret/home/user/g.xlsx": None, "/b": "y"})
    svc = ReviewReconstructionService(_FakeEngine(hasher), source_binding_repo=None)
    result = svc.reconstruct(_inputs(
        CycleState.VERIFIED,
        {"GED": _binding("GED", "/secret/home/user/g.xlsx", "x"), "BUDGET": _binding("BUDGET", "/b", "y")}))
    blob = " ".join(vars(result.message).values())
    assert "/secret/home/user" not in blob                     # no full path leaked
    assert result.filename == "g.xlsx"                          # basename only
