"""Focused checks for precise, non-mutating local Ollama setup states."""
from __future__ import annotations

import json
import socket
import urllib.error

from finsight.application.ai.private_contracts import LocalAiSetupState
from finsight.domain.ai.contracts import ProviderConfiguration
from finsight.infrastructure.ai.providers.ollama import OllamaProvider


RAW_DIGEST = "a" * 64
APPROVED_DIGEST = f"sha256:{RAW_DIGEST}"


class _Response:
    def __init__(self, body):
        self._body = json.dumps(body).encode("utf-8")
        self.peer_address = ("127.0.0.1", 11434)

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Inventory:
    def __init__(self, *, models=None, error=None):
        self.models = models or []
        self.error = error

    def __call__(self, request, timeout):
        if self.error is not None:
            raise self.error
        if request.full_url.endswith("/api/tags"):
            return _Response({"models": self.models})
        if request.full_url.endswith("/api/show"):
            return _Response(
                {
                    "details": {"format": "gguf", "family": "llama"},
                    "model_info": {"general.architecture": "llama"},
                    "capabilities": ["completion"],
                }
            )
        raise AssertionError(request.full_url)


def _resolver(*_args, **_kwargs):
    return [
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            6,
            "",
            ("127.0.0.1", 11434),
        )
    ]


def _provider(opener, *, digest=""):
    return OllamaProvider(
        ProviderConfiguration.ollama(
            model="llama3.2:3b",
            base_url="http://localhost:11434",
        ),
        status_timeout=1.0,
        opener=opener,
        private_local=True,
        approved_model_digest=digest,
        approved_model_profile_id="stage2-local-ollama-gguf-v1",
        resolver=_resolver,
    )


def test_connection_refusal_distinguishes_installation_from_stopped_service():
    refused = _Inventory(
        error=urllib.error.URLError(
            ConnectionRefusedError("Connection refused")
        )
    )
    missing = _provider(refused).setup_status(
        installation_available=False
    )
    stopped = _provider(refused).setup_status(
        installation_available=True
    )

    assert missing.state is LocalAiSetupState.NOT_INSTALLED
    assert stopped.state is LocalAiSetupState.SERVICE_NOT_RUNNING


def test_timeout_and_connection_failure_are_distinct():
    timeout = _provider(
        _Inventory(error=socket.timeout("timed out"))
    ).setup_status(installation_available=True)
    failure = _provider(
        _Inventory(error=urllib.error.URLError("local endpoint failed"))
    ).setup_status(installation_available=True)

    assert timeout.state is LocalAiSetupState.TIMEOUT
    assert failure.state is LocalAiSetupState.CONNECTION_FAILURE


def test_missing_model_is_reported_but_available_model_is_auto_verified():
    missing = _provider(
        _Inventory(models=[{"name": "other:latest", "digest": RAW_DIGEST}])
    ).setup_status(installation_available=True)
    available = _provider(
        _Inventory(
            models=[{"name": "llama3.2:3b", "digest": RAW_DIGEST}]
        )
    ).setup_status(installation_available=True)

    assert missing.state is LocalAiSetupState.MODEL_NOT_DOWNLOADED
    assert missing.available_models == ("other:latest",)
    assert available.state is LocalAiSetupState.HEALTHY
    assert available.healthy
    assert available.observed_model_digest == APPROVED_DIGEST


def test_raw_ollama_digest_is_normalized_and_verified_as_healthy():
    status = _provider(
        _Inventory(
            models=[{"name": "llama3.2:3b", "digest": RAW_DIGEST}]
        ),
        digest=APPROVED_DIGEST,
    ).setup_status(installation_available=True)

    assert status.state is LocalAiSetupState.HEALTHY
    assert status.healthy
    assert status.observed_model_digest == APPROVED_DIGEST


def test_available_model_without_verifiable_digest_fails_closed():
    status = _provider(
        _Inventory(
            models=[{"name": "llama3.2:3b", "digest": "not-a-digest"}]
        )
    ).setup_status(installation_available=True)

    assert status.state is LocalAiSetupState.MODEL_VERIFICATION_FAILED
    assert not status.healthy
