# Weekly Planner Agent — Real Email Delivery + Friday Scheduler Activation

```text
Status: active (implementation)
Phase: weekly-planner-activation
Branch: feature/weekly-planner-activation
Runtime activation: real email (reused transport) + Friday LaunchAgent
```

## Operating model

- periodic background GET-only reconciliation (weekdays 07:00 + 13:00)
- Friday 3:00 PM final source refresh (read-only)
- Friday 3:30 PM approval-ready email (idempotent)
- Friday 4:00 PM guarded publication (existing rollover publisher, approval-gated)

## Email transport

`scripts/weekly_planner_agent/mail_transport.py` reuses the repo's existing
secure mail mechanisms (no second transport, no paid API, no hardcoded secrets):

- **Gmail REST API** (`gmail.send` only, account-locked) via
  `canvas_llm_grade_check.gmail_transport` — primary.
- **SMTP** via `canvas_llm_grade_check.emailer` (credentials in the gitignored,
  0600 `~/.config/teacher-ai-workstation/smtp.env`) — fallback.

Recipient is configured through `schedule_config.delivery_config()` and is
fail-closed against the existing recipient-safety allowlist (single recipient,
no CC/BCC, never a parent/student). Delivery state is honest: `sent` = accepted
by the transport, never `delivered` (only Owen's confirmation does that).

## Scheduler

`scripts/weekly_planner_agent/activation.py` owns dispatch and the LaunchAgent
machinery. The plist carries no business logic and no secrets; it calls one
stable entrypoint (`bin/weekly-planner-friday --scheduled`), which routes by
ET time + weekday. Every milestone is fail-closed.

```bash
bin/weekly-planner-friday check     # periodic GET-only reconciliation
bin/weekly-planner-friday refresh   # Friday 3:00 PM final refresh
bin/weekly-planner-friday notify    # Friday 3:30 PM approval email
bin/weekly-planner-friday publish   # Friday 4:00 PM guarded publish
bin/weekly-planner-friday install|status|uninstall|preview|self-test
```

## Safety invariants

- The Friday rollover engine remains the sole Canvas publisher.
- The 4:00 PM path re-runs the full guarded gate (approval + source freshness +
  cross-source consistency + rollover preflight) before publishing.
- Scheduler installation is not publication approval; the teacher approval
  requirement is unchanged.
- Email never auto-enables; `email_enabled` must be set explicitly in local config.
- No tokens/secrets in Git or in the plist; `.local` delivery history stays local.
