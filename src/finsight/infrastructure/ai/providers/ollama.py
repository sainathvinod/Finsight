# Implements: Phase 4C.6 — OllamaProvider: the real AiProviderPort transport adapter (infrastructure).
#
# It ONLY: reports ProviderStatus, serializes a PromptRequest, performs the HTTP call, parses the
# transport ENVELOPE, returns RawProviderResponse, and maps transport/provider failures to the
# existing typed provider errors. It NEVER validates the answer JSON (that is ResponseValidator),
# verifies citations, retries, builds prompts, persists, logs prompt/response content, imports
# AskFinService/UI/repositories, or reinterprets financial facts. This is the ONLY module that imports
# urllib.
from __future__ import annotations
import json
import socket
import urllib.error
import urllib.request

from finsight.application.ai.contracts import PromptRequest, ProviderStatus, RawProviderResponse
from finsight.application.ai.errors import (
    ProviderError, ProviderTimeoutError, ProviderUnavailableError,
)
from finsight.diagnostics import get_logger
from finsight.domain.ai.contracts import ProviderConfiguration

_log = get_logger("ai.provider.ollama")


def _default_opener(req, timeout):
    return urllib.request.urlopen(req, timeout=timeout)   # pragma: no cover - real network seam


# Defense-in-depth confidentiality guard (also enforced at config load): Ask Fin is LOCAL-ONLY, so
# this adapter refuses to open any non-loopback endpoint — review data can never leave the machine.
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _is_loopback(base_url: str) -> bool:
    authority = base_url.split("://", 1)[-1].split("/", 1)[0]
    if authority.startswith("["):                         # bracketed IPv6, e.g. [::1]:11434
        host = authority[1:authority.index("]")] if "]" in authority else authority[1:]
    else:
        host = authority.rsplit(":", 1)[0] if ":" in authority else authority
    return host in _LOOPBACK_HOSTS


class OllamaProvider:
    """AiProviderPort adapter for a local/remote Ollama server. `enabled` reflects whether provider
    selection chose ollama; when False the adapter reports provider_disabled and never calls out. The
    HTTP `opener` is injected so tests perform no network I/O."""

    def __init__(self, config: ProviderConfiguration, *, status_timeout: float,
                 enabled: bool = True, opener=None):
        self._config = config
        self._status_timeout = status_timeout
        self._enabled = enabled
        self._opener = opener or _default_opener

    # -------- AiProviderPort --------
    def available(self) -> bool:
        return True                                   # the adapter object is constructable/callable

    def status(self) -> ProviderStatus:
        if not self._enabled:
            return ProviderStatus(operational=True, generation_available=False,
                                  reason="provider_disabled")
        try:
            body = self._request("GET", "/api/tags", None, self._status_timeout)
        except ProviderTimeoutError:
            return ProviderStatus(True, False, "status_timeout")
        except ProviderUnavailableError:
            return ProviderStatus(True, False, "unreachable")
        except ProviderError:
            return ProviderStatus(True, False, "malformed_status_response")
        models = body.get("models") if isinstance(body, dict) else None
        if not isinstance(models, list):
            return ProviderStatus(True, False, "malformed_status_response")
        names = {m.get("name") for m in models if isinstance(m, dict)}
        if self._config.model in names:
            return ProviderStatus(True, True, "ok")
        return ProviderStatus(True, False, "model_missing")

    def generate(self, request: PromptRequest, config: ProviderConfiguration) -> RawProviderResponse:
        if not self._enabled:
            raise ProviderUnavailableError("ollama provider is disabled", code="provider_disabled")
        payload = self._build_payload(request, config)
        body = self._request("POST", "/api/chat", payload, config.request_timeout_seconds)
        return self._map_response(body, config)

    # -------- request/response --------
    def _build_payload(self, request: PromptRequest, config: ProviderConfiguration) -> dict:
        # Our instructions → system role; untrusted (already-fenced) data + question → user role.
        # Content is passed VERBATIM; the adapter never edits or reinterprets it.
        messages = [
            {"role": "system", "content": request.system_prompt + "\n\n" + request.output_schema},
            {"role": "user", "content": request.context_block + "\n" + request.conversation_block
             + "\n" + request.question},
        ]
        options = {"temperature": config.temperature}         # fixed 0.0 by ProviderConfiguration
        if config.max_output_tokens is not None:
            options["num_predict"] = config.max_output_tokens  # omitted entirely when unset
        return {"model": config.model, "messages": messages, "stream": False, "format": "json",
                "options": options}

    def _map_response(self, body, config: ProviderConfiguration) -> RawProviderResponse:
        if not isinstance(body, dict):
            raise ProviderError("unexpected provider response", code="provider_bad_response")
        if "error" in body:
            msg = str(body.get("error", "")).lower()
            if "not found" in msg:
                raise ProviderUnavailableError("model not found", code="model_missing")
            raise ProviderError("provider returned an error", code="provider_error")
        if body.get("done") is False:
            raise ProviderError("incomplete provider response", code="provider_incomplete")
        message = body.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ProviderError("missing message content", code="provider_missing_content")
        metadata = {"done_reason": body.get("done_reason"), "eval_count": body.get("eval_count")}
        duration = body.get("total_duration")
        if isinstance(duration, (int, float)) and not isinstance(duration, bool):
            metadata["latency_ms"] = duration / 1_000_000.0   # Ollama reports nanoseconds
        return RawProviderResponse(text=message["content"], provider="ollama",
                                   model=body.get("model") or config.model, metadata=metadata)

    # -------- transport (urllib), returns parsed envelope or raises a typed provider error --------
    def _request(self, method: str, path: str, payload, timeout):
        if not _is_loopback(self._config.base_url):        # never call out to a non-loopback endpoint
            raise ProviderUnavailableError("Ask Fin is local-only: the Ollama endpoint must be a "
                                           "loopback address", code="non_loopback_endpoint")
        url = self._config.base_url.rstrip("/") + path
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if data is not None else {}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            resp = self._opener(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            raise self._classify_http(exc.code)
        except (socket.timeout, TimeoutError):
            raise ProviderTimeoutError("provider timed out", code="request_timeout")
        except urllib.error.URLError as exc:
            raise self._classify_urlerror(exc)
        except ValueError:                                    # malformed URL / unknown scheme
            raise ProviderUnavailableError("invalid base url", code="invalid_base_url")
        try:
            with resp as r:
                raw = r.read()
        except (socket.timeout, TimeoutError):
            raise ProviderTimeoutError("provider read timed out", code="request_timeout")
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, AttributeError, UnicodeDecodeError):
            raise ProviderError("unparseable provider body", code="provider_bad_response")

    def _classify_http(self, code: int):
        if code == 404:
            return ProviderUnavailableError("model missing", code="model_missing")
        if code == 503:
            return ProviderUnavailableError("service unavailable", code="service_unavailable")
        return ProviderError("provider http error", code="provider_http_error")

    def _classify_urlerror(self, exc: "urllib.error.URLError"):
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, (socket.timeout, TimeoutError)):
            return ProviderTimeoutError("provider timed out", code="request_timeout")
        if isinstance(reason, socket.gaierror):
            return ProviderUnavailableError("dns failure", code="dns_failure")
        text = str(reason).lower()
        if "refused" in text:
            return ProviderUnavailableError("connection refused", code="connection_refused")
        if "timed out" in text:
            return ProviderTimeoutError("provider timed out", code="request_timeout")
        return ProviderUnavailableError("provider unreachable", code="unreachable")
