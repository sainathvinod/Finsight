# Verifies: NFR-005, NFR-006, NFR-057 (AC-12): atomic transition rollback; resume from last consistent state; no lost data
import unittest, tempfile, os
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app
from finsight.infrastructure.audit import AuditStoreSqlite

class FaultyAudit(AuditStoreSqlite):
    # Simulates a crash: raises when a target step is being recorded.
    def __init__(self, dal, clock, fail_on):
        super().__init__(dal, clock); self.fail_on = fail_on
    def emit(self, cycle_id, action, actor, detail):
        if action == self.fail_on:
            raise RuntimeError("simulated crash during " + action)
        super().emit(cycle_id, action, actor, detail)

class TestCrashResume(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "fs.db")
        self.ged = os.path.join(self.tmp, "g.xlsx"); self.bud = os.path.join(self.tmp, "b.xlsx")
        build_synthetic_ged(self.ged); build_synthetic_budget(self.bud)
    def test_crash_then_resume(self):
        clock = FixedClock()
        # 1) Build an app whose audit crashes during 'analyze'.
        app = build_app(self.db, clock)
        app["orch"].audit = FaultyAudit(app["dal"], clock, fail_on="analyze")
        with self.assertRaises(RuntimeError):
            app["orch"].run_review("2026-07", "July", "2026", self.ged, self.bud, approve=True)
        # Atomicity: the ANALYZED transition rolled back -> state stayed VERIFIED, nothing written.
        cyc = app["cycle_repo"].get("2026-07") if "cycle_repo" in app else None
        # cycle_repo not exported; read state directly
        state = app["dal"].conn.execute("SELECT state FROM cycles WHERE cycle_id=?", ("2026-07",)).fetchone()[0]
        self.assertEqual(state, "Verified")
        self.assertEqual(app["finding_repo"].list("2026-07"), [])
        self.assertIsNone(app["run_repo"].get_by_cycle("2026-07"))
        pre = app["audit"].timeline("2026-07")
        for step in ["setup", "upload_ged", "upload_budget", "validate", "extract", "verify"]:
            self.assertIn(step, pre)                 # verified data + audit up to the gate survived
        self.assertNotIn("analyze", pre)
        # 2) Resume with a healthy app on the SAME database.
        app2 = build_app(self.db, clock)
        res = app2["orch"].resume("2026-07", self.ged, self.bud, approve=True)
        self.assertEqual(res["cycle"].state.value, "Exported")
        self.assertEqual(len(res["finding_records"]), 1)      # completed; no lost data
        post = app2["audit"].timeline("2026-07")
        for step in ["setup","upload_ged","upload_budget","validate","extract","verify","analyze","finding","summarize","export"]:
            self.assertEqual(post.count(step), 1)             # each step recorded exactly once (no duplication)

if __name__ == "__main__":
    unittest.main()
