# Verifies: Phase 6.4b — migration 0003 structure + database-enforced lifecycle invariants
# (ADR-011/012/014/015). These tests hit the DATABASE directly (raw SQL) to prove the schema, CHECK
# constraints, and triggers reject illegal state; repository-level rejection is covered separately.
import os
import sqlite3
import tempfile

import pytest

from finsight.infrastructure.migrations.runner import run_migrations, current_version

NEW_TABLES = {"source_bindings", "review_generations", "generation_supersessions",
              "export_artifacts", "migration_diagnostics"}
GEN_COLS = ("generation_id,cycle_id,sequence_number,analytical_state,creation_reason,"
            "based_on_generation_id,verification_basis_generation_id,verified_fingerprint,"
            "extractor_version,verification_actor,verified_at,created_by,created_at,"
            "generation_disposition,legacy_metadata_incomplete")


def head_db():
    conn = sqlite3.connect(os.path.join(tempfile.mkdtemp(), "fs.db"))
    conn.execute("PRAGMA foreign_keys=ON")
    run_migrations(conn)
    return conn


def add_cycle(conn, cid, state="Analyzed"):
    conn.execute("INSERT INTO cycles(cycle_id,month,year,state) VALUES(?,?,?,?)", (cid, "M", "2026", state))


def add_gen(conn, gid, cid, seq=1, state="ANALYZED", reason="INITIAL_VERIFICATION",
            based_on=None, basis=None, disposition="active"):
    conn.execute("INSERT INTO review_generations(%s) VALUES(%s)" % (GEN_COLS, ",".join("?" * 15)),
                 (gid, cid, seq, state, reason, based_on, basis, "fp", None, "actor",
                  "2026-01-01", "by", "2026-01-01", disposition, 0))


def add_run(conn, run_id, cid, gen=None):
    conn.execute("INSERT INTO rule_runs(run_id,cycle_id,ruleset_version,config_version,input_fingerprint,"
                 "finding_count,generation_id) VALUES(?,?,?,?,?,?,?)",
                 (run_id, cid, "R1", "C1", "ifp", 0, gen))


def add_finding(conn, fid, cid, gen=None):
    conn.execute("INSERT INTO findings(id,cycle_id,rule_id,severity,period,account,finding_type,evidence,"
                 "source_refs,state,generation_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                 (fid, cid, "r", "High", "P", "6100", "t", "{}", "[]", "New", gen))


def add_export(conn, xid, cid, gen, run):
    conn.execute("INSERT INTO export_artifacts(export_id,cycle_id,generation_id,run_id,export_path,"
                 "export_fingerprint,created_at,actor) VALUES(?,?,?,?,?,?,?,?)",
                 (xid, cid, gen, run, "/x", "xfp", "2026-01-01", "actor"))


def add_supersession(conn, prior, succ, cid_reason="promoted"):
    conn.execute("INSERT INTO generation_supersessions(prior_generation_id,successor_generation_id,"
                 "superseded_at,actor,reason) VALUES(?,?,?,?,?)",
                 (prior, succ, "2026-01-01", "actor", cid_reason))


# ---- structure -------------------------------------------------------------------------------
def test_fresh_db_has_all_new_tables_and_head_version():
    conn = head_db()
    tabs = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert NEW_TABLES.issubset(tabs)
    assert current_version(conn) == 16


def test_additive_columns_present():
    conn = head_db()
    cyc = {r[1] for r in conn.execute("PRAGMA table_info(cycles)")}
    assert {"intake_stage", "disposition", "working_generation_id", "published_generation_id"} <= cyc
    assert "generation_id" in {r[1] for r in conn.execute("PRAGMA table_info(rule_runs)")}
    assert "generation_id" in {r[1] for r in conn.execute("PRAGMA table_info(findings)")}
    # extractor_version belongs on the GENERATION (ADR-011 §8), NOT redundantly on the run.
    assert "extractor_version" not in {r[1] for r in conn.execute("PRAGMA table_info(rule_runs)")}
    assert "extractor_version" in {r[1] for r in conn.execute("PRAGMA table_info(review_generations)")}


def test_repeat_migration_execution_is_idempotent():
    conn = head_db()
    assert run_migrations(conn) == []
    from finsight.infrastructure.migrations import m0003_review_lifecycle
    m0003_review_lifecycle.up(conn)   # direct re-run must not raise or duplicate
    assert conn.execute("SELECT COUNT(*) FROM review_generations").fetchone()[0] == 0


# ---- generation constraints ------------------------------------------------------------------
def test_duplicate_sequence_rejected():
    conn = head_db(); add_cycle(conn, "A")
    add_gen(conn, "g1", "A", seq=1)
    with pytest.raises(sqlite3.IntegrityError):
        add_gen(conn, "g2", "A", seq=1)


def test_cross_cycle_parent_rejected():
    conn = head_db(); add_cycle(conn, "A"); add_cycle(conn, "B")
    add_gen(conn, "a1", "A", seq=1)
    with pytest.raises(sqlite3.IntegrityError):
        add_gen(conn, "b1", "B", seq=1, based_on="a1")


def test_cross_cycle_verification_basis_rejected():
    conn = head_db(); add_cycle(conn, "A"); add_cycle(conn, "B")
    add_gen(conn, "a1", "A", seq=1)
    with pytest.raises(sqlite3.IntegrityError):
        add_gen(conn, "b1", "B", seq=1, reason="RULESET_REANALYSIS", basis="a1")


def test_self_parent_rejected():
    conn = head_db(); add_cycle(conn, "A")
    with pytest.raises(sqlite3.IntegrityError):
        add_gen(conn, "g1", "A", seq=1, based_on="g1")


def test_self_basis_rejected():
    conn = head_db(); add_cycle(conn, "A")
    with pytest.raises(sqlite3.IntegrityError):
        add_gen(conn, "g1", "A", seq=1, reason="RULESET_REANALYSIS", basis="g1")


def test_fresh_verification_with_basis_rejected():
    conn = head_db(); add_cycle(conn, "A"); add_gen(conn, "a1", "A", seq=1)
    with pytest.raises(sqlite3.IntegrityError):     # INITIAL_VERIFICATION must not carry a basis
        add_gen(conn, "a2", "A", seq=2, reason="INITIAL_VERIFICATION", basis="a1")


def test_reanalysis_without_basis_rejected():
    conn = head_db(); add_cycle(conn, "A")
    with pytest.raises(sqlite3.IntegrityError):     # re-analysis must identify a basis
        add_gen(conn, "a1", "A", seq=1, reason="RULESET_REANALYSIS", basis=None)


def test_reanalysis_with_same_cycle_basis_allowed():
    conn = head_db(); add_cycle(conn, "A")
    add_gen(conn, "a1", "A", seq=1)
    add_gen(conn, "a2", "A", seq=2, reason="RULESET_REANALYSIS", basis="a1")   # no raise
    assert conn.execute("SELECT COUNT(*) FROM review_generations WHERE cycle_id='A'").fetchone()[0] == 2


def test_invalid_enums_rejected():
    conn = head_db(); add_cycle(conn, "A")
    with pytest.raises(sqlite3.IntegrityError):
        add_gen(conn, "g1", "A", seq=1, state="BOGUS")
    with pytest.raises(sqlite3.IntegrityError):
        add_gen(conn, "g2", "A", seq=2, reason="BOGUS")
    with pytest.raises(sqlite3.IntegrityError):
        add_gen(conn, "g3", "A", seq=3, disposition="deleted")


def test_one_run_per_generation_enforced():
    conn = head_db(); add_cycle(conn, "A"); add_gen(conn, "g1", "A")
    add_run(conn, "run1", "A", gen="g1")
    with pytest.raises(sqlite3.IntegrityError):
        add_run(conn, "run2", "A", gen="g1")        # partial unique index


# ---- supersession constraints ----------------------------------------------------------------
def test_self_supersession_rejected():
    conn = head_db(); add_cycle(conn, "A"); add_gen(conn, "g1", "A")
    with pytest.raises(sqlite3.IntegrityError):
        add_supersession(conn, "g1", "g1")


def test_duplicate_supersession_of_prior_rejected():
    conn = head_db(); add_cycle(conn, "A")
    add_gen(conn, "g1", "A", seq=1); add_gen(conn, "g2", "A", seq=2); add_gen(conn, "g3", "A", seq=3)
    add_supersession(conn, "g1", "g2")
    with pytest.raises(sqlite3.IntegrityError):
        add_supersession(conn, "g1", "g3")          # prior superseded at most once (PK)


def test_cross_cycle_supersession_rejected():
    conn = head_db(); add_cycle(conn, "A"); add_cycle(conn, "B")
    add_gen(conn, "a1", "A", seq=1); add_gen(conn, "b1", "B", seq=1)
    with pytest.raises(sqlite3.IntegrityError):
        add_supersession(conn, "a1", "b1")


def test_non_increasing_sequence_supersession_rejected():
    conn = head_db(); add_cycle(conn, "A")
    add_gen(conn, "g1", "A", seq=1); add_gen(conn, "g2", "A", seq=2)
    with pytest.raises(sqlite3.IntegrityError):
        add_supersession(conn, "g2", "g1")          # successor sequence must be later


def test_supersession_is_append_only():
    conn = head_db(); add_cycle(conn, "A")
    add_gen(conn, "g1", "A", seq=1); add_gen(conn, "g2", "A", seq=2)
    add_supersession(conn, "g1", "g2")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE generation_supersessions SET actor='x' WHERE prior_generation_id='g1'")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM generation_supersessions WHERE prior_generation_id='g1'")


# ---- cycle pointer constraints ---------------------------------------------------------------
def test_pointer_to_other_cycle_generation_rejected():
    conn = head_db(); add_cycle(conn, "A"); add_cycle(conn, "B")
    add_gen(conn, "b1", "B", seq=1)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE cycles SET working_generation_id='b1' WHERE cycle_id='A'")


def test_published_pointer_to_superseded_generation_rejected():
    conn = head_db(); add_cycle(conn, "A")
    add_gen(conn, "g1", "A", seq=1); add_gen(conn, "g2", "A", seq=2)
    add_supersession(conn, "g1", "g2")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE cycles SET published_generation_id='g1' WHERE cycle_id='A'")


# ---- finding/run + export agreement ----------------------------------------------------------
def test_finding_without_matching_run_generation_rejected():
    conn = head_db(); add_cycle(conn, "A"); add_gen(conn, "g1", "A")
    with pytest.raises(sqlite3.IntegrityError):
        add_finding(conn, "f1", "A", gen="g1")       # no run carries g1 in cycle A


def test_finding_with_matching_run_generation_allowed():
    conn = head_db(); add_cycle(conn, "A"); add_gen(conn, "g1", "A")
    add_run(conn, "run1", "A", gen="g1")
    add_finding(conn, "f1", "A", gen="g1")           # no raise
    assert conn.execute("SELECT generation_id FROM findings WHERE id='f1'").fetchone()[0] == "g1"


def test_export_disagreement_rejected():
    conn = head_db(); add_cycle(conn, "A"); add_cycle(conn, "B")
    add_gen(conn, "g1", "A"); add_run(conn, "run1", "A", gen="g1")
    with pytest.raises(sqlite3.IntegrityError):
        add_export(conn, "x1", "B", "g1", "run1")    # cycle B disagrees with generation g1's cycle A


def test_export_is_append_only():
    conn = head_db(); add_cycle(conn, "A"); add_gen(conn, "g1", "A"); add_run(conn, "run1", "A", gen="g1")
    add_export(conn, "x1", "A", "g1", "run1")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE export_artifacts SET export_path='/y' WHERE export_id='x1'")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM export_artifacts WHERE export_id='x1'")


# ---- source binding --------------------------------------------------------------------------
def test_duplicate_source_binding_pk_rejected():
    conn = head_db(); add_cycle(conn, "A")

    def ins():
        conn.execute("INSERT INTO source_bindings(cycle_id,document_type,last_known_path,"
                     "source_fingerprint,selected_at,actor) VALUES('A','ged','/p','fp','t','a')")
    ins()
    with pytest.raises(sqlite3.IntegrityError):
        ins()
