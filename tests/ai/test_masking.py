# Verifies: Phase 4C.3 / 4C.3A MaskingService — deterministic redaction policy (NFR-016, FR-098,
# ADR-010 masking policy; ADR-009 non-persistence).
import copy
import unittest

from finsight.application.ai.errors import MaskingError
from finsight.application.ai.masking import MaskingService, MaskingResult, MaskingSummary
from finsight.application.ai.masking_policy import MASKING_POLICY_VERSION, RESERVED_TOKENS, TOKENS
from finsight.domain.ai.contracts import (
    AiGroundingContext, ConversationMessage, GroundedAuditEvent, GroundedFinding, GroundedProvenanceItem,
    GroundedReview, GroundedRuleRun, GroundedSummary, MaskingConfiguration, MessageRole,
    MemoryType, ReviewMemoryEntry,
)


def _svc(names=(), mask_actor=True):
    return MaskingService(MaskingConfiguration(employee_names=tuple(names), mask_actor_fields=mask_actor))


def _mask_value(text, names=(), mask_actor=True):
    """Convenience: run one free-text value through masking via a finding's evidence value."""
    g = AiGroundingContext(review=None,
                           findings=[GroundedFinding("F1", "6100", "R", "Low", "t", "2026-07",
                                                     {"note": text}, [], "New")])
    res = _svc(names, mask_actor).mask(grounding=g, question="q")
    return res.grounding.findings[0].evidence["note"], res.summary


class TestEmailPhoneTaxBanking(unittest.TestCase):
    def test_email_masked(self):
        out, s = _mask_value("contact jane.doe@example.com now")
        self.assertEqual(out, "contact [REDACTED_EMAIL] now")
        self.assertEqual(s.email, 1)

    def test_phone_formats_masked_without_label(self):
        for raw in ("555-123-4567", "(555) 123-4567", "555 123 4567",
                    "+1 555 123 4567", "1-555-123-4567"):
            out, s = _mask_value("call %s please" % raw)
            self.assertEqual(out, "call [REDACTED_PHONE] please", raw)
            self.assertEqual(s.phone, 1, raw)

    def test_bare_ten_digits_not_masked_without_label(self):
        out, s = _mask_value("value 5551234567 recorded")
        self.assertEqual(out, "value 5551234567 recorded")
        self.assertEqual(s.total, 0)

    def test_bare_ten_digits_masked_with_label(self):
        out, s = _mask_value("cell 5551234567")
        self.assertEqual(out, "cell [REDACTED_PHONE]")
        self.assertEqual(s.phone, 1)

    def test_ssn_and_ein_formats_masked(self):
        out1, s1 = _mask_value("ssn 123-45-6789")
        self.assertEqual(out1, "ssn [REDACTED_TAX_ID]")
        self.assertEqual(s1.tax_id, 1)
        out2, s2 = _mask_value("employer 12-3456789 filed")
        self.assertEqual(out2, "employer [REDACTED_TAX_ID] filed")
        self.assertEqual(s2.tax_id, 1)

    def test_labeled_nine_digit_tax_masked_unlabeled_not(self):
        out1, _ = _mask_value("taxpayer id 123456789")
        self.assertEqual(out1, "taxpayer id [REDACTED_TAX_ID]")
        out2, s2 = _mask_value("invoice 123456789 total")
        self.assertEqual(out2, "invoice 123456789 total")     # unlabeled 9-digit is NOT a tax id
        self.assertEqual(s2.total, 0)

    def test_iban_masked(self):
        out, s = _mask_value("iban GB82WEST12345698765432 verified")
        self.assertEqual(out, "iban [REDACTED_BANKING_ID] verified")
        self.assertEqual(s.banking_id, 1)

    def test_swift_masked_only_with_label(self):
        out1, _ = _mask_value("swift DEUTDEFF")
        self.assertEqual(out1, "swift [REDACTED_BANKING_ID]")
        out2, s2 = _mask_value("code DEUTDEFF")               # no SWIFT/BIC label
        self.assertEqual(out2, "code DEUTDEFF")
        self.assertEqual(s2.total, 0)

    def test_routing_masked_only_with_label(self):
        out1, _ = _mask_value("routing number 021000021")
        self.assertEqual(out1, "routing number [REDACTED_BANKING_ID]")
        out2, s2 = _mask_value("reference 021000021 seen")     # unlabeled 9-digit not routing
        self.assertEqual(out2, "reference 021000021 seen")
        self.assertEqual(s2.total, 0)

    def test_bank_account_masked_only_with_banking_label(self):
        out1, _ = _mask_value("checking account 123456789")
        self.assertEqual(out1, "checking account [REDACTED_BANKING_ID]")
        out2, s2 = _mask_value("bank account number 998877")
        self.assertEqual(out2, "bank account number [REDACTED_BANKING_ID]")
        self.assertEqual(s2.banking_id, 1)


class TestNeverMask(unittest.TestCase):
    def test_generic_account_numbers_not_masked(self):
        for raw in ("account 6100", "GL account 6100", "account number 6100",
                    "accounting account 210500", "ledger account 4000"):
            out, s = _mask_value(raw)
            self.assertEqual(out, raw, raw)
            self.assertEqual(s.total, 0, raw)

    def test_financial_facts_not_masked(self):
        for raw in ("amount 1234567.89", "variance 23.5%", "percentage 100", "invoice INV-2026-0042",
                    "fingerprint fp-abc123def456", "budget 5000000"):
            out, s = _mask_value(raw)
            self.assertEqual(out, raw, raw)
            self.assertEqual(s.total, 0, raw)


class TestEmployeeName(unittest.TestCase):
    def test_configured_full_name_variants_masked(self):
        for raw in ("Jane Smith", "jane smith", "JANE   SMITH"):
            out, s = _mask_value(raw, names=["Jane Smith"])
            self.assertEqual(out, "[REDACTED_EMPLOYEE_NAME]", raw)
            self.assertEqual(s.employee_name, 1, raw)

    def test_partial_and_glued_names_not_masked(self):
        # Substring protection: bare partial tokens, a longer glued token, and a no-space run never
        # match the complete configured sequence.
        for raw in ("Jane", "Smith", "Jane Smithson", "JaneSmith"):
            out, s = _mask_value(raw, names=["Jane Smith"])
            self.assertEqual(out, raw, raw)
            self.assertEqual(s.employee_name, 0, raw)

    def test_configured_name_masked_in_normal_prose(self):
        # Revised 4C.3A policy (ADR-010): a complete configured name is masked wherever it occurs,
        # including mid-sentence — the earlier adjacency suppression was too conservative.
        cases = {
            "approved by Jane Smith": "approved by [REDACTED_EMPLOYEE_NAME]",
            "from jane smith": "from [REDACTED_EMPLOYEE_NAME]",
            "ask Jane Smith tomorrow": "ask [REDACTED_EMPLOYEE_NAME] tomorrow",
            "JANE   SMITH reviewed it": "[REDACTED_EMPLOYEE_NAME] reviewed it",
        }
        for raw, expected in cases.items():
            out, s = _mask_value(raw, names=["Jane Smith"])
            self.assertEqual(out, expected, raw)
            self.assertEqual(s.employee_name, 1, raw)

    def test_configured_name_masked_inside_longer_name_documented_limitation(self):
        # Documented deterministic limitation (ADR-010 §4): the service does not infer that adjacent
        # words form a larger human name, so "Jane Smith" IS masked within "Mary Jane Smith".
        out, s = _mask_value("Mary Jane Smith", names=["Jane Smith"])
        self.assertEqual(out, "Mary [REDACTED_EMPLOYEE_NAME]")
        self.assertEqual(s.employee_name, 1)

    def test_empty_list_never_blocks(self):
        out, s = _mask_value("Jane Smith reviewed the file", names=[])
        self.assertEqual(out, "Jane Smith reviewed the file")
        self.assertEqual(s.total, 0)

    def test_invalid_configured_name_raises(self):
        for bad in ("", "   ", "\t"):
            with self.assertRaises(MaskingError):
                MaskingService(MaskingConfiguration(employee_names=(bad,)))

    def test_duplicate_names_deduplicated(self):
        # equivalent normalized names collapse; a standalone name still masks exactly once
        out, s = _mask_value("Jane Smith", names=["Jane Smith", "jane  smith"])
        self.assertEqual(out, "[REDACTED_EMPLOYEE_NAME]")
        self.assertEqual(s.employee_name, 1)


class TestStructuredMasking(unittest.TestCase):
    def _grounding(self):
        return AiGroundingContext(
            review=GroundedReview("2026-07", "July", "2026", "Exported", 1),
            findings=[GroundedFinding("F1", "6100", "R-BUD-02", "High", "variance", "2026-07",
                                      {"amount": "1234567.89", "contact": "a@b.com",
                                       "variance_pct": "12.5"}, ["GED:6100"], "New")],
            summary=GroundedSummary("Exported", 1),
            rule_run=GroundedRuleRun("run1", "rs-1", "cfg-1", "fp-abc", 1),
            provenance=[GroundedProvenanceItem("GED", "vendor-acme-file.xlsx", "fp-ged", "2026-07")],
            audit_events=[GroundedAuditEvent("EXPORTED", "Jane Smith", "2026-07-01T00:00:00Z")],
        )

    def test_evidence_values_masked_facts_preserved(self):
        res = _svc(names=["Jane Smith"]).mask(grounding=self._grounding(), question="q")
        ev = res.grounding.findings[0].evidence
        self.assertEqual(ev["contact"], "[REDACTED_EMAIL]")
        self.assertEqual(ev["amount"], "1234567.89")             # amount preserved
        self.assertEqual(ev["variance_pct"], "12.5")             # percentage preserved
        # account / rule / source refs preserved
        self.assertEqual(res.grounding.findings[0].account, "6100")
        self.assertEqual(res.grounding.findings[0].source_refs, ["GED:6100"])

    def test_actor_whole_field_redacted(self):
        res = _svc().mask(grounding=self._grounding(), question="q")
        self.assertEqual(res.grounding.audit_events[0].actor, "[REDACTED_ACTOR]")
        self.assertEqual(res.grounding.audit_events[0].action, "EXPORTED")   # action preserved
        self.assertEqual(res.summary.actor, 1)

    def test_provenance_and_rulerun_not_masked(self):
        res = _svc().mask(grounding=self._grounding(), question="q")
        self.assertEqual(res.grounding.provenance[0].name, "vendor-acme-file.xlsx")
        self.assertEqual(res.grounding.rule_run.input_fingerprint, "fp-abc")

    def test_conversation_memory_question_masked(self):
        conv = [ConversationMessage("m1", "c", MessageRole.USER, "reach me at x@y.com", 1, "t")]
        mem = [ReviewMemoryEntry("mem1", "u", "2026-07", MemoryType.HUMAN_AUTHORED,
                                 "note ssn 123-45-6789", "Jane Smith", "t", "t")]
        res = _svc(names=["Jane Smith"]).mask(grounding=AiGroundingContext(review=None),
                                              question="who is cell 5551234567", conversation=conv,
                                              memory=mem)
        self.assertEqual(res.conversation[0].content, "reach me at [REDACTED_EMAIL]")
        self.assertEqual(res.memory[0].content, "note ssn [REDACTED_TAX_ID]")
        self.assertEqual(res.memory[0].actor, "[REDACTED_ACTOR]")
        self.assertEqual(res.question, "who is cell [REDACTED_PHONE]")

    def test_actor_toggle_off_applies_freetext(self):
        res = _svc(names=["Jane Smith"], mask_actor=False).mask(grounding=self._grounding(), question="q")
        # actor not whole-field redacted, but the configured name is still caught as free text
        self.assertEqual(res.grounding.audit_events[0].actor, "[REDACTED_EMPLOYEE_NAME]")
        self.assertEqual(res.summary.actor, 0)
        self.assertEqual(res.summary.employee_name, 1)


class TestPurityDeterminismIdempotence(unittest.TestCase):
    def _grounding(self):
        return AiGroundingContext(
            review=None,
            findings=[GroundedFinding("F1", "6100", "R", "Low", "t", "2026-07",
                                      {"c": "a@b.com"}, ["GED:6100"], "New")],
            audit_events=[GroundedAuditEvent("EXPORTED", "Jane Smith", "t")],
        )

    def test_inputs_not_mutated(self):
        g = self._grounding()
        before = copy.deepcopy(g)
        _svc(names=["Jane Smith"]).mask(grounding=g, question="q")
        self.assertEqual(g, before)

    def test_deterministic_equal_results(self):
        g = self._grounding()
        svc = _svc(names=["Jane Smith"])
        r1 = svc.mask(grounding=g, question="mail a@b.com")
        r2 = svc.mask(grounding=g, question="mail a@b.com")
        self.assertEqual(r1, r2)
        self.assertIsInstance(r1, MaskingResult)

    def test_idempotent_apply_twice_equals_once(self):
        g = self._grounding()
        svc = _svc(names=["Jane Smith"])
        once = svc.mask(grounding=g, question="mail a@b.com and ssn 123-45-6789")
        # feed the already-masked structures back in
        twice = svc.mask(grounding=once.grounding, question=once.question)
        self.assertEqual(once.grounding, twice.grounding)
        self.assertEqual(once.question, twice.question)
        self.assertEqual(twice.summary.total, 0)               # nothing left to mask on second pass

    def test_summary_counts_only_no_sensitive_data(self):
        res = _svc().mask(grounding=self._grounding(), question="q")
        self.assertIsInstance(res.summary, MaskingSummary)
        self.assertEqual(res.summary.email, 1)
        self.assertEqual(res.summary.actor, 1)
        self.assertEqual(res.summary.total, 2)


class TestPolicyVersion(unittest.TestCase):
    def test_summary_reports_policy_version(self):
        _, s = _mask_value("nothing sensitive")
        self.assertEqual(s.policy_version, MASKING_POLICY_VERSION)
        self.assertEqual(s.policy_version, "v1")

    def test_policy_version_present_on_result_summary(self):
        res = _svc().mask(grounding=AiGroundingContext(review=None), question="q")
        self.assertEqual(res.summary.policy_version, "v1")

    def test_policy_version_is_immutable_and_non_sensitive(self):
        _, s = _mask_value("ssn 123-45-6789 and a@b.com")   # sensitive input present
        self.assertIsInstance(s.policy_version, str)
        self.assertNotIn("123-45-6789", s.policy_version)   # no original value leaks into version
        self.assertNotIn("a@b.com", s.policy_version)


class TestProvenanceMasking(unittest.TestCase):
    def _prov(self, name):
        g = AiGroundingContext(
            review=None,
            provenance=[GroundedProvenanceItem("GED", name, "fp-ged-123", "2026-07")],
        )
        return _svc().mask(grounding=g, question="q").grounding.provenance[0]

    def test_provenance_name_email_masked(self):
        p = self._prov("vendor-jane.doe@example.com.xlsx")
        self.assertNotIn("jane.doe@example.com", p.name)     # email must not transmit unmasked
        self.assertIn("[REDACTED_EMAIL]", p.name)

    def test_provenance_structural_fields_preserved(self):
        p = self._prov("vendor-jane.doe@example.com.xlsx")
        self.assertEqual(p.doc_type, "GED")                  # structural identifier preserved
        self.assertEqual(p.fingerprint, "fp-ged-123")        # fingerprint preserved
        self.assertEqual(p.period, "2026-07")                # period preserved

    def test_ordinary_provenance_name_unchanged(self):
        p = self._prov("vendor-acme-file.xlsx")              # no sensitive tokens
        self.assertEqual(p.name, "vendor-acme-file.xlsx")

    def test_provenance_ordering_preserved(self):
        g = AiGroundingContext(review=None, provenance=[
            GroundedProvenanceItem("GED", "a.xlsx", "fp-a", "2026-07"),
            GroundedProvenanceItem("INV", "b.xlsx", "fp-b", "2026-07"),
        ])
        res = _svc().mask(grounding=g, question="q")
        self.assertEqual([p.fingerprint for p in res.grounding.provenance], ["fp-a", "fp-b"])


class TestReservedTokens(unittest.TestCase):
    def test_reserved_set_matches_emitted_tokens(self):
        self.assertEqual(RESERVED_TOKENS, frozenset(TOKENS.values()))

    def test_reserved_token_literal_passes_through_idempotently(self):
        # A literal input equal to a reserved token is treated as already redacted: unchanged, uncounted.
        for token in RESERVED_TOKENS:
            out, s = _mask_value(token)
            self.assertEqual(out, token, token)
            self.assertEqual(s.total, 0, token)

    def test_reserved_token_survives_surrounding_masking(self):
        out, s = _mask_value("prior [REDACTED_EMAIL] plus new a@b.com")
        self.assertEqual(out, "prior [REDACTED_EMAIL] plus new [REDACTED_EMAIL]")
        self.assertEqual(s.email, 1)                          # only the new address is counted


class TestByteIdenticalDeterminism(unittest.TestCase):
    def test_identical_inputs_produce_byte_identical_output(self):
        svc = _svc(names=["Jane Smith"])
        q = "from Jane Smith, mail a@b.com, ssn 123-45-6789, cell 5551234567"
        r1 = svc.mask(grounding=AiGroundingContext(review=None), question=q)
        r2 = svc.mask(grounding=AiGroundingContext(review=None), question=q)
        self.assertEqual(r1.question.encode("utf-8"), r2.question.encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
