# AI execution-seam ports (application layer). The provider port is an orchestration concern, not a
# domain concept, so it lives here (moved in Phase 4C.2). Infrastructure adapters
# (infrastructure/ai/providers) implement it; the application selects a provider via composition and
# never constructs one directly.
from __future__ import annotations
from typing import Protocol
from finsight.application.ai.contracts import PromptRequest, RawProviderResponse
from finsight.domain.ai.contracts import ProviderConfiguration


class AiProviderPort(Protocol):
    """A pluggable AI text generator. The application depends only on this Protocol and never
    constructs a provider — composition selects one (Ollama when reachable, else NullProvider).
    Providers must not persist prompts or responses, and must never author findings, severity,
    approvals, or financial actions."""
    def available(self) -> bool: ...
    def generate(self, request: PromptRequest, config: ProviderConfiguration) -> RawProviderResponse: ...
