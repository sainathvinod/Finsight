# Verifies: ReviewWorkflowService is stateless; ReviewSessions are review-scoped and isolated.
import os
import tempfile
import unittest

from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.review_session import ReviewSession
from finsight.application.errors import VerificationRequiredError


class TestReviewSession(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ged = os.path.join(self.tmp, "g.xlsx")
        self.bud = os.path.join(self.tmp, "b.xlsx")
        build_synthetic_ged(self.ged)
        build_synthetic_budget(self.bud)
        self.app = build_app(os.path.join(self.tmp, "fs.db"), FixedClock())
        self.wf = ReviewWorkflowService(self.app.orch.engine)

    def test_service_holds_no_per_cycle_map(self):
        self.assertFalse(hasattr(self.wf, "_ctx"))
        # the only instance state is the shared engine
        self.assertEqual([a for a in vars(self.wf)], ["_e"])

    def test_two_sessions_do_not_leak(self):
        self.wf.create_review("2026-07", "July", "2026")
        self.wf.create_review("2026-08", "Aug", "2026")
        s1 = ReviewSession("2026-07")
        s2 = ReviewSession("2026-08")
        self.wf.upload(s1, self.ged, self.bud)
        self.wf.process(s1)
        # s2 remains empty: uploading/processing s1 never touched s2
        self.assertIsNotNone(s1.ctx["extracted"])
        self.assertIsNone(s2.ctx["extracted"])
        self.assertNotEqual(s1.ctx["paths"], s2.ctx["paths"])

    def test_discard_one_does_not_affect_other(self):
        s1 = ReviewSession("2026-07")
        s2 = ReviewSession("2026-08")
        s1.ctx["paths"] = {"GED": "x", "BUDGET": "y"}
        s2.ctx["paths"] = {"GED": "p", "BUDGET": "q"}
        s1.discard()
        self.assertFalse(s1.has_files())
        self.assertTrue(s2.has_files())

    def test_reopen_without_reselect_is_explicit(self):
        # complete verification in one session
        self.wf.create_review("2026-07", "July", "2026")
        s1 = ReviewSession("2026-07")
        self.wf.upload(s1, self.ged, self.bud)
        self.wf.process(s1)
        self.wf.verify(s1)
        # a fresh session (as after restart) has no verified dataset -> analysis explicitly refuses
        s_new = ReviewSession("2026-07")
        with self.assertRaises(VerificationRequiredError):
            self.wf.analyze(s_new)


if __name__ == "__main__":
    unittest.main()
