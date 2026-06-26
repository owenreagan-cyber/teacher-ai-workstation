# Vibe Panel Roadmap

The Vibe Panel is a future lightweight interface for the Teacher AI Workstation Vibe Engine.

Do not build the app yet. Phase 0E-D6 stays script-first because the workflow still needs proven safety gates for image review, manual Photos import, and future Spotify authorization.

## Existing Interface Layers

1. Raycast commands.
2. Apple Shortcuts buttons.
3. Local shell and Python helpers.

## Future Options

- Raycast commands for quick mode switching.
- Apple Shortcuts buttons for widget-style triggers.
- Menu bar helper for a small always-available control surface.
- SwiftUI app for a local Vibe Panel.
- WidgetKit widget for glanceable status and safe actions.

## Proposed Future Panel Buttons

- Casual Anime.
- Teacher Coding.
- Presentation.
- Review Images.
- Apply Approved Wallpaper.
- Prepare Photos Import.
- Start Playlist.
- Status.

## Safety Gates

- Wallpapers require approval in `approval-manifest.json`.
- Photos stays manual unless a later phase explicitly approves automation.
- Spotify OAuth waits for a later secrets/capability broker phase.
- No secrets go in the repo.
- No unreviewed or unknown-source images move into classroom, business, commercial, or 3D-sale use.
- Display scaling stays untouched.

## Why Script-First

Scripts are easier to inspect, test with a temporary `HOME`, and keep reversible. A real panel should only wrap workflows that are already safe and boring.

The panel can come after Owen has tested:

- image review queue setup.
- approval manifest entries.
- wallpaper dry-runs and approved copies.
- Photos import preparation.
- manual playlist naming.
