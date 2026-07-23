# User preferences for the AI platform. Values are stored JSON-encoded (documented serialization).
# Safe, non-sensitive preferences only. No secrets, no provider credentials.
from __future__ import annotations
import json
from typing import Any, Dict
from finsight.domain.ai.contracts import UserPreference, InteractionEvent, AiInteractionEntry

# Typed defaults (documented). conversation_persistence gates whether message content is stored.
PREFERENCE_DEFAULTS: Dict[str, Any] = {
    "conversation_persistence": True,   # default retention: persist conversation content
    "answer_detail": "standard",        # future use (4D): brief | standard | detailed
    "audience": "reviewer",             # future use (4D)
    "retention_days": 0,                # 0 = keep until explicitly deleted (no auto-expiry in 4B)
}


class PreferencesService:
    def __init__(self, pref_repo, journal, uow, clock, new_id):
        self._prefs = pref_repo
        self._journal = journal
        self._uow = uow
        self._clock = clock
        self._new_id = new_id

    def get(self, user_id: str, key: str, default: Any = None) -> Any:
        pref = self._prefs.get(user_id, key)
        if pref is None:
            return PREFERENCE_DEFAULTS.get(key, default)
        return json.loads(pref.value)

    def set(self, user_id: str, key: str, value: Any) -> None:
        with self._uow.atomic():
            self._prefs.set(UserPreference(user_id, key, json.dumps(value), self._clock.now()))
            self._record(user_id, key)

    def delete(self, user_id: str, key: str) -> None:
        with self._uow.atomic():
            self._prefs.delete(user_id, key)
            self._record(user_id, key)

    def all(self, user_id: str) -> Dict[str, Any]:
        merged = dict(PREFERENCE_DEFAULTS)
        for p in self._prefs.list_for_user(user_id):
            merged[p.key] = json.loads(p.value)
        return merged

    def conversation_persistence_enabled(self, user_id: str) -> bool:
        return bool(self.get(user_id, "conversation_persistence", True))

    def _record(self, user_id: str, key: str):
        # journal the key only (never the value) — user-scoped event, no cycle
        self._journal.append(AiInteractionEntry(self._new_id(), user_id, None, None,
                                                InteractionEvent.PREFERENCES_CHANGED, "ok",
                                                {"key": key}, self._clock.now()))
