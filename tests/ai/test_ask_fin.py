# Verifies: Phase 4C.5 AskFinService orchestration (FR-099). Deterministic fakes/spies only — a fake
# clock, fake id generator, fake sleeper (no real sleeping), fake journal, and scripted providers.
import json
import types
import unittest

from finsight.application.ai.ask_fin import (
    AskFinService, AiContextSources, AiPipeline, AiOrchestrationInfra,
)
from finsight.application.ai.ask_fin_contracts import (
    AiAuthorizationContext, AskFinRequest, AskFinStage, AskFinStatus,
)
from finsight.application.ai.citations import CitationVerifier
from finsight.application.ai.contracts import ProviderStatus, RawProviderResponse
from finsight.application.ai.errors import (
    AiAuthorizationError, AiScopeError, ConversationNotFoundError, GroundingUnavailableError,
    MaskingError, PromptBuildError, ProviderTimeoutError, ProviderUnavailableError,
)
from finsight.application.ai.masking import MaskingService
from finsight.application.ai.prompt.budget import ContextBudget
from finsight.application.ai.prompt.builder import PromptBuilder
from finsight.application.ai.retry import RetryPolicy
from finsight.application.ai.runtime import AiProviderRuntime
from finsight.application.ai.validation import ResponseValidator
from finsight.domain.ai.contracts import (
    AiGroundingContext, GroundedFinding, GroundedReview, InteractionEvent, ProviderConfiguration,
)
from finsight.infrastructure.ai.providers.null import NullProvider

VALID = '{"answer_text": "grounded explanation", "unable_to_answer": false, "citations": ["finding:F1"]}'
REFUSAL = '{"answer_text": "not enough context", "unable_to_answer": true, "citations": []}'
MALFORMED = 'not json at all'
BAD_CITE = '{"answer_text": "x", "unable_to_answer": false, "citations": ["finding:NOPE"]}'
EMAIL = "jane.doe@example.com"


def _grounding(with_email=True):
    note = ("contact %s" % EMAIL) if with_email else "no pii"
    return AiGroundingContext(
        review=GroundedReview("2026-07", "July", "2026", "Exported", 1),
        findings=[GroundedFinding("F1", "6100", "R", "Low", "variance", "2026-07",
                                  {"note": note}, ["GED:6100"], "New")],
    )


# --- fakes ---
class FakeAuth:
    def __init__(self, allow=True, code="consent_denied", order=None):
        self.allow, self.code, self._order = allow, code, order
    def authorize(self, *, user_id, cycle_id):
        if self._order is not None:
            self._order.append("authorization")
        if not self.allow:
            raise AiAuthorizationError("not permitted", code=self.code)
        return AiAuthorizationContext(user_id, cycle_id, "review_readonly", True, True)


class FakeGrounding:
    def __init__(self, ctx, exc=None, order=None):
        self._ctx, self._exc, self._order = ctx, exc, order
    def context(self, cycle_id):
        if self._order is not None:
            self._order.append("grounding")
        if self._exc is not None:
            raise self._exc
        return self._ctx


class FakeConversations:
    def __init__(self, messages=(), load_exc=None, fail_append=False):
        self._messages, self._load_exc, self._fail = list(messages), load_exc, fail_append
        self.appended = []
        self.load_calls = 0
    def load(self, conversation_id, user_id, cycle_id):
        self.load_calls += 1
        if self._load_exc is not None:
            raise self._load_exc
        return ("conv", list(self._messages))
    def append_user_message(self, conversation_id, user_id, cycle_id, content):
        if self._fail:
            raise RuntimeError("append failed")
        self.appended.append(("user", content))
    def append_assistant_message(self, conversation_id, user_id, cycle_id, content):
        if self._fail:
            raise RuntimeError("append failed")
        self.appended.append(("assistant", content))


class FakeMemory:
    def __init__(self, entries=(), order=None):
        self._entries, self._order = list(entries), order
    def list(self, user_id, cycle_id):
        if self._order is not None:
            self._order.append("memory")
        return list(self._entries)


class FakePreferences:
    def __init__(self, values=None, order=None, persist=True):
        self._v = values or {"audience": "reviewer", "answer_detail": "standard"}
        self._order = order
        self._persist = persist
    def get(self, user_id, key, default=None):
        if self._order is not None:
            self._order.append("preferences")
        return self._v.get(key, default)
    def conversation_persistence_enabled(self, user_id):
        return self._persist


class ScriptedProvider:
    """Each call consumes the next script item (Exception → raise; str → return as text). Once the
    script is exhausted the last item repeats."""
    def __init__(self, script, generation_available=True, name="live", model="m", order=None):
        self._script = list(script)
        self._gen, self._name, self._model, self._order = generation_available, name, model, order
        self.calls = 0
    def available(self):
        return True
    def status(self):
        return ProviderStatus(operational=True, generation_available=self._gen, reason="")
    def generate(self, request, config):
        self.calls += 1
        if self._order is not None:
            self._order.append("provider")
        item = self._script[self.calls - 1] if self.calls - 1 < len(self._script) else self._script[-1]
        if isinstance(item, Exception):
            raise item
        return RawProviderResponse(text=item, provider=self._name, model=self._model, metadata={})


class RecordingBuilder:
    def __init__(self, inner):
        self._inner = inner
        self.seen = None
    def build(self, *, grounding, question, conversation, memory, audience=None, answer_detail=None):
        self.seen = {"grounding": grounding, "question": question, "conversation": conversation,
                     "memory": memory, "audience": audience, "answer_detail": answer_detail}
        return self._inner.build(grounding=grounding, question=question, conversation=conversation,
                                 memory=memory, audience=audience, answer_detail=answer_detail)


class RaisingBuilder:
    def build(self, **kwargs):
        raise PromptBuildError("cannot build", code="prompt_build_failed")


class RaisingMasking:
    def mask(self, **kwargs):
        raise MaskingError("masking failed", code="masking_failed")


class FakeJournal:
    def __init__(self, fail=False):
        self.entries, self._fail = [], fail
    def append(self, entry):
        if self._fail:
            raise RuntimeError("journal down")
        self.entries.append(entry)


class FakeClock:
    def now(self):
        return "2026-07-24T00:00:00Z"


class FakeIds:
    def __init__(self):
        self.n = 0
    def __call__(self):
        self.n += 1
        return "id-%d" % self.n


class FakeSleeper:
    def __init__(self):
        self.slept = []
    def sleep(self, seconds):
        self.slept.append(seconds)


def _wire(**over):
    order = over.get("order")
    ctx = over.get("grounding_ctx", _grounding())
    grounding = FakeGrounding(ctx, exc=over.get("grounding_exc"), order=order)
    conversations = over.get("conversations", FakeConversations())
    memory = FakeMemory(over.get("memory", ()), order=order)
    prefs = over.get("prefs", FakePreferences(order=order))
    auth = over.get("auth", FakeAuth(order=order))
    provider = over.get("provider", ScriptedProvider([VALID], order=order))
    fallback = over.get("fallback", NullProvider())
    config = over.get("config", ProviderConfiguration("live", "m"))
    runtime = over.get("runtime", AiProviderRuntime(provider, fallback, config))
    masking = over.get("masking", MaskingService())
    builder = over.get("builder", PromptBuilder(ContextBudget()))
    validator = over.get("validator", ResponseValidator())
    verifier = over.get("verifier", CitationVerifier())
    journal = over.get("journal", FakeJournal())
    sleeper = over.get("sleeper", FakeSleeper())
    retry = over.get("retry", RetryPolicy())
    monotonic = over.get("monotonic")

    service = AskFinService(
        authorization=auth,
        context=AiContextSources(grounding=grounding, conversations=conversations, memory=memory,
                                 preferences=prefs),
        pipeline=AiPipeline(masking=masking, prompt_builder=builder, provider_runtime=runtime,
                            validator=validator, verifier=verifier),
        infra=AiOrchestrationInfra(journal=journal, retry_policy=retry, sleeper=sleeper,
                                   clock=FakeClock(), new_id=FakeIds(), monotonic=monotonic),
    )
    return service, types.SimpleNamespace(auth=auth, grounding=grounding, conversations=conversations,
                                          provider=provider, journal=journal, sleeper=sleeper,
                                          builder=builder)


def _req(**over):
    base = dict(user_id="u", cycle_id="2026-07", question="why is 6100 high?")
    base.update(over)
    return AskFinRequest(**base)


class TestHappyPath(unittest.TestCase):
    def test_ok_with_substantive_answer(self):
        svc, bag = _wire()
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.OK)
        self.assertIsNotNone(res.answer)
        self.assertFalse(res.answer.unable_to_answer)
        self.assertEqual(res.last_stage, AskFinStage.COMPLETE)
        self.assertEqual(bag.provider.calls, 1)

    def test_boundary_stage_order(self):
        order = []
        svc, _ = _wire(order=order)
        svc.explain(_req())
        # preferences is read twice (audience + answer_detail); collapse repeats for the order check
        collapsed = [s for i, s in enumerate(order) if i == 0 or s != order[i - 1]]
        self.assertEqual(collapsed, ["authorization", "grounding", "memory", "preferences", "provider"])

    def test_deterministic_result(self):
        r1 = _wire()[0].explain(_req())
        r2 = _wire()[0].explain(_req())
        self.assertEqual(r1, r2)


class TestPreferenceResolution(unittest.TestCase):
    def test_request_overrides_preference(self):
        rec = RecordingBuilder(PromptBuilder(ContextBudget()))
        svc, _ = _wire(builder=rec)
        svc.explain(_req(audience="executive", answer_detail="detailed"))
        self.assertEqual(rec.seen["audience"], "executive")
        self.assertEqual(rec.seen["answer_detail"], "detailed")

    def test_preference_fallback(self):
        rec = RecordingBuilder(PromptBuilder(ContextBudget()))
        svc, _ = _wire(builder=rec)
        svc.explain(_req())
        self.assertEqual(rec.seen["audience"], "reviewer")
        self.assertEqual(rec.seen["answer_detail"], "standard")


class TestAuthorizationAndScope(unittest.TestCase):
    def test_authorization_denied_is_refused(self):
        order = []
        svc, bag = _wire(auth=FakeAuth(allow=False, code="consent_denied", order=order), order=order)
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.REFUSED)
        self.assertIsNone(res.answer)
        self.assertEqual(res.error_code, "consent_denied")
        self.assertEqual(res.last_stage, AskFinStage.AUTHORIZATION)
        self.assertEqual(bag.provider.calls, 0)
        self.assertEqual(order, ["authorization"])          # fail-fast: grounding never reached

    def test_missing_consent_is_refused(self):
        svc, _ = _wire(auth=FakeAuth(allow=False, code="consent_missing"))
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.REFUSED)
        self.assertEqual(res.error_code, "consent_missing")

    def test_scope_failure_is_refused(self):
        conv = FakeConversations(load_exc=AiScopeError("outside scope"))
        svc, bag = _wire(conversations=conv)
        res = svc.explain(_req(conversation_id="c1"))
        self.assertEqual(res.status, AskFinStatus.REFUSED)
        self.assertIsNone(res.answer)
        self.assertEqual(res.last_stage, AskFinStage.SCOPE)
        self.assertEqual(bag.provider.calls, 0)

    def test_conversation_not_found_is_failed(self):
        conv = FakeConversations(load_exc=ConversationNotFoundError("missing", "c1"))
        svc, _ = _wire(conversations=conv)
        res = svc.explain(_req(conversation_id="c1"))
        self.assertEqual(res.status, AskFinStatus.FAILED)
        self.assertIsNone(res.answer)
        self.assertEqual(res.last_stage, AskFinStage.SCOPE)


class TestGroundingMaskingPrompt(unittest.TestCase):
    def test_grounding_no_review_is_failed(self):
        svc, bag = _wire(grounding_ctx=AiGroundingContext(review=None))
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.FAILED)
        self.assertEqual(res.last_stage, AskFinStage.GROUNDING)
        self.assertEqual(bag.provider.calls, 0)

    def test_grounding_unavailable_error_is_failed(self):
        svc, _ = _wire(grounding_exc=GroundingUnavailableError("none"))
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.FAILED)
        self.assertEqual(res.last_stage, AskFinStage.GROUNDING)

    def test_masking_failure_stops_before_builder_and_provider(self):
        rec = RecordingBuilder(PromptBuilder(ContextBudget()))
        svc, bag = _wire(masking=RaisingMasking(), builder=rec)
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.FAILED)
        self.assertEqual(res.last_stage, AskFinStage.MASKING)
        self.assertIsNone(rec.seen)                          # builder never called
        self.assertEqual(bag.provider.calls, 0)

    def test_only_masked_values_reach_prompt_builder(self):
        rec = RecordingBuilder(PromptBuilder(ContextBudget()))
        svc, _ = _wire(builder=rec)
        svc.explain(_req(question="email me at %s" % EMAIL))
        # the question the builder saw is redacted; the raw email appears nowhere the builder received
        self.assertIn("[REDACTED_EMAIL]", rec.seen["question"])
        blob = repr(rec.seen)
        self.assertNotIn(EMAIL, blob)

    def test_prompt_build_failure_is_failed(self):
        svc, bag = _wire(builder=RaisingBuilder())
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.FAILED)
        self.assertEqual(res.last_stage, AskFinStage.PROMPT_BUILD)
        self.assertEqual(bag.provider.calls, 0)


class TestProviderOutcomes(unittest.TestCase):
    def test_null_provider_as_primary_is_degraded(self):
        svc, _ = _wire(provider=NullProvider())
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.DEGRADED)
        self.assertIsNotNone(res.answer)
        self.assertTrue(res.answer.unable_to_answer)

    def test_active_unavailable_degrades_to_fallback(self):
        svc, _ = _wire(provider=ScriptedProvider([ProviderUnavailableError("down")]))
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.DEGRADED)
        self.assertIsNotNone(res.answer)

    def test_active_refusal_is_unanswerable(self):
        svc, _ = _wire(provider=ScriptedProvider([REFUSAL], generation_available=True))
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.UNANSWERABLE)
        self.assertIsNotNone(res.answer)
        self.assertTrue(res.answer.unable_to_answer)


class TestRetry(unittest.TestCase):
    def test_timeout_retry_then_success(self):
        svc, bag = _wire(provider=ScriptedProvider([ProviderTimeoutError("t"), VALID]),
                         retry=RetryPolicy(max_timeout_retries=1, retry_delay_seconds=0.5))
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.OK)
        self.assertEqual(res.metadata.timeout_retries, 1)
        self.assertEqual(res.metadata.provider_attempts, 2)
        self.assertEqual(bag.sleeper.slept, [0.5])

    def test_timeout_exhausted_is_failed(self):
        svc, _ = _wire(provider=ScriptedProvider([ProviderTimeoutError("t")]),
                       retry=RetryPolicy(max_timeout_retries=1))
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.FAILED)
        self.assertEqual(res.last_stage, AskFinStage.PROVIDER)
        self.assertEqual(res.metadata.timeout_retries, 1)
        self.assertEqual(res.metadata.provider_attempts, 2)

    def test_malformed_retry_then_success(self):
        svc, bag = _wire(provider=ScriptedProvider([MALFORMED, VALID]),
                         retry=RetryPolicy(max_response_format_retries=1))
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.OK)
        self.assertEqual(res.metadata.validation_retries, 1)
        self.assertEqual(res.metadata.provider_attempts, 2)

    def test_malformed_exhausted_is_failed(self):
        svc, _ = _wire(provider=ScriptedProvider([MALFORMED]),
                       retry=RetryPolicy(max_response_format_retries=1))
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.FAILED)
        self.assertEqual(res.last_stage, AskFinStage.VALIDATION)
        self.assertEqual(res.metadata.validation_retries, 1)

    def test_citation_rejection_has_no_retry(self):
        svc, bag = _wire(provider=ScriptedProvider([BAD_CITE]),
                         retry=RetryPolicy(max_response_format_retries=3, max_timeout_retries=3))
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.FAILED)
        self.assertEqual(res.last_stage, AskFinStage.CITATION)
        self.assertEqual(bag.provider.calls, 1)              # citation errors never retry
        self.assertEqual(bag.sleeper.slept, [])              # and never sleep


class TestAiAnswerPresence(unittest.TestCase):
    def test_answer_none_for_failed_and_refused(self):
        refused, _ = _wire(auth=FakeAuth(allow=False))
        self.assertIsNone(refused.explain(_req()).answer)
        failed, _ = _wire(builder=RaisingBuilder())
        self.assertIsNone(failed.explain(_req()).answer)

    def test_answer_present_only_for_validated_verified(self):
        for prov, status in ((ScriptedProvider([VALID]), AskFinStatus.OK),
                             (NullProvider(), AskFinStatus.DEGRADED),
                             (ScriptedProvider([REFUSAL]), AskFinStatus.UNANSWERABLE)):
            svc, _ = _wire(provider=prov)
            res = svc.explain(_req())
            self.assertEqual(res.status, status)
            self.assertIsNotNone(res.answer)


class TestConversationPersistence(unittest.TestCase):
    def test_persists_user_and_assistant_on_valid_answer(self):
        conv = FakeConversations()
        svc, _ = _wire(conversations=conv)
        res = svc.explain(_req(conversation_id="c1"))
        self.assertEqual(conv.appended,
                         [("user", "why is 6100 high?"), ("assistant", "grounded explanation")])
        self.assertTrue(res.metadata.conversation_recorded)

    def test_no_persistence_on_failure(self):
        conv = FakeConversations()
        svc, _ = _wire(conversations=conv, builder=RaisingBuilder())
        res = svc.explain(_req(conversation_id="c1"))
        self.assertEqual(conv.appended, [])
        self.assertIsNone(res.metadata.conversation_recorded)   # persist never attempted (no answer)

    def test_no_persistence_for_one_shot(self):
        conv = FakeConversations()
        svc, _ = _wire(conversations=conv)
        res = svc.explain(_req())                            # no conversation_id
        self.assertEqual(conv.appended, [])
        self.assertEqual(conv.load_calls, 0)
        self.assertIsNone(res.metadata.conversation_recorded)

    def test_conversation_recorded_false_on_persistence_failure(self):
        conv = FakeConversations(fail_append=True)
        svc, _ = _wire(conversations=conv)
        res = svc.explain(_req(conversation_id="c1"))
        self.assertEqual(res.status, AskFinStatus.OK)        # valid answer NOT corrupted
        self.assertIsNotNone(res.answer)
        self.assertFalse(res.metadata.conversation_recorded)

    def test_conversation_recorded_none_when_persistence_disabled(self):
        conv = FakeConversations()
        svc, _ = _wire(conversations=conv, prefs=FakePreferences(persist=False))
        res = svc.explain(_req(conversation_id="c1"))
        self.assertEqual(conv.appended, [])
        self.assertIsNone(res.metadata.conversation_recorded)


class TestJournaling(unittest.TestCase):
    def test_one_requested_and_one_completed_event(self):
        svc, bag = _wire()
        svc.explain(_req())
        events = [e.event_type for e in bag.journal.entries]
        self.assertEqual(events, [InteractionEvent.EXPLANATION_REQUESTED,
                                  InteractionEvent.EXPLANATION_COMPLETED])

    def test_one_completion_despite_retries(self):
        svc, bag = _wire(provider=ScriptedProvider([ProviderTimeoutError("t"), VALID]),
                         retry=RetryPolicy(max_timeout_retries=1))
        svc.explain(_req())
        completed = [e for e in bag.journal.entries
                     if e.event_type == InteractionEvent.EXPLANATION_COMPLETED]
        self.assertEqual(len(completed), 1)                  # not one per attempt

    def test_completed_status_and_metadata_shape(self):
        svc, bag = _wire()
        res = svc.explain(_req())
        completed = bag.journal.entries[-1]
        self.assertEqual(completed.status, "ok")
        self.assertEqual(completed.metadata["provider"], "live")
        self.assertEqual(completed.metadata["grounding_confidence"], res.answer.grounding_confidence.value)
        self.assertEqual(completed.metadata["citation_count"], 1)

    def test_journal_metadata_contains_no_content(self):
        svc, bag = _wire()
        svc.explain(_req(question="secret question about %s" % EMAIL))
        blob = json.dumps([e.metadata for e in bag.journal.entries])
        for forbidden in (EMAIL, "secret question", "grounded explanation"):
            self.assertNotIn(forbidden, blob)

    def test_journal_failure_does_not_discard_valid_answer(self):
        svc, _ = _wire(journal=FakeJournal(fail=True))
        res = svc.explain(_req())
        self.assertEqual(res.status, AskFinStatus.OK)
        self.assertIsNotNone(res.answer)
        self.assertFalse(res.metadata.journal_recorded)      # surfaced, never swallowed


class TestMetadataTiming(unittest.TestCase):
    def test_elapsed_ms_from_injected_monotonic(self):
        class Mono:
            def __init__(self): self.v = [1.0, 1.5]
            def __call__(self): return self.v.pop(0)
        svc, _ = _wire(monotonic=Mono())
        res = svc.explain(_req())
        self.assertEqual(res.metadata.elapsed_ms, 500)

    def test_elapsed_ms_none_without_monotonic(self):
        svc, _ = _wire()
        self.assertIsNone(svc.explain(_req()).metadata.elapsed_ms)


if __name__ == "__main__":
    unittest.main()
