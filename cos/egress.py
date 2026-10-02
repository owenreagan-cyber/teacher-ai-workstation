"""Network egress allowlist for HTTP requests made by cos's own Python code.

Scope: this module governs HTTP that cos itself makes. Every such request goes
through request(), and a test enforces that no other cos module imports a
networking library. It is not an OS firewall: it cannot see traffic from
subprocesses. The subprocess boundary is covered separately:
  - mac.status runs fixed system binaries (pmset, memory_pressure, df, sysctl)
    that do not use the network;
  - the EventKit helper is cos's own code and makes no network calls;
  - each wrapped bin/chief-of-staff status command is statically checked at
    registration (cos/tools/script_contract.py) and is disabled if its script
    tree invokes a network-capable or mutating command.

Allowed destinations (scheme, host, port) are fixed in code:
  - local Ollama on 127.0.0.1 / localhost, port 11434, plain http
  - Open-Meteo forecast API over https
  - Brave Search API over https (web.search; the query is only ever text Owen typed)

Anything else raises EgressDenied before a socket is opened. Redirects are
refused (a 3xx could point elsewhere) and environment proxies are ignored.
Refusals are reported to the audit callback when one is given.
"""
from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request

ALLOWED = frozenset({
    ("http", "127.0.0.1", 11434),
    ("http", "localhost", 11434),
    ("https", "api.open-meteo.com", 443),
    ("https", "api.search.brave.com", 443),
})
MAX_RESPONSE_BYTES = 2_000_000
DEFAULT_PORTS = {"http": 80, "https": 443}


class EgressDenied(Exception):
    pass


class EgressError(Exception):
    """An allowed request that failed (network error or HTTP error status)."""

    def __init__(self, message, status=None, body=b""):
        super().__init__(message)
        self.status = status
        self.body = body


def check_url(url: str) -> tuple[str, str, int]:
    try:
        parts = urllib.parse.urlsplit(url)
        port = parts.port
    except ValueError as e:
        raise EgressDenied(f"unparseable url ({e})")
    scheme = (parts.scheme or "").lower()
    host = parts.hostname or ""
    if parts.username is not None or parts.password is not None:
        raise EgressDenied("credentials in url are not allowed")
    if port is None:
        port = DEFAULT_PORTS.get(scheme, -1)
    dest = (scheme, host, port)
    if dest not in ALLOWED:
        raise EgressDenied(f"destination not on allowlist: {scheme}://{host}:{port}")
    return dest


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EgressDenied(f"redirect refused ({code})")


def _opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())


def request(method: str, url: str, *, body: bytes | None = None, headers: dict | None = None,
            timeout: float = 30, audit=None, opener_factory=_opener) -> bytes:
    """Make one allowlisted HTTP request and return the response body."""
    try:
        dest = check_url(url)
    except EgressDenied as e:
        if audit is not None:
            audit("egress_denied", url_host=_host_only(url), reason=str(e))
        raise
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with opener_factory().open(req, timeout=timeout) as resp:
            data = resp.read(MAX_RESPONSE_BYTES + 1)
    except EgressDenied as e:
        if audit is not None:
            audit("egress_denied", url_host=dest[1], reason=str(e))
        raise
    except urllib.error.HTTPError as e:
        raise EgressError(f"HTTP {e.code} from {dest[1]}", status=e.code, body=e.read(4096))
    except (urllib.error.URLError, OSError) as e:
        raise EgressError(f"request to {dest[1]} failed: {e}")
    if len(data) > MAX_RESPONSE_BYTES:
        raise EgressError(f"response from {dest[1]} exceeds {MAX_RESPONSE_BYTES} bytes")
    return data


def _host_only(url: str) -> str:
    try:
        return urllib.parse.urlsplit(url).hostname or "?"
    except ValueError:
        return "?"
