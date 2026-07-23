# Conversation lifecycle + message persistence. Scope-enforced (user_id + cycle_id), retention-aware,
# transactional. This service NEVER generates messages or simulates AI: assistant content is only
# stored when supplied by a (future) caller.
from __future__ import annotations
from typing import List, Tuple
from finsight.domain.ai.contracts import (
    Conversation, ConversationMessage, MessageRole, InteractionEvent, AiInteractionEntry,
)
from finsight.application.ai.errors import ConversationNotFoundError, AiScopeError
from finsight.diagnostics import get_logger

_log = get_logger("ai.conversations")

# Documented default retention: conversations persist until explicitly deleted. There is NO
# automatic expiry in Phase 4B; message persistence is gated by the user's conversation_persistence
# preference (see PreferencesService).
DEFAULT_RETENTION_POLICY = "keep"


class ConversationService:
    def __init__(self, conv_repo, msg_repo, journal, preferences, uow, clock, new_id):
        self._conv = conv_repo
        self._msg = msg_repo
        self._journal = journal
        self._prefs = preferences
        self._uow = uow
        self._clock = clock
        self._new_id = new_id

    # --- lifecycle ---
    def create(self, user_id: str, cycle_id: str, title: str = "") -> Conversation:
        ts = self._clock.now()
        conv = Conversation(self._new_id(), user_id, cycle_id, (title or "New conversation").strip(),
                            ts, ts, DEFAULT_RETENTION_POLICY)
        with self._uow.atomic():
            self._conv.save(conv)
            self._record(InteractionEvent.CONVERSATION_CREATED, user_id, cycle_id, conv.conversation_id,
                         {"title": conv.title})
        _log.info("conversation created id=%s cid=%s", conv.conversation_id, cycle_id)
        return conv

    def list(self, user_id: str, cycle_id: str) -> List[Conversation]:
        return self._conv.list_for_scope(user_id, cycle_id)

    def load(self, conversation_id: str, user_id: str, cycle_id: str) -> Tuple[Conversation, List[ConversationMessage]]:
        conv = self._require_scope(conversation_id, user_id, cycle_id)
        return conv, self._msg.list_for_conversation(conversation_id)

    def rename(self, conversation_id: str, user_id: str, cycle_id: str, title: str) -> None:
        self._require_scope(conversation_id, user_id, cycle_id)
        ts = self._clock.now()
        with self._uow.atomic():
            self._conv.update_title(conversation_id, (title or "").strip() or "Untitled", ts)
            self._record(InteractionEvent.CONVERSATION_RENAMED, user_id, cycle_id, conversation_id,
                         {"title": (title or "").strip()})

    def delete(self, conversation_id: str, user_id: str, cycle_id: str) -> None:
        self._require_scope(conversation_id, user_id, cycle_id)
        with self._uow.atomic():
            self._conv.delete(conversation_id)   # messages cascade (FK ON DELETE CASCADE)
            self._record(InteractionEvent.CONVERSATION_DELETED, user_id, cycle_id, conversation_id, {})

    def clear_messages(self, conversation_id: str, user_id: str, cycle_id: str) -> None:
        self._require_scope(conversation_id, user_id, cycle_id)
        ts = self._clock.now()
        with self._uow.atomic():
            self._msg.clear(conversation_id)       # delete messages, preserve the conversation record
            self._conv.touch(conversation_id, ts)
            self._record(InteractionEvent.CONVERSATION_CLEARED, user_id, cycle_id, conversation_id, {})

    # --- messages ---
    def append_user_message(self, conversation_id, user_id, cycle_id, content) -> ConversationMessage:
        return self._append(conversation_id, user_id, cycle_id, MessageRole.USER, content)

    def append_assistant_message(self, conversation_id, user_id, cycle_id, content) -> ConversationMessage:
        # Stores content SUPPLIED by a caller (e.g. a future Ask Fin orchestrator). Never generated here.
        return self._append(conversation_id, user_id, cycle_id, MessageRole.ASSISTANT, content)

    def _append(self, conversation_id, user_id, cycle_id, role: MessageRole, content: str) -> ConversationMessage:
        self._require_scope(conversation_id, user_id, cycle_id)
        ts = self._clock.now()
        if not self._prefs.conversation_persistence_enabled(user_id):
            # Retention disabled: do not persist content. Return a transient, non-persisted message.
            return ConversationMessage("(transient)", conversation_id, role, content, -1, ts)
        message = ConversationMessage(self._new_id(), conversation_id, role, content,
                                      self._msg.next_seq(conversation_id), ts)
        with self._uow.atomic():
            self._msg.append(message)
            self._conv.touch(conversation_id, ts)
        return message

    # --- helpers ---
    def _require_scope(self, conversation_id, user_id, cycle_id) -> Conversation:
        conv = self._conv.get(conversation_id)
        if conv is None:
            raise ConversationNotFoundError("Conversation not found: " + conversation_id, conversation_id)
        if conv.user_id != user_id or conv.cycle_id != cycle_id:
            raise AiScopeError("Conversation is outside the requested user/review scope.")
        return conv

    def _record(self, event: InteractionEvent, user_id, cycle_id, conversation_id, metadata):
        self._journal.append(AiInteractionEntry(self._new_id(), user_id, cycle_id, conversation_id,
                                                event, "ok", metadata, self._clock.now()))
