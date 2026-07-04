#!/usr/bin/env bash
# CLI smoke tests. Must never call proof-run, validate-all, or operating tests.
#
# COS_SMOKE_ALREADY_RUNNING: set internally; nested smoke fails immediately.
set -euo pipefail

if [[ -n "${COS_SMOKE_ALREADY_RUNNING:-}" ]]; then
  echo "FAIL: recursive smoke-chief-of-staff-cli.sh detected"
  exit 1
fi
export COS_SMOKE_ALREADY_RUNNING=1

echo "Running Chief of Staff CLI smoke tests..."

raw_intake_test_file="assistant/intake/raw/smoke-test-context.md"
cleanup() {
  rm -f "${raw_intake_test_file}"
}
trap cleanup EXIT
printf '%s\n' "sample raw intake test file" > "${raw_intake_test_file}"

bin/chief-of-staff --help >/dev/null
bin/chief-of-staff --version >/dev/null
bin/chief-of-staff --status >/dev/null
bin/chief-of-staff --list-workflows >/dev/null
bin/chief-of-staff --show-context --workflow request-training-materials >/dev/null
bin/chief-of-staff --workflow request-training-materials --question "What do you need from me?" --dry-run >/dev/null
bin/chief-of-staff --workflow request-training-materials --question "What do you need from me?" --dry-run > /tmp/chief-of-staff-dry-run.txt
grep -q '^---$' /tmp/chief-of-staff-dry-run.txt
grep -q "SOURCE: assistant/chief-of-staff.md" /tmp/chief-of-staff-dry-run.txt
if grep -q "## SOURCE:" /tmp/chief-of-staff-dry-run.txt; then
  echo "FAIL: dry-run prompt should not contain heading-style source markers"
  exit 1
fi
bin/chief-of-staff --workflow project-review --context examples/sample-project-note.md --question "What is the next action?" --dry-run >/dev/null
bin/chief-of-staff --workflow project-review --context examples/sample-project-note.md --question "What is the next action?" --no-model > /tmp/chief-of-staff-prompt.txt
bin/chief-of-staff --workflow project-review --include-memory --question "test" --dry-run >/dev/null
bin/chief-of-staff --workflow project-review --include-project-memory --question "test" --dry-run >/dev/null
bin/chief-of-staff --workflow project-review --include-writing-style-memory --question "test" --dry-run >/dev/null
bin/chief-of-staff --show-context --workflow project-review --include-memory > /tmp/chief-of-staff-show-context.txt
grep -q "assistant/memory/projects.md" /tmp/chief-of-staff-show-context.txt
bin/chief-of-staff --workflow project-review --question "test" --dry-run > /tmp/chief-of-staff-no-memory.txt
if grep -q "SOURCE: assistant/memory/projects.md" /tmp/chief-of-staff-no-memory.txt; then
  echo "FAIL: normal dry-run should not include memory"
  exit 1
fi
bin/chief-of-staff --workflow project-review --include-memory --question "test" --dry-run > /tmp/chief-of-staff-memory.txt
grep -q "SOURCE: assistant/memory/projects.md" /tmp/chief-of-staff-memory.txt
if grep -q "SOURCE: assistant/memory/memory-review-checklist.md" /tmp/chief-of-staff-memory.txt; then
  echo "FAIL: memory-review-checklist.md should not be auto-included"
  exit 1
fi
if grep -q "SOURCE: assistant/memory/memory-log.md" /tmp/chief-of-staff-memory.txt; then
  echo "FAIL: memory-log.md should not be auto-included"
  exit 1
fi
bin/chief-of-staff --memory-status >/dev/null
bin/chief-of-staff --validate-memory >/dev/null
bash scripts/lesson-planning-template-readiness-status.sh > /tmp/chief-of-staff-lesson-template-readiness-script.txt
grep -q "Placeholder Registry Checks" /tmp/chief-of-staff-lesson-template-readiness-script.txt
grep -q "PASS: placeholder registry safety contract is intact" /tmp/chief-of-staff-lesson-template-readiness-script.txt
grep -q '^WARN: 0$' /tmp/chief-of-staff-lesson-template-readiness-script.txt
grep -q '^FAIL: 0$' /tmp/chief-of-staff-lesson-template-readiness-script.txt
bin/chief-of-staff --lesson-planning-template-readiness-status > /tmp/chief-of-staff-lesson-template-readiness.txt
grep -q "Placeholder Registry Checks" /tmp/chief-of-staff-lesson-template-readiness.txt
grep -q "PASS: placeholder registry safety contract is intact" /tmp/chief-of-staff-lesson-template-readiness.txt
bin/chief-of-staff --curriculum-registry-v0-status >/dev/null
bin/chief-of-staff --curriculum-registry-v0-validate >/dev/null
bash tests/curriculum-registry-v0-test.sh >/dev/null
bin/chief-of-staff --curriculum-output-contract-v0-status >/dev/null
bin/chief-of-staff --curriculum-output-contract-v0-validate >/dev/null
bash tests/curriculum-output-contract-v0-test.sh >/dev/null
bin/chief-of-staff --curriculum-binding-v0-status >/dev/null
bin/chief-of-staff --curriculum-binding-v0-validate >/dev/null
bin/chief-of-staff --curriculum-binding-v0-lookup sample-sm5-textbook-001 >/dev/null
bash tests/curriculum-binding-v0-test.sh >/dev/null
bash tests/curriculum-teacher-script-contract-v0-test.sh >/dev/null
bash tests/curriculum-worksheet-contract-v0-test.sh >/dev/null
bash tests/curriculum-review-game-contract-v0-test.sh >/dev/null
bash tests/curriculum-canvas-package-contract-v0-test.sh >/dev/null
bash tests/curriculum-contract-suite-v0-test.sh >/dev/null
bash tests/chief-of-staff-next-action-test.sh >/dev/null
bin/chief-of-staff --chief-of-staff-command-index-v1-status >/dev/null
bin/chief-of-staff --chief-of-staff-v1-status >/dev/null
bin/chief-of-staff --commands >/dev/null
bin/chief-of-staff --daily-status >/dev/null
bin/chief-of-staff --closeout >/dev/null
bin/chief-of-staff --approval-queue >/dev/null
bin/chief-of-staff --blocker-queue >/dev/null
bin/chief-of-staff --mode-status >/dev/null
bin/chief-of-staff --system-health >/dev/null
bin/chief-of-staff --workstation-health >/dev/null
bin/chief-of-staff --system-update-check >/dev/null
bin/chief-of-staff --system-update-plan >/dev/null
bin/chief-of-staff --model-routing-status >/dev/null
bin/chief-of-staff --local-llm-workstation-status >/dev/null
bin/chief-of-staff --mac-workstation-status >/dev/null
bin/chief-of-staff --widget-shortcut-status >/dev/null
bin/chief-of-staff --classroom-app-lab-status >/dev/null
bin/chief-of-staff --lovable-status >/dev/null
bin/chief-of-staff --3d-builder-status >/dev/null
bin/chief-of-staff --curriculum-contracts-status >/dev/null
bash tests/curriculum-builder-contract-schemas-status-test.sh >/dev/null
bin/chief-of-staff --curriculum-registry-dry-run-status >/dev/null
bash scripts/curriculum-builder-registry-v0-2-dry-run.sh >/dev/null
bash tests/curriculum-builder-registry-v0-2-dry-run-test.sh >/dev/null
bash tests/curriculum-builder-registry-v0-2-status-test.sh >/dev/null
bin/chief-of-staff --curriculum-registry-records-status >/dev/null
bash scripts/curriculum-builder-registry-v0-2-local-records-validate.sh >/dev/null
bash tests/curriculum-builder-registry-v0-2-local-records-test.sh >/dev/null
bin/chief-of-staff --curriculum-registry-renderer-status >/dev/null
bash scripts/curriculum-builder-registry-v0-2-render-preview.sh >/dev/null
bash tests/curriculum-builder-registry-v0-2-renderer-test.sh >/dev/null
bin/chief-of-staff --curriculum-registry-retrieval-status >/dev/null
bash scripts/curriculum-builder-registry-v0-2-retrieval-check.sh >/dev/null
bash tests/curriculum-builder-registry-v0-2-retrieval-test.sh >/dev/null
bin/chief-of-staff --curriculum-production-registry-planning-status >/dev/null
bash tests/curriculum-builder-production-registry-planning-status-test.sh >/dev/null
bin/chief-of-staff --curriculum-production-registry-owen-checklist-status >/dev/null
bash tests/curriculum-builder-production-registry-owen-checklist-status-test.sh >/dev/null
bin/chief-of-staff --curriculum-production-registry-governance-status >/dev/null
bash tests/curriculum-builder-production-registry-governance-status-test.sh >/dev/null
bash tests/curriculum-builder-production-registry-governance-guardrails-test.sh >/dev/null
bin/chief-of-staff --curriculum-production-registry-phase-2-preflight-status >/dev/null
bash tests/curriculum-builder-production-registry-phase-2-preflight-status-test.sh >/dev/null
bin/chief-of-staff --curriculum-production-registry-metadata-boundary-status >/dev/null
bash tests/curriculum-builder-production-registry-metadata-boundary-status-test.sh >/dev/null
bin/chief-of-staff --curriculum-production-registry-empty-file-status >/dev/null
bash tests/curriculum-builder-production-registry-empty-file-status-test.sh >/dev/null
bin/chief-of-staff --curriculum-production-registry-metadata-pilot-plan-status >/dev/null
bash tests/curriculum-builder-production-registry-metadata-pilot-plan-status-test.sh >/dev/null
bin/chief-of-staff --curriculum-production-registry-first-record-status >/dev/null
bash tests/curriculum-builder-production-registry-first-record-status-test.sh >/dev/null
bin/chief-of-staff --curriculum-production-registry-next-gate-status >/dev/null
bash tests/curriculum-builder-production-registry-next-gate-status-test.sh >/dev/null
bash tests/curriculum-builder-production-registry-first-record-validate-test.sh >/dev/null
bin/chief-of-staff --curriculum-source-readiness-status >/dev/null
bash tests/curriculum-source-readiness-status-test.sh >/dev/null
bin/chief-of-staff --curriculum-registry-lane-status >/dev/null
bash tests/curriculum-builder-registry-lane-status-test.sh >/dev/null
bin/chief-of-staff --curriculum-registry-a4-a7-fixture-schema-status >/dev/null
bash tests/curriculum-builder-registry-a4-a7-fixture-schema-status-test.sh >/dev/null
bin/chief-of-staff --cursor-operating-modes-status >/dev/null
bin/chief-of-staff --autonomous-build-engine-status >/dev/null
bash tests/autonomous-build-engine-status-test.sh >/dev/null
bin/chief-of-staff --governance-lane-status >/dev/null
bash tests/governance-lane-status-test.sh >/dev/null
bin/chief-of-staff --whole-system-master-roadmap-status >/dev/null
bash tests/whole-system-master-roadmap-status-test.sh >/dev/null
bin/chief-of-staff --whole-system-coherence-status >/dev/null
bash tests/whole-system-coherence-status-test.sh >/dev/null
bin/chief-of-staff --agent-builder-compatibility-governance-status >/dev/null
bash tests/agent-builder-compatibility-governance-status-test.sh >/dev/null
bin/chief-of-staff --owen-architecture-decision-packets-status >/dev/null
bash tests/owen-architecture-decision-packets-status-test.sh >/dev/null
bin/chief-of-staff --app-ecosystem-inventory-status >/dev/null
bash tests/app-ecosystem-inventory-status-test.sh >/dev/null
bin/chief-of-staff --classroom-timer-stopwatch-planning-status >/dev/null
bash tests/classroom-timer-stopwatch-planning-status-test.sh >/dev/null
bin/chief-of-staff --app-ecosystem-planning-lanes-status >/dev/null
bash tests/app-ecosystem-planning-lanes-status-test.sh >/dev/null
bin/chief-of-staff --presentation-engine-renderer-foundation-status >/dev/null
bash tests/presentation-engine-renderer-foundation-status-test.sh >/dev/null
bin/chief-of-staff --gemini-discovery-classification-intake-status >/dev/null
bash tests/gemini-discovery-classification-intake-status-test.sh >/dev/null
bin/chief-of-staff --markdown-frontmatter-planning-status >/dev/null
bash tests/markdown-frontmatter-planning-status-test.sh >/dev/null
bin/chief-of-staff --workstation-ops-lane-status >/dev/null
bash tests/workstation-ops-lane-status-test.sh >/dev/null
bash tests/backlog-non-mutation-guardrails-test.sh >/dev/null
bash tests/lane-review-hardening-guardrails-test.sh >/dev/null
bash tests/ai-tool-routing-status-test.sh >/dev/null
bash tests/local-llm-workstation-status-test.sh >/dev/null
bash tests/mac-workstation-experience-status-test.sh >/dev/null
bash tests/widget-shortcut-builder-status-test.sh >/dev/null
bash tests/classroom-app-lab-status-test.sh >/dev/null
bin/chief-of-staff --classroom-utility-templates-status >/dev/null
bash tests/classroom-utility-templates-status-test.sh >/dev/null
bash tests/lovable-classroom-app-builder-status-test.sh >/dev/null
bash tests/3d-builder-workshop-agent-status-test.sh >/dev/null
bash tests/cursor-operating-modes-status-test.sh >/dev/null
bash tests/teacher-workstation-system-updater-test.sh >/dev/null
bash tests/teacher-workstation-health-monitor-test.sh >/dev/null
bash tests/chief-of-staff-daily-operations-test.sh >/dev/null
bin/chief-of-staff --intake-status >/dev/null
bin/chief-of-staff --intake-summary >/dev/null
bin/chief-of-staff --intake-diff >/dev/null
bin/chief-of-staff --next-intake-id > /tmp/chief-of-staff-next-intake-id.txt
grep -q '^ITEM-0002$' /tmp/chief-of-staff-next-intake-id.txt
bin/chief-of-staff --validate-intake >/dev/null
bin/chief-of-staff --workflow project-review --include-approved-intake --question "test" --dry-run >/dev/null
bin/chief-of-staff --workflow project-review --include-intake-policy --question "test" --dry-run >/dev/null
bin/chief-of-staff --workflow intake-review --include-intake-queue --question "test" --dry-run >/dev/null
bin/chief-of-staff --workflow intake-review --include-intake-checklist --question "test" --dry-run >/dev/null
bin/chief-of-staff --show-context --workflow project-review --include-approved-intake > /tmp/chief-of-staff-show-intake-context.txt
grep -q "assistant/intake/approved-context.md" /tmp/chief-of-staff-show-intake-context.txt
bin/chief-of-staff --workflow project-review --question "test" --dry-run > /tmp/chief-of-staff-no-intake.txt
if grep -q "SOURCE: assistant/intake/approved-context.md" /tmp/chief-of-staff-no-intake.txt; then
  echo "FAIL: normal dry-run should not include approved intake"
  exit 1
fi
bin/chief-of-staff --workflow project-review --include-approved-intake --question "test" --dry-run > /tmp/chief-of-staff-approved-intake.txt
grep -q "SOURCE: assistant/intake/approved-context.md" /tmp/chief-of-staff-approved-intake.txt
if grep -q "SOURCE: assistant/intake/rejected-context.md" /tmp/chief-of-staff-approved-intake.txt; then
  echo "FAIL: approved intake should not include rejected-context.md"
  exit 1
fi
if grep -q "SOURCE: assistant/intake/quarantine.md" /tmp/chief-of-staff-approved-intake.txt; then
  echo "FAIL: approved intake should not include quarantine.md"
  exit 1
fi
if grep -q "SOURCE: assistant/intake/intake-log.md" /tmp/chief-of-staff-approved-intake.txt; then
  echo "FAIL: approved intake should not include intake-log.md"
  exit 1
fi
if grep -q "SOURCE: assistant/intake/review-queue.md" /tmp/chief-of-staff-approved-intake.txt; then
  echo "FAIL: approved intake should not include review-queue.md"
  exit 1
fi

expect_failure() {
  local label="$1"
  local expected="$2"
  shift
  shift

  set +e
  "$@" >/tmp/chief-of-staff-negative.out 2>/tmp/chief-of-staff-negative.err
  local status=$?
  set -e

  if [[ ${status} -eq 0 ]]; then
    echo "FAIL: ${label}"
    cat /tmp/chief-of-staff-negative.out
    cat /tmp/chief-of-staff-negative.err >&2
    exit 1
  fi

  if ! grep -q "${expected}" /tmp/chief-of-staff-negative.err; then
    echo "FAIL: ${label} did not show expected refusal reason"
    cat /tmp/chief-of-staff-negative.out
    cat /tmp/chief-of-staff-negative.err >&2
    exit 1
  fi

  echo "PASS: ${label}"
}

expect_failure "correctly refused raw-inbox" \
  "Refusing to include raw-inbox.md" \
  bin/chief-of-staff \
    --workflow project-review \
    --context assistant/training/writing-samples/raw-inbox.md \
    --question "test" \
    --dry-run

expect_failure "correctly refused rejected-samples" \
  "Refusing to include rejected-samples.md" \
  bin/chief-of-staff \
    --workflow project-review \
    --context assistant/training/writing-samples/rejected-samples.md \
    --question "test" \
    --dry-run

expect_failure "correctly refused intake raw folder" \
  "Refusing to include intake file-holding folders" \
  bin/chief-of-staff \
    --workflow project-review \
    --context assistant/intake/raw/ \
    --question "test" \
    --dry-run

expect_failure "correctly refused file under intake raw folder" \
  "Refusing to include intake file-holding folders" \
  bin/chief-of-staff \
    --workflow project-review \
    --context "${raw_intake_test_file}" \
    --question "test" \
    --dry-run

expect_failure "correctly refused rejected intake without force" \
  "Refusing to include non-approved intake context" \
  bin/chief-of-staff \
    --workflow project-review \
    --context assistant/intake/rejected-context.md \
    --question "test" \
    --dry-run

expect_failure "correctly refused quarantine intake without force" \
  "Refusing to include non-approved intake context" \
  bin/chief-of-staff \
    --workflow project-review \
    --context assistant/intake/quarantine.md \
    --question "test" \
    --dry-run

bin/chief-of-staff \
  --workflow project-review \
  --context assistant/intake/rejected-context.md \
  --force-sensitive-context \
  --question "test" \
  --dry-run > /tmp/chief-of-staff-rejected-force.txt
grep -q "Sensitive Context Warnings" /tmp/chief-of-staff-rejected-force.txt

bin/chief-of-staff \
  --workflow project-review \
  --context assistant/intake/quarantine.md \
  --force-sensitive-context \
  --question "test" \
  --dry-run > /tmp/chief-of-staff-quarantine-force.txt
grep -q "Sensitive Context Warnings" /tmp/chief-of-staff-quarantine-force.txt

echo "PASS: Chief of Staff CLI smoke tests passed."
