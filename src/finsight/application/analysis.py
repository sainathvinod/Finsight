# Implements: FR-086, NFR-021, NFR-022, F-02-06, F-02-02 (versioned, fingerprinted run; replayable)
from __future__ import annotations
import hashlib, json
from finsight.domain.money import money_str
from finsight.domain.rules import RulesEngine

def _fingerprint(vds) -> str:
    payload = {"ged": {k: money_str(v) for k, v in sorted(vds.ged_actuals.items())},
               "budget": {k: {kk: money_str(vv) for kk, vv in sorted(v.items())}
                          for k, v in sorted(vds.budget.items())}}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()

class AnalysisService:
    def __init__(self, engine: RulesEngine, ruleset_version: str, config_version: str):
        self._engine = engine; self._rsv = ruleset_version; self._cv = config_version

    def run(self, vds):
        fp = _fingerprint(vds)
        run_id = fp[:12]
        findings = self._engine.analyze(vds, run_id)
        run = {"run_id": run_id, "ruleset_version": self._rsv,
               "config_version": self._cv, "input_fingerprint": fp,
               "finding_count": len(findings)}
        return findings, run
