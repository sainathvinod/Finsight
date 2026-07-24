# Verifies: Phase 4C.6 AI runtime configuration loader — env-backed, fail-fast, no persistence.
import unittest

from finsight.infrastructure.ai.config import AiConfigError, load_ai_runtime_settings


def _load(**env):
    return load_ai_runtime_settings(env=env)


class TestDefaults(unittest.TestCase):
    def test_empty_env_defaults_to_none_provider(self):
        s = _load()
        self.assertEqual(s.provider, "none")
        self.assertEqual(s.provider_config.provider, "null")
        self.assertEqual(s.status_timeout_seconds, 2.0)
        self.assertEqual(s.retry_policy.max_response_format_retries, 1)
        self.assertEqual(s.retry_policy.max_timeout_retries, 0)
        self.assertEqual(s.retry_policy.retry_delay_seconds, 0.0)
        self.assertIsNone(s.validation_limits.max_answer_chars)

    def test_ollama_defaults(self):
        s = _load(FINSIGHT_AI_PROVIDER="ollama")
        self.assertEqual(s.provider, "ollama")
        self.assertEqual(s.provider_config.provider, "ollama")
        self.assertEqual(s.provider_config.base_url, "http://localhost:11434")
        self.assertEqual(s.provider_config.model, "llama3.2:3b")
        self.assertEqual(s.provider_config.temperature, 0.0)
        self.assertEqual(s.provider_config.request_timeout_seconds, 30.0)
        self.assertIsNone(s.provider_config.max_output_tokens)


class TestOverridesAndFallback(unittest.TestCase):
    def test_finsight_env_overrides(self):
        s = _load(FINSIGHT_AI_PROVIDER="ollama", FINSIGHT_OLLAMA_BASE_URL="http://host:9",
                  FINSIGHT_OLLAMA_MODEL="m2", FINSIGHT_AI_REQUEST_TIMEOUT="45",
                  FINSIGHT_AI_MAX_OUTPUT_TOKENS="128", FINSIGHT_AI_MAX_CITATIONS="5")
        self.assertEqual(s.provider_config.base_url, "http://host:9")
        self.assertEqual(s.provider_config.model, "m2")
        self.assertEqual(s.provider_config.request_timeout_seconds, 45.0)
        self.assertEqual(s.provider_config.max_output_tokens, 128)
        self.assertEqual(s.validation_limits.max_citations, 5)

    def test_bare_ollama_fallback(self):
        s = _load(FINSIGHT_AI_PROVIDER="ollama", OLLAMA_BASE_URL="http://bare:1", OLLAMA_MODEL="bm")
        self.assertEqual(s.provider_config.base_url, "http://bare:1")
        self.assertEqual(s.provider_config.model, "bm")

    def test_finsight_precedence_over_bare(self):
        s = _load(FINSIGHT_AI_PROVIDER="ollama", FINSIGHT_OLLAMA_MODEL="fin", OLLAMA_MODEL="bare")
        self.assertEqual(s.provider_config.model, "fin")


class TestFailFast(unittest.TestCase):
    def test_invalid_provider(self):
        with self.assertRaises(AiConfigError):
            _load(FINSIGHT_AI_PROVIDER="openai")

    def test_invalid_url(self):
        with self.assertRaises(AiConfigError):
            _load(FINSIGHT_AI_PROVIDER="ollama", FINSIGHT_OLLAMA_BASE_URL="localhost:11434")

    def test_empty_model(self):
        with self.assertRaises(AiConfigError):
            _load(FINSIGHT_AI_PROVIDER="ollama", FINSIGHT_OLLAMA_MODEL="   ")

    def test_negative_timeout(self):
        with self.assertRaises(AiConfigError):
            _load(FINSIGHT_AI_REQUEST_TIMEOUT="-1")

    def test_zero_timeout_rejected(self):
        with self.assertRaises(AiConfigError):
            _load(FINSIGHT_AI_STATUS_TIMEOUT="0")

    def test_non_numeric_timeout(self):
        with self.assertRaises(AiConfigError):
            _load(FINSIGHT_AI_REQUEST_TIMEOUT="true")

    def test_negative_retry(self):
        with self.assertRaises(AiConfigError):
            _load(FINSIGHT_AI_RETRY_FORMAT="-1")

    def test_invalid_output_tokens(self):
        with self.assertRaises(AiConfigError):
            _load(FINSIGHT_AI_PROVIDER="ollama", FINSIGHT_AI_MAX_OUTPUT_TOKENS="0")

    def test_invalid_validation_limit(self):
        with self.assertRaises(AiConfigError):
            _load(FINSIGHT_AI_MAX_ANSWER_CHARS="-5")

    def test_temperature_is_always_zero(self):
        s = _load(FINSIGHT_AI_PROVIDER="ollama")
        self.assertEqual(s.provider_config.temperature, 0.0)   # not env-overridable by contract


if __name__ == "__main__":
    unittest.main()
