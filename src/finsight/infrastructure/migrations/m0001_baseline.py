# Implements: F-02-02, ADR-004 (baseline schema).
# Behavior-preserving reproduction of the original pre-migration Dal schema. Every statement uses
# IF NOT EXISTS so this migration also safely ADOPTS a legacy database (tables already present)
# without recreating tables or losing data. Amounts are stored as TEXT (exact Decimal, ADR-003).
from __future__ import annotations
import sqlite3

VERSION = 1
NAME = "baseline"


def up(conn: sqlite3.Connection) -> None:
    c = conn
    c.execute("CREATE TABLE IF NOT EXISTS cycles("
              "cycle_id TEXT PRIMARY KEY, month TEXT, year TEXT, state TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS findings("
              "id TEXT PRIMARY KEY, cycle_id TEXT, rule_id TEXT, severity TEXT, period TEXT, "
              "account TEXT, finding_type TEXT, evidence TEXT, source_refs TEXT, state TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS rule_runs("
              "run_id TEXT PRIMARY KEY, cycle_id TEXT, ruleset_version TEXT, config_version TEXT, "
              "input_fingerprint TEXT, finding_count INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS audit("
              "seq INTEGER PRIMARY KEY AUTOINCREMENT, cycle_id TEXT, action TEXT, actor TEXT, "
              "ts TEXT, detail TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS ingested_files("
              "cycle_id TEXT, doc_type TEXT, name TEXT, fingerprint TEXT, size INTEGER, ts TEXT, "
              "actor TEXT, period TEXT, PRIMARY KEY(cycle_id, doc_type))")
    c.execute("CREATE TABLE IF NOT EXISTS config("
              "version TEXT PRIMARY KEY, materiality_pct INTEGER, bands TEXT, period TEXT, created_ts TEXT)")
