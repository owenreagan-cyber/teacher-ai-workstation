# Wallpaper Photo Curator Planning Assets

This folder stores planning assets only for the future Automated Wallpaper and Photo Curator.

## Rules

- No real images go here.
- Sample records in `sample-records.json` are fictional and safe.
- No API keys or secrets.
- No Reddit or Devvit integration yet.
- No network calls.
- No image processing.
- No student data.
- Future metadata files should avoid copyrighted image URLs until source rules are approved.
- Temp queue rules are planning/status only—no live queues.

## Files

- `metadata-schema.json` — JSON Schema for candidate metadata records (includes optional queue fields).
- `sample-records.json` — Three fictional sample records for local validation.

## Status

```bash
bin/chief-of-staff --wallpaper-photo-metadata-status
bin/chief-of-staff --wallpaper-photo-temp-queue-status
```

See `docs/wallpaper-photo-metadata-schema.md` and `docs/wallpaper-photo-temp-queue-rules.md`.
