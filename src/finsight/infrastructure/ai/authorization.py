# Implements: Phase 4C.6A — DEVELOPMENT/DEMO-ONLY authorization policy adapter.
#
# THIS IS NOT PRODUCTION CONSENT. It is a local development gate that lets the completed AskFin
# pipeline run against a local Ollama for manual smoke testing. It stores nothing, reads no database,
# creates no consent record, and confers no enterprise/role-based authorization. Production remains
# fail-closed: unless an authorization policy is explicitly supplied, AskFinService returns REFUSED.
#
# It implements the existing application port (AiAuthorizationPolicy) WITHOUT changing application
# rules: explanation-only, non-mutating; provider availability is independent and never implies
# authorization; NullProvider does not bypass it.
from __future__ import annotations

from finsight.application.ai.ask_fin_contracts import AiAuthorizationContext
from finsight.application.ai.errors import AiAuthorizationError

# FinSight is read-only; the only mode the demo policy will ever assert is explanation-only.
_EXPLANATION_ONLY_MODE = "explanation_only"


class DevelopmentAiAuthorizationPolicy:
    """Local/demo authorization gated solely by an explicit development flag (user_consent). Fail-closed
    when the flag is false. Never authorizes deterministic-workflow mutation."""

    def __init__(self, authorized: bool):
        self._authorized = bool(authorized)

    @classmethod
    def from_settings(cls, settings) -> "DevelopmentAiAuthorizationPolicy":
        """Build from AiRuntimeSettings.demo_authorized (FINSIGHT_AI_DEMO_AUTHORIZED)."""
        return cls(authorized=settings.demo_authorized)

    def authorize(self, *, user_id: str, cycle_id: str) -> AiAuthorizationContext:
        context = AiAuthorizationContext(
            user_id=user_id,
            cycle_id=cycle_id,
            application_mode=_EXPLANATION_ONLY_MODE,   # explanation-only / non-mutating, always
            ai_capability_available=True,              # the AI feature exists; NOT provider availability
            user_consent=self._authorized,             # the explicit development gate
        )
        # Fail-closed: ALL conditions required. The gate (user_consent) is the decisive local signal.
        if not (context.user_consent and context.ai_capability_available
                and context.application_mode == _EXPLANATION_ONLY_MODE):
            raise AiAuthorizationError(
                "development AI authorization is not granted (set FINSIGHT_AI_DEMO_AUTHORIZED=true for "
                "local demo use only)", code="demo_not_authorized")
        return context
