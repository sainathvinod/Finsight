# Implements: FR-076, FR-095, F-07-01, F-02-02 (Budget Health summary; consumes FindingsQueryPort dicts)
from __future__ import annotations
from typing import List, Dict, Any

class ReportingService:
    def summary(self, cycle, finding_dicts: List[Dict[str, Any]], run: Dict[str, Any]) -> Dict[str, Any]:
        lines = []
        for f in finding_dicts:
            ev = f.get("evidence", {})
            lines.append("Account " + f["account"] + ": " + f["finding_type"] + " by "
                         + ev.get("variance", "") + " (" + ev.get("variance_pct", "")
                         + "%) - severity " + f["severity"])
        health = "Needs Attention" if finding_dicts else "On Track"
        return {"section": "Budget Health", "period": cycle.month + " " + cycle.year,
                "status_label": health, "finding_count": len(finding_dicts),
                "budget_health_lines": lines,
                "ai_narrative": {"label": "AI-generated", "content": None, "note": "AI disabled (FR-095)"}}
