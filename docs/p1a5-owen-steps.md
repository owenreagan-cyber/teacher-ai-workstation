# P1a.5 — Owen's live steps

Do these after the P1a.5 pull request is merged into `main`. Every command runs in Terminal on
your Mac. Signing and the first-launch details are the same as in
`docs/chief-desktop-m15a-guide.md`.

## 1. Update the main checkout

```bash
cd ~/Projects/teacher-ai-workstation
git switch main
git pull --ff-only origin main
git log --oneline -1
```

## 2. Name your weather places (once)

Open the config file:

```bash
open -e ~/Library/Application\ Support/ChiefOfStaff/config.json
```

Inside the outer braces, add these exact lines (put a comma at the end of the line before them):

```json
  "places": {
    "home": {"name": "Sims, NC", "latitude": 35.76, "longitude": -78.06},
    "work": {"name": "Clayton, NC", "latitude": 35.65, "longitude": -78.46}
  }
```

Save, then check that cos still loads it (any typo stops it with a plain error):

```bash
~/Projects/teacher-ai-workstation/bin/cos ask "weather"
```

Expected: an answer that starts with `Sims, NC — `. Without this step, Chief calls your saved
coordinates "Home".

## 3. Point Chief.app at the main checkout (once, if not done already)

```bash
cat ~/Library/Application\ Support/ChiefOfStaff/desktop.json
```

If `cosPath` is not `~/Projects/teacher-ai-workstation/bin/cos`, set it:

```bash
cat > ~/Library/Application\ Support/ChiefOfStaff/desktop.json <<'EOF'
{
  "cosPath": "~/Projects/teacher-ai-workstation/bin/cos",
  "hotkey": "Control+Alt+C"
}
EOF
```

## 4. Rebuild and sign Chief.app

```bash
cd ~/Projects/teacher-ai-workstation/apps/chief-desktop
npm ci
npm test
CSC_NAME=1BA6ECA08FD8D21A979A33AF42296F96A9E93885 npm run package
codesign --verify --deep --strict release/mac-arm64/Chief.app && echo SIGNATURE-OK
```

`npm run package` ends with `package check: … startup files present in app.asar`; if it
prints `FAIL`, stop and send the output to Claude.

## 5. Reinstall in /Applications

Quit the running copy first: **menu bar ring → Quit Chief**. Then replace the app. The first
line deletes the old copy in `/Applications` (only the app; your state folder is untouched):

```bash
rm -rf /Applications/Chief.app
ditto ~/Projects/teacher-ai-workstation/apps/chief-desktop/release/mac-arm64/Chief.app /Applications/Chief.app
open /Applications/Chief.app
```

The dot at the top left should turn green (**Ready**). The menu bar ring now has an **Auto web
search** checkbox (on by default).

## 6. Try these in the window

Type each one into a fresh window (Control+Option+C):

1. `when do the ny rangers play?` — searches the web by itself; the answer shows
   **Searched: when do the ny rangers play** and a collapsed **Sources** list. Click a source:
   it opens in your browser. Then type `and the Islanders?` — a second search for the Islanders.
2. `find files relating to shurley on my mac` — "I can't search files on your Mac yet. That's
   coming in a later build." No search.
3. `how many emails do i have` — "Mail isn't connected yet, so I can't see your inbox." No search.
4. `brief` — the full daily brief (weather, calendar, reminders, Mac), with follow-up buttons.
5. `today's brief` — the same full brief.
6. `weather` — a weather card that starts with **Sims, NC** and buttons for Tomorrow, Hourly,
   5-day forecast, and Clayton weather. Click **Hourly**: a small chart.
7. `make sure you tell me the city` — names Sims, NC (your saved home place).
8. `use my location` — still Sims, NC: Chief uses your saved places, not the Mac's location,
   and says they live in `config.json` (it never mentions a settings screen). Then type
   `do that for me` — Sims, NC again.

Then a three-question check: `what time is it`, then `when do the ny rangers play?`, then
`how many emails do i have`. Each answer should be about its own question only.

Finally, untick **Auto web search** in the menu bar, ask `when do the ny rangers play?` again,
and check that Chief says auto web search is off and offers a **Search the web** button. Tick
it again when done.

If any answer looks wrong, copy it (the **Copy** button) and send it to Claude with the question.
