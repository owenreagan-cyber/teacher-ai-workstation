# Unsplash Wallpaper Setup

Phase 0E-D4 adds a safer wallpaper automation path while Reddit API access is pending.

Unsplash is the next target for Teacher/Coding and Presentation backgrounds because the API supports public photo search with an application access key and does not require user login for public search workflows.

## Scope

This phase is for:

- Teacher/Coding wallpaper candidates.
- Presentation background candidates.
- Calm, low-clutter school-safe images.

This phase is not for:

- Reddit anime images.
- Photos widget automation.
- Weekly automation.
- Wallpaper auto-rotation.
- Storing secrets in the repo.

## 1Password item

Create or update a 1Password item:

```text
Title: Unsplash Developer App — Teacher AI Workstation
Field: access_key
```

Do not paste the access key into ChatGPT.

## Local config path

Approved local state path:

```text
~/.teacher-ai-workstation/unsplash-config.json
```

The config may contain:

```json
{
  "access_key": "stored locally or supplied from 1Password later"
}
```

This file must not be committed.

## Approved folders

Teacher/Coding candidates:

```text
~/Pictures/Teacher-AI-Workstation/Wallpapers/Teacher-Coding
```

Presentation candidates:

```text
~/Pictures/Teacher-AI-Workstation/Wallpapers/Presentation
```

## Search presets

Start with low-clutter, school-safe searches:

```text
dark desk setup calm workspace
quiet library soft light
calm nature background classroom presentation
minimal abstract background
clean classroom desk
```

## API search dry-run

Run a real metadata-only search without downloading images:

```bash
python3 scripts/unsplash-wallpaper-search.py \
  --api-search \
  --preset teacher_coding_calm \
  --limit 3 \
  --orientation landscape
```

The script should print:

- candidate description
- Unsplash photo ID
- photographer name and username
- image dimensions
- Unsplash page URL
- whether a regular image URL is present
- rate-limit remaining

The script must not print the access key.

## Selected download workflow

Downloads require an explicit reviewed photo ID, a target, and a confirmation flag.

Preview a selected photo without downloading:

```bash
python3 scripts/unsplash-wallpaper-search.py \
  --download-photo-id CCu-16eRBOs \
  --target teacher
```

Actually download the selected candidate and update the manifest:

```bash
python3 scripts/unsplash-wallpaper-search.py \
  --download-photo-id CCu-16eRBOs \
  --target teacher \
  --confirm-download
```

Targets:

```text
teacher
presentation
```

The script should:

- fetch the selected Unsplash photo metadata
- print the selected candidate before download
- refuse to download unless `--confirm-download` is present
- register the Unsplash download event when possible
- save the image to the selected approved folder
- update the local source manifest
- mark the review status as `teacher-candidate`

## Download/review rule

Downloaded images are candidates, not automatically approved.

Default status:

```text
teacher-candidate
```

Images should be reviewed before being used in public slide decks or school-facing material.

## Manifest requirements

Every saved image should update:

```text
~/Pictures/Teacher-AI-Workstation/source-manifest.json
```

Required useful metadata:

- local_path
- source_platform: unsplash
- source_url
- source_title
- creator_or_author
- creator_username
- downloaded_at
- intended_use
- license_status
- review_status
- notes
- unsplash_photo_id
- width
- height

## Rate-limit behavior

Scripts should:

- Use low default limits.
- Print rate-limit remaining when available.
- Avoid loops that repeatedly query the API.
- Support dry-run before download.
- Refuse to run without an access key when network access is required.

## Non-goals

This phase does not:

- Set the desktop wallpaper automatically.
- Create Photos albums.
- Touch Reddit.
- Install weekly automation.
- Store secrets in the repo.
