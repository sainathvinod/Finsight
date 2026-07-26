# Implements: FR-028, FR-029, NFR-056 (ADR-004 SQLite; ADR-003 exact-decimal TEXT storage).
#   Current-state projection of user corrections. UPSERTs (ON CONFLICT DO UPDATE) so `original_value`
#   is written once and preserved across edits; revert flips a flag (never deletes). The immutable
#   history is the append-only audit ledger; this repo is the fast lookup analysis applies at verify.
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from finsight.domain.corrections import ExtractionOverride


class ExtractionOverrideRepoSqlite:
    def __init__(self, dal):
        self.dal = dal

    def upsert(self, ov: ExtractionOverride) -> None:
        # First write records the immutable original; later edits keep it (original_value excluded from
        # the UPDATE set), bump version, refresh current/actor/ts/reason and clear the reverted flag.
        self.dal.conn.execute(
            "INSERT INTO extraction_overrides("
            "cycle_id, document_type, source_ref, field, original_value, current_value, actor, ts, "
            "version, reverted, reason) VALUES(?,?,?,?,?,?,?,?,?,0,?) "
            "ON CONFLICT(cycle_id, document_type, source_ref, field) DO UPDATE SET "
            "current_value=excluded.current_value, actor=excluded.actor, ts=excluded.ts, "
            "version=extraction_overrides.version+1, reverted=0, reason=excluded.reason",
            (ov.cycle_id, ov.document_type, ov.source_ref, ov.field, ov.original_value,
             ov.current_value, ov.actor, ov.ts, ov.version, ov.reason))

    def revert(self, cycle_id: str, document_type: str, source_ref: str, field: str,
               actor: str, ts: str) -> bool:
        cur = self.dal.conn.execute(
            "UPDATE extraction_overrides SET reverted=1, actor=?, ts=?, version=version+1 "
            "WHERE cycle_id=? AND document_type=? AND source_ref=? AND field=? AND reverted=0",
            (actor, ts, cycle_id, document_type, source_ref, field))
        return cur.rowcount > 0

    def get(self, cycle_id: str, document_type: str, source_ref: str,
            field: str) -> Optional[ExtractionOverride]:
        row = self.dal.conn.execute(
            "SELECT cycle_id, document_type, source_ref, field, original_value, current_value, actor, "
            "ts, version, reverted, reason FROM extraction_overrides "
            "WHERE cycle_id=? AND document_type=? AND source_ref=? AND field=?",
            (cycle_id, document_type, source_ref, field)).fetchone()
        return _row(row) if row else None

    def list_for_cycle(self, cycle_id: str) -> List[ExtractionOverride]:
        rows = self.dal.conn.execute(
            "SELECT cycle_id, document_type, source_ref, field, original_value, current_value, actor, "
            "ts, version, reverted, reason FROM extraction_overrides WHERE cycle_id=? "
            "ORDER BY document_type, source_ref, field", (cycle_id,)).fetchall()
        return [_row(r) for r in rows]

    def effective(self, cycle_id: str) -> Dict[Tuple[str, str, str], str]:
        """{(document_type, source_ref, field): current_value} for non-reverted corrections — exactly
        what analysis applies. Reverted corrections are excluded (their effective value is the original,
        i.e. no change)."""
        rows = self.dal.conn.execute(
            "SELECT document_type, source_ref, field, current_value FROM extraction_overrides "
            "WHERE cycle_id=? AND reverted=0 ORDER BY document_type, source_ref, field", (cycle_id,)
        ).fetchall()
        return {(r[0], r[1], r[2]): r[3] for r in rows}


def _row(r) -> ExtractionOverride:
    return ExtractionOverride(
        cycle_id=r[0], document_type=r[1], source_ref=r[2], field=r[3], original_value=r[4],
        current_value=r[5], actor=r[6], ts=r[7], version=int(r[8]), reverted=bool(r[9]), reason=r[10])
