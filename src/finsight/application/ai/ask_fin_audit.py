# Implements: E-09 Ask Fin audit integration (§19; ADR-005 append-only).
#   Ask Fin is read-only, but the ACT of asking and the answer STATUS are material actions for a review
#   — they must be recorded so nothing disappears. This records a non-sensitive fact only: the mode, the
#   canonical question key (or "free_text" — never the question text itself), the answer status, whether
#   the answer was grounded, and whether it was deterministic or model-assisted. No question text, answer
#   text, or financial values are stored (confidentiality; the AI interaction journal holds LLM metadata
#   separately).
from __future__ import annotations
from typing import Optional


class AskFinAuditService:
    def __init__(self, audit, uow, clock, actor: str = "local-user"):
        self._audit = audit
        self._uow = uow
        self._clock = clock
        self._actor = actor

    def record_answer(self, cycle_id: str, *, mode: str, question_key: str, status: str,
                      grounded: bool, source: str = "deterministic",
                      provider_status: Optional[str] = None) -> None:
        """Append an ask_fin_answered fact to a review's audit trail. Only called when a review is
        active (product-help has no review to attribute to)."""
        if not cycle_id:
            return
        detail = {"mode": mode, "question_key": question_key, "status": status,
                  "grounded": bool(grounded), "source": source}
        if provider_status:
            detail["provider_status"] = provider_status
        with self._uow.atomic():
            self._audit.emit(cycle_id, "ask_fin_answered", self._actor, detail)
