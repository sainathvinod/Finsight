# NullProvider — the always-available fallback AI provider and the deterministic test double for the
# AI execution pipeline. It NEVER contacts a network, NEVER persists prompts or responses, and NEVER
# fabricates findings, severity, approvals, or financial actions. It returns a fixed safe refusal.
#
# Implements: finsight.domain.ai.ports.AiProviderPort (Phase 4C.1).
from __future__ import annotations
from finsight.domain.ai.contracts import PromptRequest, ProviderConfiguration, RawProviderResponse

# A deterministic, schema-shaped safe refusal. No financial content, no citations, no fabrication.
NULL_RESPONSE_TEXT = (
    '{"answer_text": "AI explanations are unavailable because no AI provider is configured.", '
    '"unable_to_answer": true, "citations": []}'
)


class NullProvider:
    """AiProviderPort implementation. Always available; generation is a fixed safe refusal and does
    not read or retain the request content."""

    def available(self) -> bool:
        return True

    def generate(self, request: PromptRequest, config: ProviderConfiguration) -> RawProviderResponse:
        return RawProviderResponse(
            text=NULL_RESPONSE_TEXT,
            provider="null",
            model=config.model,
            metadata={"reason": "no_provider"},
        )
