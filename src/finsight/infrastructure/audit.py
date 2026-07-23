# Implements: FR-084..089, NFR-019, F-08-01, F-02-02 (ADR-005 AuditEventPort; append-only)
from __future__ import annotations
import json
from typing import Any, Dict, List

class AuditStoreSqlite:
    def __init__(self, dal, clock): self.dal = dal; self.clock = clock
    def emit(self, cycle_id: str, action: str, actor: str, detail: Dict[str, Any]) -> None:
        self.dal.conn.execute("INSERT INTO audit(cycle_id,action,actor,ts,detail) VALUES(?,?,?,?,?)",
            (cycle_id, action, actor, self.clock.now(), json.dumps(detail, sort_keys=True)))
    def timeline(self, cycle_id: str) -> List[str]:
        return [r[0] for r in self.dal.conn.execute(
            "SELECT action FROM audit WHERE cycle_id=? ORDER BY seq", (cycle_id,)).fetchall()]
    def events(self, cycle_id: str) -> List[Dict[str, Any]]:
        rows = self.dal.conn.execute("SELECT action,actor,ts,detail FROM audit WHERE cycle_id=? ORDER BY seq",
                                     (cycle_id,)).fetchall()
        return [{"action": r[0], "actor": r[1], "ts": r[2], "detail": json.loads(r[3])} for r in rows]
