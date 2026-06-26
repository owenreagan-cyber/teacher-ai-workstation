# Phase 0E Quick Commands

Use these commands from the repo root.

## Status

```bash
bash scripts/mode-status.sh
```

## Summary

```bash
bash scripts/phase-0e-summary.sh
```

## Verify

```bash
bash scripts/verify-phase-0e.sh
```

## Image Review Status

```bash
python3 scripts/image-review-status.py
```

## Initialize Folders And Manifests

```bash
bash scripts/prepare-image-review-queue.sh
bash scripts/prepare-photos-widget-folders.sh
bash scripts/init-image-approval-manifest.sh
python3 scripts/provision-wallpapers.py --init-folders --show-presets
```

## Add Reference-Only Entry

Dry-run example:

```bash
python3 scripts/stage-reference-only-candidates.py \
  --filename "example-reference.jpg" \
  --local-path "$HOME/Pictures/Teacher-AI-Workstation/Image-Review/Reference-Only/example-reference.jpg" \
  --source-platform "unknown" \
  --source-url "unknown" \
  --creator "unknown" \
  --notes "Reference-only dry-run example." \
  --dry-run
```

## Add Approval Entry

Dry-run example:

```bash
python3 scripts/add-image-approval-entry.py \
  --filename "example-wallpaper.jpg" \
  --local-path "$HOME/Pictures/Teacher-AI-Workstation/Image-Review/Approved-Personal-Wallpaper/example-wallpaper.jpg" \
  --source-platform "manual-example" \
  --source-url "unknown" \
  --creator "unknown" \
  --license-or-usage-note "Example only. Replace with real source/licensing review notes." \
  --intended-use "personal_wallpaper" \
  --review-status "approved_personal_wallpaper" \
  --notes "Dry-run example only." \
  --dry-run
```

## Dry-Run Wallpaper Apply

```bash
python3 scripts/apply-approved-wallpaper.py \
  --filename "example-wallpaper.jpg" \
  --mode casual \
  --dry-run
```

## Dry-Run Photos Import Prep

```bash
python3 scripts/prepare-approved-photos-import.py \
  --filename "example-widget.jpg" \
  --dry-run
```

## Update From GitHub

```bash
git switch main
git pull
```

## Final Smoke Test

```bash
bash scripts/verify-phase-0e.sh
bash scripts/phase-0e-summary.sh
```

## Commands That Require Extra Caution

Use `--dry-run` first before:

- any use of `--apply`.
- any future wallpaper setting command.
- any command involving real image files.
- any future command involving OAuth or API keys.

Do not paste or store secrets in the repo.

Do not use real copyrighted URLs in examples or docs unless the source/license has been reviewed.
