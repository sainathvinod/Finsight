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
        # Production wiring: both append-only sinks, merged into one timeline.
        self.audit = AuditQueryService(self.app["audit_stream"], self.app["audit"])

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


class TestAuditQueryServiceReadsTheReviewStream(unittest.TestCase):
    """Verifies: F-08-02 — the audit read model presents the trail the review workflow writes.

    The managed review workflow appends to the chained review audit stream, not to the legacy
    orchestrator's audit store. A read model pointed at the wrong sink returns an empty timeline
    while every workflow test still passes, so this asserts the wiring directly.
    """

    def setUp(self):
        from finsight.app import build_query_services
        from finsight.domain.source_intake import SourceRole
        from finsight.infrastructure.secure_store import TestEnvironmentStoreKeyProvider
        from tests.support import persist_confirmed_validation

        fixtures = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "initiatives",
            "configurable-rule-engine-v2",
            "fixtures",
        )
        self.tmp = tempfile.mkdtemp()
        self.services = build_query_services(
            os.path.join(self.tmp, "stream.db"),
            key_provider=TestEnvironmentStoreKeyProvider(),
        )
        review = self.services.review_management.create_review(
            5, 2026, idempotency_key="audit-stream-create"
        )
        self.review_id = review.review_id
        budget = self.services.source_intake.inspect(
            os.path.join(fixtures, "Sample_Budget_Report.xlsx"), SourceRole.BUDGET
        )
        ged = self.services.source_intake.inspect(
            os.path.join(fixtures, "Sample_GED_Report.xlsx"), SourceRole.GED
        )
        pair = self.services.source_intake.evaluate(
            budget=budget, ged=ged, selected_period=review.period
        )
        self.services.review_management.commit_source_intake(
            self.review_id, pair, idempotency_key="audit-stream-sources"
        )
        dataset = self.services.financial_review.reconstruct_dataset(self.review_id)
        self.services.financial_review.confirm_reviewed_data(
            self.review_id, dataset, attestation_text="Audit stream read-model test."
        )
        persist_confirmed_validation(
            self.services.financial_review, self.review_id, dataset
        )

    def test_audit_query_service_reads_the_chained_review_stream(self):
        events = self.services.audit.timeline(self.review_id)
        actions = [event.action for event in events]

        self.assertGreater(len(events), 0, "the managed review workflow recorded no audit trail")
        self.assertIn("review_created", actions)
        self.assertIn("deterministic_validation_completed", actions)
        # Append-only stream order: creation precedes validation completion.
        self.assertLess(
            actions.index("review_created"),
            actions.index("deterministic_validation_completed"),
        )

    def test_every_event_carries_attribution_and_a_timestamp(self):
        for event in self.services.audit.timeline(self.review_id):
            self.assertTrue(event.actor, f"{event.action} has no attributable actor")
            self.assertTrue(event.ts, f"{event.action} has no timestamp")
            self.assertIsInstance(event.detail, dict)

    def test_unknown_review_returns_an_empty_timeline(self):
        self.assertEqual(self.services.audit.timeline("does-not-exist"), [])
        self.assertEqual(self.services.audit.timeline(""), [])


if __name__ == "__main__":
    unittest.main()
