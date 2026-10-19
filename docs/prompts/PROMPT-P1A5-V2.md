# PROMPT — P1a.5 (v2): Chief's rich messenger

## Where you are

- **Worktree and branch:** `~/Projects/taw-p1a5`, branch `feature/p1a5`, from `main` at
  `237690c`.
- **Read first:**
  - `AGENTS.md`
  - `CHIEF-OF-STAFF.md`
  - `docs/DECISIONS.md` (D-002, D-003, D-009, D-011, D-018, and especially **D-022**, which
    relaxes search and data rules)
  - `cos/`, `apps/chief-desktop/`, `evals/`
- **This prompt replaces** `docs/prompts/PROMPT-P1A5.md`, which is an older draft. Don't
  build from that one.
- **Git limits:** don't push, merge, rebase, or force anything. Owen pushes and opens the PR.
- **Sandbox:** the light profile is active, so Ollama is reachable. Run real-model checks as
  well as fake ones.
- **Commits:** one commit per section, in order. Keep the `cos` core logic in Python; the
  desktop app only renders what `cos` returns.

## 0. Baseline

On the clean tree, run:
- `tests/cos`
- `tests/evals`
- the fake harness
- `python3.12 evals/harness/run.py --model real`

Record the results in `docs/p1a5-baseline.md`. The REL-2 real run had 5 failures: `ho-lunch-001`,
`pe-real-thanks-001`, `pe-real-safe-unload-001`, `pe-real-safe-disk-001`, and `tc-status-001`.
Reproduce them. Unload any model you load when done.

## 1. Fixes before features

- **Certification semantics (D-009):** `certification: true` must mean **every CERT passed
  and** the tree was a clean commit. Today it only checks the clean tree. Fix the flag, and add
  harness tests that a failed CERT, or a dirty tree, gives `certification: false`.
- **Root-cause and fix the 5 real-model failures.** For each one, report the cause and the fix.
  Fix the behavior, not the test, unless the test itself is wrong.
- **Leftover P1a items:**
  - **Greeting:** after midnight and before 5 AM, say "Working late" (or "Good morning");
    never "Good evening".
  - **Brief:** remove legacy status lines that clutter the brief in the Chief window.
  - **Status:** validate the `status()` result field by field, not as a cast.
  - **Disk cleanup:** a code-level guard so Chief never suggests deleting files or emptying
    the trash as a fix.
  - **Social replies:** "thanks", "thank you", "ok", "got it", and "cool" get a fixed short
    reply with no model call, and never use Owen's name.
  - **Unload:** before suggesting an "unload" command, check what is actually loaded
    (`ollama ps`), and only name loaded models.
  - **Harness labels:** distinguish a *warning* from a *suggestion*.
  - **Docs:** remove the stale "sanitize-then-escalate" text from `CHIEF-OF-STAFF.md`.
  - **Packaging check:** after `npm run build`, verify every module the app needs at startup
    exists in the packaged output (asar), so a missing file is caught at build time.

## 2. Request sorting and honest capability answers

- **Router:** `cos/intent.py` classifies each Owen message into exactly one of `time`,
  `weather`, `calendar`, `reminders`, `brief`, `mac_status`, `capabilities`, `web_lookup`,
  `local_files`, `mail`, `social`, or `general`.
  - Deterministic patterns go first.
  - The local model is the fallback, and it returns only a label from that list.
  - "on my mac", "my files", "find the file", and "in Downloads / Documents / Drive /
    iCloud" map to `local_files`.
- **`local_files`, `mail`, and `calendar` never call web search.**
- **Not-built-yet answers come from the registry, never the model:**
  - `local_files`: "I can't search files on your Mac yet. That's coming in a later build."
  - `mail`: "Mail isn't connected yet, so I can't see your inbox."
- **`capabilities`:** a fixed answer generated from the registry and config. It covers what
  Chief can do, what's connected, what isn't yet, and that settings live in `config.json` in
  the Chief state folder (there's no settings screen yet). Chief never invents settings
  screens or menu paths.
- **Brief:** "brief", "today's brief", "daily brief", "morning brief", and "my brief" run the
  full deterministic brief.

## 3. Weather written by code, with named places

- **Config:** add `places`. If `places.home` exists, use it as written. Otherwise, if the
  legacy `latitude`/`longitude` keys exist, migrate them to `places.home` with the name
  "Home". Never invent a city name.
  - Default for new installs: `{"home": {"name": "Sims, NC", "latitude": 35.76,
    "longitude": -78.06}, "work": {"name": "Clayton, NC", "latitude": 35.65,
    "longitude": -78.46}}`.
  - Update the config schema, and keep rejecting unknown keys.
- **No model on weather turns.** Every `weather` answer is written by a deterministic
  formatter from the tool result, beginning with the place name, for example
  "Sims, NC — 61°F, overcast. High 61° · Low 47° · Rain 10%."
  - This covers "tomorrow", "this weekend", "5 day", "hourly", "at work", "what city is that",
    and "use my location".
  - Unknown places get: "I only know Sims (home) and Clayton (work) so far."
- **Owen's exact lines:** in the docs, show the exact JSON Owen adds to his config to set
  `places`. His current config already has the Sims coordinates (35.76, −78.06) and no name.

## 4. Automatic web search (D-022)

- **When to search:** a `web_lookup` intent searches automatically. Owen doesn't type
  "search", and the typed `search …` command still works.
- **The query:** built from Owen's own messages in this conversation. The model may shorten
  or clarify it, but query text must **never** come from tool results, web pages, mail,
  files, or calendar content.
  - A short follow-up ("and the Islanders?") may combine with Owen's previous message, but
    only if that message was also a `web_lookup`.
- **Visibility:** every searched answer shows a "Searched: <exact query>" line.
- **Control:**
  - config `auto_search` (default true), plus a tray toggle "Auto web search"
  - the daily and monthly caps still apply
- **URL check:** remove from every answer any URL that didn't come from that turn's tool
  results.
- **Harness, using Owen's real transcript:**
  - "when do the ny rangers play?" searches automatically
  - "find files relating to shurley on my mac" never searches the web
  - "how many emails do i have" gets the mail-not-connected answer
  - "brief" and "today's brief" give the full brief
  - "weather", "make sure you tell me the city", "use my location", and "do that for me"
    always name Sims, NC, and never mention a settings screen
  - a three-question session: each answer addresses its own question

## 5. Rich answers in Chief.app

- **Answer format:** `cos` returns `blocks` alongside the text. Block types:
  - `text`
  - `weather_now` (card)
  - `forecast_hourly` and `forecast_daily` (simple charts)
  - `sources` (search results: title, site, link id)
  - `searched` (the query line)
  - `suggestions` (2–4 follow-up buttons that send a message)
  - `notice`

  Document the format in `docs/response-blocks.md`.
- **Private resources:** URLs live in a `resources` table that only the main process sees.
  The window gets link IDs, never URLs, and opening a link goes through a validated bridge
  call. Save `blocks` and `resources` in session history so they still work after a relaunch.
- **Rendering:** the window renders each block type, and the home card stays as it is.
- **Tests:**
  - block validation, including unknown types being rejected
  - the renderer receiving no URLs
  - suggestion buttons sending text only
  - static checks updated

## 6. Real-model check and docs

- **Real-model run:** on the final clean tree, `python3.12 evals/harness/run.py --model real`
  must print `certification: true` under the new meaning. Report each suite's counts. Unload
  models afterward.
- **Docs:** update `CHIEF-OF-STAFF.md`'s "Works today / Missing" lists.
- **Owen's live steps:** write `docs/p1a5-owen-steps.md` with the exact commands to rebuild and
  reinstall Chief.app in `/Applications`, plus the 8 live questions above to try in the window.

## Validation

- `tests/cos`, `tests/evals`, `tests/test_dev_guard.py`
- `tools/dev_safety/dev_safety_probe.py --synthetic`
- the fake and real harness
- `cd apps/chief-desktop && npm ci && npm test && npm run typecheck && npm run build` (use
  `--cache "$TMPDIR/npm-cache"` if needed)
- `git diff --check`
- the 167-command repo set: no new failures vs REL-2's final 160/7

## Report

- SHAs per section
- the 5 failures with cause and fix
- baseline vs final harness results, both fake and real
- anything not done, and why
- Owen's exact next commands:
  1. `git push -u origin feature/p1a5`
  2. PR click steps, using a merge commit
  3. the Chief.app reinstall from `docs/p1a5-owen-steps.md`
- `git status -sb`
