# Local LLM / Ollama — Non-Activation Boundaries

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Local LLM / Ollama Workstation — Program D1
Network calls: no
Ollama install: blocked
Model downloads: blocked
Model inference: blocked
```

## Purpose

Define hard boundaries for Program D1 and all future Local LLM/Ollama work until explicit implementation approval.

## Blocked Now (Program D1 and Default)

| Capability | Status |
| --- | --- |
| Ollama install | blocked |
| Homebrew/package manager install for LLM stack | blocked |
| Model downloads (`ollama pull`) | blocked |
| Model inference (`ollama run`) | blocked |
| Localhost ping / port checks | blocked |
| Service reachability probes | blocked |
| Model folder inspection | blocked |
| `/Applications` or home-directory LLM scans | blocked |
| API keys / OAuth / cloud LLM routing | blocked |
| Automated cloud/local routing | blocked |
| Student data processing | blocked |
| Real curriculum content ingestion | blocked |

## Allowed Now (Program D1)

- Repo-local documentation and planning
- Deterministic status script reporting planning boundaries
- Chief of Staff read-only status command
- Cross-links to AI Tool Routing Matrix (lane visibility only)
- References to installer scripts as **planning artifacts only** — never executed by status surfaces

## Relationship to Other Programs

| Program | Boundary |
| --- | --- |
| AI Tool Routing (R) | Reports Ollama lane as blocked — does not activate runtime |
| Health Monitor (H) | Observes repo health — `--local-llm-health` remains planned/blocked for live probes |
| System Updater (I) | Plans updates — does not install Ollama or models |
| Chief of Staff (B) | Exposes read-only status — does not run inference |

## Future Stages (Approval-Gated)

| Stage | Requires |
| --- | --- |
| D2 Secrets/Capability Broker | Explicit approval mission |
| D3 Live Ollama health probes | Separate approval — not Program D1 |
| D4 Model inventory (live) | Separate approval |
| D5 Inference routing | Separate approval + routing policy |

Program D1 must not blur into any future stage.
