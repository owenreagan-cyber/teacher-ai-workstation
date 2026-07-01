# Appearance & Vibe Automated Wallpaper and Photo Curator Plan

## Purpose

This document is a planning-only design for a future local Mac app/workflow called **Automated Wallpaper and Photo Curator**. It describes how Owen may eventually keep wallpaper and photo-widget rotation folders fresh with human-reviewed candidates from approved sources.

This PR is planning-only. It does not fetch images, download images, process images, create folders, send notifications, or automate macOS wallpaper or Photos settings.

## Current Status

```text
Current status: foundation stack complete for now; live wallpaper/photo curator implementation not started.
```

The Appearance & Vibe wallpaper/photo curator foundation stack is complete for now. Phase B folder design is documented in `docs/wallpaper-photo-rotation-folder-design.md`. This document remains planning/status-only.

No curator runtime, fetcher, review UI, image worker, rotation-folder automation, scheduler, background job, or live wallpaper app exists yet.

## Why This Belongs in Appearance & Vibe

Appearance & Vibe covers how Owen's Mac feels day to day: wallpapers, photo widgets, visual modes, and personal inspiration lanes separate from teaching and business work. A future curator keeps those visuals fresh without mixing unsafe sources into classroom or product folders.

The curator should stay local-first, inspectable, and approval-gated so Owen controls what lands on the Mac.

## Future User Experience

Future intended UX:

```text
1. A scheduled local curator checks approved sources automatically.
2. It keeps up to 10 wallpaper candidates and 10 photo candidates in temporary review queues.
3. It sends Owen a local notification when new candidates are ready.
4. Owen reviews candidates in a local UI.
5. Owen can Approve or Dismiss each candidate.
6. Dismissed candidates are deleted.
7. Approved candidates move to image processing.
8. Processed images are stored in the correct local rotation folders.
9. The app never approves images automatically.
```

## Future Candidate Flow

```text
Approved source list
→ metadata scan
→ candidate scoring
→ limited temp review queue
→ local notification
→ Approve/Dismiss review
→ delete dismissed
→ process approved
→ store in wallpaper rotation or photo-widget rotation folder
```

## Future Source Model

Allowlisted sources only.

Source categories:

```text
Reddit wallpaper/anime/image communities
highly ranked anime wallpaper sites
high-quality photo/picture sites
artist/source pages with clear permission
sites with official APIs or clear usage terms
local folders manually approved by Owen
```

Source rules:

```text
No random blind scraping.
No private accounts.
No paywalled sources.
No login-required sources by default.
No NSFW sources by default.
No source without a clear permission or terms review.
Prefer metadata and source links before downloading full-resolution images.
```

## Reddit and Devvit Decision

```text
The local Mac curator should be the first implementation target.
Reddit may be a future source.
Devvit may be a future Reddit-native companion app.
Devvit should not be the core runtime for local Mac wallpaper/photo automation.
```

Devvit is good for Reddit-native community experiences. Devvit requires Reddit platform review before launch or publishing. Devvit is not the right core runtime for controlling local Mac folders, notifications, wallpaper settings, or photo-widget rotation folders.

A local Mac app/fetcher is the right core runtime for Owen's automation. A future Reddit or Devvit component should be optional and separate.

## Future Fetcher Concept

The future fetcher should eventually:

- run automatically on a schedule
- check only approved sources
- collect metadata first
- limit candidate downloads
- avoid duplicate images
- avoid NSFW content by default
- avoid copyrighted or unclear-source content by default
- avoid hotlinking as a storage strategy
- log candidate source URLs
- keep review queues small
- fail safely without deleting approved images

None of this is implemented in this PR.

## Future Image Scoring Concept

Scoring fields:

```text
source
source URL
candidate URL
title
artist/creator if available
license/permission status
width
height
aspect ratio
file format
file size
estimated wallpaper fit
estimated photo-widget fit
NSFW/content flag
watermark risk
duplicate risk
overall score
```

Preferred wallpaper targets:

```text
3840x2160
2560x1440
1920x1080
3440x1440
5120x2880
```

Preferred phone/photo-widget targets:

```text
1170x2532
1290x2796
1440x3200
1080x2400
```

Format notes:

```text
Preserve original when possible.
Use JPEG/WebP for photos when appropriate.
Use PNG/WebP for sharp art when appropriate.
Use AVIF/WebP only if downstream tools support them.
Do not convert destructively without keeping source reference metadata.
```

## Future Temporary Review Queue

Future design:

```text
maximum 10 wallpaper candidates
maximum 10 photo candidates
dismissed images deleted
approved images move forward
stale unreviewed candidates expire later only after explicit design approval
```

This PR does not create temp folders or queues.

## Future Approve/Dismiss Review

Owen reviews each candidate manually. Approve moves a candidate forward to processing. Dismiss deletes the candidate from the temp queue. The app never auto-approves.

## Future Image Processing Concept

Approved images may eventually be resized, cropped, or converted for wallpaper or photo-widget fit. Processing rules require separate human approval before implementation. This PR does not process images.

## Future Storage Destinations

Conceptual folder names only:

```text
~/Pictures/Wallpaper Rotation/
~/Pictures/Photo Widget Rotation/
~/Pictures/Wallpaper Curator/Temp Wallpaper Candidates/
~/Pictures/Wallpaper Curator/Temp Photo Candidates/
```

```text
These folders are future conceptual destinations only.
This PR does not create them.
```

## Safety Boundaries

- planning-only
- local-first
- no image fetching
- no image downloading
- no image processing
- no temp folders created
- no rotation folders created
- no notifications sent
- no macOS wallpaper changes
- no Photos changes
- no Reddit integration
- no Devvit integration
- no APIs
- no OAuth
- no secrets
- no network calls
- no folder scanning
- no background jobs
- no launch agents
- no NSFW sources by default
- no student-sensitive data
- no real student names
- no school systems
- human approval required before final storage

## Copyright and Source-Terms Boundaries

Only sources with clear permission or reviewed terms may enter the allowlist. Metadata and source links come before full downloads. Unclear license, watermark risk, or commercial-use ambiguity should block automatic promotion.

## NSFW and Content Safety Boundaries

NSFW sources are off by default. Content flags, watermark risk, and duplicate risk belong in scoring. Dismissed candidates are deleted. Human review is required before any image reaches rotation folders.

## macOS Permission Boundaries

Future implementation may need folder access, notification permission, and possibly Photos or wallpaper APIs. Each permission requires explicit design approval. This PR does not request or use those permissions.

## Human Approval Gates

```text
1. Approve source allowlist.
2. Approve metadata-only source check.
3. Approve temp review folder design.
4. Approve notification design.
5. Approve review UI design.
6. Approve image processing rules.
7. Approve destination folders.
8. Approve Reddit source integration, if ever needed.
9. Approve Devvit companion app, if ever needed.
10. Approve automatic schedule.
```

## Future Phases

```text
Phase A: Planning only
Phase B: Local folder and destination design
Phase C: Metadata-only source explorer
Phase D: Candidate queue prototype without downloads
Phase E: Limited approved-source fetcher
Phase F: Local review UI with Approve/Dismiss
Phase G: Image processing worker
Phase H: Rotation folder output
Phase I: Optional Reddit source integration
Phase J: Optional Devvit companion app
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-curator-plan-status
bin/chief-of-staff --wallpaper-photo-folder-design-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-curator-plan-status.sh
bash scripts/wallpaper-photo-folder-design-status.sh
```

See also `docs/wallpaper-photo-rotation-folder-design.md` for Phase B folder layout.

## What This PR Does Not Implement

- This PR is planning-only.
- This PR does not fetch images.
- This PR does not download images.
- This PR does not process images.
- This PR does not create temp folders.
- This PR does not create wallpaper/photo rotation folders.
- This PR does not send notifications.
- This PR does not modify macOS wallpaper settings.
- This PR does not modify Photos or photo widgets.
- This PR does not add Reddit or Devvit integration.
- This PR does not add network calls.
- This PR does not add APIs, OAuth, or secrets.

## Future Ideas Not Included

```text
interactive TUI
Raycast launcher
Mac menu bar launcher
voice control
automatic approval
background watchers without human review
connected Gmail/Drive/Calendar commands
school-system integrations
lesson generation hooks
vector search over images
cloud sync of rotation folders
```
