# Wallpaper/Photo Rotation Handoff and Safety Audit

## Purpose

This document defines a local-only planning/status foundation for future **approved local rotation handoff** and a **final safety audit** of the Appearance & Vibe wallpaper/photo curator foundation stack. It combines manual handoff rules, readiness gates, safety checklist coverage, fictional sample readiness reports, and read-only validation—without moving, copying, or deleting files.

This PR adds rotation handoff and safety audit planning/status only. It does not move, copy, delete, or rename files.

## Current Status

```text
Current status: rotation handoff and safety audit planning/status only.
```

Rotation handoff planning, fictional sample readiness report, and read-only validator live in `assistant/appearance-vibe/wallpaper-photo-curator/`. No real rotation, file moves, queue writes, wallpaper changes, or Photos changes exist yet.

## Relationship to Rotation Folder Design

Phase B defined rotation folder layout and destination design. This audit confirms what must pass before any future handoff into those folders. See `docs/wallpaper-photo-rotation-folder-design.md`.

## Relationship to Image Processor Foundation

Phase P defined image processor foundation with output intents and manual-only gates. Processed outputs must not enter rotation folders until processor behavior is separately approved. See `docs/wallpaper-photo-image-processor-foundation.md`.

## Relationship to Scheduler Foundation

Phase Q defined scheduler foundation with run intents and preflight checks. A future scheduler must not trigger handoff until scheduler behavior is separately approved. See `docs/wallpaper-photo-scheduler-foundation.md`.

## Relationship to Notification Foundation

Phase R defined notification foundation with review-ready summary fields. Notifications must not trigger handoff actions. See `docs/wallpaper-photo-notification-foundation.md`.

## Future Rotation Handoff Concept

```text
approved candidate
→ approved image processing plan
→ manual processor approved separately
→ processed output created in a future approved step
→ handoff readiness check
→ manual review
→ future manual copy/move command approved separately
→ future wallpaper/photo rotation folders updated separately
```

This PR does not execute that pipeline.

## Manual Handoff Rules

```text
manual handoff must require explicit user action
manual handoff must never delete source files
manual handoff must never overwrite existing files without future approval
manual handoff must verify destination folder status first
manual handoff must verify metadata status first
manual handoff must verify processing status first
manual handoff must verify queue/review status first
manual handoff must report intended actions before any write behavior exists
```

## Rotation Readiness Gates

```text
folder design status passes
folder creation status passes
metadata status passes
queue file status passes
review UI prototype status passes
image processor foundation status passes
scheduler foundation status passes
notification foundation status passes
source allowlist status passes
simulated discovery status passes
dashboard passes
working tree is clean
```

## Safety Audit Checklist

Checklist coverage includes:

```text
source allowlist
simulated discovery
metadata schema
queue file format
approve/dismiss UI design
review UI prototype
image processing rules
image processor foundation
scheduler foundation
notification foundation
folder design
folder creation helper
dry-run folder validator
rotation handoff
Reddit future-only boundary
Devvit future-only boundary
student data safety
network/API/secrets safety
file write/delete safety
macOS wallpaper/Photos safety
```

## Feature Stack Coverage

```text
Curator plan: foundation complete
Folder design: foundation complete
Dry-run folder validator: foundation complete
Manual folder creation helper: dry-run/create helper complete
Metadata schema: foundation complete
Temp queue rules: foundation complete
Queue file format and validator: foundation complete
Approve/Dismiss UI design: foundation complete
Image processing rules: foundation complete
Local scheduler plan: foundation complete
Approved-source fetcher plan: foundation complete
Source allowlist foundation: foundation complete
Simulated approved-source discovery: foundation complete
Review UI prototype plan: foundation complete
Image processor foundation: foundation complete
Scheduler foundation: foundation complete
Notification foundation: foundation complete
Rotation handoff and safety audit: current PR
```

Appearance & Vibe wallpaper/photo curator foundation stack: complete for now. Live curator implementation: not started.

## Blocked Automatic Actions

```text
no file moves
no file copies
no file deletion
no folder scanning
no image output writes
no queue writes
no wallpaper changes
no Photos changes
no real rotation
no real image processing
no scheduler implementation
no notifications
no network calls
no Reddit integration
no Devvit integration
```

## Human Approval Gates

```text
1. Approve rotation handoff and safety audit.
2. Approve manual handoff rules.
3. Approve readiness gates.
4. Approve safety audit checklist.
5. Approve future manual copy/move behavior separately.
6. Approve future image processor implementation separately.
7. Approve future scheduler implementation separately.
8. Approve future notification implementation separately.
9. Approve future macOS wallpaper/Photos integration separately.
10. Approve any future Reddit/Devvit implementation separately.
```

## What This PR Does Not Implement

- This PR adds rotation handoff and safety audit planning/status only.
- This PR does not move, copy, delete, or rename files.
- This PR does not scan folders.
- This PR does not write image files.
- This PR does not write queues.
- This PR does not change macOS wallpaper.
- This PR does not modify Photos or photo widgets.
- This PR does not implement real rotation.
- This PR does not implement real image processing.
- This PR does not implement a scheduler.
- This PR does not send notifications.
- This PR does not make network calls.
- This PR does not add Reddit or Devvit integration.
- Sample handoff report is fictional/local-only.

## Future Implementation Options

```text
Option A: Pause Appearance & Vibe here and return to Chief of Staff / Teacher Workstation core.
Option B: Add a real dry-run processor implementation in a later PR after explicit approval.
Option C: Add a real manual handoff helper in a later PR after explicit approval.
Option D: Add a real local review UI implementation in a later PR after explicit approval.
Option E: Add real source fetching only after explicit network/API/source approval.
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-rotation-handoff-safety-status
bin/chief-of-staff --wallpaper-photo-rotation-handoff-validator
bin/chief-of-staff --wallpaper-photo-notification-foundation-status
bin/chief-of-staff --wallpaper-photo-scheduler-foundation-status
bin/chief-of-staff --wallpaper-photo-image-processor-foundation-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-rotation-handoff-safety-status.sh
bash scripts/wallpaper-photo-rotation-handoff-validator.sh
```
