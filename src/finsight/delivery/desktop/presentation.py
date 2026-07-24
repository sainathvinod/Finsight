# Phase 5.1 — reviewer-facing presentation helpers. Turns internal identifiers/state values into
# human-readable labels for the PRIMARY surface, while callers keep the canonical value available in
# tooltips/secondary details. Presentation only: no financial logic, no state changes, no AI.
from __future__ import annotations
from typing import Optional

# Domain CycleState value → friendly, reviewer-facing label. Canonical state stays available for
# tooltips/traceability; this only softens the primary surface.
_STATE_LABEL = {
    "Created": "Created",
    "Intake": "Files uploaded",
    "Processed": "Data processed",
    "Verified": "Data verified",
    "Analyzed": "Analysis complete",
    "Summarized": "Summary ready",
    "Exported": "Exported",
}

# Citation namespace → human noun. The canonical key (e.g. "finding:F1") is preserved by callers.
_CITATION_NOUN = {
    "finding": "Finding",
    "run": "Rule run",
    "prov": "Source",
    "audit": "Audit",
    "memory": "Note",
}


def period_text(month: Optional[str], year: Optional[str]) -> str:
    """"July 2026" from month/year; falls back gracefully."""
    month = (month or "").strip()
    year = (year or "").strip()
    if month and year:
        return f"{month} {year}"
    return month or year or "—"


def state_label(state: Optional[str]) -> str:
    if not state:
        return "Not started"
    return _STATE_LABEL.get(state, state)


def citation_label(key: str) -> str:
    """"finding:F1" → "Finding F1"; unknown shapes returned unchanged. Canonical key kept by caller."""
    if ":" not in key:
        return key
    namespace, identifier = key.split(":", 1)
    noun = _CITATION_NOUN.get(namespace)
    if noun is None:
        return key
    if namespace == "prov":                      # provenance identifiers are long fingerprints
        identifier = (identifier[:8] + "…") if len(identifier) > 9 else identifier
    return f"{noun} {identifier}"


def action_label(action: Optional[str]) -> str:
    """Audit action → Title Case words ("setup" → "Setup", "run_analysis" → "Run Analysis")."""
    if not action:
        return "—"
    return action.replace("_", " ").replace("-", " ").strip().title()
