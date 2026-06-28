# Wallpaper Photo Curator Planning Assets

This folder stores planning assets only for the future Automated Wallpaper and Photo Curator.

## Rules

- No real images go here.
- Sample records in `sample-records.json`, `sample-queue.json`, and `sample-source-allowlist.json` are fictional and safe.
- No API keys or secrets.
- No Reddit or Devvit integration yet.
- No network calls.
- No image processing.
- No student data.
- Future metadata files should avoid copyrighted image URLs until source rules are approved.
- Temp queue rules, queue file format, Approve/Dismiss UI design, image processing rules, local scheduler plan, approved-source fetcher plan, and source allowlist foundation are planning/status only—no live queues, UI, processing, scheduler, fetcher, or source fetching.

## Files

- `metadata-schema.json` — JSON Schema for candidate metadata records (includes optional queue fields).
- `sample-records.json` — Three fictional sample metadata records for local validation.
- `queue-file-format.json` — JSON Schema for future queue files.
- `sample-queue.json` — Fictional sample queue file for dry-run validation.
- `source-allowlist-schema.json` — JSON Schema for future approved source allowlist files.
- `sample-source-allowlist.json` — Four fictional sample source allowlist entries for dry-run validation.

## Status

```bash
bin/chief-of-staff --wallpaper-photo-metadata-status
bin/chief-of-staff --wallpaper-photo-temp-queue-status
bin/chief-of-staff --wallpaper-photo-queue-file-status
bin/chief-of-staff --wallpaper-photo-queue-file-validator
bin/chief-of-staff --wallpaper-photo-approve-dismiss-ui-status
bin/chief-of-staff --wallpaper-photo-image-processing-status
bin/chief-of-staff --wallpaper-photo-local-scheduler-status
bin/chief-of-staff --wallpaper-photo-source-fetcher-plan-status
bin/chief-of-staff --wallpaper-photo-source-allowlist-status
bin/chief-of-staff --wallpaper-photo-source-allowlist-validator
```

See `docs/wallpaper-photo-metadata-schema.md`, `docs/wallpaper-photo-temp-queue-rules.md`, `docs/wallpaper-photo-queue-file-format.md`, `docs/wallpaper-photo-approve-dismiss-ui-design.md`, `docs/wallpaper-photo-image-processing-rules.md`, `docs/wallpaper-photo-local-automation-scheduler-plan.md`, `docs/wallpaper-photo-approved-source-fetcher-plan.md`, and `docs/wallpaper-photo-source-allowlist-foundation.md`.
