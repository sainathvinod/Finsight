# Verifies: Phase 4C.4 ResponseValidator — deterministic, fail-closed schema enforcement (FR-099).
import json
import unittest

from finsight.application.ai.contracts import ResponseValidationLimits, ValidatedResponse
from finsight.application.ai.errors import ResponseFormatError
from finsight.application.ai.validation import ResponseValidator


def _json(answer_text="explanation", unable=False, citations=("finding:F1",)):
    return json.dumps({"answer_text": answer_text, "unable_to_answer": unable,
                       "citations": list(citations)})


def _reject(testcase, raw, code, limits=None, schema_version="v1"):
    v = ResponseValidator(limits)
    with testcase.assertRaises(ResponseFormatError) as ctx:
        v.validate(raw, schema_version=schema_version)
    testcase.assertEqual(ctx.exception.code, code, raw)
    return ctx.exception


class TestValidResponses(unittest.TestCase):
    def test_valid_substantive(self):
        out = ResponseValidator().validate(_json())
        self.assertIsInstance(out, ValidatedResponse)
        self.assertEqual(out.answer_text, "explanation")
        self.assertFalse(out.unable_to_answer)
        self.assertEqual(out.citation_keys, ("finding:F1",))

    def test_surrounding_whitespace_accepted(self):
        out = ResponseValidator().validate("  \n" + _json() + "\t\n ")
        self.assertEqual(out.citation_keys, ("finding:F1",))

    def test_unable_to_answer_with_refusal_text_accepted(self):
        out = ResponseValidator().validate(_json(answer_text="No relevant data.", unable=True,
                                                  citations=()))
        self.assertTrue(out.unable_to_answer)
        self.assertEqual(out.citation_keys, ())

    def test_unable_to_answer_empty_text_accepted(self):
        out = ResponseValidator().validate(_json(answer_text="", unable=True, citations=()))
        self.assertTrue(out.unable_to_answer)

    def test_deterministic_output(self):
        v = ResponseValidator()
        self.assertEqual(v.validate(_json()), v.validate(_json()))


class TestStructuralRejection(unittest.TestCase):
    def test_invalid_json(self):
        _reject(self, "{not json", "invalid_json")

    def test_markdown_fences_rejected(self):
        _reject(self, "```json\n" + _json() + "\n```", "invalid_json")

    def test_prose_before_rejected(self):
        _reject(self, "Here is the answer: " + _json(), "invalid_json")

    def test_prose_after_rejected(self):
        _reject(self, _json() + " thanks!", "invalid_json")

    def test_non_object_rejected(self):
        for raw in ("[1, 2, 3]", "\"a string\"", "5", "true", "null"):
            _reject(self, raw, "not_object")

    def test_missing_field(self):
        _reject(self, json.dumps({"answer_text": "a", "unable_to_answer": False}), "missing_field")

    def test_extra_field(self):
        obj = {"answer_text": "a", "unable_to_answer": False, "citations": ["finding:F1"], "x": 1}
        _reject(self, json.dumps(obj), "extra_field")


class TestTypeRejection(unittest.TestCase):
    def test_answer_text_wrong_type(self):
        _reject(self, json.dumps({"answer_text": 5, "unable_to_answer": False,
                                  "citations": ["finding:F1"]}), "wrong_type")

    def test_unable_wrong_type_int(self):
        _reject(self, json.dumps({"answer_text": "a", "unable_to_answer": 1,
                                  "citations": ["finding:F1"]}), "wrong_type")

    def test_unable_wrong_type_string(self):
        _reject(self, json.dumps({"answer_text": "a", "unable_to_answer": "true",
                                  "citations": ["finding:F1"]}), "wrong_type")

    def test_citations_wrong_type(self):
        _reject(self, json.dumps({"answer_text": "a", "unable_to_answer": False,
                                  "citations": "finding:F1"}), "wrong_type")

    def test_nested_citation_value_rejected(self):
        _reject(self, json.dumps({"answer_text": "a", "unable_to_answer": False,
                                  "citations": [{"k": "finding:F1"}]}), "wrong_type")

    def test_null_field_rejected(self):
        _reject(self, json.dumps({"answer_text": None, "unable_to_answer": False,
                                  "citations": ["finding:F1"]}), "null_field")

    def test_empty_citation_rejected(self):
        _reject(self, json.dumps({"answer_text": "a", "unable_to_answer": False,
                                  "citations": [""]}), "empty_citation")

    def test_duplicate_citation_rejected(self):
        _reject(self, json.dumps({"answer_text": "a", "unable_to_answer": False,
                                  "citations": ["finding:F1", "finding:F1"]}), "duplicate_citation")


class TestCrossField(unittest.TestCase):
    def test_unable_true_with_citations(self):
        _reject(self, _json(unable=True, citations=("finding:F1",)), "unable_with_citations")

    def test_substantive_empty_text(self):
        _reject(self, _json(answer_text="", unable=False, citations=("finding:F1",)), "empty_answer")

    def test_substantive_no_citations(self):
        _reject(self, _json(unable=False, citations=()), "no_citations")


class TestVersioning(unittest.TestCase):
    def test_unsupported_schema_version(self):
        _reject(self, _json(), "unsupported_schema_version", schema_version="v2")


class TestConfiguredLimits(unittest.TestCase):
    def test_answer_length_limit(self):
        _reject(self, _json(answer_text="abcd"), "answer_too_long",
                limits=ResponseValidationLimits(max_answer_chars=3))

    def test_citation_count_limit(self):
        raw = _json(citations=("finding:F1", "run:R1"))
        _reject(self, raw, "too_many_citations", limits=ResponseValidationLimits(max_citations=1))

    def test_citation_key_length_limit(self):
        _reject(self, _json(citations=("finding:F1",)), "citation_key_too_long",
                limits=ResponseValidationLimits(max_citation_key_chars=5))

    def test_none_limits_are_unlimited(self):
        out = ResponseValidator(ResponseValidationLimits()).validate(_json(answer_text="x" * 10_000))
        self.assertTrue(out.answer_text)

    def test_zero_limit_is_valid_and_enforced(self):
        # 0 is a valid configured limit (not None): any citation key over 0 chars is rejected.
        _reject(self, _json(), "citation_key_too_long",
                limits=ResponseValidationLimits(max_citation_key_chars=0))

    def test_invalid_limits_rejected(self):
        for kwargs in ({"max_answer_chars": -1}, {"max_citations": True},
                       {"max_citation_key_chars": 1.5}):
            with self.assertRaises(ValueError):
                ResponseValidationLimits(**kwargs)


class TestErrorPrivacy(unittest.TestCase):
    def test_errors_contain_no_raw_response_text(self):
        raw = _json(answer_text="SUPERSECRET-CONTENT", unable=False, citations=())  # fails no_citations
        err = _reject(self, raw, "no_citations")
        blob = "%s|%s|%s" % (err.message, err.code, err.detail)
        self.assertNotIn("SUPERSECRET-CONTENT", blob)
        self.assertIsNone(err.detail)


if __name__ == "__main__":
    unittest.main()
