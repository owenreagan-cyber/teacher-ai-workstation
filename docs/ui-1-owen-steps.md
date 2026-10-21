# UI-1 — Owen's steps (Chief's full window)

Status: UI-1 · 2026-10-21 · Branch `feature/ui-1` (worktree `~/Projects/taw-ui1`)

Chief.app is now a full window: a left rail, the Today page, a chat panel you can split,
focus, or hide, and a Settings page. Everything still comes from `cos`; the window only shows
it.

## 1. After the PR is merged: update the main checkout

```bash
cd ~/Projects/teacher-ai-workstation
git switch main
git pull --ff-only origin main
```

## 2. Optional: look at Today from the terminal first

```bash
bin/cos home
bin/cos needs
bin/cos config get
```

`cos home` lists each section with its freshness (`current`, `updating`, `stale`,
`unavailable`). `cos needs` should print one line, "Canvas planner status isn't connected
yet.", until `bin/canvas-weekly-status` exists.

## 3. Rebuild and sign Chief.app

```bash
cd ~/Projects/teacher-ai-workstation/apps/chief-desktop
npm ci
npm test
CSC_NAME=1BA6ECA08FD8D21A979A33AF42296F96A9E93885 npm run package
codesign --verify --deep --strict release/mac-arm64/Chief.app && echo SIGNATURE-OK
```

`npm ci` installs two new font packages (IBM Plex Sans and Mono, bundled into the app). On a
fresh checkout `npm test` reports one skipped test, "the real build passes the check"; that is
expected, because `npm run package` builds first and then runs the same check.
`npm run package` ends with `package check: … startup files present in app.asar`; if it prints
`FAIL`, stop and send the output to Claude.

## 4. Reinstall in /Applications

Quit the running copy first: **menu bar ring → Quit Chief**. Then replace the app. The first
line deletes the old copy in `/Applications` (only the app; your state folder is untouched):

```bash
rm -rf /Applications/Chief.app
ditto ~/Projects/teacher-ai-workstation/apps/chief-desktop/release/mac-arm64/Chief.app /Applications/Chief.app
open /Applications/Chief.app
```

The window now opens at about 1320 × 860, not as the old compact window.

## 5. What to look at in the new window

- [ ] **Rail:** the Chief mark with a green **Ready** dot; Today, Chat, Agents & builds, Mac,
      and Files (greyed out, "later"); Settings and a quiet **Stop Chief** at the bottom. Make
      the window narrower than about 1100 px: the rail shrinks to icons.
- [ ] **Header:** "Good morning / afternoon / evening, Owen" (or "Working late" after
      midnight), the date, and "Sims, NC". **Today's brief** puts the brief in the chat;
      **Dev Mode** is greyed out ("coming with the Mac helper").
- [ ] **Needs your decision** (amber) says "Nothing needs your decision." **Suggested next
      steps** (blue) is empty, or shows "Store the web search key" if the Keychain has no key.
      Below them: "Canvas planner status isn't connected yet."
- [ ] **Weather:** Sims, NC, a big temperature, high, low, rain, and a 7-day strip, with
      "Updated <time>" at the top right.
- [ ] **Today** lists your events (course codes such as `SM5` in a small chip) and a
      reminders line. **Mac** shows memory and CPU tiles; their trend lines fill in over the
      next minutes. Disk, battery, and the loaded model are below, with **Healthy** or
      **Needs attention**.
- [ ] **Agent activity** says no agents are running. **Recent builds** lists the last five
      merges on `main`, ending with this PR.
- [ ] **Staleness:** put the Mac to sleep for 20 minutes (or turn Wi-Fi off and wait). Weather
      should say **Stale · last checked <time>** with its numbers faded, then refresh to
      "Updated" within a minute of waking.
- [ ] **Chat:** the **Split / Focus / Hide** control at the top right. Focus gives the chat a
      centered column and shrinks the rail. Quit and reopen Chief: the same mode comes back.
      An empty chat shows three starters: Summarize today, Diagnose my Mac, What needs me?
- [ ] **Keyboard:** ⌘1–⌘4 switch pages (⌘5, Files, does nothing yet), ⌘\ hides and shows the
      chat, ⌘K jumps to the chat box, Esc hides the window.
- [ ] **Settings:** Start at login and the hotkey are shown (change start at login from the
      menu bar ring); screen protection toggles; your two places appear with their coordinates.
      Click **Add a place**, type `Test place`, `35.70`, `-78.10`, click **Add**: it appears
      in the list, and `bin/cos config get` shows it too. Remove it again by editing
      `config.json` (the window has no Remove button yet). Typing `95` as a latitude shows an
      error and saves nothing.
- [ ] **Light and dark:** switch macOS appearance (System Settings → Appearance): the window
      follows it.
- [ ] **Ask "what can you do?"**: the answer now mentions the Settings screen.

If something looks wrong, take a screenshot (turn **Screen protection** off first, or the
window comes out blank) and send it to Claude.

## The needs.json file (optional)

Decisions you (or a build report) want on the Today page go in
`~/Library/Application Support/ChiefOfStaff/needs.json`. Chief never writes this file, and it
starts empty (there is no file until you make one):

```json
{
  "items": [
    {
      "id": "pick-sm5-title",
      "kind": "decision",
      "title": "Pick the SM5 homework title",
      "reason": "Canvas titles must match before Friday.",
      "created_at": "2026-10-20T09:00:00-04:00",
      "action": {"type": "page", "label": "Open Settings", "page": "settings"}
    }
  ]
}
```

- `kind` is `decision`, `suggestion`, or `info`. `action` is optional: `{"type": "open_link",
  "label": …, "url": "https://…"}`, `{"type": "page", "label": …, "page": "today" | "chat" |
  "agents" | "mac" | "settings"}`, or `{"type": "command", "label": …, "command": …}` (the window
  only copies the command; it never runs it).
- Add `"resolved": true` to an item to make it disappear. The same works for an item from
  another provider: `{"id": "config:search-key", "resolved": true}` hides that suggestion.
- A typo makes the whole file show as one note, "needs.json couldn't be read", with the reason.
