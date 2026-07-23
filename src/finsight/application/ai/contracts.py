# AI execution-seam contracts (application layer). These are orchestration contracts — the request a
# provider is asked to complete, and the raw completion it returns — not domain concepts, so they
# live with the application AI services rather than in domain/ai (moved in Phase 4C.2).
# Framework-independent; immutable; no I/O.
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

DEFAULT_PROMPT_VERSION = "v1"
DEFAULT_SCHEMA_VERSION = "v1"


@dataclass(frozen=True)
class PromptRequest:
    """Provider-independent execution request. The PromptBuilder owns HOW each section is composed
    from masked grounding/history; provider adapters serialize this into their own wire format.
    Sections are already-composed, provider-neutral text."""
    system_prompt: str
    context_block: str
    conversation_block: str
    question: str
    output_schema: str
    prompt_version: str = DEFAULT_PROMPT_VERSION
    schema_version: str = DEFAULT_SCHEMA_VERSION


@dataclass(frozen=True)
class RawProviderResponse:
    """Raw, transient provider output. NEVER persisted (ADR-009). Carries the raw text plus
    non-sensitive execution metadata (provider, model, timing/finish reason)."""
    text: str
    provider: str
    model: str
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderStatus:
    """Two orthogonal facts about a provider. `operational` = the adapter is callable. `generation
    _available` = a real generative model will actually answer. NullProvider is operational but NOT
    generation-available. UI generation status and provider selection MUST use `generation_available`
    — never adapter callability alone."""
    operational: bool
    generation_available: bool
    reason: str = ""
