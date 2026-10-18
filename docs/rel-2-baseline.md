# REL-2 Baseline — `feature/rel-2` before any REL-2 change

```text
Branch: feature/rel-2 (worktree ~/Projects/taw-rel2)
HEAD under test: b1f22dc (main after PR #386, REL-1), no REL-2 changes
Date: 2026-10-18
Runner: the REL-1 runner, one command at a time, 10-minute cap per command, python3.12
Environment: Claude Code D-022 light profile (localhost and github.com fetch allowed; push,
             credential folders, and destructive commands outside the project blocked),
             same mktemp -> $TMPDIR shim as MERGE-1 and REL-1
Python: python3.12 (3.12.13) and python3 (Homebrew 3.14.7) both have PyMuPDF 1.28.2,
        PyYAML 6.0.3, Pillow 12.3.0, python-docx 1.2.0, python-pptx 1.0.2 (installed by Owen)
```

## What was run

The same 167 commands as `docs/merge-1-baseline.md` and `docs/rel-1-baseline.md`, in the same
order, with the same runner and `mktemp` shim.

## Result vs REL-1

| | REL-1 final (`5adbb62`) | REL-2 baseline (`b1f22dc`) |
| --- | --- | --- |
| **167-command set** | 151 pass / 16 fail | **157 pass / 10 fail** |

Changes, all caused by Owen's package installs (no code changed between the two runs):

| Command | REL-1 final | REL-2 baseline | Cause |
| --- | --- | --- | --- |
| `artifact-quality-preflight-test` | FAIL | **PASS** | Pillow, python-docx, python-pptx now installed |
| `artifact-quality-status-test` | FAIL (53/0/13) | **PASS** | same; the status script runs plain `python3` (3.14) |
| `unittest:artifact_quality` | FAIL | **PASS** | Pillow and python-docx now installed for python3.12 |
| `curriculum-production-status-test` | FAIL (25/0/4) | **PASS** | PyYAML now installed for `python3` (3.14) |
| `lesson-blueprint-status-test` | FAIL (31/0/4) | **PASS** | same |
| `lesson-package-status-test` | FAIL (28/0/2) | **PASS** | same |

No other command changed status, and the 10 remaining failures print the same output as in
REL-1's final run. `--dashboard` and both `validate-all` runs pass (160/0/0 and 79/0/0);
`--dashboard` took 43.0 s.

## Failures that remain

| Cause | Affected commands | REL-2 section |
| --- | --- | --- |
| No launch manifest for `Q1W5` (the launcher self-test asks for a week with no registered manifest) | `canvas-llm-canvas-launch`, `-canvas-launch-approval`, `-canvas-launch-transport` | not in scope |
| Local state / scheduler not readable in the sandbox (`STATE=FAIL`, `SCHEDULER=FAIL`) | `canvas-llm-grade-check-test` | not in scope |
| Homeroom course ID: the test expects 26429, the data says 26427 | `canvas-llm-intake-test` | §2 |
| Validator expects "Homework", the config says "At Home" (`Subject agenda uses Homework label`, `Weekly agenda right column is Homework`) | `canvas-llm-phase-22-canonical-knowledge-test` | §3 |
| The test reads `.local/canvas-llm/approved-course-metadata`, git-ignored local state that exists in the main checkout but not in this worktree (`FAIL missing artifact`) | `canvas-llm-phase-22-predictive-weekly-planning-workstation-test` | not in scope (environment) |
| Committed phase-23 demo data holds absolute `~/Projects/teacher-ai-workstation` paths, so a rebuild in another worktree differs | `canvas-llm-phase-23-weekly-content-production-engine-test` | §5 |
| Port 4310 launcher: the server does not come up for the launcher's `curl` probe in the sandbox | `canvas-planner-launcher-test` | not in scope |
| Week detection: `Q2W3` not found for the pinned date | `teacher-workstation-ui-test` | checked after §1 |

## Full results

Totals: 167 commands, 157 pass, 10 fail.

| Command | Result | Exit | Summary PASS/WARN/FAIL | Secs |
| --- | --- | --- | --- | --- |
| `agents:bash-n-cos` | PASS | 0 |  | 0.0 |
| `agents:agents-governance-status` | PASS | 0 | 47/0/0 | 0.1 |
| `agents:cos--agents-governance-status` | PASS | 0 | 47/0/0 | 0.1 |
| `agents:cursor-workflow-status` | PASS | 0 | 126/0/0 | 0.2 |
| `agents:cos--cursor-workflow-status` | PASS | 0 | 126/0/0 | 0.2 |
| `agents:phase-1-status` | PASS | 0 | 928/0/0 | 1.0 |
| `agents:cos--dashboard` | PASS | 0 | 160/0/0 | 43.0 |
| `agents:cos--whole-system-master-roadmap-status` | PASS | 0 | 106/0/0 | 2.2 |
| `agents:cos--whole-system-coherence-status` | PASS | 0 | 115/0/0 | 0.3 |
| `agents:cos--app-ecosystem-inventory-status` | PASS | 0 | 51/0/0 | 0.2 |
| `validate-all:default` | PASS | 0 | 79/0/0 | 31.8 |
| `validate-all:smoke+phase1` | PASS | 0 | 79/0/0 | 37.5 |
| `sh:3d-builder-workshop-agent-status-test.sh` | PASS | 0 |  | 0.1 |
| `sh:agent-builder-compatibility-governance-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:agents-governance-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:ai-tool-routing-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:app-ecosystem-inventory-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:app-ecosystem-planning-lanes-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:app-runtime-approval-gate-status-test.sh` | PASS | 0 |  | 0.8 |
| `sh:artifact-quality-preflight-test.sh` | PASS | 0 |  | 11.9 |
| `sh:artifact-quality-status-test.sh` | PASS | 0 |  | 3.1 |
| `sh:autonomous-build-engine-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:backlog-non-mutation-guardrails-test.sh` | PASS | 0 |  | 3.0 |
| `sh:canvas-llm-approval-queue-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-artifact-health-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-assignment-draft-generator-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-assignment-preflight-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-canvas-connector-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-canvas-dashboard-test.sh` | PASS | 0 |  | 0.5 |
| `sh:canvas-llm-canvas-drift-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-canvas-launch-approval-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-canvas-launch-inventory-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-canvas-launch-live-gating-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-llm-canvas-launch-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-canvas-launch-transport-test.sh` | FAIL | 1 |  | 0.3 |
| `sh:canvas-llm-canvas-operations-test.sh` | PASS | 0 |  | 0.5 |
| `sh:canvas-llm-cleanup-safety-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-communication-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-deploy-test.sh` | PASS | 0 |  | 0.5 |
| `sh:canvas-llm-deployment-audit-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-deployment-readiness-test.sh` | PASS | 0 |  | 0.6 |
| `sh:canvas-llm-duplicate-detection-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-grade-check-test.sh` | FAIL | 1 |  | 0.3 |
| `sh:canvas-llm-homework-rules-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-intake-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-live-canvas-transport-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-live-q1w2-deployment-test.sh` | PASS | 0 |  | 0.7 |
| `sh:canvas-llm-live-transport-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-pacing-parser-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-pacing-translation-and-reminders-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-phase-18a-canonical-weekly-plan-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-llm-phase-18b-weekly-plan-integration-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-llm-phase-18c-preview-assembly-test.sh` | PASS | 0 |  | 0.9 |
| `sh:canvas-llm-phase-18d-write-readiness-dry-run-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-phase-18e-owner-policy-execution-preconditions-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-phase-22-canonical-knowledge-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-phase-22-predictive-weekly-planning-workstation-test.sh` | FAIL | 1 |  | 0.3 |
| `sh:canvas-llm-phase-23-weekly-content-production-engine-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-phase-24-predictive-teacher-brain-test.sh` | PASS | 0 |  | 0.6 |
| `sh:canvas-llm-phase-25-curriculum-source-intelligence-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-phase-26-unified-weekly-production-workstation-test.sh` | PASS | 0 |  | 0.6 |
| `sh:canvas-llm-phase-27-canvas-readiness-and-safety-diff-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-repair-detection-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-sandbox-connector-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-teacher-decisions-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-weekly-agenda-publisher-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-weekly-deployment-center-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-weekly-guardrails-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-page-identity-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-planner-launcher-test.sh` | FAIL | 1 |  | 17.1 |
| `sh:chief-of-staff-daily-operations-test.sh` | PASS | 0 |  | 0.3 |
| `sh:chief-of-staff-dashboard-hardening-test.sh` | PASS | 0 |  | 14.4 |
| `sh:chief-of-staff-next-action-test.sh` | PASS | 0 |  | 0.1 |
| `sh:chief-of-staff-v1-operating-test.sh` | PASS | 0 |  | 34.2 |
| `sh:classroom-app-lab-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:classroom-timer-stopwatch-planning-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:classroom-timer-stopwatch-runtime-static-safety-test.sh` | PASS | 0 |  | 0.1 |
| `sh:classroom-timer-stopwatch-runtime-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:classroom-utility-templates-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:curriculum-binding-v0-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-contract-schemas-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-production-registry-empty-file-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-builder-production-registry-first-record-status-test.sh` | PASS | 0 |  | 0.7 |
| `sh:curriculum-builder-production-registry-first-record-validate-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-builder-production-registry-governance-guardrails-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-production-registry-governance-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:curriculum-builder-production-registry-metadata-boundary-status-test.sh` | PASS | 0 |  | 0.7 |
| `sh:curriculum-builder-production-registry-metadata-pilot-plan-status-test.sh` | PASS | 0 |  | 0.6 |
| `sh:curriculum-builder-production-registry-next-gate-status-test.sh` | PASS | 0 |  | 0.6 |
| `sh:curriculum-builder-production-registry-owen-checklist-status-test.sh` | PASS | 0 |  | 0.7 |
| `sh:curriculum-builder-production-registry-phase-2-preflight-status-test.sh` | PASS | 0 |  | 0.6 |
| `sh:curriculum-builder-production-registry-planning-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:curriculum-builder-registry-a4-a7-fixture-schema-status-test.sh` | PASS | 0 |  | 1.1 |
| `sh:curriculum-builder-registry-lane-status-test.sh` | PASS | 0 |  | 18.8 |
| `sh:curriculum-builder-registry-v0-2-dry-run-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-builder-registry-v0-2-local-records-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-registry-v0-2-renderer-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-registry-v0-2-retrieval-test.sh` | PASS | 0 |  | 0.4 |
| `sh:curriculum-builder-registry-v0-2-status-test.sh` | PASS | 0 |  | 0.6 |
| `sh:curriculum-canvas-package-contract-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-contract-suite-v0-test.sh` | PASS | 0 |  | 2.0 |
| `sh:curriculum-library-foundation-status-test.sh` | PASS | 0 |  | 0.7 |
| `sh:curriculum-output-contract-v0-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-production-status-test.sh` | PASS | 0 |  | 0.6 |
| `sh:curriculum-registry-v0-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-review-game-contract-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-source-readiness-status-test.sh` | PASS | 0 |  | 2.1 |
| `sh:curriculum-teacher-script-contract-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-worksheet-contract-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:cursor-operating-modes-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:gemini-discovery-classification-intake-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:governance-lane-status-test.sh` | PASS | 0 |  | 1.2 |
| `sh:lane-review-hardening-guardrails-test.sh` | PASS | 0 |  | 10.9 |
| `sh:lesson-blueprint-status-test.sh` | PASS | 0 |  | 0.7 |
| `sh:lesson-package-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:local-llm-workstation-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:lovable-classroom-app-builder-status-test.sh` | PASS | 0 |  | 0.1 |
| `sh:mac-workstation-experience-status-test.sh` | PASS | 0 |  | 0.1 |
| `sh:markdown-frontmatter-planning-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:owen-architecture-decision-packets-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:presentation-engine-renderer-foundation-status-test.sh` | PASS | 0 |  | 0.8 |
| `sh:q2w3-live-refresh-regression-test.sh` | PASS | 0 |  | 0.1 |
| `sh:smoke-chief-of-staff-cli-boundary-test.sh` | PASS | 0 |  | 0.0 |
| `sh:smoke-chief-of-staff-cli.sh` | PASS | 0 |  | 2.0 |
| `sh:teacher-knowledge-vault-m0-architecture-freeze-status-test.sh` | PASS | 0 |  | 1.3 |
| `sh:teacher-knowledge-vault-m1-fake-catalog-status-test.sh` | PASS | 0 |  | 2.9 |
| `sh:teacher-knowledge-vault-m2-local-discovery-approval-status-test.sh` | PASS | 0 |  | 5.1 |
| `sh:teacher-knowledge-vault-m2b-repo-staging-metadata-discovery-test.sh` | PASS | 0 |  | 0.5 |
| `sh:teacher-knowledge-vault-m2b-repo-staging-metadata-status-test.sh` | PASS | 0 |  | 6.8 |
| `sh:teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status-test.sh` | PASS | 0 |  | 7.5 |
| `sh:teacher-knowledge-vault-m2d-selected-folder-metadata-scan-test.sh` | PASS | 0 |  | 0.3 |
| `sh:teacher-knowledge-vault-m2d-selected-folder-preflight-test.sh` | PASS | 0 |  | 0.2 |
| `sh:teacher-knowledge-vault-m2d-selected-folder-status-test.sh` | PASS | 0 |  | 2.5 |
| `sh:teacher-knowledge-vault-m3-fake-duplicate-search-status-test.sh` | PASS | 0 |  | 5.2 |
| `sh:teacher-knowledge-vault-m4-smart-rename-status-test.sh` | PASS | 0 |  | 5.3 |
| `sh:teacher-knowledge-vault-m5-organization-rollback-status-test.sh` | PASS | 0 |  | 5.6 |
| `sh:teacher-knowledge-vault-m6-extraction-ocr-approval-status-test.sh` | PASS | 0 |  | 6.8 |
| `sh:teacher-knowledge-vault-m7-connector-approval-status-test.sh` | PASS | 0 |  | 7.6 |
| `sh:teacher-knowledge-vault-m7b-manual-source-inventory-status-test.sh` | PASS | 0 |  | 8.3 |
| `sh:teacher-knowledge-vault-m7c-manual-inventory-import-preview-status-test.sh` | PASS | 0 |  | 9.0 |
| `sh:teacher-knowledge-vault-m7d-runtime-import-approval-gate-status-test.sh` | PASS | 0 |  | 10.0 |
| `sh:teacher-knowledge-vault-m7e-local-test-catalog-import-test.sh` | PASS | 0 |  | 0.2 |
| `sh:teacher-knowledge-vault-m7e-local-test-catalog-status-test.sh` | PASS | 0 |  | 10.7 |
| `sh:teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status-test.sh` | PASS | 0 |  | 11.4 |
| `sh:teacher-knowledge-vault-m7g-persistent-working-catalog-import-test.sh` | PASS | 0 |  | 0.3 |
| `sh:teacher-knowledge-vault-m7g-persistent-working-catalog-status-test.sh` | PASS | 0 |  | 17.8 |
| `sh:teacher-workstation-health-monitor-test.sh` | PASS | 0 |  | 14.3 |
| `sh:teacher-workstation-system-updater-test.sh` | PASS | 0 |  | 0.4 |
| `sh:teacher-workstation-ui-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:validation-performance-boundary-test.sh` | PASS | 0 |  | 0.4 |
| `sh:vibe-wallpaper-widgets-planning-status-test.sh` | PASS | 0 |  | 0.8 |
| `sh:whole-system-coherence-status-test.sh` | PASS | 0 |  | 0.6 |
| `sh:whole-system-master-roadmap-status-test.sh` | PASS | 0 |  | 5.6 |
| `sh:widget-shortcut-builder-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:workstation-ops-lane-status-test.sh` | PASS | 0 |  | 18.3 |
| `py:canvas-html-compatibility-test.py` | PASS | 0 |  | 0.0 |
| `py:canvas-llm-mastery-fixtures-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-mastery-hardening-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-announcement-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-math-translation-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-pacing-translation-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-reading-spelling-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-shurley-science-history-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-weekly-loop-test.py` | PASS | 0 |  | 0.1 |
| `unittest:artifact_quality` | PASS | 0 |  | 8.5 |
| `unittest:curriculum_production` | PASS | 0 |  | 0.1 |
| `unittest:lesson_blueprint` | PASS | 0 |  | 0.1 |
