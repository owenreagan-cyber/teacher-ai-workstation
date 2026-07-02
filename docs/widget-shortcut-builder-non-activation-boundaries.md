# Widget and Shortcut Builder — Non-Activation Boundaries

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Widget and Shortcut Builder — Program F1
Widget install: blocked
Shortcut install: blocked
Shortcut execution: blocked
AppleScript: blocked
Mac system changes: blocked
Automation: no
Network calls: no
```

## Purpose

Define hard boundaries for Program F1 and all future Widget and Shortcut Builder work until explicit implementation approval.

## Blocked Now (Program F1 and Default)

| Capability | Status |
| --- | --- |
| Widget installation | blocked |
| Shortcut installation | blocked |
| `.shortcut` file generation | blocked |
| Shortcuts.app execution | blocked |
| `shortcuts` CLI execution | blocked |
| `osascript` / AppleScript automation | blocked |
| `defaults write` system prefs | blocked |
| Mac system setting changes | blocked |
| Wallpaper apply | blocked |
| Widget layout apply | blocked |
| LaunchAgents / background jobs | blocked |
| Notifications / schedulers | blocked |
| API / OAuth / network calls | blocked |
| Student data on surfaces | blocked |
| Real curriculum content on surfaces | blocked |

## Allowed Now (Program F1)

- Repo-local documentation and metadata-only catalog concepts
- Deterministic status script reporting planning boundaries
- Cross-links to Mac Workstation Experience (`--mac-workstation-status`), Local LLM (`--local-llm-workstation-status`), and AI Tool Routing (`--model-routing-status`)
- Chief of Staff read-only catalog foundation via `--widget-shortcut-status`

## Relationship to Other Programs

| Program | Boundary |
| --- | --- |
| Mac Workstation Experience (E1) | Teacher modes and appearance planning — no widget/shortcut install |
| Local LLM / Ollama (D1) | Status only — no inference for widget content |
| AI Tool Routing (R0) | Lane visibility — no automated shortcut routing |
| Health Monitor (H) | Repo health — `--widget-health` / `--shortcut-health` remain planned/blocked |
| Chief of Staff (B) | Orchestration and status — no install or run |

## Future Stages (Approval-Gated)

| Stage | Requires |
| --- | --- |
| F2 Widget catalog live health | Explicit approval mission |
| F3 Shortcut catalog live health | Explicit approval mission |
| F4 Manual widget install path | Explicit approval per widget |
| F5 Manual shortcut install path | Explicit approval per shortcut |
| F6 Vibe Panel / launch helpers | Program E3 + explicit approval |

Program F1 must not blur into any future stage.
