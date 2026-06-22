#!/usr/bin/env bash
set -euo pipefail

echo "Running Chief of Staff CLI smoke tests..."

bin/chief-of-staff --help >/dev/null
bin/chief-of-staff --version >/dev/null
bin/chief-of-staff --status >/dev/null
bin/chief-of-staff --list-workflows >/dev/null
bin/chief-of-staff --show-context --workflow request-training-materials >/dev/null
bin/chief-of-staff --workflow request-training-materials --question "What do you need from me?" --dry-run >/dev/null
bin/chief-of-staff --workflow project-review --context examples/sample-project-note.md --question "What is the next action?" --dry-run >/dev/null
bin/chief-of-staff --workflow project-review --context examples/sample-project-note.md --question "What is the next action?" --no-model > /tmp/chief-of-staff-prompt.txt

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

echo "PASS: Chief of Staff CLI smoke tests passed."
