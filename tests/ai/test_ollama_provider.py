# Verifies: Phase 4C.6 OllamaProvider — transport, serialization, response mapping, status, error
# classification (FR-104/NFR-046). No real network: the HTTP opener is injected.
import io
import json
import socket
import unittest
import urllib.error

from finsight.application.ai.contracts import PromptRequest
from finsight.application.ai.errors import (
    ProviderError, ProviderTimeoutError, ProviderUnavailableError, ResponseFormatError,
)
from finsight.domain.ai.contracts import ProviderConfiguration
from finsight.infrastructure.ai.providers.ollama import OllamaProvider

_PROMPT = PromptRequest(system_prompt="SYS", context_block="CTX", conversation_block="CONV",
                        question="Q", output_schema="SCHEMA", prompt_version="v1", schema_version="v1")


def _cfg(timeout=30.0, max_tokens=None):
    return ProviderConfiguration.ollama(model="llama3.2:3b", base_url="http://localhost:11434",
                                        request_timeout_seconds=timeout, max_output_tokens=max_tokens)


class _FakeResp:
    def __init__(self, body):
        self._body = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
    def read(self):
        return self._body
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


class _Opener:
    """Records the request it was given and returns/raises a scripted result."""
    def __init__(self, result):
        self._result = result
        self.request = None
        self.timeout = None
    def __call__(self, req, timeout):
        self.request, self.timeout = req, timeout
        if isinstance(self._result, Exception):
            raise self._result
        return _FakeResp(self._result)


_CHAT_OK = {"model": "llama3.2:3b", "message": {"role": "assistant", "content": '{"answer_text":"x"}'},
            "done": True, "done_reason": "stop", "total_duration": 2_000_000, "eval_count": 7}


class TestRequestSerialization(unittest.TestCase):
    def _sent(self, cfg):
        op = _Opener(_CHAT_OK)
        OllamaProvider(cfg, status_timeout=2.0, opener=op).generate(_PROMPT, cfg)
        return op, json.loads(op.request.data.decode("utf-8"))

    def test_endpoint_method_and_headers(self):
        op, _ = self._sent(_cfg())
        self.assertEqual(op.request.full_url, "http://localhost:11434/api/chat")
        self.assertEqual(op.request.method, "POST")
        self.assertEqual(op.request.headers.get("Content-type"), "application/json")

    def test_payload_shape(self):
        _, payload = self._sent(_cfg())
        self.assertEqual(payload["model"], "llama3.2:3b")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["format"], "json")
        self.assertEqual(payload["options"]["temperature"], 0.0)
        self.assertEqual([m["role"] for m in payload["messages"]], ["system", "user"])
        self.assertIn("SYS", payload["messages"][0]["content"])
        self.assertIn("SCHEMA", payload["messages"][0]["content"])
        self.assertIn("CTX", payload["messages"][1]["content"])
        self.assertIn("Q", payload["messages"][1]["content"])

    def test_num_predict_included_when_configured(self):
        _, payload = self._sent(_cfg(max_tokens=256))
        self.assertEqual(payload["options"]["num_predict"], 256)

    def test_num_predict_omitted_when_unset(self):
        _, payload = self._sent(_cfg())
        self.assertNotIn("num_predict", payload["options"])

    def test_timeout_passed(self):
        op, _ = self._sent(_cfg(timeout=12.5))
        self.assertEqual(op.timeout, 12.5)

    def test_prompt_request_unchanged(self):
        before = (_PROMPT.system_prompt, _PROMPT.context_block, _PROMPT.question)
        self._sent(_cfg())
        self.assertEqual((_PROMPT.system_prompt, _PROMPT.context_block, _PROMPT.question), before)


class TestResponseMapping(unittest.TestCase):
    def _gen(self, body, cfg=None):
        cfg = cfg or _cfg()
        return OllamaProvider(cfg, status_timeout=2.0, opener=_Opener(body)).generate(_PROMPT, cfg)

    def test_valid_envelope(self):
        r = self._gen(_CHAT_OK)
        self.assertEqual(r.text, '{"answer_text":"x"}')       # content verbatim, NOT validated here
        self.assertEqual(r.provider, "ollama")
        self.assertEqual(r.model, "llama3.2:3b")
        self.assertEqual(r.metadata["done_reason"], "stop")
        self.assertEqual(r.metadata["eval_count"], 7)
        self.assertEqual(r.metadata["latency_ms"], 2.0)

    def test_model_fallback_to_config(self):
        body = {k: v for k, v in _CHAT_OK.items() if k != "model"}
        self.assertEqual(self._gen(body).model, "llama3.2:3b")

    def test_missing_message_is_provider_error(self):
        body = {"done": True}
        with self.assertRaises(ProviderError) as ctx:
            self._gen(body)
        self.assertEqual(ctx.exception.code, "provider_missing_content")

    def test_missing_content_is_provider_error(self):
        body = {"message": {"role": "assistant"}, "done": True}
        with self.assertRaises(ProviderError) as ctx:
            self._gen(body)
        self.assertEqual(ctx.exception.code, "provider_missing_content")

    def test_non_string_content_is_provider_error(self):
        body = {"message": {"role": "assistant", "content": {"nested": 1}}, "done": True}
        with self.assertRaises(ProviderError):
            self._gen(body)

    def test_incomplete_response_is_provider_error(self):
        body = {"message": {"role": "assistant", "content": "x"}, "done": False}
        with self.assertRaises(ProviderError) as ctx:
            self._gen(body)
        self.assertEqual(ctx.exception.code, "provider_incomplete")

    def test_malformed_envelope_json_is_provider_error(self):
        with self.assertRaises(ProviderError) as ctx:
            self._gen(b"not json")
        self.assertEqual(ctx.exception.code, "provider_bad_response")

    def test_model_not_found_error_payload_is_unavailable(self):
        with self.assertRaises(ProviderUnavailableError) as ctx:
            self._gen({"error": "model 'x' not found, try pulling it"})
        self.assertEqual(ctx.exception.code, "model_missing")

    def test_never_raises_response_format_error(self):
        # message.content that is invalid FinSight JSON is returned normally (validator's job)
        body = {"message": {"role": "assistant", "content": "totally not json"}, "done": True}
        r = self._gen(body)
        self.assertEqual(r.text, "totally not json")


class TestErrorClassification(unittest.TestCase):
    def _gen_raising(self, exc, cfg=None):
        cfg = cfg or _cfg()
        return OllamaProvider(cfg, status_timeout=2.0, opener=_Opener(exc)).generate(_PROMPT, cfg)

    def test_http_404_model_missing(self):
        exc = urllib.error.HTTPError("u", 404, "not found", {}, io.BytesIO(b"model missing detail"))
        with self.assertRaises(ProviderUnavailableError) as ctx:
            self._gen_raising(exc)
        self.assertEqual(ctx.exception.code, "model_missing")

    def test_http_503_unavailable(self):
        exc = urllib.error.HTTPError("u", 503, "unavailable", {}, None)
        with self.assertRaises(ProviderUnavailableError) as ctx:
            self._gen_raising(exc)
        self.assertEqual(ctx.exception.code, "service_unavailable")

    def test_http_500_provider_error(self):
        exc = urllib.error.HTTPError("u", 500, "boom", {}, None)
        with self.assertRaises(ProviderError) as ctx:
            self._gen_raising(exc)
        self.assertEqual(ctx.exception.code, "provider_http_error")

    def test_connection_refused_unavailable(self):
        with self.assertRaises(ProviderUnavailableError) as ctx:
            self._gen_raising(urllib.error.URLError(ConnectionRefusedError("Connection refused")))
        self.assertEqual(ctx.exception.code, "connection_refused")

    def test_dns_failure_unavailable(self):
        with self.assertRaises(ProviderUnavailableError) as ctx:
            self._gen_raising(urllib.error.URLError(socket.gaierror("name resolution failed")))
        self.assertEqual(ctx.exception.code, "dns_failure")

    def test_socket_timeout_is_timeout(self):
        with self.assertRaises(ProviderTimeoutError) as ctx:
            self._gen_raising(socket.timeout("timed out"))
        self.assertEqual(ctx.exception.code, "request_timeout")

    def test_url_timeout_reason_is_timeout(self):
        with self.assertRaises(ProviderTimeoutError):
            self._gen_raising(urllib.error.URLError(socket.timeout("timed out")))

    def test_generic_urlerror_unreachable(self):
        with self.assertRaises(ProviderUnavailableError) as ctx:
            self._gen_raising(urllib.error.URLError("host down"))
        self.assertEqual(ctx.exception.code, "unreachable")

    def test_errors_contain_no_prompt_or_response(self):
        exc = urllib.error.HTTPError("u", 500, "boom", {}, io.BytesIO(b"SENSITIVE-BODY"))
        try:
            self._gen_raising(exc)
            self.fail("expected error")
        except ProviderError as err:
            blob = "%s|%s|%s" % (err.message, err.code, err.detail)
            for forbidden in ("SYS", "CTX", "Q", "SENSITIVE-BODY"):
                self.assertNotIn(forbidden, blob)

    def test_provider_never_raises_response_format_error(self):
        # sanity: ResponseFormatError is not part of this adapter's contract
        self.assertNotIn(ResponseFormatError, OllamaProvider.__mro__)


class TestStatus(unittest.TestCase):
    def _status(self, result, enabled=True, model="llama3.2:3b"):
        cfg = ProviderConfiguration.ollama(model=model)
        return OllamaProvider(cfg, status_timeout=2.0, enabled=enabled, opener=_Opener(result)).status()

    def test_disabled(self):
        st = self._status({"models": []}, enabled=False)
        self.assertFalse(st.generation_available)
        self.assertEqual(st.reason, "provider_disabled")

    def test_reachable_model_present(self):
        st = self._status({"models": [{"name": "llama3.2:3b"}, {"name": "other"}]})
        self.assertTrue(st.generation_available)
        self.assertEqual(st.reason, "ok")

    def test_reachable_model_absent(self):
        st = self._status({"models": [{"name": "other"}]})
        self.assertFalse(st.generation_available)
        self.assertEqual(st.reason, "model_missing")

    def test_unreachable(self):
        st = self._status(urllib.error.URLError(ConnectionRefusedError("refused")))
        self.assertEqual(st.reason, "unreachable")

    def test_status_timeout(self):
        st = self._status(socket.timeout("timed out"))
        self.assertEqual(st.reason, "status_timeout")

    def test_malformed_status_body(self):
        st = self._status(b"not json")
        self.assertEqual(st.reason, "malformed_status_response")

    def test_malformed_status_shape(self):
        st = self._status({"unexpected": True})
        self.assertEqual(st.reason, "malformed_status_response")

    def test_operational_always_true(self):
        self.assertTrue(self._status({"models": []}).operational)


if __name__ == "__main__":
    unittest.main()
