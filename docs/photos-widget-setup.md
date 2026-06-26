# Photos and Widget Setup

Photos and Widget Setup is a safe Phase 0E scaffold for making Casual Anime Mode more visual and personal.

This phase comes after:

1. Visual Modes.
2. Raycast Vibe Switcher.
3. Apple Shortcuts Vibe Buttons.

The goal is to prepare Casual Anime Mode for photo/widget personalization. This is a manual/assisted phase, not full Photos automation.

## Source Boundary

Personal anime/reference images are fine for private wallpapers, widgets, and inspiration. They are reference-only by default.

They are not approved for public classroom materials, business products, commercial 3D printing, public portfolio work, or other public-facing work without review/licensing.

When unsure, keep the image in Reference-Only.

## Folder Plan

Casual Anime wallpaper folder:

```text
~/Pictures/Teacher-AI-Workstation/Wallpapers/Casual-Anime
```

Anime inspiration/reference-only folder:

```text
~/Pictures/Teacher-AI-Workstation/Reference-Only/Anime-Inspiration
```

Photos import folder:

```text
~/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle
```

## Prepare Folders

From the repo:

```bash
bash scripts/prepare-photos-widget-folders.sh
```

The script creates or confirms the folders above and writes:

```text
~/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle/README.txt
```

It does not automate Photos, modify the Photos library, download images, use network calls, or change Display scaling.

## Manual Photos Setup

1. Add personal/reference images to:

   ```text
   ~/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle
   ```

2. Open Photos.
3. Import those selected images.
4. Create a Photos album named:

   ```text
   Casual Anime Shuffle
   ```

5. Add imported images to that album.
6. Do not import huge random folders blindly.
7. Keep anything questionable in Reference-Only.

## Manual Widget Setup

Open Notification Center or desktop widgets.

Add a Photos widget if available. Point or select the album:

```text
Casual Anime Shuffle
```

Optional widgets:

- Weather.
- Clock.
- Battery.
- Calendar.
- Music/Spotify if available.

Keep widgets lightweight and not cluttered.

## Suggested Casual Anime Widget Layout

- Photos widget: medium or large.
- Weather: small.
- Clock: small.
- Battery: small.
- Calendar: small or medium.

## Widget Plan File

This repo also includes a simple human-readable plan:

```text
configs/widgets/casual-anime-widget-plan.json
```

It is only a plan. It does not automate Photos, widget placement, Spotify, or any macOS settings.

## Testing

Run:

```bash
bash scripts/prepare-photos-widget-folders.sh
ls -la ~/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle
cat ~/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle/README.txt
```

## Reversal

To remove this layer:

- Remove widgets from desktop or Notification Center.
- Delete the Photos album if desired.
- Delete local import folder contents only if Owen intentionally wants to remove them.

Deleting the Photos album does not need to delete source files from the local import folder.

## Safety

This scaffold does not:

- automate Photos.
- modify the Photos library.
- download images.
- call Reddit, Unsplash, Spotify, or any network API.
- touch accounts, credentials, passwords, tokens, API keys, OAuth, or secrets.
- change Display scaling.
- change existing Visual Mode scripts.
- change Raycast scripts.
- change Apple Shortcuts scripts.
- alter existing source manifests.
- introduce dependencies.
