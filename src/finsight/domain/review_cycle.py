# Implements: FR-005, FR-006, NFR-006, F-02-02  (ADR-006 Review-Cycle model)
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class CycleState(str, Enum):
    CREATED = "Created"
    INTAKE = "Intake"
    VALIDATED = "Validated"
    PROCESSED = "Processed"
    VERIFIED = "Verified"
    ANALYZED = "Analyzed"
    SUMMARIZED = "Summarized"
    EXPORTED = "Exported"

@dataclass
class ReviewCycle:
    cycle_id: str
    month: str
    year: str
    state: CycleState = CycleState.CREATED
