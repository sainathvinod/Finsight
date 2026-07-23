import unittest
from finsight.domain.ai.contracts import (
    ProviderConfiguration, MaskingConfiguration, MaskCategory,
    DEFAULT_OLLAMA_BASE_URL, DEFAULT_OLLAMA_MODEL,
)
from finsight.application.ai.contracts import PromptRequest, RawProviderResponse


class TestProviderConfiguration(unittest.TestCase):
    def test_ollama_defaults(self):
        c = ProviderConfiguration.ollama()
        self.assertEqual(c.provider, "ollama")
        self.assertEqual(c.base_url, "http://localhost:11434")
        self.assertEqual(c.model, "llama3.2:3b")
        self.assertEqual(DEFAULT_OLLAMA_BASE_URL, "http://localhost:11434")
        self.assertEqual(DEFAULT_OLLAMA_MODEL, "llama3.2:3b")

    def test_temperature_fixed_zero(self):
        self.assertEqual(ProviderConfiguration.ollama().temperature, 0.0)
        self.assertEqual(ProviderConfiguration.null().temperature, 0.0)
        with self.assertRaises(ValueError):
            ProviderConfiguration("ollama", "m", "", temperature=0.7)

    def test_timeout_and_tokens_not_hardcoded(self):
        c = ProviderConfiguration.ollama()
        self.assertIsNone(c.request_timeout_seconds)   # supplied by configuration, never hardcoded
        self.assertIsNone(c.max_output_tokens)

    def test_immutable(self):
        c = ProviderConfiguration.null()
        with self.assertRaises(Exception):
            c.model = "x"           # frozen dataclass


class TestMaskingConfiguration(unittest.TestCase):
    def test_empty_name_list_by_default(self):
        m = MaskingConfiguration()
        self.assertEqual(m.employee_names, ())         # empty by default; never blocks execution
        self.assertTrue(m.mask_actor_fields)

    def test_categories_exclude_deterministic_financial_facts(self):
        vals = {c.value for c in MaskCategory}
        self.assertEqual(vals, {"employee_name", "email", "phone", "tax_id", "banking_id", "actor"})
        for never_masked in ("account", "gl_account", "finding", "rule", "variance", "percentage"):
            self.assertNotIn(never_masked, vals)


class TestExecutionContracts(unittest.TestCase):
    def test_prompt_request_versions_default(self):
        r = PromptRequest("sys", "ctx", "conv", "q", "schema")
        self.assertEqual(r.prompt_version, "v1")
        self.assertEqual(r.schema_version, "v1")

    def test_raw_response_metadata_defaults_empty(self):
        r = RawProviderResponse("t", "null", "none")
        self.assertEqual(r.metadata, {})


if __name__ == "__main__":
    unittest.main()
