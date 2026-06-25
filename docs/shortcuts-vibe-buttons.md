# Apple Shortcuts Vibe Buttons

Apple Shortcuts Vibe Buttons are the next interface layer after the Raycast Vibe Switcher. They let Apple Shortcuts act like button/widget-style access to Visual Modes without requiring Owen to remember Terminal commands.

This phase uses local shell scripts as the bridge between Apple Shortcuts and the existing Visual Mode scripts. The Visual Mode scripts remain the source of truth:

```text
scripts/mode-casual.sh --apply
scripts/mode-teacher.sh --apply
scripts/mode-status.sh
```

This phase does not build a full custom macOS app. It also does not build a true WidgetKit widget yet.

## Install

From the repo:

```bash
bash scripts/install-shortcuts-vibe-buttons.sh
```

The installer creates or refreshes:

```text
~/Shortcuts-Scripts/vibe-casual.sh
~/Shortcuts-Scripts/vibe-teacher.sh
~/Shortcuts-Scripts/vibe-status.sh
```

Each local script changes into:

```text
~/Projects/teacher-ai-workstation
```

Then it calls the reviewed Visual Mode scripts in this repo.

## Test

After installing, run:

```bash
bash ~/Shortcuts-Scripts/vibe-status.sh
bash ~/Shortcuts-Scripts/vibe-casual.sh
bash ~/Shortcuts-Scripts/vibe-teacher.sh
```

## Manual Apple Shortcuts Setup

1. Open the Shortcuts app.
2. Create a new Shortcut.
3. Add action: Run Shell Script.
4. Set shell to `/bin/bash` if available.
5. For Casual Anime, command:

   ```bash
   /Users/owen/Shortcuts-Scripts/vibe-casual.sh
   ```

6. Name it:

   ```text
   Vibe: Casual Anime
   ```

7. Repeat for Teacher Coding:

   ```bash
   /Users/owen/Shortcuts-Scripts/vibe-teacher.sh
   ```

   Name:

   ```text
   Vibe: Teacher Coding
   ```

8. Repeat for Status:

   ```bash
   /Users/owen/Shortcuts-Scripts/vibe-status.sh
   ```

   Name:

   ```text
   Vibe: Visual Mode Status
   ```

Owen can optionally add the Shortcuts to the menu bar, Dock, or widgets if macOS offers those options.

## Safety

Keep these shortcuts local and reversible. To remove this layer, delete:

```text
~/Shortcuts-Scripts
```

Then delete the Shortcuts from the Shortcuts app.

This scaffold does not:

- change global Display scaling.
- install dependencies.
- use network calls.
- use accounts, credentials, passwords, tokens, API keys, OAuth, or secrets.
- touch Photos.
- touch Spotify.
- touch wallpapers.
- touch Raycast setup.
- touch browser profiles.
- touch iCloud.

## Future Path

The intended interface path is:

1. Raycast commands.
2. Apple Shortcuts buttons.
3. Menu bar helper.
4. Real WidgetKit widget or small macOS Vibe Panel app.
