# Presentation metadata for the nine-step workflow. This is display/gating logic only — it changes
# no state and computes nothing financial. State ranks mirror the orchestrator's CycleState order.
from __future__ import annotations
from typing import List, Optional, Tuple

STEPS = ["Review Setup", "Data Upload", "Upload Validation", "Processing", "Verification",
         "Analysis", "Findings", "Leadership Summary", "Export"]

# Persisted CycleState -> rank (VALIDATED is unused by the flow, so not ranked).
RANK = {"Created": 0, "Intake": 1, "Processed": 2, "Verified": 3,
        "Analyzed": 4, "Summarized": 5, "Exported": 6}

# Minimum rank to *reach* (enable) a step, and the rank at which a step is *done*.
_MIN_RANK = [0, 0, 1, 1, 2, 3, 4, 4, 5]
_DONE_RANK = [0, 1, 2, 2, 3, 4, 4, 5, 6]
# Steps that carry an advancing action (vs. pure result views: Upload Validation, Findings).
_IS_ACTION = [True, True, False, True, True, True, False, True, True]


def rank(state: Optional[str]) -> int:
    return RANK.get(state, -1) if state else -1


def gates(state: Optional[str]) -> Tuple[List[bool], List[bool], int]:
    """Return (done, enabled, current_index) for the nine steps given the persisted state.
    - done: step already completed (revisitable, read-only)
    - enabled: step reachable now
    - current: the first incomplete *action* step (or 0 when there is no review yet)"""
    r = rank(state)
    done = [r >= 0 and r >= _DONE_RANK[i] for i in range(9)]
    if r < 0:
        enabled = [i == 0 for i in range(9)]     # no review yet -> only Review Setup
    else:
        enabled = [r >= _MIN_RANK[i] for i in range(9)]
    current = -1
    for i in range(9):
        if _IS_ACTION[i] and enabled[i] and not done[i]:
            current = i
            break
    if r < 0:
        current = 0
    return done, enabled, current
