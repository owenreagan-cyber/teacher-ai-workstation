# Wallpaper/Photo Rotation Folder Design

## Purpose

This document is a planning-only folder and destination design for the future **Automated Wallpaper and Photo Curator**. It defines where wallpaper candidates, photo-widget candidates, approved outputs, metadata, and dismissed handling should live on Owen's Mac once implementation begins.

This PR is the folder design step only. It does not create folders, fetch images, process images, or automate macOS wallpaper or Photos settings.

## Current Status

```text
Current status: Phase B planning only.
```

Phase D manual folder creation helper is in `docs/wallpaper-photo-manual-folder-creation-helper.md`. Phase E metadata schema is in `docs/wallpaper-photo-metadata-schema.md`. Phase S rotation handoff and safety audit defines readiness gates before any future handoff into rotation folders. See `docs/wallpaper-photo-rotation-handoff-safety-audit.md`.

## Relationship to the Curator Plan

This design extends `docs/appearance-vibe-wallpaper-photo-curator-plan.md` (Phase A). Phase A defined the future curator UX, source model, and safety boundaries. Phase B defines the future folder layout those flows will use.

## Folder Design Principles

- Local-first and human-approval-gated
- Temporary queues stay small and separate from final rotation folders
- Approved outputs are distinct from candidate queues
- Metadata travels with candidates for source traceability
- Dismissed images are deleted later only after explicit cleanup approval
- Conceptual paths only until Owen approves actual folder creation

## Conceptual Root Folder

```text
~/Pictures/Wallpaper Curator/
```

All curator-managed working folders live under this root in the future design. Final rotation folders may also be referenced at the top level of `~/Pictures/` for macOS wallpaper and photo-widget use.

## Conceptual Temporary Candidate Folders

```text
~/Pictures/Wallpaper Curator/Temp Wallpaper Candidates/
~/Pictures/Wallpaper Curator/Temp Photo Candidates/
```

These hold up to 10 wallpaper and 10 photo candidates awaiting Owen's review. They are temporary by design.

## Conceptual Approved Output Folders

```text
~/Pictures/Wallpaper Curator/Approved Wallpaper Queue/
~/Pictures/Wallpaper Curator/Approved Photo Queue/
~/Pictures/Wallpaper Curator/Processed Wallpaper/
~/Pictures/Wallpaper Curator/Processed Photo Widget/
~/Pictures/Wallpaper Rotation/
~/Pictures/Photo Widget Rotation/
```

Approved queues hold images Owen has accepted but not yet processed. Processed folders hold outputs ready for rotation. `Wallpaper Rotation` and `Photo Widget Rotation` are the final destinations the Mac may read for display.

## Conceptual Metadata Folders

```text
~/Pictures/Wallpaper Curator/Metadata/
```

Future metadata records (JSON or similar) would track source URLs, scoring fields, review decisions, and processed output paths. This PR does not create metadata files or databases.

## Conceptual Dismissed Handling

Dismissed candidates should be deleted from temp queues later. No permanent dismissed archive is planned by default. Deletion rules require separate human approval before implementation.

## Future Candidate Lifecycle

```text
approved source
→ metadata-only candidate record
→ temp wallpaper/photo candidate queue
→ local notification
→ approve/dismiss review
→ dismissed candidate deleted
→ approved candidate moved to approved queue
→ processing rules applied
→ processed output moved to wallpaper/photo-widget rotation folder
→ metadata retained for source traceability
```

## Future Folder Permission Model

Future implementation may need:

- read/write access to `~/Pictures/Wallpaper Curator/` and rotation folders
- optional notification permission for review prompts
- no automatic Photos library writes without explicit approval
- no automatic desktop wallpaper changes without explicit approval

Each permission requires a separate human approval gate.

## Future Human Approval Gates

```text
1. Approve conceptual folder design.
2. Approve actual folder creation.
3. Approve metadata file format.
4. Approve temp candidate queue behavior.
5. Approve cleanup/deletion rules.
6. Approve processing destination folders.
7. Approve macOS permissions.
8. Approve notification behavior.
9. Approve image processing rules.
10. Approve any source integration.
```

## Future Cleanup Rules

Temporary queue rules:

```text
maximum 10 wallpaper candidates
maximum 10 photo candidates
candidate queues are temporary
dismissed images should be deleted later
approved images should move forward later
stale candidate cleanup requires separate approval
```

Stale unreviewed candidates may expire only after Owen approves cleanup policy.

## Safety Boundaries

- planning-only
- no folders created
- no image fetching
- no image downloading
- no image processing
- no image deletion implemented
- no folder scanning
- no notifications sent
- no macOS wallpaper changes
- no Photos changes
- no Reddit integration
- no Devvit integration
- no network calls
- no APIs, OAuth, or secrets
- no background jobs or launch agents
- no student-sensitive data
- no real student names
- human approval required before folder creation

## What This PR Does Not Implement

- This PR is planning-only.
- This PR does not create folders.
- This PR does not fetch images.
- This PR does not download images.
- This PR does not process images.
- This PR does not delete images.
- This PR does not scan folders.
- This PR does not send notifications.
- This PR does not change macOS wallpaper settings.
- This PR does not modify Photos or photo widgets.
- This PR does not add Reddit or Devvit integration.
- This PR does not add network calls.
- This PR does not add APIs, OAuth, or secrets.

## Future Implementation Phases

```text
Phase B: Folder and destination design
Phase C: Dry-run folder validator
Phase D: Manual folder creation helper
Phase E: Metadata schema and sample records
Phase F: Temp queue rules
Phase G: Approve/Dismiss UI design
Phase H: Image processing rules
Phase I: Local automation scheduler
Phase J: Approved-source fetcher
```

Phase B is complete as documentation only. Phases C–J remain future work.

## Conceptual Folder Paths (Summary)

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
These are future conceptual destinations only.
This PR does not create these folders.
```

## Future Metadata Fields

Planned metadata fields (not created in this PR):

```text
source name
source URL
candidate URL
original file name
local temporary file name
content type
width
height
aspect ratio
file format
file size
artist/creator if available
license/permission note
NSFW/content flag
duplicate risk
watermark risk
review decision
reviewed date
processed output path
```

```text
This PR does not create metadata files or databases.
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-folder-design-status
bin/chief-of-staff --wallpaper-photo-dry-run-folder-validator
bin/chief-of-staff --wallpaper-photo-folder-creation-status
bin/chief-of-staff --wallpaper-photo-create-folders --dry-run
bin/chief-of-staff --wallpaper-photo-rotation-handoff-safety-status
bin/chief-of-staff --wallpaper-photo-rotation-handoff-validator
bin/chief-of-staff --wallpaper-photo-metadata-status
bin/chief-of-staff --wallpaper-photo-curator-plan-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-folder-design-status.sh
bash scripts/wallpaper-photo-dry-run-folder-validator.sh
bash scripts/wallpaper-photo-create-folders.sh --dry-run
bash scripts/wallpaper-photo-rotation-handoff-safety-status.sh
bash scripts/wallpaper-photo-rotation-handoff-validator.sh
```

See also `docs/wallpaper-photo-dry-run-folder-validator.md` for Phase C dry-run path validation, `docs/wallpaper-photo-manual-folder-creation-helper.md` for Phase D manual creation, and `docs/wallpaper-photo-rotation-handoff-safety-audit.md` for Phase S rotation handoff and safety audit.
