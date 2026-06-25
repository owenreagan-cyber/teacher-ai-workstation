# Raycast Vibe Switcher

The Raycast Vibe Switcher gives Owen quick commands for changing Visual Modes without remembering Terminal commands.

## Commands

This repo includes Raycast script command templates in:

```text
configs/raycast/
```

Templates:

```text
switch-vibe-casual.sh
switch-vibe-teacher.sh
visual-mode-status.sh
```

## Local install

Raycast script commands should live outside the repo in a local script directory such as:

```text
~/Raycast-Scripts
```

Install or refresh the local copies:

```bash
mkdir -p ~/Raycast-Scripts
cp configs/raycast/*.sh ~/Raycast-Scripts/
chmod +x ~/Raycast-Scripts/*.sh
```

Then in Raycast:

1. Open Raycast.
2. Search for Extensions.
3. Open Extensions.
4. Find Script Commands.
5. Add Script Directory.
6. Choose `/Users/owen/Raycast-Scripts`.

## Usage

In Raycast, search:

```text
Switch Vibe
```

Available commands:

- `Switch Vibe: Casual Anime`.
- `Switch Vibe: Teacher Coding`.
- `Visual Mode Status`.

## Safety

These commands call the already-reviewed mode scripts:

```text
scripts/mode-casual.sh --apply
scripts/mode-teacher.sh --apply
scripts/mode-status.sh
```

They do not:

- change global Display scaling.
- download images.
- touch Spotify.
- touch Photos.
- install Raycast extensions.
- use passwords, tokens, API keys, or account credentials.

## Future widget path

Raycast is the first working interface.

Future interfaces may include:

1. Apple Shortcuts buttons.
2. macOS Shortcuts widgets.
3. A small Vibe Panel app.
4. A true WidgetKit widget later.

Do not build the custom widget until the script and shortcut flows are proven stable.
