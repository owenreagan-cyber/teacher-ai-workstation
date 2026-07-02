# AI Tool Routing Matrix — Operational Surface

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: AI Tool Routing Matrix — Operational Routing Surface
Classification: read-only routing visibility — not live routing
Network calls: no
Automated routing: no
```

## Purpose

Make the **AI Tool Routing Matrix** operationally visible through deterministic, repo-local Chief of Staff status surfaces. This program reports routing readiness; it does not route work or call external tools.

## Relationship to Other Programs

| Program | Role |
| --- | --- |
| Chief of Staff (B) | Orchestration control plane |
| Health Monitor (H) | Observes PASS/WARN/FAIL health |
| System Updater (I) | Plans updates read-only |
| **AI Tool Routing (this)** | Reports tool/model lane status read-only |

## Tool Lane Status Model

| Lane | Operational status | Routing activation |
| --- | --- | --- |
| Cursor | active (local repo) | local mission execution only |
| ChatGPT / Claude / Gemini | manual browser only | inactive |
| Codex | optional local CLI | inactive automated routing |
| Lovable | planning only (Program G1) | blocked |
| Ollama / local LLM | planning only (Program D) | blocked |
| 3D Builder Workshop Agent | planning only (Program J) | blocked |
| Cloud APIs (OpenAI/Anthropic/Google) | blocked | inactive |

## What Can Be Verified Now (Repo-Local)

- Matrix doc and model-routing policy exist
- Tool lanes documented with approval boundaries
- Chief of Staff manifest lists routing command
- `--model-routing-status` CLI available
- No automated routing scripts active in Chief of Staff

## Architecture Rules

1. Chief of Staff orchestrates; it does not replace specialist builders.
2. Sensitive student data stays local-only or unprocessed until explicitly approved.
3. Cloud tools remain manual unless a separate API mission approves connection.
4. This surface must not become Health Monitor or System Updater.

## CLI Surface

```bash
bin/chief-of-staff --model-routing-status
bash scripts/ai-tool-routing-status.sh
```

## Non-Activation

No API keys, OAuth, network calls, automated routing, Ollama ping, model downloads, Lovable connection, or live model inference.
