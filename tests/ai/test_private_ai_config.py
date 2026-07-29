"""Security tests for the local-only Stage 2 Ollama configuration."""
from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from finsight.delivery.desktop.ask_fin_preferences import (
    PrivateAskFinPreferenceStore,
)
from finsight.infrastructure.ai.private_config import (
    PrivateAskFinConfigurationError,
    load_private_ask_fin_settings,
    require_loopback_ollama_url,
)
from finsight.infrastructure.ai.providers.ollama import _RejectRedirects


@pytest.mark.parametrize(
    "url",
    (
        "http://localhost:11434",
        "http://127.0.0.1:11434",
        "http://[::1]:11434",
    ),
)
def test_loopback_ollama_endpoints_are_allowed(url):
    assert require_loopback_ollama_url(url) == url


@pytest.mark.parametrize(
    "url",
    (
        "https://localhost:11434",
        "http://ollama.example.com:11434",
        "http://192.168.1.20:11434",
        "http://127.0.0.2:11434",
        "http://8.8.8.8:11434",
        "http://user:secret@localhost:11434",
        "http://localhost:11434/api/chat",
        "file:///tmp/ollama.sock",
        "localhost:11434",
    ),
)
def test_nonlocal_or_ambiguous_endpoints_are_rejected(url):
    with pytest.raises(PrivateAskFinConfigurationError):
        require_loopback_ollama_url(url)


def test_settings_have_no_cloud_provider_or_fallback_selector():
    settings = load_private_ask_fin_settings(env={})
    assert settings.provider_configuration.provider == "ollama"
    assert settings.provider_configuration.base_url == "http://localhost:11434"
    assert settings.provider_configuration.temperature == 0.0
    assert settings.approved_model_digest == ""


@pytest.mark.parametrize("provider", ("openai", "anthropic", "gemini", "azure"))
def test_external_ai_provider_names_fail_closed(provider):
    with pytest.raises(PrivateAskFinConfigurationError):
        load_private_ask_fin_settings(env={"FINSIGHT_AI_PROVIDER": provider})


def test_external_ollama_host_cannot_be_smuggled_through_environment():
    with pytest.raises(PrivateAskFinConfigurationError):
        load_private_ask_fin_settings(
            env={
                "FINSIGHT_AI_PROVIDER": "ollama",
                "FINSIGHT_OLLAMA_BASE_URL": "https://cloud.example/v1",
            }
        )


@pytest.mark.parametrize(
    "model",
    (
        "gpt-oss:120b-cloud",
        "remote/qwen3",
        "https://models.example/model",
        "azure-openai:model",
    ),
)
def test_cloud_style_ollama_model_aliases_are_rejected(model):
    with pytest.raises(PrivateAskFinConfigurationError):
        load_private_ask_fin_settings(
            env={
                "FINSIGHT_OLLAMA_MODEL": model,
                "FINSIGHT_OLLAMA_MODEL_DIGEST": "sha256:" + ("a" * 64),
            }
        )


def test_approved_model_digest_is_validated_and_retained():
    digest = "sha256:" + ("a" * 64)
    settings = load_private_ask_fin_settings(
        env={"FINSIGHT_OLLAMA_MODEL_DIGEST": digest}
    )
    assert settings.approved_model_digest == digest
    with pytest.raises(PrivateAskFinConfigurationError):
        load_private_ask_fin_settings(
            env={"FINSIGHT_OLLAMA_MODEL_DIGEST": "sha256:not-a-digest"}
        )


def test_private_transport_redirect_policy_never_forwards_a_request():
    handler = _RejectRedirects()
    assert (
        handler.redirect_request(
            object(),
            object(),
            302,
            "Found",
            {},
            "https://external.example/collect",
        )
        is None
    )


def test_desktop_preferences_need_no_manual_model_identity_approval(tmp_path):
    settings = QSettings(
        str(tmp_path / "ask-fin.ini"), QSettings.Format.IniFormat
    )
    # Simulate an installation that used the former manual approval flow.
    settings.setValue(
        PrivateAskFinPreferenceStore.DIGEST_KEY,
        "sha256:" + ("a" * 64),
    )
    store = PrivateAskFinPreferenceStore(settings)

    snapshot = store.snapshot(environment={})
    saved = store.save(
        endpoint="http://127.0.0.1:11434",
        model="llama3.2:3b",
        approved_model_digest="sha256:" + ("b" * 64),
    )

    assert snapshot.approved_model_digest == ""
    assert saved.approved_model_digest == ""
    assert settings.value(PrivateAskFinPreferenceStore.DIGEST_KEY) is None


def test_environment_digest_remains_an_optional_managed_pin(tmp_path):
    store = PrivateAskFinPreferenceStore(
        QSettings(
            str(tmp_path / "ask-fin.ini"), QSettings.Format.IniFormat
        )
    )
    managed_digest = "sha256:" + ("c" * 64)

    snapshot = store.snapshot(
        environment={"FINSIGHT_OLLAMA_MODEL_DIGEST": managed_digest}
    )

    assert snapshot.approved_model_digest == managed_digest
    assert snapshot.environment_override
