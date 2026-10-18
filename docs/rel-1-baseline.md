# REL-1 Baseline — `feature/rel-1` before any REL-1 change

```text
Branch: feature/rel-1 (worktree ~/Projects/taw-rel1)
HEAD under test: 92fb514 (main after PR #385), no REL-1 changes
Date: 2026-10-18
Runner: the MERGE-1 runner, one command at a time, 10-minute cap per command, python3.12
Environment: Claude Code D1.1 sandbox (no network, no Ollama, no local port binding,
             ~/.teacher-ai-workstation unreadable), same mktemp -> $TMPDIR shim as MERGE-1
Python: python3.12 now has PyYAML 6.0.3 and PyMuPDF 1.28.2 (installed by Owen)
```

## What was run

The same 167 commands as `docs/merge-1-baseline.md`, in the same order, with the same runner
and `mktemp` shim (see that file for how the list was built). The Chief suites and the one
newer test from PR #384 were run after them as a separate set, so the 167 totals stay
comparable with MERGE-1.

**Clean-tree note.** Work on section 1 started while this run was in progress. To make sure
nothing it touched leaked into the baseline, the 11 commands that read the bounded runner,
the dashboard, or the Teacher Workstation server (`--dashboard`, both `validate-all` runs,
the dashboard hardening, v1 operating, smoke, launcher, UI, validation-performance and
TKV M2c tests) were rerun on a tree restored to `92fb514`. The table below uses those clean
reruns. Every one gave the same result as in the first pass.

## Result vs MERGE-1

| | MERGE-1 after merge (`c4de912`) | REL-1 baseline (`92fb514`) |
| --- | --- | --- |
| **167-command set** | 132 pass / 35 fail | **134 pass / 33 fail** |

Changes, all caused by Owen's python3.12 installs (no code changed between the two runs):

- `unittest:curriculum_production`: FAIL -> **PASS** (PyYAML now loads the YAML catalogs).
- `unittest:lesson_blueprint`: FAIL -> **PASS** (same).
- `unittest:artifact_quality`: still FAIL, now on `No module named 'PIL'` (Pillow) and
  `No module named 'docx'` (python-docx) instead of `fitz` / `JSONDecodeError`.

No other command changed status, Summary counts, or FAIL/Error lines.

## Failures that remain (recorded, not fixed here)

| Cause | Affected commands |
| --- | --- |
| App-runtime and timer gates allow only `apps/classroom-timer-stopwatch/`, but `apps/` also holds the five Teacher Workstation apps plus `chief-desktop` and `raycast-chief-of-staff` | `app-runtime-approval-gate-status-test`, `classroom-timer-stopwatch-runtime-status-test`, `whole-system-master-roadmap-status-test`, `--dashboard`, `--whole-system-master-roadmap-status`, both `validate-all` runs, `chief-of-staff-v1-operating-test` |
| Date-dependent (today 2026-10-18 is past the planned weeks): `select_startup_week` compares `None > str` | `canvas-llm-approval-queue`, `-artifact-health`, `-assignment-draft-generator`, `-canvas-dashboard`, `-canvas-operations`, `-deployment-readiness`, `-pacing-parser`, `-teacher-decisions`, `-weekly-agenda-publisher` |
| Date-dependent: no launch manifest for the computed week `Q1W5` | `canvas-llm-canvas-launch`, `-canvas-launch-approval`, `-canvas-launch-transport` |
| Date-dependent: week detection / Q2W3 state differs | `canvas-llm-intake`, `-phase-22-canonical-knowledge`, `-phase-22-predictive-weekly-planning-workstation`, `-phase-23-weekly-content-production-engine`, `teacher-workstation-ui-test` (and, outside the 167, `q2w3-corrective-pass-regression-test`) |
| Local state / scheduler not readable in the sandbox (`STATE=FAIL`, `SCHEDULER=FAIL`) | `canvas-llm-grade-check-test` |
| Port 4310 / launcher in the sandbox (local port binding is not permitted) | `canvas-planner-launcher-test` |
| Status scripts call `python3`, which is Homebrew Python 3.14 here and has neither PyYAML nor PyMuPDF (Owen installed them for python3.12) | `curriculum-production-status-test`, `lesson-blueprint-status-test`, `lesson-package-status-test` |
| `fitz` / PIL / python-docx missing for the interpreter in use | `artifact-quality-preflight-test`, `artifact-quality-status-test`, `unittest:artifact_quality` |

## Chief suites and the newer test (outside the 167)

| Command | Result | Exit | Secs |
| --- | --- | --- | --- |
| `bash tests/q2w3-corrective-pass-regression-test.sh` | FAIL (`Science reminder must be non-empty`, date-dependent) | 1 | 0.1 |
| `python3.12 -m unittest discover -s tests/cos -p 'test_*.py'` | PASS | 0 | 5.9 |
| `python3.12 -m unittest discover -s tests/evals -p 'test_*.py'` | PASS | 0 | 7.6 |
| `python3.12 -m unittest discover -s tests -p 'test_dev_guard*.py'` | PASS | 0 | 0.4 |
| `python3.12 tools/dev_safety/dev_safety_probe.py --synthetic` | PASS | 0 | 14.1 |
| `python3.12 evals/harness/run.py --model fake` | PASS: all 11 suites pass. It printed `certification: false (UNCOMMITTED CODE)` only because the worktree had uncommitted files at the time; certification requires a clean commit (D-009) | 0 | 22.8 |

## Dashboard runtime reference

`bin/chief-of-staff --dashboard` took **52.5 s** on the clean tree (53.4 s in the first pass;
61.4 s in MERGE-1). Section 1 compares against this.

## Full results

Totals: 167 commands, 134 pass, 33 fail.

| Command | Result | Exit | Summary PASS/WARN/FAIL | Secs |
| --- | --- | --- | --- | --- |
| `agents:bash-n-cos` | PASS | 0 |  | 0.0 |
| `agents:agents-governance-status` | PASS | 0 | 47/0/0 | 0.1 |
| `agents:cos--agents-governance-status` | PASS | 0 | 47/0/0 | 0.1 |
| `agents:cursor-workflow-status` | PASS | 0 | 126/0/0 | 0.3 |
| `agents:cos--cursor-workflow-status` | PASS | 0 | 126/0/0 | 0.3 |
| `agents:phase-1-status` | PASS | 0 | 928/0/0 | 1.1 |
| `agents:cos--dashboard` | FAIL | 2 | 157/0/3 | 52.5 |
| `agents:cos--whole-system-master-roadmap-status` | FAIL | 1 | 104/0/2 | 2.6 |
| `agents:cos--whole-system-coherence-status` | PASS | 0 | 115/0/0 | 0.2 |
| `agents:cos--app-ecosystem-inventory-status` | PASS | 0 | 51/0/0 | 0.2 |
| `validate-all:default` | FAIL | 1 | 76/0/3 | 31.6 |
| `validate-all:smoke+phase1` | FAIL | 1 | 76/0/3 | 34.3 |
| `sh:3d-builder-workshop-agent-status-test.sh` | PASS | 0 |  | 0.1 |
| `sh:agent-builder-compatibility-governance-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:agents-governance-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:ai-tool-routing-status-test.sh` | PASS | 0 |  | 0.1 |
| `sh:app-ecosystem-inventory-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:app-ecosystem-planning-lanes-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:app-runtime-approval-gate-status-test.sh` | FAIL | 1 | 53/0/7 | 0.2 |
| `sh:artifact-quality-preflight-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:artifact-quality-status-test.sh` | FAIL | 1 | 53/0/13 | 0.4 |
| `sh:autonomous-build-engine-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:backlog-non-mutation-guardrails-test.sh` | PASS | 0 |  | 2.5 |
| `sh:canvas-llm-approval-queue-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-artifact-health-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-assignment-draft-generator-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-assignment-preflight-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-canvas-connector-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-canvas-dashboard-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-canvas-drift-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-canvas-launch-approval-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-canvas-launch-inventory-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-canvas-launch-live-gating-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-llm-canvas-launch-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-canvas-launch-transport-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-canvas-operations-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-cleanup-safety-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-communication-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-deploy-test.sh` | PASS | 0 |  | 0.5 |
| `sh:canvas-llm-deployment-audit-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-deployment-readiness-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-duplicate-detection-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-grade-check-test.sh` | FAIL | 1 |  | 0.4 |
| `sh:canvas-llm-homework-rules-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-intake-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-live-canvas-transport-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-live-q1w2-deployment-test.sh` | PASS | 0 |  | 0.5 |
| `sh:canvas-llm-live-transport-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-pacing-parser-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-pacing-translation-and-reminders-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-phase-18a-canonical-weekly-plan-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-llm-phase-18b-weekly-plan-integration-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-llm-phase-18c-preview-assembly-test.sh` | PASS | 0 |  | 0.8 |
| `sh:canvas-llm-phase-18d-write-readiness-dry-run-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-phase-18e-owner-policy-execution-preconditions-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-phase-22-canonical-knowledge-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-phase-22-predictive-weekly-planning-workstation-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-phase-23-weekly-content-production-engine-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-phase-24-predictive-teacher-brain-test.sh` | PASS | 0 |  | 0.5 |
| `sh:canvas-llm-phase-25-curriculum-source-intelligence-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-phase-26-unified-weekly-production-workstation-test.sh` | PASS | 0 |  | 0.5 |
| `sh:canvas-llm-phase-27-canvas-readiness-and-safety-diff-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-repair-detection-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-sandbox-connector-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-teacher-decisions-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-weekly-agenda-publisher-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-weekly-deployment-center-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-weekly-guardrails-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-page-identity-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-planner-launcher-test.sh` | FAIL | 1 |  | 17.0 |
| `sh:chief-of-staff-daily-operations-test.sh` | PASS | 0 |  | 0.2 |
| `sh:chief-of-staff-dashboard-hardening-test.sh` | PASS | 0 |  | 8.3 |
| `sh:chief-of-staff-next-action-test.sh` | PASS | 0 |  | 0.1 |
| `sh:chief-of-staff-v1-operating-test.sh` | FAIL | 1 | 76/0/3 | 30.2 |
| `sh:classroom-app-lab-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:classroom-timer-stopwatch-planning-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:classroom-timer-stopwatch-runtime-static-safety-test.sh` | PASS | 0 |  | 0.1 |
| `sh:classroom-timer-stopwatch-runtime-status-test.sh` | FAIL | 1 | 75/0/7 | 0.2 |
| `sh:classroom-utility-templates-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:curriculum-binding-v0-test.sh` | PASS | 0 |  | 0.5 |
| `sh:curriculum-builder-contract-schemas-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:curriculum-builder-production-registry-empty-file-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-production-registry-first-record-status-test.sh` | PASS | 0 |  | 0.7 |
| `sh:curriculum-builder-production-registry-first-record-validate-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-builder-production-registry-governance-guardrails-test.sh` | PASS | 0 |  | 0.4 |
| `sh:curriculum-builder-production-registry-governance-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:curriculum-builder-production-registry-metadata-boundary-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:curriculum-builder-production-registry-metadata-pilot-plan-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-production-registry-next-gate-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-production-registry-owen-checklist-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:curriculum-builder-production-registry-phase-2-preflight-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:curriculum-builder-production-registry-planning-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-registry-a4-a7-fixture-schema-status-test.sh` | PASS | 0 |  | 0.6 |
| `sh:curriculum-builder-registry-lane-status-test.sh` | PASS | 0 |  | 11.5 |
| `sh:curriculum-builder-registry-v0-2-dry-run-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-builder-registry-v0-2-local-records-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-builder-registry-v0-2-renderer-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-builder-registry-v0-2-retrieval-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-registry-v0-2-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:curriculum-canvas-package-contract-v0-test.sh` | PASS | 0 |  | 0.1 |
| `sh:curriculum-contract-suite-v0-test.sh` | PASS | 0 |  | 1.6 |
| `sh:curriculum-library-foundation-status-test.sh` | PASS | 0 |  | 0.7 |
| `sh:curriculum-output-contract-v0-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-production-status-test.sh` | FAIL | 1 | 25/0/4 | 0.2 |
| `sh:curriculum-registry-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-review-game-contract-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-source-readiness-status-test.sh` | PASS | 0 |  | 1.6 |
| `sh:curriculum-teacher-script-contract-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-worksheet-contract-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:cursor-operating-modes-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:gemini-discovery-classification-intake-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:governance-lane-status-test.sh` | PASS | 0 |  | 1.2 |
| `sh:lane-review-hardening-guardrails-test.sh` | PASS | 0 |  | 9.3 |
| `sh:lesson-blueprint-status-test.sh` | FAIL | 1 | 31/0/4 | 0.5 |
| `sh:lesson-package-status-test.sh` | FAIL | 1 | 28/0/2 | 0.2 |
| `sh:local-llm-workstation-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:lovable-classroom-app-builder-status-test.sh` | PASS | 0 |  | 0.1 |
| `sh:mac-workstation-experience-status-test.sh` | PASS | 0 |  | 0.1 |
| `sh:markdown-frontmatter-planning-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:owen-architecture-decision-packets-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:presentation-engine-renderer-foundation-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:q2w3-live-refresh-regression-test.sh` | PASS | 0 |  | 0.1 |
| `sh:smoke-chief-of-staff-cli-boundary-test.sh` | PASS | 0 |  | 0.0 |
| `sh:smoke-chief-of-staff-cli.sh` | PASS | 0 |  | 1.5 |
| `sh:teacher-knowledge-vault-m0-architecture-freeze-status-test.sh` | PASS | 0 |  | 1.2 |
| `sh:teacher-knowledge-vault-m1-fake-catalog-status-test.sh` | PASS | 0 |  | 2.1 |
| `sh:teacher-knowledge-vault-m2-local-discovery-approval-status-test.sh` | PASS | 0 |  | 3.0 |
| `sh:teacher-knowledge-vault-m2b-repo-staging-metadata-discovery-test.sh` | PASS | 0 |  | 0.2 |
| `sh:teacher-knowledge-vault-m2b-repo-staging-metadata-status-test.sh` | PASS | 0 |  | 4.2 |
| `sh:teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status-test.sh` | PASS | 0 |  | 4.8 |
| `sh:teacher-knowledge-vault-m2d-selected-folder-metadata-scan-test.sh` | PASS | 0 |  | 0.2 |
| `sh:teacher-knowledge-vault-m2d-selected-folder-preflight-test.sh` | PASS | 0 |  | 0.1 |
| `sh:teacher-knowledge-vault-m2d-selected-folder-status-test.sh` | PASS | 0 |  | 1.4 |
| `sh:teacher-knowledge-vault-m3-fake-duplicate-search-status-test.sh` | PASS | 0 |  | 3.8 |
| `sh:teacher-knowledge-vault-m4-smart-rename-status-test.sh` | PASS | 0 |  | 4.4 |
| `sh:teacher-knowledge-vault-m5-organization-rollback-status-test.sh` | PASS | 0 |  | 5.2 |
| `sh:teacher-knowledge-vault-m6-extraction-ocr-approval-status-test.sh` | PASS | 0 |  | 6.3 |
| `sh:teacher-knowledge-vault-m7-connector-approval-status-test.sh` | PASS | 0 |  | 7.4 |
| `sh:teacher-knowledge-vault-m7b-manual-source-inventory-status-test.sh` | PASS | 0 |  | 7.7 |
| `sh:teacher-knowledge-vault-m7c-manual-inventory-import-preview-status-test.sh` | PASS | 0 |  | 8.7 |
| `sh:teacher-knowledge-vault-m7d-runtime-import-approval-gate-status-test.sh` | PASS | 0 |  | 9.2 |
| `sh:teacher-knowledge-vault-m7e-local-test-catalog-import-test.sh` | PASS | 0 |  | 0.2 |
| `sh:teacher-knowledge-vault-m7e-local-test-catalog-status-test.sh` | PASS | 0 |  | 10.0 |
| `sh:teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status-test.sh` | PASS | 0 |  | 10.9 |
| `sh:teacher-knowledge-vault-m7g-persistent-working-catalog-import-test.sh` | PASS | 0 |  | 0.3 |
| `sh:teacher-knowledge-vault-m7g-persistent-working-catalog-status-test.sh` | PASS | 0 |  | 11.6 |
| `sh:teacher-workstation-health-monitor-test.sh` | PASS | 0 |  | 13.8 |
| `sh:teacher-workstation-system-updater-test.sh` | PASS | 0 |  | 0.4 |
| `sh:teacher-workstation-ui-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:validation-performance-boundary-test.sh` | PASS | 0 |  | 0.3 |
| `sh:vibe-wallpaper-widgets-planning-status-test.sh` | PASS | 0 |  | 0.7 |
| `sh:whole-system-coherence-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:whole-system-master-roadmap-status-test.sh` | FAIL | 1 | 104/0/2 | 2.3 |
| `sh:widget-shortcut-builder-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:workstation-ops-lane-status-test.sh` | PASS | 0 |  | 13.9 |
| `py:canvas-html-compatibility-test.py` | PASS | 0 |  | 0.0 |
| `py:canvas-llm-mastery-fixtures-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-mastery-hardening-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-announcement-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-math-translation-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-pacing-translation-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-reading-spelling-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-shurley-science-history-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-weekly-loop-test.py` | PASS | 0 |  | 0.1 |
| `unittest:artifact_quality` | FAIL | 1 |  | 0.2 |
| `unittest:curriculum_production` | PASS | 0 |  | 0.1 |
| `unittest:lesson_blueprint` | PASS | 0 |  | 0.1 |
