# MERGE-1 Baseline — `main` before the Chief merge

```text
Branch: integrate/cos-into-main
HEAD under test: 8279bcb (= origin/main 0609599 + docs/prompts/PROMPT-MERGE-1.md only)
Date: 2026-10-18
Runner: one command at a time, 10-minute cap per command, python3.12
Environment: Claude Code D1.1 sandbox (no network, no Ollama, ~/.teacher-ai-workstation unreadable)
```

## What was run

Sources for the command list: `AGENTS.md` § Validation Commands (minimum and broader proof),
`scripts/chief-of-staff-validate-all.sh` (default and with `COS_VALIDATE_INCLUDE_SMOKE=1
COS_VALIDATE_INCLUDE_PHASE1=1`), and every test in `tests/`:

- `bash tests/*.sh` (each file individually)
- `python3.12 tests/*.py` (each file individually)
- `python3.12 -m unittest discover -s tests/<dir> -p "test_*.py"` for
  `artifact_quality`, `curriculum_production`, `lesson_blueprint`

Sandbox note: macOS `mktemp` with no template ignores `$TMPDIR` and writes to
`/var/folders/...`, which the sandbox blocks. The run puts a small `mktemp` shim first on
`PATH` that adds a `$TMPDIR` template; it changes nothing in the repo. Without the shim, 9
more tests fail on `mkstemp ... Operation not permitted` (44 failures instead of 35). The
after-merge run uses the same shim.

## Failures that already exist on `main` (recorded, not fixed)

| Cause | Affected commands |
| --- | --- |
| `apps/` holds five runtime apps (`teacher-workstation`, `phase23-teacher-workspace`, `predictive-weekly-planning`, `unified-weekly-production`, `weekly-content-production`) that the app-runtime and timer gates do not allow | `app-runtime-approval-gate-status-test`, `classroom-timer-stopwatch-runtime-status-test`, `whole-system-master-roadmap-status-test`, `bin/chief-of-staff --dashboard`, `--whole-system-master-roadmap-status`, both `validate-all` runs, `chief-of-staff-v1-operating-test` |
| Date-dependent: today (2026-10-18) is past the planned weeks; `select_startup_week` compares `None > str`, or no manifest exists for the computed week (Q1W5), or Q2W3 detection differs | `canvas-llm-approval-queue`, `-artifact-health`, `-assignment-draft-generator`, `-canvas-dashboard`, `-canvas-operations`, `-deployment-readiness`, `-pacing-parser`, `-teacher-decisions`, `-weekly-agenda-publisher`, `-canvas-launch`, `-canvas-launch-approval`, `-canvas-launch-transport`, `-intake`, `-phase-22-*`, `-phase-23-*`, `teacher-workstation-ui-test` |
| Local state/scheduler not readable in sandbox (`STATE=FAIL`, `SCHEDULER=FAIL`) | `canvas-llm-grade-check-test` |
| Port 4310 / launcher behavior in sandbox | `canvas-planner-launcher-test` |
| Python modules not installed for python3.12: `fitz` (PyMuPDF) for artifact quality; `yaml` (PyYAML) for curriculum production, so YAML catalogs fall back to `json.loads` and raise `JSONDecodeError` | `artifact-quality-*`, `unittest:artifact_quality`, `unittest:curriculum_production`, `unittest:lesson_blueprint`, `lesson-blueprint-status-test`, `lesson-package-status-test`, `curriculum-production-status-test` |

## Full results

Totals: 167 commands, 132 pass, 35 fail.

| Command | Result | Exit | Summary PASS/WARN/FAIL | Secs |
| --- | --- | --- | --- | --- |
| `agents:bash-n-cos` | PASS | 0 |  | 0.0 |
| `agents:agents-governance-status` | PASS | 0 | 47/0/0 | 0.1 |
| `agents:cos--agents-governance-status` | PASS | 0 | 47/0/0 | 0.2 |
| `agents:cursor-workflow-status` | PASS | 0 | 126/0/0 | 0.3 |
| `agents:cos--cursor-workflow-status` | PASS | 0 | 126/0/0 | 0.3 |
| `agents:phase-1-status` | PASS | 0 | 928/0/0 | 1.3 |
| `agents:cos--dashboard` | FAIL | 2 | 157/0/3 | 61.4 |
| `agents:cos--whole-system-master-roadmap-status` | FAIL | 1 | 104/0/2 | 2.9 |
| `agents:cos--whole-system-coherence-status` | PASS | 0 | 115/0/0 | 0.3 |
| `agents:cos--app-ecosystem-inventory-status` | PASS | 0 | 51/0/0 | 0.3 |
| `validate-all:default` | FAIL | 1 | 76/0/3 | 39.5 |
| `validate-all:smoke+phase1` | FAIL | 1 | 76/0/3 | 39.8 |
| `sh:3d-builder-workshop-agent-status-test.sh` | PASS | 0 |  | 0.1 |
| `sh:agent-builder-compatibility-governance-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:agents-governance-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:ai-tool-routing-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:app-ecosystem-inventory-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:app-ecosystem-planning-lanes-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:app-runtime-approval-gate-status-test.sh` | FAIL | 1 | 53/0/5 | 0.2 |
| `sh:artifact-quality-preflight-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:artifact-quality-status-test.sh` | FAIL | 1 | 53/0/13 | 0.4 |
| `sh:autonomous-build-engine-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:backlog-non-mutation-guardrails-test.sh` | PASS | 0 |  | 2.7 |
| `sh:canvas-llm-approval-queue-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-artifact-health-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-assignment-draft-generator-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-assignment-preflight-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-canvas-connector-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-canvas-dashboard-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-canvas-drift-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-canvas-launch-approval-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-canvas-launch-inventory-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-canvas-launch-live-gating-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-llm-canvas-launch-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-canvas-launch-transport-test.sh` | FAIL | 1 |  | 0.3 |
| `sh:canvas-llm-canvas-operations-test.sh` | FAIL | 1 |  | 0.3 |
| `sh:canvas-llm-cleanup-safety-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-communication-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-deploy-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-deployment-audit-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-deployment-readiness-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-duplicate-detection-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-grade-check-test.sh` | FAIL | 1 |  | 0.3 |
| `sh:canvas-llm-homework-rules-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-intake-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-live-canvas-transport-test.sh` | PASS | 0 |  | 0.4 |
| `sh:canvas-llm-live-q1w2-deployment-test.sh` | PASS | 0 |  | 0.7 |
| `sh:canvas-llm-live-transport-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-pacing-parser-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-pacing-translation-and-reminders-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-llm-phase-18a-canonical-weekly-plan-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-llm-phase-18b-weekly-plan-integration-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-llm-phase-18c-preview-assembly-test.sh` | PASS | 0 |  | 1.0 |
| `sh:canvas-llm-phase-18d-write-readiness-dry-run-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-phase-18e-owner-policy-execution-preconditions-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-phase-22-canonical-knowledge-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:canvas-llm-phase-22-predictive-weekly-planning-workstation-test.sh` | FAIL | 1 |  | 0.3 |
| `sh:canvas-llm-phase-23-weekly-content-production-engine-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-phase-24-predictive-teacher-brain-test.sh` | PASS | 0 |  | 0.7 |
| `sh:canvas-llm-phase-25-curriculum-source-intelligence-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-phase-26-unified-weekly-production-workstation-test.sh` | PASS | 0 |  | 0.6 |
| `sh:canvas-llm-phase-27-canvas-readiness-and-safety-diff-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-repair-detection-test.sh` | PASS | 0 |  | 0.3 |
| `sh:canvas-llm-sandbox-connector-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-teacher-decisions-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-weekly-agenda-publisher-test.sh` | FAIL | 1 |  | 0.2 |
| `sh:canvas-llm-weekly-deployment-center-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-llm-weekly-guardrails-test.sh` | PASS | 0 |  | 0.1 |
| `sh:canvas-page-identity-test.sh` | PASS | 0 |  | 0.2 |
| `sh:canvas-planner-launcher-test.sh` | FAIL | 1 |  | 34.7 |
| `sh:chief-of-staff-daily-operations-test.sh` | PASS | 0 |  | 0.2 |
| `sh:chief-of-staff-dashboard-hardening-test.sh` | PASS | 0 |  | 8.3 |
| `sh:chief-of-staff-next-action-test.sh` | PASS | 0 |  | 0.1 |
| `sh:chief-of-staff-v1-operating-test.sh` | FAIL | 1 | 76/0/3 | 31.6 |
| `sh:classroom-app-lab-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:classroom-timer-stopwatch-planning-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:classroom-timer-stopwatch-runtime-static-safety-test.sh` | PASS | 0 |  | 0.1 |
| `sh:classroom-timer-stopwatch-runtime-status-test.sh` | FAIL | 1 | 75/0/5 | 0.2 |
| `sh:classroom-utility-templates-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:curriculum-binding-v0-test.sh` | PASS | 0 |  | 0.4 |
| `sh:curriculum-builder-contract-schemas-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-production-registry-empty-file-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-builder-production-registry-first-record-status-test.sh` | PASS | 0 |  | 0.7 |
| `sh:curriculum-builder-production-registry-first-record-validate-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-builder-production-registry-governance-guardrails-test.sh` | PASS | 0 |  | 0.4 |
| `sh:curriculum-builder-production-registry-governance-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-production-registry-metadata-boundary-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:curriculum-builder-production-registry-metadata-pilot-plan-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-production-registry-next-gate-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-production-registry-owen-checklist-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-production-registry-phase-2-preflight-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-production-registry-planning-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-registry-a4-a7-fixture-schema-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:curriculum-builder-registry-lane-status-test.sh` | PASS | 0 |  | 10.6 |
| `sh:curriculum-builder-registry-v0-2-dry-run-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-builder-registry-v0-2-local-records-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-builder-registry-v0-2-renderer-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-builder-registry-v0-2-retrieval-test.sh` | PASS | 0 |  | 0.4 |
| `sh:curriculum-builder-registry-v0-2-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:curriculum-canvas-package-contract-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-contract-suite-v0-test.sh` | PASS | 0 |  | 1.5 |
| `sh:curriculum-library-foundation-status-test.sh` | PASS | 0 |  | 0.6 |
| `sh:curriculum-output-contract-v0-test.sh` | PASS | 0 |  | 0.3 |
| `sh:curriculum-production-status-test.sh` | FAIL | 1 | 25/0/4 | 0.2 |
| `sh:curriculum-registry-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-review-game-contract-v0-test.sh` | PASS | 0 |  | 0.1 |
| `sh:curriculum-source-readiness-status-test.sh` | PASS | 0 |  | 1.5 |
| `sh:curriculum-teacher-script-contract-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:curriculum-worksheet-contract-v0-test.sh` | PASS | 0 |  | 0.2 |
| `sh:cursor-operating-modes-status-test.sh` | PASS | 0 |  | 0.4 |
| `sh:gemini-discovery-classification-intake-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:governance-lane-status-test.sh` | PASS | 0 |  | 1.0 |
| `sh:lane-review-hardening-guardrails-test.sh` | PASS | 0 |  | 9.2 |
| `sh:lesson-blueprint-status-test.sh` | FAIL | 1 | 31/0/4 | 0.3 |
| `sh:lesson-package-status-test.sh` | FAIL | 1 | 28/0/2 | 0.2 |
| `sh:local-llm-workstation-status-test.sh` | PASS | 0 |  | 0.1 |
| `sh:lovable-classroom-app-builder-status-test.sh` | PASS | 0 |  | 0.1 |
| `sh:mac-workstation-experience-status-test.sh` | PASS | 0 |  | 0.2 |
| `sh:markdown-frontmatter-planning-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:owen-architecture-decision-packets-status-test.sh` | PASS | 0 |  | 0.3 |
| `sh:presentation-engine-renderer-foundation-status-test.sh` | PASS | 0 |  | 0.6 |
| `sh:q2w3-live-refresh-regression-test.sh` | PASS | 0 |  | 0.1 |
| `sh:smoke-chief-of-staff-cli-boundary-test.sh` | PASS | 0 |  | 0.0 |
| `sh:smoke-chief-of-staff-cli.sh` | PASS | 0 |  | 1.6 |
| `sh:teacher-knowledge-vault-m0-architecture-freeze-status-test.sh` | PASS | 0 |  | 1.0 |
| `sh:teacher-knowledge-vault-m1-fake-catalog-status-test.sh` | PASS | 0 |  | 2.4 |
| `sh:teacher-knowledge-vault-m2-local-discovery-approval-status-test.sh` | PASS | 0 |  | 2.9 |
| `sh:teacher-knowledge-vault-m2b-repo-staging-metadata-discovery-test.sh` | PASS | 0 |  | 0.3 |
| `sh:teacher-knowledge-vault-m2b-repo-staging-metadata-status-test.sh` | PASS | 0 |  | 4.2 |
| `sh:teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status-test.sh` | PASS | 0 |  | 5.3 |
| `sh:teacher-knowledge-vault-m2d-selected-folder-metadata-scan-test.sh` | PASS | 0 |  | 0.2 |
| `sh:teacher-knowledge-vault-m2d-selected-folder-preflight-test.sh` | PASS | 0 |  | 0.1 |
| `sh:teacher-knowledge-vault-m2d-selected-folder-status-test.sh` | PASS | 0 |  | 1.6 |
| `sh:teacher-knowledge-vault-m3-fake-duplicate-search-status-test.sh` | PASS | 0 |  | 3.7 |
| `sh:teacher-knowledge-vault-m4-smart-rename-status-test.sh` | PASS | 0 |  | 4.2 |
| `sh:teacher-knowledge-vault-m5-organization-rollback-status-test.sh` | PASS | 0 |  | 5.0 |
| `sh:teacher-knowledge-vault-m6-extraction-ocr-approval-status-test.sh` | PASS | 0 |  | 6.1 |
| `sh:teacher-knowledge-vault-m7-connector-approval-status-test.sh` | PASS | 0 |  | 7.3 |
| `sh:teacher-knowledge-vault-m7b-manual-source-inventory-status-test.sh` | PASS | 0 |  | 7.6 |
| `sh:teacher-knowledge-vault-m7c-manual-inventory-import-preview-status-test.sh` | PASS | 0 |  | 9.0 |
| `sh:teacher-knowledge-vault-m7d-runtime-import-approval-gate-status-test.sh` | PASS | 0 |  | 9.8 |
| `sh:teacher-knowledge-vault-m7e-local-test-catalog-import-test.sh` | PASS | 0 |  | 0.2 |
| `sh:teacher-knowledge-vault-m7e-local-test-catalog-status-test.sh` | PASS | 0 |  | 9.9 |
| `sh:teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status-test.sh` | PASS | 0 |  | 10.5 |
| `sh:teacher-knowledge-vault-m7g-persistent-working-catalog-import-test.sh` | PASS | 0 |  | 0.3 |
| `sh:teacher-knowledge-vault-m7g-persistent-working-catalog-status-test.sh` | PASS | 0 |  | 10.8 |
| `sh:teacher-workstation-health-monitor-test.sh` | PASS | 0 |  | 12.7 |
| `sh:teacher-workstation-system-updater-test.sh` | PASS | 0 |  | 0.4 |
| `sh:teacher-workstation-ui-test.sh` | FAIL | 1 |  | 0.1 |
| `sh:validation-performance-boundary-test.sh` | PASS | 0 |  | 0.4 |
| `sh:vibe-wallpaper-widgets-planning-status-test.sh` | PASS | 0 |  | 0.7 |
| `sh:whole-system-coherence-status-test.sh` | PASS | 0 |  | 0.5 |
| `sh:whole-system-master-roadmap-status-test.sh` | FAIL | 1 | 104/0/2 | 2.2 |
| `sh:widget-shortcut-builder-status-test.sh` | PASS | 0 |  | 0.1 |
| `sh:workstation-ops-lane-status-test.sh` | PASS | 0 |  | 13.5 |
| `py:canvas-html-compatibility-test.py` | PASS | 0 |  | 0.0 |
| `py:canvas-llm-mastery-fixtures-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-mastery-hardening-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-announcement-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-math-translation-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-pacing-translation-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-reading-spelling-test.py` | PASS | 0 |  | 0.1 |
| `py:canvas-llm-phase-3-shurley-science-history-test.py` | PASS | 0 |  | 0.0 |
| `py:canvas-llm-phase-3-weekly-loop-test.py` | PASS | 0 |  | 0.1 |
| `unittest:artifact_quality` | FAIL | 1 |  | 0.1 |
| `unittest:curriculum_production` | FAIL | 1 |  | 0.1 |
| `unittest:lesson_blueprint` | FAIL | 1 |  | 0.1 |
