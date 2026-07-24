# Typed errors for the AI platform application layer.
from __future__ import annotations
from typing import Any, Optional


class AiError(Exception):
    # Retry eligibility is a property of the error TYPE (default: not retryable). The future
    # orchestrator reads `.retryable` and owns the retry count — validation/verification never do.
    retryable: bool = False

    def __init__(self, message: str, detail: Optional[Any] = None, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.detail = detail
        self.code = code            # machine-readable, NON-SENSITIVE reason; never raw output/content


class ConversationNotFoundError(AiError):
    """No conversation exists for the requested identifier."""


class AiScopeError(AiError):
    """The requested record is outside the (user_id, cycle_id) scope — refused to prevent leakage."""


class MemoryProvenanceError(AiError):
    """A review-memory entry lacks required provenance (content, or a deterministic source for a
    system-derived entry). Model-authored durable memory is not permitted."""


# --- Phase 4C error model (raised by the AI execution pipeline; stages noted per error) ---
class AiAuthorizationError(AiError):
    """AI use is not permitted in the current mode (authorization stage). Note: provider
    *unavailability* is NOT an error — it degrades to NullProvider — so this covers mode/read-only
    violations only."""


class GroundingUnavailableError(AiError):
    """No deterministic grounding exists for the requested review (grounding-retrieval stage)."""


class MaskingError(AiError):
    """Masking could not be completed. Fail-closed: the provider must not be called (masking stage)."""


class PromptBuildError(AiError):
    """The prompt could not be assembled (PromptBuilder stage)."""


class PromptBudgetError(AiError):
    """Grounding does not fit the minimum viable context budget (PromptBuilder stage)."""


class ProviderError(AiError):
    """Base for AI provider transport/execution failures (provider stage). Infrastructure adapters
    wrap raw transport exceptions into this hierarchy so the application never sees urllib/HTTP."""


class ProviderUnavailableError(ProviderError):
    """The AI provider is not reachable/available (provider stage)."""


class ProviderTimeoutError(ProviderError):
    """The AI provider did not respond within the configured timeout (provider stage)."""
    retryable = True                # bounded retry configured elsewhere; loop owned by orchestrator


class ResponseFormatError(AiError):
    """The provider response was malformed or violated the required output schema
    (response-validation stage). Retryable: a single reformat attempt may succeed (count owned by the
    future orchestrator). Raised only by ResponseValidator; carries a non-sensitive `code` only."""
    retryable = True


class CitationError(AiError):
    """The response cited references that do not resolve to this turn's deterministic context
    (citation-verification stage). NON-retryable in v1: the same deterministic context will not change
    on retry. Raised only by CitationVerifier; carries a non-sensitive `code` only."""
    retryable = False
