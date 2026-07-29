import pytest

from finsight.application.failure_contracts import (
    CatalogedApplicationFailure,
    ErrorEnvelope,
    MutationOutcome,
    Retryability,
    safe_failure_message,
    safe_failure_presentation,
)


def test_cataloged_failure_contains_complete_user_contract():
    failure = CatalogedApplicationFailure(
        ErrorEnvelope.build(
            code="FS-AUT-001",
            category="Authorization",
            correlation_id="corr_123",
            cause="Your current role does not permit this action.",
            impact="The review was not changed.",
            remedies=("Ask a Rule Administrator to verify your assignment.",),
            retryability=Retryability.RETRY_AFTER_AUTHORIZATION,
            actor_reference="actor:qualified",
        )
    )

    message = failure.user_message()
    assert "FS-AUT-001" in message
    assert "Impact:" in message
    assert "Next step:" in message
    assert "State change: No changes were made." in message
    assert "Account: actor:qualified" in message
    assert "Correlation ID: corr_123" in message


def test_unexpected_exception_text_is_never_disclosed():
    message = safe_failure_message(
        RuntimeError("/private/path/secret.db failed with salary=100000"),
        fallback_correlation_id="corr_safe",
    )

    assert "/private/path" not in message
    assert "salary" not in message
    assert "FinSight could not complete the requested action." in message
    assert "FS-SYS-001" not in message
    assert "Correlation ID" not in message
    assert MutationOutcome.UNKNOWN.value not in message

    presentation = safe_failure_presentation(
        RuntimeError("sensitive raw text"),
        fallback_correlation_id="corr_safe",
    )
    assert "FS-SYS-001" not in presentation.primary
    assert "Error code: FS-SYS-001" in presentation.technical_details
    assert "Correlation ID: corr_safe" in presentation.technical_details


def test_envelope_rejects_incomplete_contract():
    with pytest.raises(ValueError):
        ErrorEnvelope.build(
            code="INVALID",
            category="Runtime",
            correlation_id="",
            cause="",
            impact="",
            remedies=(),
            retryability=Retryability.NOT_RETRYABLE,
        )
