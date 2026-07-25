# Implements: NFR-005, NFR-057, NFR-058, FR-107, NFR-022, F-02-02 (ADR-004 DAL; transactions; TEXT amounts)
from __future__ import annotations
import sqlite3, json
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
from finsight.domain.review_cycle import ReviewCycle, CycleState
from finsight.infrastructure.migrations.runner import run_migrations

class Dal:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")   # enforce FK/ON DELETE CASCADE (AI tables)
        # Versioned schema (ADR-004). The baseline migration reproduces the original schema exactly
        # and is idempotent, so a new DB initializes and a legacy pre-migration DB is adopted safely.
        run_migrations(self.conn)

class SqliteUnitOfWork:
    # ADR-004: the DAL owns transactions. All-or-nothing per cycle transition (NFR-005/057).
    def __init__(self, dal): self.dal = dal
    @contextmanager
    def atomic(self):
        try:
            yield
            self.dal.conn.commit()
        except Exception:
            self.dal.conn.rollback()
            raise

class ReviewCycleRepoSqlite:
    def __init__(self, dal): self.dal = dal
    def save(self, cycle):  # no commit: transaction owned by the UnitOfWork
        self.dal.conn.execute("INSERT INTO cycles(cycle_id,month,year,state) VALUES(?,?,?,?) "
            "ON CONFLICT(cycle_id) DO UPDATE SET state=excluded.state",
            (cycle.cycle_id, cycle.month, cycle.year, cycle.state.value))
    def get(self, cycle_id) -> Optional[ReviewCycle]:
        row = self.dal.conn.execute("SELECT cycle_id,month,year,state FROM cycles WHERE cycle_id=?",
                                    (cycle_id,)).fetchone()
        if not row:
            return None
        return ReviewCycle(row[0], row[1], row[2], CycleState(row[3]))
    def list_all(self) -> List[ReviewCycle]:  # read-only; newest-first for the desktop UI
        rows = self.dal.conn.execute("SELECT cycle_id,month,year,state FROM cycles "
                                     "ORDER BY year DESC, month DESC, cycle_id").fetchall()
        return [ReviewCycle(r[0], r[1], r[2], CycleState(r[3])) for r in rows]

class IngestedFileRepoSqlite:
    def __init__(self, dal): self.dal = dal
    def save(self, f):
        self.dal.conn.execute("INSERT OR REPLACE INTO ingested_files VALUES(?,?,?,?,?,?,?,?)",
            (f.cycle_id, f.doc_type, f.name, f.fingerprint, f.size, f.timestamp, f.actor, f.period))
    def list(self, cycle_id) -> List[Dict[str, Any]]:
        rows = self.dal.conn.execute("SELECT doc_type,name,fingerprint,size,ts,actor,period FROM "
            "ingested_files WHERE cycle_id=? ORDER BY doc_type", (cycle_id,)).fetchall()
        keys = ["doc_type","name","fingerprint","size","ts","actor","period"]
        return [dict(zip(keys, r)) for r in rows]

class FindingRepoSqlite:
    # FindingsCommandPort.add + FindingsQueryPort.list  (ADR-007)
    def __init__(self, dal): self.dal = dal
    def add(self, f):
        # Column-qualified so additive lifecycle columns (generation_id, migration 0003) don't shift
        # positional binds. generation_id is intentionally left to its default (NULL) here — the
        # deterministic write path is NOT generation-aware in this phase (Phase 6.4b).
        self.dal.conn.execute(
            "INSERT OR REPLACE INTO findings(id,cycle_id,rule_id,severity,period,account,finding_type,"
            "evidence,source_refs,state) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (f.id, f.cycle_id, f.rule_id, f.severity, f.period, f.account, f.finding_type,
             json.dumps(f.evidence, sort_keys=True), json.dumps(f.source_refs), f.state))
    def list(self, cycle_id) -> List[Dict[str, Any]]:
        rows = self.dal.conn.execute("SELECT id,rule_id,severity,account,finding_type,evidence,source_refs "
            "FROM findings WHERE cycle_id=? ORDER BY account", (cycle_id,)).fetchall()
        out = []
        for r in rows:
            out.append({"id": r[0], "rule_id": r[1], "severity": r[2], "account": r[3],
                        "finding_type": r[4], "evidence": json.loads(r[5]), "source_refs": json.loads(r[6])})
        return out
    def list_views(self, cycle_id) -> List[Dict[str, Any]]:  # read-only; adds period + state for the UI
        rows = self.dal.conn.execute(
            "SELECT id,rule_id,severity,period,account,finding_type,evidence,source_refs,state "
            "FROM findings WHERE cycle_id=? ORDER BY account", (cycle_id,)).fetchall()
        out = []
        for r in rows:
            out.append({"id": r[0], "rule_id": r[1], "severity": r[2], "period": r[3], "account": r[4],
                        "finding_type": r[5], "evidence": json.loads(r[6]), "source_refs": json.loads(r[7]),
                        "state": r[8]})
        return out

class RuleRunRepoSqlite:
    def __init__(self, dal): self.dal = dal
    def save(self, run):
        # Column-qualified so the additive generation_id column (migration 0003) doesn't shift
        # positional binds. generation_id stays NULL here — the analysis write path is not
        # generation-aware in this phase (Phase 6.4b).
        self.dal.conn.execute(
            "INSERT OR REPLACE INTO rule_runs(run_id,cycle_id,ruleset_version,config_version,"
            "input_fingerprint,finding_count) VALUES(?,?,?,?,?,?)",
            (run["run_id"], run.get("cycle_id"), run["ruleset_version"], run["config_version"],
             run["input_fingerprint"], run["finding_count"]))
    def get_by_cycle(self, cycle_id) -> Optional[Dict[str, Any]]:
        r = self.dal.conn.execute("SELECT run_id,ruleset_version,config_version,input_fingerprint,finding_count "
            "FROM rule_runs WHERE cycle_id=? ORDER BY run_id LIMIT 1", (cycle_id,)).fetchone()
        if not r:
            return None
        return {"run_id": r[0], "ruleset_version": r[1], "config_version": r[2],
                "input_fingerprint": r[3], "finding_count": r[4]}

class ConfigRepoSqlite:
    def __init__(self, dal): self.dal = dal
    def save(self, cfg):
        self.dal.conn.execute("INSERT OR REPLACE INTO config VALUES(?,?,?,?,?)",
            (cfg["config_version"], int(cfg["materiality_pct"]), json.dumps(cfg["severity_bands"], sort_keys=True),
             cfg.get("period", ""), cfg.get("created_ts", "")))
    def active(self) -> Optional[Dict[str, Any]]:
        r = self.dal.conn.execute("SELECT version,materiality_pct,bands,period,created_ts FROM config "
            "ORDER BY created_ts DESC, version DESC LIMIT 1").fetchone()
        if not r:
            return None
        return {"config_version": r[0], "materiality_pct": r[1], "severity_bands": json.loads(r[2]),
                "period": r[3], "created_ts": r[4]}
