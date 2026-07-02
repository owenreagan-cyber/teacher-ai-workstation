# Chief of Staff Daily Operations Framework

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Chief of Staff v1 Agent Core — Program B2
Read-only: yes
Scheduling: no
Notifications: no
Automation: no
```

## Purpose

Define the **daily operations framework** for Chief of Staff v1. Daily operations are deterministic, local-first, read-only surfaces that help Owen review workstation state without activating runtime work.

Chief of Staff does **not** schedule reminders, send notifications, or run background jobs.

## Daily Operations Surfaces

| Surface | Command / Doc | Status |
| --- | --- | --- |
| Daily status aggregate | `bin/chief-of-staff --daily-status` | implemented |
| Daily briefing (AI summarization) | `--daily-briefing` | planned — requires explicit approval |
| Next-action recommendation | `bin/chief-of-staff --next-action` | implemented (B1) |
| Active priority review | `assistant/memory/active-priorities.md` | doc pointer |
| Build queue review | `docs/build-queue.md` | doc pointer |
| Blocker review | `bin/chief-of-staff --blocker-queue` | implemented |
| Approval queue review | `bin/chief-of-staff --approval-queue` | implemented |
| Validation snapshot | `bin/chief-of-staff --validate-all` | implemented |
| Dashboard snapshot | `bin/chief-of-staff --dashboard` | implemented |
| Closeout prompt | `bin/chief-of-staff --closeout` | implemented |
| Recommended next mission | `docs/master-build-roadmap.md` §10 | doc pointer |

## Recommended Daily Flow (Manual)

1. Run `bin/chief-of-staff --daily-status` for a lightweight aggregate.
2. Review `assistant/memory/active-priorities.md` and `docs/build-queue.md`.
3. Run `bin/chief-of-staff --next-action` for deterministic program recommendation.
4. Run `bin/chief-of-staff --approval-queue` and `--blocker-queue` before starting new implementation.
5. Use `bin/chief-of-staff --dashboard` when full health proof is needed.
6. End session with `bin/chief-of-staff --closeout` checklist.

## Boundaries

- No LLM inference or AI summarization in daily operations commands
- No network calls, APIs, or OAuth
- No student data or real curriculum content
- No Mac system changes, widgets, or shortcuts
- Canvas LLM stop marker remains active unless explicitly superseded

## Proof

```bash
bin/chief-of-staff --daily-status
bash tests/chief-of-staff-daily-operations-test.sh
```
