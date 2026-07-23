# Typed errors for the AI platform application layer.
from __future__ import annotations
from typing import Any, Optional


class AiError(Exception):
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class ConversationNotFoundError(AiError):
    """No conversation exists for the requested identifier."""


class AiScopeError(AiError):
    """The requested record is outside the (user_id, cycle_id) scope — refused to prevent leakage."""


class MemoryProvenanceError(AiError):
    """A review-memory entry lacks required provenance (content, or a deterministic source for a
    system-derived entry). Model-authored durable memory is not permitted."""
