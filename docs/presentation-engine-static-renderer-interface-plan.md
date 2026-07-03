# Presentation Engine — Static Renderer Interface Plan

Last updated: 2026-07-03

```text
Status: planning-only interface specification
Schema activation: none — concepts and fake fixtures only
Runtime commands: none
Render command: none
Generation command: none
```

## Purpose

Define future **Presentation Engine** planning concepts for classroom display structures. This document is a static interface plan — not an active schema, API, or renderer.

All examples are fake/local. No real lesson content, copied curriculum, student data, Drive URLs, file paths, render commands, or generation commands.

## Concept Inventory

| Concept | Role | Example fixture field |
| --- | --- | --- |
| `presentation_plan` | Top-level classroom display intent (labels only) | `example-presentation-plan-001.json` |
| `slide_outline` | Ordered slide labels and display hints | `example-slide-outline-001.json` |
| `theme_profile` | Display theme labels (colors/fonts as text labels) | `theme_profile_label` |
| `teacher_display_mode` | Projection posture label (e.g. example-full-screen) | `teacher_display_mode` |
| `resource_reference_label` | Non-resolving registry-style label | `fake-local-resource-label` |
| `speaker_notes_label` | Teacher cue label — not pasted notes text | `speaker_notes_label` |
| `classroom_interaction_hint` | Engagement scaffolding label | `classroom_interaction_hint` |
| `export_target` | Future export gate enum — no export active | `export_target: blocked_planning_only` |

## Future `presentation_plan` Shape (Planning Only)

```json
{
  "fixture_classification": "fake_local_planning_only",
  "presentation_plan_id": "example-presentation-plan-001",
  "title_label": "Example Fraction Review Display",
  "subject_label": "example-math",
  "grade_band_label": "example-grade",
  "resource_reference_label": "fake-local-resource-label",
  "theme_profile_label": "example-classroom-theme",
  "teacher_display_mode": "example-full-screen",
  "export_target": "blocked_planning_only",
  "runtime_rendering": "blocked",
  "ai_generation": "blocked"
}
```

Canonical fake fixture: `assistant/presentation-engine/samples/renderer-planning/example-presentation-plan-001.json`

## Future `slide_outline` Shape (Planning Only)

```json
{
  "fixture_classification": "fake_local_planning_only",
  "slide_outline_id": "example-slide-outline-001",
  "presentation_plan_id": "example-presentation-plan-001",
  "slides": [
    {
      "slide_index": 1,
      "slide_title_label": "Example Opener Label",
      "speaker_notes_label": "example-teacher-cue-label",
      "classroom_interaction_hint": "example-think-pair-share-label"
    }
  ],
  "export_target": "blocked_planning_only"
}
```

Canonical fake fixture: `assistant/presentation-engine/samples/renderer-planning/example-slide-outline-001.json`

## Rules

| Rule | Enforcement |
| --- | --- |
| Fake/local labels only | Status script + negative fixtures |
| No real lesson content | No Saxon, textbook, worksheet, or assessment text |
| No student data | Constitution absolute ban |
| No Drive URLs or file paths | Negative fixture + status grep checks |
| No render command | No CLI handler for render/export/generate |
| No schema activation | JSON fixtures marked `fake_local_planning_only` |
| No generation prompts | Fixtures exclude prompt fields |

## Relationship to Renderer Foundation v1

| Layer | Doc | Scope |
| --- | --- | --- |
| Contract renderer interfaces | `docs/renderer-foundation-v0.md` | Curriculum output contracts |
| Input readiness | `docs/renderer-input-readiness-v0.md` | Fail-safe refusal rules |
| Presentation Engine static plan | this doc | Classroom display planning concepts |

Presentation Engine may eventually align slide-outline concepts with `direct_instruction_slide_deck_contract` — alignment is **not started**.

## Negative Example

`assistant/presentation-engine/samples/renderer-planning/negative/blocked-runtime-export-example.json` documents fields that must **not** appear in approved planning fixtures (URLs, paths, generation prompts, student identifiers).

## Approval Before Activation

Activating any schema validator, render pipeline, or export command requires:

1. Owen explicit implementation mission
2. `docs/implementation-approval-gate.md` compliance
3. `docs/presentation-engine-blocked-runtime-boundaries.md` gate review
4. Separate missions for integrations, AI, and real curriculum — all blocked today

## Non-Activation

This static interface plan does not create runtime behavior. Concept names are documentation vocabulary only until an approved implementation mission activates them.
