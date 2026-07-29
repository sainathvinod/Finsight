"""Fail-closed local-only configuration for Stage 2 Private Ask Fin."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

from finsight.domain.ai.contracts import (
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    ProviderConfiguration,
)
from finsight.domain.ai.local_endpoint import (
    is_cloud_style_model_alias,
    normalized_loopback_http_url,
)


STAGE2_LOCAL_MODEL_PROFILE_ID = "stage2-local-ollama-gguf-v1"
_MODEL_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


class PrivateAskFinConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class PrivateAskFinSettings:
    provider_configuration: ProviderConfiguration
    status_timeout_seconds: float
    approved_model_digest: str = ""
    approved_model_profile_id: str = STAGE2_LOCAL_MODEL_PROFILE_ID


def _positive_number(env, key: str, default: float) -> float:
    raw = env.get(key)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise PrivateAskFinConfigurationError(f"{key} must be a number.")
    if value <= 0:
        raise PrivateAskFinConfigurationError(f"{key} must be greater than zero.")
    return value


def _positive_integer_or_none(env, key: str):
    raw = env.get(key)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise PrivateAskFinConfigurationError(f"{key} must be an integer.")
    if value <= 0:
        raise PrivateAskFinConfigurationError(f"{key} must be greater than zero.")
    return value


def require_loopback_ollama_url(value: str) -> str:
    """Permit HTTP only to the operating system's loopback interface."""

    try:
        return normalized_loopback_http_url(value)
    except ValueError:
        raise PrivateAskFinConfigurationError(
            "FINSIGHT_OLLAMA_BASE_URL must be a plain HTTP loopback endpoint "
            "with an explicit local port."
        )


def load_private_ask_fin_settings(env=None) -> PrivateAskFinSettings:
    """Load only Ollama configuration; no cloud-provider selector exists."""

    env = os.environ if env is None else env
    if (env.get("FINSIGHT_AI_PROVIDER") or "ollama").strip().casefold() not in {
        "ollama",
        "",
    }:
        raise PrivateAskFinConfigurationError(
            "Stage 2 Private Ask Fin supports only the local Ollama provider."
        )
    base_url = require_loopback_ollama_url(
        (env.get("FINSIGHT_OLLAMA_BASE_URL") or DEFAULT_OLLAMA_BASE_URL).strip()
    )
    model = (env.get("FINSIGHT_OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL).strip()
    if not model:
        raise PrivateAskFinConfigurationError(
            "FINSIGHT_OLLAMA_MODEL must not be empty."
        )
    if is_cloud_style_model_alias(model):
        raise PrivateAskFinConfigurationError(
            "FINSIGHT_OLLAMA_MODEL must identify a pinned local model, not a "
            "cloud or remote alias."
        )
    approved_digest = (
        env.get("FINSIGHT_OLLAMA_MODEL_DIGEST") or ""
    ).strip().casefold()
    if approved_digest and _MODEL_DIGEST.fullmatch(approved_digest) is None:
        raise PrivateAskFinConfigurationError(
            "FINSIGHT_OLLAMA_MODEL_DIGEST must be sha256 followed by exactly "
            "64 lowercase hexadecimal characters."
        )
    request_timeout = _positive_number(
        env, "FINSIGHT_AI_REQUEST_TIMEOUT", 30.0
    )
    status_timeout = _positive_number(
        env, "FINSIGHT_AI_STATUS_TIMEOUT", 2.0
    )
    max_tokens = _positive_integer_or_none(
        env, "FINSIGHT_AI_MAX_OUTPUT_TOKENS"
    )
    return PrivateAskFinSettings(
        provider_configuration=ProviderConfiguration.ollama(
            model=model,
            base_url=base_url,
            request_timeout_seconds=request_timeout,
            max_output_tokens=max_tokens,
        ),
        status_timeout_seconds=status_timeout,
        approved_model_digest=approved_digest,
    )
