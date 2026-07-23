# Implements: FR-021, FR-022, FR-024, FR-025, FR-081 (subset), F-01-05, F-02-02 (Validation service + readiness)
from __future__ import annotations
from typing import List, Dict, Any, Tuple

def validate_ged(records: List[Dict[str, Any]]) -> Tuple[list, list]:
    valid, quarantined = [], []
    for rec in records:
        if not rec["account"]:
            quarantined.append({**rec, "reason": "missing account"})
        elif rec["amount"] is None:
            quarantined.append({**rec, "reason": "non-numeric/placeholder amount"})
        else:
            valid.append(rec)
    return valid, quarantined

def validate_budget(records: List[Dict[str, Any]]) -> Tuple[list, list]:
    valid, quarantined = [], []
    for rec in records:
        if rec["budget"] is None:
            quarantined.append({**rec, "reason": "missing budget"})
        else:
            valid.append(rec)
    return valid, quarantined

def readiness(ged_valid, budget_valid) -> Dict[str, str]:
    # single-capability readiness verdict (R-RDY-07 subset)
    if budget_valid and ged_valid:
        return {"Budget Analysis": "Available"}
    missing = []
    if not budget_valid: missing.append("Budget Tracker")
    if not ged_valid: missing.append("GED")
    return {"Budget Analysis": "Unavailable - missing: " + ", ".join(missing)}
