# Local LLM / Ollama Workstation — Readiness Plan

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Local LLM / Ollama Workstation — Program D
Classification: read-only planning — no runtime activation
```

## Purpose

Plan future local LLM/Ollama workstation support for privacy-first, offline-capable teacher workflows. Program D1 implements **read-only status visibility only**.

## Policy Baseline

- `assistant/model-routing.md` — Ollama lane inactive by default
- `docs/ai-tool-routing-matrix.md` — routing matrix; no automated routing active
- `docs/ai-tool-routing-operational-surface.md` — lane visibility read-only

## Future Local LLM Stages

| Stage | Goal | Program D1 status |
| --- | --- | --- |
| D1 | Read-only status/planning foundation | **implemented read-only** |
| D2 | Secrets/capability broker | blocked — approval-gated |
| D3 | Live Ollama health (binary/service) | blocked — not D1 |
| D4 | Model inventory (installed models) | blocked |
| D5 | Approved inference routing | blocked |
| D6 | Background model services | blocked |

## Model-Family Roles (Planning Only)

| Family | Planned role |
| --- | --- |
| Gemma / Gemma 3 / Gemma 3n | Lightweight helper; summarization; classification |
| DeepSeek | Technical/code reasoning — not curriculum authority |
| Qwen | Local coding/general assistant candidate |
| Other | Evaluate by task, safety, speed, memory, quality |

Names remain tentative until locally verified in a future approved mission.

## What Program D1 Verifies (Repo-Local)

- Non-activation boundary doc exists
- Readiness plan and foundation closure doc exist
- Roadmap/capability map/build queue reference Program D accurately
- `--local-llm-workstation-status` CLI available
- Status script passes without executing Ollama or network probes

## Installer Reference (Not Executed by D1)

`setup/08-local-ai.sh` exists as historical installer scaffolding. Program D1 status surfaces **must not** invoke it, brew, ollama, or package managers.

## Non-Activation

No Ollama install, model downloads, inference, localhost probes, API calls, OAuth, student data, or real curriculum content handling.
