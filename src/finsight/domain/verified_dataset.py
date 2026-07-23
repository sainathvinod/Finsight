# Implements: FR-026, NFR-047, F-02-02  (ADR-006: VerifiedDataset by construction; TB-02 gate)
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict

_KEY = object()  # module-private construction key; only the verification service holds it

@dataclass(frozen=True)
class VerifiedDataset:
    cycle_id: str
    ged_actuals: Dict[str, Decimal]        # account_no -> summed verified actual
    budget: Dict[str, Dict[str, Decimal]]  # account_no -> {"budget":..., "atd":...}
    _key: object = field(default=None, repr=False, compare=False)
    def __post_init__(self):
        if self._key is not _KEY:
            raise PermissionError(
                "VerifiedDataset can be constructed only by the verification service "
                "after human approval (ADR-006 / FR-026).")

def _make_verified_dataset(cycle_id, ged_actuals, budget) -> VerifiedDataset:
    # The ONLY factory. Imported solely by application.verification.
    return VerifiedDataset(cycle_id, dict(ged_actuals), dict(budget), _KEY)
