# Shortcuts Phase 0E Tools

Phase 0E Shortcuts Tools are optional Apple Shortcuts bridges for status and verification only.

They intentionally use:

```text
~/.teacher-ai-workstation/shortcuts/
```

Older Vibe Buttons use:

```text
~/Shortcuts-Scripts
```

The Phase 0E tools use the local state convention under `~/.teacher-ai-workstation` because they are workstation maintenance/status helpers, not mode-switch buttons.

## Install

From the repo:

```bash
bash scripts/install-phase-0e-shortcuts-tools.sh
```

This creates:

```text
~/.teacher-ai-workstation/shortcuts/phase-0e-status.sh
~/.teacher-ai-workstation/shortcuts/image-review-status.sh
~/.teacher-ai-workstation/shortcuts/phase-0e-verify.sh
```

## Manual Apple Shortcuts Setup

1. Open Shortcuts app.
2. Create a new shortcut.
3. Add "Run Shell Script".
4. Set shell to zsh or bash.
5. Paste the full path to one generated script.
6. Set "Pass Input" to stdin or ignore input.
7. Leave "Run as Administrator" off.
8. Name the shortcut.
9. Run it once to test.

Suggested shortcut names:

- `Phase 0E Status`
- `Image Review Status`
- `Phase 0E Verify`

## Safety

These generated scripts:

- run status or verification only.
- do not use `--apply`.
- do not modify Photos.
- do not set wallpaper.
- do not require admin.
- do not call APIs.
- do not use credentials, API keys, OAuth, tokens, or secrets.
- do not change Display scaling.

They expect the repo at:

```text
~/Projects/teacher-ai-workstation
```

If the repo is somewhere else, edit `REPO_DIR` in the generated script.
