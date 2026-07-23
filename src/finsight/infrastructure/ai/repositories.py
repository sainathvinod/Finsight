# SQLite adapters for the AI Platform persistence ports. Repository methods execute statements but
# do NOT commit — the application service wraps writes in the shared UnitOfWork (as in the rest of
# the DAL). Enum values are stored as their string value and reconstructed on read.
#
# SECURITY LIMITATION (see ADR-009): persisted conversation content and review memory are treated as
# potentially sensitive financial data. There is NO encryption at rest yet. This AI persistence must
# NOT be used with real sensitive data until encryption-at-rest is implemented. Synthetic/demo use
# only for now.
from __future__ import annotations
import json
from typing import List, Optional

from finsight.domain.ai.contracts import (
    Conversation, ConversationMessage, MessageRole, ReviewMemoryEntry, MemoryType,
    UserPreference, AiInteractionEntry, InteractionEvent,
)


class ConversationRepoSqlite:
    def __init__(self, dal):
        self.dal = dal

    def save(self, c: Conversation) -> None:
        self.dal.conn.execute(
            "INSERT INTO ai_conversations(conversation_id,user_id,cycle_id,title,created_ts,updated_ts,"
            "retention_policy) VALUES(?,?,?,?,?,?,?) ON CONFLICT(conversation_id) DO UPDATE SET "
            "title=excluded.title, updated_ts=excluded.updated_ts, retention_policy=excluded.retention_policy",
            (c.conversation_id, c.user_id, c.cycle_id, c.title, c.created_ts, c.updated_ts, c.retention_policy))

    def get(self, conversation_id: str) -> Optional[Conversation]:
        r = self.dal.conn.execute(
            "SELECT conversation_id,user_id,cycle_id,title,created_ts,updated_ts,retention_policy "
            "FROM ai_conversations WHERE conversation_id=?", (conversation_id,)).fetchone()
        return Conversation(*r) if r else None

    def list_for_scope(self, user_id: str, cycle_id: str) -> List[Conversation]:
        rows = self.dal.conn.execute(
            "SELECT conversation_id,user_id,cycle_id,title,created_ts,updated_ts,retention_policy "
            "FROM ai_conversations WHERE user_id=? AND cycle_id=? ORDER BY updated_ts DESC, conversation_id",
            (user_id, cycle_id)).fetchall()
        return [Conversation(*r) for r in rows]

    def update_title(self, conversation_id: str, title: str, updated_ts: str) -> None:
        self.dal.conn.execute("UPDATE ai_conversations SET title=?, updated_ts=? WHERE conversation_id=?",
                              (title, updated_ts, conversation_id))

    def touch(self, conversation_id: str, updated_ts: str) -> None:
        self.dal.conn.execute("UPDATE ai_conversations SET updated_ts=? WHERE conversation_id=?",
                              (updated_ts, conversation_id))

    def delete(self, conversation_id: str) -> None:
        self.dal.conn.execute("DELETE FROM ai_conversations WHERE conversation_id=?", (conversation_id,))


class MessageRepoSqlite:
    def __init__(self, dal):
        self.dal = dal

    def append(self, m: ConversationMessage) -> None:
        self.dal.conn.execute(
            "INSERT INTO ai_messages(message_id,conversation_id,role,content,seq,created_ts) "
            "VALUES(?,?,?,?,?,?)",
            (m.message_id, m.conversation_id, m.role.value, m.content, m.seq, m.created_ts))

    def list_for_conversation(self, conversation_id: str) -> List[ConversationMessage]:
        rows = self.dal.conn.execute(
            "SELECT message_id,conversation_id,role,content,seq,created_ts FROM ai_messages "
            "WHERE conversation_id=? ORDER BY seq", (conversation_id,)).fetchall()
        return [ConversationMessage(r[0], r[1], MessageRole(r[2]), r[3], r[4], r[5]) for r in rows]

    def next_seq(self, conversation_id: str) -> int:
        r = self.dal.conn.execute("SELECT COALESCE(MAX(seq),0)+1 FROM ai_messages WHERE conversation_id=?",
                                  (conversation_id,)).fetchone()
        return int(r[0])

    def clear(self, conversation_id: str) -> None:
        self.dal.conn.execute("DELETE FROM ai_messages WHERE conversation_id=?", (conversation_id,))


class ReviewMemoryRepoSqlite:
    def __init__(self, dal):
        self.dal = dal

    def add(self, e: ReviewMemoryEntry) -> None:
        self.dal.conn.execute(
            "INSERT INTO ai_review_memory(memory_id,user_id,cycle_id,memory_type,content,source_type,"
            "source_id,actor,created_ts,updated_ts) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (e.memory_id, e.user_id, e.cycle_id, e.memory_type.value, e.content, e.source_type,
             e.source_id, e.actor, e.created_ts, e.updated_ts))

    def get(self, memory_id: str) -> Optional[ReviewMemoryEntry]:
        r = self.dal.conn.execute(
            "SELECT memory_id,user_id,cycle_id,memory_type,content,source_type,source_id,actor,"
            "created_ts,updated_ts FROM ai_review_memory WHERE memory_id=?", (memory_id,)).fetchone()
        if not r:
            return None
        return ReviewMemoryEntry(r[0], r[1], r[2], MemoryType(r[3]), r[4], r[7], r[8], r[9], r[5], r[6])

    def list_for_scope(self, user_id: str, cycle_id: str) -> List[ReviewMemoryEntry]:
        rows = self.dal.conn.execute(
            "SELECT memory_id,user_id,cycle_id,memory_type,content,source_type,source_id,actor,"
            "created_ts,updated_ts FROM ai_review_memory WHERE user_id=? AND cycle_id=? "
            "ORDER BY created_ts, memory_id", (user_id, cycle_id)).fetchall()
        return [ReviewMemoryEntry(r[0], r[1], r[2], MemoryType(r[3]), r[4], r[7], r[8], r[9], r[5], r[6])
                for r in rows]

    def delete(self, memory_id: str) -> None:
        self.dal.conn.execute("DELETE FROM ai_review_memory WHERE memory_id=?", (memory_id,))

    def delete_for_scope(self, user_id: str, cycle_id: str) -> int:
        cur = self.dal.conn.execute("DELETE FROM ai_review_memory WHERE user_id=? AND cycle_id=?",
                                    (user_id, cycle_id))
        return int(cur.rowcount)


class UserPreferencesRepoSqlite:
    def __init__(self, dal):
        self.dal = dal

    def get(self, user_id: str, key: str) -> Optional[UserPreference]:
        r = self.dal.conn.execute(
            "SELECT user_id,key,value,updated_ts FROM ai_user_preferences WHERE user_id=? AND key=?",
            (user_id, key)).fetchone()
        return UserPreference(*r) if r else None

    def set(self, p: UserPreference) -> None:
        self.dal.conn.execute(
            "INSERT INTO ai_user_preferences(user_id,key,value,updated_ts) VALUES(?,?,?,?) "
            "ON CONFLICT(user_id,key) DO UPDATE SET value=excluded.value, updated_ts=excluded.updated_ts",
            (p.user_id, p.key, p.value, p.updated_ts))

    def delete(self, user_id: str, key: str) -> None:
        self.dal.conn.execute("DELETE FROM ai_user_preferences WHERE user_id=? AND key=?", (user_id, key))

    def list_for_user(self, user_id: str) -> List[UserPreference]:
        rows = self.dal.conn.execute(
            "SELECT user_id,key,value,updated_ts FROM ai_user_preferences WHERE user_id=? ORDER BY key",
            (user_id,)).fetchall()
        return [UserPreference(*r) for r in rows]


class AiInteractionJournalSqlite:
    """Append + read only. No update/delete methods exist (operational traceability)."""

    def __init__(self, dal):
        self.dal = dal

    def append(self, e: AiInteractionEntry) -> None:
        self.dal.conn.execute(
            "INSERT INTO ai_interactions(interaction_id,user_id,cycle_id,conversation_id,event_type,"
            "status,metadata_json,created_ts) VALUES(?,?,?,?,?,?,?,?)",
            (e.interaction_id, e.user_id, e.cycle_id, e.conversation_id, e.event_type.value, e.status,
             json.dumps(e.metadata, sort_keys=True), e.created_ts))

    def list_for_scope(self, user_id: str, cycle_id: str) -> List[AiInteractionEntry]:
        rows = self.dal.conn.execute(
            "SELECT interaction_id,user_id,cycle_id,conversation_id,event_type,status,metadata_json,"
            "created_ts FROM ai_interactions WHERE user_id=? AND cycle_id=? ORDER BY created_ts, interaction_id",
            (user_id, cycle_id)).fetchall()
        return [AiInteractionEntry(r[0], r[1], r[2], r[3], InteractionEvent(r[4]), r[5],
                                   json.loads(r[6]), r[7]) for r in rows]
