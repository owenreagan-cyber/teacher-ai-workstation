# Renderer Foundation v0

Last updated: 2026-07-01

```text
Status: documentation/status/interface only
Foundation status: active_v0
Implementation approval status: not approved by default for rendering, export, or generation
```

## Purpose

This document is the **canonical closure summary** for Renderer Foundation v0 under approved Phase 3 boundaries. It defines renderer interface seams, compatibility planning with Output Contract v0, and validation surfaces — without implementing HTML, PDF, slides, worksheets, review games, or Canvas packages.

Cross-references:

- Program roadmap: `docs/master-build-roadmap.md`
- Curriculum Builder v1: `docs/curriculum-builder-v1-foundation.md`
- Output Contract v0: `docs/curriculum-output-contract-v0.md`
- Binding v0: `docs/curriculum-binding-v0.md`
- Implementation gate: `docs/implementation-approval-gate.md`
- Engineering authority: `docs/engineering-constitution.md`

## Renderer Boundary

Renderers are future teacher-reviewed output producers that consume validated Output Contract v0 artifacts and optional Registry–Contract Binding v0 lookups.

Renderer Foundation v0 defines **interfaces only**:

- renderer identity and contract compatibility metadata
- explicit not-started implementation status
- deterministic read-only manifest validation
- Chief of Staff status and dashboard proof

Renderer Foundation v0 does **not** render, export, generate, or write student-facing artifacts.

## Implemented Subsystems (v0 Foundation)

| Subsystem | Location | Role |
| --- | --- | --- |
| Interface schema | `assistant/renderer-foundation/v0/renderer-interface-schema.json` | Placeholder renderer interface record schema |
| Manifest fixtures | `assistant/renderer-foundation/v0/sample-renderer-manifests.json` | Fictional interface manifests per canonical contract |
| Foundation status | `scripts/renderer-foundation-status.sh` | Read-only v0 foundation closure proof |
| Manifest validator | `scripts/renderer-foundation-v0-validator.sh` | Deterministic read-only JSON validation |

## Canonical Contract Compatibility (Planning Only)

| Contract type | Sample contract | Placeholder renderer interface |
| --- | --- | --- |
| `direct_instruction_slide_deck_contract` | `sample-di-slide-deck-001.json` | `sample-renderer-di-slide-deck-001` |
| `teacher_script_contract` | `sample-teacher-script-001.json` | `sample-renderer-teacher-script-001` |
| `worksheet_contract` | `sample-worksheet-001.json` | `sample-renderer-worksheet-001` |
| `review_game_contract` | `sample-review-game-001.json` | `sample-renderer-review-game-001` |
| `canvas_export_package_contract` | `sample-canvas-package-001.json` | `sample-renderer-canvas-package-001` |

Compatibility is documented metadata only. No renderer consumes contracts in v0.

## Chief of Staff Command Surface

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --renderer-foundation-status` | Full Renderer Foundation v0 PASS/WARN/FAIL |
| `bin/chief-of-staff --renderer-foundation-v0-validate` | Read-only renderer manifest v0 validator |
| `bin/chief-of-staff --curriculum-output-contract-v0-status` | Related output contract foundation status |
| `bin/chief-of-staff --dashboard` | Includes Renderer Foundation in dashboard |

## Validation Suite

```bash
bash scripts/renderer-foundation-v0-validator.sh
bash scripts/renderer-foundation-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

## Boundaries (Still Active)

Renderer Foundation v0 does **not** include:

- HTML rendering, PDF rendering, or live export
- worksheet, review game, slide deck, or Canvas package generation
- lesson generation or student-facing artifact writes
- LLM calls, APIs, OAuth, network calls, or automation
- file writes beyond approved docs/fixtures/status artifacts

## Future Approval Gates

| Track | Gate | Doc |
| --- | --- | --- |
| First real renderer | Per-contract renderer intake | `docs/implementation-approval-gate.md` |
| Canvas package builder | Canvas LLM unfreeze + renderer maturity | `docs/canvas-llm-stop-marker-curriculum-builder-return.md` |

## v0 Foundation Definition of Done

Renderer Foundation v0 is **complete** for the approved scope when:

1. Interface schema and fictional manifests validate deterministically
2. All five canonical contract types have placeholder renderer interfaces
3. Chief of Staff command surface is documented and wired
4. Dashboard includes foundation status without regression
5. This document and cross-links are active

## Non-Activation Confirmation

Documentation/status/interface only. No HTML rendering, PDF rendering, worksheet generation, review game generation, Canvas package generation, live export, lesson generation, LLM calls, APIs, network calls, or automation.
