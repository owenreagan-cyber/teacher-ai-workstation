# Wallpaper/Photo Dry-Run Folder Validator

## Purpose

This document describes a dry-run-only validator for the future **Automated Wallpaper and Photo Curator** folder layout. The validator checks conceptual path strings from `docs/wallpaper-photo-rotation-folder-design.md` for safety and consistency without touching the filesystem.

This PR is dry-run only. It does not create folders, delete files, scan folders, or automate macOS wallpaper or Photos settings.

## Current Status

```text
Current status: Phase C dry-run validator only.
```

The validator reports on path strings only. No folder creation helper, metadata files, or curator runtime exists yet.

## Relationship to Folder Design

This validator implements Phase C of the curator roadmap. Phase B defined conceptual folders in `docs/wallpaper-photo-rotation-folder-design.md`. Phase C validates those paths as strings before any future folder creation helper runs.

## Dry-Run Only Boundary

- Validates path strings only
- Does not call `mkdir`, `rm`, `rmdir`, or `find`
- Does not read or write wallpaper/photo directories
- Does not fetch, download, or process images
- Does not send notifications
- Does not change macOS wallpaper or Photos settings

## Conceptual Folder Paths Checked

```text
~/Pictures/Wallpaper Curator/
~/Pictures/Wallpaper Curator/Temp Wallpaper Candidates/
~/Pictures/Wallpaper Curator/Temp Photo Candidates/
~/Pictures/Wallpaper Curator/Approved Wallpaper Queue/
~/Pictures/Wallpaper Curator/Approved Photo Queue/
~/Pictures/Wallpaper Curator/Processed Wallpaper/
~/Pictures/Wallpaper Curator/Processed Photo Widget/
~/Pictures/Wallpaper Curator/Metadata/
~/Pictures/Wallpaper Rotation/
~/Pictures/Photo Widget Rotation/
```

```text
These paths are checked as strings only.
This PR does not create these folders.
```

## Path Safety Rules

The validator checks conceptually for:

```text
path starts with ~/Pictures/
path does not contain ..
path does not contain shell wildcards
path does not begin with /
path does not contain command substitution
path does not contain semicolon
path does not contain pipe
path does not contain ampersand
path does not contain backticks
path does not contain unexpanded variables other than leading ~
```

## Parent Location Checks

Parent checks are string-only. For curator subfolders, the validator confirms the path is nested under `~/Pictures/Wallpaper Curator/`. For rotation folders, the validator confirms the path is a direct child concept under `~/Pictures/`. No filesystem probe is performed.

## What the Validator Reports

For each conceptual path:

- PASS when all string safety rules pass
- FAIL when a dangerous or invalid pattern is detected

The script also reports dry-run status, that no folders were created, and that no external or destructive commands were used.

## What the Validator Does Not Do

- This PR is dry-run only.
- This PR does not create folders.
- This PR does not delete files.
- This PR does not scan folders.
- This PR does not fetch images.
- This PR does not download images.
- This PR does not process images.
- This PR does not send notifications.
- This PR does not change macOS wallpaper settings.
- This PR does not modify Photos or photo widgets.
- This PR does not add Reddit or Devvit integration.
- This PR does not add network calls.
- This PR does not add APIs, OAuth, or secrets.

## Future Approval Gates

```text
1. Approve dry-run path validation rules.
2. Approve actual folder creation helper.
3. Approve exact destination folder names.
4. Approve parent folder permissions.
5. Approve cleanup and stale candidate rules.
6. Approve metadata file format.
7. Approve notification behavior.
8. Approve image processing rules.
9. Approve any source integration.
10. Approve scheduled automation.
```

## Future Implementation Phases

```text
Phase C: Dry-run folder validator
Phase D: Manual folder creation helper
Phase E: Metadata schema and sample records
Phase F: Temp queue rules
Phase G: Approve/Dismiss UI design
Phase H: Image processing rules
Phase I: Local automation scheduler
Phase J: Approved-source fetcher
```

Phase C dry-run validation is complete. Phase D manual folder creation helper is in `docs/wallpaper-photo-manual-folder-creation-helper.md`.

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-dry-run-folder-validator
bin/chief-of-staff --wallpaper-photo-folder-creation-status
bin/chief-of-staff --wallpaper-photo-create-folders --dry-run
bin/chief-of-staff --wallpaper-photo-folder-design-status
bin/chief-of-staff --wallpaper-photo-curator-plan-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-dry-run-folder-validator.sh
bash scripts/wallpaper-photo-create-folders.sh --dry-run
```
