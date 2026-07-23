# Verifies: FR-069, FR-070, FR-071, NFR-036, FR-076, FR-116, FR-120, F-02-02 (golden-dataset: exactly one finding)
import unittest, tempfile, os
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app

class TestGolden(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ged = os.path.join(self.tmp, "ged.synthetic.xlsx")
        self.bud = os.path.join(self.tmp, "budget.synthetic.xlsx")
        build_synthetic_ged(self.ged); build_synthetic_budget(self.bud)
        self.app = build_app(os.path.join(self.tmp, "fs.db"), FixedClock())
    def test_end_to_end_one_finding(self):
        res = self.app["orch"].run_review("2026-07", "July", "2026", self.ged, self.bud, approve=True)
        findings = res["findings"]
        self.assertEqual(len(findings), 1)                       # exactly one
        f = findings[0]
        self.assertEqual(f.account, "6100")
        self.assertEqual(f.finding_type, "over-budget")
        self.assertEqual(f.rule_id, "R-BUD-02")
        self.assertEqual(f.severity, "High")                     # +30% -> High
        self.assertEqual(f.evidence["variance"], "3000.00")
        self.assertEqual(f.evidence["variance_pct"], "30.00")
        self.assertTrue(f.source_refs)                           # one-hop lineage (NFR-067)
        # summary + export produced
        self.assertEqual(res["summary"]["finding_count"], 1)
        self.assertEqual(res["summary"]["ai_narrative"]["content"], None)   # AI off (FR-095)
        self.assertIn("config_version", res["export"])
        self.assertEqual(res["export"]["ai_content"], "(none - AI disabled)")

if __name__ == "__main__":
    unittest.main()
