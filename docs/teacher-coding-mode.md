# Teacher/Coding Mode

Teacher/Coding Mode is the focused work profile for the Teacher AI Workstation.

It should feel clean, readable, calm, and coding-ready without wasting the 16-inch screen.

## Purpose

Use this mode for:

- Cursor coding.
- Terminal work.
- GitHub review.
- Teacher planning.
- Chief of Staff CLI work.
- Documentation.
- School-safe screen sharing.

## Sizing target

Keep macOS display scaling on Default.

Recommended comfort targets:

- Dock size: 40.
- Dock auto-hide: on.
- Recent apps in Dock: off.
- Desktop icon size: 68.
- Desktop label text: 13 or 14 when safe to set.
- Cursor editor font: 15 or 16, configured manually inside Cursor.
- Terminal/Ghostty font: 15 or 16, configured manually inside the terminal app.
- Pointer size: slightly larger than default, configured manually in System Settings if needed.

Do not use exaggerated icon or text sizes.

## Wallpaper direction

Use calm backgrounds such as:

- Dark navy gradient.
- Quiet abstract pattern.
- Low-contrast desk setup.
- Calm library/classroom mood.
- Soft charcoal or dark blue, not pure flat black unless Owen chooses it.

Wallpaper candidates should live in:

```text
~/Pictures/Teacher-AI-Workstation/Wallpapers/Teacher-Coding
```

## Widgets

Keep widgets minimal.

Recommended widgets:

- Calendar.
- Reminders.
- Weather.
- Battery.
- Clock.

Avoid crowding the desktop.

## Raycast behavior

Raycast should eventually expose actions like:

- Open Teacher AI Workstation repo.
- Open Cursor in the repo.
- Open Obsidian vault.
- Run Teacher/Coding Mode.
- Run smoke test.

Raycast extension installation remains assisted, not forced.

## Obsidian behavior

Obsidian should open the repo as a local Markdown vault.

Do not commit `.obsidian/` local state.

Future mode switching may copy approved workspace templates from `configs/obsidian/` into the local untracked `.obsidian/` folder.

## Manual tuning notes

If text still feels too small, adjust app-level fonts first:

- Cursor editor font.
- Terminal/Ghostty font.
- Browser default zoom for specific profiles.

Avoid changing global display scaling unless the default display mode remains uncomfortable after app-level tuning.
