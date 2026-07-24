# Verifies: Phase 4C.6 composition-root wiring of AskFinService (provider selection, runtime fallback,
# injected authorization, conversation_recorded). No real network (opener injected) and no real sleep
# (retry delay defaults to 0). End-to-end paths use NullProvider.
import json
import unittest
import urllib.error

from finsight.app import AiExplanationServices, build_ai_explanation_service
from finsight.application.ai.ask_fin_contracts import (
    AiAuthorizationContext, AskFinRequest, AskFinStatus,
)
from finsight.infrastructure.ai.config import load_ai_runtime_settings
from tests.ai.support import make, seed_review


class OkAuth:
    def authorize(self, *, user_id, cycle_id):
        return AiAuthorizationContext(user_id, cycle_id, "review_readonly", True, True)


def _settings(**env):
    return load_ai_runtime_settings(env=env)


class _Resp:
    def __init__(self, body):
        self._body = json.dumps(body).encode("utf-8")
    def read(self):
        return self._body
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


class _PathOpener:
    """Serves /api/tags from `tags`; for /api/chat returns `chat` or raises `chat_exc`."""
    def __init__(self, tags, chat=None, chat_exc=None):
        self._tags, self._chat, self._chat_exc = tags, chat, chat_exc
    def __call__(self, req, timeout):
        if req.full_url.endswith("/api/tags"):
            return _Resp(self._tags)
        if self._chat_exc is not None:
            raise self._chat_exc
        return _Resp(self._chat)


def _raise_opener(exc):
    def _open(req, timeout):
        raise exc
    return _open


class TestProviderSelection(unittest.TestCase):
    def test_none_selects_null(self):
        _tmp, c, ai = make()
        svc = build_ai_explanation_service(c, ai, authorization=OkAuth(), settings=_settings())
        self.assertIsInstance(svc, AiExplanationServices)
        self.assertFalse(svc.provider_status.generation_available)
        self.assertEqual(svc.provider_status.reason, "provider_disabled")

    def test_ollama_healthy_selects_ollama(self):
        _tmp, c, ai = make()
        opener = _PathOpener(tags={"models": [{"name": "llama3.2:3b"}]})
        svc = build_ai_explanation_service(c, ai, authorization=OkAuth(),
                                           settings=_settings(FINSIGHT_AI_PROVIDER="ollama"),
                                           opener=opener)
        self.assertTrue(svc.provider_status.generation_available)
        self.assertEqual(svc.provider_status.reason, "ok")

    def test_ollama_unavailable_selects_null(self):
        _tmp, c, ai = make()
        opener = _raise_opener(urllib.error.URLError(ConnectionRefusedError("refused")))
        svc = build_ai_explanation_service(c, ai, authorization=OkAuth(),
                                           settings=_settings(FINSIGHT_AI_PROVIDER="ollama"),
                                           opener=opener)
        self.assertFalse(svc.provider_status.generation_available)
        self.assertEqual(svc.provider_status.reason, "unreachable")


class TestEndToEndWiring(unittest.TestCase):
    def _svc(self, **kw):
        _tmp, c, ai = make()
        seed_review(c, _tmp, "2026-07")
        return c, ai, build_ai_explanation_service(c, ai, authorization=OkAuth(), **kw)

    def test_none_provider_degraded_end_to_end(self):
        c, ai, svc = self._svc(settings=_settings())
        res = svc.ask_fin.explain(AskFinRequest("local-user", "2026-07", "why is 6100 high?"))
        self.assertEqual(res.status, AskFinStatus.DEGRADED)      # NullProvider refusal, validated
        self.assertIsNotNone(res.answer)
        self.assertIsNone(res.metadata.conversation_recorded)    # one-shot
        self.assertEqual(res.metadata.masking_policy_version, "v1")

    def test_runtime_fallback_after_startup(self):
        _tmp, c, ai = make()
        seed_review(c, _tmp, "2026-07")
        # healthy at startup (tags ok → Ollama active) but chat refuses at call time → runtime degrades
        opener = _PathOpener(tags={"models": [{"name": "llama3.2:3b"}]},
                             chat_exc=urllib.error.URLError(ConnectionRefusedError("refused")))
        svc = build_ai_explanation_service(c, ai, authorization=OkAuth(),
                                           settings=_settings(FINSIGHT_AI_PROVIDER="ollama"),
                                           opener=opener)
        self.assertTrue(svc.provider_status.generation_available)   # Ollama selected active
        res = svc.ask_fin.explain(AskFinRequest("local-user", "2026-07", "why?"))
        self.assertEqual(res.status, AskFinStatus.DEGRADED)          # degraded to NullProvider mid-call

    def test_conversation_recorded_true(self):
        _tmp, c, ai = make()
        seed_review(c, _tmp, "2026-07")
        conv = ai.conversations.create("local-user", "2026-07", "t")
        svc = build_ai_explanation_service(c, ai, authorization=OkAuth(), settings=_settings())
        res = svc.ask_fin.explain(AskFinRequest("local-user", "2026-07", "why?",
                                                conversation_id=conv.conversation_id))
        self.assertTrue(res.metadata.conversation_recorded)

    def test_conversation_recorded_none_when_disabled(self):
        _tmp, c, ai = make()
        seed_review(c, _tmp, "2026-07")
        ai.preferences.set("local-user", "conversation_persistence", False)
        conv = ai.conversations.create("local-user", "2026-07", "t")
        svc = build_ai_explanation_service(c, ai, authorization=OkAuth(), settings=_settings())
        res = svc.ask_fin.explain(AskFinRequest("local-user", "2026-07", "why?",
                                                conversation_id=conv.conversation_id))
        self.assertIsNone(res.metadata.conversation_recorded)

    def test_authorization_denied_is_refused(self):
        _tmp, c, ai = make()
        seed_review(c, _tmp, "2026-07")

        class DenyAuth:
            def authorize(self, *, user_id, cycle_id):
                from finsight.application.ai.errors import AiAuthorizationError
                raise AiAuthorizationError("no consent", code="consent_missing")
        svc = build_ai_explanation_service(c, ai, authorization=DenyAuth(), settings=_settings())
        res = svc.ask_fin.explain(AskFinRequest("local-user", "2026-07", "why?"))
        self.assertEqual(res.status, AskFinStatus.REFUSED)
        self.assertIsNone(res.answer)


if __name__ == "__main__":
    unittest.main()
