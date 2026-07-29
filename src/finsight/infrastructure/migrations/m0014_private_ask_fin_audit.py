"""Stage 2 append-only local audit for private Ask Fin interactions."""
from __future__ import annotations

import sqlite3


VERSION = 14
NAME = "private_ask_fin_audit"


def up(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_private_ask_fin_interactions("
        "interaction_id TEXT PRIMARY KEY,"
        "user_id TEXT NOT NULL,"
        "review_id TEXT REFERENCES v2_review_cycles(review_id) ON DELETE CASCADE,"
        "validation_run_id TEXT,"
        "scope_json TEXT,"
        "mode TEXT NOT NULL CHECK(mode IN ('application_help','financial_review')),"
        "question TEXT NOT NULL,"
        "retrieved_records_json TEXT NOT NULL,"
        "provider TEXT NOT NULL,"
        "model TEXT NOT NULL,"
        "model_version TEXT NOT NULL,"
        "prompt_version TEXT NOT NULL,"
        "response TEXT NOT NULL,"
        "citations_json TEXT NOT NULL,"
        "refusal_trigger TEXT,"
        "latency_ms INTEGER,"
        "failure_state TEXT,"
        "status TEXT NOT NULL,"
        "grounding_review_id TEXT,"
        "created_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_private_ask_fin_review "
        "ON v2_private_ask_fin_interactions(review_id,created_at,interaction_id)"
    )
