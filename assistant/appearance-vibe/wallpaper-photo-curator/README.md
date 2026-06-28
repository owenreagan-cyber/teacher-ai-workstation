# Wallpaper Photo Curator Planning Assets

This folder stores planning assets only for the future Automated Wallpaper and Photo Curator.

## Rules

- No real images go here.
- Sample records in `sample-records.json`, `sample-queue.json`, `sample-source-allowlist.json`, `sample-discovery-report.json`, `sample-review-ui-state.json`, `sample-image-processing-plan.json`, `sample-scheduler-run-plan.json`, `sample-notification-plan.json`, and `sample-rotation-handoff-readiness-report.json` are fictional and safe.
- No API keys or secrets.
- No Reddit or Devvit integration yet.
- No network calls.
- No image processing, rendering, or file reads/writes.
- No scheduler, launch agents, cron jobs, background jobs, or notifications.
- No student data.
- Future metadata files should avoid copyrighted image URLs until source rules are approved.
- Temp queue rules, queue file format, Approve/Dismiss UI design, image processing rules, local scheduler plan, approved-source fetcher plan, source allowlist foundation, simulated discovery plan, review UI prototype plan, image processor foundation, scheduler foundation, notification foundation, and rotation handoff safety audit are planning/status only—no live queues, UI, processing, rendering, scheduler runtime, notifications, rotation handoff, fetcher, discovery, or source fetching.

## Files

- `metadata-schema.json` — JSON Schema for candidate metadata records (includes optional queue fields).
- `sample-records.json` — Three fictional sample metadata records for local validation.
- `queue-file-format.json` — JSON Schema for future queue files.
- `sample-queue.json` — Fictional sample queue file for dry-run validation.
- `source-allowlist-schema.json` — JSON Schema for future approved source allowlist files.
- `sample-source-allowlist.json` — Four fictional sample source allowlist entries for dry-run validation.
- `sample-discovery-report.json` — Fictional simulated discovery report with candidate-count placeholders.
- `sample-review-ui-state.json` — Fictional sample review UI state with candidate cards and simulated action labels.
- `sample-image-processing-plan.json` — Fictional sample processing plan with output intents and report-only fit/crop strategies.
- `sample-scheduler-run-plan.json` — Fictional sample scheduler run plan with run intents and pause/disable placeholders.
- `sample-notification-plan.json` — Fictional sample notification plan with review-ready summary previews.
- `sample-rotation-handoff-readiness-report.json` — Fictional sample rotation handoff readiness report with gates and safety audit items.

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
bin/chief-of-staff --wallpaper-photo-simulated-discovery-status
bin/chief-of-staff --wallpaper-photo-simulated-discovery-validator
bin/chief-of-staff --wallpaper-photo-review-ui-prototype-status
bin/chief-of-staff --wallpaper-photo-review-ui-state-validator
bin/chief-of-staff --wallpaper-photo-image-processor-foundation-status
bin/chief-of-staff --wallpaper-photo-image-processing-plan-validator
bin/chief-of-staff --wallpaper-photo-scheduler-foundation-status
bin/chief-of-staff --wallpaper-photo-scheduler-run-plan-validator
bin/chief-of-staff --wallpaper-photo-notification-foundation-status
bin/chief-of-staff --wallpaper-photo-notification-plan-validator
bin/chief-of-staff --wallpaper-photo-rotation-handoff-safety-status
bin/chief-of-staff --wallpaper-photo-rotation-handoff-validator
```

See `docs/wallpaper-photo-metadata-schema.md`, `docs/wallpaper-photo-temp-queue-rules.md`, `docs/wallpaper-photo-queue-file-format.md`, `docs/wallpaper-photo-approve-dismiss-ui-design.md`, `docs/wallpaper-photo-image-processing-rules.md`, `docs/wallpaper-photo-local-automation-scheduler-plan.md`, `docs/wallpaper-photo-approved-source-fetcher-plan.md`, `docs/wallpaper-photo-source-allowlist-foundation.md`, `docs/wallpaper-photo-simulated-approved-source-discovery-plan.md`, `docs/wallpaper-photo-live-local-review-ui-prototype-plan.md`, `docs/wallpaper-photo-image-processor-foundation.md`, `docs/wallpaper-photo-scheduler-foundation.md`, `docs/wallpaper-photo-notification-foundation.md`, and `docs/wallpaper-photo-rotation-handoff-safety-audit.md`.
