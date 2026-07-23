# Verifies: FR-086, NFR-022 (AC-6) + T-005: RuleRun persisted with versions+fingerprint; ConfigVersion persisted & bound
import unittest, tempfile, os
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app
from finsight.infrastructure.persistence import Dal, RuleRunRepoSqlite, ConfigRepoSqlite

class TestRunConfigPersistence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "fs.db")
        self.ged = os.path.join(self.tmp, "g.xlsx"); self.bud = os.path.join(self.tmp, "b.xlsx")
        build_synthetic_ged(self.ged); build_synthetic_budget(self.bud)
    def test_rulerun_and_configversion_persisted(self):
        app = build_app(self.db, FixedClock())
        app["orch"].run_review("2026-07", "July", "2026", self.ged, self.bud, approve=True)
        # reopen a fresh DAL on the same file -> proves durability (not just in-memory)
        dal2 = Dal(self.db)
        run = RuleRunRepoSqlite(dal2).get_by_cycle("2026-07")
        self.assertIsNotNone(run)
        self.assertEqual(run["ruleset_version"], "R1.0")
        self.assertEqual(run["config_version"], "cfg-synthetic-1")
        self.assertTrue(run["input_fingerprint"])
        self.assertEqual(run["finding_count"], 1)
        cfg = ConfigRepoSqlite(dal2).active()
        self.assertEqual(cfg["config_version"], "cfg-synthetic-1")     # ConfigVersion persisted (T-005)
        self.assertEqual(cfg["materiality_pct"], 20)
        self.assertEqual(run["config_version"], cfg["config_version"]) # run bound to the ConfigVersion

if __name__ == "__main__":
    unittest.main()
