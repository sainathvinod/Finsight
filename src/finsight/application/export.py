# Implements:
#   Feature: F-07-04 — Unified Export Capability (R1 core); F-07-03 — Report History & Reproducibility
#   Requirements: FR-116, FR-120
#   ADRs: ADR-015 §3 (immutable export + manifest identity); ADR-011 §8 (generation = export snapshot)
#
# Product purpose:
#   Builds the self-describing, labeled export package for a completed review — the leadership summary
#   plus a manifest that permanently identifies the exact generation/run/versions that produced it, so
#   a distributed financial artifact forever means what it said when generated (ADR-015 §2).
#
# Trust constraints:
#   - The manifest's "verified-source fingerprint" is the generation's verified-DATASET fingerprint
#     (ADR-015 §3, architect-confirmed) — source-bytes identity lives in the source binding/provenance.
#   - An export is a snapshot of ONE generation; R1 is single-generation, so status is always "current"
#     (supersession/"superseded" labeling is R2). Deterministic; independent of Ollama.
from __future__ import annotations
import hashlib
import json
from typing import Dict, Any, Optional

class ExportService:
    def build(self, cycle, summary: Dict[str, Any], run: Dict[str, Any], data_as_of: str,
              manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        content = {"period": cycle.month + " " + cycle.year,
                   "data_as_of": data_as_of,
                   "config_version": run["config_version"],
                   "ruleset_version": run["ruleset_version"],
                   "ai_content": "(none - AI disabled)",
                   "summary": summary}
        if manifest is not None:
            content["manifest"] = manifest        # ADR-015 §3 identity embedded in the export content
        return content

    def to_json(self, export: Dict[str, Any]) -> str:
        return json.dumps(export, sort_keys=True, indent=2)

    def fingerprint(self, export: Dict[str, Any]) -> str:
        """Deterministic content hash of the export package (ADR-015 §3 'export fingerprint'). Computed
        over the canonical JSON of the content INCLUDING its manifest — but the fingerprint itself is
        never embedded in the content (avoids circularity); it is the export_artifacts identity."""
        blob = json.dumps(export, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()
