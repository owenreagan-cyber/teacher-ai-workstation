# Phase 0E-D2 Wallpaper + Image Provisioning

Phase 0E-D2 adds the content provisioning plan for the Vibe Engine.

This phase prepares a safe pipeline for gathering candidate wallpapers and inspiration images without mixing personal/reference material with teacher or business assets.

## Goals

- Use Unsplash for Teacher/Coding and Presentation wallpaper candidates.
- Use Reddit only for personal/reference-only anime inspiration.
- Save source metadata for every downloaded candidate.
- Keep all downloads local.
- Make the first script dry-run first and opt-in for downloads.
- Avoid Photos, Spotify, and Raycast automation in this phase.

## Non-goals

This phase does not:

- Create Photos albums automatically.
- Set widgets automatically.
- Create Spotify playlists.
- Install Raycast extensions.
- Claim any image is commercial-safe.
- Move anime/reference images into business or 3D commercial folders.

## Source lanes

### Unsplash lane

Use for:

- Teacher/Coding wallpaper candidates.
- Presentation background candidates.
- Calm slide deck visuals.
- Nature, library, classroom, desk, abstract, and low-clutter backgrounds.

Default folders:

```text
~/Pictures/Teacher-AI-Workstation/Wallpapers/Teacher-Coding
~/Pictures/Teacher-AI-Workstation/Wallpapers/Presentation
```

### Reddit anime inspiration lane

Use for:

- Personal wallpapers.
- Casual Anime Mode inspiration.
- Photos widget candidates.
- Reference-only visual inspiration.

Default folders:

```text
~/Pictures/Teacher-AI-Workstation/Reference-Only/Anime-Inspiration
~/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle
```

Reddit images are reference-only by default. They are not teacher/presentation-safe or commercial-safe without review.

## Required source manifest

Every downloaded image candidate should be tracked in:

```text
~/Pictures/Teacher-AI-Workstation/source-manifest.json
```

Each entry should include:

- local_path
- source_platform
- source_url
- source_title
- creator_or_author when available
- downloaded_at
- intended_use
- license_status
- review_status
- notes

## Review statuses

Use these statuses:

```text
reference-only
teacher-candidate
presentation-candidate
approved-for-personal-wallpaper
approved-for-teacher-use
rejected
unknown
```

Default status for Reddit/anime content:

```text
reference-only
```

Default status for Unsplash content:

```text
teacher-candidate
```

## Script behavior

The first version of `scripts/provision-wallpapers.py` should support:

- `--dry-run` to show what it would do.
- `--init-folders` to create folders.
- `--source unsplash` for future Unsplash searches.
- `--source reddit` for future Reddit reference-only searches.
- `--limit` to avoid large downloads.
- `--query` for search terms.
- `--manifest` to print or update manifest location.

The initial version may create folders and manifest placeholders without downloading.

## Safety reminders

- Do not put API keys in the repo.
- Do not paste API keys into ChatGPT.
- Do not store OAuth tokens in Markdown.
- Do not use Reddit/anime images for business/product work by default.
- Keep commercial use separate from personal inspiration.

## Future phases

After D2:

- D3 can guide Photos album and widget setup.
- D4 can add Raycast Switch Vibe commands.
- D5 can add Spotify playlist automation after approved OAuth and secret handling.
