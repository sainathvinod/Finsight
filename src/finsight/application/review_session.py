# A caller-owned, review-scoped working context for the interactive workflow. It carries the
# transient recompute state (selected paths, provenance, extracted data, verified dataset) that the
# step-oriented ReviewWorkflowService needs between steps. It is NOT persisted, holds NO repositories
# or database connection, and contains NO PySide6 types. One session belongs to exactly one review.
from __future__ import annotations
from typing import Any, Dict


def _empty_ctx() -> Dict[str, Any]:
    return {"provenance": None, "paths": None, "extracted": None, "readiness": None,
            "rejected": None, "vds": None, "findings": None, "run": None}


class ReviewSession:
    """Transient working context for one review workflow. The desktop controller owns the active
    session and replaces it when the active review changes; the workflow service is stateless and
    receives the session explicitly."""

    def __init__(self, cycle_id: str):
        self.cycle_id = cycle_id
        self.ctx: Dict[str, Any] = _empty_ctx()

    def has_files(self) -> bool:
        return bool(self.ctx.get("paths"))

    def discard(self) -> None:
        self.ctx = _empty_ctx()
