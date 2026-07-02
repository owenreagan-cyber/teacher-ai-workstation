# Integration Planning Foundation v0

Last updated: 2026-07-01

```text
Status: documentation/status/planning only
Foundation status: active_v0
Implementation approval status: not approved by default for APIs, OAuth, sync, or live integrations
```

## Purpose

This document is the **canonical closure summary** for Integration Planning Foundation v0 under approved Phase 3 boundaries. It documents future integration seams for Google Drive, Canvas LMS, and OAuth — with deterministic proof that all integrations remain **inactive**.

Cross-references:

- Program roadmap: `docs/master-build-roadmap.md`
- Google Drive planning: `docs/google-drive-integration-planning-v0.md`
- Canvas planning: `docs/canvas-integration-planning-v0.md`
- OAuth boundary: `docs/oauth-integration-boundary-v0.md`
- Canvas LLM stop marker: `docs/canvas-llm-stop-marker-curriculum-builder-return.md`
- Implementation gate: `docs/implementation-approval-gate.md`

## Implemented Subsystems (v0 Foundation)

| Subsystem | Location | Role |
| --- | --- | --- |
| Google Drive planning | `docs/google-drive-integration-planning-v0.md` | Future Drive reference/sync planning only |
| Canvas planning | `docs/canvas-integration-planning-v0.md` | Future Canvas publish/export planning only |
| OAuth boundary | `docs/oauth-integration-boundary-v0.md` | Credential and OAuth seam boundaries |
| Inactive manifest | `assistant/integration-planning/v0/integration-inactive-manifest.json` | Fictional inactive integration fixtures |
| Foundation status | `scripts/integration-planning-foundation-status.sh` | Read-only v0 foundation closure proof |
| Manifest validator | `scripts/integration-planning-foundation-v0-validator.sh` | Deterministic inactive-integration validation |

## Chief of Staff Command Surface

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --integration-planning-foundation-status` | Full Integration Planning Foundation v0 PASS/WARN/FAIL |
| `bin/chief-of-staff --integration-planning-foundation-v0-validate` | Read-only inactive integration manifest validator |
| `bin/chief-of-staff --dashboard` | Includes Integration Planning foundation in dashboard |

## Future Tool Integrations (Inactive)

External AI and app-builder tools are documented in `assistant/model-routing.md` as part of the broader tool ecosystem (ChatGPT, Claude, Gemini, Cursor, Codex, Lovable).

### Lovable Classroom App Builder Integration — Future / Approval-Gated

Chief of Staff may eventually route approved classroom-app ideas into Lovable. **Current status: planning only — not connected.**

Architecture rule: Chief of Staff must not become Lovable. Chief of Staff decides, validates, routes, tracks, and provides status. Lovable remains an external app-builder tool.

Blocked until explicit future approval: Lovable API, OAuth, credentials, network calls, live app generation, classroom app deployment, automation, student data, generated student-facing apps, and any live integration.

See `docs/master-build-roadmap.md` Program G1.

## Validation Suite

```bash
bash scripts/integration-planning-foundation-v0-validator.sh
bash scripts/integration-planning-foundation-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

## Sync Lifecycle Planning (Inactive)

Future approved sync lifecycle (not active in v0):

```text
planning -> approval gate -> credential boundary -> manual dry-run -> teacher review -> optional activation mission
```

No sync jobs, webhooks, background jobs, or automation exist in v0.

## Boundaries (Still Active)

Integration Planning Foundation v0 does **not** include:

- live integrations, APIs, OAuth setup, or credential storage
- network calls, sync jobs, webhooks, or background jobs
- Drive file access, Canvas publishing, or external service calls

## v0 Foundation Definition of Done

Integration Planning Foundation v0 is **complete** for the approved scope when:

1. Drive, Canvas, and OAuth planning docs are active and cross-linked
2. Inactive integration manifest validates deterministically
3. Chief of Staff command surface is documented and wired
4. Dashboard includes foundation status without regression
5. This document and cross-links are active

## Non-Activation Confirmation

Documentation/status/planning only. No live integrations, APIs, OAuth, network calls, credential storage, sync jobs, webhooks, automation, Drive file access, or Canvas publishing.
