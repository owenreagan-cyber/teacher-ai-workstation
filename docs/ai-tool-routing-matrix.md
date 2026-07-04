# AI Tool Routing Matrix

Last updated: 2026-07-02

```text
Status: documentation/status only
Authority: companion to assistant/model-routing.md and docs/master-build-roadmap.md
Matrix version: 2026-07-02-v1
Chief of Staff routing status: read-only operational surface — no automated routing active
```

## Purpose

Define **who does what** across cloud AI, local models, coding agents, and future app-builder surfaces. Chief of Staff may eventually route approved work using this matrix. **No live routing, APIs, or network calls are active.**

Policy baseline: `assistant/model-routing.md`

Read-only proof: `bin/chief-of-staff --ai-tool-routing-status`

Extended governance: `docs/agent-builder-compatibility-and-external-tool-governance.md` (builder classification, CoS no-launch rule, trial checklist)

## Matrix

| Tool | Best use | Should not do | Data allowed | Data blocked | Network/API | CoS routing | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **ChatGPT** | Architecture, review, roadmap, mission prompts | Repo writes, source of truth, student data processing | Owen-authored prompts, public docs, synthetic examples | Student PII, credentials, unreviewed exports | Manual browser only | inactive | API later |
| **Cursor** | Repo implementation, testing, PR lifecycle, validation | Curriculum authority, student-facing output without review | Repo code, docs, fictional fixtures | Student data, secrets in prompts | Local repo work | active (local) | per mission |
| **Gemini** | Curriculum/pedagogical architecture, design exploration | Final curriculum truth, unsupervised generation | Owen-authored curriculum concepts, public standards refs | Student PII, classroom rosters | Manual browser only | inactive | API later |
| **Claude** | Long-form writing, deep review, structured analysis | Autonomous repo mutation, grading authority | Drafts Owen provides, docs | Student PII, grade data | Manual browser only | inactive | API later |
| **Codex** | Focused code implementation/review when invoked | Policy decisions, curriculum design | Repo code, scripts | Student data | Local CLI optional | inactive | per mission |
| **Lovable** | Future classroom app builder (teacher tools, mini-apps, dashboards) | Lesson generation, curriculum registry, CoS replacement | Approved app specs after gate | Student data, student-facing apps without approval | blocked | inactive | Program G1 |
| **Ollama / local models** | Offline helpers: classification, summarization, technical assistance | Source of truth without human review; cloud substitute by default | Local Owen-authored text, repo docs | Student PII until explicit local policy | local only | inactive | install/download gated |
| **OpenAI API** (future) | Approved cloud inference | Default routing without intake | TBD per mission | Student PII default block | blocked | inactive | explicit mission |
| **Anthropic API** (future) | Approved cloud inference | Default routing without intake | TBD per mission | Student PII default block | blocked | inactive | explicit mission |
| **Google API** (future) | Approved cloud inference | Default routing without intake | TBD per mission | Student PII default block | blocked | inactive | explicit mission |
| **3D Builder Workshop Agent** (future) | Classroom object design/sourcing pipeline | Curriculum generation, CoS replacement | Approved object specs after gate | Student data, unapproved deploy | blocked | inactive | Program J |
| **Image generation** (future) | Visual asset workflows when approved | Student-facing output without review | Teacher-approved prompts only | Student PII, copyrighted refs | blocked | inactive | explicit mission |

## High-Level Roles

- **ChatGPT:** architecture, review, roadmap, mission prompts.
- **Cursor:** repo implementation, testing, PR lifecycle.
- **Gemini:** curriculum/pedagogical architecture.
- **Claude:** long-form writing/review if used.
- **Codex:** focused code implementation/review if used.
- **Lovable:** future classroom app builder — external tool after safety gate.
- **Ollama/local models:** offline local helpers; never source of truth without review.
- **3D Builder Workshop Agent:** future classroom object sub-agent; Program J.
- **Image generation (future):** visual asset workflows when explicitly approved.

## Local Model Families (Planning)

Roles are planning guidance only. Model names and versions must be verified locally before assignment.

| Family | Planned role | Notes |
| --- | --- | --- |
| Gemma / Gemma 3 / Gemma 3n | Lightweight local helper; summarization; classification | Unconfirmed variant names marked tentative until verified |
| DeepSeek | Technical/code reasoning; validator/debugging assistance | Not curriculum authority |
| Qwen | Local coding/general assistant candidate | Evaluate by task, safety, speed, memory |
| Other local models | Task-specific evaluation | No installs/downloads until explicit approval |

## Architecture Rules

1. Chief of Staff decides, validates, routes, tracks, and reports — it does not replace specialized builders.
2. Sensitive student data stays local-only or unprocessed until explicitly approved.
3. Cloud tools remain manual-paste or mission-scoped unless a separate API mission approves connection.
4. Lovable, Curriculum Builder runtime, Local LLM inference, renderers, and 3D Builder Workshop Agent remain external/separate subsystems. Chief of Staff orchestrates only.

## Future Chief of Staff Surfaces (Roadmap Only)

- `bin/chief-of-staff --model-routing-status` (planned; see Program B5)
- Future routing commands require explicit implementation missions

## Non-Activation

Documentation/status only. No API keys, OAuth, network calls, automated routing, model downloads, or Lovable connection.
