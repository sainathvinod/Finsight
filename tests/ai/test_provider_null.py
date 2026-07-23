import json
import unittest
from finsight.infrastructure.ai.providers.null import NullProvider
from finsight.application.ai.contracts import PromptRequest, RawProviderResponse
from finsight.domain.ai.contracts import ProviderConfiguration


def _req():
    return PromptRequest("sys", "ctx", "conv", "q", "schema")


class TestNullProvider(unittest.TestCase):
    def setUp(self):
        self.p = NullProvider()
        self.cfg = ProviderConfiguration.null()

    def test_implements_port_surface(self):
        self.assertTrue(hasattr(self.p, "available"))
        self.assertTrue(hasattr(self.p, "generate"))

    def test_always_available(self):
        self.assertTrue(self.p.available())

    def test_generate_is_deterministic(self):
        a = self.p.generate(_req(), self.cfg)
        b = self.p.generate(_req(), self.cfg)
        self.assertIsInstance(a, RawProviderResponse)
        self.assertEqual(a, b)                 # frozen dataclass equality; no clock/random
        self.assertEqual(a.provider, "null")
        self.assertEqual(a.model, "none")

    def test_safe_refusal_no_fabrication(self):
        a = self.p.generate(_req(), self.cfg)
        payload = json.loads(a.text)
        self.assertTrue(payload["unable_to_answer"])
        self.assertEqual(payload["citations"], [])
        low = a.text.lower()
        for token in ("finding", "severity", "variance", "approve", "reject"):
            self.assertNotIn(token, low)       # never fabricates deterministic financial content


if __name__ == "__main__":
    unittest.main()
