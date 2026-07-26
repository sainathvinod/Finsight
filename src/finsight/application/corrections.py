# Implements: FR-028, FR-029, NFR-056, F-01-09 (user corrections to extracted data before verification).
#   Trust posture: corrections are additive and human-made. The source file is never mutated; the
#   ORIGINAL extracted value is preserved immutably; every save/revert is an append-only audit fact
#   (§19); analysis later runs on the APPROVED corrected dataset (applied at verify). AI is never
#   involved — this is deterministic, human-controlled editing (CLAUDE.md Trust > AI).
from __future__ import annotations
from typing import Optional

from finsight.domain.corrections import ExtractionOverride, CORRECTABLE_FIELDS, NUMERIC_FIELDS
from finsight.domain.money import to_decimal
from finsight.domain.review_cycle import CycleState, has_reached
from finsight.application.errors import InvalidCorrectionError, ReviewNotFoundError


class CorrectionService:
    """Command service for user corrections. Guards that edits happen only after processing and before
    verification (FR-028: corrections are pre-approval), validates each value, persists the current
    override, and records the decision in the append-only audit ledger."""

    def __init__(self, override_repo, cycle_repo, audit, uow, clock, actor: str = "local-user"):
        self._repo = override_repo
        self._cycle_repo = cycle_repo
        self._audit = audit
        self._uow = uow
        self._clock = clock
        self._actor = actor

    def _guard_editable(self, cycle_id: str):
        cycle = self._cycle_repo.get(cycle_id)
        if cycle is None:
            raise ReviewNotFoundError("No review exists for " + cycle_id + ".")
        if not has_reached(cycle.state, CycleState.PROCESSED):
            raise InvalidCorrectionError("Corrections can be made only after the data is processed.")
        if has_reached(cycle.state, CycleState.VERIFIED):
            raise InvalidCorrectionError(
                "This review is already verified; its extracted data can no longer be edited.")
        return cycle

    def save(self, cycle_id: str, document_type: str, source_ref: str, field: str,
             original_value: str, new_value: str, reason: Optional[str] = None) -> ExtractionOverride:
        self._guard_editable(cycle_id)
        document_type = (document_type or "").upper()
        if field not in CORRECTABLE_FIELDS.get(document_type, ()):
            raise InvalidCorrectionError("'%s' is not an editable field for %s." % (field, document_type))
        value = (new_value or "").strip()
        if field in NUMERIC_FIELDS:
            if to_decimal(value) is None:
                raise InvalidCorrectionError("Enter a valid number.")
        elif not value:
            raise InvalidCorrectionError("Value cannot be empty.")

        existing = self._repo.get(cycle_id, document_type, source_ref, field)
        # The immutable original is the extracted value captured on the FIRST correction of this cell.
        original = existing.original_value if existing else (original_value or "")
        version = (existing.version + 1) if existing else 1
        now = self._clock.now()
        ov = ExtractionOverride(cycle_id, document_type, source_ref, field, original, value,
                                self._actor, now, version, False, reason)
        with self._uow.atomic():
            self._repo.upsert(ov)
            self._audit.emit(cycle_id, "correction_saved", self._actor, {
                "document_type": document_type, "source_ref": source_ref, "field": field,
                "original_value": original, "corrected_value": value, "reason": reason or "",
                "version": version, "reverted": False})
        return ov

    def revert(self, cycle_id: str, document_type: str, source_ref: str, field: str) -> bool:
        self._guard_editable(cycle_id)
        document_type = (document_type or "").upper()
        existing = self._repo.get(cycle_id, document_type, source_ref, field)
        if existing is None or existing.reverted:
            return False
        now = self._clock.now()
        with self._uow.atomic():
            self._repo.revert(cycle_id, document_type, source_ref, field, self._actor, now)
            self._audit.emit(cycle_id, "correction_reverted", self._actor, {
                "document_type": document_type, "source_ref": source_ref, "field": field,
                "original_value": existing.original_value, "corrected_value": existing.current_value,
                "version": existing.version + 1, "reverted": True})
        return True

    def list_for_cycle(self, cycle_id: str):
        return self._repo.list_for_cycle(cycle_id)

    def active_overrides(self, cycle_id: str):
        """Non-reverted corrections — what disclosure and analysis reflect."""
        return [o for o in self._repo.list_for_cycle(cycle_id) if not o.reverted]

    def has_corrections(self, cycle_id: str) -> bool:
        return bool(self.active_overrides(cycle_id))
