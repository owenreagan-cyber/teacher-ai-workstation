# Lovable Classroom App Builder — Readiness Plan

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Lovable Classroom App Builder — Program G1
Classification: read-only planning surface — not connected
```

## Purpose

Plan future Chief of Staff routing of **approved** classroom-app ideas into Lovable for teacher tools, mini-apps, review games, dashboards, and workflow helpers. Program G1 implements **read-only planning visibility only**.

## Architecture Rule

Chief of Staff must **not** become Lovable. Chief of Staff decides, validates, routes, tracks, and reports. Lovable remains an external app-builder tool.

## Future Classroom App Types (Planning)

| Type | Examples |
| --- | --- |
| Teacher tools | Grade helpers, planners, trackers |
| Classroom mini-apps | Timers, group pickers, noise meters |
| Review games | Quiz surfaces, spinners |
| Dashboards | Class status boards |
| Workflow helpers | Checklist apps |

## Future Stages

| Stage | Goal | G1 status |
| --- | --- | --- |
| G1 | Read-only planning/status surface | **implemented read-only** |
| G2 | Manual browser-profile workflows | blocked — approval-gated |
| G3 | Read-only integration probes | blocked |
| G4 | Write integration | blocked |
| G5 | Automation | blocked |

## What Program G1 Verifies (Repo-Local)

- Non-activation boundary doc exists
- Readiness plan and foundation closure doc exist
- Model routing and AI tool routing matrix reference Lovable as inactive
- `--lovable-status` CLI available
- Status script passes without API, OAuth, or network behavior

## Non-Activation

No Lovable API, OAuth, credentials, network calls, live app generation, deployment, automation, or student data.
