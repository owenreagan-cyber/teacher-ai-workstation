# Lesson Planning v1 Foundation

Last updated: 2026-07-01

```text
Status: documentation/status only
Foundation status: active_v1
Implementation approval status: not approved by default for generation, LLM calls, or retrieval
```

## Purpose

This document is the **canonical closure summary** for Lesson Planning v1 foundation under approved Phase 3 boundaries. It describes the safe local-first lesson planning workflow structure, validation surfaces, and approval gates without activating lesson generation.

Cross-references:

- Program roadmap: `docs/master-build-roadmap.md`
- Workflow guide: `docs/lesson-planning-workflow-guide.md`
- Safe review checklist: `docs/safe-local-lesson-review-checklist.md`
- Workspace README: `assistant/lesson-planning/README.md`
- Engineering authority: `docs/engineering-constitution.md`

## Implemented Subsystems (v1 Foundation)

| Subsystem | Location | Role |
| --- | --- | --- |
| Planning workspace | `assistant/lesson-planning/` | Local queue, templates, brief/draft scaffolds |
| Workflow guide | `docs/lesson-planning-workflow-guide.md` | Safe local sequence documentation |
| Workflow schema v0 | `assistant/lesson-planning/workflow/v0/lesson-workflow-schema.json` | Placeholder workflow planning schema |
| Sample workflow | `assistant/lesson-planning/workflow/v0/sample-lesson-workflow-001.json` | Fictional workflow fixture |
| Workspace status | `scripts/lesson-planning-status.sh` | Read-only workspace PASS/WARN/FAIL |
| Foundation status | `scripts/lesson-planning-foundation-status.sh` | Read-only v1 foundation closure proof |
| Workflow validator | `scripts/lesson-planning-workflow-v0-validator.sh` | Deterministic read-only JSON validation |

## Safe Local Workflow Sequence

```text
planning queue -> lesson brief -> supporting drafts -> lesson pack status -> queue status -> human review
```

This sequence is planning documentation and status only. It does not generate lessons, drafts, or review notes.

## Chief of Staff Command Surface

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --lesson-planning-foundation-status` | Full Lesson Planning v1 foundation PASS/WARN/FAIL |
| `bin/chief-of-staff --lesson-planning-workflow-v0-validate` | Read-only workflow v0 validator |
| `bin/chief-of-staff --lesson-status` | Lesson planning workspace status |
| `bin/chief-of-staff --lesson-workflow-status` | Safe workflow sequence status |
| `bin/chief-of-staff --dashboard` | Includes Lesson Planning foundation in dashboard |

## Validation Suite

```bash
bash scripts/lesson-planning-workflow-v0-validator.sh
bash scripts/lesson-planning-foundation-status.sh
bash scripts/lesson-planning-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

## ID Conventions (v0)

| Kind | Pattern | Example |
| --- | --- | --- |
| Workflow ID | `sample-lesson-workflow-<slug>` | `sample-lesson-workflow-001` |
| Lesson slug | `[a-z0-9-]+` | `placeholder-fractions-review` |
| Step ID | `step-NN` | `step-01` |

All v0 workflow fixtures use **fictional placeholder** labels and manual planning references only.

## no lesson generation

Lesson Planning v1 foundation does not generate lessons, briefs, drafts, review notes, or classroom-ready content.

## Boundaries (Still Active)

Lesson Planning v1 foundation does **not** include:

- real lesson generation or LLM calls
- generated lesson briefs, drafts, or review notes in repo
- student data or real student names
- retrieval, renderers, or curriculum registry writes
- APIs, OAuth, network calls, or automation
- publishing, sharing, or school-system integrations

## Future Approval Gates

| Track | Gate | Doc |
| --- | --- | --- |
| Lesson generation | Separate approved mission | `docs/implementation-approval-gate.md` |
| LLM-assisted planning | Local LLM + explicit intake | `docs/master-build-roadmap.md` Program D |
| Curriculum library linkage | Curriculum Library foundation | `docs/curriculum-builder-local-first-foundation-plan.md` |
| Renderers | Renderer foundation intake | Phase 3 Workstream C |

## v1 Foundation Definition of Done

Lesson Planning v1 foundation is **complete** for the approved scope when:

1. Workflow schema v0 and fictional sample validate deterministically
2. Workspace status, workflow status, and foundation status scripts are clean
3. Chief of Staff command surface is documented and wired
4. Dashboard includes foundation status without regression
5. This document and cross-links are active

## Non-Activation Confirmation

Documentation/status only. No lesson generation, generated lesson drafts, generated lesson briefs, real review notes, student data, LLM calls, APIs, retrieval, renderers, network calls, OAuth, or automation.
