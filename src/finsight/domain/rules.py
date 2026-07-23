# Implements: FR-030, FR-031, FR-033, FR-070, FR-086, R-BUD-01, R-BUD-02, R-FND-02, F-02-02
from __future__ import annotations
from decimal import Decimal
from typing import Callable, List
from finsight.domain.money import pct, money_str
from finsight.domain.findings import make_finding, classify_severity
from finsight.domain.verified_dataset import VerifiedDataset

class RulesEngine:
    def __init__(self, add_finding: Callable, config: dict):
        self._add = add_finding                 # FindingsCommandPort.add (wired only here)
        self._cfg = config

    def analyze(self, vds: VerifiedDataset, run_id: str) -> List:
        # GATE: the engine accepts ONLY a VerifiedDataset (ADR-006 / FR-026 / NFR-047).
        if not isinstance(vds, VerifiedDataset):
            raise TypeError("RulesEngine.analyze requires a VerifiedDataset (verification gate).")
        materiality = int(self._cfg["materiality_pct"])
        bands = self._cfg["severity_bands"]
        period = self._cfg.get("period", "")
        out = []
        for account in sorted(vds.budget):          # explicit deterministic ordering (ADR-003)
            planned = vds.budget[account]["budget"]  # R-BUD-01: planned = budget (workbook figure)
            actual = vds.ged_actuals.get(account, Decimal(0))  # actual = summed GED activity
            variance = actual - planned
            p = pct(variance, planned)
            if p is None or abs(p) < Decimal(materiality):
                continue
            sev = classify_severity(abs(p), bands)     # R-FND-02
            ftype = "over-budget" if variance > 0 else "under-budget"
            fid = "F-" + run_id + "-" + account
            finding = make_finding(
                id=fid, cycle_id=vds.cycle_id, rule_id="R-BUD-02", severity=sev.label,
                period=period, account=account, finding_type=ftype,
                evidence={"planned": money_str(planned), "actual": money_str(actual),
                          "variance": money_str(variance), "variance_pct": money_str(p)},
                source_refs=["Original Budget!" + account, "GED!" + account])
            self._add(finding)
            out.append(finding)
        return sorted(out, key=lambda f: f.account)   # stable order
