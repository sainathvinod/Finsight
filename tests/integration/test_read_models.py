# Verifies: read-only query services present persisted review/findings/audit facts for the UI,
# via the real deterministic workflow (no fabricated data), without writing or altering anything.
import os
import tempfile
import unittest

from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app
from finsight.application.read_models.queries import (
    ReviewQueryService, FindingsQueryService, AuditQueryService,
)


class TestReadModels(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        ged = os.path.join(self.tmp, "ged.synthetic.xlsx")
        bud = os.path.join(self.tmp, "budget.synthetic.xlsx")
        build_synthetic_ged(ged)
        build_synthetic_budget(bud)
        self.app = build_app(os.path.join(self.tmp, "fs.db"), FixedClock())
        self.app["orch"].run_review("2026-07", "July", "2026", ged, bud, approve=True)
        self.reviews = ReviewQueryService(self.app["cycle_repo"], self.app["finding_repo"])
        self.findings = FindingsQueryService(self.app["finding_repo"])
        self.audit = AuditQueryService(self.app["audit"])

    def test_list_reviews_includes_completed_review(self):
        items = self.reviews.list_reviews()
        match = [r for r in items if r.cycle_id == "2026-07"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].state, "Exported")
        self.assertEqual(match[0].month, "July")

    def test_review_status_reports_finding_count(self):
        status = self.reviews.get_status("2026-07")
        self.assertIsNotNone(status)
        self.assertEqual(status.finding_count, 1)
        self.assertEqual(status.state, "Exported")

    def test_findings_view_matches_deterministic_output(self):
        views = self.findings.list_for_cycle("2026-07")
        self.assertEqual(len(views), 1)
        f = views[0]
        self.assertEqual(f.account, "6100")
        self.assertEqual(f.rule_id, "R-BUD-02")
        self.assertEqual(f.severity, "High")           # deterministic; never AI-assigned
        self.assertEqual(f.finding_type, "over-budget")
        self.assertEqual(f.evidence["variance"], "3000.00")
        self.assertEqual(f.state, "New")
        self.assertTrue(f.source_refs)

    def test_audit_timeline_is_ordered_and_grounded(self):
        events = self.audit.timeline("2026-07")
        actions = [e.action for e in events]
        self.assertIn("analyze", actions)
        self.assertIn("finding", actions)
        # append-only order: setup precedes analyze
        self.assertLess(actions.index("setup"), actions.index("analyze"))

    def test_unknown_review_status_is_none(self):
        self.assertIsNone(self.reviews.get_status("does-not-exist"))


if __name__ == "__main__":
    unittest.main()
