# AI execution-seam ports (application layer). The provider port is an orchestration concern, not a
# domain concept, so it lives here (moved in Phase 4C.2). Infrastructure adapters
# (infrastructure/ai/providers) implement it; the application selects a provider via composition and
# never constructs one directly.
from __future__ import annotations
from typing import Protocol
from finsight.application.ai.contracts import PromptRequest, ProviderStatus, RawProviderResponse
from finsight.application.ai.ask_fin_contracts import AiAuthorizationContext
from finsight.domain.ai.contracts import ProviderConfiguration


class AiAuthorizationPolicy(Protocol):
    """Decides whether explanation-only, non-mutating AI use is permitted. Fail-closed: raises
    AiAuthorizationError when consent is missing/denied or the mode disallows it. Provider availability
    is NOT authorization; NullProvider does not bypass it; it can never authorize deterministic-workflow
    mutation. It resolves and returns the AiAuthorizationContext it evaluated (for non-sensitive
    metadata). No production consent source exists yet — composition injects a concrete policy; tests
    inject fakes. This phase introduces only the port and its contract."""
    def authorize(self, *, user_id: str, cycle_id: str) -> AiAuthorizationContext: ...


class AiProviderPort(Protocol):
    """A pluggable AI text generator. The application depends only on this Protocol and never
    constructs a provider — composition selects one (Ollama when reachable, else NullProvider).
    Providers must not persist prompts or responses, and must never author findings, severity,
    approvals, or financial actions.

    `available()` means the ADAPTER is operational/callable — it does NOT mean a generative model is
    ready. For generation readiness (e.g. provider selection or UI status) use
    `status().generation_available`."""
    def available(self) -> bool: ...
    def status(self) -> ProviderStatus: ...
    def generate(self, request: PromptRequest, config: ProviderConfiguration) -> RawProviderResponse: ...
