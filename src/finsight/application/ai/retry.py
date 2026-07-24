# Implements: Phase 4C.5 — retry policy value object + Sleeper abstraction.
#
# The RetryPolicy owns MAX attempts and delay values only; AskFinService owns the transient attempt
# counters and the loop. Delays are performed by an injected Sleeper so tests never really sleep.
# ResponseValidator and CitationVerifier never retry. Production defaults are deferred to composition —
# the defaults here are the safe no-retry floor, nothing invented.
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


class Sleeper(Protocol):
    """Performs a retry delay. Injected so tests can supply a no-op/recording fake — no real sleeping
    in tests."""
    def sleep(self, seconds: float) -> None: ...


@dataclass(frozen=True)
class RetryPolicy:
    """Bounds only. max_response_format_retries applies to ResponseFormatError (approved: at most one);
    max_timeout_retries applies to ProviderTimeoutError. CitationError and
    authorization/scope/grounding/masking/prompt errors are never retried and have no bound here."""
    max_response_format_retries: int = 0
    max_timeout_retries: int = 0
    retry_delay_seconds: float = 0.0

    def __post_init__(self):
        for name in ("max_response_format_retries", "max_timeout_retries"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("%s must be an int >= 0" % name)
        if isinstance(self.retry_delay_seconds, bool) or not isinstance(
                self.retry_delay_seconds, (int, float)) or self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be a number >= 0")
