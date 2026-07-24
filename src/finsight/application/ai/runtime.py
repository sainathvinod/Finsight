# Implements: Phase 4C.5 — AiProviderRuntime: the narrow provider-execution collaborator.
#
# It receives an already-built PromptRequest, invokes the configured active provider, and degrades to
# the injected NullProvider on ProviderUnavailableError. It reports which provider/model actually
# produced the response and whether generation was available. It is NOT a service locator or a generic
# provider factory, and it is independent of masking, prompting, validation, citation, journaling, and
# UI. ProviderTimeoutError is NOT handled here — it propagates so AskFinService owns retry.
# No OllamaProvider or HTTP transport in this phase.
from __future__ import annotations
from dataclasses import dataclass

from finsight.application.ai.contracts import PromptRequest, RawProviderResponse
from finsight.application.ai.errors import ProviderUnavailableError
from finsight.application.ai.ports import AiProviderPort
from finsight.domain.ai.contracts import ProviderConfiguration


@dataclass(frozen=True)
class ProviderExecution:
    """What the runtime produced this call. `degraded` = the fallback (NullProvider) was used because
    the active provider was unavailable. `generation_available` = the active provider reported a live
    generative model at call time. Carries NO prompt and NO original content beyond the raw response
    the caller must still validate."""
    response: RawProviderResponse
    provider: str
    model: str
    degraded: bool
    generation_available: bool


class AiProviderRuntime:
    def __init__(self, active: AiProviderPort, fallback: AiProviderPort,
                 config: ProviderConfiguration):
        self._active = active
        self._fallback = fallback          # NullProvider — the degrade target
        self._config = config

    def execute(self, request: PromptRequest) -> ProviderExecution:
        generation_available = self._active.status().generation_available
        try:
            resp = self._active.generate(request, self._config)
        except ProviderUnavailableError:
            # Provider unavailability is NOT an error condition — degrade to NullProvider and continue.
            # Its validated refusal flows through the normal pipeline exactly like any provider.
            resp = self._fallback.generate(request, self._config)
            return ProviderExecution(resp, resp.provider, resp.model, degraded=True,
                                     generation_available=False)
        return ProviderExecution(resp, resp.provider, resp.model, degraded=False,
                                 generation_available=generation_available)
