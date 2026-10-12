"""Gmail REST API transport for the Grade Check teacher report + OAuth helper.

PRIMARY send path. Uses the Gmail REST API over ``urllib`` (stdlib only — no
third-party google-api-python-client dependency) with OAuth 2.0. OAuth client
credentials and refresh-token storage live in a gitignored, 0600 private config
directory (never in the repo, never in chat).

Safety invariants (must be preserved, not re-ordered):
- NEVER send to parents/guardians/students/any recipient other than Owen.
- NEVER print client secrets, auth codes, access tokens, refresh tokens, or
  token contents.
- Only an allowlisted sender/recipient passes the Grade Check gate.
- Only the account ``oreagan81@gmail.com`` may be authorized; any other account
  fails closed with ``OAUTH ACCOUNT SAFETY BLOCK``.
- Gmail data access is limited to ``gmail.send`` only. Identity verification
  uses the OpenID Connect ``id_token`` (identity scopes only) — it never calls a
  Gmail profile/read endpoint, so no broader Gmail scope is added just to verify
  identity. ``openid``/``email``/``profile`` are non-Gmail identity scopes.

The Gmail API is used as an *outbound message send* transport only
(``users.messages.send``). No mailbox read, no draft management, no label
mutation.
"""
from __future__ import annotations

import base64
import http.server
import json
import os
import socket
import stat
import socketserver
import threading
import uuid
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import urllib.request
import urllib.error
import urllib.parse

REPO_ROOT = Path(__file__).resolve().parents[2]

# Gitignored private OAuth storage. Keep outside the working tree by default.
CONFIG_DIR = Path.home() / ".config" / "teacher-ai-workstation" / "grade-check-oauth"
CLIENT_CREDS_FILE = CONFIG_DIR / "client_secret.json"
TOKEN_FILE = CONFIG_DIR / "token.json"
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"

# Gmail data access is intentionally limited to send-only.
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
# Identity scopes (OIDC) are NOT Gmail data-access scopes. Google may echo these
# back either in short form or in their canonical URI form (userinfo.email /
# userinfo.profile) in the token response `scope` field. Both must be allowed.
IDENTITY_SCOPES = frozenset({
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo",
    "https://www.googleapis.com/auth/plus.profile",
    "https://www.googleapis.com/auth/plus.me",
})
SCOPES = "openid email profile " + GMAIL_SEND_SCOPE

# The ONLY account allowed to authorize.
ALLOWED_ACCOUNT = "oreagan81@gmail.com"

# Non-secret relative config path in the private dir (for messages).
CONFIG_DIR_REL = "~/.config/teacher-ai-workstation/grade-check-oauth"

# Test hook: override the storage directory (kept out of the public path).
_config_dir: Path = CONFIG_DIR


class GmailTransportError(RuntimeError):
    """Raised when the Gmail API send fails. Carries a non-secret reason."""


class OAuthAccountBlocked(RuntimeError):
    """Raised when an account other than oreagan81@gmail.com is authorized."""


@dataclass
class GmailSendResult:
    sent: bool
    message_id: str | None = None
    reason: str | None = None


# ---------------------------------------------------------------------------
# Path helpers (overridable for deterministic tests)
# ---------------------------------------------------------------------------
def set_config_dir(path: Path | str) -> None:
    """Override the OAuth storage dir (tests only)."""
    global _config_dir
    _config_dir = Path(path)


def client_creds_file() -> Path:
    return _config_dir / "client_secret.json"


def token_file() -> Path:
    return _config_dir / "token.json"


def _redact(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}...{value[-2:]}"


def file_mode_is_600(path: Path) -> bool:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        return False
    return mode == 0o600


def oauth_ready() -> bool:
    """True only when both client credentials and a refresh token are present."""
    return client_creds_file().exists() and token_file().exists()


# ---------------------------------------------------------------------------
# Scope / identity helpers
# ---------------------------------------------------------------------------
def _granted_scope_set(token: dict[str, Any]) -> set[str]:
    granted = token.get("scope", "")
    return {s.strip() for s in str(granted).split() if s.strip()}


def _scope_has_gmail_send(scopes: set[str]) -> bool:
    return GMAIL_SEND_SCOPE in scopes


def _scope_is_gmail_send_only(scopes: set[str]) -> bool:
    """True when the granted set is ``gmail.send`` plus OIDC identity scopes.

    Requires exactly ``gmail.send`` as the only Gmail data/action scope; allows
    identity scopes (openid/email/profile, short or canonical URI form); rejects
    any other Gmail API data scope (gmail.readonly, gmail.modify, mail.google.com,
    gmail.compose, gmail.insert, any other auth/gmail.*).
    """
    if GMAIL_SEND_SCOPE not in scopes:
        return False
    for s in scopes:
        if s in IDENTITY_SCOPES:
            continue
        if s == GMAIL_SEND_SCOPE:
            continue
        # Any other scope is not an identity scope and not gmail.send. Reject
        # anything that is (or could be) a Gmail data scope, and any unknown
        # scope, to avoid broadening Gmail access.
        return False
    return True


def _identity_is_allowed(email: str | None) -> bool:
    return (email or "").strip().lower() == ALLOWED_ACCOUNT


def validate_token_metadata(token: dict[str, Any]) -> str | None:
    """Return a fail-closed reason, or None if the token metadata is safe.

    Checks (in order): authorized identity is oreagan81@gmail.com, gmail.send is
    present, and Gmail data access is send-only (no broader Gmail scope).
    """
    email = token.get("email")
    if not _identity_is_allowed(email):
        return "OAUTH ACCOUNT SAFETY BLOCK: authorized account is not " \
               f"{ALLOWED_ACCOUNT}"
    scopes = _granted_scope_set(token)
    if not _scope_has_gmail_send(scopes):
        return "OAUTH SCOPE SAFETY BLOCK: gmail.send scope not present"
    if not _scope_is_gmail_send_only(scopes):
        return "OAUTH SCOPE SAFETY BLOCK: Gmail data scope beyond gmail.send"
    return None


# ---------------------------------------------------------------------------
# Client credential reading
# ---------------------------------------------------------------------------
def _client_info() -> dict[str, str]:
    """Return client_id, client_secret, auth_uri, token_uri, redirect_uris."""
    path = client_creds_file()
    if not path.exists():
        raise GmailTransportError("Gmail OAuth client credentials missing; local setup required")
    data = json.loads(path.read_text(encoding="utf-8"))
    section = data.get("installed") or data.get("web") or {}
    client_id = section.get("client_id") or ""
    client_secret = section.get("client_secret") or ""
    tok_uri = section.get("token_uri") or TOKEN_URI
    auth_uri = section.get("auth_uri") or AUTH_URI
    if not client_id or not client_secret:
        raise GmailTransportError("Gmail OAuth client credentials incomplete; local setup required")
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": auth_uri,
        "token_uri": tok_uri,
        "redirect_uris": section.get("redirect_uris") or [],
    }


def _load_token() -> dict[str, Any]:
    if not token_file().exists():
        raise GmailTransportError("Gmail OAuth refresh token missing; local setup required")
    token = json.loads(token_file().read_text(encoding="utf-8"))
    if not token.get("refresh_token"):
        raise GmailTransportError("Gmail OAuth token has no refresh_token; local setup required")
    return token


# ---------------------------------------------------------------------------
# Network primitives (POST / GET)
# ---------------------------------------------------------------------------
def _post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = (exc.read() or b"").decode("utf-8", "replace")[:300]
        except Exception:  # noqa: BLE001
            detail = ""
        raise GmailTransportError(f"Gmail OAuth HTTP {exc.code}: {detail or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise GmailTransportError(f"Gmail OAuth network: {exc.reason}") from exc


def get_access_token_from_refresh(client: dict[str, str], token: dict[str, Any]) -> str:
    """Exchange the stored refresh token for a fresh access token."""
    resp = _post_form(
        client["token_uri"],
        {
            "grant_type": "refresh_token",
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "refresh_token": token["refresh_token"],
            "scope": SCOPES,
        },
    )
    access_token = resp.get("access_token")
    if not access_token:
        raise GmailTransportError("Gmail OAuth refresh failed: no access_token returned")
    return access_token


def _get_access_token() -> str:
    client = _client_info()
    token = _load_token()
    return get_access_token_from_refresh(client, token)


# ---------------------------------------------------------------------------
# Identity verification via the OIDC id_token (no Gmail read scope needed)
# ---------------------------------------------------------------------------
def decode_id_token_email(id_token: str) -> str | None:
    """Read the ``email`` claim from a JWT id_token payload. Never verifies
    the signature here (the token came directly from Google over TLS); it only
    extracts the identity claim. Returns None if not parseable."""
    if not id_token:
        return None
    parts = id_token.split(".")
    if len(parts) < 2:
        return None
    # Re-pad the base64url segment before decoding.
    padded = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None
    return payload.get("email")


def extract_identity_from_token_response(resp: dict[str, Any]) -> str | None:
    """Derive the authenticated account email from the token response id_token.

    Requires the OIDC identity scopes (openid/email/profile) which are non-Gmail
    identity scopes. Returns None if no id_token or no email claim is present.
    """
    return decode_id_token_email(resp.get("id_token", ""))


# ---------------------------------------------------------------------------
# Localhost OAuth callback listener (replaces the deprecated OOB flow)
# ---------------------------------------------------------------------------
class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    server_version = "grade-check-oauth"

    def do_GET(self):  # noqa: N802
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        self.server.received = {
            "code": (params.get("code") or [None])[0],
            "state": (params.get("state") or [None])[0],
            "error": (params.get("error") or [None])[0],
        }
        body = (
            b"<html><body><h2>Authorization received.</h2>"
            b"<p>You can close this window and return to the terminal.</p>"
            b"</body></html>"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # noqa: D401
        pass


def start_callback_listener() -> tuple[object, int]:
    """Start a local HTTP listener on 127.0.0.1 with an ephemeral port.

    Returns ``(server, port)``. ``server.received`` will be populated once the
    browser returns the authorization response.
    """
    server = ReusableTCPServer(("127.0.0.1", 0), _CallbackHandler)
    server.received = None
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = int(server.server_address[1])
    return server, port


def stop_callback_listener(server: object) -> None:
    try:
        server.shutdown()
        server.server_close()
    except Exception:  # noqa: BLE001
        pass


def build_redirect_uri(client: dict[str, str], port: int) -> str:
    """Pick the localhost redirect URI.

    Prefers a client-configured ``http://localhost`` style redirect URI when it
    is present; otherwise constructs ``http://localhost:{port}/`` from the
    listener's ephemeral port.

    A configured ``http://localhost`` (no port) is normalized to include the
    ephemeral port so it matches the local callback listener, e.g.
    ``http://localhost`` -> ``http://localhost:{port}/``.
    """
    uris = client.get("redirect_uris") or []
    for u in uris:
        if "localhost" not in u:
            continue
        # Strip any trailing slash, then rebuild cleanly.
        base = u.rstrip("/")
        # If no explicit port, append the listener's ephemeral port.
        parsed = urllib.parse.urlparse(base)
        if not parsed.port:
            return f"http://localhost:{port}/"
        return base + "/"
    return f"http://localhost:{port}/"


def build_authorize_url(client: dict[str, str], redirect_uri: str, state: str) -> str:
    """Build the Google consent URL. No secrets in the URL; scopes send-only."""
    params = {
        "client_id": client["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{client['auth_uri']}?{urllib.parse.urlencode(params)}"


def exchange_authorization_code(
    client: dict[str, str], code: str, redirect_uri: str
) -> dict[str, Any]:
    """Exchange the one-time auth code for a token. ``code`` is never printed."""
    resp = _post_form(
        client["token_uri"],
        {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": redirect_uri,
            "scope": SCOPES,
        },
    )
    if not resp.get("refresh_token"):
        raise GmailTransportError("Gmail OAuth exchange returned no refresh_token")
    return resp


def _write_token(token: dict[str, Any]) -> None:
    path = token_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(token, indent=2, sort_keys=True), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def obtain_authorization_code(
    *,
    client: dict[str, str],
    print_fn=print,
    open_url=None,
    timeout: int = 120,
) -> tuple[str, str]:
    """Open the consent URL and wait for the localhost callback.

    Returns ``(code, state)``. The listener is started, the URL is opened (and
    printed for manual use), and the browser callback is captured before the
    listener is shut down. No paste-required OOB flow.
    """
    server, port = start_callback_listener()
    redirect_uri = build_redirect_uri(client, port)
    state = uuid.uuid4().hex
    url = build_authorize_url(client, redirect_uri, state)
    # Ensure the exchange step reuses the SAME redirect_uri used to obtain the code.
    client["__redirect_uri"] = redirect_uri

    print_fn("Authorizing oreagan81@gmail.com (gmail.send only)...")
    print_fn("Open this URL in your browser if it does not open automatically:")
    print_fn(url)
    if open_url is None:
        open_url = lambda u: webbrowser.open(u)  # noqa: E731
    try:
        open_url(url)
    except Exception:  # noqa: BLE001
        pass

    try:
        server.timeout = timeout
        deadline = timeout
        # Wait for the callback; poll server.received.
        import time as _time
        waited = 0
        while server.received is None and waited < deadline:
            _time.sleep(0.2)
            waited += 0.2
    except Exception:  # noqa: BLE001
        stop_callback_listener(server)
        raise GmailTransportError("Gmail OAuth callback listener failed")
    finally:
        stop_callback_listener(server)

    if server.received is None:
        raise GmailTransportError("Gmail OAuth callback timed out; no authorization received")
    if server.received.get("error"):
        raise GmailTransportError(
            f"Gmail OAuth authorization error: {server.received['error']}"
        )
    if server.received.get("state") != state:
        raise GmailTransportError("Gmail OAuth callback state mismatch")
    code = server.received.get("code")
    if not code:
        raise GmailTransportError("Gmail OAuth authorization returned no code")
    return code, state


def run_oauth_setup(
    *,
    print_fn=print,
    open_url=None,
    get_authorization_code=None,
    exchange_fn=exchange_authorization_code,
    identity_fn=extract_identity_from_token_response,
) -> int:
    """One-time interactive OAuth authorization for oreagan81@gmail.com.

    Returns 0 on success (token.json written, 0600), non-zero otherwise. Fails
    closed with OAUTH ACCOUNT SAFETY BLOCK if any other account is authorized.
    Never prints secrets, codes, access/refresh tokens, or token contents.

    Identity is verified from the OIDC ``id_token`` — no Gmail profile/read
    endpoint is called, and no Gmail scope beyond ``gmail.send`` is requested.
    """
    try:
        client = _client_info()
    except GmailTransportError as exc:
        print_fn(f"BLOCKER: {exc}")
        return 1

    if get_authorization_code is None:
        get_authorization_code = lambda **kw: obtain_authorization_code(**kw)  # noqa: E731

    try:
        code, state = get_authorization_code(client=client, print_fn=print_fn, open_url=open_url)
    except GmailTransportError as exc:
        print_fn(f"BLOCKER: {exc}")
        return 1
    if not code:
        print_fn("BLOCKER: no authorization code provided")
        return 1

    # Reuse the exact redirect_uri that was used to obtain the code.
    # obtain_authorization_code stores it on client["__redirect_uri"] so the
    # token exchange uses the same URI Google authorized.
    redirect_uri = client.get("__redirect_uri")

    try:
        token = exchange_fn(client, code, redirect_uri)
    except GmailTransportError as exc:
        print_fn(f"BLOCKER: {exc}")
        return 1

    # Verify the granted scope: gmail.send present and Gmail access send-only.
    scopes = _granted_scope_set(token)
    if not _scope_has_gmail_send(scopes):
        print_fn("OAUTH SCOPE SAFETY BLOCK: gmail.send scope not present")
        return 1
    if not _scope_is_gmail_send_only(scopes):
        print_fn("OAUTH SCOPE SAFETY BLOCK: Gmail data scope beyond gmail.send")
        return 1

    # Verify the authorized account from the OIDC id_token (no Gmail read scope).
    email = identity_fn(token)
    if not email:
        print_fn(
            "OAUTH ACCOUNT SAFETY BLOCK: identity cannot be proven from the "
            "OIDC id_token (missing email claim). Failing closed."
        )
        return 1
    if not _identity_is_allowed(email):
        print_fn("OAUTH ACCOUNT SAFETY BLOCK: authorized account is not "
                 f"{ALLOWED_ACCOUNT}")
        return 1

    # Persist token with verified metadata, 0600.
    token["email"] = email
    token["scope"] = SCOPES
    token["token_type"] = token.get("token_type", "Bearer")
    _write_token(token)
    print_fn("Token stored at: " + str(token_file()))
    return 0


def oauth_status() -> dict[str, Any]:
    """Read-only readiness report (no network, no send)."""
    client_present = client_creds_file().exists()
    tok_present = token_file().exists()
    perms_safe = file_mode_is_600(token_file()) if tok_present else False

    identity_ok: bool | None = None
    scope_ok: bool | None = None
    gmail_only_ok: bool | None = None
    reason: str | None = None
    if tok_present:
        try:
            token = json.loads(token_file().read_text(encoding="utf-8"))
            identity_ok = _identity_is_allowed(token.get("email"))
            scopes = _granted_scope_set(token)
            scope_ok = _scope_has_gmail_send(scopes)
            gmail_only_ok = _scope_is_gmail_send_only(scopes)
            reason = validate_token_metadata(token)
        except (json.JSONDecodeError, OSError):
            identity_ok = False
            scope_ok = False
            gmail_only_ok = False
            reason = "token file unreadable"

    ready = bool(
        client_present
        and tok_present
        and perms_safe
        and identity_ok is True
        and scope_ok is True
        and gmail_only_ok is True
        and reason is None
    )
    return {
        "client_credential_present": client_present,
        "token_present": tok_present,
        "token_permissions_safe": perms_safe,
        "authorized_sender_identity": identity_ok,
        "gmail_send_scope_present": scope_ok,
        "gmail_transport_ready": ready,
        "blocker": reason,
    }


def oauth_status_lines() -> list[str]:
    s = oauth_status()
    return [
        f"client credential present: {'YES' if s['client_credential_present'] else 'NO'}",
        f"token present: {'YES' if s['token_present'] else 'NO'}",
        f"token permissions safe: {'PASS' if s['token_permissions_safe'] else 'FAIL'}",
        f"authorized sender identity: "
        f"{'PASS' if s['authorized_sender_identity'] is True else 'FAIL'}",
        f"gmail.send scope present: "
        f"{'PASS' if s['gmail_send_scope_present'] is True else 'FAIL'}",
        f"Gmail transport ready: {'YES' if s['gmail_transport_ready'] else 'NO'}",
    ]


# ---------------------------------------------------------------------------
# Message building + send (unchanged: send-only, gmail.send)
# ---------------------------------------------------------------------------
def build_gmail_message(subject: str, body: str, sender: str, recipient: str) -> str:
    """Build a RFC-2822 raw message and return base64url-encoded form."""
    from email.message import EmailMessage
    from email.utils import formataddr

    msg = EmailMessage()
    msg["From"] = formataddr(("Owen Reagan", sender))
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)
    raw = msg.as_bytes()
    return base64.urlsafe_b64encode(raw).decode("ascii")


def send_via_gmail_api(subject: str, body: str, sender: str, recipient: str) -> GmailSendResult:
    """Send one message via users.messages.send with OAuth 2.0."""
    access_token = _get_access_token()
    raw_b64 = build_gmail_message(subject, body, sender, recipient)
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    payload = json.dumps({"raw": raw_b64}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = (exc.read() or b"").decode("utf-8", "replace")[:300]
        except Exception:  # noqa: BLE001
            detail = ""
        raise GmailTransportError(f"Gmail API send HTTP {exc.code}: {detail or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise GmailTransportError(f"Gmail API send network: {exc.reason}") from exc

    mid = result.get("id")
    return GmailSendResult(sent=True, message_id=mid)


def command_self_test() -> int:
    import tempfile
    import time

    # Message building
    raw = build_gmail_message("Test Subject", "Hello body", "oreagan81@gmail.com",
                              "owen.reagan@thalesacademy.org")
    decoded = base64.urlsafe_b64decode(raw.encode("ascii") + b"==").decode("utf-8")
    assert "To: owen.reagan@thalesacademy.org" in decoded
    assert "Subject: Test Subject" in decoded
    assert "Hello body" in decoded

    # Redaction never reveals full values.
    assert _redact("abcdefghijkl") == "ab...kl"

    # No OOB redirect anywhere.
    client = {"auth_uri": AUTH_URI, "client_id": "c", "redirect_uris": ["http://localhost:8080/"]}
    url = build_authorize_url(client, "http://localhost:8080/", "abc123")
    assert "urn:ietf:wg:oauth:2.0:oob" not in url
    # Parse the query and assert the redirect_uri + state params.
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert q["redirect_uri"] == ["http://localhost:8080/"]
    assert q["state"] == ["abc123"]
    assert GMAIL_SEND_SCOPE in q["scope"][0]

    # Desktop client with a port-less localhost URI -> normalized to ephemeral
    # port so the callback listener and the Google redirect match.
    assert build_redirect_uri({"redirect_uris": ["http://localhost"]}, 54321) == "http://localhost:54321/"
    assert build_redirect_uri({"redirect_uris": ["http://localhost:8080"]}, 54321) == "http://localhost:8080/"
    assert build_redirect_uri({"redirect_uris": [GMAIL_SEND_SCOPE]}, 54321) == "http://localhost:54321/"

    # gmail.send token does NOT call profile endpoints (pure helpers).
    ok = {"scope": SCOPES, "email": ALLOWED_ACCOUNT}
    assert _scope_is_gmail_send_only(_granted_scope_set(ok)) is True
    assert validate_token_metadata(ok) is None

    # Identity scopes may be echoed back in canonical userinfo URI form.
    real_echoed = {"scope": "openid https://www.googleapis.com/auth/userinfo.email "
                            "https://www.googleapis.com/auth/userinfo.profile " + GMAIL_SEND_SCOPE,
                   "email": ALLOWED_ACCOUNT}
    assert _scope_is_gmail_send_only(_granted_scope_set(real_echoed)) is True
    assert validate_token_metadata(real_echoed) is None

    # Ordering is irrelevant: send + identity in any order passes.
    reordered = {"scope": GMAIL_SEND_SCOPE + " openid email profile", "email": ALLOWED_ACCOUNT}
    assert _scope_is_gmail_send_only(_granted_scope_set(reordered)) is True

    # Missing gmail.send scope.
    no_send = {"scope": "https://www.googleapis.com/auth/gmail.readonly", "email": ALLOWED_ACCOUNT}
    assert _scope_has_gmail_send(_granted_scope_set(no_send)) is False
    assert "gmail.send scope not present" in (validate_token_metadata(no_send) or "")
    assert _scope_is_gmail_send_only(_granted_scope_set(no_send)) is False

    # Identity scopes alone (no gmail.send) -> FAIL.
    identity_only = {"scope": "openid email profile", "email": ALLOWED_ACCOUNT}
    assert _scope_is_gmail_send_only(_granted_scope_set(identity_only)) is False

    # Broader Gmail data scopes are all rejected. When gmail.send is present
    # alongside a broader scope, validate_token_metadata reports "beyond
    # gmail.send"; when a broader scope is present but gmail.send is absent, it
    # reports "scope not present". Either way _scope_is_gmail_send_only must be
    # False and no broader Gmail scope is accepted.
    for bad_scope in [
        "openid email profile " + GMAIL_SEND_SCOPE + " https://www.googleapis.com/auth/gmail.readonly",
        "openid email profile https://www.googleapis.com/auth/gmail.modify",
        "openid email profile https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.compose",
        "openid email profile https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.insert",
        "openid email profile https://mail.google.com/",
        "openid email profile " + GMAIL_SEND_SCOPE + " https://mail.google.com/",
    ]:
        bad = {"scope": bad_scope, "email": ALLOWED_ACCOUNT}
        assert _scope_is_gmail_send_only(_granted_scope_set(bad)) is False, bad_scope
        reason = validate_token_metadata(bad) or ""
        # A broader Gmail data scope must always be rejected.
        assert (reason and ("beyond gmail.send" in reason or "scope not present" in reason)), bad_scope

    # Wrong authorized account.
    wrong_acct = {"scope": SCOPES, "email": "someone.else@gmail.com"}
    assert _identity_is_allowed("someone.else@gmail.com") is False
    assert "OAUTH ACCOUNT SAFETY BLOCK" in (validate_token_metadata(wrong_acct) or "")

    # Identity extraction from an id_token (no network, no Gmail read scope).
    # Build a fake JWT: header.payload.signature where payload holds email.
    def _make_jwt(payload):
        def b64(d):
            return base64.urlsafe_b64encode(json.dumps(d).encode("utf-8")).decode("ascii").rstrip("=")
        return b64({"alg": "none"}) + "." + b64(payload) + ".sig"

    idt_ok = _make_jwt({"email": ALLOWED_ACCOUNT})
    assert decode_id_token_email(idt_ok) == ALLOWED_ACCOUNT
    assert extract_identity_from_token_response({"id_token": idt_ok}) == ALLOWED_ACCOUNT
    idt_wrong = _make_jwt({"email": "someone.else@gmail.com"})
    assert _identity_is_allowed(extract_identity_from_token_response({"id_token": idt_wrong})) is False
    assert decode_id_token_email("not.a.jwt") is None

    # Localhost callback flow: run oauth_setup with an injected authorization
    # code provider + exchange fn (no network, no real browser).
    with tempfile.TemporaryDirectory() as tmp:
        set_config_dir(Path(tmp))
        (Path(tmp) / "client_secret.json").write_text(
            json.dumps({"installed": {"client_id": "c", "client_secret": "s",
                                      "auth_uri": AUTH_URI, "token_uri": TOKEN_URI,
                                      "redirect_uris": ["http://localhost:8080/"]}}))

        def fake_code_provider(**kw):
            return "SECRET_AUTHCODE", "state"

        def fake_exchange(client, code, redirect_uri):
            return {
                "refresh_token": "SECRET_REFRESH_TOKEN",
                "access_token": "SECRET_ACCESS_TOKEN",
                "id_token": idt_ok,
                "scope": SCOPES,
                "token_type": "Bearer",
            }

        rc = run_oauth_setup(
            print_fn=lambda *a, **k: None,
            get_authorization_code=fake_code_provider,
            exchange_fn=fake_exchange,
            identity_fn=extract_identity_from_token_response,
        )
        assert rc == 0, "setup should succeed with correct account + send-only scope"
        assert token_file().exists()
        assert file_mode_is_600(token_file())
        token = json.loads(token_file().read_text(encoding="utf-8"))
        assert token["email"] == ALLOWED_ACCOUNT
        assert GMAIL_SEND_SCOPE in token["scope"]

        # Wrong account in id_token -> fails closed.
        idt_wrong2 = _make_jwt({"email": "someone.else@gmail.com"})
        def fake_exchange_wrong(client, code, redirect_uri):
            return {"refresh_token": "SECRET_REFRESH_TOKEN", "access_token": "SECRET_ACCESS_TOKEN",
                    "id_token": idt_wrong2, "scope": SCOPES, "token_type": "Bearer"}
        rc2 = run_oauth_setup(
            print_fn=lambda *a, **k: None,
            get_authorization_code=fake_code_provider,
            exchange_fn=fake_exchange_wrong,
            identity_fn=extract_identity_from_token_response,
        )
        assert rc2 != 0, "wrong account must fail closed"

        # Broad Gmail scope in exchange -> fails closed.
        def fake_exchange_broad(client, code, redirect_uri):
            return {"refresh_token": "SECRET_REFRESH_TOKEN", "access_token": "SECRET_ACCESS_TOKEN",
                    "id_token": idt_ok,
                    "scope": "openid email profile https://www.googleapis.com/auth/gmail.readonly",
                    "token_type": "Bearer"}
        rc3 = run_oauth_setup(
            print_fn=lambda *a, **k: None,
            get_authorization_code=fake_code_provider,
            exchange_fn=fake_exchange_broad,
            identity_fn=extract_identity_from_token_response,
        )
        assert rc3 != 0, "broader Gmail scope must fail closed"

        # No id_token -> fails closed (identity cannot be proven).
        def fake_exchange_no_id(client, code, redirect_uri):
            return {"refresh_token": "SECRET_REFRESH_TOKEN", "access_token": "SECRET_ACCESS_TOKEN",
                    "scope": SCOPES}
        rc4 = run_oauth_setup(
            print_fn=lambda *a, **k: None,
            get_authorization_code=fake_code_provider,
            exchange_fn=fake_exchange_no_id,
            identity_fn=extract_identity_from_token_response,
        )
        assert rc4 != 0, "missing id_token must fail closed"

        # Token contents never printed: captured output must not contain tokens.
        captured = []
        captured_print = lambda *a, **k: captured.append(" ".join(str(x) for x in a))
        rc5 = run_oauth_setup(
            print_fn=captured_print,
            get_authorization_code=fake_code_provider,
            exchange_fn=fake_exchange,
            identity_fn=extract_identity_from_token_response,
        )
        assert rc5 == 0
        joined = "\n".join(captured)
        for secret in ["SECRET_AUTHCODE", "SECRET_REFRESH_TOKEN", "SECRET_ACCESS_TOKEN",
                       "refresh_token", "access_token", "client_secret"]:
            assert secret not in joined, f"secret leaked: {secret}"

    set_config_dir(CONFIG_DIR)
    print("PASS grade-check gmail transport self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
