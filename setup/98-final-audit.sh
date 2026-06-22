#!/usr/bin/env bash
set -euo pipefail

EXPECTED_HTTPS="https://github.com/owenreagan-cyber/teacher-ai-workstation.git"
EXPECTED_SSH="git@github.com:owenreagan-cyber/teacher-ai-workstation.git"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/teacher-ai-final-audit.XXXXXX")"
pass_count=0
warn_count=0
fail_count=0
repo_root=""

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

pass() {
  echo "PASS: $1"
  pass_count=$((pass_count + 1))
}

warn() {
  echo "WARN: $1"
  warn_count=$((warn_count + 1))
}

fail() {
  echo "FAIL: $1"
  fail_count=$((fail_count + 1))
}

section() {
  echo
  echo "## $1"
}

check_file() {
  local file="$1"
  local severity="${2:-fail}"
  if [[ -f "${file}" ]]; then
    pass "${file} exists."
  elif [[ "${severity}" == "warn" ]]; then
    warn "${file} missing."
  else
    fail "${file} missing."
  fi
}

check_executable() {
  local file="$1"
  local severity="${2:-fail}"
  if [[ -x "${file}" ]]; then
    pass "${file} is executable."
  elif [[ "${severity}" == "warn" ]]; then
    warn "${file} is not executable."
  else
    fail "${file} is not executable."
  fi
}

check_command_available() {
  local command_name="$1"
  local severity="${2:-fail}"
  if command -v "${command_name}" >/dev/null 2>&1; then
    pass "${command_name} is available."
  elif [[ "${severity}" == "warn" ]]; then
    warn "${command_name} is not available."
  else
    fail "${command_name} is not available."
  fi
}

check_bash_syntax_one_file() {
  local file="$1"
  local out_file="${TMP_DIR}/syntax.out"
  local err_file="${TMP_DIR}/syntax.err"
  if bash -n "${file}" >"${out_file}" 2>"${err_file}"; then
    pass "syntax OK - ${file}"
  else
    fail "syntax error - ${file}"
    sed 's/^/  /' "${err_file}"
  fi
}

run_check_capture() {
  local label="$1"
  local severity="$2"
  shift 2
  local out_file="${TMP_DIR}/capture.out"
  if "$@" >"${out_file}" 2>&1; then
    pass "${label}"
  elif [[ "${severity}" == "warn" ]]; then
    warn "${label}"
    sed 's/^/  /' "${out_file}"
  else
    fail "${label}"
    sed 's/^/  /' "${out_file}"
  fi
}

resolve_repo_root() {
  local script_dir
  local candidate=""

  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  candidate="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -z "${candidate}" ]]; then
    candidate="$(cd "${script_dir}/.." && pwd -P)"
  fi

  if [[ -f "${candidate}/README.md" && -f "${candidate}/bootstrap.sh" && -f "${candidate}/setup/99-verify-setup.sh" ]]; then
    repo_root="${candidate}"
    cd "${repo_root}"
    pass "Repo root resolved: ${repo_root}"
  else
    fail "Could not resolve repo root with expected sentinel files."
  fi
}

check_git_repository() {
  local remote=""
  local branch=""
  local untracked=""
  local behind=""
  local git_size_human=""
  local git_size_kb=""

  section "Repository Checks"
  check_command_available git fail

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    pass "Current directory is inside a Git repo."
  else
    fail "Current directory is not inside a Git repo."
    return
  fi

  remote="$(git remote get-url origin 2>/dev/null || true)"
  if [[ "${remote}" == "${EXPECTED_HTTPS}" || "${remote}" == "${EXPECTED_SSH}" ]]; then
    pass "origin remote points to the Teacher AI Workstation repository."
  elif [[ -n "${remote}" ]]; then
    fail "origin remote points to ${remote}, not the expected Teacher AI Workstation repository."
  else
    fail "origin remote is not configured."
  fi

  branch="$(git branch --show-current 2>/dev/null || true)"
  if [[ "${branch}" == "main" ]]; then
    pass "Current branch is main."
  elif [[ -n "${branch}" ]]; then
    fail "Current branch is ${branch}, expected main."
  else
    warn "Current branch could not be determined."
  fi

  if git diff --quiet; then
    pass "Tracked working tree is clean."
  else
    fail "Tracked working tree has uncommitted changes."
  fi

  if git diff --staged --quiet; then
    pass "Staged changes are clean."
  else
    fail "Staged changes are present."
  fi

  untracked="$(git ls-files --others --exclude-standard)"
  if [[ -n "${untracked}" ]]; then
    warn "Untracked files are present."
    printf '%s\n' "${untracked}" | sed 's/^/  /'
  else
    pass "No untracked files."
  fi

  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    behind="$(git rev-list --count HEAD..origin/main 2>/dev/null || true)"
    if [[ "${behind}" =~ ^[0-9]+$ ]] && (( behind > 0 )); then
      warn "Local HEAD appears ${behind} commit(s) behind origin/main."
    else
      pass "Local HEAD is not obviously behind origin/main."
    fi
  else
    warn "origin/main is unavailable locally; cannot compare behind status."
  fi

  if [[ -d ".git" ]]; then
    git_size_human="$(du -sh .git 2>/dev/null | awk '{print $1}' || true)"
    git_size_kb="$(du -sk .git 2>/dev/null | awk '{print $1}' || true)"
    echo "Git directory size: ${git_size_human:-unknown}"
    if [[ "${git_size_kb}" =~ ^[0-9]+$ ]] && (( git_size_kb > 51200 )); then
      warn ".git appears larger than 50 MB."
    else
      pass ".git size is reasonable for a fresh clone."
    fi
  fi
}

check_core_files() {
  section "Core File Checks"
  for file in README.md Brewfile bootstrap.sh machine-spec.md .gitignore docs/day-1-manual-steps.md docs/recovery-guide.md docs/final-installer-audit.md; do
    check_file "${file}" fail
  done
  check_executable bootstrap.sh fail
  check_executable bin/chief-of-staff warn
  check_executable tests/smoke-chief-of-staff-cli.sh warn
}

check_setup_scripts() {
  local script
  local expected_scripts=(
    setup/00-check-system.sh
    setup/01-install-homebrew.sh
    setup/02-install-apps.sh
    setup/03-macos-defaults.sh
    setup/04-folder-structure.sh
    setup/05-dock-layout.sh
    setup/06-wallpapers.sh
    setup/07-git-github.sh
    setup/08-local-ai.sh
    setup/09-generate-report.sh
    setup/10-shell-profile.sh
    setup/98-final-audit.sh
    setup/99-verify-setup.sh
  )

  section "Setup Script Checks"
  for script in "${expected_scripts[@]}"; do
    check_file "${script}" fail
    check_executable "${script}" fail
  done

  section "Bash Syntax Checks"
  check_bash_syntax_one_file bootstrap.sh
  for script in setup/*.sh; do
    check_bash_syntax_one_file "${script}"
  done
}

run_chief_of_staff_checks() {
  section "Chief of Staff CLI Checks"
  if [[ ! -f "bin/chief-of-staff" ]]; then
    fail "bin/chief-of-staff missing."
    return
  fi

  run_check_capture "bin/chief-of-staff syntax passed." fail bash -n bin/chief-of-staff
  run_check_capture "bin/chief-of-staff --help passed." fail bin/chief-of-staff --help
  run_check_capture "bin/chief-of-staff --status passed." fail bin/chief-of-staff --status
  run_check_capture "bin/chief-of-staff --list-workflows passed." fail bin/chief-of-staff --list-workflows
  run_check_capture "Chief of Staff dry run passed." fail bin/chief-of-staff --workflow request-training-materials --question "Final audit dry run" --dry-run

  run_check_capture "bin/chief-of-staff --memory-status passed or warned." warn bin/chief-of-staff --memory-status
  run_check_capture "bin/chief-of-staff --validate-memory passed or warned." warn bin/chief-of-staff --validate-memory
  run_check_capture "bin/chief-of-staff --intake-status passed or warned." warn bin/chief-of-staff --intake-status
  run_check_capture "bin/chief-of-staff --intake-summary passed or warned." warn bin/chief-of-staff --intake-summary
  run_check_capture "bin/chief-of-staff --validate-intake passed or warned." warn bin/chief-of-staff --validate-intake
  run_check_capture "bin/chief-of-staff --preflight passed or warned." warn bin/chief-of-staff --preflight

  if [[ -f "tests/smoke-chief-of-staff-cli.sh" ]]; then
    run_check_capture "Chief of Staff CLI smoke tests passed." fail bash tests/smoke-chief-of-staff-cli.sh
  else
    warn "tests/smoke-chief-of-staff-cli.sh missing."
  fi
}

check_brewfile() {
  local item
  section "Brewfile Checks"
  check_file Brewfile fail

  for item in git gh python uv llm; do
    if grep -q "^brew \"${item}\"" Brewfile; then
      pass "Essential Brewfile formula present: ${item}"
    else
      fail "Essential Brewfile formula missing: ${item}"
    fi
  done

  for item in ollama fabric openscad; do
    if grep -q "^brew \"${item}\"" Brewfile; then
      pass "Optional Brewfile formula present: ${item}"
    else
      warn "Optional Brewfile formula missing: ${item}"
    fi
  done

  for item in bambu-studio 1password ghostty cursor; do
    if grep -q "^cask \"${item}\"" Brewfile; then
      pass "Optional Brewfile cask present: ${item}"
    else
      warn "Optional Brewfile cask missing: ${item}"
    fi
  done
}

check_memory_files() {
  local file
  section "Memory Checks"
  for file in \
    assistant/memory/README.md \
    assistant/memory/projects.md \
    assistant/memory/teaching-context.md \
    assistant/memory/writing-style-rules.md \
    assistant/memory/preferences.md \
    assistant/memory/decisions.md \
    assistant/memory/active-priorities.md \
    assistant/memory/memory-review-checklist.md \
    assistant/memory/memory-log.md; do
    check_file "${file}" warn
  done
}

check_intake_files() {
  local file
  section "Intake Checks"
  for file in \
    assistant/intake/README.md \
    assistant/intake/intake-policy.md \
    assistant/intake/review-queue.md \
    assistant/intake/approved-context.md \
    assistant/intake/rejected-context.md \
    assistant/intake/quarantine.md \
    assistant/intake/intake-log.md \
    assistant/intake/intake-review-checklist.md \
    assistant/intake/raw/.gitkeep \
    assistant/intake/quarantine-files/.gitkeep \
    assistant/intake/approved-files/.gitkeep \
    assistant/intake/templates/intake-item-template.md \
    assistant/intake/templates/review-decision-template.md \
    assistant/intake/templates/sanitized-summary-template.md; do
    check_file "${file}" warn
  done
}

expect_ignored() {
  local path="$1"
  if git check-ignore -q "${path}"; then
    pass "${path} is ignored."
  else
    fail "${path} is not ignored."
  fi
}

expect_not_ignored() {
  local path="$1"
  if git check-ignore -q "${path}"; then
    fail "${path} is ignored but should remain trackable."
  else
    pass "${path} is not ignored."
  fi
}

check_gitignore_safety() {
  section ".gitignore Safety Checks"
  expect_ignored "assistant/intake/raw/testfile.txt"
  expect_ignored "assistant/intake/quarantine-files/testfile.txt"
  expect_ignored "assistant/intake/approved-files/testfile.txt"
  expect_not_ignored "assistant/intake/raw/.gitkeep"
  expect_not_ignored "assistant/intake/quarantine-files/.gitkeep"
  expect_not_ignored "assistant/intake/approved-files/.gitkeep"
  expect_ignored "logs/test.log"
  expect_ignored "logs/test.md"
}

check_3d_readiness() {
  local file
  section "3D Readiness Checks"
  for file in \
    3d-agent/README.md \
    3d-agent/print-profile.md \
    3d-agent/templates/openscad-header.scad \
    3d-agent/verification/README.md \
    3d-agent/verification/pre-slicer-checklist.md \
    3d-agent/training/openscad-test-suite.md \
    3d-agent/training/llm-routing-for-cad.md \
    docs/3d-printing-day-1-setup.md \
    docs/3d-printing-roadmap.md; do
    check_file "${file}" fail
  done
  check_file "3d-agent/partner-workflow.md" warn
}

check_safety_text() {
  section "Safety Text Spot Checks"
  if [[ -f "3d-agent/verification/README.md" ]] && grep -qi "slicer-ready pending human verification" 3d-agent/verification/README.md; then
    pass "3D verification includes slicer-ready pending human verification language."
  else
    warn "3D verification wording may need review."
  fi

  if [[ -f "3d-agent/verification/README.md" ]] && grep -Eqi "cannot block, stop, disable, or prevent|cannot .*block.*stop.*prevent" 3d-agent/verification/README.md; then
    pass "3D verification says the system cannot block/stop/prevent printing."
  else
    warn "3D block/stop/prevent wording may need review."
  fi

  if [[ -f "assistant/intake/README.md" ]] && grep -Eqi "Raw material is not automatically loaded|raw intake.*not.*automatically loaded|raw.*not automatically loaded" assistant/intake/README.md; then
    pass "Intake README says raw intake is not automatically loaded."
  else
    warn "Intake README automatic-loading wording may need review."
  fi

  if [[ -f "assistant/memory/README.md" ]] && grep -Eqi "not automatically loaded|not automatically generated" assistant/memory/README.md; then
    pass "Memory README says memory is not automatically loaded or generated."
  else
    warn "Memory README automatic-loading wording may need review."
  fi

  if [[ -f "docs/chief-of-staff-roadmap.md" ]] && grep -q "open new MacBook Pro M5 Pro" docs/chief-of-staff-roadmap.md; then
    pass "Roadmap includes the open MacBook Pro checkpoint."
  else
    warn "Roadmap may be missing the open MacBook Pro checkpoint."
  fi

  if [[ -f "README.md" ]] && grep -q "bash setup/98-final-audit.sh" README.md; then
    pass "README references setup/98-final-audit.sh."
  else
    warn "README does not reference setup/98-final-audit.sh."
  fi

  if [[ -f "docs/day-1-manual-steps.md" ]] && grep -q "setup/98-final-audit.sh" docs/day-1-manual-steps.md; then
    pass "Day 1 manual references setup/98-final-audit.sh."
  else
    warn "Day 1 manual does not reference setup/98-final-audit.sh."
  fi

  if [[ -f "docs/recovery-guide.md" ]] && grep -q "setup/98-final-audit.sh" docs/recovery-guide.md; then
    pass "Recovery guide references setup/98-final-audit.sh."
  else
    warn "Recovery guide does not reference setup/98-final-audit.sh."
  fi
}

check_docs_cross_references() {
  section "Docs Links Check"
  if grep -q "docs/day-1-manual-steps.md" README.md; then pass "README references day-1 manual."; else warn "README missing day-1 manual reference."; fi
  if grep -Eq "docs/recovery-guide.md|recovery" README.md; then pass "README references recovery guidance."; else warn "README missing recovery guidance reference."; fi
  if grep -q "setup/98-final-audit.sh" docs/day-1-manual-steps.md; then pass "Day 1 manual references final audit."; else warn "Day 1 manual missing final audit reference."; fi
  if grep -q "setup/98-final-audit.sh" docs/recovery-guide.md; then pass "Recovery guide references final audit."; else warn "Recovery guide missing final audit reference."; fi
  if grep -q "README.md" docs/final-installer-audit.md; then pass "Final audit doc references README."; else warn "Final audit doc missing README reference."; fi
  if grep -q "docs/day-1-manual-steps.md" docs/final-installer-audit.md; then pass "Final audit doc references Day 1 manual."; else warn "Final audit doc missing Day 1 manual reference."; fi
  if grep -q "docs/recovery-guide.md" docs/final-installer-audit.md; then pass "Final audit doc references recovery guide."; else warn "Final audit doc missing recovery guide reference."; fi
}

scan_for_secrets() {
  local file
  local key_regex='BEGIN (OPENSSH |RSA )?PRIVATE KEY'
  local assigned_regex='(^|[^[:alnum:]_])(password|api[_-]?key|secret|token)[[:space:]]*[:=][[:space:]]*[^[:space:]`"]+'

  section "Secrets Scan"
  while IFS= read -r file; do
    if grep -Eiq "${key_regex}" "${file}"; then
      fail "${file} may contain private key block markers."
    fi
    if grep -Eiq "${assigned_regex}" "${file}"; then
      case "${file}" in
        *.md)
          warn "${file} contains documentation-like assigned credential wording."
          ;;
        *)
          fail "${file} may contain assigned credential-like text."
          ;;
      esac
    fi
  done < <(
    find . -type f \
      \( -name '*.md' -o -name '*.sh' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' -o -name '*.env' -o -name 'Brewfile' -o -name '.gitignore' \) \
      ! -path './.git/*' \
      ! -path './node_modules/*' \
      ! -path './vendor/*' \
      ! -path './assistant/intake/raw/*' \
      ! -path './assistant/intake/quarantine-files/*' \
      ! -path './assistant/intake/approved-files/*' \
      ! -path './logs/*' \
      | sed 's#^\./##' | sort
  )
  pass "Repo-only lightweight secrets scan completed."
}

fresh_clone_simulation() {
  section "Fresh Clone Simulation"
  cat <<'EOF'
Files the new Mac will need from this repo:
- README.md
- bootstrap.sh
- Brewfile
- setup/*.sh
- docs/day-1-manual-steps.md
- docs/recovery-guide.md

External things the new Mac will need:
- internet
- Xcode Command Line Tools
- GitHub access
- Homebrew install access
- Apple ID during Apple setup
- passwords entered only into Apple/macOS/GitHub/Homebrew/app prompts, not into this repo

Manual steps that will still remain after bootstrap:
- Focus Modes
- browser profiles
- Raycast
- Obsidian
- 1Password
- AlDente
- Bambu Studio profile checks
- Ricoh printer test at school
EOF
  pass "Fresh clone simulation printed."
}

print_summary() {
  echo
  echo "## Final Audit Summary"
  echo "PASS count: ${pass_count}"
  echo "WARN count: ${warn_count}"
  echo "FAIL count: ${fail_count}"
  echo
  if (( fail_count > 0 )); then
    echo "Final Audit Result: FAIL"
    exit 1
  elif (( warn_count > 0 )); then
    echo "Final Audit Result: PASS WITH WARNINGS"
    exit 0
  else
    echo "Final Audit Result: PASS"
    exit 0
  fi
}

echo "Phase 0D Final Installer Audit"
echo "This audit does not install apps, call a model, or scan outside this repo."

section "Repo Root Resolution"
resolve_repo_root

if [[ -n "${repo_root}" ]]; then
  check_git_repository
  check_core_files
  check_setup_scripts
  run_chief_of_staff_checks
  check_brewfile
  check_memory_files
  check_intake_files
  check_gitignore_safety
  check_3d_readiness
  check_safety_text
  check_docs_cross_references
  scan_for_secrets
  fresh_clone_simulation
fi

print_summary
