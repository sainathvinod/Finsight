# Implements: FR-069, FR-070, FR-071, NFR-025, NFR-067, F-02-02  (ADR-007; R-FND-02)
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

class Severity(Enum):
    CRITICAL = (4, "Critical", "octagon")
    HIGH = (3, "High", "triangle")
    MEDIUM = (2, "Medium", "diamond")
    LOW = (1, "Low", "dot")
    def __init__(self, rank, label, shape):
        self.rank = rank; self.label = label; self.shape = shape  # color-independent (NFR-025)

_FKEY = object()

@dataclass(frozen=True)
class Finding:
    id: str
    cycle_id: str
    rule_id: str
    severity: str          # Severity.label
    period: str
    account: str
    finding_type: str
    evidence: Dict[str, str]
    source_refs: List[str]
    state: str = "New"
    _key: object = field(default=None, repr=False, compare=False)
    def __post_init__(self):
        if self._key is not _FKEY:
            raise PermissionError(
                "Finding can be created only via the rules engine / FindingsCommandPort (ADR-007).")

def make_finding(id, cycle_id, rule_id, severity, period, account, finding_type, evidence, source_refs):
    # Only the rules engine imports this. Delivery/AI hold the query side only.
    return Finding(id, cycle_id, rule_id, severity, period, account, finding_type,
                   dict(evidence), list(source_refs), "New", _FKEY)

# Implements: FR-070, R-FND-02 (severity is deterministic, configurable, never AI-assigned)
def classify_severity(abs_pct: Decimal, bands: Dict[str, int]) -> Severity:
    v = int(abs_pct)
    if v >= bands["critical"]:
        return Severity.CRITICAL
    if v >= bands["high"]:
        return Severity.HIGH
    if v >= bands["medium"]:
        return Severity.MEDIUM
    return Severity.LOW
