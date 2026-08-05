"""Private Ask Fin integration against the approved sealed Stage 1 fixture run."""

from __future__ import annotations

import json

from finsight.app import build_private_ask_fin_backend, build_query_services
from finsight.application.ai.contracts import ProviderStatus, RawProviderResponse
from finsight.application.ai.private_ask_fin import PrivateAskFinService
from finsight.application.ai.private_contracts import (
    AskFinContext,
    PrivateAskFinRequest,
    PrivateAskFinStatus,
)
from finsight.application.ai.private_grounding import V2FinancialGroundingService
from finsight.domain.ai.contracts import ProviderConfiguration
from finsight.domain.source_intake import SourceRole
from finsight.infrastructure.ai.private_audit import (
    PrivateAskFinAuditRepositorySqlite,
)
from finsight.infrastructure.ai.private_config import PrivateAskFinSettings
from finsight.infrastructure.identity import FixedIdentityProvider
from tests.support import FixedClock, persist_confirmed_validation


FIXTURES = "initiatives/configurable-rule-engine-v2/fixtures"
LOCAL_MODEL_DIGEST = "sha256:" + ("a" * 64)


class Allow:
    def authorize(self, *, user_id, review_id):
        assert user_id == "local-user"
        assert review_id.startswith("rev_")


class CapturingProvider:
    def __init__(self):
        self.context = None
        self.calls = 0

    def status(self):
        return ProviderStatus(True, True, "ok")

    def generate(self, request, config):
        self.calls += 1
        payload = request.context_block.split("\n", 1)[1].rsplit("\n", 1)[0]
        self.context = json.loads(payload)
        account = next(
            item
            for item in self.context["records"]
            if item["object_type"] == "account"
            and item["facts"]["account_number"] == "555035"
        )
        key = account["citation_key"]
        assert account["facts"]["bgt_label"] == "$1,100,000.00"
        assert account["facts"]["summed_ged_amount_label"] == "$1,250,000.00"
        assert account["facts"]["over_budget_amount_label"] == "$150,000.00"
        answer = (
            "Account 555035 has recorded GED spend of $1,250,000.00 against "
            "BGT of $1,100,000.00, an unfavorable $150,000.00 variance "
            f"[{key}]."
        )
        return RawProviderResponse(
            json.dumps(
                {
                    "answer_text": answer,
                    "unable_to_answer": False,
                    "citations": [key],
                }
            ),
            "ollama",
            config.model,
            {},
        )


class Audit:
    def __init__(self):
        self.entries = []

    def append(self, value):
        self.entries.append(value)


class UnableProvider:
    """Exercise the deterministic closed-claim recovery path."""

    def __init__(self):
        self.contexts = []

    def status(self):
        return ProviderStatus(True, True, "ok")

    def generate(self, request, config):
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
            {},
        )


class MalformedProvider(UnableProvider):
    def generate(self, request, config):
        payload = request.context_block.split("\n", 1)[1].rsplit("\n", 1)[0]
        self.contexts.append(json.loads(payload))
        return RawProviderResponse(
            "{not-json",
            "ollama",
            config.model,
            {},
        )


class UnsafeSummaryProvider(UnableProvider):
    def generate(self, request, config):
        payload = request.context_block.split("\n", 1)[1].rsplit("\n", 1)[0]
        context = json.loads(payload)
        self.contexts.append(context)
        summary = next(
            item
            for item in context["records"]
            if item["object_type"] == "leadership-summary"
        )
        key = summary["citation_key"]
        return RawProviderResponse(
            json.dumps(
                {
                    "answer_text": (
                        f"You should increase the budget immediately [{key}]."
                    ),
                    "unable_to_answer": False,
                    "citations": [key],
                }
            ),
            "ollama",
            config.model,
            {},
        )


class UncitedProvider(UnableProvider):
    def generate(self, request, config):
        payload = request.context_block.split("\n", 1)[1].rsplit("\n", 1)[0]
        self.contexts.append(json.loads(payload))
        return RawProviderResponse(
            json.dumps(
                {
                    "answer_text": "The review has several items to inspect.",
                    "unable_to_answer": False,
                    "citations": [],
                }
            ),
            "ollama",
            config.model,
            {},
        )


class InvalidCitationProvider(UnableProvider):
    def generate(self, request, config):
        payload = request.context_block.split("\n", 1)[1].rsplit("\n", 1)[0]
        self.contexts.append(json.loads(payload))
        invalid_key = "finding:another-review:not-active"
        return RawProviderResponse(
            json.dumps(
                {
                    "answer_text": (
                        f"The review has several items to inspect [{invalid_key}]."
                    ),
                    "unable_to_answer": False,
                    "citations": [invalid_key],
                }
            ),
            "ollama",
            config.model,
            {},
        )


def _sealed_review(tmp_path):
    database_path = str(tmp_path / "private-ask-fin.db")
    services = build_query_services(database_path, clock=FixedClock())
    review = services.review_management.create_review(
        5, 2026, idempotency_key="ask-fin-create"
    )
    budget = services.source_intake.inspect(
        f"{FIXTURES}/Sample_Budget_Report.xlsx", SourceRole.BUDGET
    )
    ged = services.source_intake.inspect(
        f"{FIXTURES}/Sample_GED_Report.xlsx", SourceRole.GED
    )
    pair = services.source_intake.evaluate(
        budget=budget, ged=ged, selected_period=review.period
    )
    services.review_management.commit_source_intake(
        review.review_id, pair, idempotency_key="ask-fin-sources"
    )
    dataset = services.financial_review.reconstruct_dataset(review.review_id)
    services.financial_review.confirm_reviewed_data(
        review.review_id,
        dataset,
        attestation_text="Reviewed for private Ask Fin integration.",
    )
    projection = persist_confirmed_validation(
        services.financial_review, review.review_id, dataset
    )
    return database_path, services, review, projection


def test_private_ask_fin_uses_sealed_v2_values_and_source_lineage(tmp_path):
    _database_path, services, review, projection = _sealed_review(tmp_path)
    provider = CapturingProvider()
    audit = Audit()
    service = PrivateAskFinService(
        authorization=Allow(),
        grounding=V2FinancialGroundingService(services.financial_review),
        provider=provider,
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://localhost:11434",
            request_timeout_seconds=2.0,
        ),
        audit=audit,
        clock=FixedClock(),
        active_review_id=lambda: review.review_id,
    )

    result = service.ask(
        PrivateAskFinRequest(
            user_id="local-user",
            review_id=review.review_id,
            question="Why is Account 555035 over budget?",
        )
    )

    assert result.status is PrivateAskFinStatus.OK
    assert result.validation_run_id == projection["run_id"]
    assert "$1,250,000.00" in result.answer_text
    assert "$1,100,000.00" in result.answer_text
    assert "$150,000.00" in result.answer_text
    assert result.citations[0].review_id == review.review_id
    assert provider.context["active_review_id"] == review.review_id
    assert provider.context["validation_run_id"] == projection["run_id"]
    assert all(
        item["citation_key"].split(":", 2)[1] == review.review_id
        for item in provider.context["records"]
    )
    source_rows = [
        item
        for item in provider.context["records"]
        if item["object_type"] in {"transaction", "budget-source"}
    ]
    assert any(item["facts"]["source_row"] == 91 for item in source_rows)
    assert any(item["facts"]["source_row"] == 246 for item in source_rows)
    assert audit.entries[-1]["retrieved_records"]
    assert audit.entries[-1]["grounding_review_id"] == review.review_id
    assert provider.calls == 1


def test_ordinary_active_review_questions_use_bounded_grounding_and_recover(
    tmp_path,
):
    _database_path, services, review, projection = _sealed_review(tmp_path)
    provider = UnableProvider()
    audit = Audit()
    service = PrivateAskFinService(
        authorization=Allow(),
        grounding=V2FinancialGroundingService(services.financial_review),
        provider=provider,
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://localhost:11434",
            request_timeout_seconds=2.0,
        ),
        audit=audit,
        clock=FixedClock(),
        active_review_id=lambda: review.review_id,
    )

    questions = (
        "Summarize this review.",
        "What are the top findings?",
        "Which accounts need attention?",
        "Which vendors have the highest recorded spend?",
        "Show the evidence for the highest-severity finding.",
        "What are the financial review priorities?",
    )
    results = [
        service.ask(
            PrivateAskFinRequest(
                user_id="local-user",
                review_id=review.review_id,
                question=question,
            )
        )
        for question in questions
    ]
    assert all(result.status is PrivateAskFinStatus.OK for result in results), [
        (question, result.status, result.failure_state, result.answer_text)
        for question, result in zip(questions, results)
    ]
    assert all(result.citations for result in results)
    assert all(result.validation_run_id == projection["run_id"] for result in results)
    assert all(
        citation.review_id == review.review_id
        for result in results
        for citation in result.citations
    )
    retrieved_types = [
        {key.split(":", 1)[0] for key in result.retrieved_record_keys}
        for result in results
    ]
    assert "leadership-summary" in retrieved_types[0]
    assert "finding" in retrieved_types[1]
    assert "account" in retrieved_types[2]
    assert "vendor" in retrieved_types[3]
    assert {"finding", "transaction"}.intersection(retrieved_types[4])
    assert "leadership-summary" in retrieved_types[5]
    assert len(provider.contexts) == 1
    assert len(provider.contexts[0]["records"]) <= 20
    assert len(json.dumps(provider.contexts[0], sort_keys=True)) < 60_000
    assert all(entry["status"] == "ok" for entry in audit.entries)
    summary, findings, accounts, vendors, evidence, priorities = results
    assert "$10,372,000.00" in summary.answer_text
    assert "Partial — $3,500,095.00" in summary.answer_text
    assert "Account 555035" in findings.answer_text
    assert "Account 555035" in accounts.answer_text
    assert "$0.00 over budget" not in accounts.answer_text
    assert "No vendor recorded" not in vendors.answer_text
    assert vendors.answer_text.index("TEKSYSTEMS, INC") < (
        vendors.answer_text.index("APPS ASSOCIATES LLC")
    )
    assert "Budget source evidence includes row 91" in evidence.answer_text
    assert "GED source evidence includes row 246" in evidence.answer_text
    assert priorities.answer_text.index("Account 555035") < (
        priorities.answer_text.index("Account 527015")
    )


def test_summary_uses_verified_closed_claims_without_a_model_format_gate(
    tmp_path,
):
    _database_path, services, review, _projection = _sealed_review(tmp_path)
    provider = MalformedProvider()
    service = PrivateAskFinService(
        authorization=Allow(),
        grounding=V2FinancialGroundingService(services.financial_review),
        provider=provider,
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://localhost:11434",
            request_timeout_seconds=2.0,
        ),
        audit=Audit(),
        clock=FixedClock(),
        active_review_id=lambda: review.review_id,
    )

    result = service.ask(
        PrivateAskFinRequest(
            user_id="local-user",
            review_id=review.review_id,
            question="Summarize this financial review.",
        )
    )

    assert result.status is PrivateAskFinStatus.OK
    assert result.citations
    assert result.failure_state is None
    assert result.provider == "finsight"
    assert provider.contexts == []
    assert "$10,372,000.00" in result.answer_text


def test_safe_summary_does_not_expose_unsolicited_model_decision_language(
    tmp_path,
):
    _database_path, services, review, _projection = _sealed_review(tmp_path)
    provider = UnsafeSummaryProvider()
    service = PrivateAskFinService(
        authorization=Allow(),
        grounding=V2FinancialGroundingService(services.financial_review),
        provider=provider,
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://localhost:11434",
            request_timeout_seconds=2.0,
        ),
        audit=Audit(),
        clock=FixedClock(),
        active_review_id=lambda: review.review_id,
    )

    result = service.ask(
        PrivateAskFinRequest(
            user_id="local-user",
            review_id=review.review_id,
            question="Summarize this financial review.",
        )
    )

    assert result.status is PrivateAskFinStatus.OK
    assert result.citations
    assert result.failure_state is None
    assert result.provider == "finsight"
    assert provider.contexts == []
    assert "$10,372,000.00" in result.answer_text
    assert "increase the budget" not in result.answer_text.casefold()


def test_ordinary_review_questions_use_verified_closed_claims_directly(
    tmp_path,
):
    _database_path, services, review, _projection = _sealed_review(tmp_path)
    provider = UncitedProvider()
    service = PrivateAskFinService(
        authorization=Allow(),
        grounding=V2FinancialGroundingService(services.financial_review),
        provider=provider,
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://localhost:11434",
            request_timeout_seconds=2.0,
        ),
        audit=Audit(),
        clock=FixedClock(),
        active_review_id=lambda: review.review_id,
    )

    questions = (
        "Summarize this financial review.",
        "Summarize the top findings.",
        "Which accounts need attention?",
    )
    results = [
        service.ask(
            PrivateAskFinRequest(
                user_id="local-user",
                review_id=review.review_id,
                question=question,
            )
        )
        for question in questions
    ]

    assert all(result.status is PrivateAskFinStatus.OK for result in results)
    assert all(result.citations for result in results)
    assert all(result.failure_state is None for result in results)
    assert all(result.provider == "finsight" for result in results)
    assert provider.contexts == []
    assert "$10,372,000.00" in results[0].answer_text
    assert "Account 555035" in results[1].answer_text
    assert "Account 555035" in results[2].answer_text


def test_ordinary_read_question_fails_closed_on_out_of_scope_model_citation(
    tmp_path,
):
    _database_path, services, review, _projection = _sealed_review(tmp_path)
    service = PrivateAskFinService(
        authorization=Allow(),
        grounding=V2FinancialGroundingService(services.financial_review),
        provider=InvalidCitationProvider(),
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://localhost:11434",
            request_timeout_seconds=2.0,
        ),
        audit=Audit(),
        clock=FixedClock(),
        active_review_id=lambda: review.review_id,
    )

    result = service.ask(
        PrivateAskFinRequest(
            user_id="local-user",
            review_id=review.review_id,
            question="Why is Account 555035 over budget?",
        )
    )

    assert result.status is PrivateAskFinStatus.UNANSWERABLE
    assert not result.citations
    assert result.failure_state == "citation_or_value_verification_failed"


def test_common_entity_and_evidence_questions_use_only_relevant_review_facts(
    tmp_path,
):
    _database_path, services, review, _projection = _sealed_review(tmp_path)
    provider = UnableProvider()
    service = PrivateAskFinService(
        authorization=Allow(),
        grounding=V2FinancialGroundingService(services.financial_review),
        provider=provider,
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://localhost:11434",
            request_timeout_seconds=2.0,
        ),
        audit=Audit(),
        clock=FixedClock(),
        active_review_id=lambda: review.review_id,
    )

    questions = (
        "Which accounts are over budget?",
        "What evidence supports the budget overrun?",
        "Tell me about Outside Consultants Fees.",
    )
    results = [
        service.ask(
            PrivateAskFinRequest(
                user_id="local-user",
                review_id=review.review_id,
                question=question,
            )
        )
        for question in questions
    ]

    assert all(result.status is PrivateAskFinStatus.OK for result in results)
    over_budget, evidence, named_account = results
    assert "Account 555035" in over_budget.answer_text
    assert "Account 527015" not in over_budget.answer_text
    assert "Account 533003" not in over_budget.answer_text
    assert "$0.00 over budget" not in over_budget.answer_text
    assert "Account: 555035" in evidence.answer_text
    assert "Budget source evidence includes row 91" in evidence.answer_text
    assert "GED source evidence includes row 246" in evidence.answer_text
    assert "Account 527015" not in evidence.answer_text
    assert "Account 533003" not in evidence.answer_text
    assert "Account 555035" in named_account.answer_text
    assert "$1,100,000.00" in named_account.answer_text
    assert "$1,250,000.00" in named_account.answer_text
    assert "$150,000.00" in named_account.answer_text
    assert all(
        citation.review_id == review.review_id
        for result in results
        for citation in result.citations
    )


def test_unknown_question_does_not_trigger_closed_claim_substitution(
    tmp_path,
):
    _database_path, services, review, _projection = _sealed_review(tmp_path)
    provider = UnableProvider()
    service = PrivateAskFinService(
        authorization=Allow(),
        grounding=V2FinancialGroundingService(services.financial_review),
        provider=provider,
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://localhost:11434",
            request_timeout_seconds=2.0,
        ),
        audit=Audit(),
        clock=FixedClock(),
        active_review_id=lambda: review.review_id,
    )

    result = service.ask(
        PrivateAskFinRequest(
            user_id="local-user",
            review_id=review.review_id,
            question="Tell me something unrelated.",
        )
    )

    assert result.status is PrivateAskFinStatus.UNANSWERABLE
    assert not result.citations
    assert result.failure_state == "unsupported_question"


def test_every_scoped_suggestion_has_verified_active_review_grounding(
    tmp_path,
):
    _database_path, services, review, projection = _sealed_review(tmp_path)
    provider = UnableProvider()
    service = PrivateAskFinService(
        authorization=Allow(),
        grounding=V2FinancialGroundingService(services.financial_review),
        provider=provider,
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://localhost:11434",
            request_timeout_seconds=2.0,
        ),
        audit=Audit(),
        clock=FixedClock(),
        active_review_id=lambda: review.review_id,
    )
    priority = projection["leadership_summary"]["highest_priority_findings"][0]
    contexts = (
        AskFinContext(
            review.review_id,
            "finding",
            priority["finding_id"],
            priority["title"],
        ),
        AskFinContext(
            review.review_id,
            "account",
            "00-0245|555035",
            "Account 555035",
        ),
        AskFinContext(
            review.review_id,
            "vendor",
            "TEKSYSTEMS, INC",
            "TEKSYSTEMS, INC",
        ),
    )

    for context in contexts:
        session = service.session(
            user_id="local-user",
            review_id=review.review_id,
            context=context,
        )
        assert session.suggested_questions
        for question in session.suggested_questions:
            result = service.ask(
                PrivateAskFinRequest(
                    user_id="local-user",
                    review_id=review.review_id,
                    question=question,
                    context=context,
                )
            )
            assert result.status is PrivateAskFinStatus.OK, (
                context.object_type,
                question,
                result.failure_state,
            )
            assert result.citations
            assert all(
                citation.review_id == review.review_id for citation in result.citations
            )
            if context.object_type == "account":
                assert (
                    "555035" in result.answer_text
                    or "source evidence includes row" in result.answer_text
                    or "Vendor " in result.answer_text
                )
                if "vendors" in question.casefold():
                    assert (
                        "Account 555035 has recorded GED activity from vendor"
                        in result.answer_text
                    )
                    assert not any(
                        item["object_type"] == "vendor"
                        for item in provider.contexts[-1]["records"]
                    )
            if context.object_type == "vendor":
                assert (
                    "TEKSYSTEMS, INC" in result.answer_text
                    or "source evidence includes row" in result.answer_text
                ), (question, result.intent, result.answer_text)


class _Response:
    def __init__(self, value):
        self._value = json.dumps(value).encode("utf-8")

    def read(self):
        return self._value

    @property
    def peer_address(self):
        return ("127.0.0.1", 11434)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class LocalOllamaOpener:
    """A loopback transport fake; it has no external-network seam."""

    def __init__(self, review_id):
        self.review_id = review_id
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request.full_url, timeout))
        if request.full_url.endswith("/api/tags"):
            return _Response(
                {
                    "models": [
                        {
                            "name": "local-fixture:1",
                            "digest": LOCAL_MODEL_DIGEST,
                        }
                    ]
                }
            )
        if request.full_url.endswith("/api/show"):
            return _Response(
                {
                    "details": {"format": "gguf", "family": "llama"},
                    "model_info": {"general.architecture": "llama"},
                    "capabilities": ["completion"],
                }
            )
        payload = json.loads(request.data.decode("utf-8"))
        user_content = payload["messages"][1]["content"]
        context_text = user_content.split("<FINSIGHT_CONTEXT>\n", 1)[1].split(
            "\n</FINSIGHT_CONTEXT>", 1
        )[0]
        context = json.loads(context_text)
        assert context["active_review_id"] == self.review_id
        account = next(
            item
            for item in context["records"]
            if item["object_type"] == "account"
            and item["facts"]["account_number"] == "555035"
        )
        key = account["citation_key"]
        content = json.dumps(
            {
                "answer_text": (f"Account 555035 is $150,000.00 over budget [{key}]."),
                "unable_to_answer": False,
                "citations": [key],
            }
        )
        return _Response(
            {
                "model": "local-fixture:1",
                "message": {"role": "assistant", "content": content},
                "done": True,
            }
        )


def test_worker_backend_reopens_its_own_store_and_persists_local_audit(tmp_path):
    database_path, services, review, _projection = _sealed_review(tmp_path)
    opener = LocalOllamaOpener(review.review_id)
    settings = PrivateAskFinSettings(
        provider_configuration=ProviderConfiguration.ollama(
            model="local-fixture:1",
            base_url="http://127.0.0.1:11434",
            request_timeout_seconds=2.0,
        ),
        status_timeout_seconds=1.0,
        # Normal desktop use has no manual identity-approval step. The local
        # provider must pin and verify the exact observed digest automatically.
        approved_model_digest="",
    )
    backend = build_private_ask_fin_backend(
        database_path,
        settings=settings,
        opener=opener,
        clock_factory=FixedClock,
        identity_provider=FixedIdentityProvider(services.identity_resolution),
        identity_resolution=services.identity_resolution,
        active_review_id=review.review_id,
    )

    session = backend.session(
        user_id=services.identity_resolution.require_actor().actor_id,
        review_id=review.review_id,
    )
    assert session.review_id == review.review_id
    assert session.mode.value == "financial_review"

    result = backend.ask(
        PrivateAskFinRequest(
            user_id=services.identity_resolution.require_actor().actor_id,
            review_id=review.review_id,
            question="Why is Account 555035 over budget?",
        )
    )
    assert result.status is PrivateAskFinStatus.OK
    assert result.model_version == LOCAL_MODEL_DIGEST
    assert all(url.startswith("http://127.0.0.1:11434/") for url, _ in opener.calls)

    audit = PrivateAskFinAuditRepositorySqlite(
        services.financial_review._uow.dal,
        services.financial_review._uow,
    )
    rows = audit.list_for_review(review.review_id)
    assert len(rows) == 1
    assert rows[0]["question"] == "Why is Account 555035 over budget?"
    assert rows[0]["grounding_review_id"] == review.review_id

    blocked_backend = build_private_ask_fin_backend(
        database_path,
        settings=settings,
        opener=opener,
        clock_factory=FixedClock,
        identity_resolution=services.identity_resolution,
        active_review_id="rev_other",
    )
    provider_calls_before_scope_rejection = len(opener.calls)
    blocked = blocked_backend.ask(
        PrivateAskFinRequest(
            user_id=services.identity_resolution.require_actor().actor_id,
            review_id=review.review_id,
            question="Why is Account 555035 over budget?",
        )
    )
    assert blocked.status is PrivateAskFinStatus.REFUSED
    assert len(opener.calls) == provider_calls_before_scope_rejection
