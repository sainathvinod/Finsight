# Implements: FR-026, FR-027, FR-028, FR-029, NFR-047, F-02-02 (Verification service = the gate; builds VerifiedDataset)
from __future__ import annotations
from decimal import Decimal
from typing import Dict, Any
from finsight.domain.verified_dataset import _make_verified_dataset  # ONLY importer of the factory

class VerificationService:
    def build(self, cycle_id: str, extracted: Dict[str, Any], approved: bool):
        if not approved:
            raise PermissionError("Analysis cannot proceed on unverified data (FR-026 / verification gate).")
        ged_actuals: Dict[str, Decimal] = {}
        for rec in extracted["ged_valid"]:
            ged_actuals[rec["account"]] = ged_actuals.get(rec["account"], Decimal(0)) + rec["amount"]
        budget: Dict[str, Dict[str, Decimal]] = {}
        for rec in extracted["budget_valid"]:
            budget[rec["account"]] = {"budget": rec["budget"], "atd": rec["atd"]}
        return _make_verified_dataset(cycle_id, ged_actuals, budget)
