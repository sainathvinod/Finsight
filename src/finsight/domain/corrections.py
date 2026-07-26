# Implements: FR-028, FR-029, NFR-056, F-01-09 (user correction to an extracted value).
#   A correction is additive and non-destructive: it records the immutable ORIGINAL extracted value and
#   the CURRENT corrected value for one (document, row, field), never mutating the source (ADR-006).
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

# Fields a reviewer may correct, per source. Only fields that flow into the deterministic verified
# dataset are correctable — correcting them changes analysis; other columns are display-only.
CORRECTABLE_FIELDS = {
    "GED": ("account", "amount"),
    "BUDGET": ("account", "budget", "atd"),
}
# Fields whose value is an exact-decimal money amount (parsed via domain.money.to_decimal on apply).
NUMERIC_FIELDS = frozenset({"amount", "budget", "atd"})


@dataclass(frozen=True)
class ExtractionOverride:
    cycle_id: str
    document_type: str          # 'GED' | 'BUDGET'
    source_ref: str             # lineage of the edited row, e.g. 'GED!R57'
    field: str                  # 'account' | 'amount' | 'budget' | 'atd'
    original_value: str         # immutable extracted value (exact text)
    current_value: str          # corrected value (exact text)
    actor: str
    ts: str
    version: int
    reverted: bool = False
    reason: Optional[str] = None

    @property
    def effective_value(self) -> str:
        """The value analysis uses: the correction unless it has been reverted to the original."""
        return self.original_value if self.reverted else self.current_value
