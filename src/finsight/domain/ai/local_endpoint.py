"""Pure validation for the private local-model endpoint."""
from __future__ import annotations

import ipaddress
import re


_LOOPBACK_HTTP_ENDPOINT = re.compile(
    r"http://(?P<host>\[[0-9A-Fa-f:.]+\]|[^/:?#\s]+):"
    r"(?P<port>[0-9]{1,5})/?\Z"
)
_CLOUD_STYLE_MODEL_ALIAS = re.compile(
    r"(?:"
    r"://|"
    r"(?:^|[:/@._-])(?:cloud|remote|hosted|online)(?:$|[:/@._-])|"
    r"(?:^|[:/@._-])(?:openai|anthropic|azure|bedrock|vertex|gemini)"
    r"(?:$|[:/@._-])"
    r")",
    re.IGNORECASE,
)


def normalized_loopback_http_url(value: str) -> str:
    """Return a normalized URL only for an explicit loopback HTTP endpoint."""

    if not isinstance(value, str):
        raise ValueError("The local-model endpoint must be text.")
    match = _LOOPBACK_HTTP_ENDPOINT.fullmatch(value.strip())
    if match is None:
        raise ValueError("The local-model endpoint must be loopback HTTP with a port.")
    host = match.group("host").strip("[]")
    port = int(match.group("port"))
    if not 1 <= port <= 65_535:
        raise ValueError("The local-model endpoint port is invalid.")
    normalized_host = host.casefold()
    local = normalized_host == "localhost"
    if not local:
        try:
            address = ipaddress.ip_address(host)
            local = address in {
                ipaddress.ip_address("127.0.0.1"),
                ipaddress.ip_address("::1"),
            }
        except ValueError:
            local = False
    if not local:
        raise ValueError("The local-model endpoint must use a loopback host.")
    display_host = f"[{host}]" if ":" in host else host
    return f"http://{display_host}:{port}"


def is_cloud_style_model_alias(value: str) -> bool:
    """Return whether a model identifier advertises a remote/cloud target.

    A pinned digest remains the primary identity control.  This conservative
    lexical guard prevents an Ollama cloud alias from entering the approved
    local profile in the first place.
    """

    if not isinstance(value, str) or not value.strip():
        return True
    return _CLOUD_STYLE_MODEL_ALIAS.search(value.strip()) is not None
