"""Real email transport for the Weekly Planner Agent.

Reuses the repo's existing secure mail mechanisms — never a second transport:

* Gmail REST API (send-only, ``gmail.send``, account-locked to Owen) via
  ``scripts.canvas_llm_grade_check.gmail_transport``.
* SMTP fallback via ``scripts.canvas_llm_grade_check.emailer`` (credentials in
  the gitignored, 0600 ``~/.config/teacher-ai-workstation/smtp.env``).

No passwords, app passwords, tokens, or email addresses are hardcoded here.
The recipient is configured through ``schedule_config.delivery_config()`` and is
fail-closed against the existing recipient safety allowlist (single recipient,
no CC/BCC, never a parent/student address).

Delivery state is honest: a message is marked ``accepted`` (transport accepted
it) — never ``delivered``. Final inbox receipt is only confirmable by Owen.
"""
from __future__ import annotations

from typing import Any

from scripts.canvas_llm_grade_check import emailer, gmail_transport

from . import schedule_config


def transport_status() -> dict[str, Any]:
    """Read-only readiness report. Never sends, never prints secrets."""
    gmail_ready = bool(gmail_transport.oauth_ready())
    smtp_cfg = emailer._smtp_config()
    smtp_ready = bool(smtp_cfg.get("host"))
    cfg = schedule_config.delivery_config()
    return {
        "gmail_ready": gmail_ready,
        "smtp_ready": smtp_ready,
        "enabled": bool(cfg.get("email_enabled")),
        "recipient_configured": bool(cfg.get("email_recipient")),
        "from_configured": bool(cfg.get("email_from")),
    }


def send(subject: str, body: str, recipient: str | None = None) -> dict[str, Any]:
    """Send one message through the best available transport. Read-only on failure.

    Returns ``{accepted, transport, message_id, error}``. ``accepted=True`` means
    the transport accepted the message for delivery (NOT that the recipient has
    confirmed receipt).
    """
    cfg = schedule_config.delivery_config()
    if not cfg.get("email_enabled"):
        return {"accepted": False, "transport": None, "message_id": None,
                "error": "EMAIL_DISABLED"}

    to = (recipient or "").strip() or str(cfg.get("email_recipient") or "").strip()
    if not to:
        return {"accepted": False, "transport": None, "message_id": None,
                "error": "RECIPIENT_MISSING"}

    # Recipient safety: exactly one allowlisted recipient, no CC/BCC, never a
    # parent/student address. Fail closed before any network call.
    block = emailer.check_recipient_safety(to)
    if block is not None:
        return {"accepted": False, "transport": None, "message_id": None,
                "error": block}

    # Primary: Gmail OAuth/API (send-only, strongest delivery signal).
    if gmail_transport.oauth_ready():
        try:
            result = gmail_transport.send_via_gmail_api(
                subject=subject, body=body,
                sender=gmail_transport.ALLOWED_ACCOUNT, recipient=to,
            )
            return {"accepted": bool(result.sent), "transport": "gmail",
                    "message_id": result.message_id, "error": None}
        except gmail_transport.GmailTransportError as exc:
            return {"accepted": False, "transport": "gmail", "message_id": None,
                    "error": f"gmail send error: {exc}"}

    # Fallback: SMTP (existing primitive). Sender must stay on the allowlist.
    smtp_cfg = emailer._smtp_config()
    if not smtp_cfg.get("host"):
        return {"accepted": False, "transport": None, "message_id": None,
                "error": "EMAIL_TRANSPORT_NOT_CONFIGURED"}
    sender = smtp_cfg.get("from") or smtp_cfg.get("user")
    if not emailer._sender_allowed(sender):
        return {"accepted": False, "transport": None, "message_id": None,
                "error": "SENDER_NOT_ALLOWLISTED"}
    try:
        emailer._send_smtp(smtp_cfg, subject, body, to)
        return {"accepted": True, "transport": "smtp", "message_id": None,
                "error": None}
    except Exception as exc:  # noqa: BLE001 — SMTP errors surface as non-secret reason
        return {"accepted": False, "transport": "smtp", "message_id": None,
                "error": f"smtp send error: {type(exc).__name__}"}


def command_self_test() -> int:
    # No network: prove the adapter maps config/recipient-safety/transport
    # outcomes honestly using the existing emailer primitives (which are already
    # covered by their own zero-network self-tests).
    status = transport_status()
    assert isinstance(status["gmail_ready"], bool)
    assert isinstance(status["smtp_ready"], bool)
    assert isinstance(status["enabled"], bool)

    # Disabled email -> EMAIL_DISABLED without any transport call.
    from . import schedule_config as sc
    orig = sc.planner_root
    import tempfile
    from pathlib import Path
    sc.planner_root = lambda: Path(tempfile.mkdtemp())
    try:
        result = send("s", "b", "owen.reagan@thalesacademy.org")
        assert result["accepted"] is False and result["error"] == "EMAIL_DISABLED", result
    finally:
        sc.planner_root = orig

    # Recipient safety is delegated to the canonical allowlist (reuse).
    assert emailer.check_recipient_safety("parent@example.com") is not None
    assert emailer.check_recipient_safety("owen.reagan@thalesacademy.org") is None

    print("PASS weekly-planner-agent mail-transport self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
