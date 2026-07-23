# Implements: FR-116, FR-120, F-07-04, F-02-02 (self-describing, labeled export)
from __future__ import annotations
import json
from typing import Dict, Any

class ExportService:
    def build(self, cycle, summary: Dict[str, Any], run: Dict[str, Any], data_as_of: str) -> Dict[str, Any]:
        return {"period": cycle.month + " " + cycle.year,
                "data_as_of": data_as_of,
                "config_version": run["config_version"],
                "ruleset_version": run["ruleset_version"],
                "ai_content": "(none - AI disabled)",
                "summary": summary}

    def to_json(self, export: Dict[str, Any]) -> str:
        return json.dumps(export, sort_keys=True, indent=2)
