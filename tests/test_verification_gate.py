# Verifies: FR-026, NFR-047 (VerifiedDataset by construction; engine rejects unverified data)
import unittest
from decimal import Decimal
from finsight.domain.verified_dataset import VerifiedDataset, _make_verified_dataset
from finsight.domain.findings import Finding
from finsight.domain.rules import RulesEngine

class TestGate(unittest.TestCase):
    def test_direct_verifieddataset_construction_forbidden(self):
        with self.assertRaises(PermissionError):
            VerifiedDataset("c", {}, {})
    def test_factory_constructs(self):
        vds = _make_verified_dataset("c", {"6100": Decimal("13000")}, {"6100": {"budget": Decimal("10000")}})
        self.assertIsInstance(vds, VerifiedDataset)
    def test_engine_rejects_non_verified(self):
        eng = RulesEngine(add_finding=lambda f: None, config={"materiality_pct":20,"severity_bands":{"critical":50,"high":30,"medium":20}})
        with self.assertRaises(TypeError):
            eng.analyze({"6100": "raw"}, "run")   # a raw dict is not a VerifiedDataset
    def test_direct_finding_construction_forbidden(self):
        with self.assertRaises(PermissionError):
            Finding("id","c","R","High","p","6100","over-budget",{},[])

if __name__ == "__main__":
    unittest.main()
