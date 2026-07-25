# Verifies: Phase 6.4b — lifecycle repositories (ADR-011/012/015). Round trips, ordering, next
# sequence, append-only behavior, legacy nullable readability, enum validation, and — critically —
# EXPLICIT transaction composition without premature commit (a later promotion service must be able to
# append supersession + move the published pointer + append audit atomically in ONE UnitOfWork).
import os
import tempfile

import pytest

from finsight.domain.lifecycle import (
    SourceBinding, ReviewGeneration, GenerationSupersession, ExportArtifact,
    IntakeStage, CycleDisposition,
)
from finsight.infrastructure.persistence import (
    Dal, SqliteUnitOfWork, ReviewCycleRepoSqlite, RuleRunRepoSqlite,
)
from finsight.infrastructure.audit import AuditStoreSqlite
from finsight.infrastructure.lifecycle_repositories import (
    SourceBindingRepoSqlite, ReviewGenerationRepoSqlite, GenerationSupersessionRepoSqlite,
    ExportArtifactRepoSqlite, CycleLifecycleRepoSqlite, LifecycleConstraintError,
)
from finsight.domain.review_cycle import ReviewCycle, CycleState
from tests.support import FixedClock


def _dal():
    return Dal(os.path.join(tempfile.mkdtemp(), "fs.db"))


def _gen(gid, cid, seq, reason="INITIAL_VERIFICATION", basis=None, state="ANALYZED"):
    return ReviewGeneration(
        generation_id=gid, cycle_id=cid, sequence_number=seq, analytical_state=state,
        creation_reason=reason, based_on_generation_id=None, verification_basis_generation_id=basis,
        verified_fingerprint="fp", extractor_version="x1", verification_actor="rev",
        verified_at="2026-01-01", created_by="by", created_at="2026-01-01")


def _seed_cycle(dal, cid):
    with SqliteUnitOfWork(dal).atomic():
        ReviewCycleRepoSqlite(dal).save(ReviewCycle(cid, "May", "2026", CycleState.ANALYZED))


# ---- source binding --------------------------------------------------------------------------
def test_source_binding_round_trip_and_upsert():
    dal = _dal(); _seed_cycle(dal, "A")
    repo = SourceBindingRepoSqlite(dal)
    with SqliteUnitOfWork(dal).atomic():
        repo.upsert(SourceBinding("A", "ged", "/p1", "fp1", "t1", "actor"))
    assert repo.get("A", "ged").last_known_path == "/p1"
    with SqliteUnitOfWork(dal).atomic():
        repo.upsert(SourceBinding("A", "ged", "/p2", "fp2", "t2", "actor"))   # same key -> update
    assert repo.get("A", "ged").source_fingerprint == "fp2"
    assert len(repo.list_for_cycle("A")) == 1


# ---- generations -----------------------------------------------------------------------------
def test_generation_round_trip_ordering_and_next_sequence():
    dal = _dal(); _seed_cycle(dal, "A")
    repo = ReviewGenerationRepoSqlite(dal)
    assert repo.next_sequence_number("A") == 1
    with SqliteUnitOfWork(dal).atomic():
        repo.insert(_gen("g1", "A", 1))
        repo.insert(_gen("g2", "A", 2, reason="RULESET_REANALYSIS", basis="g1"))
    got = repo.get("g1")
    assert got.generation_id == "g1" and got.verified_fingerprint == "fp" and got.extractor_version == "x1"
    assert [g.generation_id for g in repo.list_for_cycle("A")] == ["g1", "g2"]   # by sequence
    assert repo.next_sequence_number("A") == 3


def test_generation_cross_cycle_basis_raises_constraint_error():
    dal = _dal(); _seed_cycle(dal, "A"); _seed_cycle(dal, "B")
    repo = ReviewGenerationRepoSqlite(dal)
    with SqliteUnitOfWork(dal).atomic():
        repo.insert(_gen("a1", "A", 1))
    with pytest.raises(LifecycleConstraintError):
        with SqliteUnitOfWork(dal).atomic():
            repo.insert(_gen("b1", "B", 1, reason="RULESET_REANALYSIS", basis="a1"))


def test_working_and_published_generation_via_pointers():
    dal = _dal(); _seed_cycle(dal, "A")
    gens = ReviewGenerationRepoSqlite(dal); cyc = CycleLifecycleRepoSqlite(dal)
    with SqliteUnitOfWork(dal).atomic():
        gens.insert(_gen("g1", "A", 1))
        cyc.set_working_generation("A", "g1")
        cyc.set_published_generation("A", "g1")
    assert gens.working_generation("A").generation_id == "g1"
    assert gens.published_generation("A").generation_id == "g1"


def test_cycle_lifecycle_stage_and_disposition_enum_validation():
    dal = _dal(); _seed_cycle(dal, "A")
    cyc = CycleLifecycleRepoSqlite(dal)
    with SqliteUnitOfWork(dal).atomic():
        cyc.set_intake_stage("A", IntakeStage.PROCESSED)
        cyc.set_disposition("A", CycleDisposition.ABANDONED)
    assert cyc.pointers("A")[0] == "PROCESSED" and cyc.pointers("A")[1] == "Abandoned"
    with pytest.raises(ValueError):
        cyc.set_intake_stage("A", "NOT_A_STAGE")


# ---- supersession (append-only) --------------------------------------------------------------
def test_supersession_append_get_and_double_supersede_rejected():
    dal = _dal(); _seed_cycle(dal, "A")
    gens = ReviewGenerationRepoSqlite(dal); sup = GenerationSupersessionRepoSqlite(dal)
    with SqliteUnitOfWork(dal).atomic():
        gens.insert(_gen("g1", "A", 1)); gens.insert(_gen("g2", "A", 2)); gens.insert(_gen("g3", "A", 3))
    with SqliteUnitOfWork(dal).atomic():
        sup.append(GenerationSupersession("g1", "g2", "t", "actor", "promoted"))
    assert sup.get_successor("g1").successor_generation_id == "g2"
    assert [s.prior_generation_id for s in sup.history_for_cycle("A")] == ["g1"]
    with pytest.raises(LifecycleConstraintError):
        with SqliteUnitOfWork(dal).atomic():
            sup.append(GenerationSupersession("g1", "g3", "t", "actor", "again"))
    assert not hasattr(sup, "update") and not hasattr(sup, "delete")   # append-only API


# ---- export (append-only) --------------------------------------------------------------------
def test_export_artifact_round_trip_and_listing():
    dal = _dal(); _seed_cycle(dal, "A")
    gens = ReviewGenerationRepoSqlite(dal); runs = RuleRunRepoSqlite(dal); exp = ExportArtifactRepoSqlite(dal)
    with SqliteUnitOfWork(dal).atomic():
        gens.insert(_gen("g1", "A", 1))
        runs.save({"run_id": "run1", "cycle_id": "A", "ruleset_version": "R", "config_version": "C",
                   "input_fingerprint": "ifp", "finding_count": 0})
        dal.conn.execute("UPDATE rule_runs SET generation_id='g1' WHERE run_id='run1'")
        exp.insert(ExportArtifact("x1", "A", "g1", "run1", "/x", "xfp", "t", "actor"))
    assert exp.get("x1").export_fingerprint == "xfp"
    assert [a.export_id for a in exp.list_for_generation("g1")] == ["x1"]
    assert [a.export_id for a in exp.list_for_cycle("A")] == ["x1"]
    assert not hasattr(exp, "update")


# ---- legacy nullable readability -------------------------------------------------------------
def test_legacy_null_generation_ids_remain_readable():
    dal = _dal(); _seed_cycle(dal, "A")
    with SqliteUnitOfWork(dal).atomic():
        RuleRunRepoSqlite(dal).save({"run_id": "run1", "cycle_id": "A", "ruleset_version": "R",
                                     "config_version": "C", "input_fingerprint": "ifp", "finding_count": 0})
    # the legacy read path is unaffected by the added nullable generation_id column
    assert RuleRunRepoSqlite(dal).get_by_cycle("A")["run_id"] == "run1"
    assert dal.conn.execute("SELECT generation_id FROM rule_runs WHERE run_id='run1'").fetchone()[0] is None


# ---- transaction composition (no premature commit) -------------------------------------------
def test_repositories_do_not_commit_internally():
    dal = _dal(); _seed_cycle(dal, "A")
    ReviewGenerationRepoSqlite(dal).insert(_gen("g1", "A", 1))   # write WITHOUT a UnitOfWork commit
    dal.conn.rollback()                                          # a repo that self-committed would survive
    assert ReviewGenerationRepoSqlite(dal).get("g1") is None


def test_promotion_shaped_transaction_commits_atomically():
    dal = _dal(); _seed_cycle(dal, "A")
    gens = ReviewGenerationRepoSqlite(dal); sup = GenerationSupersessionRepoSqlite(dal)
    cyc = CycleLifecycleRepoSqlite(dal); audit = AuditStoreSqlite(dal, FixedClock())
    with SqliteUnitOfWork(dal).atomic():
        gens.insert(_gen("g1", "A", 1)); gens.insert(_gen("g2", "A", 2))
        cyc.set_published_generation("A", "g1")
    # One transaction: supersede g1 -> publish g2 -> audit, atomically (promotion SHAPE, not the service)
    with SqliteUnitOfWork(dal).atomic():
        sup.append(GenerationSupersession("g1", "g2", "t", "actor", "promotion"))
        cyc.set_published_generation("A", "g2")
        audit.emit("A", "generation_promoted", "actor", {"from": "g1", "to": "g2"})
    assert gens.published_generation("A").generation_id == "g2"
    assert sup.get_successor("g1").successor_generation_id == "g2"
    assert "generation_promoted" in audit.timeline("A")


def test_failed_composed_transaction_rolls_back_all():
    dal = _dal(); _seed_cycle(dal, "A")
    gens = ReviewGenerationRepoSqlite(dal); sup = GenerationSupersessionRepoSqlite(dal)
    cyc = CycleLifecycleRepoSqlite(dal)
    with SqliteUnitOfWork(dal).atomic():
        gens.insert(_gen("g1", "A", 1)); gens.insert(_gen("g2", "A", 2))
        cyc.set_published_generation("A", "g1")
    with pytest.raises(RuntimeError):
        with SqliteUnitOfWork(dal).atomic():
            sup.append(GenerationSupersession("g1", "g2", "t", "actor", "promotion"))
            cyc.set_published_generation("A", "g2")
            raise RuntimeError("boom before commit")
    assert gens.published_generation("A").generation_id == "g1"      # pointer unchanged
    assert sup.get_successor("g1") is None                           # supersession rolled back
