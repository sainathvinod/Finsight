# Implements: FR-001, FR-003, FR-010, NFR-062, F-02-02  (IngestedFile provenance; safe-rejection contract)
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class IngestedFile:
    cycle_id: str
    doc_type: str          # "GED" | "BUDGET"
    name: str
    fingerprint: str       # sha256 of the source bytes (integrity/provenance)
    size: int
    timestamp: str         # injected clock
    actor: str
    period: str

@dataclass(frozen=True)
class RejectionResult:
    ok: bool
    reason: str = ""       # plain-language, no raw trace (NFR-062)
    next_step: str = ""
