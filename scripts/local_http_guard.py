"""Shared write guard for the repo's local HTTP servers (D-022).

Every local server that accepts planning writes (the Teacher Workstation and
the older phase-22, phase-23, and phase-26 workstations) runs these checks
before any route logic:

- every request: a loopback ``Host`` for the server's own port
  (``127.0.0.1:<port>`` or ``localhost:<port>``)
- every mutating request (POST, PUT, PATCH, DELETE):
  - same origin: ``Origin`` (or ``Referer`` when there is no Origin) is the
    server's own ``http://<host>``
  - the per-start random request token in the server's token header
  - ``Content-Type: application/json``
  - a ``Content-Length`` body of at most 1 MB (413 above that); any
    ``Transfer-Encoding`` is refused (411)

The token reaches the page through a placeholder that ``inject_token``
replaces when the page is served, so only pages served by this server start
can make writes.

Usage inside a ``BaseHTTPRequestHandler`` whose server has
``request_token = new_token()``:

    def do_POST(self):
        if not local_http_guard.guard(self, "POST", token_header=TOKEN_HEADER):
            return
        ...
"""
from __future__ import annotations

import hmac
import json
import secrets
from http.server import BaseHTTPRequestHandler

MAX_BODY_BYTES = 1024 * 1024
MUTATING_METHODS = ("POST", "PUT", "PATCH", "DELETE")


class GuardRejected(Exception):
    """A request failed a route-protection check before any route logic ran."""

    def __init__(self, status: int, error: str) -> None:
        super().__init__(error)
        self.status = status
        self.error = error


def new_token() -> str:
    """A fresh random request token for one server start."""
    return secrets.token_urlsafe(32)


def inject_token(body: bytes, placeholder: str, token: str) -> bytes:
    """Put this server start's token into a served page."""
    return body.replace(placeholder.encode("ascii"), token.encode("ascii"))


def allowed_hosts(handler: BaseHTTPRequestHandler) -> tuple[str, ...]:
    port = handler.server.server_address[1]
    return (f"127.0.0.1:{port}", f"localhost:{port}")


def check_host(handler: BaseHTTPRequestHandler) -> str:
    host = (handler.headers.get("Host") or "").strip().lower()
    if host not in allowed_hosts(handler):
        raise GuardRejected(403, "HOST_REJECTED")
    return host


def check_mutation(handler: BaseHTTPRequestHandler, host: str, *, token_header: str) -> None:
    own_origin = f"http://{host}"
    origin = handler.headers.get("Origin")
    if origin is not None:
        if origin.strip().lower() != own_origin:
            raise GuardRejected(403, "ORIGIN_REJECTED")
    else:
        referer = (handler.headers.get("Referer") or "").strip().lower()
        if not (referer == own_origin or referer.startswith(own_origin + "/")):
            raise GuardRejected(403, "ORIGIN_REJECTED")

    token = handler.headers.get(token_header) or ""
    if not hmac.compare_digest(token.encode("utf-8"),
                               handler.server.request_token.encode("ascii")):
        raise GuardRejected(403, "TOKEN_REJECTED")

    ctype = (handler.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
    if ctype != "application/json":
        raise GuardRejected(415, "CONTENT_TYPE_REJECTED")

    if handler.headers.get("Transfer-Encoding"):
        raise GuardRejected(411, "LENGTH_REQUIRED")
    raw_length = handler.headers.get("Content-Length") or "0"
    try:
        length = int(raw_length)
    except ValueError:
        raise GuardRejected(400, "BAD_CONTENT_LENGTH") from None
    if length < 0:
        raise GuardRejected(400, "BAD_CONTENT_LENGTH")
    if length > MAX_BODY_BYTES:
        raise GuardRejected(413, "BODY_TOO_LARGE")


def send_rejection(handler: BaseHTTPRequestHandler, exc: GuardRejected) -> None:
    body = json.dumps({"error": exc.error}, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(exc.status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def guard(handler: BaseHTTPRequestHandler, method: str, *, token_header: str) -> bool:
    """Run the route-protection checks. Returns False (response sent) if rejected."""
    try:
        host = check_host(handler)
        if method in MUTATING_METHODS:
            check_mutation(handler, host, token_header=token_header)
    except GuardRejected as exc:
        # The unread body (if any) must not be parsed as a next request.
        handler.close_connection = True
        send_rejection(handler, exc)
        return False
    return True
