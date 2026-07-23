# NullProvider — a PERMANENT production provider (not merely a test double). It is the provider used
# whenever no live model is generating answers: provider unavailable, provider disabled, missing
# model, or offline operation. It NEVER contacts a network, NEVER persists prompts or responses, and
# NEVER fabricates findings, severity, approvals, or financial actions. It returns a deterministic
# safe refusal.
#
# Implements: finsight.application.ai.ports.AiProviderPort (Phase 4C.1).
from __future__ import annotations
from finsight.application.ai.contracts import PromptRequest, RawProviderResponse
from finsight.domain.ai.contracts import ProviderConfiguration

# A deterministic, schema-shaped safe refusal. No financial content, no citations, no fabrication.
NULL_RESPONSE_TEXT = (
    '{"answer_text": "AI explanations are currently unavailable.", '
    '"unable_to_answer": true, "citations": []}'
)


class NullProvider:
    """AiProviderPort implementation. Always available; generation is a fixed safe refusal and does
    not read or retain the request content. Covers provider-unavailable, provider-disabled,
    missing-model, and offline operation."""

    def available(self) -> bool:
        return True

    def generate(self, request: PromptRequest, config: ProviderConfiguration) -> RawProviderResponse:
        return RawProviderResponse(
            text=NULL_RESPONSE_TEXT,
            provider="null",
            model=config.model,
            metadata={"reason": "no_active_provider"},
        )
