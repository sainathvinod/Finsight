# Implements: Phase 4C.6 — environment-backed AI runtime configuration (infrastructure). Reads
# FINSIGHT_* env vars (with bare OLLAMA_* fallback for URL/model only), validates fail-fast, and
# returns the existing immutable application/domain contracts. Nothing is persisted to SQLite; no
# secrets. Numeric values are isolated here — never hidden inside the provider or validator.
#
# Note: this module deliberately does NOT import urllib — URL validation is a minimal manual check so
# that urllib stays confined to the OllamaProvider adapter (architecture invariant).
from __future__ import annotations
import os
from dataclasses import dataclass

from finsight.application.ai.contracts import ResponseValidationLimits
from finsight.application.ai.retry import RetryPolicy
from finsight.domain.ai.contracts import (
    DEFAULT_OLLAMA_BASE_URL, DEFAULT_OLLAMA_MODEL, ProviderConfiguration,
)

# Approved development defaults (overrideable; documented; isolated to this loader).
_DEFAULT_REQUEST_TIMEOUT = 30.0
_DEFAULT_STATUS_TIMEOUT = 2.0
_DEFAULT_RETRY_FORMAT = 1
_DEFAULT_RETRY_TIMEOUT = 0
_DEFAULT_RETRY_DELAY = 0.0
_SUPPORTED_PROVIDERS = ("none", "ollama")
_BOOL_TRUE = ("1", "true", "yes", "on")
_BOOL_FALSE = ("", "0", "false", "no", "off")


class AiConfigError(ValueError):
    """Fail-fast configuration error raised at composition. Carries only the offending key/reason —
    never any value that could be sensitive."""


@dataclass(frozen=True)
class AiRuntimeSettings:
    """Fully-resolved, validated AI runtime configuration. Immutable; safe to log/inspect (no secrets).

    ``demo_authorized`` reflects the LOCAL/DEMO-ONLY development gate (FINSIGHT_AI_DEMO_AUTHORIZED). It
    is NOT production consent and has no effect unless a DevelopmentAiAuthorizationPolicy is explicitly
    wired from it; provider availability never implies authorization."""
    provider: str                                  # "none" | "ollama"
    provider_config: ProviderConfiguration
    status_timeout_seconds: float
    retry_policy: RetryPolicy
    validation_limits: ResponseValidationLimits
    demo_authorized: bool = False


def _positive_float(env, key, default) -> float:
    raw = env.get(key)
    if raw is None or raw == "":
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise AiConfigError("%s must be a number" % key)
    if value <= 0:
        raise AiConfigError("%s must be > 0" % key)
    return value


def _nonneg_float(env, key, default) -> float:
    raw = env.get(key)
    if raw is None or raw == "":
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise AiConfigError("%s must be a number" % key)
    if value < 0:
        raise AiConfigError("%s must be >= 0" % key)
    return value


def _nonneg_int(env, key, default) -> int:
    raw = env.get(key)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise AiConfigError("%s must be an integer" % key)
    if value < 0:
        raise AiConfigError("%s must be >= 0" % key)
    return value


def _opt_positive_int(env, key):
    raw = env.get(key)
    if raw is None or raw == "":
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise AiConfigError("%s must be an integer" % key)
    if value <= 0:
        raise AiConfigError("%s must be > 0" % key)
    return value


def _opt_nonneg_int(env, key):
    raw = env.get(key)
    if raw is None or raw == "":
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise AiConfigError("%s must be an integer" % key)
    if value < 0:
        raise AiConfigError("%s must be >= 0" % key)
    return value


def _bool_flag(env, key, default=False) -> bool:
    """Explicit, deterministic boolean parse. Accepts 1/true/yes/on and 0/false/no/off/'' (case-
    insensitive); any other value is rejected fail-fast (never silently authorized or denied)."""
    raw = env.get(key)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in _BOOL_TRUE:
        return True
    if normalized in _BOOL_FALSE:
        return False
    raise AiConfigError("%s must be one of %s / %s" % (key, _BOOL_TRUE, _BOOL_FALSE[1:]))


# CONFIDENTIALITY (ADR-013/ADR-009, DEC-022 "AI enhances, never defines"): Ask Fin's only generative
# provider is a LOCAL Ollama. The endpoint MUST be a loopback address so review data never leaves the
# machine — no cloud/remote inference is ever contacted. This is enforced here (fail-fast at config
# load), not merely documented.
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _host_of(authority: str) -> str:
    """Extract the host from an authority (host[:port]); handles bracketed IPv6 (`[::1]:11434`).
    urllib-free (this module deliberately keeps urllib confined to the Ollama adapter)."""
    if authority.startswith("["):                      # IPv6 literal, e.g. [::1]:11434
        return authority[1:authority.index("]")] if "]" in authority else authority[1:]
    return authority.rsplit(":", 1)[0] if ":" in authority else authority


def _validate_base_url(url: str) -> str:
    # http(s) scheme + a LOOPBACK host only. Remote/cloud endpoints are rejected fail-fast.
    if not (url.startswith("http://") or url.startswith("https://")):
        raise AiConfigError("FINSIGHT_OLLAMA_BASE_URL must start with http:// or https://")
    authority = url.split("://", 1)[1].split("/", 1)[0]   # host[:port] before any path
    if not authority:
        raise AiConfigError("FINSIGHT_OLLAMA_BASE_URL must include a host")
    # Reject URL userinfo: "http://localhost:11434@evil.example.com/" would connect to evil.example.com
    # while a naive host parse sees "localhost". No userinfo is ever valid for a loopback Ollama.
    if "@" in authority:
        raise AiConfigError(
            "FINSIGHT_OLLAMA_BASE_URL must not contain user info (@) — the real host would be remote; "
            "Ask Fin is local-only (confidentiality)")
    host = _host_of(authority)
    if host not in _LOOPBACK_HOSTS:
        raise AiConfigError(
            "FINSIGHT_OLLAMA_BASE_URL must be a LOOPBACK address (localhost, 127.0.0.1, or ::1) — "
            "Ask Fin is local-only; remote/cloud AI endpoints are not permitted (confidentiality)")
    return url


def load_ai_runtime_settings(env=None) -> AiRuntimeSettings:
    """Resolve and validate all AI runtime configuration. Raises AiConfigError on any invalid value."""
    env = os.environ if env is None else env

    provider = (env.get("FINSIGHT_AI_PROVIDER") or "none").strip().lower()
    if provider not in _SUPPORTED_PROVIDERS:
        raise AiConfigError("FINSIGHT_AI_PROVIDER must be one of %s" % (_SUPPORTED_PROVIDERS,))

    base_url = _validate_base_url(
        env.get("FINSIGHT_OLLAMA_BASE_URL") or env.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_BASE_URL)
    model = (env.get("FINSIGHT_OLLAMA_MODEL") or env.get("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL).strip()
    if not model:
        raise AiConfigError("FINSIGHT_OLLAMA_MODEL must not be empty")

    request_timeout = _positive_float(env, "FINSIGHT_AI_REQUEST_TIMEOUT", _DEFAULT_REQUEST_TIMEOUT)
    status_timeout = _positive_float(env, "FINSIGHT_AI_STATUS_TIMEOUT", _DEFAULT_STATUS_TIMEOUT)
    max_output_tokens = _opt_positive_int(env, "FINSIGHT_AI_MAX_OUTPUT_TOKENS")

    if provider == "ollama":
        provider_config = ProviderConfiguration.ollama(
            model=model, base_url=base_url, request_timeout_seconds=request_timeout,
            max_output_tokens=max_output_tokens)
    else:
        provider_config = ProviderConfiguration.null()

    retry_policy = RetryPolicy(
        max_response_format_retries=_nonneg_int(env, "FINSIGHT_AI_RETRY_FORMAT", _DEFAULT_RETRY_FORMAT),
        max_timeout_retries=_nonneg_int(env, "FINSIGHT_AI_RETRY_TIMEOUT", _DEFAULT_RETRY_TIMEOUT),
        retry_delay_seconds=_nonneg_float(env, "FINSIGHT_AI_RETRY_DELAY", _DEFAULT_RETRY_DELAY))

    validation_limits = ResponseValidationLimits(
        max_answer_chars=_opt_nonneg_int(env, "FINSIGHT_AI_MAX_ANSWER_CHARS"),
        max_citations=_opt_nonneg_int(env, "FINSIGHT_AI_MAX_CITATIONS"),
        max_citation_key_chars=_opt_nonneg_int(env, "FINSIGHT_AI_MAX_CITATION_KEY_CHARS"))

    demo_authorized = _bool_flag(env, "FINSIGHT_AI_DEMO_AUTHORIZED", default=False)

    return AiRuntimeSettings(provider=provider, provider_config=provider_config,
                             status_timeout_seconds=status_timeout, retry_policy=retry_policy,
                             validation_limits=validation_limits, demo_authorized=demo_authorized)
