# Widget and Shortcut Builder — Readiness Plan

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Widget and Shortcut Builder — Program F
Classification: read-only catalog foundation — no install or automation
```

## Purpose

Plan future teacher productivity widgets, shortcuts, quick actions, and dashboard panels surfaced from approved Chief of Staff commands. Program F1 implements **read-only catalog and status visibility only**.

## Metadata-Only Future Catalog (Planning)

### Widget concepts (documentation only)

| Concept | Purpose |
| --- | --- |
| Chief of Staff Status Widget | Dashboard health at a glance |
| Next Action Widget | Single recommended focus |
| Dashboard Health Widget | PASS/WARN/FAIL summary |
| Curriculum Builder Widget | Registry/contract readiness |
| Lesson Planning Widget | Lesson workspace pointers |
| Canvas Frozen/Ready Widget | Canvas stop-marker visibility |
| Local LLM Status Widget | D1 planning boundaries |
| Mode Widget | Teacher mode context |
| Approval Queue Widget | Pending approvals |
| Today's Teacher Launchpad | Curated daily entry points |

### Shortcut concepts (documentation only)

| Concept | Purpose |
| --- | --- |
| Open Workstation | Launch planning context |
| Run Dashboard | `bin/chief-of-staff --dashboard` |
| Run Proof Main | Pre-merge proof runner |
| Start Planning Mode | Mode context pointer |
| Start Teaching Mode | Mode context pointer |
| Open Cursor Mission | Mission prompt pointer |
| Open Gemini Curriculum Architect | Routing matrix pointer |
| Open Lovable App Builder | Manual profile only until G1 |
| Capture App Idea | Intake pointer |
| Capture Resource Note | Intake pointer |
| Run Daily Briefing | Future B2+ — approval-gated |
| Run Closeout | `--closeout` pointer |

### Additional surfaces (planning)

- Quick actions and teacher workflow buttons
- Menu bar helpers
- Vibe Panel ideas
- Classroom-mode controls
- Lesson-prep helpers
- App-launch helpers
- Reviewable automation ideas (blocked until explicit approval)

## Future Stages

| Stage | Goal | F1 status |
| --- | --- | --- |
| F1 | Read-only catalog/status foundation | **implemented read-only** |
| F2 | Widget catalog live health | blocked — approval-gated |
| F3 | Shortcut catalog live health | blocked — approval-gated |
| F4 | Manual widget install path | blocked |
| F5 | Manual shortcut install path | blocked |
| F6 | Vibe Panel integration | blocked — Program E3 |

## What Program F1 Verifies (Repo-Local)

- Non-activation boundary doc exists
- Readiness plan and foundation closure doc exist
- Catalog concepts documented as metadata-only
- `--widget-shortcut-status` CLI available
- Status script passes without widget/shortcut/Mac automation behavior
- `--widget-health` and `--shortcut-health` remain planned (not live health)

## Non-Activation

No widget install, shortcut install, shortcut execution, AppleScript, Mac settings mutation, automation, network calls, student data, or real curriculum content.
