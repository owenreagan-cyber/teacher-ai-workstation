# Renderer Input Readiness v0

Last updated: 2026-07-01

```text
Status: documentation/status only
Readiness enforcement: planning rules only — no runtime renderer
```

## Purpose

This document defines the **future renderer input contract** for Teacher Workstation. It specifies what validated local artifacts a renderer may consume and what readiness gates must pass before any renderer implementation is approved.

Cross-references:

- Renderer Foundation v1: `docs/renderer-v1-foundation.md`
- Input manifest: `assistant/renderer/v0/renderer-manifest.json`
- Curriculum Registry v0: `docs/curriculum-registry-v0.md`
- Curriculum Library v1: `docs/curriculum-library-v1-foundation.md`
- Output Contract v0: `docs/curriculum-output-contract-v0.md`
- Binding v0: `docs/curriculum-binding-v0.md`
- Lesson Planning v1: `docs/lesson-planning-v1-foundation.md`

## Required Input Categories

### Curriculum Registry v0

- **Role:** canonical manual metadata records (`registry_id`)
- **Artifact:** `assistant/curriculum-builder/registry/v0/registry.json`
- **Validation:** `bin/chief-of-staff --curriculum-registry-v0-validate`
- **Rule:** every contract `registry_reference` must resolve to a registry record

### Curriculum Library reference v0

- **Role:** source storage metadata references (Drive/NAS/iCloud/local)
- **Artifact:** `assistant/curriculum-library/v0/sample-library-references.json`
- **Validation:** `bin/chief-of-staff --curriculum-library-reference-v0-validate`
- **Rule:** library references are metadata-only; no live source resolution

### Output Contract v0

- **Role:** structured contract envelopes and canonical contract payloads
- **Root:** `assistant/curriculum-builder/output-contract/v0/`
- **Validation:** `bin/chief-of-staff --curriculum-output-contract-v0-validate`
- **Rule:** renderer type must match `contract_type`

### Teacher Script Contract v0

- **Role:** teacher script section planning within output contract suite
- **Doc:** `docs/curriculum-teacher-script-contract-v0.md`
- **Rule:** script renderer consumes validated teacher script contract only

### Lesson Planning workflow v0

- **Role:** safe local workflow sequence and review gates
- **Artifact:** `assistant/lesson-planning/workflow/v0/sample-lesson-workflow-001.json`
- **Validation:** `bin/chief-of-staff --lesson-planning-workflow-v0-validate`
- **Rule:** lesson context requires `human_review_required: true` and `generation_enabled: false` in fixtures

### Registry–Contract Binding v0

- **Role:** read-only cross-reference between registry records and contracts
- **Artifact:** `assistant/curriculum-builder/binding/v0/binding-manifest.json`
- **Validation:** `bin/chief-of-staff --curriculum-binding-v0-validate`
- **Rule:** binding lookup must pass before contract-to-registry joins in renderers

### Delivery / manual export readiness (frozen)

- **Role:** Canvas LLM manual export planning metadata only
- **Docs:** `docs/canvas-llm-stop-marker-curriculum-builder-return.md`, `docs/canvas-llm-frozen-foundation-handoff-snapshot.md`
- **Rule:** Canvas package renderer remains blocked while stop marker is active

## Readiness Gates (Future)

Before renderer execution:

1. All required input validators return PASS
2. Review status is teacher-approved or explicitly manual-ready
3. No quarantined or blocked registry/library records
4. No student-data policy violations
5. No unresolved binding references
6. No placeholder-only fixtures used for real output missions
7. Separate renderer implementation mission approved

## Fail-Safe Refusal Conditions

Future renderers must refuse when:

| Condition | Action |
| --- | --- |
| Input validation FAIL | refuse |
| Missing registry/library/contract artifact | refuse |
| Binding inconsistency | refuse |
| Unverified external source required | refuse |
| Student data detected | refuse |
| Quarantined resource | refuse |
| Canvas/API/network needed | refuse |
| Implementation not approved | refuse |

## Non-Activation Confirmation

Planning contract only. No renderer runtime, no file generation, no network calls.
