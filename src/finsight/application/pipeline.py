# Implements: FR-011..016, FR-021, FR-022, FR-007, NFR-062, F-01-05, F-02-02 (extraction + safe rejection)
from __future__ import annotations
from typing import Dict, Any
from finsight.application import normalization as N
from finsight.application import validation as V

# Extractor identity (ADR-011 §8 verification-basis property). Bump ONLY when normalization/validation
# behavior changes such that a previously certified verified dataset would no longer reproduce. Phase
# 6.4c reconstruction compares this to a generation's recorded extractor_version (when present) to
# distinguish an extractor-driven verified-data divergence from a source-byte change.
EXTRACTOR_VERSION = "extractor-v1"

class ExtractionPipeline:
    extractor_version = EXTRACTOR_VERSION

    def __init__(self, reader):
        self._reader = reader  # DocumentReader (infrastructure)

    def _safe_read(self, path, doc_type):
        # An unreadable/corrupt workbook must never crash the run (NFR-062/AC-3).
        try:
            return self._reader.read(path, doc_type), ""
        except Exception as exc:
            return None, ("The %s file could not be read (it may be corrupt or not a valid "
                          "workbook: %s). Replace it with a readable file and re-run Upload "
                          "Validation." % (doc_type, type(exc).__name__))

    def run(self, ged_path: str, budget_path: str) -> Dict[str, Any]:
        ged_rows, ged_err = self._safe_read(ged_path, "GED")
        bud_rows, bud_err = self._safe_read(budget_path, "BUDGET")
        if ged_err or bud_err:
            reason = " ".join(r for r in (ged_err, bud_err) if r)
            return {"available": False, "reason": reason,
                    "readiness": {"Budget Analysis": "Unavailable - " + reason},
                    "ged_valid": [], "ged_quarantined": [], "budget_valid": [], "budget_quarantined": []}
        ged_norm = N.normalize_ged(ged_rows)
        bud_norm = N.normalize_budget(bud_rows)
        ged_valid, ged_q = V.validate_ged(ged_norm)
        bud_valid, bud_q = V.validate_budget(bud_norm)
        readiness = V.readiness(ged_valid, bud_valid)
        available = readiness["Budget Analysis"] == "Available"
        return {"available": available,
                "reason": "" if available else readiness["Budget Analysis"],
                "readiness": readiness,
                "ged_valid": ged_valid, "ged_quarantined": ged_q,
                "budget_valid": bud_valid, "budget_quarantined": bud_q}
