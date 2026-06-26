# Raycast Phase 0E Tools

These Raycast Script Command templates provide optional status and dry-run access to the Phase 0E visual/vibe/image-safety layer.

They are safe by default:

- status only.
- dry-run only.
- no `--apply`.
- no network calls.
- no Photos changes.
- no desktop wallpaper setting.

## Templates

```text
configs/raycast/phase-0e-status.sh
configs/raycast/image-review-status.sh
configs/raycast/phase-0e-verify.sh
configs/raycast/dry-run-approved-wallpaper.sh
configs/raycast/dry-run-approved-photos-import.sh
```

Each template defines:

```bash
REPO_DIR="${HOME}/Projects/teacher-ai-workstation"
```

If Owen clones the repo somewhere else, update `REPO_DIR` in the copied Raycast script.

## Install

Raycast script commands should live outside the repo in a local Raycast script directory.

Example:

```bash
mkdir -p ~/Raycast-Scripts
cp configs/raycast/phase-0e-status.sh ~/Raycast-Scripts/
cp configs/raycast/image-review-status.sh ~/Raycast-Scripts/
cp configs/raycast/phase-0e-verify.sh ~/Raycast-Scripts/
cp configs/raycast/dry-run-approved-wallpaper.sh ~/Raycast-Scripts/
cp configs/raycast/dry-run-approved-photos-import.sh ~/Raycast-Scripts/
chmod +x ~/Raycast-Scripts/phase-0e-status.sh
chmod +x ~/Raycast-Scripts/image-review-status.sh
chmod +x ~/Raycast-Scripts/phase-0e-verify.sh
chmod +x ~/Raycast-Scripts/dry-run-approved-wallpaper.sh
chmod +x ~/Raycast-Scripts/dry-run-approved-photos-import.sh
```

Then in Raycast:

1. Open Raycast.
2. Search for Extensions.
3. Open Extensions.
4. Find Script Commands.
5. Add Script Directory.
6. Choose `/Users/owen/Raycast-Scripts`.

## Commands

- `Phase 0E Status`: runs `bash scripts/phase-0e-summary.sh`.
- `Image Review Status`: runs `python3 scripts/image-review-status.py`.
- `Phase 0E Verify`: runs `bash scripts/verify-phase-0e.sh`.
- `Dry Run Approved Wallpaper`: runs `scripts/apply-approved-wallpaper.py` with `--dry-run`.
- `Dry Run Approved Photos Import`: runs `scripts/prepare-approved-photos-import.py` with `--dry-run`.

The dry-run wallpaper command asks for filename and mode.

Mode values:

```text
casual
teacher
presentation
```

The dry-run Photos import command asks for filename.

## Safety

These templates do not replace human review.

Only use `--apply` from Terminal after checking:

- the image exists.
- the image has an approval manifest entry.
- the approval status matches the intended use.
- the image is in the correct review folder.
