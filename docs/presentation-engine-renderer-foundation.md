# Presentation Engine — Renderer Foundation Planning

Last updated: 2026-07-03

```text
Status: documentation/status only
Program: Presentation Engine — Classroom Display Renderer Foundation
Closure status: complete_presentation_engine_renderer_foundation_planning
Classification: planning-only — no runtime rendering, export, or generation
Implementation approval: not approved by this doc alone
```

## Purpose

Canonical planning foundation for a future **Presentation Engine** that helps Owen structure classroom display artifacts (slide outlines, teacher display modes, speaker-note labels, interaction hints) from approved local metadata — without implementing rendering, AI generation, or real curriculum ingestion.

This lane is distinct from but related to **Renderer Foundation v1** (`docs/renderer-v1-foundation.md`), which defines general curriculum-contract renderer interfaces. Presentation Engine focuses on teacher-facing classroom display workflow value.

## Teacher Workflow Value

| Future capability | Teacher value | Current status |
| --- | --- | --- |
| Structured slide outline from registry labels | Faster lesson openers and review displays | planning only |
| Theme/display-mode planning | Consistent classroom projection posture | planning only |
| Resource reference labels on slides | Traceability without opening Drive | planning only |
| Speaker-notes labels (metadata) | Cue cards without pasted curriculum text | planning only |
| Classroom interaction hints | Engagement scaffolding as labels only | planning only |
| Export target planning | Explicit approval gate before any export | planning only |

**This mission does not generate, render, or export any real slides.**

## Local-First Posture

- All examples are fake/local fixtures under `assistant/presentation-engine/samples/renderer-planning/`.
- No network calls, OAuth, Drive, Canvas, NAS, or iCloud access.
- No real curriculum files, copied textbook text, worksheet questions, or student data.
- Production registry remains parked; this lane does not add registry records.

## Future Input Model (Inactive)

Future Presentation Engine inputs are **metadata labels and planning records only**:

| Input concept | Source lane | Status |
| --- | --- | --- |
| `resource_reference_label` | Curriculum Builder / production registry labels | inactive — manual labels only when approved |
| `presentation_plan` | Presentation Engine planning fixtures | inactive |
| `slide_outline` | Presentation Engine planning fixtures | inactive |
| `theme_profile` | Presentation Engine planning fixtures | inactive |
| Contract-bound slide deck metadata | Renderer Foundation v1 / A4–A7 contracts | inactive |
| Lesson planning workflow records | Lesson Planning Foundation | inactive |

See `docs/presentation-engine-static-renderer-interface-plan.md` for concept definitions.

## Future Output Model (Inactive)

| Output concept | Description | Status |
| --- | --- | --- |
| Classroom display structure (planning JSON) | Fake fixture shape only | inactive |
| Slide outline labels | Non-rendered outline records | inactive |
| Export target enum | Planning gate — no export command | inactive |
| Rendered slide files | HTML/PPTX/Keynote/Google Slides | **blocked** |

## Safe Fixture-Only Examples

| Fixture | Path |
| --- | --- |
| Example presentation plan | `assistant/presentation-engine/samples/renderer-planning/example-presentation-plan-001.json` |
| Example slide outline | `assistant/presentation-engine/samples/renderer-planning/example-slide-outline-001.json` |
| Negative blocked-export example | `assistant/presentation-engine/samples/renderer-planning/negative/blocked-runtime-export-example.json` |

All fixtures use fake labels (`example-math`, `fake-local-resource-label`, etc.). PASS on status commands proves fixture presence only — not runtime approval.

## Blocked Runtime Behavior

See `docs/presentation-engine-blocked-runtime-boundaries.md` for the full blocked list.

Summary: runtime rendering, slide export, AI generation, auto lesson creation, real curriculum ingestion, file parsing, OCR, integrations, and student-data workflows remain **blocked**.

## Relationship to Curriculum Builder / Resource Registry

| Surface | Relationship |
| --- | --- |
| Curriculum Builder registry lanes | Presentation Engine may consume **approved metadata labels** only — no auto-resolution |
| Production registry (parked) | One governed record exists; no second record; no writes from this lane |
| Renderer Foundation v1 | General contract renderer interfaces; Presentation Engine is classroom-display scoped |
| CB-IMPL-3 registry renderer preview | Metadata preview only; not Presentation Engine runtime |

## Relationship to Chief of Staff

| Command | Role |
| --- | --- |
| `bin/chief-of-staff --presentation-engine-renderer-foundation-status` | Read-only planning closure proof |
| `bin/chief-of-staff --renderer-foundation-status` | General renderer interface foundation |
| `bin/chief-of-staff --whole-system-master-roadmap-status` | Lane 13 posture and next safe lane selector |
| `bin/chief-of-staff --curriculum-registry-lane-status` | Registry lane aggregate (parked production path) |

## Relationship to Future Classroom Display Workflows

Future classroom display workflows may chain:

```text
approved metadata labels → presentation_plan (fixture) → slide_outline (fixture) → [Owen approval gate] → export target (blocked until mission)
```

No step in this chain is active. Widget/shortcut install, live Vibe Panel, and utility app execution remain blocked in separate lanes.

## Approval Gates Required Before Implementation

| Gate | Requirement |
| --- | --- |
| Implementation gate | Explicit Owen mission per `docs/implementation-approval-gate.md` |
| Real curriculum ingestion | Separate approved mission — blocked |
| AI generation | Separate approved mission — blocked |
| Export/render runtime | Separate approved mission — blocked |
| Drive/Canvas/NAS/iCloud/API | Separate integration missions — blocked |
| Production registry writes | Parked (Option D); writer/`--write`/second record blocked |
| Student data | Absolute prohibition per Engineering Constitution |

## Definition of Done (This Mission)

| # | Deliverable | Status |
| --- | --- | --- |
| 1 | Renderer foundation doc | this file |
| 2 | Static renderer interface plan | `docs/presentation-engine-static-renderer-interface-plan.md` |
| 3 | Blocked runtime boundaries | `docs/presentation-engine-blocked-runtime-boundaries.md` |
| 4 | Fake/local fixtures | `assistant/presentation-engine/samples/renderer-planning/` |
| 5 | Status script | `scripts/presentation-engine-renderer-foundation-status.sh` |
| 6 | CLI command | `bin/chief-of-staff --presentation-engine-renderer-foundation-status` |
| 7 | Tests | `tests/presentation-engine-renderer-foundation-status-test.sh` |
| 8 | Roadmap coherence | whole-system report, build queue, capability map |

## Orchestrated Proof

```bash
bin/chief-of-staff --presentation-engine-renderer-foundation-status
bash scripts/presentation-engine-renderer-foundation-status.sh
bash tests/presentation-engine-renderer-foundation-status-test.sh
```

## Recommended Next Mission

Safe docs/status lanes (proposal index sync, A4–A7 fixture enrichment planning) or blocked production-registry gates (Options A/B/C) only with explicit Owen decision. Runtime Presentation Engine export/render requires a separate implementation mission.

## Non-Activation

`complete_presentation_engine_renderer_foundation_planning` is a documentation closure marker only. It does not authorize rendering, export, AI generation, real curriculum ingestion, integrations, or production registry mutation.
