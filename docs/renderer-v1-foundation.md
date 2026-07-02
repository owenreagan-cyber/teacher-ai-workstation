# Renderer Foundation v1

Last updated: 2026-07-01

```text
Status: documentation/status/interface only
Foundation status: active_v1
Implementation approval status: not approved by default for rendering, export, or generation
```

## Purpose

This document is the **canonical closure summary** for Renderer Foundation v1 under approved Phase 3 boundaries. It defines how future renderers will safely consume curriculum contracts, lesson-planning workflow records, registry/library references, binding lookups, and delivery-readiness metadata — without implementing rendering.

Cross-references:

- Interface layer (v0): `docs/renderer-foundation-v0.md`
- Input readiness contract: `docs/renderer-input-readiness-v0.md`
- Input manifest: `assistant/renderer/v0/renderer-manifest.json`
- Interface manifests: `assistant/renderer-foundation/v0/sample-renderer-manifests.json`
- Program closure: `docs/teacher-workstation-foundation-v0.md`
- Implementation gate: `docs/implementation-approval-gate.md`
- Model/tool routing: `assistant/model-routing.md`

## 1. Renderer Role

A future renderer transforms **approved, validated, local metadata and contracts** into teacher-facing or student-facing presentation artifacts.

**Current status:** not implemented.

Renderer Foundation v1 defines planning seams, input requirements, output boundaries, approval gates, and fail-safe rules only.

## 2. Future Renderer Types (Inactive)

| Renderer type | Contract compatibility | Status |
| --- | --- | --- |
| Slide renderer | `direct_instruction_slide_deck_contract` | inactive |
| Teacher script renderer | `teacher_script_contract` | inactive |
| Worksheet renderer | `worksheet_contract` | inactive |
| Review game renderer | `review_game_contract` | inactive |
| Canvas package renderer/exporter | `canvas_export_package_contract` | inactive |
| Printable artifact renderer | cross-contract planning only | inactive |

All renderer types remain **interface_only / not_started** in fixtures.

## 3. Future Renderer Inputs

Future renderers must consume validated local inputs only:

| Input source | Artifact / doc | Status command |
| --- | --- | --- |
| Curriculum Registry v0 | `assistant/curriculum-builder/registry/v0/registry.json` | `--curriculum-registry-v0-status` |
| Curriculum Library reference v0 | `assistant/curriculum-library/v0/sample-library-references.json` | `--curriculum-library-foundation-status` |
| Output Contract v0 | `assistant/curriculum-builder/output-contract/v0/` | `--curriculum-output-contract-v0-status` |
| Teacher Script Contract v0 | `docs/curriculum-teacher-script-contract-v0.md` | contract suite tests |
| Lesson Planning workflow v0 | `assistant/lesson-planning/workflow/v0/sample-lesson-workflow-001.json` | `--lesson-planning-foundation-status` |
| Registry–Contract Binding v0 | `assistant/curriculum-builder/binding/v0/binding-manifest.json` | `--curriculum-binding-v0-status` |
| Delivery / manual export readiness | Canvas LLM planning docs (frozen) | `--teacher-app-designer-canvas-llm-status` |

See `docs/renderer-input-readiness-v0.md` for full input readiness rules.

## 4. Input Readiness Requirements

Before any future renderer runs, these conditions must be satisfied:

- valid registry and library references
- valid output contracts for the target renderer type
- valid lesson-planning workflow metadata when lesson context is required
- valid binding references when cross-linking registry and contracts
- approved or manual-ready review status (future gate)
- no quarantined resources
- no unresolved required dependencies
- no student-data violations
- no unverified external sources
- no placeholder-only resources used for real outputs

## 5. Output Boundaries (Current Mission)

Renderer Foundation v1 generates **no outputs**.

Blocked outputs:

- HTML, PDF, slides, worksheets, review games, Canvas packages
- screenshots, lesson drafts, generated teacher scripts, exported files

## 6. Future Approval Gates

Separate approved missions are required for:

- static preview renderer
- HTML renderer
- PDF/export renderer
- Canvas package renderer
- worksheet renderer
- review game renderer
- real curriculum rendering

See `docs/implementation-approval-gate.md` validators/renderers checklist.

## 7. Fail-Safe Rules

Future renderers must refuse work when:

- input validation fails
- dependencies are missing
- source is unverified
- review status is not approved/manual-ready
- resource is quarantined
- placeholder-only resource is required for a real output
- student data is present or required
- Canvas/API/network access would be needed

## 8. Future Downstream Tool Surfaces (Inactive)

Approved renderer outputs may eventually feed other teacher-facing tools. **No connections are active in Renderer Foundation v1.**

| Future surface | Relationship to renderers | Status |
| --- | --- | --- |
| Lovable | May later consume approved output-contract patterns for classroom app building | inactive |
| Canvas LLM manual export | May later package metadata-only contract outputs when unfreezed | frozen |
| Local printable/export paths | May later render teacher-reviewed artifacts locally | not started |

Lovable is documented in `assistant/model-routing.md` and `docs/master-build-roadmap.md` Program G1 as a future Chief of Staff tool integration for classroom app ideas. Chief of Staff does not route to Lovable, and renderers do not call Lovable APIs in v1. Chief of Staff must not become Lovable — it decides, validates, routes, tracks, and provides status only.

No Lovable API calls, app generation, deployment, OAuth, credentials, or automation.

## Implemented Subsystems (v1 Foundation)

| Subsystem | Location | Role |
| --- | --- | --- |
| v1 closure doc | `docs/renderer-v1-foundation.md` | Canonical renderer foundation summary |
| Input readiness doc | `docs/renderer-input-readiness-v0.md` | Input contract and readiness rules |
| Input manifest | `assistant/renderer/v0/renderer-manifest.json` | Required input source planning manifest |
| Interface manifests | `assistant/renderer-foundation/v0/sample-renderer-manifests.json` | Per-contract renderer interface fixtures |
| Foundation status | `scripts/renderer-foundation-status.sh` | Read-only v1 foundation closure proof |
| Input validator | `scripts/renderer-input-readiness-v0-validator.sh` | Deterministic input manifest validation |
| Interface validator | `scripts/renderer-foundation-v0-validator.sh` | Deterministic interface manifest validation |

## Chief of Staff Command Surface

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --renderer-foundation-status` | Full Renderer Foundation v1 PASS/WARN/FAIL |
| `bin/chief-of-staff --renderer-foundation-v0-validate` | Interface manifest validator |
| `bin/chief-of-staff --renderer-input-readiness-v0-validate` | Input readiness manifest validator |
| `bin/chief-of-staff --dashboard` | Includes Renderer Foundation in dashboard |

## Validation Suite

```bash
bash scripts/renderer-input-readiness-v0-validator.sh
bash scripts/renderer-foundation-v0-validator.sh
bash scripts/renderer-foundation-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

## v1 Foundation Definition of Done

Renderer Foundation v1 is **complete** when:

1. v1 closure and input readiness docs are active
2. Input manifest and interface manifests validate deterministically
3. All five canonical contract types have placeholder renderer interfaces
4. Input readiness references registry, library, contracts, binding, and lesson planning
5. Chief of Staff and dashboard integration are clean
6. No renderer implementation or generated artifacts exist

## Non-Activation Confirmation

Documentation/status/interface only. No renderer code, HTML/PDF generation, slides, worksheets, review games, Canvas packages, lesson generation, LLM calls, APIs, network calls, Lovable integration, or automation.
