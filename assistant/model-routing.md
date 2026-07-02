# Model Routing

The Chief of Staff should use a hybrid brain strategy. Do not hardcode one model forever.

## Routing strategy

- Local model: private, student-adjacent, school-sensitive, or personal work where local processing is preferred.
- Cloud model: large context, deep reasoning, hard debugging, complex planning, or tasks that exceed the local model.
- Coding model: app development, code review, debugging, architecture, prompt design, and repository work.
- Small local model: quick formatting, small summaries, simple rewriting, and low-risk drafts.
- Future 3D/CAD model or coding model: OpenSCAD, CadQuery, slicer analysis, print-failure diagnosis, and design support after the future 3D agent exists.

## AI tool ecosystem (planning only)

Chief of Staff may eventually route approved work to these surfaces. **All remain inactive by default** unless a separate mission explicitly approves connection.

Full matrix: `docs/ai-tool-routing-matrix.md`

| Tool | Role | Current status |
| --- | --- | --- |
| Local LLM (Ollama) | Private local inference | setup only — see `setup/08-local-ai.sh` |
| ChatGPT / OpenAI | Cloud reasoning and drafting | manual paste only; no API routing |
| Claude (Anthropic) | Cloud reasoning and coding | manual paste only; no API routing |
| Gemini (Google) | Cloud reasoning and search-adjacent tasks | manual paste only; no API routing |
| Cursor | Repository engineering and mission execution | active for local repo work only |
| Codex | CLI coding agent surface | optional local CLI; no automated routing |
| Lovable | Future classroom app-builder surface | **inactive** — future Chief of Staff tool integration |

### Lovable (future / inactive)

**Classification:** Lovable Classroom App Builder Integration — Future / Approval-Gated

Lovable is a **future app-builder integration** for classroom-app ideas. Chief of Staff may eventually route **approved** classroom-app concepts into Lovable for teacher tools, classroom mini-apps, review games, dashboards, workflow helpers, and other classroom-support apps.

**Architecture rule:** Chief of Staff must **not** become Lovable. Chief of Staff decides, validates, routes, tracks, and provides status. Lovable remains an external app-builder tool used only after an approved classroom-app request passes the safety/implementation gate.

Current boundaries:

- no Lovable API calls
- no app generation or deployment
- no live integration, OAuth, credentials, or automation
- no network calls from Chief of Staff to Lovable
- no student data or generated student-facing apps
- no connection to renderer runtime in this phase

Future Lovable work may consume **approved renderer/output-contract patterns** only after separate renderer and integration intake. See `docs/renderer-v1-foundation.md`, `docs/master-build-roadmap.md` Program G1, and `docs/ai-tool-routing-matrix.md`.

Browser profile note: `docs/browser-profiles-guide.md` lists Lovable as a separate profile for manual use only.

## Sensitive data rule

Sensitive student data should be local-only or not processed until explicitly approved.

## Day 1 runtime note

Ollama is the Day 1 local runtime because it is simple. MLX and Rapid-MLX can be evaluated later after real workflows are proven.
