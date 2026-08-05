"""Natural-language and evidence-depth acceptance tests for private Ask Fin.

These tests deliberately use the approved sealed May 2026 synthetic review.
The provider always reports that it cannot answer, so every successful
financial response must come from FinSight's deterministic closed-claim path.
No network client or external AI service is involved.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re

import pytest

from finsight.application.ai.contracts import ProviderStatus, RawProviderResponse
from finsight.application.ai.private_ask_fin import (
    DECISION_REFUSAL,
    PrivateAskFinService,
)
from finsight.application.ai.private_contracts import (
    AskFinContext,
    PrivateAskFinRequest,
    PrivateAskFinStatus,
)
from finsight.application.ai.private_grounding import V2FinancialGroundingService
from finsight.domain.ai.contracts import ProviderConfiguration
from tests.integration.test_private_ask_fin_v2_grounding import _sealed_review
from tests.support import FixedClock


_ACCOUNT_SCOPE = "00-0245|555035"
_ACCOUNT_NAME = "Outside Consultants' Fees"
_INSUFFICIENT_FRAGMENT = "enough verified information"
_CITATION = re.compile(r"\[([a-z][a-z0-9_-]*:[^\[\]\s]+)\]")


class _AllowActiveReviewer:
    def authorize(self, *, user_id, review_id):
        assert user_id == "local-user"
        assert review_id.startswith("rev_")


class _ClosedClaimOnlyLocalProvider:
    """A loopback-only fake that forces deterministic response recovery."""

    def __init__(self):
        self.calls = 0
        self.contexts: list[dict] = []
        self.configurations: list[ProviderConfiguration] = []

    def status(self):
        return ProviderStatus(True, True, "ok")

    def generate(self, request, config):
        self.calls += 1
        self.configurations.append(config)
        assert config.provider == "ollama"
        assert config.base_url == "http://127.0.0.1:11434"
        payload = request.context_block.split("\n", 1)[1].rsplit("\n", 1)[0]
        self.contexts.append(json.loads(payload))
        return RawProviderResponse(
            json.dumps(
                {
                    "answer_text": (
                        "I do not have enough recorded evidence in this "
                        "review to answer that question."
                    ),
                    "unable_to_answer": True,
                    "citations": [],
                }
            ),
            "ollama",
            config.model,
            {"model_version": config.model},
        )


class _Audit:
    def __init__(self):
        self.entries: list[dict] = []

    def append(self, value):
        self.entries.append(dict(value))


@dataclass
class _Harness:
    services: object
    review: object
    projection: dict
    provider: _ClosedClaimOnlyLocalProvider
    audit: _Audit
    active_review: dict[str, str]
    service: PrivateAskFinService

    def ask(
        self,
        question: str,
        *,
        context: AskFinContext | None = None,
        review_id: str | None = None,
    ):
        return self.service.ask(
            PrivateAskFinRequest(
                user_id="local-user",
                review_id=review_id or self.review.review_id,
                question=question,
                context=context,
            )
        )


@pytest.fixture
def harness(tmp_path) -> _Harness:
    _database_path, services, review, projection = _sealed_review(tmp_path)
    provider = _ClosedClaimOnlyLocalProvider()
    audit = _Audit()
    active_review = {"review_id": review.review_id}
    service = PrivateAskFinService(
        authorization=_AllowActiveReviewer(),
        grounding=V2FinancialGroundingService(services.financial_review),
        provider=provider,
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://127.0.0.1:11434",
            request_timeout_seconds=2.0,
        ),
        audit=audit,
        clock=FixedClock(),
        active_review_id=lambda: active_review["review_id"],
    )
    return _Harness(
        services=services,
        review=review,
        projection=projection,
        provider=provider,
        audit=audit,
        active_review=active_review,
        service=service,
    )


def _intent_value(result) -> str:
    value = getattr(result, "intent", None)
    if value is None:
        return ""
    return str(getattr(value, "value", value))


def _assert_active_grounding(harness: _Harness, result) -> None:
    assert result.status is PrivateAskFinStatus.OK
    assert result.validation_run_id == harness.projection["run_id"]
    assert result.citations
    assert all(
        citation.review_id == harness.review.review_id for citation in result.citations
    )
    assert all(
        citation.key in result.retrieved_record_keys for citation in result.citations
    )
    inline = set(_CITATION.findall(result.answer_text))
    assert inline == {citation.key for citation in result.citations}


def _source_rows(result) -> set[int]:
    return {
        int(citation.navigation_target["source_row"])
        for citation in result.citations
        if citation.navigation_target.get("source_row") is not None
    }


@pytest.mark.parametrize(
    "message",
    ("hi", "hello", "good morning", "thanks", "how are you?"),
)
def test_social_messages_are_natural_and_bypass_financial_retrieval(
    harness: _Harness,
    message: str,
):
    calls_before = harness.provider.calls

    result = harness.ask(message)

    assert result.status is PrivateAskFinStatus.OK
    assert _intent_value(result) == "greeting_or_social_acknowledgement"
    assert result.citations == ()
    assert result.retrieved_record_keys == ()
    assert harness.provider.calls == calls_before
    assert result.provider == "finsight"
    assert result.model == "deterministic-intent-v1"
    assert harness.audit.entries[-1]["provider"] == "finsight"
    assert "not enough" not in result.answer_text.casefold()
    assert any(
        phrase in result.answer_text.casefold()
        for phrase in ("fin", "welcome", "help", "you’re welcome", "you're welcome")
    )


@pytest.mark.parametrize("message", ("sc", "what?", "explain"))
def test_ambiguous_text_receives_clarification_not_evidence_refusal(
    harness: _Harness,
    message: str,
):
    calls_before = harness.provider.calls

    result = harness.ask(message)

    assert result.status is PrivateAskFinStatus.OK
    assert _intent_value(result) == "unsupported"
    assert result.citations == ()
    assert result.retrieved_record_keys == ()
    assert harness.provider.calls == calls_before
    assert result.provider == "finsight"
    assert harness.audit.entries[-1]["provider"] == "finsight"
    assert "not sure" in result.answer_text.casefold()
    assert message.casefold() in result.answer_text.casefold()
    assert "not enough" not in result.answer_text.casefold()
    assert "summar" in result.answer_text.casefold()
    assert "evidence" in result.answer_text.casefold()


def test_application_help_is_conversational_without_financial_retrieval(
    harness: _Harness,
):
    calls_before = harness.provider.calls

    result = harness.ask("How can FinSight help me?")

    assert result.status is PrivateAskFinStatus.OK
    assert _intent_value(result) == "application_help"
    assert result.citations == ()
    assert result.retrieved_record_keys == ()
    assert harness.provider.calls == calls_before
    assert "review" in result.answer_text.casefold()
    assert "finding" in result.answer_text.casefold()
    assert "evidence" in result.answer_text.casefold()


@pytest.mark.parametrize(
    "question",
    (
        "Summarize this review.",
        "Give me the main points.",
        "What should I know?",
    ),
)
def test_summary_variants_return_the_same_sealed_executive_facts(
    harness: _Harness,
    question: str,
):
    result = harness.ask(question)

    _assert_active_grounding(harness, result)
    assert _intent_value(result) == "review_summary"
    assert "May 2026" in result.answer_text
    assert "$10,372,000" in result.answer_text
    assert "$3,500,095" in result.answer_text
    assert "$9,382,095" in result.answer_text
    assert "5" in result.answer_text
    assert "4 High" in result.answer_text
    assert "missing" in result.answer_text.casefold()
    assert "incomplete" in result.answer_text.casefold()
    assert "selected projection" not in result.answer_text.casefold()
    assert "preserved projection" not in result.answer_text.casefold()


def test_whats_wrong_maps_to_grounded_findings_not_generic_insufficiency(
    harness: _Harness,
):
    result = harness.ask("What's wrong with this review?")

    _assert_active_grounding(harness, result)
    assert _intent_value(result) == "findings_summary"
    assert "5" in result.answer_text
    assert "555035" in result.answer_text
    assert "over budget" in result.answer_text.casefold()
    assert "missing" in result.answer_text.casefold()
    assert _INSUFFICIENT_FRAGMENT not in result.answer_text.casefold()


def test_specific_account_answer_has_financial_depth_and_exact_evidence(
    harness: _Harness,
):
    result = harness.ask("Why is Account 555035 over budget?")

    _assert_active_grounding(harness, result)
    assert _intent_value(result) == "account_question"
    assert _ACCOUNT_NAME in result.answer_text
    assert "$1,100,000" in result.answer_text
    assert "$1,250,000" in result.answer_text
    assert "$150,000" in result.answer_text
    assert "13.64%" in result.answer_text
    assert "APPS ASSOCIATES LLC" in result.answer_text
    assert re.search(
        r"Contributing GED source row \d+:.+Reference "
        r"(?!No reference recorded)[A-Za-z0-9_-]+",
        result.answer_text,
    ), result.answer_text
    assert "Budget Overrun" in result.answer_text
    assert "2.0.0" in result.answer_text
    assert "C91" in result.answer_text
    assert "246" in result.answer_text
    assert {91, 246}.issubset(_source_rows(result))

    resolved = getattr(result, "resolved_context", None)
    assert resolved is not None
    assert resolved.review_id == harness.review.review_id
    assert resolved.object_type == "account"
    assert resolved.object_id == _ACCOUNT_SCOPE
    assert resolved.validation_run_id == harness.projection["run_id"]


def test_vendor_department_transaction_and_comparison_intents_are_grounded(
    harness: _Harness,
):
    cases = (
        (
            "Which vendor contributed most?",
            "vendor_question",
            ("TEKSYSTEMS, INC",),
        ),
        (
            "Summarize Department 00-0245.",
            "department_question",
            ("00-0245", "$10,372,000"),
        ),
        (
            "Tell me about GED row 66.",
            "ged_transaction_question",
            ("533003", "$82.50", "PCARD_0126"),
        ),
        (
            "Compare budget and actual for Account 555035.",
            "comparison_request",
            ("$1,100,000", "$1,250,000", "$150,000"),
        ),
    )

    for question, expected_intent, expected_values in cases:
        result = harness.ask(question)
        _assert_active_grounding(harness, result)
        assert _intent_value(result) == expected_intent
        assert all(value in result.answer_text for value in expected_values)
        if expected_intent == "ged_transaction_question":
            assert 66 in _source_rows(result)


def test_incomplete_duplicate_and_first_finding_questions_are_evidence_rich(
    harness: _Harness,
):
    incomplete = harness.ask("Why is the review incomplete?")
    duplicate = harness.ask("Explain the duplicate transaction.")
    first = harness.ask("Explain the first finding.")

    for result in (incomplete, duplicate, first):
        _assert_active_grounding(harness, result)

    assert _intent_value(incomplete) == "findings_summary"
    assert "missing" in incomplete.answer_text.casefold()
    assert "Amount" in incomplete.answer_text
    assert "O87" in incomplete.answer_text
    assert "CORE-04" in incomplete.answer_text
    assert 87 in _source_rows(incomplete)

    assert _intent_value(duplicate) == "ged_transaction_question"
    assert "533003" in duplicate.answer_text
    assert "$82.50" in duplicate.answer_text
    assert "65" in duplicate.answer_text
    assert "66" in duplicate.answer_text
    assert "CORE-03" in duplicate.answer_text
    assert "2.0.0" in duplicate.answer_text
    assert {65, 66}.issubset(_source_rows(duplicate))

    assert _intent_value(first) == "findings_summary"
    assert "High" in first.answer_text
    assert "Budget Overrun" in first.answer_text
    assert "555035" in first.answer_text
    assert "$150,000" in first.answer_text
    assert {91, 246}.issubset(_source_rows(first))


def test_prior_result_context_supports_safe_natural_followups(
    harness: _Harness,
):
    first = harness.ask("Why is Account 555035 over budget?")
    _assert_active_grounding(harness, first)
    prior_scope = getattr(first, "resolved_context", None)
    assert prior_scope is not None

    followups = (
        ("Why?", ("555035", "$150,000")),
        ("Show evidence.", ("C91", "246")),
        ("Tell me more.", ("555035", "$1,250,000")),
        ("Which vendor?", ("APPS ASSOCIATES LLC",)),
        ("What should I inspect next?", ("evidence",)),
    )
    for question, expected_values in followups:
        result = harness.ask(question, context=prior_scope)
        _assert_active_grounding(harness, result)
        assert _intent_value(result) == "clarification_or_follow_up"
        assert all(
            value.casefold() in result.answer_text.casefold()
            for value in expected_values
        )
        assert getattr(result, "resolved_context", None) == prior_scope
        assert _INSUFFICIENT_FRAGMENT not in result.answer_text.casefold()


def test_explicit_context_is_the_safe_followup_fallback(harness: _Harness):
    context = AskFinContext(
        harness.review.review_id,
        "account",
        _ACCOUNT_SCOPE,
        "Account 555035",
        validation_run_id=harness.projection["run_id"],
    )

    result = harness.ask("Show the rows that caused this.", context=context)

    _assert_active_grounding(harness, result)
    assert _intent_value(result) == "clarification_or_follow_up"
    assert "555035" in result.answer_text
    assert "C91" in result.answer_text
    assert "246" in result.answer_text
    assert {91, 246}.issubset(_source_rows(result))


@pytest.mark.parametrize(
    "question",
    (
        "Should I increase the budget?",
        "Approve this.",
        "Make the decision for me.",
    ),
)
def test_prohibited_decisions_remain_refused_before_model_use(
    harness: _Harness,
    question: str,
):
    calls_before = harness.provider.calls

    result = harness.ask(question)

    assert result.status is PrivateAskFinStatus.REFUSED
    assert _intent_value(result) == "prohibited_decision"
    assert result.answer_text == DECISION_REFUSAL
    assert result.citations == ()
    assert harness.provider.calls == calls_before


def test_unsupported_factual_claim_remains_fail_closed(harness: _Harness):
    result = harness.ask(
        "What was the approved 2027 cloud forecast for this department?"
    )

    assert result.status is PrivateAskFinStatus.UNANSWERABLE
    assert _intent_value(result) == "unsupported"
    assert result.citations == ()
    assert _INSUFFICIENT_FRAGMENT in result.answer_text.casefold()


def test_cross_review_and_stale_run_contexts_never_leak(
    harness: _Harness,
):
    account = harness.ask("Why is Account 555035 over budget?")
    prior_scope = getattr(account, "resolved_context", None)
    assert prior_scope is not None
    provider_calls = harness.provider.calls

    cross_review = AskFinContext(
        "rev_another",
        "account",
        _ACCOUNT_SCOPE,
        "Account 555035",
        validation_run_id=harness.projection["run_id"],
    )
    denied = harness.ask("Show evidence.", context=cross_review)
    assert denied.status is PrivateAskFinStatus.REFUSED
    assert denied.citations == ()
    assert harness.provider.calls == provider_calls

    stale_scope = AskFinContext(
        prior_scope.review_id,
        prior_scope.object_type,
        prior_scope.object_id,
        prior_scope.label,
        validation_run_id="run_predecessor",
    )

    stale = harness.ask("Show evidence.", context=stale_scope)
    assert stale.status is PrivateAskFinStatus.REFUSED
    assert stale.citations == ()
    assert stale.failure_state == "context_validation_run_mismatch"
    assert harness.provider.calls == provider_calls


def test_natural_language_path_uses_loopback_ollama_only(
    harness: _Harness,
):
    questions = (
        "Summarize this review.",
        "Why is Account 555035 over budget?",
        "Explain the duplicate transaction.",
    )

    results = [harness.ask(question) for question in questions]

    assert all(result.status is PrivateAskFinStatus.OK for result in results)
    # Standard review summaries and recorded duplicate explanations use the
    # independently verified closed-claim plan after local readiness is
    # confirmed. The entity-specific account question still uses Ollama.
    assert harness.provider.calls == 1
    assert harness.provider.configurations
    assert all(
        config.provider == "ollama" and config.base_url == "http://127.0.0.1:11434"
        for config in harness.provider.configurations
    )
    assert all(
        context["active_review_id"] == harness.review.review_id
        and context["validation_run_id"] == harness.projection["run_id"]
        for context in harness.provider.contexts
    )
    assert all(
        record["citation_key"].split(":", 2)[1] == harness.review.review_id
        for context in harness.provider.contexts
        for record in context["records"]
    )
