"""Persistent, non-secret application preferences for local Ask Fin."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from PySide6.QtCore import QSettings

from finsight.infrastructure.ai.private_config import (
    PrivateAskFinSettings,
    load_private_ask_fin_settings,
)


_ENV_KEYS = (
    "FINSIGHT_OLLAMA_BASE_URL",
    "FINSIGHT_OLLAMA_MODEL",
    "FINSIGHT_OLLAMA_MODEL_DIGEST",
)


@dataclass(frozen=True)
class PrivateAskFinPreferenceSnapshot:
    endpoint: str
    model: str
    approved_model_digest: str
    environment_override: bool = False


class PrivateAskFinPreferenceStore:
    """QSettings adapter for the local endpoint and model name.

    A model digest supplied by the process environment remains an optional
    managed deployment pin. Normal desktop use does not persist a manual
    identity approval: the provider automatically pins and verifies Ollama's
    exact observed digest before every prompt-bearing request.
    """

    ENDPOINT_KEY = "ask_fin/ollama_endpoint"
    MODEL_KEY = "ask_fin/ollama_model"
    DIGEST_KEY = "ask_fin/ollama_model_digest"

    def __init__(self, settings: QSettings | None = None):
        self._settings = settings or QSettings("FinSight", "FinSight")

    def snapshot(
        self, *, environment: Mapping[str, str] | None = None
    ) -> PrivateAskFinPreferenceSnapshot:
        values = self._effective_environment(environment=environment)
        resolved = load_private_ask_fin_settings(env=values)
        return PrivateAskFinPreferenceSnapshot(
            endpoint=resolved.provider_configuration.base_url,
            model=resolved.provider_configuration.model,
            approved_model_digest=resolved.approved_model_digest,
            environment_override=any(
                key in (os.environ if environment is None else environment)
                for key in _ENV_KEYS
            ),
        )

    def effective_settings(
        self, *, environment: Mapping[str, str] | None = None
    ) -> PrivateAskFinSettings:
        return load_private_ask_fin_settings(
            env=self._effective_environment(environment=environment)
        )

    def save(
        self,
        *,
        endpoint: str,
        model: str,
        approved_model_digest: str,
    ) -> PrivateAskFinPreferenceSnapshot:
        # Validate the complete candidate before changing persistent state.
        # ``approved_model_digest`` remains in this boundary for compatibility
        # with older callers, but manual digest approval is intentionally no
        # longer persisted. Explicit environment policy is applied later by
        # ``effective_settings``.
        del approved_model_digest
        candidate = load_private_ask_fin_settings(
            env={
                "FINSIGHT_AI_PROVIDER": "ollama",
                "FINSIGHT_OLLAMA_BASE_URL": endpoint,
                "FINSIGHT_OLLAMA_MODEL": model,
            }
        )
        self._settings.setValue(
            self.ENDPOINT_KEY,
            candidate.provider_configuration.base_url,
        )
        self._settings.setValue(
            self.MODEL_KEY,
            candidate.provider_configuration.model,
        )
        # Migrate away any digest saved by the former manual-approval flow.
        self._settings.remove(self.DIGEST_KEY)
        self._settings.sync()
        return PrivateAskFinPreferenceSnapshot(
            endpoint=candidate.provider_configuration.base_url,
            model=candidate.provider_configuration.model,
            approved_model_digest=candidate.approved_model_digest,
            environment_override=False,
        )

    def _effective_environment(
        self, *, environment: Mapping[str, str] | None
    ) -> dict[str, str]:
        values: dict[str, str] = {
            "FINSIGHT_AI_PROVIDER": "ollama",
        }
        endpoint = str(self._settings.value(self.ENDPOINT_KEY, "") or "").strip()
        model = str(self._settings.value(self.MODEL_KEY, "") or "").strip()
        if endpoint:
            values["FINSIGHT_OLLAMA_BASE_URL"] = endpoint
        if model:
            values["FINSIGHT_OLLAMA_MODEL"] = model
        source = os.environ if environment is None else environment
        for key in ("FINSIGHT_AI_PROVIDER", *_ENV_KEYS):
            if key in source:
                values[key] = str(source[key])
        for key in (
            "FINSIGHT_AI_REQUEST_TIMEOUT",
            "FINSIGHT_AI_STATUS_TIMEOUT",
            "FINSIGHT_AI_MAX_OUTPUT_TOKENS",
        ):
            if key in source:
                values[key] = str(source[key])
        return values


__all__ = [
    "PrivateAskFinPreferenceSnapshot",
    "PrivateAskFinPreferenceStore",
]
