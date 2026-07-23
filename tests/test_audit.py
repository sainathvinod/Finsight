# Verifies: NFR-019, FR-084..089 (every step emits an audit event; reconstructable)
import unittest, tempfile, os
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app

class TestAudit(unittest.TestCase):
    def test_all_steps_audited(self):
        tmp = tempfile.mkdtemp()
        g = os.path.join(tmp,"g.xlsx"); b = os.path.join(tmp,"b.xlsx")
        build_synthetic_ged(g); build_synthetic_budget(b)
        app = build_app(os.path.join(tmp,"fs.db"), FixedClock())
        app["orch"].run_review("2026-07","July","2026",g,b,approve=True)
        actions = app["audit"].timeline("2026-07")
        for step in ["setup","upload_ged","upload_budget","validate","extract","verify","analyze","finding","summarize","export"]:
            self.assertIn(step, actions)

if __name__ == "__main__":
    unittest.main()
