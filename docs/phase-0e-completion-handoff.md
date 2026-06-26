# Phase 0E Completion Handoff

Phase 0E adds the visual, vibe, and image-safety foundation for the Teacher AI Workstation.

It is not a product app. It is not the Teacher Chief of Staff agent. It is the workstation/vibe/safety layer that makes later Phase 1 work calmer and safer.

## What Phase 0E Accomplished

- Visual Mode scripts exist for Casual Anime, Teacher Coding, and status.
- Raycast Vibe Switcher templates exist.
- Apple Shortcuts Vibe Buttons scaffold exists.
- Photos/widget setup is documented and manual.
- Image review queue folders are scaffolded.
- Image approval manifest is scaffolded.
- Phase 0E-D6 image review and Vibe tools exist.
- Spotify playlists are documented as manual-only.
- Vibe Panel is documented as roadmap/scaffold only.
- Final status and verification helpers exist.

## Safe And Usable Now

Run status:

```bash
bash scripts/phase-0e-summary.sh
```

Run verifier:

```bash
bash scripts/verify-phase-0e.sh
```

Check image review state:

```bash
python3 scripts/image-review-status.py
```

Optional Raycast status commands can be installed from:

```text
configs/raycast/
```

Optional Apple Shortcuts status tools can be installed with:

```bash
bash scripts/install-phase-0e-shortcuts-tools.sh
```

## What Remains Manual

- Choosing real wallpapers.
- Reviewing image source, license, and intended use.
- Moving candidate images through the review queue.
- Editing `approval-manifest.json`.
- Importing images into Photos.
- Creating the `Casual Anime Shuffle` Photos album.
- Adding desktop or Notification Center widgets.
- Creating Spotify playlists by hand.

## What Remains Scaffold-Only

- Spotify API/OAuth.
- automatic Spotify playlist creation.
- real menu bar helper.
- SwiftUI Vibe Panel app.
- WidgetKit widget.
- automatic desktop wallpaper setting.
- Photos automation.
- Reddit/anime automation.

## What Should Not Be Done Yet

- Do not build the Chief of Staff agent in Phase 0E.
- Do not build a real app yet.
- Do not use OAuth or API keys for Spotify, Reddit, Unsplash, Gmail, or Drive in this phase.
- Do not store secrets in the repo.
- Do not use unknown-source images for classroom, business, commercial, portfolio, or 3D-sale use.
- Do not use Reddit/anime/fan-art/character images for public or commercial work by default.
- Do not change global Display scaling.

## Phase 0E Done Definition

Phase 0E is done when:

- visual modes work.
- Vibe switching works.
- image review queue exists.
- approval manifest exists.
- status/dry-run tools exist.
- Photos and wallpaper workflows are guarded.
- Spotify and Vibe Panel are documented but not automated.
- Reddit API approval is pending and automation is paused.
- `source-manifest.json` status is documented.
- final verifier passes with no critical failures.

## Source Manifest Status

The existing source manifest is local workstation state:

```text
~/Pictures/Teacher-AI-Workstation/source-manifest.json
```

Its schema is documented in:

```text
docs/source-manifest-schema.md
```

Existing provisioning scripts may create or update it when image candidates are downloaded or scaffolded. It is not a repo-tracked config file.

The newer approval manifest is also local workstation state:

```text
~/Pictures/Teacher-AI-Workstation/Image-Review/approval-manifest.json
```

Phase 0E does not require `source-manifest.json` before Phase 1 begins. It is required only when using the image candidate/source workflow. Phase 1 Chief of Staff and Developer Mode can begin as long as the final verifier has no critical failures and image automation remains guarded.

## Why This Prepares Phase 1

Phase 0E reduces visual/workspace friction and gives image workflows a safe review boundary.

That lets Phase 1 focus on:

- Teacher Chief of Staff agent foundations.
- Developer Mode for lessons, tools, and apps.
- lesson planning workflows.
- safe classroom productivity automation.

## If Verification Fails

Check branch:

```bash
git status
```

Pull latest main:

```bash
git switch main
git pull
```

Rerun setup scripts for missing folders:

```bash
bash scripts/prepare-image-review-queue.sh
bash scripts/prepare-photos-widget-folders.sh
python3 scripts/provision-wallpapers.py --init-folders --show-presets
```

Rerun:

```bash
bash scripts/verify-phase-0e.sh
```

If syntax fails, do not merge. Return to Codex with the error.

If warnings are only missing optional local folders, those can be fixed manually with setup scripts.
