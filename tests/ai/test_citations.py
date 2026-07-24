# Verifies: Phase 4C.4 CitationVerifier, grounding confidence, and AiAnswer factory (FR-099).
import copy
import unittest

from finsight.application.ai.citations import (
    CitationVerifier, grounding_confidence, assemble_ai_answer,
)
from finsight.application.ai.contracts import (
    AiAnswer, CitationIndex, CitationNamespace, GroundingConfidence, ValidatedResponse,
)
from finsight.application.ai.errors import CitationError

_AUDIT_KEY = "audit:EXPORTED@2026-07-01T00:00:00Z"


def _index(valid=None, omitted=(), fmt="v1"):
    if valid is None:
        valid = {"finding:F1", "run:R1", "prov:FP1", _AUDIT_KEY, "memory:M1"}
    return CitationIndex(valid_keys=frozenset(valid), omitted_finding_ids=frozenset(omitted),
                         format_version=fmt)


def _validated(*keys, answer_text="grounded answer", unable=False):
    return ValidatedResponse(answer_text=answer_text, unable_to_answer=unable,
                             citation_keys=tuple(keys))


def _reject(testcase, validated, index, code):
    with testcase.assertRaises(CitationError) as ctx:
        CitationVerifier().verify(validated, index)
    testcase.assertEqual(ctx.exception.code, code)
    return ctx.exception


class TestValidCitations(unittest.TestCase):
    def test_each_namespace_resolves(self):
        cases = {
            "finding:F1": (CitationNamespace.FINDING, "F1"),
            "run:R1": (CitationNamespace.RUN, "R1"),
            "prov:FP1": (CitationNamespace.PROV, "FP1"),
            _AUDIT_KEY: (CitationNamespace.AUDIT, "EXPORTED@2026-07-01T00:00:00Z"),
            "memory:M1": (CitationNamespace.MEMORY, "M1"),
        }
        for key, (ns, ident) in cases.items():
            refs = CitationVerifier().verify(_validated(key), _index())
            self.assertEqual(len(refs), 1, key)
            self.assertEqual(refs[0].namespace, ns, key)
            self.assertEqual(refs[0].identifier, ident, key)
            self.assertEqual(refs[0].key, key, key)

    def test_canonical_ordering(self):
        # emitted in reverse canonical order; verifier returns finding, run, prov, audit, memory
        refs = CitationVerifier().verify(
            _validated("memory:M1", _AUDIT_KEY, "prov:FP1", "run:R1", "finding:F1"), _index())
        self.assertEqual([r.namespace for r in refs],
                         [CitationNamespace.FINDING, CitationNamespace.RUN, CitationNamespace.PROV,
                          CitationNamespace.AUDIT, CitationNamespace.MEMORY])

    def test_unable_to_answer_yields_no_references(self):
        refs = CitationVerifier().verify(_validated(answer_text="", unable=True), _index())
        self.assertEqual(refs, ())

    def test_deterministic_output(self):
        v = CitationVerifier()
        r1 = v.verify(_validated("finding:F1", "run:R1"), _index())
        r2 = v.verify(_validated("finding:F1", "run:R1"), _index())
        self.assertEqual(r1, r2)


class TestCitationRejection(unittest.TestCase):
    def test_missing_colon(self):
        _reject(self, _validated("finding"), _index(), "malformed_citation")

    def test_empty_identifier(self):
        _reject(self, _validated("finding:"), _index(), "malformed_citation")

    def test_bracketed_key(self):
        _reject(self, _validated("[finding:F1]"), _index(), "malformed_citation")

    def test_whitespace_key(self):
        _reject(self, _validated("finding: F1"), _index(), "malformed_citation")

    def test_unknown_namespace(self):
        _reject(self, _validated("vendor:ACME"), _index(), "unknown_namespace")

    def test_omitted_finding_namespace_rejected(self):
        # the literal non-citable namespace is not a supported namespace
        _reject(self, _validated("omitted-finding:F9"), _index(), "unknown_namespace")

    def test_omitted_finding_id_rejected(self):
        _reject(self, _validated("finding:F9"), _index(omitted=("F9",)), "omitted_finding_cited")

    def test_absent_from_current_context(self):
        _reject(self, _validated("finding:F2"), _index(), "citation_not_in_context")

    def test_duplicate_rejected(self):
        _reject(self, _validated("finding:F1", "finding:F1"), _index(), "duplicate_citation")

    def test_format_version_mismatch(self):
        _reject(self, _validated("finding:F1"), _index(fmt="v2"), "unsupported_citation_format")

    def test_case_sensitive_namespace(self):
        _reject(self, _validated("FINDING:F1"), _index(), "unknown_namespace")


class TestVerifierPurity(unittest.TestCase):
    def test_inputs_not_mutated(self):
        validated = _validated("run:R1", "finding:F1")
        index = _index()
        before_v, before_i = copy.deepcopy(validated), copy.deepcopy(index)
        CitationVerifier().verify(validated, index)
        self.assertEqual(validated, before_v)
        self.assertEqual(index, before_i)

    def test_errors_contain_no_answer_text(self):
        validated = _validated("vendor:BAD", answer_text="SUPERSECRET-ANSWER")
        err = _reject(self, validated, _index(), "unknown_namespace")
        blob = "%s|%s|%s" % (err.message, err.code, err.detail)
        self.assertNotIn("SUPERSECRET-ANSWER", blob)


class TestGroundingConfidence(unittest.TestCase):
    def test_unable_to_answer_is_unavailable(self):
        self.assertEqual(
            grounding_confidence(unable_to_answer=True, verified_citation_count=3,
                                 has_citable_grounding=True, truncated=False),
            GroundingConfidence.UNAVAILABLE)

    def test_no_citable_grounding_is_unavailable(self):
        self.assertEqual(
            grounding_confidence(unable_to_answer=False, verified_citation_count=0,
                                 has_citable_grounding=False, truncated=False),
            GroundingConfidence.UNAVAILABLE)

    def test_zero_verified_citations_is_unavailable(self):
        self.assertEqual(
            grounding_confidence(unable_to_answer=False, verified_citation_count=0,
                                 has_citable_grounding=True, truncated=False),
            GroundingConfidence.UNAVAILABLE)

    def test_verified_with_truncation_is_medium(self):
        self.assertEqual(
            grounding_confidence(unable_to_answer=False, verified_citation_count=2,
                                 has_citable_grounding=True, truncated=True),
            GroundingConfidence.MEDIUM)

    def test_verified_no_truncation_is_high(self):
        self.assertEqual(
            grounding_confidence(unable_to_answer=False, verified_citation_count=2,
                                 has_citable_grounding=True, truncated=False),
            GroundingConfidence.HIGH)


class TestAssembleAiAnswer(unittest.TestCase):
    def test_pure_assembly_computes_confidence_and_metadata(self):
        validated = _validated("finding:F1")
        refs = CitationVerifier().verify(validated, _index())
        answer = assemble_ai_answer(
            validated=validated, citations=refs, provider="null", model="none",
            schema_version="v1", prompt_version="v1", masking_policy_version="v1",
            has_citable_grounding=True, truncated=False)
        self.assertIsInstance(answer, AiAnswer)
        self.assertEqual(answer.grounding_confidence, GroundingConfidence.HIGH)
        self.assertEqual(answer.citation_format_version, "v1")
        self.assertEqual(answer.answer_text, "grounded answer")
        self.assertEqual(answer.citations, refs)
        self.assertEqual(answer.masking_policy_version, "v1")


if __name__ == "__main__":
    unittest.main()
