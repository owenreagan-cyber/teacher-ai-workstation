# Canvas Planner macOS Launcher

```text
Status: macOS app launcher for the Teacher Workstation Canvas/Pacing integration
App:   Teacher Workstation — Canvas Planner
Repo:  ~/Projects/teacher-ai-workstation
```

A lightweight native `.app` bundle that launches the existing local Teacher
Workstation backend and opens the Canvas/Pacing planner. It does **not** rewrite
the UI, duplicate Canvas/Pacing logic, expose secrets, or perform Canvas writes.

## App location

```text
~/Applications/Teacher Workstation - Canvas Planner.app
```

## Install / update

```bash
bin/install-canvas-planner-app
```

Idempotent — rebuilds the bundle and replaces only that app. It does not touch
unrelated apps/files. Re-run after repo changes to refresh the launcher.

## Open

```bash
bin/open-canvas-planner
# or
open "$HOME/Applications/Teacher Workstation - Canvas Planner.app"
```

Spotlight and the Dock index `~/Applications`, so the app is pinnable to the Dock
and searchable like any other Mac app.

## Launch behavior

1. **Health check** — `GET http://127.0.0.1:4310/api/status`. The response must be
   JSON containing the `"overall"` key, so an unrelated service squatting on the
   port is not mistaken for the backend.
2. **Reuse** — if healthy, the backend is reused (never duplicated) and the
   planner URL is opened.
3. **Start** — if not running, the launcher starts `bin/teacher-workstation
   --no-open` from the repo, then polls health (bounded, 15s) before opening.
4. **Direct route** — opens `http://127.0.0.1:4310/#weekly` (Weekly Planning /
   Canvas & Pacing).

## Backend ownership

The launcher tracks whether it started the backend (reuse vs. start). In this
first phase the backend is **left running** after the browser window closes, so
closing a browser tab never kills the planning workspace. No broad process-kill
logic exists; the launcher only reuses an existing healthy backend.

## Local URL

```text
http://127.0.0.1:4310
```

The backend remains bound to `127.0.0.1` only.

## Logs

```text
.local/teacher-workstation/launcher/launcher.log
```

Logs capture: launch timestamp, health status, backend started/reused, startup
failure, and the URL opened. Tokens, Authorization headers, secret URLs, and
student data are never logged.

## Troubleshooting

If the app shows "Teacher Workstation could not start":

1. Open Terminal.
2. Run `bin/teacher-workstation --no-open`.
3. Confirm `http://127.0.0.1:4310/api/status` returns JSON.

If the repository was moved, set `TEACHER_WORKSTATION_REPO` to the new path
before launching, or update the single constant in
`scripts/canvas_planner_app/launcher.sh`.

## Uninstall

```bash
rm -rf "$HOME/Applications/Teacher Workstation - Canvas Planner.app"
```

This removes only the app bundle. It does **not** delete the repo, `.local`
state, Canvas data, owner input, approvals, or deployment ledgers.

## Environment / PATH

GUI apps launched from Finder do not inherit the Terminal `PATH`. The launcher
resolves `python3` from a short fallback list (`$PYTHON` → `python3` →
`/usr/bin/python3` → Homebrew paths). The Teacher Workstation server is stdlib
only and runs on the system Python.

## Signing / Gatekeeper

The app is ad-hoc signed (`codesign --force --deep --sign -`) for personal local
use — no Apple Developer certificate, no secrets. Gatekeeper is not disabled
system-wide. If macOS quarantines the locally-built app, the standard local
resolution (`open` the app once, or `xattr -dr com.apple.quarantine` on the app
only) is safe; `spctl --master-disable` must not be used.

## Icon

The app icon (blue rounded square, weekly grid calendar, green checkmark) is
generated reproducibly by `scripts/canvas_planner_app/generate_icon.py` (pure
stdlib, no Pillow) and packaged as `CanvasPlanner.icns` by
`scripts/canvas_planner_app/build_app.sh`.

## Status

```bash
bin/chief-of-staff --canvas-planner-launcher-status
```

## Future native shell (documented, not implemented)

A later phase may add a Swift + WKWebView native shell (no browser chrome, native
toolbar, app menu, Back/Forward/Refresh, server lifecycle, notifications, Dock
badge, menu-bar integration). This phase keeps the default-browser experience.

## Future unified entry point (documented, not implemented)

This launcher can later evolve into a unified Teacher Workstation entry point for
Home, Today, Chief of Staff, Canvas/Pacing, Curriculum, Materials, Homeroom,
Projects, and System Status. This phase stays Canvas/Pacing focused.
