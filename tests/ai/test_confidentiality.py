# Verifies: Ask Fin CONFIDENTIALITY / local-only guarantees (ADR-013, ADR-009, DEC-022). Ask Fin's
# only generative provider is a LOCAL Ollama on a loopback address; review data never leaves the
# machine — no cloud/remote provider, no external fallback, and the deterministic core makes no network
# calls at all. These are enforced (config + adapter), not merely documented.
import os
import re

import pytest

from finsight.infrastructure.ai.config import load_ai_runtime_settings, AiConfigError, _SUPPORTED_PROVIDERS
from finsight.infrastructure.ai.providers.ollama import OllamaProvider, _is_loopback
from finsight.application.ai.errors import ProviderUnavailableError
from finsight.domain.ai.contracts import ProviderConfiguration

_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src", "finsight")


# ---- loopback-only endpoint policy (config + adapter) ----
@pytest.mark.parametrize("url", ["http://localhost:11434", "http://127.0.0.1:11434", "http://[::1]:11434"])
def test_loopback_endpoints_accepted(url):
    s = load_ai_runtime_settings({"FINSIGHT_AI_PROVIDER": "ollama", "FINSIGHT_OLLAMA_BASE_URL": url})
    assert s.provider_config.base_url == url and _is_loopback(url)


@pytest.mark.parametrize("url", ["http://example.com:11434", "https://api.openai.com",
                                 "https://api.anthropic.com", "http://10.0.0.5:11434", "http://ollama.cloud"])
def test_non_loopback_endpoints_rejected_fail_fast(url):
    with pytest.raises(AiConfigError):
        load_ai_runtime_settings({"FINSIGHT_AI_PROVIDER": "ollama", "FINSIGHT_OLLAMA_BASE_URL": url})
    assert not _is_loopback(url)


def test_adapter_refuses_non_loopback_without_making_a_call():
    # Defense-in-depth: even if a non-loopback config were constructed, the adapter never calls out.
    calls = []
    cfg = ProviderConfiguration.ollama(model="m", base_url="http://evil.example.com:11434",
                                       request_timeout_seconds=1.0, max_output_tokens=None)
    prov = OllamaProvider(cfg, status_timeout=1.0, enabled=True,
                          opener=lambda req, timeout: calls.append(req) or None)
    assert prov.status().generation_available is False   # reported unavailable, not usable
    assert calls == []                                   # and NO network call was ever attempted
    with pytest.raises(ProviderUnavailableError):        # generate() surfaces the refusal directly
        prov._request("POST", "/api/chat", {"x": 1}, 1.0)
    assert calls == []


def test_adapter_only_contacts_the_configured_loopback_endpoint():
    seen = {}

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"models": []}'

    def opener(req, timeout):
        seen["url"] = req.full_url
        return _Resp()
    cfg = ProviderConfiguration.ollama(model="m", base_url="http://127.0.0.1:11434",
                                       request_timeout_seconds=1.0, max_output_tokens=None)
    OllamaProvider(cfg, status_timeout=1.0, enabled=True, opener=opener).status()
    assert seen["url"].startswith("http://127.0.0.1:11434/")   # only the loopback endpoint contacted


# ---- no cloud provider / no external fallback ----
def test_only_local_providers_are_supported():
    assert _SUPPORTED_PROVIDERS == ("none", "ollama")    # no openai/anthropic/cloud provider


def test_no_cloud_sdk_or_endpoint_referenced_in_source():
    banned = ("openai", "anthropic", "api.openai.com", "api.anthropic.com", "googleapis",
              "azure", "bedrock", "huggingface.co", "cohere")
    hits = []
    for dp, _dirs, files in os.walk(_SRC):
        for fn in files:
            if fn.endswith(".py"):
                txt = open(os.path.join(dp, fn), encoding="utf-8").read().lower()
                for b in banned:
                    if b in txt and "test" not in fn:
                        hits.append((os.path.relpath(os.path.join(dp, fn), _SRC), b))
    assert hits == [], hits                              # no cloud AI SDK/endpoint anywhere in src


def test_only_ollama_provider_module_imports_urllib():
    # network egress is confined to the single local Ollama adapter (architecture invariant)
    importers = []
    for dp, _dirs, files in os.walk(_SRC):
        for fn in files:
            if fn.endswith(".py"):
                txt = open(os.path.join(dp, fn), encoding="utf-8").read()
                if re.search(r"^\s*import\s+urllib|^\s*from\s+urllib", txt, re.M):
                    importers.append(os.path.relpath(os.path.join(dp, fn), _SRC))
    assert importers == ["infrastructure/ai/providers/ollama.py"], importers


# ---- deterministic core makes no network calls ----
def test_deterministic_workflow_makes_no_network_calls(tmp_path, monkeypatch):
    import socket
    from finsight.app import build_app
    from finsight.application.review_session import ReviewSession
    from finsight.application.workflow import ReviewWorkflowService
    from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget

    def _boom(*a, **k):
        raise AssertionError("deterministic workflow attempted a network connection")
    monkeypatch.setattr(socket.socket, "connect", _boom)

    db = str(tmp_path / "fs.db")
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    c = build_app(db, FixedClock()); wf = ReviewWorkflowService(c.orch.engine)
    wf.create_review("A", "May", "2026"); s = ReviewSession("A")
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s)
    assert wf.analyze(s).finding_count >= 1              # full review, zero network egress
    wf.summarize(s); wf.export(s)
