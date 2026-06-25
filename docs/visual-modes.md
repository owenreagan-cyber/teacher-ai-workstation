# Visual Modes + Vibe Engine

Phase 0E-D adds a reversible visual comfort layer for the Teacher AI Workstation.

The goal is not to make the Mac look huge or distorted. The goal is to keep the 16-inch Retina display on its default scaling while making the parts Owen actually sees every day more comfortable, polished, and personal.

## Core idea

The Vibe Engine is a local, reversible system for switching the Mac between practical visual modes.

It may adjust safe local settings such as:

- Dock size and auto-hide behavior.
- Desktop icon size.
- Desktop label text size when safe to set.
- Finder view defaults where safe.
- Wallpaper folders.
- Screenshot location.
- Mode-specific notes and launch guidance.

It should not:

- Change global display scaling automatically.
- Scrape copyrighted images into commercial folders.
- Store secrets in the repository.
- Configure paid services without explicit approval.
- Bypass macOS privacy prompts.
- Treat personal inspiration images as business-safe assets.

## Display scaling rule

Leave macOS display scaling on Default unless Owen intentionally changes it.

The visual modes should improve readability by tuning app-level and workspace-level details instead of reducing screen real estate globally.

## Modes

### Teacher/Coding Mode

Purpose:

- Teaching work.
- Cursor and Terminal development.
- GitHub review.
- Planning and documentation.
- Chief of Staff work.

Style:

- Clean.
- Calm.
- Low clutter.
- Slight readability bump.
- Professional enough for school or screen sharing.

### Casual Anime Mode

Purpose:

- Relaxed browsing.
- Creative planning.
- Anime inspiration.
- Music.
- Personal writing.
- 3D idea exploration.

Style:

- Anime aesthetic.
- Cozy creative studio.
- Fun and chill, not childish.
- Slightly larger and more visual than Teacher/Coding Mode.
- Balanced so the 16-inch display still feels spacious.

### Future Presentation/Classroom Mode

Purpose:

- Screen sharing.
- Classroom projection.
- Presentations.
- Clean live demos.

This mode is not implemented in the first Phase 0E-D pass.

## Phase 0E-D implementation layers

### D1: Foundation

- Add mode docs.
- Add mode config files.
- Add safe mode scripts.
- Create local folders.
- Apply reversible Dock/Desktop/Finder comfort settings.
- Add status reporting.

No API downloads. No Spotify automation. No Photos automation.

### D2: Wallpaper and image provisioning

- Unsplash for teacher/presentation-safe background candidates.
- Reddit anime sources only for personal/reference-only inspiration.
- Source manifests and attribution notes.
- No automatic commercial approval.

### D3: Photos and widgets

- Prepare image import folders.
- Guide creation of the Photos album `Casual Anime Shuffle`.
- Guide setup of the Photos widget.

### D4: Raycast switcher

- Add a Raycast script command for switching modes.
- Keep Raycast setup assisted because permissions and extensions may require human clicks.

### D5: Spotify playlist automation

- Use Spotify Web API only after Owen creates and approves a Spotify Developer App.
- Store client secrets in 1Password, not the repo.
- Use OAuth scopes only for approved playlist actions.

## Folder layout

The local mode scripts create these folders when run:

```text
~/Pictures/Teacher-AI-Workstation/Wallpapers/Teacher-Coding
~/Pictures/Teacher-AI-Workstation/Wallpapers/Casual-Anime
~/Pictures/Teacher-AI-Workstation/Wallpapers/Presentation
~/Pictures/Teacher-AI-Workstation/Reference-Only/Anime-Inspiration
~/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle
~/Screenshots
```

## Safety and reversibility

Mode scripts should be safe to inspect before running.

They should print what they are doing, avoid destructive operations, and avoid secret handling.

If a setting is too fragile or too user-specific to automate safely, document it instead of forcing it.
