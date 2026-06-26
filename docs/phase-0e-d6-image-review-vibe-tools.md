# Phase 0E-D6 Image Review and Vibe Tools

Phase 0E-D6 adds safe local helpers around the image review queue, approval manifest, wallpaper preparation, Photos import preparation, Spotify playlist planning, and the future Vibe Panel.

This phase keeps risky integrations scaffolded or manual. It does not download images, call network APIs, modify Photos, use OAuth, set Spotify playlists, change Display scaling, or approve images automatically.

## Built In This PR

Functional local helpers:

- `scripts/add-image-approval-entry.py`
- `scripts/image-review-status.py`
- `scripts/stage-unsplash-candidates-for-review.py`
- `scripts/stage-reference-only-candidates.py`
- `scripts/apply-approved-wallpaper.py`
- `scripts/prepare-approved-photos-import.py`

Shared helper:

- `scripts/image_review_lib.py`

Scaffold/config/docs:

- `configs/spotify-vibe-playlists.json`
- `docs/spotify-vibe-playlists.md`
- `docs/vibe-panel-roadmap.md`
- `docs/phase-0e-d6-image-review-vibe-tools.md`

## Fully Functional

These are usable locally now:

- add one approval manifest entry.
- stage one reference-only candidate.
- stage Unsplash candidate metadata from a local JSON file.
- print review queue and manifest status.
- dry-run approved wallpaper copy.
- copy approved wallpaper with `--apply` after manifest approval and source file presence.
- dry-run approved Photos import copy.
- copy approved Photos widget images with `--apply` after manifest approval and source file presence.

## Dry-Run By Default

These tools are dry-run by default or can be safely run with `--dry-run`:

- `scripts/apply-approved-wallpaper.py`
- `scripts/prepare-approved-photos-import.py`
- `scripts/add-image-approval-entry.py --dry-run`
- `scripts/stage-reference-only-candidates.py --dry-run`
- `scripts/stage-unsplash-candidates-for-review.py --dry-run`

`apply-approved-wallpaper.py` will not set the desktop wallpaper. The `--set-desktop` flag is scaffold-only in this phase.

## Scaffold-Only

These are plans only:

- Spotify playlist automation.
- OAuth and Spotify API work.
- menu bar helper.
- SwiftUI app.
- WidgetKit widget.
- desktop wallpaper setting through macOS automation.

## Safe Workflow

1. Put candidate images in:

   ```text
   ~/Pictures/Teacher-AI-Workstation/Image-Review/Incoming-Candidates
   ```

2. Review the image source, creator, usage note, intended use, and status.
3. Add or update a manifest entry.
4. Move the image manually into the right review folder.
5. Use dry-run helpers to confirm approved wallpaper or Photos import actions.
6. Use `--apply` only after manifest approval and manual review.

## Important Review Rules

- Unknown-source images default to `reference_only` or `rejected_or_hold`.
- Reddit, anime, fan-art, and character images default to `reference_only`.
- Unsplash candidates still require source metadata and human review.
- Classroom presentation use requires `approved_presentation_safe`.
- Business, commercial, public portfolio, and commercial 3D printing uses require explicit licensing/review outside this scaffold.

## Test Commands

Syntax checks:

```bash
python3 -m py_compile scripts/add-image-approval-entry.py
python3 -m py_compile scripts/image-review-status.py
python3 -m py_compile scripts/stage-unsplash-candidates-for-review.py
python3 -m py_compile scripts/stage-reference-only-candidates.py
python3 -m py_compile scripts/apply-approved-wallpaper.py
python3 -m py_compile scripts/prepare-approved-photos-import.py
python3 -m py_compile scripts/image_review_lib.py
```

JSON checks:

```bash
node -e 'JSON.parse(require("fs").readFileSync("configs/spotify-vibe-playlists.json", "utf8"))'
```

Temporary HOME flow:

```bash
TMP_HOME=/private/tmp/teacher-ai-phase-0e-d6-test
env HOME="$TMP_HOME" bash scripts/init-image-approval-manifest.sh
env HOME="$TMP_HOME" python3 scripts/stage-reference-only-candidates.py --filename "anime-reference-example.jpg" --local-path "$TMP_HOME/Pictures/Teacher-AI-Workstation/Image-Review/Reference-Only/anime-reference-example.jpg" --source-platform "reddit" --source-url "unknown" --creator "unknown" --notes "Reference-only test entry."
env HOME="$TMP_HOME" python3 scripts/image-review-status.py
env HOME="$TMP_HOME" python3 scripts/add-image-approval-entry.py --filename "approved-wallpaper-example.jpg" --local-path "$TMP_HOME/Pictures/Teacher-AI-Workstation/Image-Review/Approved-Personal-Wallpaper/approved-wallpaper-example.jpg" --source-platform "manual-test" --source-url "unknown" --creator "unknown" --license-or-usage-note "Test placeholder only." --intended-use "personal_wallpaper" --review-status "approved_personal_wallpaper" --notes "Dry-run-safe test approval."
env HOME="$TMP_HOME" python3 scripts/apply-approved-wallpaper.py --filename "approved-wallpaper-example.jpg" --mode casual --dry-run
env HOME="$TMP_HOME" python3 scripts/add-image-approval-entry.py --filename "approved-widget-example.jpg" --local-path "$TMP_HOME/Pictures/Teacher-AI-Workstation/Image-Review/Approved-Photos-Widget/approved-widget-example.jpg" --source-platform "manual-test" --source-url "unknown" --creator "unknown" --license-or-usage-note "Test placeholder only." --intended-use "photos_widget" --review-status "approved_photos_widget" --notes "Dry-run-safe widget test approval."
env HOME="$TMP_HOME" python3 scripts/prepare-approved-photos-import.py --filename "approved-widget-example.jpg" --dry-run
```

Unsplash local JSON dry-run:

```bash
env HOME="$TMP_HOME" python3 scripts/stage-unsplash-candidates-for-review.py --candidates-json /private/tmp/teacher-ai-unsplash-candidates-test.json --intended-use personal_wallpaper --dry-run
```

## Manual Approval Required

Owen still needs to decide:

- whether a real image is reference-only, personal wallpaper, Photos widget, or presentation-safe.
- whether a source has enough metadata.
- whether creator attribution or licensing is acceptable.
- when to copy reviewed images into final folders.

## Wait For Future Permission

Wait before adding:

- Spotify API/OAuth.
- automatic playlist creation.
- Photos automation.
- real menu bar app.
- SwiftUI Vibe Panel.
- WidgetKit widget.
- automatic desktop wallpaper setting.
