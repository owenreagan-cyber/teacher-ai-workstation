# Wallpaper/Photo Manual Folder Creation Helper

## Purpose

This guide documents a manual, explicit folder creation helper for the future **Automated Wallpaper and Photo Curator**. Owen can preview the approved folder structure in dry-run mode and create directories only when intentionally running create mode.

## Current Status

```text
Current status: Phase D manual folder creation helper.
```

The helper creates directories only. It does not fetch images, process images, or automate macOS wallpaper or Photos settings.

## Relationship to the Dry-Run Validator

Phase C (`docs/wallpaper-photo-dry-run-folder-validator.md`) validates conceptual path strings. Phase D adds the first user-run creation helper for the same approved structure after Owen chooses to create folders.

## Safety Boundary

- This PR adds a manual helper only.
- The default mode is dry-run/read-only.
- Dashboard/status checks do not create folders.
- Folder creation must require an explicit create flag or command.
- The helper creates directories only; it does not fetch, download, process, move, or delete images.
- The helper does not delete files or folders.
- The helper does not scan folders.
- The helper does not send notifications.
- The helper does not change macOS wallpaper settings.
- The helper does not modify Photos or photo widgets.
- The helper does not add Reddit or Devvit integration.
- The helper does not add network calls.
- The helper does not add APIs, OAuth, or secrets.

## Approved Folder Structure

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

## Default Dry-Run Behavior

With no arguments or with `--dry-run`, the helper prints the folders that would be created under `~/Pictures/` and reports `Folders created: no`.

## Explicit Create Behavior

With `--create`, the helper runs `mkdir -p` only for the approved directory list under the resolved root (`~/Pictures` by default, or `--root` for testing).

## Existing Folder Behavior

If a folder already exists, the helper reports it as already present and does not delete or modify it.

## What the Helper Must Never Do

- Automatic folder creation from dashboard or status scripts
- File or folder deletion
- Folder scanning
- Image fetching, downloading, or processing
- Network calls, notifications, or macOS automation

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-folder-creation-status
bin/chief-of-staff --wallpaper-photo-create-folders --dry-run
bin/chief-of-staff --wallpaper-photo-create-folders --create
bin/chief-of-staff --wallpaper-photo-dry-run-folder-validator
bin/chief-of-staff --wallpaper-photo-folder-design-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-folder-creation-status.sh
bash scripts/wallpaper-photo-create-folders.sh --dry-run
bash scripts/wallpaper-photo-create-folders.sh --create
```

For testing only:

```bash
bash scripts/wallpaper-photo-create-folders.sh --create --root /tmp/teacher-ai-wallpaper-folder-test
```

## Future Approval Gates

```text
1. Approve manual folder creation helper.
2. Owen intentionally runs the create command.
3. Confirm created folders exist.
4. Approve metadata file format.
5. Approve temp candidate queue behavior.
6. Approve cleanup and stale candidate rules.
7. Approve notification behavior.
8. Approve image processing rules.
9. Approve any source integration.
10. Approve scheduled automation.
```

## Future Implementation Phases

```text
Phase D: Manual folder creation helper
Phase E: Metadata schema and sample records
Phase F: Temp queue rules
Phase G: Approve/Dismiss UI design
Phase H: Image processing rules
Phase I: Local automation scheduler
Phase J: Approved-source fetcher
```
