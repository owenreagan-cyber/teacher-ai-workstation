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

## 2. EventKit helper: build, sign, and the one-time grant

The helper is `ChiefOfStaffEventKitReader.app` (bundle id `local.chief-of-staff.eventkit-reader`).
cos launches it only through LaunchServices (`open`), so macOS gives the Calendar and
Reminders permission to **this helper's own identity**, not to Terminal or Raycast. The helper
refuses EventKit commands when launched any other way (`wrong_launch`).

> **Permission scope:** macOS has no read-only EventKit tier for reading events. The grant
> you approve is "Full Access". Chief of Staff enforces read-only behavior in its own code:
> the helper has no command that creates, edits, or deletes events or reminders, and it calls
> no EventKit mutation API (a test checks the source). cos itself never prompts, because
> every cos launch sets `COS_EVENTKIT_NO_PROMPT=1`. The only prompts come from the explicit
> commands below.

**2.0 — Clear the grant left by the development incident (2026-10-01).** A test run during
hardening launched the ad-hoc-signed helper, and both prompts were approved. Reset that grant
so the first real grant goes to your signed build:

```bash
tccutil reset Calendar local.chief-of-staff.eventkit-reader
tccutil reset Reminders local.chief-of-staff.eventkit-reader
```

**2.1 — Build and sign with your Apple Development identity.** TCC ties the grant to the code
signature. An ad-hoc signature changes on every rebuild, which can silently reset the grant.

```bash
security find-identity -v -p codesigning        # copy the "Apple Development: …" name
scripts/cos-build-eventkit-helper.sh "Apple Development: <Your Name> (<TEAMID>)"
# expect: Identifier=local.chief-of-staff.eventkit-reader, TeamIdentifier=<TEAMID>,
#         designated => identifier "local.chief-of-staff.eventkit-reader" and anchor apple generic …
```

**2.2 — Confirm attribution (no prompt).**

```bash
APP=cos/helpers/eventkit-reader/build/ChiefOfStaffEventKitReader.app
OUT="$(mktemp)"
open -W -n -g -j --stdout "$OUT" --stderr "$OUT" "$APP" --args identity; sleep 1; cat "$OUT"
# expect "self_responsible":true and "ppid":1 (launched by launchd, not by Terminal)
"$APP/Contents/MacOS/eventkit-reader" status
# expect {"status":"wrong_launch",...}: a bare run is refused, so Terminal can never be granted
```

**2.3 — Grant access once (these two commands show the prompts).** Choose **Allow Full Access**.
The dialog names "Chief of Staff EventKit Reader".

```bash
open -W -n --stdout "$OUT" --stderr "$OUT" "$APP" --args events --days 1; sleep 1; cat "$OUT"
open -W -n --stdout "$OUT" --stderr "$OUT" "$APP" --args reminders --due-within-days 1; sleep 1; cat "$OUT"
open -W -n -g -j --stdout "$OUT" --stderr "$OUT" "$APP" --args status; sleep 1; cat "$OUT"
# expect {"calendar":"ok","reminders":"ok","status":"ok"}
rm -f "$OUT"
```

`open -W` sometimes prints `Unable to block on application` when the helper exits very quickly.
That message is harmless; the output file is complete after the `sleep`.
Revoke anytime in **System Settings → Privacy & Security → Calendars / Reminders**.

- [ ] 2.0 reset done; 2.1 build shows your TeamIdentifier.
- [ ] 2.2 shows `self_responsible: true`, and the bare run is refused.
- [ ] 2.3 prompts named the Chief of Staff helper, and `status` reports `ok` for both.
- [ ] Terminal and Raycast do **not** appear under Calendars or Reminders in System Settings
      (unless you granted them earlier for other reasons).

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
npm ci            # installs exactly what package-lock.json pins
npm run typecheck
npm run dev        # Raycast imports "Chief of Staff"; then Ctrl-C to stop the dev watcher
```

Then in Raycast: **Settings → Extensions → Chief of Staff**. Set **Path to bin/cos** if
needed, and give **Ask Chief** a hotkey.

- [ ] Hotkey → "what time is it" → answer shows, with `Tools used: time.now` and the model.
- [ ] **Daily Brief** renders, and no Calendar/Reminders prompt appears for Raycast.
- [ ] `npm run dev` was stopped. Check with `pgrep -fl "ray develop"`, which should print nothing.

## 5. Week of use (exit criterion)

- [ ] Used the hotkey and `cos brief` every school day for a week. Note anything wrong or
      missing for M2.
