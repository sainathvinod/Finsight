# Implements: ADR-011 (lifecycle/generation), ADR-012 (source binding), ADR-014 (abandonment),
# ADR-015 (export identity), Phase 6.3A/6.3B corrections. Phase 6.4b — ADDITIVE lifecycle persistence
# ONLY. This migration creates the schema and honestly backfills legacy reviews; it does NOT wire any
# production workflow to write these tables (no source-binding-on-upload, no generation-on-verify, no
# promotion/supersession, no reconstruction, no restart recovery — those are Phase 6.4c+).
#
# Additive + idempotent: new tables/indexes/triggers use IF NOT EXISTS; ALTERs are guarded by
# PRAGMA table_info; backfill uses deterministic IDs + INSERT OR IGNORE / guarded UPDATEs so repeated
# execution never duplicates a generation, finding, or run. No existing table is renamed or rewritten;
# no financial value is changed; no normalized workbook rows are ever persisted.
#
# CONSTRAINT/TRIGGER BOUNDARY (ADR-011 §9 request): STABLE STRUCTURAL invariants are enforced in the
# database (PRIMARY KEY / UNIQUE / CHECK / FK / partial-unique-index / narrow BEFORE-triggers). More
# complex SEMANTIC rules that need cross-row visibility are ALSO pre-validated in the repository layer
# for clear errors; the triggers are the authoritative backstop. Enum validation for the cycles.*
# columns added via ALTER (which cannot carry a CHECK in SQLite) is done in the repository.
from __future__ import annotations
import datetime
import sqlite3

VERSION = 3
NAME = "review_lifecycle"

# Analytical progression ranking, embedded as a frozen historical snapshot (migrations must not drift
# with the domain enum). Mirrors CycleState / STATE_ORDER at the time this migration was authored.
_STATE_RANK = {
    "Created": 0, "Intake": 1, "Validated": 1, "Processed": 2, "Verified": 3,
    "Analyzed": 4, "Summarized": 5, "Exported": 6,
}
_ANALYZED_RANK = _STATE_RANK["Analyzed"]

# Legacy state -> honest intake stage of the currently bound+extracted candidate (ADR-011 §7).
_INTAKE_FOR_STATE = {
    "Created": "CREATED", "Intake": "SOURCE_BOUND", "Validated": "SOURCE_BOUND",
    "Processed": "PROCESSED", "Verified": "PROCESSED",
    "Analyzed": "PROCESSED", "Summarized": "PROCESSED", "Exported": "PROCESSED",
}
# Analyzed+ state -> the generation's frozen analytical_state.
_ANALYTICAL_FOR_STATE = {"Analyzed": "ANALYZED", "Summarized": "SUMMARIZED", "Exported": "EXPORTED"}

LEGACY_VERIFICATION_ACTOR = "legacy-unknown"
LEGACY_BACKFILL_ACTOR = "legacy-backfill"


def _iso_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(r[1] == column for r in conn.execute("PRAGMA table_info(%s)" % table))


def _add_column(conn: sqlite3.Connection, table: str, column: str, coldef: str) -> None:
    if not _has_column(conn, table, column):
        conn.execute("ALTER TABLE %s ADD COLUMN %s" % (table, coldef))


def up(conn: sqlite3.Connection, clock=None) -> None:
    now = clock.now() if clock is not None else _iso_now()
    c = conn

    # ---- New authoritative tables (ADR-011/012/015) -----------------------------------------
    c.execute(
        "CREATE TABLE IF NOT EXISTS source_bindings("
        "cycle_id TEXT NOT NULL REFERENCES cycles(cycle_id), "
        "document_type TEXT NOT NULL, "
        "last_known_path TEXT NOT NULL, "
        "source_fingerprint TEXT NOT NULL, "
        "selected_at TEXT NOT NULL, "
        "actor TEXT NOT NULL, "
        "PRIMARY KEY(cycle_id, document_type))")   # one binding per cycle + authoritative doc type

    c.execute(
        "CREATE TABLE IF NOT EXISTS review_generations("
        "generation_id TEXT PRIMARY KEY, "
        "cycle_id TEXT NOT NULL REFERENCES cycles(cycle_id), "
        "sequence_number INTEGER NOT NULL, "
        "analytical_state TEXT NOT NULL CHECK(analytical_state IN "
        "('VERIFIED','ANALYZED','SUMMARIZED','EXPORTED')), "
        "creation_reason TEXT NOT NULL CHECK(creation_reason IN "
        "('INITIAL_VERIFICATION','SOURCE_REVERIFICATION','EXTRACTOR_REVERIFICATION',"
        "'RULESET_REANALYSIS','CONFIG_REANALYSIS')), "
        "based_on_generation_id TEXT REFERENCES review_generations(generation_id), "
        "verification_basis_generation_id TEXT REFERENCES review_generations(generation_id), "
        "verified_fingerprint TEXT, "
        "extractor_version TEXT, "                 # verification-basis property (ADR-011 §8), inherited
        "verification_actor TEXT, "
        "verified_at TEXT, "
        "created_by TEXT NOT NULL, "
        "created_at TEXT NOT NULL, "
        "generation_disposition TEXT NOT NULL DEFAULT 'active' "
        "CHECK(generation_disposition IN ('active','abandoned')), "
        "legacy_metadata_incomplete INTEGER NOT NULL DEFAULT 0 "
        "CHECK(legacy_metadata_incomplete IN (0,1)), "
        "UNIQUE(cycle_id, sequence_number), "
        "CHECK(based_on_generation_id IS NULL OR based_on_generation_id <> generation_id), "
        "CHECK(verification_basis_generation_id IS NULL OR "
        "verification_basis_generation_id <> generation_id), "
        # Verification-basis honesty: fresh verification carries no basis; re-analysis must have one.
        "CHECK("
        "(creation_reason IN ('INITIAL_VERIFICATION','SOURCE_REVERIFICATION','EXTRACTOR_REVERIFICATION')"
        " AND verification_basis_generation_id IS NULL) OR "
        "(creation_reason IN ('RULESET_REANALYSIS','CONFIG_REANALYSIS')"
        " AND verification_basis_generation_id IS NOT NULL)))")
    c.execute("CREATE INDEX IF NOT EXISTS idx_generations_cycle "
              "ON review_generations(cycle_id, sequence_number)")

    c.execute(
        "CREATE TABLE IF NOT EXISTS generation_supersessions("
        "prior_generation_id TEXT PRIMARY KEY REFERENCES review_generations(generation_id), "
        "successor_generation_id TEXT NOT NULL REFERENCES review_generations(generation_id), "
        "superseded_at TEXT NOT NULL, "
        "actor TEXT NOT NULL, "
        "reason TEXT NOT NULL, "
        "CHECK(prior_generation_id <> successor_generation_id))")  # prior superseded at most once (PK)

    c.execute(
        "CREATE TABLE IF NOT EXISTS export_artifacts("
        "export_id TEXT PRIMARY KEY, "
        "cycle_id TEXT NOT NULL REFERENCES cycles(cycle_id), "
        "generation_id TEXT NOT NULL REFERENCES review_generations(generation_id), "
        "run_id TEXT NOT NULL REFERENCES rule_runs(run_id), "
        "export_path TEXT NOT NULL, "
        "export_fingerprint TEXT NOT NULL, "
        "created_at TEXT NOT NULL, "
        "actor TEXT NOT NULL)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_export_generation ON export_artifacts(generation_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_export_cycle ON export_artifacts(cycle_id)")

    # Honest, append-only record of legacy reviews that could NOT be backfilled into a trustworthy
    # generation (no usable fingerprint). Never fabricates a generation; keeps results accessible.
    c.execute(
        "CREATE TABLE IF NOT EXISTS migration_diagnostics("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, migration TEXT NOT NULL, cycle_id TEXT, "
        "code TEXT NOT NULL, detail TEXT NOT NULL, created_ts TEXT NOT NULL)")

    # ---- Additive columns on existing tables (nullable / defaulted for legacy compatibility) ----
    _add_column(c, "cycles", "intake_stage", "intake_stage TEXT")
    _add_column(c, "cycles", "disposition", "disposition TEXT DEFAULT 'Active'")
    _add_column(c, "cycles", "working_generation_id",
                "working_generation_id TEXT REFERENCES review_generations(generation_id)")
    _add_column(c, "cycles", "published_generation_id",
                "published_generation_id TEXT REFERENCES review_generations(generation_id)")
    _add_column(c, "rule_runs", "generation_id",
                "generation_id TEXT REFERENCES review_generations(generation_id)")
    _add_column(c, "findings", "generation_id",
                "generation_id TEXT REFERENCES review_generations(generation_id)")
    # Exactly one rule run per generation (ADR-011 §8): partial unique index (NULLs unconstrained).
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_rule_runs_generation "
              "ON rule_runs(generation_id) WHERE generation_id IS NOT NULL")
    c.execute("CREATE INDEX IF NOT EXISTS idx_findings_generation ON findings(generation_id)")

    _create_triggers(c)
    backfill(c, now)


def _create_triggers(c: sqlite3.Connection) -> None:
    # Cross-row STRUCTURAL invariants that a column CHECK cannot express (they need other rows).
    # Each trigger is single-purpose and documented; RAISE(ABORT) surfaces as sqlite3.IntegrityError.

    # Lineage parent + verification basis must be same-cycle.
    c.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_generation_same_cycle_refs "
        "BEFORE INSERT ON review_generations FOR EACH ROW WHEN "
        "(NEW.based_on_generation_id IS NOT NULL AND "
        "(SELECT cycle_id FROM review_generations WHERE generation_id=NEW.based_on_generation_id) "
        "IS NOT NEW.cycle_id) OR "
        "(NEW.verification_basis_generation_id IS NOT NULL AND "
        "(SELECT cycle_id FROM review_generations WHERE generation_id=NEW.verification_basis_generation_id)"
        " IS NOT NEW.cycle_id) "
        "BEGIN SELECT RAISE(ABORT, 'generation parent/basis must belong to the same cycle'); END")

    # Supersession: same-cycle prior/successor with a strictly increasing sequence.
    c.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_supersession_validate "
        "BEFORE INSERT ON generation_supersessions FOR EACH ROW WHEN "
        "((SELECT cycle_id FROM review_generations WHERE generation_id=NEW.prior_generation_id) IS NOT "
        "(SELECT cycle_id FROM review_generations WHERE generation_id=NEW.successor_generation_id)) OR "
        "((SELECT sequence_number FROM review_generations WHERE generation_id=NEW.successor_generation_id)"
        " <= (SELECT sequence_number FROM review_generations WHERE generation_id=NEW.prior_generation_id)) "
        "BEGIN SELECT RAISE(ABORT, 'supersession must be same-cycle with an increasing sequence'); END")
    # Append-only.
    c.execute("CREATE TRIGGER IF NOT EXISTS trg_supersession_no_update BEFORE UPDATE ON "
              "generation_supersessions BEGIN SELECT RAISE(ABORT, "
              "'generation_supersessions is append-only'); END")
    c.execute("CREATE TRIGGER IF NOT EXISTS trg_supersession_no_delete BEFORE DELETE ON "
              "generation_supersessions BEGIN SELECT RAISE(ABORT, "
              "'generation_supersessions is append-only'); END")

    # Export: cycle/generation/run must agree (generation same-cycle; run belongs to that generation
    # and cycle).
    c.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_export_validate "
        "BEFORE INSERT ON export_artifacts FOR EACH ROW WHEN "
        "((SELECT cycle_id FROM review_generations WHERE generation_id=NEW.generation_id) IS NOT NEW.cycle_id)"
        " OR ((SELECT generation_id FROM rule_runs WHERE run_id=NEW.run_id) IS NOT NEW.generation_id) "
        "OR ((SELECT cycle_id FROM rule_runs WHERE run_id=NEW.run_id) IS NOT NEW.cycle_id) "
        "BEGIN SELECT RAISE(ABORT, 'export cycle/generation/run must agree'); END")
    # Append-only.
    c.execute("CREATE TRIGGER IF NOT EXISTS trg_export_no_update BEFORE UPDATE ON export_artifacts "
              "BEGIN SELECT RAISE(ABORT, 'export_artifacts is append-only'); END")
    c.execute("CREATE TRIGGER IF NOT EXISTS trg_export_no_delete BEFORE DELETE ON export_artifacts "
              "BEGIN SELECT RAISE(ABORT, 'export_artifacts is append-only'); END")

    # Cycle generation pointers must reference a same-cycle generation; a published pointer must not
    # reference a superseded prior generation.
    c.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_cycle_pointer_validate "
        "BEFORE UPDATE OF working_generation_id, published_generation_id ON cycles FOR EACH ROW WHEN "
        "(NEW.working_generation_id IS NOT NULL AND "
        "(SELECT cycle_id FROM review_generations WHERE generation_id=NEW.working_generation_id) "
        "IS NOT NEW.cycle_id) OR "
        "(NEW.published_generation_id IS NOT NULL AND "
        "(SELECT cycle_id FROM review_generations WHERE generation_id=NEW.published_generation_id) "
        "IS NOT NEW.cycle_id) OR "
        "(NEW.published_generation_id IS NOT NULL AND EXISTS(SELECT 1 FROM generation_supersessions "
        "WHERE prior_generation_id=NEW.published_generation_id)) "
        "BEGIN SELECT RAISE(ABORT, 'cycle generation pointer invalid (wrong cycle or superseded)'); END")

    # A finding's generation must have a matching rule run in the same cycle (findings⇒run⇒generation
    # consistency). Only fires when a generation_id is actually assigned.
    for verb, evt in (("ins", "INSERT"), ("upd", "UPDATE OF generation_id")):
        c.execute(
            "CREATE TRIGGER IF NOT EXISTS trg_finding_generation_%s "
            "BEFORE %s ON findings FOR EACH ROW WHEN NEW.generation_id IS NOT NULL AND NOT EXISTS("
            "SELECT 1 FROM rule_runs r WHERE r.generation_id=NEW.generation_id AND r.cycle_id=NEW.cycle_id) "
            "BEGIN SELECT RAISE(ABORT, "
            "'finding generation must have a matching rule run in the same cycle'); END"
            % (verb, evt))


def backfill(conn: sqlite3.Connection, now: str) -> None:
    """Deterministic, idempotent, HONEST legacy backfill (ADR-011 §7 / Phase 6.3A).

    - Every cycle receives an honest intake_stage + Active disposition.
    - ANALYZED+ cycles with a usable rule-run fingerprint get Generation 1 (INITIAL_VERIFICATION),
      auto-published; the chosen run and the cycle's findings attach to it.
    - ANALYZED+ cycles WITHOUT a usable fingerprint get NO generation (results retained) and an honest
      migration_diagnostics row.
    - Pre-analysis cycles get NO generation and NO fabricated source binding.
    - Never invents a verifier name or a precise verification timestamp; legacy_metadata_incomplete
      records the gap. Repeated execution creates no duplicate generation/run/finding attachment.
    """
    for cycle_id, state in conn.execute("SELECT cycle_id, state FROM cycles").fetchall():
        conn.execute("UPDATE cycles SET intake_stage=? WHERE cycle_id=? AND intake_stage IS NULL",
                     (_INTAKE_FOR_STATE.get(state, "CREATED"), cycle_id))
        conn.execute("UPDATE cycles SET disposition='Active' WHERE cycle_id=? AND disposition IS NULL",
                     (cycle_id,))

        if _STATE_RANK.get(state, 0) < _ANALYZED_RANK:
            continue   # no generation before analysis; no source binding fabricated

        run = conn.execute(
            "SELECT run_id, input_fingerprint FROM rule_runs WHERE cycle_id=? "
            "AND input_fingerprint IS NOT NULL AND input_fingerprint<>'' "
            "ORDER BY run_id LIMIT 1", (cycle_id,)).fetchone()
        if run is None:
            conn.execute(
                "INSERT INTO migration_diagnostics(migration, cycle_id, code, detail, created_ts) "
                "SELECT ?,?,?,?,? WHERE NOT EXISTS(SELECT 1 FROM migration_diagnostics "
                "WHERE migration=? AND cycle_id=? AND code=?)",
                (NAME, cycle_id, "legacy_generation_not_backfilled",
                 "ANALYZED+ review has no rule run with a usable input fingerprint; findings retained "
                 "as history, no generation fabricated", now, NAME, cycle_id,
                 "legacy_generation_not_backfilled"))
            continue

        run_id, fingerprint = run
        gen_id = "gen-%s-1" % cycle_id
        actor, verified_at = _legacy_verification(conn, cycle_id)
        incomplete = 1 if (actor == LEGACY_VERIFICATION_ACTOR or verified_at is None) else 0
        conn.execute(
            "INSERT OR IGNORE INTO review_generations("
            "generation_id, cycle_id, sequence_number, analytical_state, creation_reason, "
            "based_on_generation_id, verification_basis_generation_id, verified_fingerprint, "
            "extractor_version, verification_actor, verified_at, created_by, created_at, "
            "generation_disposition, legacy_metadata_incomplete) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (gen_id, cycle_id, 1, _ANALYTICAL_FOR_STATE[state], "INITIAL_VERIFICATION",
             None, None, fingerprint, None, actor, verified_at, LEGACY_BACKFILL_ACTOR, now,
             "active", incomplete))
        # Attach exactly one run (one-run-per-generation), then the cycle's findings. Order matters:
        # the finding⇒run consistency trigger requires the run to already carry the generation.
        conn.execute("UPDATE rule_runs SET generation_id=? WHERE run_id=? AND generation_id IS NULL",
                     (gen_id, run_id))
        conn.execute("UPDATE findings SET generation_id=? WHERE cycle_id=? AND generation_id IS NULL",
                     (gen_id, cycle_id))
        # First generation of a review auto-publishes (ADR-011 §8): set both pointers if unset.
        conn.execute(
            "UPDATE cycles SET working_generation_id=?, published_generation_id=? WHERE cycle_id=? "
            "AND working_generation_id IS NULL AND published_generation_id IS NULL",
            (gen_id, gen_id, cycle_id))


def _legacy_verification(conn: sqlite3.Connection, cycle_id: str):
    """Return (actor, verified_at) from an EXPLICIT recorded verification audit fact, or the honest
    legacy marker + NULL timestamp when none exists. Never fabricates a name or a precise time."""
    row = conn.execute(
        "SELECT actor, ts FROM audit WHERE cycle_id=? AND action IN ('verify','verified','approved') "
        "ORDER BY seq LIMIT 1", (cycle_id,)).fetchone()
    if row and row[0]:
        return row[0], row[1]
    return LEGACY_VERIFICATION_ACTOR, None
