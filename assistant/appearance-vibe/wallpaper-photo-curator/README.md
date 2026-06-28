# Wallpaper Photo Curator Planning Assets

This folder stores planning assets only for the future Automated Wallpaper and Photo Curator.

## Rules

- No real images go here.
- Sample records in `sample-records.json` and `sample-queue.json` are fictional and safe.
- No API keys or secrets.
- No Reddit or Devvit integration yet.
- No network calls.
- No image processing.
- No student data.
- Future metadata files should avoid copyrighted image URLs until source rules are approved.
- Temp queue rules, queue file format, Approve/Dismiss UI design, and image processing rules are planning/status only—no live queues, UI, or processing.

## Files

- `metadata-schema.json` — JSON Schema for candidate metadata records (includes optional queue fields).
- `sample-records.json` — Three fictional sample metadata records for local validation.
- `queue-file-format.json` — JSON Schema for future queue files.
- `sample-queue.json` — Fictional sample queue file for dry-run validation.

## Status

```bash
bin/chief-of-staff --wallpaper-photo-metadata-status
bin/chief-of-staff --wallpaper-photo-temp-queue-status
bin/chief-of-staff --wallpaper-photo-queue-file-status
bin/chief-of-staff --wallpaper-photo-queue-file-validator
bin/chief-of-staff --wallpaper-photo-approve-dismiss-ui-status
bin/chief-of-staff --wallpaper-photo-image-processing-status
```

See `docs/wallpaper-photo-metadata-schema.md`, `docs/wallpaper-photo-temp-queue-rules.md`, `docs/wallpaper-photo-queue-file-format.md`, `docs/wallpaper-photo-approve-dismiss-ui-design.md`, and `docs/wallpaper-photo-image-processing-rules.md`.
