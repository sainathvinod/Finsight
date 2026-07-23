import unittest
from tests.ai.support import make, seed_review
from finsight.domain.ai.contracts import GroundedFinding, AiGroundingContext


class TestGrounding(unittest.TestCase):
    def setUp(self):
        self.tmp, self.container, self.ai = make()
        self.g = self.ai.grounding

    def test_structured_facts_with_source_references(self):
        seed_review(self.container, self.tmp, "2026-07")
        findings = self.g.findings("2026-07")
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertIsInstance(f, GroundedFinding)     # structured domain record, not a UI view model
        self.assertEqual(f.account, "6100")
        self.assertTrue(f.source_refs)                # deterministic source references
        self.assertIn("variance", f.evidence)

    def test_context_aggregates_deterministic_facts(self):
        seed_review(self.container, self.tmp, "2026-07")
        ctx = self.g.context("2026-07")
        self.assertIsInstance(ctx, AiGroundingContext)
        self.assertEqual(ctx.review.cycle_id, "2026-07")
        self.assertEqual(ctx.summary.finding_count, 1)
        self.assertIsNotNone(ctx.rule_run)
        self.assertTrue(ctx.rule_run.input_fingerprint)      # deterministic run reference
        self.assertTrue(ctx.provenance)                       # GED + BUDGET provenance

    def test_cycle_isolation(self):
        # One review exists; querying any other cycle returns nothing — grounding for one review
        # can never surface another review's facts. (Only one review is seeded here because the
        # deterministic finding id is derived from the input fingerprint, so two reviews built from
        # identical synthetic data would collide on the finding-id primary key.)
        seed_review(self.container, self.tmp, "2026-07")
        self.assertEqual(len(self.g.findings("2026-07")), 1)
        self.assertEqual(self.g.review("2026-07").cycle_id, "2026-07")
        self.assertEqual(self.g.findings("2026-08"), [])       # different cycle -> no leakage
        self.assertIsNone(self.g.review("2026-08"))
        self.assertIsNone(self.g.summary("2026-08"))
        self.assertIsNone(self.g.rule_run("2026-08"))

    def test_read_only_surface_no_command_access(self):
        public = {m for m in dir(self.g) if not m.startswith("_")}
        self.assertEqual(public, {"review", "findings", "summary", "rule_run",
                                  "provenance", "audit_events", "context"})


if __name__ == "__main__":
    unittest.main()
