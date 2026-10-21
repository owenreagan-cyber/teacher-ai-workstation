# PROMPT — UI-1: Chief's full window (Command Center)

Approved by Owen on 2026-10-20. The design is the "Chief UI Directions" design-lock canvas.
This prompt describes it in full, so you don't need to see the canvas.

## Where you are

- **Worktree and branch:** `~/Projects/taw-ui1`, branch `feature/ui-1`, from `origin/main`
  (Owen creates it).
- **Read first:**
  - `AGENTS.md`
  - `CHIEF-OF-STAFF.md`
  - `docs/DECISIONS.md` (especially D-022 through D-026)
  - `docs/response-blocks.md`
  - `cos/`
  - `apps/chief-desktop/`
- **Build inside the existing `apps/chief-desktop` (Electron + React).** Don't start a new
  app. The `cos` Python core stays the source of all data; the window only renders what
  `cos` returns.
- **Git limits:** don't push or merge.
- **Sandbox:** the light profile is active, so Ollama is reachable. Run fake- and real-model
  checks.
- **Commits:** one commit per section.
- **Not in this build:**
  - the menu bar launcher (UI-2)
  - real agent delegation
  - Canvas planner changes (a separate team is building `bin/canvas-weekly-status`)

## Look

- **Palette:** graphite and white with one blue accent. Each color has one meaning:
  - blue = action and selection
  - amber = needs Owen
  - green = verified or healthy
  - red = failed or destructive
- **Type:** IBM Plex Sans and IBM Plex Mono, **bundled locally** (for example the
  `@fontsource` packages). The renderer must make no network requests.
- **Light and dark modes,** following macOS by default.
- **Readability:** text at least 12 px, and secondary text meets 4.5:1 contrast. Real
  buttons, visible focus rings, and `aria-label` on icon-only buttons.
- **Light tokens:** bg `#F3F4F6`, surface `#FFFFFF`, ink `#15171C`, muted `#545B67`, line
  `#D9DDE3`, accent `#2459C3`, accentSoft `#EAF0FB`, green `#1F7A4D`, red `#9B2C1F`, amber
  `#9A4A06`, amberSoft `#FFF1DE`.
- **Dark tokens:** bg `#0F1115`, surface `#171A20`, ink `#ECEEF2`, muted `#A3AAB6`, line
  `#2C313A`, accent `#3A73E0`, green `#4CC38A`, red `#F08A7E`, amber `#F2B25C`.

## 1. One home snapshot from `cos`, with freshness

- **New command:** `cos home --json`. It returns:
  - `weather`: now, plus a 7-day strip from the existing forecast data, with the place name
  - `calendar` (today)
  - `reminders`
  - `mac`: memory free, CPU load, disk free, battery and power, uptime, loaded model
  - `needs` (section 2)
  - `builds`: the last five merge commits on `main` in the repo, as title and short ref
  - `agents`: always an empty list for now, with `available: false`
- **Per-section freshness:** each section carries `generated_at`, `status`
  (current / updating / stale / unavailable), and a human `reason` when it isn't current.
- **Fast and cached:** it renders from a cache file in the state folder at once, then
  refreshes each source in the background on its own schedule. Suggested intervals:
  - weather 15 min
  - calendar and reminders 5 min
  - Mac 30 s while the window is visible
  - builds 10 min

  One failing source never blanks the others.
- **Stale-card fix:** the window shows each card's freshness label. A card past its
  interval shows **Stale · last checked <time>** and fades its numbers. The greeting
  ("Good morning / afternoon / evening / Working late") is always computed from the current
  time, never from the cache.
- **Mac history:** the main process keeps the last ~30 minutes of memory and CPU samples in
  memory, for small trend lines. They're never written to disk.

## 2. "Needs your decision" and "Suggested next steps" (providers, never the model)

- **New command:** `cos needs --json`. It gathers items from registered **providers**. Each
  item has a stable `id`, `kind` (`decision` | `suggestion` | `info`), `title`, `reason`,
  `source`, `created_at`, and an optional `action` (an open-link, a `cos` command, or a
  deep link).
- **Providers in this build:**
  1. **`config`:** Chief's own setup problems, for example places missing or a search key
     missing.
  2. **`owner_list`:** a file Owen controls,
     `~/Library/Application Support/ChiefOfStaff/needs.json`, for decisions he or a build
     report adds. Seed it with nothing; the docs show the format.
  3. **`canvas`:** runs `bin/canvas-weekly-status --json` if it exists and maps its
     `action_items` (kind, title, reason, deep_link). If it's missing, return a single
     `info` item: "Canvas planner status isn't connected yet."
  4. **`harness`:** if the latest real-model eval report failed certification, add a
     `decision` item.
- **Items are deduplicated by id,** and a resolved item disappears.
- **The model never creates, edits, or ranks these items.**

## 3. The window: rail, Today, chat modes

- **Left rail:** Chief mark and Ready status; Today, Chat, Agents & builds, Mac, Files
  (shown as "later" and disabled); then Settings and a quiet **Stop Chief** at the bottom.
  It collapses to icons below about 1100 px wide.
- **Today page, top to bottom:**
  1. **Header:** the greeting, then "Monday, October 19 · Sims, NC" (from config), with
     **Today's brief** and **Dev Mode** buttons. Dev Mode is disabled with "coming with the
     Mac helper" until that build.
  2. **Two cards side by side:**
     - **Needs your decision** (amber, with a count): only `decision` items, five at most,
       then "View all"
     - **Suggested next steps** (blue, with a count): only `suggestion` items

     Empty state: "Nothing needs your decision."
  3. **Weather:** place, freshness, large current temperature and conditions, high, low,
     and rain, plus a 7-day strip.
  4. **Today** (calendar items with course-code chips, plus the reminders line) and **Mac**
     (memory and CPU tiles with trend lines; disk, battery, and loaded model; healthy or
     attention label), side by side.
  5. **Agent activity:** "No agents running. When Chief delegates work, each agent shows
     here with Working, Waiting or Done, and a Stop button." Next to it, **Recent builds**
     from `builds`.
- **Chat panel** on the right, with a **Split / Focus / Hide** segmented control:
  - The choice is remembered across restarts. Keyboard: ⌘\ toggles Hide.
  - **Focus** collapses the rail to icons and gives the conversation a centered column
    about 780 px wide.
  - An empty chat shows starter buttons: "Summarize today," "Diagnose my Mac," "What needs
    me?" Each sends that text.
  - The existing response blocks keep working in every mode.
- **Keyboard:**
  - ⌘1 through ⌘5 for rail pages
  - ⌘K focuses the chat input (a full command palette comes in UI-2)
  - Esc hides the window

## 4. Settings page (reads and writes `config.json` through `cos`)

- **New commands:** `cos config get --json` and `cos config set <key> <json-value>`. They
  validate against the config schema and reject unknown keys. Writes are atomic, keep the
  file at 0600, and are recorded in the audit log.
- **Sections:**
  - **General:** start at login, screen protection, the hotkey (display only), appearance
    (follows macOS)
  - **Weather places:** home and work with name and coordinates. Edit and **Add a place**,
    where the user types the name, latitude, and longitude; no geocoding in this build.
  - **Search and local model:** auto web search, search limits (display only), the model
    name, how long it stays loaded
- **Footer:** "These settings are saved in config.json in Chief's data folder."
- **Capabilities answer:** update it to say there's now a Settings screen, and drop "no
  settings screen."

## 5. Fixes carried over

- **`desktop.json`:** expand a leading `~` in `cosPath`, with a test.
- **The `npm test` ordering bug:** `test/check-package.test.mjs` "the real build passes the
  check" must build first, or skip with a clear message when `dist/` is missing.
- **Docs:** correct `docs/p1a5-owen-steps.md` to use the full `/Users/...` path, or rely on
  the new `~` support.

## Tests and validation

- **Python:**
  - `cos home` (sections, per-section freshness, one failing source, cache-first render
    data)
  - `cos needs` (each provider, dedupe, the canvas provider when the command is missing or
    present)
  - `cos config get/set` (validation, unknown key rejected, atomic write, file mode, audit
    record)
  - greeting by time of day, including after midnight
- **Desktop:**
  - the Today page renders from a fixture snapshot
  - decisions and suggestions split by `kind`
  - stale label and fade
  - chat mode persistence
  - the rail collapses below the breakpoint
  - Settings round-trips through `cos config`
  - static checks extended: no network in the renderer, fonts bundled, preload bridge
    exactly the allowed functions (add only what's needed, such as `home`, `needs`,
    `configGet`, `configSet`)
- **Commands:**
  - `python3.12 -m unittest discover -s tests/cos -p 'test_*.py'`
  - `python3.12 -m unittest discover -s tests/evals -p 'test_*.py'`
  - `python3.12 evals/harness/run.py --model fake`, then `--model real` on the clean final
    tree (`certification: true`); unload models afterward
  - `cd apps/chief-desktop && npm ci && npm test && npm run typecheck && npm run build`
  - `git diff --check`
  - the 167-command repo set: no new failures

## Docs and report

- **`docs/ui-1-owen-steps.md`:** exact commands to rebuild, sign, and reinstall Chief.app
  (the same flow as P1a.5: `CSC_NAME=1BA6ECA08FD8D21A979A33AF42296F96A9E93885 npm run
  package`, `codesign --verify`, quit Chief, `rm -rf /Applications/Chief.app`, `ditto` the
  build, then `open`). Add a short checklist of what to look at in the new window.
- **`CHIEF-OF-STAFF.md`:** update "Works today / Missing."
- **Report:**
  - commit SHAs per section
  - test counts
  - the harness results, fake and real
  - anything not done, and why
  - Owen's exact next commands: push, PR click steps (merge commit), and the reinstall
  - `git status -sb`
