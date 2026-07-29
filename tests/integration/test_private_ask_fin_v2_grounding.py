"""Private Ask Fin integration against the approved sealed Stage 1 fixture run."""
from __future__ import annotations

import json

from finsight.app import build_private_ask_fin_backend, build_query_services
from finsight.application.ai.contracts import ProviderStatus, RawProviderResponse
from finsight.application.ai.private_ask_fin import PrivateAskFinService
from finsight.application.ai.private_contracts import (
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
from tests.support import FixedClock


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
    evaluation = services.financial_review.evaluate(dataset)
    projection = services.financial_review.persist_evaluation(
        review.review_id, dataset, evaluation
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
                "answer_text": (
                    "Account 555035 is $150,000.00 over budget "
                    f"[{key}]."
                ),
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
        identity_provider=FixedIdentityProvider(
            services.identity_resolution
        ),
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
