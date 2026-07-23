import copy
import unittest

from finsight.application.ai.prompt.budget import ContextBudget
from finsight.application.ai.prompt.builder import PromptBuilder, PromptBuildResult
from finsight.domain.ai.contracts import (
    AiGroundingContext, GroundedReview, GroundedFinding, GroundedSummary, GroundedRuleRun,
    GroundedProvenanceItem, GroundedAuditEvent, ConversationMessage, MessageRole,
    ReviewMemoryEntry, MemoryType,
)


def _finding(fid, account, severity):
    return GroundedFinding(fid, account, "R-BUD-02", severity, "variance", "2026-07",
                           {"variance_pct": "12.5", "amount": "100"}, ["GED:6100"], "New")


def _grounding(findings):
    return AiGroundingContext(
        review=GroundedReview("2026-07", "July", "2026", "Exported", len(findings)),
        findings=findings,
        summary=GroundedSummary("Exported", len(findings)),
        rule_run=GroundedRuleRun("run123", "rs-1", "cfg-1", "fp-abc", len(findings)),
        provenance=[GroundedProvenanceItem("GED", "ged.xlsx", "fp-ged", "2026-07")],
        audit_events=[GroundedAuditEvent("EXPORTED", "reviewer", "2026-07-01T00:00:00Z")],
    )


def _msg(seq, role, content):
    return ConversationMessage("m%d" % seq, "conv", role, content, seq, "2026-07-01T00:00:0%dZ" % seq)


class TestPromptBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = PromptBuilder(ContextBudget())        # unlimited by default

    def test_byte_identical_for_identical_inputs(self):
        g = _grounding([_finding("F-crit", "6100", "Critical"), _finding("F-low", "6200", "Low")])
        conv = [_msg(1, MessageRole.USER, "why?")]
        r1 = self.builder.build(grounding=g, question="explain", conversation=conv)
        r2 = self.builder.build(grounding=g, question="explain", conversation=conv)
        self.assertIsInstance(r1, PromptBuildResult)
        self.assertEqual(r1, r2)                              # frozen-dataclass equality
        self.assertEqual(r1.request.context_block, r2.request.context_block)

    def test_findings_ordered_by_severity_desc(self):
        g = _grounding([_finding("F-low", "6100", "Low"), _finding("F-crit", "6100", "Critical")])
        block = self.builder.build(grounding=g, question="q").request.context_block
        self.assertLess(block.index("[finding:F-crit]"), block.index("[finding:F-low]"))

    def test_finding_budget_trims_to_citation_key_only(self):
        builder = PromptBuilder(ContextBudget(max_findings=1))
        g = _grounding([_finding("F-crit", "6100", "Critical"), _finding("F-low", "6200", "Low")])
        res = builder.build(grounding=g, question="q")
        block = res.request.context_block
        self.assertEqual(res.truncation.findings_trimmed, 1)
        self.assertTrue(res.truncation.truncated)
        self.assertIn("[finding:F-crit] account=", block)                 # full detail kept
        self.assertIn("[finding:F-low] (detail omitted by budget)", block)  # key preserved
        self.assertNotIn("[finding:F-low] account=", block)

    def test_conversation_keeps_most_recent(self):
        builder = PromptBuilder(ContextBudget(max_conversation_messages=2))
        conv = [_msg(1, MessageRole.USER, "oldest"), _msg(2, MessageRole.ASSISTANT, "middle"),
                _msg(3, MessageRole.USER, "newest")]
        res = builder.build(grounding=_grounding([]), question="q", conversation=conv)
        cb = res.request.conversation_block
        self.assertEqual(res.truncation.conversation_dropped, 1)
        self.assertNotIn("oldest", cb)
        self.assertLess(cb.index("middle"), cb.index("newest"))           # chronological order

    def test_provider_independent(self):
        g = _grounding([_finding("F1", "6100", "High")])
        req = self.builder.build(grounding=g, question="q").request
        blob = (req.system_prompt + req.context_block + req.conversation_block + req.output_schema).lower()
        for provider_token in ("ollama", "llama", "http://", "localhost"):
            self.assertNotIn(provider_token, blob)

    def test_versioned_system_prompt_and_schema(self):
        req = self.builder.build(grounding=_grounding([]), question="q").request
        self.assertEqual(req.prompt_version, "v1")
        self.assertEqual(req.schema_version, "v1")
        self.assertIn("Explain only", req.system_prompt)
        self.assertIn("unable_to_answer", req.output_schema)

    def test_audience_and_detail_directives(self):
        req = self.builder.build(grounding=_grounding([]), question="q",
                                 audience="executive", answer_detail="detailed").request
        self.assertIn("Audience: executive.", req.system_prompt)
        self.assertIn("Answer detail: detailed.", req.system_prompt)

    def test_unlimited_budget_no_truncation(self):
        g = _grounding([_finding("F1", "6100", "High")])
        res = self.builder.build(grounding=g, question="q")
        self.assertFalse(res.truncation.truncated)

    def test_memory_rendered_with_source_for_system_derived(self):
        mem = [ReviewMemoryEntry("mem1", "u", "2026-07", MemoryType.SYSTEM_DERIVED, "auto note",
                                 "system", "2026-07-01T00:00:00Z", "2026-07-01T00:00:00Z",
                                 source_type="finding", source_id="F1")]
        block = self.builder.build(grounding=_grounding([]), question="q", memory=mem).request.context_block
        self.assertIn("[memory:mem1] type=system_derived: auto note (source=finding/F1)", block)

    def test_inputs_not_mutated(self):
        findings = [_finding("F-low", "6100", "Low"), _finding("F-crit", "6100", "Critical")]
        conv = [_msg(2, MessageRole.USER, "b"), _msg(1, MessageRole.USER, "a")]
        g = _grounding(findings)
        before_f, before_c = copy.deepcopy(findings), copy.deepcopy(conv)
        self.builder.build(grounding=g, question="q", conversation=conv)
        self.assertEqual(findings, before_f)     # builder is pure — no input mutation/reordering
        self.assertEqual(conv, before_c)

    def test_empty_grounding_does_not_crash(self):
        req = self.builder.build(grounding=AiGroundingContext(review=None), question="q").request
        self.assertIn("REVIEW: (none)", req.context_block)
        self.assertIn("FINDINGS:", req.context_block)


if __name__ == "__main__":
    unittest.main()
