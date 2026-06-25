# Casual Anime Mode

Casual Anime Mode is the relaxed creative profile for the Teacher AI Workstation.

It should feel like a cozy anime creative studio: fun, chill, personal, and inspiring without becoming cluttered or oversized.

## Purpose

Use this mode for:

- Relaxed browsing.
- Music.
- Personal writing.
- Anime inspiration.
- Creative planning.
- 3D idea exploration.
- Casual Obsidian notes.

## Sizing target

Keep macOS display scaling on Default.

Recommended comfort targets:

- Dock size: 48.
- Dock auto-hide: on unless Owen later prefers it visible in Casual Mode.
- Recent apps in Dock: off.
- Desktop icon size: 80.
- Desktop label text: 14 or 15 when safe to set.
- Cursor editor font: 16 if coding casually.
- Terminal/Ghostty font: 16.
- Pointer size: slightly larger than default if useful.

Do not use giant or distorted UI settings. Avoid 128px desktop icons by default.

## Vibe direction

Casual Anime Mode should feel:

- Anime aesthetic.
- Cozy.
- Creative.
- Chill.
- Slightly more visual than Teacher/Coding Mode.
- Still practical on a 16-inch screen.

Good inspiration categories:

- Favorite characters.
- Cozy anime rooms.
- Cool anime workstations.
- Lofi/chill scenes.
- Night city anime.
- Soft neon.
- Fantasy school/library.
- 3D print idea references.

## Wallpaper folders

Use:

```text
~/Pictures/Teacher-AI-Workstation/Wallpapers/Casual-Anime
~/Pictures/Teacher-AI-Workstation/Reference-Only/Anime-Inspiration
~/Pictures/Teacher-AI-Workstation/Photos-Import/Casual-Anime-Shuffle
```

## Copyright and reference boundary

Anime character art, fan art, Reddit images, and reference images are personal/reference-only unless separately reviewed.

They are fine for private inspiration, local wallpapers, and personal widgets.

They are not approved for:

- Commercial 3D printing.
- Product listings.
- Business branding.
- Public school slide decks.
- Customer/client products.

Use `docs/image-source-policy.md` before moving any image from reference-only use into teacher materials or business/product work.

## Photos widget idea

Create a Photos album named:

```text
Casual Anime Shuffle
```

Use it for the Photos widget after importing approved personal images.

The first implementation should prepare folders and instructions. Full Photos automation can be explored later after manual workflow is proven.

## Spotify playlist ideas

Future Spotify automation may create playlists such as:

- Lofi Anime Coding.
- Night Drive Synthwave.
- Chill J-Pop Focus.
- Video Game Study.
- Creative 3D Design.
- Teacher Planning Calm.

Spotify automation requires a Spotify Developer App, OAuth approval, and safe secret handling through 1Password or another approved local mechanism. It should not store Spotify secrets in the repo.

## Raycast behavior

Future Raycast command:

```text
Switch Vibe -> Casual Anime
```

Potential actions:

- Run `scripts/mode-casual.sh`.
- Open Casual Anime wallpaper folder.
- Open Photos import folder.
- Open Spotify playlist.
- Open Obsidian vault.

## Manual tuning notes

If Casual Mode feels too busy, reduce widgets first.

If Casual Mode feels too small, increase app fonts before changing global display scaling.
