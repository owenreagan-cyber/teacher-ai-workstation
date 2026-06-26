#!/usr/bin/env bash
set -euo pipefail

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

check_required_file() {
  if [[ -f "$1" ]]; then
    pass "required file exists: $1"
  else
    fail "required file missing: $1"
  fi
}

check_optional_file() {
  if [[ -f "$1" ]]; then
    pass "optional Phase 0E file exists: $1"
  else
    warn "optional Phase 0E file missing: $1"
  fi
}

check_bash_syntax() {
  if [[ ! -f "$1" ]]; then
    fail "cannot syntax-check missing bash script: $1"
    return
  fi
  if bash -n "$1"; then
    pass "bash syntax ok: $1"
  else
    fail "bash syntax failed: $1"
  fi
}

check_python_syntax() {
  if [[ ! -f "$1" ]]; then
    fail "cannot syntax-check missing Python script: $1"
    return
  fi
  if PYTHONPYCACHEPREFIX=/private/tmp/teacher-ai-pycache python3 -m py_compile "$1"; then
    pass "python syntax ok: $1"
  else
    fail "python syntax failed: $1"
  fi
}

check_json_syntax() {
  if [[ ! -f "$1" ]]; then
    warn "cannot JSON-check missing config: $1"
    return
  fi
  if node -e 'JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"))' "$1"; then
    pass "JSON syntax ok: $1"
  else
    fail "JSON syntax failed: $1"
  fi
}

check_local_folder() {
  local folder="$1"
  local setup_hint="$2"
  if [[ -d "$folder" ]]; then
    pass "local folder exists: $folder"
  else
    warn "local folder missing: $folder"
    printf '      setup: %s\n' "$setup_hint"
  fi
}

printf '\nPhase 0E Verification\n'
printf '=====================\n\n'

printf 'Core file checks\n'
printf '%s\n' '----------------'
for file in \
  scripts/mode-casual.sh \
  scripts/mode-teacher.sh \
  scripts/mode-status.sh \
  scripts/image_review_lib.py \
  scripts/image-review-status.py \
  scripts/add-image-approval-entry.py \
  scripts/stage-reference-only-candidates.py \
  scripts/stage-unsplash-candidates-for-review.py \
  scripts/apply-approved-wallpaper.py \
  scripts/prepare-approved-photos-import.py \
  scripts/init-image-approval-manifest.sh \
  scripts/prepare-image-review-queue.sh; do
  check_required_file "$file"
done

printf '\nOptional docs/config checks\n'
printf '%s\n' '---------------------------'
for file in \
  docs/phase-0e-d6-image-review-vibe-tools.md \
  docs/vibe-panel-roadmap.md \
  docs/spotify-vibe-playlists.md \
  configs/spotify-vibe-playlists.json \
  configs/image-review-queue.json \
  configs/image-approval-manifest-template.json; do
  check_optional_file "$file"
done

printf '\nBash syntax checks\n'
printf '%s\n' '------------------'
for file in \
  scripts/mode-casual.sh \
  scripts/mode-teacher.sh \
  scripts/mode-status.sh \
  scripts/init-image-approval-manifest.sh \
  scripts/prepare-image-review-queue.sh \
  scripts/prepare-photos-widget-folders.sh \
  scripts/install-shortcuts-vibe-buttons.sh; do
  check_bash_syntax "$file"
done

if [[ -f scripts/phase-0e-summary.sh ]]; then
  check_bash_syntax scripts/phase-0e-summary.sh
fi
if [[ -f scripts/install-phase-0e-shortcuts-tools.sh ]]; then
  check_bash_syntax scripts/install-phase-0e-shortcuts-tools.sh
fi

printf '\nPython syntax checks\n'
printf '%s\n' '--------------------'
if command -v python3 >/dev/null 2>&1; then
  for file in \
    scripts/image_review_lib.py \
    scripts/image-review-status.py \
    scripts/add-image-approval-entry.py \
    scripts/stage-reference-only-candidates.py \
    scripts/stage-unsplash-candidates-for-review.py \
    scripts/apply-approved-wallpaper.py \
    scripts/prepare-approved-photos-import.py \
    scripts/provision-wallpapers.py \
    scripts/unsplash-wallpaper-search.py; do
    check_python_syntax "$file"
  done
else
  warn "python3 missing; skipping Python syntax checks"
fi

printf '\nJSON syntax checks\n'
printf '%s\n' '------------------'
if command -v node >/dev/null 2>&1; then
  for file in \
    configs/spotify-vibe-playlists.json \
    configs/image-review-queue.json \
    configs/image-approval-manifest-template.json \
    configs/widgets/casual-anime-widget-plan.json \
    configs/visual-modes/casual-anime.json \
    configs/visual-modes/teacher.json \
    configs/wallpaper-sources.json; do
    check_json_syntax "$file"
  done
else
  warn "node missing; skipping JSON syntax checks"
fi

printf '\nLocal folder checks\n'
printf '%s\n' '-------------------'
check_local_folder "$HOME/Pictures/Teacher-AI-Workstation/Image-Review" "bash scripts/prepare-image-review-queue.sh"
check_local_folder "$HOME/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle" "bash scripts/prepare-photos-widget-folders.sh"
check_local_folder "$HOME/Pictures/Teacher-AI-Workstation/Wallpapers/Casual-Anime" "python3 scripts/provision-wallpapers.py --init-folders --show-presets"
check_local_folder "$HOME/Pictures/Teacher-AI-Workstation/Wallpapers/Presentation" "python3 scripts/provision-wallpapers.py --init-folders --show-presets"
check_local_folder "$HOME/Pictures/Teacher-AI-Workstation/Wallpapers/Teacher-Coding" "python3 scripts/provision-wallpapers.py --init-folders --show-presets"

printf '\nImage review status\n'
printf '%s\n' '-------------------'
if command -v python3 >/dev/null 2>&1 && [[ -f scripts/image-review-status.py ]]; then
  if python3 scripts/image-review-status.py; then
    pass "image review status command completed"
  else
    warn "image review status command returned a warning/error; inspect output above"
  fi
else
  warn "skipping image review status command"
fi

printf '\nSummary\n'
printf '%s\n' '-------'
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi

exit 0
