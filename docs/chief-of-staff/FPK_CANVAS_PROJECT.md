# FPK Canvas Project

Permanent project handoff for the FPK Canvas Builder inside the Teacher AI Workstation.

```text
Status: active governance (read-only / documentation + config consolidation)
Authority: this file is the front door; deeper authority lives in the files below
Runtime activation: none
```

## Identity

| Field | Value | Authority |
| --- | --- | --- |
| Teacher | Owen Reagan | OWNER_POLICY |
| Class | 4A - Reagan | OWNER_POLICY |
| Room | 203 | OWNER_POLICY |
| School year | 2026-2027 | OWNER_POLICY |
| Live pacing tab | 4A - Reagan | OWNER_POLICY |
| Active repo | `/Users/owen/Projects/teacher-ai-workstation` | OWNER_POLICY |

Machine-readable: `config/fpk/identity.json`.

## Source priority

```text
1. Owen's newest explicit instruction
2. live pacing / live Canvas reads
3. current canonical handoff and locked decisions
4. approved project examples
5. uploaded curriculum/source materials
6. older project precedent
7. model inference
```

Fail closed on ambiguity. Machine-readable: `config/fpk/pacing-source.json`.

## Architecture

The Canvas workflow is intentionally narrow and local-first. The highest authority is the owner-approved operating contract:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

The workflow maintains:

- simplified subject agenda pages (Math, Reading/Spelling, Language Arts, History when active, Science when active)
- only required graded assignments
- minimal assessment announcements
- a monthly (rolling) Homeroom newsletter

Nothing in this project authorizes automatic Canvas publication. Publication is teacher-reviewed and explicitly approved.

## Canonical pointer map

| Concern | Canonical path |
| --- | --- |
| Operating contract | `docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md` |
| Source matrix | `docs/programs/canvas-llm/canonical-context-pack/canonical-source-matrix.md` |
| Context-pack manifest | `docs/programs/canvas-llm/canonical-context-pack/context-pack-manifest.json` |
| Course routing | `config/curriculum/canvas-course-mappings.json` |
| Agenda page rules | `config/curriculum/canvas/agenda-page-rules.json` |
| Weekly agenda standard | `config/curriculum/canvas/weekly-agenda-standard-2026-2027.json` |
| Instructional weeks | `config/curriculum/canvas/instructional-weeks-2026-2027.json` |
| Quarter activation | `config/curriculum/canvas/quarter-subject-activation-2026-2027.json` |
| Homeroom newsletter | `docs/programs/canvas-llm/canonical-context-pack/newsletter-homeroom-contract.md` |
| FPK config layer | `config/fpk/` |
| Current live state | `docs/chief-of-staff/CURRENT_STATE.md` |
| Locked decisions | `docs/chief-of-staff/LOCKED_DECISIONS.md` |
| Operations | `docs/chief-of-staff/OPERATIONS.md` |
| Legacy archaeology | `docs/chief-of-staff/CANVAS_ARCHAEOLOGY.md` |
| GET-only sweep plan | `docs/programs/canvas-llm/canvas-get-only-sweep-plan.md` |

## Rule authority types

Every rule/precedent record uses one of three authorities (see `config/fpk/rule-authority.json`):

```text
OWNER_POLICY         — explicit owner-approved rule, binding
LIVE_CANVAS_PRECEDENT— observed live Canvas behavior, precedent only
MODEL_INFERENCE      — model inference, must never silently become policy
```

## Weekly lifecycle

Every weekly item preserves provenance across four states (see `config/fpk/weekly-lifecycle.json`):

```text
SOURCE → PROPOSED → TEACHER_APPROVED → PUBLISHED_VERIFIED
```

## Credential boundary

The Canvas credential lives outside the repo at `~/.config/teacher-ai-workstation/canvas.env` (mode 0600). Never print token contents. Never persist the token into repo files.
