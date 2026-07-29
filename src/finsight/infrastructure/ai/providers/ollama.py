# Implements: Phase 4C.6 — OllamaProvider: the real AiProviderPort transport adapter (infrastructure).
#
# It ONLY: reports ProviderStatus, serializes a PromptRequest, performs the HTTP call, parses the
# transport ENVELOPE, returns RawProviderResponse, and maps transport/provider failures to the
# existing typed provider errors. It NEVER validates the answer JSON (that is ResponseValidator),
# verifies citations, retries, builds prompts, persists, logs prompt/response content, imports
# AskFinService/UI/repositories, or reinterprets financial facts. This is the ONLY module that imports
# urllib.
from __future__ import annotations
import ipaddress
import json
import shutil
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Optional

from finsight.application.ai.contracts import PromptRequest, ProviderStatus, RawProviderResponse
from finsight.application.ai.private_contracts import (
    LocalAiSetupState,
    LocalAiSetupStatus,
)
from finsight.application.ai.errors import (
    ProviderError, ProviderTimeoutError, ProviderUnavailableError,
)
from finsight.diagnostics import get_logger
from finsight.domain.ai.contracts import ProviderConfiguration
from finsight.domain.ai.local_endpoint import (
    is_cloud_style_model_alias,
    normalized_loopback_http_url,
)

_log = get_logger("ai.provider.ollama")


def _default_opener(req, timeout):
    return urllib.request.urlopen(req, timeout=timeout)   # pragma: no cover - real network seam


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Keep private financial prompts on the configured local endpoint."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _redirect_rejecting_opener(req, timeout):
    # An explicit empty ProxyHandler is important: build_opener otherwise
    # inherits HTTP(S)_PROXY and platform proxy settings.  Private financial
    # prompts must connect directly to the validated loopback endpoint.
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        _RejectRedirects(),
    )
    return opener.open(req, timeout=timeout)


_PRIVATE_PATHS = frozenset({"/api/tags", "/api/show", "/api/chat"})
_LOCAL_PROFILE_ID = "stage2-local-ollama-gguf-v1"


def _normalized_sha256_digest(value: object) -> str:
    digest = str(value or "").strip().casefold()
    if len(digest) == 64 and all(
        character in "0123456789abcdef" for character in digest
    ):
        return f"sha256:{digest}"
    return digest


def _is_sha256_digest(value: str) -> bool:
    return (
        value.startswith("sha256:")
        and len(value) == 71
        and all(
            character in "0123456789abcdef"
            for character in value.removeprefix("sha256:")
        )
    )


def _loopback_address(value: object) -> bool:
    try:
        return ipaddress.ip_address(str(value).split("%", 1)[0]).is_loopback
    except ValueError:
        return False


def _extract_peer_address(response) -> Optional[str]:
    """Best-effort extraction across urllib/http.client response wrappers."""

    direct = getattr(response, "peer_address", None)
    if callable(direct):
        direct = direct()
    if isinstance(direct, (tuple, list)) and direct:
        return str(direct[0])
    if isinstance(direct, str):
        return direct

    current = response
    for path in (
        ("fp", "raw", "_sock"),
        ("fp", "raw", "_connection", "sock"),
        ("_fp", "fp", "raw", "_sock"),
    ):
        current = response
        try:
            for name in path:
                current = getattr(current, name)
            peer = current.getpeername()
        except (AttributeError, OSError, TypeError):
            continue
        if isinstance(peer, (tuple, list)) and peer:
            return str(peer[0])
    return None


def _close_quietly(response) -> None:
    try:
        response.close()
    except (AttributeError, OSError):
        pass


class OllamaProvider:
    """AiProviderPort adapter for a local/remote Ollama server. `enabled` reflects whether provider
    selection chose ollama; when False the adapter reports provider_disabled and never calls out. The
    HTTP `opener` is injected so tests perform no network I/O."""

    def __init__(
        self,
        config: ProviderConfiguration,
        *,
        status_timeout: float,
        enabled: bool = True,
        opener=None,
        forbid_redirects: bool = False,
        private_local: bool = False,
        approved_model_digest: str = "",
        approved_model_profile_id: str = "",
        resolver: Optional[Callable] = None,
    ):
        self._config = config
        self._status_timeout = status_timeout
        self._enabled = enabled
        self._private_local = private_local
        # A deployment may supply a managed digest pin. Normal desktop use
        # deliberately leaves it empty: the provider then pins the exact
        # digest it observes from the verified loopback service for this
        # provider instance. Either path is rechecked immediately before a
        # prompt is sent.
        self._approved_model_digest = _normalized_sha256_digest(
            approved_model_digest
        )
        self._approved_model_profile_id = approved_model_profile_id
        self._resolver = resolver or socket.getaddrinfo
        self._verified_model_digest = ""
        self._opener = opener or (
            _redirect_rejecting_opener if forbid_redirects else _default_opener
        )
        if self._private_local:
            # Constructor validation prevents a later request from widening the
            # transport target through a mutable or request-supplied URL.
            normalized = normalized_loopback_http_url(config.base_url)
            if normalized != config.base_url.rstrip("/"):
                raise ValueError("private Ollama endpoint is not normalized loopback HTTP")
            # Private mode always disables redirects and environment/system
            # proxies.  A supplied opener is a test seam; the same address and
            # peer checks still wrap every request it returns.
            if opener is None:
                self._opener = _redirect_rejecting_opener

    # -------- AiProviderPort --------
    def available(self) -> bool:
        return True                                   # the adapter object is constructable/callable

    def status(self) -> ProviderStatus:
        if not self._enabled:
            return ProviderStatus(operational=True, generation_available=False,
                                  reason="provider_disabled")
        if self._private_local:
            try:
                self._verify_approved_model_identity()
            except ProviderError as exc:
                return ProviderStatus(True, False, exc.code or "model_identity_unverified")
            return ProviderStatus(True, True, "ok")
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

    def setup_status(
        self, *, installation_available: Optional[bool] = None
    ) -> LocalAiSetupStatus:
        """Return a precise local-runtime status without sending review data.

        The probe reads only Ollama's model inventory. It never downloads,
        starts, or modifies software, and it retains the same loopback,
        no-proxy, no-redirect and peer-verification controls as generation.
        """

        installed = (
            shutil.which("ollama") is not None
            if installation_available is None
            else bool(installation_available)
        )
        base = {
            "endpoint": self._config.base_url,
            "model": self._config.model,
        }
        try:
            tags = self._request(
                "GET", "/api/tags", None, self._status_timeout
            )
        except ProviderTimeoutError:
            return LocalAiSetupStatus(
                state=LocalAiSetupState.TIMEOUT,
                message="The local Ollama service did not respond in time.",
                **base,
            )
        except ProviderUnavailableError as exc:
            if exc.code == "connection_refused":
                state = (
                    LocalAiSetupState.SERVICE_NOT_RUNNING
                    if installed
                    else LocalAiSetupState.NOT_INSTALLED
                )
                message = (
                    "Ollama is installed, but its local service is not running."
                    if installed
                    else "Ollama is not installed on this computer."
                )
            else:
                state = LocalAiSetupState.CONNECTION_FAILURE
                message = (
                    "FinSight could not connect securely to the configured "
                    "local Ollama endpoint."
                )
            return LocalAiSetupStatus(state=state, message=message, **base)
        except ProviderError:
            return LocalAiSetupStatus(
                state=LocalAiSetupState.CONNECTION_FAILURE,
                message=(
                    "The local Ollama service returned an unreadable status "
                    "response."
                ),
                **base,
            )

        models = tags.get("models") if isinstance(tags, dict) else None
        if not isinstance(models, list):
            return LocalAiSetupStatus(
                state=LocalAiSetupState.CONNECTION_FAILURE,
                message=(
                    "The local Ollama service returned an unreadable model "
                    "inventory."
                ),
                **base,
            )
        inventory = tuple(
            sorted(
                {
                    str(item.get("name") or item.get("model") or "").strip()
                    for item in models
                    if isinstance(item, dict)
                    and str(
                        item.get("name") or item.get("model") or ""
                    ).strip()
                },
                key=str.casefold,
            )
        )
        selected = next(
            (
                item
                for item in models
                if isinstance(item, dict)
                and str(item.get("name") or item.get("model") or "").strip()
                == self._config.model
            ),
            None,
        )
        if selected is None:
            return LocalAiSetupStatus(
                state=LocalAiSetupState.MODEL_NOT_DOWNLOADED,
                message=(
                    f"The configured model {self._config.model} is not "
                    "downloaded in Ollama."
                ),
                available_models=inventory,
                **base,
            )
        observed_digest = _normalized_sha256_digest(selected.get("digest"))
        try:
            self._verify_approved_model_identity()
        except ProviderTimeoutError:
            return LocalAiSetupStatus(
                state=LocalAiSetupState.TIMEOUT,
                message=(
                    "The local model identity check did not respond in time."
                ),
                available_models=inventory,
                observed_model_digest=observed_digest,
                **base,
            )
        except ProviderUnavailableError as exc:
            if exc.code == "model_missing":
                state = LocalAiSetupState.MODEL_NOT_DOWNLOADED
                message = (
                    f"The configured model {self._config.model} is not "
                    "downloaded in Ollama."
                )
            else:
                state = LocalAiSetupState.MODEL_VERIFICATION_FAILED
                message = (
                    "FinSight could not verify the installed local model."
                )
            return LocalAiSetupStatus(
                state=state,
                message=message,
                available_models=inventory,
                observed_model_digest=observed_digest,
                **base,
            )
        except ProviderError:
            return LocalAiSetupStatus(
                state=LocalAiSetupState.CONNECTION_FAILURE,
                message=(
                    "FinSight could not verify the local model response."
                ),
                available_models=inventory,
                observed_model_digest=observed_digest,
                **base,
            )
        return LocalAiSetupStatus(
            state=LocalAiSetupState.HEALTHY,
            message="Ask Fin is ready and using a verified local model.",
            available_models=inventory,
            observed_model_digest=self._verified_model_digest,
            **base,
        )

    def generate(self, request: PromptRequest, config: ProviderConfiguration) -> RawProviderResponse:
        if not self._enabled:
            raise ProviderUnavailableError("ollama provider is disabled", code="provider_disabled")
        if self._private_local:
            # Re-check immediately before the prompt-bearing request.  The
            # earlier status call is UX information, not an authorization
            # token, and cannot protect against a swapped local model.
            self._verify_approved_model_identity()
        payload = self._build_payload(request, config)
        body = self._request("POST", "/api/chat", payload, config.request_timeout_seconds)
        return self._map_response(body, config)

    def _verify_approved_model_identity(self) -> None:
        if is_cloud_style_model_alias(self._config.model):
            raise ProviderUnavailableError(
                "cloud-style model aliases are not approved",
                code="model_alias_blocked",
            )
        if self._approved_model_profile_id != _LOCAL_PROFILE_ID:
            raise ProviderUnavailableError(
                "local model profile is not approved",
                code="model_profile_unapproved",
            )

        tags = self._request("GET", "/api/tags", None, self._status_timeout)
        models = tags.get("models") if isinstance(tags, dict) else None
        if not isinstance(models, list):
            raise ProviderError(
                "malformed model inventory",
                code="malformed_status_response",
            )
        installed = next(
            (
                item
                for item in models
                if isinstance(item, dict)
                and (item.get("name") or item.get("model")) == self._config.model
            ),
            None,
        )
        if installed is None:
            raise ProviderUnavailableError(
                "selected local model is not installed",
                code="model_missing",
            )
        observed_digest = _normalized_sha256_digest(installed.get("digest"))
        if not _is_sha256_digest(observed_digest):
            raise ProviderUnavailableError(
                "installed model does not expose a verifiable SHA-256 digest",
                code="model_digest_unverifiable",
            )
        expected_digest = (
            self._approved_model_digest or self._verified_model_digest
        )
        if expected_digest and observed_digest != expected_digest:
            raise ProviderUnavailableError(
                "installed model digest does not match the configured or "
                "automatically pinned local identity",
                code="model_digest_mismatch",
            )

        show = self._request(
            "POST",
            "/api/show",
            {"model": self._config.model, "verbose": False},
            self._status_timeout,
        )
        if not self._matches_local_profile(show):
            raise ProviderUnavailableError(
                "installed model metadata does not match the approved profile",
                code="model_profile_mismatch",
            )
        self._verified_model_digest = observed_digest

    def _matches_local_profile(self, body: object) -> bool:
        if not isinstance(body, dict):
            return False
        details = body.get("details")
        model_info = body.get("model_info")
        capabilities = body.get("capabilities")
        if (
            not isinstance(details, dict)
            or not isinstance(model_info, dict)
            or not isinstance(capabilities, list)
        ):
            return False
        if str(details.get("format") or "").casefold() != "gguf":
            return False
        family = str(details.get("family") or "").strip().casefold()
        architecture = str(
            model_info.get("general.architecture") or ""
        ).strip().casefold()
        if not family or not architecture or family != architecture:
            return False
        normalized_capabilities = {
            str(item).strip().casefold() for item in capabilities
        }
        if "completion" not in normalized_capabilities:
            return False

        # Cloud-capable aliases and explicit remote-provider identity fields
        # are not part of the approved local GGUF profile.  License/homepage
        # fields are intentionally ignored because local model metadata may
        # legitimately contain public documentation URLs.
        for key in ("model", "name", "provider", "remote_model", "remote_host"):
            value = body.get(key)
            if value and (
                key in {"provider", "remote_model", "remote_host"}
                or is_cloud_style_model_alias(str(value))
            ):
                return False
        return True

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
        response_model = body.get("model") or config.model
        if self._private_local and response_model != config.model:
            raise ProviderUnavailableError(
                "response came from an unapproved model",
                code="model_response_mismatch",
            )
        metadata = {"done_reason": body.get("done_reason"), "eval_count": body.get("eval_count")}
        if self._private_local:
            metadata.update(
                {
                    "model_version": self._verified_model_digest,
                    "model_digest": self._verified_model_digest,
                    "model_profile_id": self._approved_model_profile_id,
                }
            )
        duration = body.get("total_duration")
        if isinstance(duration, (int, float)) and not isinstance(duration, bool):
            metadata["latency_ms"] = duration / 1_000_000.0   # Ollama reports nanoseconds
        return RawProviderResponse(
            text=message["content"],
            provider="ollama",
            model=response_model,
            metadata=metadata,
        )

    # -------- transport (urllib), returns parsed envelope or raises a typed provider error --------
    def _request(self, method: str, path: str, payload, timeout):
        if self._private_local:
            if path not in _PRIVATE_PATHS:
                raise ProviderUnavailableError(
                    "private Ollama path is not approved",
                    code="path_not_allowed",
                )
            self._require_resolved_loopback()
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
        if self._private_local:
            peer = _extract_peer_address(resp)
            if peer is None or not _loopback_address(peer):
                _close_quietly(resp)
                raise ProviderUnavailableError(
                    "connected peer is not verified loopback",
                    code="peer_not_loopback",
                )
        try:
            with resp as r:
                raw = r.read()
        except (socket.timeout, TimeoutError):
            raise ProviderTimeoutError("provider read timed out", code="request_timeout")
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, AttributeError, UnicodeDecodeError):
            raise ProviderError("unparseable provider body", code="provider_bad_response")

    def _require_resolved_loopback(self) -> None:
        parsed = urllib.parse.urlsplit(self._config.base_url)
        host = parsed.hostname
        port = parsed.port
        if not host or port is None:
            raise ProviderUnavailableError(
                "private Ollama endpoint is invalid",
                code="invalid_base_url",
            )
        try:
            addresses = self._resolver(
                host,
                port,
                type=socket.SOCK_STREAM,
            )
        except (OSError, TypeError):
            raise ProviderUnavailableError(
                "local endpoint resolution failed",
                code="loopback_resolution_failed",
            )
        resolved = {
            str(item[4][0])
            for item in addresses
            if len(item) >= 5 and item[4]
        }
        if not resolved or any(not _loopback_address(item) for item in resolved):
            raise ProviderUnavailableError(
                "local endpoint resolved outside loopback",
                code="non_loopback_resolution",
            )

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
