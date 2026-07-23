# Implements: AI Platform persistence (Phase 4B). Additive + idempotent (IF NOT EXISTS); does not
# touch any deterministic table. Explicit foreign keys, CHECK constraints, and scope indexes.
#
# SECURITY LIMITATION (ADR-009): these tables hold potentially sensitive conversation content and
# review memory. There is NO encryption at rest. Do not use with real sensitive data until
# encryption-at-rest is implemented.
from __future__ import annotations
import sqlite3

VERSION = 2
NAME = "ai_platform"


def up(conn: sqlite3.Connection) -> None:
    c = conn
    c.execute("CREATE TABLE IF NOT EXISTS ai_user_preferences("
              "user_id TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, updated_ts TEXT NOT NULL, "
              "PRIMARY KEY(user_id, key))")

    c.execute("CREATE TABLE IF NOT EXISTS ai_conversations("
              "conversation_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, cycle_id TEXT NOT NULL, "
              "title TEXT NOT NULL, created_ts TEXT NOT NULL, updated_ts TEXT NOT NULL, "
              "retention_policy TEXT NOT NULL)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ai_conversations_scope "
              "ON ai_conversations(user_id, cycle_id)")

    c.execute("CREATE TABLE IF NOT EXISTS ai_messages("
              "message_id TEXT PRIMARY KEY, "
              "conversation_id TEXT NOT NULL REFERENCES ai_conversations(conversation_id) ON DELETE CASCADE, "
              "role TEXT NOT NULL CHECK(role IN ('user','assistant')), content TEXT NOT NULL, "
              "seq INTEGER NOT NULL, created_ts TEXT NOT NULL)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ai_messages_conv ON ai_messages(conversation_id, seq)")

    c.execute("CREATE TABLE IF NOT EXISTS ai_review_memory("
              "memory_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, cycle_id TEXT NOT NULL, "
              "memory_type TEXT NOT NULL CHECK(memory_type IN ('human_authored','system_derived')), "
              "content TEXT NOT NULL, source_type TEXT, source_id TEXT, actor TEXT NOT NULL, "
              "created_ts TEXT NOT NULL, updated_ts TEXT NOT NULL)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ai_review_memory_scope "
              "ON ai_review_memory(user_id, cycle_id)")

    c.execute("CREATE TABLE IF NOT EXISTS ai_interactions("
              "interaction_id TEXT PRIMARY KEY, user_id TEXT, cycle_id TEXT, conversation_id TEXT, "
              "event_type TEXT NOT NULL, status TEXT NOT NULL, metadata_json TEXT NOT NULL, "
              "created_ts TEXT NOT NULL)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ai_interactions_scope "
              "ON ai_interactions(user_id, cycle_id)")
