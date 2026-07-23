# Durable review memory. HUMAN-CONTROLLED: entries are created only through explicit commands and
# carry provenance. There is intentionally NO API that accepts model output — model-authored durable
# memory is impossible. System-derived entries must reference a deterministic source. Scoped by
# (user_id, cycle_id); no leakage across reviews or users. No automatic summarization.
from __future__ import annotations
from typing import List
from finsight.domain.ai.contracts import (
    ReviewMemoryEntry, MemoryType, InteractionEvent, AiInteractionEntry,
)
from finsight.application.ai.errors import MemoryProvenanceError, AiScopeError
from finsight.diagnostics import get_logger

_log = get_logger("ai.memory")


class ReviewMemoryService:
    def __init__(self, mem_repo, journal, uow, clock, new_id):
        self._mem = mem_repo
        self._journal = journal
        self._uow = uow
        self._clock = clock
        self._new_id = new_id

    def add_human_authored(self, user_id: str, cycle_id: str, content: str, actor: str) -> ReviewMemoryEntry:
        if not (content or "").strip():
            raise MemoryProvenanceError("Human-authored memory requires content.")
        if not (actor or "").strip():
            raise MemoryProvenanceError("Human-authored memory requires an actor.")
        return self._add(user_id, cycle_id, MemoryType.HUMAN_AUTHORED, content, actor, None, None)

    def add_system_derived(self, user_id: str, cycle_id: str, content: str,
                           source_type: str, source_id: str, actor: str = "system") -> ReviewMemoryEntry:
        if not (content or "").strip():
            raise MemoryProvenanceError("System-derived memory requires content.")
        if not (source_type or "").strip() or not (source_id or "").strip():
            raise MemoryProvenanceError("System-derived memory must reference a deterministic source "
                                        "(source_type and source_id).")
        return self._add(user_id, cycle_id, MemoryType.SYSTEM_DERIVED, content, actor, source_type, source_id)

    def _add(self, user_id, cycle_id, memory_type, content, actor, source_type, source_id) -> ReviewMemoryEntry:
        ts = self._clock.now()
        entry = ReviewMemoryEntry(self._new_id(), user_id, cycle_id, memory_type, content.strip(),
                                  actor, ts, ts, source_type, source_id)
        with self._uow.atomic():
            self._mem.add(entry)
            self._record(InteractionEvent.MEMORY_CREATED, user_id, cycle_id,
                         {"memory_id": entry.memory_id, "type": memory_type.value})
        _log.info("review memory added id=%s cid=%s type=%s", entry.memory_id, cycle_id, memory_type.value)
        return entry

    def list(self, user_id: str, cycle_id: str) -> List[ReviewMemoryEntry]:
        return self._mem.list_for_scope(user_id, cycle_id)

    def delete_entry(self, user_id: str, cycle_id: str, memory_id: str) -> None:
        entry = self._mem.get(memory_id)
        if entry is None:
            return
        if entry.user_id != user_id or entry.cycle_id != cycle_id:
            raise AiScopeError("Memory entry is outside the requested user/review scope.")
        with self._uow.atomic():
            self._mem.delete(memory_id)
            self._record(InteractionEvent.MEMORY_DELETED, user_id, cycle_id, {"memory_id": memory_id})

    def forget_review(self, user_id: str, cycle_id: str) -> int:
        with self._uow.atomic():
            removed = self._mem.delete_for_scope(user_id, cycle_id)
            self._record(InteractionEvent.MEMORY_FORGOTTEN, user_id, cycle_id, {"removed": removed})
        _log.info("review memory forgotten cid=%s removed=%s", cycle_id, removed)
        return removed

    def _record(self, event: InteractionEvent, user_id, cycle_id, metadata):
        self._journal.append(AiInteractionEntry(self._new_id(), user_id, cycle_id, None,
                                                event, "ok", metadata, self._clock.now()))
