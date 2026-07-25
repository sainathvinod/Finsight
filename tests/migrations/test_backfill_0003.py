# Verifies: Phase 6.4b — deterministic, honest legacy backfill (ADR-011 §7 / Phase 6.3A). Legacy
# reviews are upgraded WITHOUT fabricating a verifier, a timestamp, a source binding, or a generation
# where no usable fingerprint exists. Repeated execution never duplicates a generation/run/finding.
import os
import sqlite3
import tempfile

from finsight.infrastructure.migrations.runner import run_migrations
from finsight.infrastructure.migrations import m0001_baseline, m0002_ai_platform, m0003_review_lifecycle


def v2_db():
    """A pre-lifecycle (v2) database with the original 4-col cycles / 10-col findings / 6-col runs."""
    conn = sqlite3.connect(os.path.join(tempfile.mkdtemp(), "fs.db"))
    conn.execute("PRAGMA foreign_keys=ON")
    run_migrations(conn, migrations=[(1, "baseline", m0001_baseline.up),
                                     (2, "ai_platform", m0002_ai_platform.up)])
    return conn


def add_cycle(conn, cid, state):
    conn.execute("INSERT INTO cycles VALUES(?,?,?,?)", (cid, "May", "2026", state))


def add_run(conn, run_id, cid, fp="src-fp"):
    conn.execute("INSERT INTO rule_runs VALUES(?,?,?,?,?,?)", (run_id, cid, "R1", "C1", fp, 1))


def add_finding(conn, fid, cid):
    conn.execute("INSERT INTO findings VALUES(?,?,?,?,?,?,?,?,?,?)",
                 (fid, cid, "R-BUD-02", "High", "May 2026", "6100", "over-budget",
                  '{"variance":"3000.00"}', '["GED!6100"]', "New"))


def add_verify_audit(conn, cid, actor="local-user", ts="2026-05-01T00:00:00Z"):
    conn.execute("INSERT INTO audit(cycle_id,action,actor,ts,detail) VALUES(?,?,?,?,?)",
                 (cid, "verify", actor, ts, "{}"))


def upgrade(conn):
    run_migrations(conn)   # applies v3 + backfill
    return conn


def gen_of(conn, cid):
    return conn.execute(
        "SELECT generation_id,sequence_number,analytical_state,creation_reason,verified_fingerprint,"
        "verification_actor,verified_at,legacy_metadata_incomplete FROM review_generations "
        "WHERE cycle_id=?", (cid,)).fetchone()


def pointers(conn, cid):
    return conn.execute("SELECT intake_stage,disposition,working_generation_id,published_generation_id "
                        "FROM cycles WHERE cycle_id=?", (cid,)).fetchone()


# ---- analyzed / exported with complete metadata ----------------------------------------------
def test_analyzed_review_complete_metadata():
    conn = v2_db()
    add_cycle(conn, "A", "Analyzed"); add_run(conn, "run-A", "A"); add_finding(conn, "f-A", "A")
    add_verify_audit(conn, "A", actor="reviewer-x", ts="2026-05-02T00:00:00Z")
    upgrade(conn)
    g = gen_of(conn, "A")
    assert g[0] == "gen-A-1" and g[1] == 1 and g[2] == "ANALYZED" and g[3] == "INITIAL_VERIFICATION"
    assert g[4] == "src-fp"                       # verified fingerprint = the run's recorded fingerprint
    assert g[5] == "reviewer-x" and g[6] == "2026-05-02T00:00:00Z" and g[7] == 0  # complete, honest
    intake, disp, working, published = pointers(conn, "A")
    assert intake == "PROCESSED" and disp == "Active"
    assert working == "gen-A-1" and published == "gen-A-1"          # first generation auto-published
    assert conn.execute("SELECT generation_id FROM rule_runs WHERE run_id='run-A'").fetchone()[0] == "gen-A-1"
    assert conn.execute("SELECT generation_id FROM findings WHERE id='f-A'").fetchone()[0] == "gen-A-1"


def test_exported_review_maps_to_exported_state():
    conn = v2_db()
    add_cycle(conn, "E", "Exported"); add_run(conn, "run-E", "E"); add_verify_audit(conn, "E")
    upgrade(conn)
    assert gen_of(conn, "E")[2] == "EXPORTED"


# ---- honest incompleteness -------------------------------------------------------------------
def test_missing_verification_actor_marked_incomplete():
    conn = v2_db()
    add_cycle(conn, "A", "Analyzed"); add_run(conn, "run-A", "A")   # NO verify audit event
    upgrade(conn)
    g = gen_of(conn, "A")
    assert g[5] == m0003_review_lifecycle.LEGACY_VERIFICATION_ACTOR    # honest marker, not a human name
    assert g[6] is None and g[7] == 1                                 # no timestamp; incomplete flagged


def test_missing_verification_timestamp_marked_incomplete():
    conn = v2_db()
    add_cycle(conn, "A", "Analyzed"); add_run(conn, "run-A", "A")
    add_verify_audit(conn, "A", actor="reviewer-x", ts=None)          # actor present, timestamp missing
    upgrade(conn)
    g = gen_of(conn, "A")
    assert g[5] == "reviewer-x" and g[6] is None and g[7] == 1        # real actor kept; incomplete flagged


def test_missing_fingerprint_creates_no_generation_but_retains_findings():
    conn = v2_db()
    add_cycle(conn, "A", "Analyzed"); add_run(conn, "run-A", "A", fp="")  # unusable fingerprint
    add_finding(conn, "f-A", "A")
    upgrade(conn)
    assert gen_of(conn, "A") is None                                 # no fabricated generation
    assert conn.execute("SELECT COUNT(*) FROM findings WHERE cycle_id='A'").fetchone()[0] == 1  # retained
    diag = conn.execute("SELECT code FROM migration_diagnostics WHERE cycle_id='A'").fetchone()
    assert diag and diag[0] == "legacy_generation_not_backfilled"    # honestly recorded


def test_no_runs_at_all_creates_no_generation():
    conn = v2_db()
    add_cycle(conn, "A", "Analyzed"); add_finding(conn, "f-A", "A")  # findings but no run
    upgrade(conn)
    assert gen_of(conn, "A") is None
    assert conn.execute("SELECT COUNT(*) FROM migration_diagnostics WHERE cycle_id='A'").fetchone()[0] == 1


# ---- pre-analysis ----------------------------------------------------------------------------
def test_pre_analysis_reviews_get_intake_stage_no_generation():
    conn = v2_db()
    add_cycle(conn, "c1", "Created")
    add_cycle(conn, "c2", "Intake")
    add_cycle(conn, "c3", "Processed")
    add_cycle(conn, "c4", "Verified")
    upgrade(conn)
    assert pointers(conn, "c1")[0] == "CREATED"
    assert pointers(conn, "c2")[0] == "SOURCE_BOUND"
    assert pointers(conn, "c3")[0] == "PROCESSED"
    assert pointers(conn, "c4")[0] == "PROCESSED"                    # verified candidate was processed
    for c in ("c1", "c2", "c3", "c4"):
        assert gen_of(conn, c) is None
        assert pointers(conn, c)[1] == "Active"
    assert conn.execute("SELECT COUNT(*) FROM source_bindings").fetchone()[0] == 0  # none fabricated


# ---- multiple reviews / multiple runs --------------------------------------------------------
def test_multiple_reviews_backfilled_independently():
    conn = v2_db()
    add_cycle(conn, "A", "Analyzed"); add_run(conn, "run-A", "A"); add_verify_audit(conn, "A")
    add_cycle(conn, "B", "Exported"); add_run(conn, "run-B", "B"); add_verify_audit(conn, "B")
    add_cycle(conn, "C", "Created")
    upgrade(conn)
    assert gen_of(conn, "A")[2] == "ANALYZED"
    assert gen_of(conn, "B")[2] == "EXPORTED"
    assert gen_of(conn, "C") is None


def test_multiple_runs_attaches_exactly_one_and_all_findings():
    conn = v2_db()
    add_cycle(conn, "A", "Analyzed")
    add_run(conn, "run-1", "A", fp="fp1")
    add_run(conn, "run-2", "A", fp="fp2")
    add_finding(conn, "f-1", "A"); add_finding(conn, "f-2", "A")
    upgrade(conn)
    attached = conn.execute("SELECT run_id FROM rule_runs WHERE generation_id='gen-A-1' ORDER BY run_id").fetchall()
    assert attached == [("run-1",)]                                 # deterministic: lowest run_id only
    assert conn.execute("SELECT generation_id FROM rule_runs WHERE run_id='run-2'").fetchone()[0] is None
    # all cycle findings attach to the single backfilled generation
    assert conn.execute("SELECT COUNT(*) FROM findings WHERE generation_id='gen-A-1'").fetchone()[0] == 2


# ---- determinism / idempotency ---------------------------------------------------------------
def test_repeat_backfill_is_idempotent():
    conn = v2_db()
    add_cycle(conn, "A", "Analyzed"); add_run(conn, "run-A", "A"); add_finding(conn, "f-A", "A")
    add_verify_audit(conn, "A")
    upgrade(conn)
    before = gen_of(conn, "A")
    m0003_review_lifecycle.backfill(conn, "2099-01-01T00:00:00Z")   # run again
    assert conn.execute("SELECT COUNT(*) FROM review_generations").fetchone()[0] == 1  # no duplicate
    assert gen_of(conn, "A") == before                             # unchanged (incl. created_at)


def test_backfill_changes_no_financial_values():
    conn = v2_db()
    add_cycle(conn, "A", "Analyzed"); add_run(conn, "run-A", "A"); add_finding(conn, "f-A", "A")
    upgrade(conn)
    ev = conn.execute("SELECT evidence FROM findings WHERE id='f-A'").fetchone()[0]
    assert "3000.00" in ev                                          # Decimal-as-text untouched
