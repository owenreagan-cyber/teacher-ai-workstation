#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS: %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf 'WARN: %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'FAIL: %s\n' "$1"
}

require_file() {
  local path="$1"
  local description="$2"

  if [[ -f "$path" ]]; then
    pass "$description"
  else
    fail "$description — missing: $path"
  fi
}

require_executable() {
  local path="$1"
  local description="$2"

  if [[ -x "$path" ]]; then
    pass "$description"
  else
    fail "$description — not executable: $path"
  fi
}

PACK_DIR="docs/programs/canvas-llm/canonical-context-pack"
VALIDATOR="scripts/canvas-llm-canonical-context-pack-validator.py"
VALIDATOR_OUT="$(mktemp)"
trap 'rm -f "$VALIDATOR_OUT"' EXIT

echo "Canvas LLM Canonical Context Pack Status"
echo

if [[ -d "$PACK_DIR" ]]; then
  pass "Canonical Context Pack directory exists"
else
  fail "Canonical Context Pack directory is missing"
fi

require_file \
  "$PACK_DIR/context-pack-manifest.json" \
  "Context Pack manifest exists"

require_file \
  "$PACK_DIR/product-and-architecture-rules.md" \
  "Product and architecture contract exists"

require_file \
  "$PACK_DIR/weekly-input-contract.md" \
  "Weekly input contract exists"

require_file \
  "$PACK_DIR/announcement-contract.md" \
  "Announcement contract exists"

require_file \
  "$PACK_DIR/resource-resolution-contract.md" \
  "Resource-resolution contract exists"

require_file \
  "$PACK_DIR/approval-and-publish-contract.md" \
  "Approval and publish contract exists"

require_file \
  "$PACK_DIR/legacy-app-comparison-oracle.md" \
  "Legacy comparison oracle exists"

require_file \
  "$VALIDATOR" \
  "Canonical Context Pack validator exists"

require_executable \
  "$VALIDATOR" \
  "Canonical Context Pack validator is executable"

markdown_count="$(
  find "$PACK_DIR" \
    -maxdepth 1 \
    -type f \
    -name '*.md' \
    | wc -l \
    | tr -d ' '
)"

if [[ "$markdown_count" = "20" ]]; then
  pass "Context Pack contains exactly 20 Markdown documents"
else
  fail "Context Pack Markdown inventory expected 20, found $markdown_count"
fi

empty_markdown="$(
  find "$PACK_DIR" \
    -maxdepth 1 \
    -type f \
    -name '*.md' \
    -size 0 \
    -print
)"

if [[ -z "$empty_markdown" ]]; then
  pass "No Context Pack Markdown document is empty"
else
  fail "Empty Context Pack documents found: $empty_markdown"
fi

if python3 "$VALIDATOR" >"$VALIDATOR_OUT" 2>&1; then
  pass "Canonical Context Pack validator exits successfully"
else
  fail "Canonical Context Pack validator returned nonzero"
fi

if grep -Fq 'PASS: standalone Spelling announcements are allowed' "$VALIDATOR_OUT"; then
  pass "Standalone Spelling announcements are canonically allowed"
else
  fail "Standalone Spelling announcement rule is missing"
fi

if grep -Fq \
  'PASS: incorrect standalone-Spelling prohibition is absent from the Context Pack' \
  "$VALIDATOR_OUT"
then
  pass "Incorrect standalone-Spelling prohibition is absent"
else
  fail "Incorrect standalone-Spelling prohibition check did not pass"
fi

if grep -Eq '^PASS: [0-9]+$' "$VALIDATOR_OUT"; then
  pass "Validator reports a PASS summary"
else
  fail "Validator PASS summary is missing"
fi

if grep -Fq "PASS: manifest status is 'validated'" "$VALIDATOR_OUT"; then
  pass "Context Pack manifest is marked validated"
else
  fail "Context Pack manifest is not marked validated"
fi

if grep -Fq 'WARN: 0' "$VALIDATOR_OUT"; then
  pass "Validator reports WARN: 0"
else
  warn "Validator reports one or more warnings"
fi

if grep -Fq 'FAIL: 0' "$VALIDATOR_OUT"; then
  pass "Validator reports FAIL: 0"
else
  fail "Validator reports one or more failures"
fi

if grep -Fq \
  'PASS: synthetic fixtures are prohibited as implicit production input' \
  "$VALIDATOR_OUT"
then
  pass "Production fixture prohibition is validated"
else
  fail "Production fixture prohibition validation is missing"
fi

if grep -Fq \
  'PASS: Phase 27 safety boundary is preserved' \
  "$VALIDATOR_OUT"
then
  pass "Phase 27 safety boundary is validated"
else
  fail "Phase 27 safety-boundary validation is missing"
fi

if grep -Fq \
  'PASS: export and Canvas publish remain distinct' \
  "$VALIDATOR_OUT"
then
  pass "Export and Canvas publication remain distinct"
else
  fail "Export-versus-publish validation is missing"
fi

if grep -Fq \
  'PASS: no obvious token or authorization secret material found' \
  "$VALIDATOR_OUT"
then
  pass "Context Pack secret-material scan passes"
else
  fail "Context Pack secret-material scan did not pass"
fi

echo
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
