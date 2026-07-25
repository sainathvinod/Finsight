# Verifies: Phase 6.4cA BLOCKER 1 — verification persists its complete verification basis by creating
# the WORKING generation at analytical_state=VERIFIED, atomically. A VERIFIED-only review is therefore
# as reproducible + integrity-checked as an ANALYZED one: restart rebuilds the verified dataset and
# proves it equals the certified one, failing loudly on any drift.
import os

import pytest

from finsight.app import build_app, build_query_services
from finsight.application.review_session import ReviewSession
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.reconstruction import RecoveryStatus
from finsight.application.errors import PersistenceError
from finsight.infrastructure.lifecycle_repositories import ReviewGenerationRepoSqlite
from finsight.delivery.desktop.controllers import AppController
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def _files(tmp_path, tag=""):
    g = os.path.join(str(tmp_path), "ged%s.xlsx" % tag); b = os.path.join(str(tmp_path), "bud%s.xlsx" % tag)
    build_synthetic_ged(g); build_synthetic_budget(b); return g, b


def _verify_only(db, cid, ged, bud):
    c = build_app(db, FixedClock()); wf = ReviewWorkflowService(c.orch.engine)
    wf.create_review(cid, "May", "2026"); s = ReviewSession(cid)
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s)
    c.dal.conn.close()


def test_initial_verification_creates_working_generation_with_full_basis(tmp_path):
    db = str(tmp_path / "fs.db"); ged, bud = _files(tmp_path)
    _verify_only(db, "A", ged, bud)
    c = build_app(db, FixedClock())
    gens = ReviewGenerationRepoSqlite(c.dal).list_for_cycle("A")
    assert len(gens) == 1
    g = gens[0]
    assert g.analytical_state.value == "VERIFIED"
    assert g.creation_reason.value == "INITIAL_VERIFICATION"
    assert g.verified_fingerprint and g.extractor_version == "extractor-v1"
    assert g.verification_actor == "local-user" and g.verified_at        # honest human approval fact
    assert g.verification_basis_generation_id is None                    # fresh verification
    # working pointer set; NOT published; no supersession (no promotion this phase)
    intake, disp, working, published = c.cycle_lifecycle_repo.pointers("A")
    assert working == g.generation_id and published is None
    assert c.dal.conn.execute("SELECT COUNT(*) FROM generation_supersessions").fetchone()[0] == 0


def test_verified_only_restart_reconstructs_and_matches(tmp_path):
    db = str(tmp_path / "fs.db"); ged, bud = _files(tmp_path)
    _verify_only(db, "A", ged, bud)
    c = AppController(build_query_services(db))          # fresh process
    r = c.reconstruct_sync("A")
    assert r.status == RecoveryStatus.RECONSTRUCTED_MATCH  # basis check passes for matching source
    assert c.workflow_state("A") == "Verified"


def test_verified_only_restart_detects_dataset_mismatch_and_blocks_analysis(tmp_path):
    db = str(tmp_path / "fs.db"); ged, bud = _files(tmp_path)
    _verify_only(db, "A", ged, bud)
    # simulate certified data no longer reproducible (e.g. hidden extractor drift): tamper the recorded
    # verified-dataset fingerprint so the rebuilt dataset cannot match.
    con = build_app(db, FixedClock())
    with con.uow.atomic():
        con.dal.conn.execute("UPDATE review_generations SET verified_fingerprint='deadbeef' WHERE cycle_id='A'")
    con.dal.conn.close()
    c = AppController(build_query_services(db))
    r = c.reconstruct_sync("A")
    assert r.status == RecoveryStatus.VERIFIED_DATA_MISMATCH
    assert not c.has_working_set("A")                    # no working set installed -> analysis blocked
    assert c.workflow_state("A") == "Verified"           # state + prior records unchanged


def test_extractor_version_mismatch_classified_distinctly_via_generation(tmp_path):
    db = str(tmp_path / "fs.db"); ged, bud = _files(tmp_path)
    _verify_only(db, "A", ged, bud)
    con = build_app(db, FixedClock())
    with con.uow.atomic():
        con.dal.conn.execute("UPDATE review_generations SET extractor_version='extractor-OLD', "
                             "verified_fingerprint='deadbeef' WHERE cycle_id='A'")
    con.dal.conn.close()
    c = AppController(build_query_services(db))
    assert c.reconstruct_sync("A").status == RecoveryStatus.EXTRACTOR_VERSION_MISMATCH


def test_verification_is_atomic_generation_write_failure_rolls_back(tmp_path):
    db = str(tmp_path / "fs.db"); ged, bud = _files(tmp_path)
    c = build_app(db, FixedClock()); wf = ReviewWorkflowService(c.orch.engine)
    wf.create_review("A", "May", "2026"); s = ReviewSession("A")
    wf.upload(s, ged, bud); wf.process(s)
    # inject a fault in the generation write; the whole do_verified transaction must roll back
    c.orch.engine.review_generation_repo.insert = lambda g: (_ for _ in ()).throw(RuntimeError("boom"))
    with pytest.raises(PersistenceError):
        wf.verify(s)
    assert wf.state("A") == "Processed"                  # NOT advanced to Verified
    assert ReviewGenerationRepoSqlite(c.dal).list_for_cycle("A") == []   # no half-created generation
    assert c.cycle_lifecycle_repo.pointers("A")[2] is None              # no working pointer


def test_legacy_analyzed_review_not_double_generation(tmp_path):
    # A review already ANALYZED never re-enters do_verified (resume-gated), so no extra generation.
    db = str(tmp_path / "fs.db"); ged, bud = _files(tmp_path)
    c = build_app(db, FixedClock()); wf = ReviewWorkflowService(c.orch.engine)
    wf.create_review("A", "May", "2026"); s = ReviewSession("A")
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s); wf.analyze(s)
    assert len(ReviewGenerationRepoSqlite(c.dal).list_for_cycle("A")) == 1   # exactly one
