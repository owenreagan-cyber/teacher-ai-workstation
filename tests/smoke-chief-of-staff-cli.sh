#!/usr/bin/env bash
set -euo pipefail

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
