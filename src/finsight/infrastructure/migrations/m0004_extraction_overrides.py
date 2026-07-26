# Implements: FR-028, FR-029, NFR-056, F-01-09 (user corrections to extracted data before verification).
#   ADR-003 (exact-decimal, values stored as TEXT — never REAL), ADR-005 (each correction is an
#   append-only audit fact; this table is the fast CURRENT-state projection), ADR-006 (corrections are
#   additive; the raw source is never mutated), ADR-011 §8 (the corrected dataset drives the verified
#   fingerprint). Phase target-product #6.
#
# Additive + idempotent: the table/triggers use IF NOT EXISTS; no existing table is renamed or rewritten;
# no financial value is changed; no normalized workbook rows are persisted. The immutable HISTORY of
# every correction lives in the append-only `audit` ledger (correction_saved / correction_reverted);
# this table holds only the current effective override per (cycle, document, row, field), so analysis
# can deterministically apply corrections. `original_value` is written once and never overwritten.
from __future__ import annotations
import sqlite3

VERSION = 4
NAME = "extraction_overrides"


def up(conn: sqlite3.Connection, clock=None) -> None:
    c = conn
    c.execute(
        "CREATE TABLE IF NOT EXISTS extraction_overrides("
        "cycle_id TEXT NOT NULL REFERENCES cycles(cycle_id), "
        "document_type TEXT NOT NULL, "            # 'GED' | 'BUDGET'
        "source_ref TEXT NOT NULL, "               # lineage of the edited row, e.g. 'GED!R57'
        "field TEXT NOT NULL, "                    # 'account' | 'amount' | 'budget' | 'atd'
        "original_value TEXT NOT NULL, "           # immutable extracted value (exact text) — set once
        "current_value TEXT NOT NULL, "            # corrected value (exact text)
        "actor TEXT NOT NULL, "
        "ts TEXT NOT NULL, "
        "version INTEGER NOT NULL, "               # bumped on each edit/revert of this key
        "reverted INTEGER NOT NULL DEFAULT 0 CHECK(reverted IN (0,1)), "
        "reason TEXT, "
        "PRIMARY KEY(cycle_id, document_type, source_ref, field))")
    c.execute("CREATE INDEX IF NOT EXISTS idx_overrides_cycle ON extraction_overrides(cycle_id)")

    # Non-destructive projection: a correction record is never DELETEd — reverting sets reverted=1 and
    # keeps original + current, so the current state is always recoverable (the audit ledger is the
    # authoritative history either way). Repositories UPSERT (ON CONFLICT DO UPDATE), never REPLACE,
    # so this trigger does not interfere with editing an existing correction.
    c.execute("CREATE TRIGGER IF NOT EXISTS trg_overrides_no_delete BEFORE DELETE ON "
              "extraction_overrides BEGIN SELECT RAISE(ABORT, "
              "'extraction_overrides is non-destructive; revert instead of delete'); END")
    # original_value is immutable once written (an edit may change current_value/version/reverted, but
    # never the recorded original extracted value).
    c.execute("CREATE TRIGGER IF NOT EXISTS trg_overrides_original_immutable BEFORE UPDATE ON "
              "extraction_overrides FOR EACH ROW WHEN NEW.original_value IS NOT OLD.original_value "
              "BEGIN SELECT RAISE(ABORT, 'original_value is immutable'); END")
