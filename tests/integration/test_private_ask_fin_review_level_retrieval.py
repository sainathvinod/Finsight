"""Focused acceptance coverage for review-level private Ask Fin retrieval.

Most cases use a provider that reports ``unable_to_answer`` so success proves
that FinSight found enough deterministic evidence in the active sealed May
2026 review. Additional cases prove standard review answers do not depend on
untrusted model formatting, plus an opt-in test checks the real local runtime.
"""

from __future__ import annotations

import json
import os

import pytest

from finsight.application.ai.contracts import ProviderStatus, RawProviderResponse
from finsight.application.ai.private_ask_fin import PrivateAskFinService
from finsight.application.ai.private_contracts import (
    AskFinContext,
    PrivateAskFinRequest,
    PrivateAskFinStatus,
)
from finsight.application.ai.private_grounding import V2FinancialGroundingService
from finsight.domain.ai.contracts import ProviderConfiguration
from finsight.infrastructure.ai.providers.ollama import OllamaProvider
from tests.integration.test_private_ask_fin_natural_language_refinement import (
    _INSUFFICIENT_FRAGMENT,
    _AllowActiveReviewer,
    _Audit,
    _assert_active_grounding,
    _intent_value,
    _source_rows,
    harness as _natural_language_harness,
)
from tests.support import FixedClock


@pytest.fixture
def harness(tmp_path):
    return _natural_language_harness.__wrapped__(tmp_path)


def _assert_answerable(harness, result) -> None:
    _assert_active_grounding(harness, result)
    assert _INSUFFICIENT_FRAGMENT not in result.answer_text.casefold()


def _citation_for_row(result, source_row: int):
    return next(
        citation
        for citation in result.citations
        if citation.navigation_target.get("source_row") == source_row
    )


class _SubstantiveButUnverifiableProvider:
    """A running local provider that returns prose FinSight must reject."""

    def __init__(self, failure_kind: str):
        self.failure_kind = failure_kind
        self.calls = 0
        self.rejected_text = ""

    def status(self):
        return ProviderStatus(True, True, "ok")

    def generate(self, request, config):
        self.calls += 1
        assert config.provider == "ollama"
        assert config.base_url == "http://127.0.0.1:11434"
        payload = request.context_block.split("\n", 1)[1].rsplit("\n", 1)[0]
        context = json.loads(payload)
        review_key = next(
            record["citation_key"]
            for record in context["records"]
            if record["object_type"] == "review"
        )
        if self.failure_kind == "unknown_citation":
            citation_key = (
                "review:rev_outside_active_scope:run_outside_active_scope"
            )
            self.rejected_text = (
                "This review is healthy and requires no further attention "
                f"[{citation_key}]."
            )
        else:
            citation_key = review_key
            self.rejected_text = (
                "This review is Healthy with exactly $999,999,999 of actual "
                f"spend [{citation_key}]."
            )
        return RawProviderResponse(
            json.dumps(
                {
                    "answer_text": self.rejected_text,
                    "unable_to_answer": False,
                    "citations": [citation_key],
                }
            ),
            "ollama",
            config.model,
            {"model_version": config.model},
        )


def _service_with_provider(harness, provider, audit):
    return PrivateAskFinService(
        authorization=_AllowActiveReviewer(),
        grounding=V2FinancialGroundingService(
            harness.services.financial_review
        ),
        provider=provider,
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://127.0.0.1:11434",
            request_timeout_seconds=2.0,
        ),
        audit=audit,
        clock=FixedClock(),
        active_review_id=lambda: harness.review.review_id,
    )


@pytest.mark.parametrize(
    "failure_kind",
    ("unknown_citation", "fabricated_value"),
)
def test_review_summary_does_not_make_unverifiable_model_prose_an_answer_gate(
    harness,
    failure_kind: str,
):
    provider = _SubstantiveButUnverifiableProvider(failure_kind)
    audit = _Audit()
    service = _service_with_provider(harness, provider, audit)

    result = service.ask(
        PrivateAskFinRequest(
            user_id="local-user",
            review_id=harness.review.review_id,
            question="Summarize this review.",
        )
    )

    _assert_answerable(harness, result)
    assert provider.calls == 0
    assert result.failure_state is None
    assert result.provider == "finsight"
    assert result.model == "deterministic-review-v1"
    assert provider.rejected_text == ""
    assert "healthy" not in result.answer_text.casefold()
    assert "$999,999,999" not in result.answer_text
    assert "Incomplete" in result.answer_text
    assert "$10,372,000" in result.answer_text
    assert "$3,500,095" in result.answer_text
    assert audit.entries[-1]["status"] == PrivateAskFinStatus.OK.value
    assert audit.entries[-1]["failure_state"] is None
    assert audit.entries[-1]["response"] == result.answer_text
    assert audit.entries[-1]["citations"] == [
        citation.key for citation in result.citations
    ]
    assert all(
        key in result.retrieved_record_keys
        for key in audit.entries[-1]["citations"]
    )


def test_review_summary_searches_review_leadership_and_projection_records(
    harness,
):
    result = harness.ask("Summarize this review.")

    _assert_answerable(harness, result)
    assert _intent_value(result) == "review_summary"
    assert "May 2026" in result.answer_text
    assert "Incomplete" in result.answer_text
    assert "$10,372,000" in result.answer_text
    assert "$3,500,095" in result.answer_text
    assert "$9,382,095" in result.answer_text
    assert "5" in result.answer_text
    assert "4 High" in result.answer_text
    assert "missing" in result.answer_text.casefold()
    assert {
        citation.object_type for citation in result.citations
    }.issuperset({"review", "leadership-summary"})
    assert result.resolved_context is not None
    assert result.resolved_context.object_type == "review"
    assert result.resolved_context.validation_run_id == harness.projection["run_id"]


@pytest.mark.parametrize(
    "question",
    (
        "What's wrong with this review?",
        "What should I look at first?",
        "Which findings are most important?",
    ),
)
def test_broad_review_questions_retrieve_recorded_priorities(
    harness,
    question: str,
):
    result = harness.ask(question)

    _assert_answerable(harness, result)
    assert _intent_value(result) == "findings_summary"
    assert "555035" in result.answer_text
    assert "over budget" in result.answer_text.casefold()
    assert result.resolved_context is not None
    assert result.resolved_context.object_type == "finding"
    assert result.resolved_context.validation_run_id == harness.projection["run_id"]


def test_highest_priority_finding_returns_detail_and_exact_source_evidence(
    harness,
):
    result = harness.ask("Explain the highest-priority finding.")

    _assert_answerable(harness, result)
    assert _intent_value(result) == "findings_summary"
    assert "High" in result.answer_text
    assert "Budget Overrun" in result.answer_text
    assert "555035" in result.answer_text
    assert "Outside Consultants' Fees" in result.answer_text
    assert "$1,100,000" in result.answer_text
    assert "$1,250,000" in result.answer_text
    assert "$150,000" in result.answer_text
    assert "13.64%" in result.answer_text
    assert "CORE-01" in result.answer_text
    assert "2.0.0" in result.answer_text
    assert "C91" in result.answer_text
    assert {91, 246}.issubset(_source_rows(result))


def test_no_scope_evidence_never_returns_generic_insufficiency(harness):
    result = harness.ask("Show the supporting evidence.")

    assert result.status is PrivateAskFinStatus.OK
    assert _intent_value(result) == "evidence_request"
    assert _INSUFFICIENT_FRAGMENT not in result.answer_text.casefold()
    if result.citations:
        _assert_active_grounding(harness, result)
        assert "555035" in result.answer_text
        assert "C91" in result.answer_text
        assert {91, 246}.issubset(_source_rows(result))
        assert result.resolved_context is not None
        assert result.resolved_context.object_type == "finding"
    else:
        # A brief request to choose a finding is an approved no-scope fallback.
        lowered = result.answer_text.casefold()
        assert "which" in lowered
        assert "finding" in lowered
        assert "evidence" in lowered


@pytest.mark.parametrize(
    "question",
    (
        "Show evidence for Account 999999.",
        "Show supporting evidence for the approved 2027 cloud forecast.",
    ),
)
def test_unresolved_explicit_evidence_target_fails_closed(
    harness,
    question: str,
):
    result = harness.ask(question)

    assert result.status is PrivateAskFinStatus.UNANSWERABLE, (
        result.intent,
        result.failure_state,
        result.answer_text,
        result.retrieved_record_keys,
    )
    assert result.citations == ()
    assert _INSUFFICIENT_FRAGMENT in result.answer_text.casefold()
    assert "555035" not in result.answer_text


def test_conversation_scope_drives_generic_supporting_evidence(harness):
    finding = harness.ask("Tell me more about the missing GED amount.")
    _assert_answerable(harness, finding)
    assert finding.resolved_context is not None
    assert finding.resolved_context.object_type == "finding"

    evidence = harness.ask(
        "Show the supporting evidence.",
        context=finding.resolved_context,
    )

    _assert_answerable(harness, evidence)
    assert _intent_value(evidence) in {
        "clarification_or_follow_up",
        "evidence_request",
    }
    assert evidence.resolved_context == finding.resolved_context
    assert "537035" in evidence.answer_text
    assert "O87" in evidence.answer_text
    assert 87 in _source_rows(evidence)
    citation = _citation_for_row(evidence, 87)
    assert citation.navigation_target["source_file"] == "Sample_GED_Report.xlsx"
    assert citation.navigation_target["worksheet"] == "GED"
    assert citation.navigation_target["cell"] == "O87"


def test_explicit_review_and_missing_ged_queries_reset_an_unrelated_scope(
    harness,
):
    account_context = AskFinContext(
        review_id=harness.review.review_id,
        object_type="account",
        object_id="00-0245|555035",
        label="Account 555035",
        validation_run_id=harness.projection["run_id"],
    )

    summary = harness.ask(
        "Summarize this review.",
        context=account_context,
    )
    _assert_answerable(harness, summary)
    assert _intent_value(summary) == "review_summary"
    assert summary.resolved_context is not None
    assert summary.resolved_context.object_type == "review"
    assert "$10,372,000" in summary.answer_text

    missing = harness.ask(
        "Tell me more about the missing GED amount.",
        context=account_context,
    )
    _assert_answerable(harness, missing)
    assert _intent_value(missing) == "ged_transaction_question"
    assert missing.resolved_context is not None
    assert missing.resolved_context.object_type == "finding"
    assert "537035" in missing.answer_text
    assert "O87" in missing.answer_text


def test_explicit_review_question_resets_a_stale_same_review_object_scope(
    harness,
):
    stale_account_context = AskFinContext(
        review_id=harness.review.review_id,
        object_type="account",
        object_id="00-0245|555035",
        label="Account 555035",
        validation_run_id="run_predecessor",
    )

    result = harness.ask(
        "Summarize this review.",
        context=stale_account_context,
    )

    _assert_answerable(harness, result)
    assert _intent_value(result) == "review_summary"
    assert result.validation_run_id == harness.projection["run_id"]
    assert result.resolved_context is not None
    assert result.resolved_context.object_type == "review"
    assert result.resolved_context.validation_run_id == harness.projection["run_id"]


def test_review_summary_scope_falls_back_to_highest_priority_evidence(
    harness,
):
    summary = harness.ask("Summarize this review.")
    _assert_answerable(harness, summary)
    assert summary.resolved_context is not None
    assert summary.resolved_context.object_type == "review"

    evidence = harness.ask(
        "Show the supporting evidence.",
        context=summary.resolved_context,
    )

    _assert_answerable(harness, evidence)
    assert evidence.resolved_context is not None
    assert evidence.resolved_context.object_type == "finding"
    assert "555035" in evidence.answer_text
    assert {91, 246}.issubset(_source_rows(evidence))


def test_screenshot_conversation_sequence_reanchors_each_explicit_topic(
    harness,
):
    greeting = harness.ask("how are you")
    assert greeting.status is PrivateAskFinStatus.OK
    assert greeting.resolved_context is None

    summary = harness.ask("Summarize this review.")
    _assert_answerable(harness, summary)
    assert summary.resolved_context is not None
    assert summary.resolved_context.object_type == "review"

    evidence = harness.ask(
        "Show the supporting evidence.",
        context=summary.resolved_context,
    )
    _assert_answerable(harness, evidence)
    assert evidence.resolved_context is not None
    assert evidence.resolved_context.object_type == "finding"
    assert "555035" in evidence.answer_text

    missing = harness.ask(
        "Tell me more about the missing GED amount.",
        context=evidence.resolved_context,
    )
    _assert_answerable(harness, missing)
    assert missing.resolved_context is not None
    assert missing.resolved_context.object_type == "finding"
    assert "537035" in missing.answer_text
    assert "O87" in missing.answer_text
    assert 87 in _source_rows(missing)


def test_missing_ged_amount_explains_failure_rule_scope_evidence_and_impact(
    harness,
):
    result = harness.ask("Tell me more about the missing GED amount.")

    _assert_answerable(harness, result)
    assert _intent_value(result) == "ged_transaction_question"
    assert "Missing or invalid required GED value" in result.answer_text
    assert "Amount" in result.answer_text
    assert "missing" in result.answer_text.casefold()
    assert "CORE-04" in result.answer_text
    assert "2.0.0" in result.answer_text
    assert "537035" in result.answer_text
    assert "Purchased Software" in result.answer_text
    assert "00-0245" in result.answer_text
    assert "why finsight flagged it" in result.answer_text.casefold()
    assert "why it matters" in result.answer_text.casefold()
    assert "reliable" in result.answer_text.casefold()
    assert "O87" in result.answer_text
    assert 87 in _source_rows(result)
    citation = next(
        citation
        for citation in result.citations
        if citation.object_type == "transaction"
        and citation.navigation_target.get("source_row") == 87
    )
    assert citation.object_type == "transaction"
    assert citation.navigation_target["source_file"] == "Sample_GED_Report.xlsx"
    assert citation.navigation_target["worksheet"] == "GED"
    assert citation.navigation_target["source_row"] == 87
    assert citation.navigation_target["cell"] == "O87"


def test_incomplete_review_identifies_missing_amount_and_dependent_limitation(
    harness,
):
    result = harness.ask("Why is the review incomplete?")

    _assert_answerable(harness, result)
    assert _intent_value(result) == "findings_summary"
    assert "Incomplete" in result.answer_text
    assert "Amount" in result.answer_text
    assert "CORE-04" in result.answer_text
    assert "537035" in result.answer_text
    assert "O87" in result.answer_text
    assert "not evaluated" in result.answer_text.casefold()
    assert 87 in _source_rows(result)


def test_review_level_retrieval_cannot_cross_review_or_validation_run(
    harness,
):
    finding = harness.ask("Explain the highest-priority finding.")
    _assert_answerable(harness, finding)
    assert finding.resolved_context is not None
    provider_calls = harness.provider.calls

    wrong_review = AskFinContext(
        review_id="rev_different",
        object_type=finding.resolved_context.object_type,
        object_id=finding.resolved_context.object_id,
        label=finding.resolved_context.label,
        validation_run_id=harness.projection["run_id"],
    )
    denied_review = harness.ask(
        "Show the supporting evidence.",
        context=wrong_review,
    )
    assert denied_review.status is PrivateAskFinStatus.REFUSED
    assert denied_review.citations == ()

    stale_run = AskFinContext(
        review_id=harness.review.review_id,
        object_type=finding.resolved_context.object_type,
        object_id=finding.resolved_context.object_id,
        label=finding.resolved_context.label,
        validation_run_id="run_predecessor",
    )
    denied_run = harness.ask(
        "Show the supporting evidence.",
        context=stale_run,
    )
    assert denied_run.status is PrivateAskFinStatus.REFUSED
    assert denied_run.citations == ()
    assert denied_run.failure_state == "context_validation_run_mismatch"
    assert harness.provider.calls == provider_calls


@pytest.mark.skipif(
    os.environ.get("FINSIGHT_LIVE_OLLAMA_TEST") != "1",
    reason="requires the explicitly enabled local Ollama runtime",
)
def test_live_local_model_answers_requested_active_review_questions(
    harness,
):
    configuration = ProviderConfiguration.ollama(
        model="llama3.2:3b",
        base_url="http://127.0.0.1:11434",
        request_timeout_seconds=120.0,
    )
    provider = OllamaProvider(
        configuration,
        status_timeout=3.0,
        private_local=True,
        forbid_redirects=True,
        approved_model_profile_id="stage2-local-ollama-gguf-v1",
    )
    service = PrivateAskFinService(
        authorization=_AllowActiveReviewer(),
        grounding=V2FinancialGroundingService(
            harness.services.financial_review
        ),
        provider=provider,
        provider_configuration=configuration,
        audit=_Audit(),
        clock=FixedClock(),
        active_review_id=lambda: harness.review.review_id,
    )
    questions = (
        "Summarize this review.",
        "What's wrong with this review?",
        "What should I look at first?",
        "Show the supporting evidence.",
        "Tell me more about the missing GED amount.",
        "Explain the highest-priority finding.",
        "Why is the review incomplete?",
        "Which findings are most important?",
    )

    results = [
        service.ask(
            PrivateAskFinRequest(
                user_id="local-user",
                review_id=harness.review.review_id,
                question=question,
            )
        )
        for question in questions
    ]

    failures = [
        (question, result.status.value, result.failure_state)
        for question, result in zip(questions, results)
        if result.status is not PrivateAskFinStatus.OK
    ]
    assert failures == []
    assert all(result.citations for result in results)
    assert all(
        _INSUFFICIENT_FRAGMENT not in result.answer_text.casefold()
        for result in results
    )
    assert all(
        result.validation_run_id == harness.projection["run_id"]
        for result in results
    )
