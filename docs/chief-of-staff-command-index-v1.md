# Chief of Staff Command Index v1

Last updated: 2026-07-01

```text
Status: documentation/status only
Index status: active_v1
Read-only: yes — commands report PASS/WARN/FAIL; they do not activate runtime work
```

## Purpose

Canonical grouped index of Chief of Staff v1 operating commands. Use this document to find the right read-only status, validation, or proof surface without hunting scattered docs.

Cross-references:

- Interactive CLI: `docs/interactive-chief-of-staff-cli.md`
- Dashboard: `docs/chief-of-staff-dashboard.md`
- v1 foundation (when complete): `docs/chief-of-staff-v1-foundation.md`
- Master roadmap: `docs/master-build-roadmap.md`

## Chief of Staff v1 Operating Commands

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --daily-status` | Unified daily operating summary |
| `bin/chief-of-staff --next-action` | Deterministic next recommended program/focus |
| `bin/chief-of-staff --validate-all` | Validation orchestration across core subsystems |
| `bin/chief-of-staff --proof-run` | Reproducible pre-merge proof runner |
| `bin/chief-of-staff --chief-of-staff-v1-status` | Chief of Staff v1 foundation status |
| `bin/chief-of-staff --dashboard` | Full local health dashboard |

## Core Health and Workflow

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --dashboard` | Full workstation health dashboard |
| `bin/chief-of-staff --cursor-workflow-status` | Cursor workflow and governance checks |
| `bin/chief-of-staff --return-to-core-status` | Parked tracks / return-to-core map |
| `bin/chief-of-staff --status` | Basic CLI status |
| `bin/chief-of-staff --memory-status` | Project memory status |
| `bin/chief-of-staff --validate-memory` | Memory validation |

## Curriculum Builder (v1 Foundation)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --curriculum-builder-foundation-status` | Full Curriculum Builder foundation checks |
| `bin/chief-of-staff --curriculum-registry-v0-status` | Registry v0 status |
| `bin/chief-of-staff --curriculum-registry-v0-validate` | Registry v0 validator |
| `bin/chief-of-staff --curriculum-output-contract-v0-status` | Output contract v0 status |
| `bin/chief-of-staff --curriculum-output-contract-v0-validate` | Output contract v0 validator |
| `bin/chief-of-staff --curriculum-binding-v0-status` | Binding v0 status |
| `bin/chief-of-staff --curriculum-binding-v0-validate` | Binding v0 validator |
| `bin/chief-of-staff --curriculum-binding-v0-lookup <registry_id>` | Read-only binding lookup |

## Lesson Planning (Scaffold; Generation Not Active)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --lesson-status` | Lesson planning workspace status |
| `bin/chief-of-staff --lesson-workflow-status` | Lesson workflow status |
| `bin/chief-of-staff --lesson-planning-template-readiness-status` | Template readiness (parked) |

## Canvas LLM (Frozen / Planning Only)

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --teacher-app-designer-canvas-llm-status` | Canvas LLM foundation status (frozen) |

Do not start Canvas LLM runtime PRs by default. See `docs/canvas-llm-stop-marker-curriculum-builder-return.md`.

## Developer Mode

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --developer-status` | Developer Mode status |
| `bin/chief-of-staff --create-developer-project <template> <slug>` | Create developer project from template |

## Proof and Validation Scripts

| Script | Purpose |
| --- | --- |
| `bash scripts/run-workstation-proof.sh` | Full local proof runner |
| `bash scripts/chief-of-staff-validate-all.sh` | Core validation orchestration |
| `bash tests/smoke-chief-of-staff-cli.sh` | CLI smoke tests |
| `bash tests/curriculum-contract-suite-v0-test.sh` | Curriculum contract suite |

## Boundaries

Chief of Staff v1 commands:

- orchestrate read-only status and validation
- recommend next approved work deterministically
- do not generate lessons, curriculum, or review notes
- do not call external APIs, OAuth, or network services
- do not scan folders, index documents, or run LLM inference for planning

## no lesson generation

Chief of Staff coordinates work; it does not generate lesson content.
