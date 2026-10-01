# cos M1 — Live checks (Owen runs these)

Status: pending · Branch: `feature/cos-m1` · Owner: Owen

The automated tests are synthetic and offline. These checks run against the real Mac:
Ollama, EventKit, Open-Meteo, and Raycast. Run them from Terminal in the repo root
(`~/Projects/teacher-ai-workstation`, or the `taw-cos-m1` worktree before merge).
Tick each box and note anything unexpected.

## 0. Prerequisites

```bash
python3.12 --version                        # 3.12.x
curl -s http://127.0.0.1:11434/api/version  # Ollama is up
ollama list | grep -E 'qwen3.6:35b|gpt-oss:20b'
bin/cos tools                               # creates the state dir (0700), lists 8 read-only tools
stat -f '%Lp' ~/Library/Application\ Support/ChiefOfStaff   # expect 700
```

- [ ] All of the above look right.
- [ ] D1 denies Claude Code access to `~/Library/Application Support/ChiefOfStaff/`
      (applied 2026-10-01; see the review bundle).

## 1. Weather location (one time)

Fill in your own coordinates. Two decimals is enough, since cos rounds to two before sending.

```bash
cat > ~/Library/Application\ Support/ChiefOfStaff/config.json <<'EOF'
{"latitude": 00.00, "longitude": -00.00}
EOF
chmod 600 ~/Library/Application\ Support/ChiefOfStaff/config.json
```

## 2. First EventKit run (grants Calendar and Reminders access)

Build the helper, then run it once for each data type. macOS shows a permission prompt
the first time. Choose **Allow Full Access**.

```bash
swift build -c release --package-path cos/helpers/eventkit-reader
H=cos/helpers/eventkit-reader/.build/release/eventkit-reader
$H status                    # shows current access; never prompts
$H events --days 1           # Calendar prompt → Allow Full Access
$H reminders --due-within-days 1   # Reminders prompt → Allow Full Access
$H status                    # expect {"calendar":"ok","reminders":"ok","status":"ok"}
```

> **About who gets the permission:** the helper is a plain command-line tool, so macOS
> attributes the grant to the app that launches it. For these commands that's Terminal
> (or iTerm). The Raycast **Daily Brief** asks once more for Raycast itself (step 4).
> Revoke anytime in **System Settings → Privacy & Security → Calendars / Reminders**.
> Giving the helper its own identity is listed as a known gap.

- [ ] Both prompts were shown and granted, and `status` reports `ok` for both.
- [ ] `events` output contains only title, start, end, all_day, and calendar fields.

## 3. CLI checks

Each answer should end with a `Tools used:` line. The first question may take 20–60 s while
the model loads.

```bash
bin/cos ask "what time is it"                 # expect Tools used: time.now
bin/cos ask "what's the weather"              # expect Tools used: weather.today
bin/cos ask "how's my Mac"                    # expect Tools used: mac.status
bin/cos ask "what's on my calendar today"     # expect Tools used: calendar.today
bin/cos brief                                 # 15 lines at most; no model used
```

- [ ] Time matches the menu bar clock.
- [ ] Weather matches a weather app (roughly).
- [ ] Mac line matches battery, disk, and memory shown by macOS.
- [ ] Calendar answer matches today's Calendar app.
- [ ] Brief shows date, weather, calendar, reminders, one Mac line, and status highlights.

Kill switch and audit:

```bash
bin/cos stop "live check"
bin/cos ask "what time is it"     # expect: stopped by kill switch (exit 3), no model call
bin/cos brief                     # expect: stopped by kill switch (exit 3)
bin/cos resume
bin/cos audit verify              # expect: OK: chain intact (N records)
```

- [ ] Stop blocks both commands, resume restores them, and the audit chain verifies.

## 4. Raycast import

Follow `apps/raycast-chief-of-staff/README.md`:

```bash
cd apps/raycast-chief-of-staff
npm install
npm run dev        # Raycast imports "Chief of Staff"; then Ctrl-C to stop the dev watcher
```

Then in Raycast: **Settings → Extensions → Chief of Staff**. Set **Path to bin/cos** if
needed, and give **Ask Chief** a hotkey.

- [ ] Hotkey → "what time is it" → answer shows, with `Tools used: time.now` and the model.
- [ ] **Daily Brief** renders (approve the Raycast Calendar/Reminders prompt if shown).
- [ ] `npm run dev` was stopped. Check with `pgrep -fl "ray develop"`, which should print nothing.

## 5. Week of use (exit criterion)

- [ ] Used the hotkey and `cos brief` every school day for a week. Note anything wrong or
      missing for M2.
