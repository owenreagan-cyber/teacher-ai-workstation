#!/usr/bin/env python3
"""Gated email delivery for the consolidated teacher report.

Email is sent ONLY to Owen Reagan and ONLY when:
1. explicit send approval is granted (env ``CANVAS_LLM_GRADE_CHECK_SEND_APPROVED``), and
2. a transport is configured — Gmail OAuth/API (primary) or SMTP (optional
   fallback, disabled by default).

Recipient safety is enforced first and fail-closed. Parent messages are NEVER
emailed directly to parents — they only appear inside the teacher's own report
as copy/paste templates.
"""
from __future__ import annotations

import email.message
import os
import smtplib
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PRIVATE_ENV_FILE = Path.home() / ".config" / "teacher-ai-workstation" / "smtp.env"

# ---------------------------------------------------------------------------
# RECIPIENT / SENDER SAFETY ALLOWLISTS (fail closed)
# ---------------------------------------------------------------------------
# The ONLY automated sender is Owen's Gmail. The ONLY automated recipient is
# Owen's school email. Every other address, CC, BCC, or second recipient is
# rejected with a RECIPIENT SAFETY BLOCK before any network/SMTP call.
ALLOWED_SENDER = "oreagan81@gmail.com"
ALLOWED_RECIPIENT = "owen.reagan@thalesacademy.org"


class EmailNotConfigured(RuntimeError):
    """Raised when email delivery is not approved or not configured."""


@dataclass
class EmailResult:
    sent: bool
    recipients: list[str]
    subject: str
    reason: str | None = None


def _normalize_address(addr: str) -> str:
    """Lowercase and strip surrounding whitespace/quotes for comparison."""
    return " ".join((addr or "").strip().lower().split())


def _recipient_allowed(addr: str) -> bool:
    return _normalize_address(addr) == ALLOWED_RECIPIENT


def _sender_allowed(addr: str) -> bool:
    return _normalize_address(addr) == ALLOWED_SENDER


def check_recipient_safety(
    recipient: str,
    cc: str | None = None,
    bcc: str | None = None,
) -> str | None:
    """Return a fail-closed block reason, or None if the recipient set is safe.

    Rules enforced:
    - Exactly ONE recipient (the school email) — no second recipient.
    - No CC.
    - No BCC.
    - Any parent/guardian/student address is rejected.
    - A mixed list containing the school email plus any other address is rejected.
    """
    # Exactly one recipient required.
    if not recipient:
        return "RECIPIENT SAFETY BLOCK: no recipient provided"
    # A list of recipients is not allowed.
    if isinstance(recipient, (list, tuple)):
        if len(recipient) != 1:
            return "RECIPIENT SAFETY BLOCK: more than one recipient"
        recipient = recipient[0]
    if not isinstance(recipient, str):
        return "RECIPIENT SAFETY BLOCK: invalid recipient type"

    # No CC.
    if cc:
        return "RECIPIENT SAFETY BLOCK: CC is not allowed"
    # No BCC.
    if bcc:
        return "RECIPIENT SAFETY BLOCK: BCC is not allowed"

    addr = _normalize_address(recipient)
    if addr != ALLOWED_RECIPIENT:
        return (
            "RECIPIENT SAFETY BLOCK: recipient not on allowlist "
            f"({_normalize_address(recipient)})"
        )
    return None


def _parse_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            result[key] = value
    return result


def _smtp_config() -> dict[str, str]:
    env = dict(os.environ)
    env.update(_parse_env_file(PRIVATE_ENV_FILE))
    return {
        "host": env.get("SMTP_HOST", "").strip(),
        "port": env.get("SMTP_PORT", "").strip(),
        "user": env.get("SMTP_USER", "").strip(),
        "password": env.get("SMTP_PASSWORD", "").strip(),
        "from": env.get("SMTP_FROM", "").strip(),
    }


def _smtp_enabled() -> bool:
    """SMTP fallback is OFF by default; enable only via explicit env flag."""
    return (
        os.environ.get("CANVAS_LLM_GRADE_CHECK_SMTP_ENABLED", "").strip().lower()
        in {"1", "true", "yes"}
    )


def send_approved() -> bool:
    return (
        os.environ.get("CANVAS_LLM_GRADE_CHECK_SEND_APPROVED", "").strip().lower()
        in {"1", "true", "yes"}
    )


def _send_smtp(cfg: dict[str, str], subject: str, body: str, recipient: str) -> None:
    host = cfg["host"]
    port = int(cfg["port"] or 587)
    msg = email.message.EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["from"] or cfg["user"]
    msg["To"] = recipient
    msg.set_content(body)

    if cfg["user"]:
        # STARTTLS + login (port 587) is the common school-SMTP path.
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.ehlo()
            if port != 465:
                server.starttls()
                server.ehlo()
            server.login(cfg["user"], cfg["password"])
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.send_message(msg)


def send_teacher_report(
    *,
    subject: str,
    body: str,
    recipient: str,
    cc: str | None = None,
    bcc: str | None = None,
    config: dict[str, str] | None = None,
    force_transport: str | None = None,
) -> EmailResult:
    """Send the consolidated report to Owen only, or explain why it was not sent.

    Safety order (preserved, fail-closed):
      1. recipient / CC / BCC safety
      2. send approval
      3. transport configuration (Gmail OAuth/API primary; SMTP optional fallback)
      4. sender allowlist
      5. send

    Primary transport is Gmail OAuth/API. SMTP is used only if explicitly
    enabled (``CANVAS_LLM_GRADE_CHECK_SMTP_ENABLED``) and Gmail is unavailable.
    """
    # 1. Recipient safety gate (fail closed, checked before anything else).
    block = check_recipient_safety(recipient, cc=cc, bcc=bcc)
    if block is not None:
        return EmailResult(
            sent=False,
            recipients=[recipient] if isinstance(recipient, (str,)) else (list(recipient) if isinstance(recipient, (list, tuple)) else []),
            subject=subject,
            reason=block,
        )

    # 2. Send approval gate.
    if not send_approved():
        return EmailResult(
            sent=False,
            recipients=[recipient] if isinstance(recipient, str) else list(recipient),
            subject=subject,
            reason=(
                "send not approved; set CANVAS_LLM_GRADE_CHECK_SEND_APPROVED=1 "
                "to enable the first live email"
            ),
        )

    # 3. Transport selection happens before resolve the sender, because the
    #    actual sender depends on which transport sends.
    transport = force_transport or _select_transport()
    cfg = config if config is not None else _smtp_config()

    # 4. Resolve the sender for the selected transport, then run the sender
    #    allowlist gate on THAT sender (never on stale SMTP from/user when the
    #    Gmail OAuth transport is in use).
    if transport == "gmail":
        # Gmail OAuth/API always sends from the allowlisted OAuth account,
        # independent of any leftover SMTP env config.
        sender = ALLOWED_SENDER
    else:
        sender = cfg.get("from") or cfg.get("user") or ALLOWED_SENDER
    if not _sender_allowed(sender):  # type: ignore[arg-type]
        return EmailResult(
            sent=False,
            recipients=[recipient] if isinstance(recipient, str) else list(recipient),
            subject=subject,
            reason=(
                "RECIPIENT SAFETY BLOCK: sender not on allowlist "
                f"({_normalize_address(sender)})"
            ),
        )

    # 5. Send using the selected transport.
    if transport == "gmail":
        from scripts.canvas_llm_grade_check import gmail_transport

        if not gmail_transport.oauth_ready():
            return EmailResult(
                sent=False,
                recipients=[recipient] if isinstance(recipient, str) else list(recipient),
                subject=subject,
                reason=(
                    "Gmail OAuth/API not configured: "
                    "gmail_transport.oauth_ready() is False (client_secret.json + "
                    "token.json required in the gitignored OAuth config dir)"
                ),
            )
        try:
            res = gmail_transport.send_via_gmail_api(
                subject=subject, body=body,
                sender=sender, recipient=recipient,
            )
        except gmail_transport.GmailTransportError as exc:
            return EmailResult(
                sent=False,
                recipients=[recipient] if isinstance(recipient, str) else list(recipient),
                subject=subject,
                reason=f"Gmail API send error: {exc}",
            )
        return EmailResult(sent=True, recipients=[recipient] if isinstance(recipient, str) else list(recipient), subject=subject)

    if transport == "smtp":
        if not cfg["host"]:
            return EmailResult(
                sent=False,
                recipients=[recipient] if isinstance(recipient, str) else list(recipient),
                subject=subject,
                reason="SMTP not configured (SMTP_HOST missing)",
            )
        try:
            _send_smtp(cfg, subject, body, recipient)
        except (smtplib.SMTPException, OSError) as exc:
            return EmailResult(
                sent=False,
                recipients=[recipient] if isinstance(recipient, str) else list(recipient),
                subject=subject,
                reason=f"SMTP send error: {exc.__class__.__name__}: {exc}",
            )
        return EmailResult(sent=True, recipients=[recipient] if isinstance(recipient, str) else list(recipient), subject=subject)

    # No transport configured -> fail closed.
    return EmailResult(
        sent=False,
        recipients=[recipient] if isinstance(recipient, str) else list(recipient),
        subject=subject,
        reason="no email transport configured (Gmail OAuth/API unavailable; SMTP disabled)",
    )


def _select_transport() -> str:
    """Choose Gmail OAuth/API when ready, else SMTP when enabled, else none."""
    from scripts.canvas_llm_grade_check import gmail_transport

    if gmail_transport.oauth_ready():
        return "gmail"
    if _smtp_enabled():
        return "smtp"
    return "none"


def emailer_has_no_parent_recipients() -> bool:
    source = Path(__file__).read_text().lower()
    marker = "def emailer_has_no_parent_recipients"
    idx = source.find(marker)
    scan = source[:idx] if idx >= 0 else source
    return "@parents" not in scan and "parent@" not in scan


def command_self_test() -> int:
    assert emailer_has_no_parent_recipients()

    # Zero-network mock: substitute the Gmail transport module so we can exercise
    # the exact send logic without touching the network or real credentials.
    import importlib
    from types import SimpleNamespace

    gmail_mod = SimpleNamespace(
        oauth_ready=lambda: True,
        GmailTransportError=RuntimeError,
        send_via_gmail_api=lambda subject, body, sender, recipient: SimpleNamespace(
            sent=True, message_id="mock-msg-id"
        ),
    )
    saved = sys.modules.get("scripts.canvas_llm_grade_check.gmail_transport")
    setattr(sys.modules["scripts.canvas_llm_grade_check"], "gmail_transport", gmail_mod)
    sys.modules["scripts.canvas_llm_grade_check.gmail_transport"] = gmail_mod
    try:
        # RECIPIENT SAFETY — fail-closed unit checks (no SMTP/network needed)
        CONF = {"host": "smtp.example.com", "port": "587", "user": "", "password": "", "from": ""}
        os.environ["CANVAS_LLM_GRADE_CHECK_SEND_APPROVED"] = "1"

        # PASS: allowlisted sender+recipient -> Gmail transport mock succeeds.
        pass_match = send_teacher_report(
            subject="4A Grade Check - Student Flags", body="test",
            recipient="owen.reagan@thalesacademy.org",
            config={"host": "", "port": "587", "user": "oreagan81@gmail.com",
                    "password": "", "from": "oreagan81@gmail.com"},
        )
        assert pass_match.sent is True
        assert pass_match.reason is None
        assert check_recipient_safety("owen.reagan@thalesacademy.org") is None

        # BLOCK: second recipient (list of 2).
        blk2 = send_teacher_report(subject="s", body="b",
                                   recipient=["owen.reagan@thalesacademy.org", "parent@example.com"], config=CONF)
        assert blk2.sent is False and "RECIPIENT SAFETY BLOCK" in (blk2.reason or "")
        assert "more than one recipient" in (blk2.reason or "")

        # BLOCK: mixed list.
        blk3 = send_teacher_report(subject="s", body="b",
                                   recipient=["owen.reagan@thalesacademy.org", "student@school.edu"], config=CONF)
        assert blk3.sent is False and "RECIPIENT SAFETY BLOCK" in (blk3.reason or "")

        # BLOCK: parent email.
        blk4 = send_teacher_report(subject="s", body="b", recipient="parent@example.com", config=CONF)
        assert blk4.sent is False and "RECIPIENT SAFETY BLOCK" in (blk4.reason or "")
        assert "not on allowlist" in (blk4.reason or "")

        # BLOCK: student email.
        blk5 = send_teacher_report(subject="s", body="b", recipient="stu.dent@school.edu", config=CONF)
        assert blk5.sent is False and "RECIPIENT SAFETY BLOCK" in (blk5.reason or "")

        # BLOCK: CC.
        blk6 = send_teacher_report(subject="s", body="b", recipient="owen.reagan@thalesacademy.org",
                                   cc="someone@example.com", config=CONF)
        assert blk6.sent is False and "CC is not allowed" in (blk6.reason or "")

        # BLOCK: BCC.
        blk7 = send_teacher_report(subject="s", body="b", recipient="owen.reagan@thalesacademy.org",
                                   bcc="someone@example.com", config=CONF)
        assert blk7.sent is False and "BCC is not allowed" in (blk7.reason or "")

        # BLOCK: sender not on Gmail allowlist (via SMTP transport path).
        blk8 = send_teacher_report(subject="s", body="b", recipient="owen.reagan@thalesacademy.org",
                                   config={"host": "smtp.example.com", "port": "587",
                                           "user": "notgmail@other.com", "password": "", "from": "notgmail@other.com"},
                                   force_transport="smtp")
        assert blk8.sent is False and "sender not on allowlist" in (blk8.reason or "")

        # Gmail transport uses the allowlisted sender even when a stale SMTP
        # "from" (e.g. the recipient email) is present in config. This is the
        # regression that previously blocked the Gmail baseline send. We mock
        # send_via_gmail_api to capture the sender it is called with.
        captured = {}
        gmail_ok = SimpleNamespace(
            oauth_ready=lambda: True,
            GmailTransportError=RuntimeError,
            send_via_gmail_api=lambda **k: (captured.update({"sender": k.get("sender")}),
                                            SimpleNamespace(sent=True, message_id="abc123"))[-1],
        )
        saved_gt = sys.modules.get("scripts.canvas_llm_grade_check.gmail_transport")
        sys.modules["scripts.canvas_llm_grade_check.gmail_transport"] = gmail_ok
        setattr(sys.modules["scripts.canvas_llm_grade_check"], "gmail_transport", gmail_ok)
        try:
            sent_good = send_teacher_report(
                subject="s", body="b", recipient="owen.reagan@thalesacademy.org",
                config={"host": "smtp.example.com", "port": "587",
                        "user": "owen.reagan@thalesacademy.org", "password": "",
                        "from": "owen.reagan@thalesacademy.org"},
            )
        finally:
            sys.modules["scripts.canvas_llm_grade_check.gmail_transport"] = saved_gt
            setattr(sys.modules["scripts.canvas_llm_grade_check"], "gmail_transport", saved_gt)
        assert sent_good.sent is True, f"Gmail transport should use allowlisted sender, got: {sent_good.reason}"
        assert captured.get("sender") == ALLOWED_SENDER, f"Gmail sender must be the allowlisted account, got: {captured.get('sender')}"
        assert sent_good.recipients == ["owen.reagan@thalesacademy.org"]

        # Gmail API failure -> does NOT persist (reason carries the error, sent=False).
        # Simulate by swapping send_via_gmail_api to raise.
        raising = SimpleNamespace(
            oauth_ready=lambda: True,
            GmailTransportError=RuntimeError,
            send_via_gmail_api=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        sys.modules["scripts.canvas_llm_grade_check.gmail_transport"] = raising
        setattr(sys.modules["scripts.canvas_llm_grade_check"], "gmail_transport", raising)
        blk9 = send_teacher_report(subject="s", body="b", recipient="owen.reagan@thalesacademy.org",
                                   config={"host": "", "port": "587", "user": "oreagan81@gmail.com",
                                           "password": "", "from": "oreagan81@gmail.com"})
        assert blk9.sent is False
        assert "Gmail API send error" in (blk9.reason or "")

        os.environ.pop("CANVAS_LLM_GRADE_CHECK_SEND_APPROVED", None)

        # Not approved by default -> no send.
        result = send_teacher_report(
            subject="4A Grade Check - Student Flags", body="test",
            recipient="owen.reagan@thalesacademy.org",
            config={"host": "smtp.example.com", "port": "587", "user": "", "password": "", "from": ""},
        )
        assert result.sent is False
        assert "not approved" in (result.reason or "")
    finally:
        if saved is not None:
            sys.modules["scripts.canvas_llm_grade_check.gmail_transport"] = saved
            setattr(sys.modules["scripts.canvas_llm_grade_check"], "gmail_transport", saved)
        else:
            sys.modules.pop("scripts.canvas_llm_grade_check.gmail_transport", None)
            pkg = sys.modules.get("scripts.canvas_llm_grade_check")
            if pkg is not None and hasattr(pkg, "gmail_transport"):
                delattr(pkg, "gmail_transport")
        os.environ.pop("CANVAS_LLM_GRADE_CHECK_SEND_APPROVED", None)

    print("PASS grade-check emailer self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
