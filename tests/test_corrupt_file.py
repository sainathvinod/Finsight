# Verifies: FR-007, NFR-012, NFR-062 (AC-3): corrupt/missing input rejected safely; no crash; no rule ran
import unittest, tempfile, os
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app

class TestCorruptFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ged = os.path.join(self.tmp, "ged.synthetic.xlsx")
        self.bud = os.path.join(self.tmp, "budget.synthetic.xlsx")
        build_synthetic_budget(self.bud)
    def test_corrupt_ged_rejected_no_crash(self):
        with open(self.ged, "wb") as f:
            f.write(b"this is not a valid workbook")   # corrupt .xlsx
        app = build_app(os.path.join(self.tmp, "fs.db"), FixedClock())
        res = app["orch"].run_review("2026-07", "July", "2026", self.ged, self.bud, approve=True)
        self.assertTrue(res["rejected"])                      # plain-language rejection
        self.assertIn("could not be read", res["rejected"])
        self.assertEqual(res["finding_records"], [])          # no rule executed
        self.assertIsNone(app["run_repo"].get_by_cycle("2026-07"))  # no RuleRun
        acts = app["audit"].timeline("2026-07")
        self.assertIn("validate", acts)
        self.assertNotIn("verify", acts)                      # gate never reached
        self.assertNotIn("analyze", acts)
    def test_missing_file_rejected(self):
        app = build_app(os.path.join(self.tmp, "fs2.db"), FixedClock())
        res = app["orch"].run_review("2026-08", "Aug", "2026",
                                     os.path.join(self.tmp, "nope.xlsx"), self.bud, approve=True)
        self.assertTrue(res["rejected"])
        self.assertIn("missing", res["rejected"].lower())
        self.assertNotIn("analyze", app["audit"].timeline("2026-08"))

if __name__ == "__main__":
    unittest.main()
