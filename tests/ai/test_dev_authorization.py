# Verifies: Phase 4C.6A development/demo authorization (fail-closed) + config flag + smoke-test safety.
# NOT production consent. All provider work uses fakes; no network, no real sleep.
import sys
import unittest

from finsight.application.ai.ask_fin_contracts import AskFinRequest, AskFinStatus
from finsight.application.ai.errors import AiAuthorizationError
from finsight.infrastructure.ai.authorization import DevelopmentAiAuthorizationPolicy
from finsight.infrastructure.ai.config import AiConfigError, load_ai_runtime_settings
from tests.ai.support import make, seed_review
from finsight.app import build_ai_explanation_service


def _settings(**env):
    return load_ai_runtime_settings(env=env)


class TestDemoAuthorizedFlag(unittest.TestCase):
    def test_default_false(self):
        self.assertFalse(_settings().demo_authorized)

    def test_explicit_true_values(self):
        for v in ("1", "true", "TRUE", "yes", "On"):
            self.assertTrue(_settings(FINSIGHT_AI_DEMO_AUTHORIZED=v).demo_authorized, v)

    def test_explicit_false_values(self):
        for v in ("0", "false", "no", "off", ""):
            self.assertFalse(_settings(FINSIGHT_AI_DEMO_AUTHORIZED=v).demo_authorized, v)

    def test_invalid_value_rejected(self):
        with self.assertRaises(AiConfigError):
            _settings(FINSIGHT_AI_DEMO_AUTHORIZED="maybe")


class TestDevelopmentPolicy(unittest.TestCase):
    def test_authorized_true_returns_explanation_only_context(self):
        ctx = DevelopmentAiAuthorizationPolicy(True).authorize(user_id="u", cycle_id="c")
        self.assertTrue(ctx.user_consent)
        self.assertEqual(ctx.application_mode, "explanation_only")
        self.assertTrue(ctx.ai_capability_available)

    def test_authorized_false_fails_closed(self):
        with self.assertRaises(AiAuthorizationError) as ctx:
            DevelopmentAiAuthorizationPolicy(False).authorize(user_id="u", cycle_id="c")
        self.assertEqual(ctx.exception.code, "demo_not_authorized")

    def test_from_settings_default_denies(self):
        pol = DevelopmentAiAuthorizationPolicy.from_settings(_settings())
        with self.assertRaises(AiAuthorizationError):
            pol.authorize(user_id="u", cycle_id="c")

    def test_from_settings_gate_true_grants(self):
        pol = DevelopmentAiAuthorizationPolicy.from_settings(
            _settings(FINSIGHT_AI_DEMO_AUTHORIZED="true"))
        self.assertTrue(pol.authorize(user_id="u", cycle_id="c").user_consent)


class TestAuthorizationInPipeline(unittest.TestCase):
    def _explain(self, *, demo, provider="none", conversation_id=None):
        _tmp, container, ai = make()
        seed_review(container, _tmp, "2026-07")
        env = {"FINSIGHT_AI_PROVIDER": provider}
        if demo:
            env["FINSIGHT_AI_DEMO_AUTHORIZED"] = "true"
        settings = _settings(**env)
        svc = build_ai_explanation_service(
            container, ai, authorization=DevelopmentAiAuthorizationPolicy.from_settings(settings),
            settings=settings)
        return svc.ask_fin.explain(AskFinRequest("local-user", "2026-07", "why?",
                                                 conversation_id=conversation_id))

    def test_unauthorized_refused_no_provider_call(self):
        res = self._explain(demo=False)
        self.assertEqual(res.status, AskFinStatus.REFUSED)
        self.assertIsNone(res.answer)
        self.assertEqual(res.metadata.provider_attempts, 0)      # no provider call on refusal

    def test_authorized_allows_explanation_flow(self):
        # provider=none → NullProvider, but authorization passes so the pipeline runs to a validated
        # refusal (DEGRADED). NullProvider does NOT bypass authorization — it ran only because the gate
        # granted it.
        res = self._explain(demo=True)
        self.assertEqual(res.status, AskFinStatus.DEGRADED)
        self.assertIsNotNone(res.answer)

    def test_provider_availability_does_not_imply_authorization(self):
        # Even with a healthy provider selection, an unauthorized gate still REFUSES before any call.
        res = self._explain(demo=False, provider="none")
        self.assertEqual(res.status, AskFinStatus.REFUSED)

    def test_nullprovider_does_not_bypass_authorization(self):
        # provider=none uses NullProvider; unauthorized still REFUSES (no bypass).
        self.assertEqual(self._explain(demo=False).status, AskFinStatus.REFUSED)

    def test_deterministic_state_unchanged_by_explanation(self):
        _tmp, container, ai = make()
        seed_review(container, _tmp, "2026-07")
        before = container.finding_repo.list("2026-07")
        settings = _settings(FINSIGHT_AI_DEMO_AUTHORIZED="true")
        svc = build_ai_explanation_service(
            container, ai, authorization=DevelopmentAiAuthorizationPolicy.from_settings(settings),
            settings=settings)
        svc.ask_fin.explain(AskFinRequest("local-user", "2026-07", "why?"))
        self.assertEqual(container.finding_repo.list("2026-07"), before)  # no deterministic mutation


class TestFutureInjectedPolicyStillSupported(unittest.TestCase):
    def test_arbitrary_injected_policy(self):
        _tmp, container, ai = make()
        seed_review(container, _tmp, "2026-07")

        class OkAuth:
            def authorize(self, *, user_id, cycle_id):
                from finsight.application.ai.ask_fin_contracts import AiAuthorizationContext
                return AiAuthorizationContext(user_id, cycle_id, "explanation_only", True, True)
        svc = build_ai_explanation_service(container, ai, authorization=OkAuth(), settings=_settings())
        self.assertEqual(svc.ask_fin.explain(AskFinRequest("local-user", "2026-07", "q")).status,
                         AskFinStatus.DEGRADED)


class TestSmokeModuleSafety(unittest.TestCase):
    def test_imports_without_network(self):
        # Block network + real sleep, then import: importing must run nothing.
        import socket
        import time
        orig_conn, orig_sleep = socket.socket.connect, time.sleep
        socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(AssertionError("network on import"))
        time.sleep = lambda *a, **k: (_ for _ in ()).throw(AssertionError("sleep on import"))
        try:
            sys.modules.pop("scripts.smoke_ollama", None)
            import scripts.smoke_ollama as smoke
            self.assertTrue(callable(smoke.main))
            self.assertTrue(callable(smoke.run_provider_smoke))
            self.assertTrue(callable(smoke.run_pipeline_smoke))
        finally:
            socket.socket.connect, time.sleep = orig_conn, orig_sleep

    def test_main_aborts_without_ollama_provider(self):
        import scripts.smoke_ollama as smoke
        self.assertEqual(smoke.main(env={}), 2)                       # provider != ollama → abort

    def test_main_aborts_without_demo_authorization(self):
        import scripts.smoke_ollama as smoke
        self.assertEqual(smoke.main(env={"FINSIGHT_AI_PROVIDER": "ollama"}), 2)  # not authorized → abort


if __name__ == "__main__":
    unittest.main()
