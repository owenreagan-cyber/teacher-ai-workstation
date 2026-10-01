# Chief desktop M1.5A: review bundle

```text
Milestone:   M1.5A — Chief desktop shell (compact, persistent)
Branch:      feature/cos-m15a (worktree ~/Projects/taw-cos-m1), from feature/cos-m1 3708de2 (M1 not merged)
Commits:     d23cd3c  cos: sessions, history, status for desktop shell
             efcde38  chief-desktop: M1.5A compact shell
             804dd13  docs: chief-desktop M1.5A guide and review bundle
             (this)   M15A hardening: turn validation (002), minimize removed (010), projector docs (001)
Diff:        SHA-256 e0b859399e395702e49f6bef17b6889e9eb570e2fae7aae5653a4b008df47fc4  (original review range)
             = git diff 3708de2 804dd13 -- . ':(exclude)docs/chief-desktop-m15a-review-bundle.md' | shasum -a 256
Hardening:   SHA-256 2887879d4d8d68bc5e55c1ecbe3a5edecd4918f525106eee4c8a08017eda96ea
             = git diff 804dd13 HEAD -- . ':(exclude)docs/chief-desktop-m15a-review-bundle.md' | shasum -a 256
Python:      170 passed, 0 failed (137 M1, unchanged + 27 M1.5A + 6 hardening)
App:         18 passed, 0 failed (node:test; 14 + 4 hardening) + 198 static checks passed, 0 failed
Typecheck:   npm run typecheck — clean (renderer, main, preload projects)
Build:       npm run build — dist/renderer (Vite) + out/main, out/preload (tsc)
Not done:    no push, no merge; npm run dev, the packaged app, windows, hotkeys not launched
```

## Independent review findings and dispositions (M15A-001 … M15A-010)

| ID | Finding | Disposition |
|---|---|---|
| M15A-001 | A hardware-mirrored projector shows Chief despite content protection. | **Docs fixed.** The guide now opens its live checks with **Classroom projector**: hide Chief with ⌃⌥C before connecting, or set the projector to Extended display (System Settings → Displays → select the projector → Use as: Extended display). New live check **7.8 Mirrored display** records what a real mirrored display shows. Auto-hide on mirroring stays M1.5B work, and the known-gap row remains a classroom blocker until 7.8 is run. |
| M15A-002 | Session turns were not shape-checked, so a wrongly typed field could reach the renderer. | **Fixed in both layers.** Core: `cos/sessions.py:48-68` `check_turn` requires `ts`, `question`, `answer` (str), `tools_used` and `notices` (list of str), `fast_path` (bool), `model` (str or null), and `total_ms` (int ≥ 0, not bool). It runs on every write (`append_turn`, `:107`; an invalid turn is not written, and `cos ask` notes this on stderr) and on every read (`read_session`, `:81-97`; bad lines, including non-JSON lines, are skipped and counted, and extra fields are dropped). `cos history --json` keeps its stdout array unchanged and writes `{"skipped_lines": N}` to stderr (`cos/cli.py:220-224`). Model history uses only valid turns. Shell: `src/main/cos.ts:39-55` rebuilds every turn field by field (`toTurn`, `answerFields`). History drops invalid turns (`:135`), and ask returns `internal` if any field is wrong (`:125-129`). Only known fields are passed on, and brief `lines` must be a list of strings. Tests: 6 Python (`TurnValidationTests`), 4 app. |
| M15A-003 … M15A-009 | **Finding text was not provided to Claude in this pass.** | **Pending.** Dispositions to be added when the findings are supplied. |
| M15A-010 | `minimize()` in the bridge was unused. | **Fixed.** Removed from the preload, the `chief:minimize` handler, and `ChiefBridge`. The static check's allowed list now has 10 functions and 9 invoke channels. The native yellow button still minimizes, and the hotkey restores a minimized window. |

## Scope

**Part 1 — `cos` core (Python, stdlib only, backward compatible)**
- `cos ask --session ID`: up to the last 10 turns (and at most 12,000 characters, oldest dropped
  first) go to the model as history. The completed turn is appended to
  `<state>/sessions/ID.jsonl` (directory 0700, file 0600, `O_NOFOLLOW`, `flock`). Fast-path
  answers are recorded too. A stopped or failed ask appends nothing and creates no file.
- Session IDs must fully match `[a-z0-9-]{1,40}`. Anything else is a usage error (exit 2,
  `error_kind: "usage"`), checked before the runtime is built.
- `cos history --session ID --json`: a read-only turn array. It returns `[]` for a missing
  session, creates nothing, writes no audit record, and works while stopped.
- `cos status --json`: kill switch (and reason), model and fallback model, Ollama reachability and
  loaded models (one 2 s `GET /api/ps` through `egress`), audit `ok`/`empty`/`fail`, and
  version. It makes **no model call and no audit write**, because surfaces poll it every 30 s.
- `ask --json` adds `session_id`, `ts`, and `total_ms`. Every handled error carries
  `error_kind`: `usage`, `stopped`, `model_unavailable`, or `internal`. Exit codes are unchanged
  (internal = 1, same as an uncaught exception before, but with no traceback in `--json` mode).
- Raycast: `apps/raycast-chief-of-staff` is untouched. Its argv (`ask --json Q`, `brief --json`)
  and the fields it reads are unchanged. The new fields are additive.

**Part 2 — `apps/chief-desktop` (Electron + Vite + React + Tailwind)**
- `src/main/`: `main.ts` (window, tray, hotkey, IPC), `security.ts` (CSP, `app://` protocol,
  session lockdown), `cos.ts` (execFile runner), `args.ts` (pure `buildArgs`), `config.ts`
  (`desktop.json`, window state), `trayIcon.ts` (template image drawn in code).
- `src/preload/preload.ts`: the `window.chief` bridge.
- `src/renderer/`: the UI (`App.tsx`), fixed error text and the status dot (`messages.ts`), and icons.
- `test/` (node:test) and `scripts/static-checks.mjs`.

**Part 3 — docs**: `docs/chief-desktop-m15a-guide.md` (Owen's steps) and this bundle.

## Test output

```text
$ python3.12 -m unittest discover -s tests/cos -p 'test_*.py'
Ran 170 tests
OK

New (tests/cos/test_sessions_status.py), all ok:
  SessionIdTests     test_valid_ids, test_invalid_ids_rejected (../x, A, "", 41 chars, a/b, a.b, "default\n", …)
  SessionStoreTests  test_create_append_and_modes (0700/0600), test_missing_session_reads_empty_and_creates_nothing,
                     test_history_capped_by_turns, test_history_capped_by_chars_keeps_newest, test_torn_line_is_skipped
  AskSessionTests    test_session_turns_become_history_and_new_turn_is_appended, test_ask_history_is_capped,
                     test_without_session_nothing_is_recorded_and_json_has_null_session,
                     test_fast_path_records_into_session, test_stopped_ask_with_session_appends_nothing,
                     test_invalid_session_ids_are_usage_errors
  ErrorKindTests     test_model_unavailable, test_usage, test_internal_has_no_traceback, test_stopped_brief
  HistoryTests       test_returns_turns_with_all_fields, test_missing_session_is_empty_and_read_only,
                     test_history_does_not_modify_session, test_history_works_while_stopped
  StatusTests        test_fields_with_ollama_up, test_ollama_down, test_kill_switch_reported_with_reason,
                     test_cli_status_makes_zero_model_calls_and_writes_no_audit, test_cli_status_with_ollama_down,
                     test_audit_states
  TurnValidationTests (M15A-002)  test_each_malformed_line_is_skipped_valid_lines_return (tools_used not a
                     list / item not str, notices missing, fast_path string, total_ms negative / string / bool,
                     model number, answer null, non-JSON line, JSON non-object), test_history_json_array_unchanged_and_
                     skip_count_on_stderr, test_skip_count_zero_when_clean, test_extra_fields_are_dropped,
                     test_invalid_turn_is_never_written, test_malformed_history_lines_are_not_sent_to_the_model
All tests use StateDirTest (COS_STATE_DIR temp directory).

$ cd apps/chief-desktop && npm ci && npm run typecheck && npm test && npm run build
added 321 packages
✔ every action produces the exact expected argv
✔ question is trimmed and kept as one argv element after --
✔ invalid session ids are rejected
✔ oversize, empty, non-text, and NUL questions are rejected
✔ unknown actions are rejected
✔ no argument is ever a shell string
✔ argv reaches cos verbatim, with no shell interpretation      (fake cos; $(…), ;, && and backticks not executed)
✔ the environment is minimal                                   (HOME, LANG, PATH only)
✔ history arrays become a turns envelope
✔ invalid input never runs cos
✔ missing cos and desktop.json errors are setup errors
✔ unparseable output becomes an internal error
✔ cos error kinds pass through
✔ stop and resume succeed on exit 0 and fail otherwise
✔ history drops each malformed turn and keeps the valid ones       (M15A-002, same cases as Python)
✔ history with a non-JSON line from cos is an internal error, not a partial array
✔ ask with any malformed turn field is rejected, never passed on
✔ a valid ask passes only known fields
ℹ tests 18  ℹ pass 18  ℹ fail 0
static checks: 198 passed, 0 failed
dist/renderer/index.html  0.65 kB · assets/index-*.css 14.49 kB · assets/index-*.js 229.33 kB

$ git diff --check   (clean)
```

Packaging smoke test (not launched): `CSC_IDENTITY_AUTO_DISCOVERY=false npm run package --
-c.mac.identity=-` produced `release/mac-arm64/Chief.app`:
- `Identifier=local.chief-of-staff.desktop`, `flags=0x10002(adhoc,runtime)`, entitlement
  `com.apple.security.cs.allow-jit` only.
- `app.asar` holds only `package.json`, `out/main/*`, `out/preload/preload.js`, and
  `dist/renderer/*`, with no `node_modules`.

electron-builder warns that an ad-hoc build with the hardened runtime may fail library validation
at launch. Owen's Apple Development signature (one team ID for every component) doesn't have that
problem. No real identity was used, and the keychain was not touched beyond a read-only
`security find-identity -v -p codesigning` listing, which confirmed that `CSC_NAME=<SHA-1>`
selects one identity.

## Security baseline checklist

Paths are relative to `apps/chief-desktop/` unless they start with `cos/`.

| # | Requirement | Result | Where |
|---|---|---|---|
| 1 | `contextIsolation: true` | PASS | `src/main/main.ts:85` |
| 2 | `nodeIntegration: false` | PASS | `src/main/main.ts:86` |
| 3 | `sandbox: true` | PASS | `src/main/main.ts:87` |
| 4 | `webSecurity: true` | PASS | `src/main/main.ts:88` |
| 5 | devTools only in dev builds | PASS | `src/main/main.ts:89` (`devTools: !app.isPackaged`) |
| 6 | No webview tags | PASS | `src/main/main.ts:90` (`webviewTag: false`); `src/main/security.ts:96` (`will-attach-webview` → `preventDefault`); static check bans `<webview` in renderer |
| 7 | CSP in index.html | PASS | `src/renderer/index.html:6-7` |
| 8 | CSP enforced via session headers | PASS | `src/main/security.ts:82-89` (`onHeadersReceived`, replaces any upstream CSP); `src/main/security.ts:42-57` (`app://` responses carry the header) |
| 9 | CSP has `connect-src 'none'` and the exact required directives | PASS | `src/main/security.ts:7-9`; static check asserts the meta and header strings are identical |
| 10 | `will-navigate` → `preventDefault` | PASS | `src/main/security.ts:94` (applied to every WebContents via `web-contents-created`, `src/main/main.ts:40`); also `will-redirect` at `:95` |
| 11 | `setWindowOpenHandler` → deny | PASS | `src/main/security.ts:97` |
| 12 | Local content only; dev URL only `http://localhost:<port>` and only when `!app.isPackaged` | PASS | `src/main/security.ts:15-20`; load at `src/main/main.ts:117`; renderer served from the bundle by `app://chief/` with a path-traversal check at `src/main/security.ts:47` |
| 13 | Deny all permissions | PASS | `src/main/security.ts:74-76` (request, check, and device handlers all deny) |
| 14 | No network from the app | PASS | `src/main/security.ts:78-80` (`onBeforeRequest` cancels everything except `app://chief/`, plus the dev server and devtools when unpackaged); static checks: no `fetch(`/`XMLHttpRequest`/`WebSocket`/`EventSource`/`sendBeacon` in the renderer, no `node:http(s)`/`net`/`tls`/`fetch(`/`net.request` in main |
| 15 | Preload exposes only `window.chief`, with named functions | PASS* | `src/preload/preload.ts:19-40`; every call uses a literal `chief:*` channel; there is no `send`/`invoke(channel)` passthrough, and `ipcRenderer` is never exposed. *See deviation D1 (`onEvent`) |
| 16 | IPC accepts only the app's own frame | PASS | `src/main/main.ts:240-250` (`event.sender === win.webContents`, plus a frame URL prefix check) |
| 17 | `execFile`, never `exec` or a shell | PASS | `src/main/cos.ts:65-68`; static checks ban `exec(`, `execSync`, `spawn(`, `fork(`, and a `shell:` option in main/preload |
| 18 | One pure `buildArgs(action, params)` with session ID and length checks | PASS | `src/main/args.ts:4-5,33-50`; `--` before the question (`:36`) |
| 19 | Minimal env and timeout | PASS | `src/main/cos.ts:29-35` (PATH, HOME, LANG), timeouts at `:19-26` |
| 20 | `cosPath` from `desktop.json`, with a default and a setup message | PASS | `src/main/config.ts:6-9,17-48`; `src/main/cos.ts:84-88` |
| 21 | JSON parse failure → `{ok:false, error_kind:"internal"}` | PASS | `src/main/cos.ts:101-105` and envelope validation at `:108-121` |
| 22 | Content protection on by default, and every launch starts protected | PASS | `src/main/main.ts:95-97`; toggle at `:148-154` |
| 23 | Window title always "Chief" | PASS | `src/main/main.ts:24,100`; `src/renderer/index.html:10` |
| 24 | Close hides; quit only via the tray or ⌘Q | PASS | `src/main/main.ts:101-106`, `before-quit` |
| 25 | Tray: template image, no text or tooltip | PASS | `src/main/trayIcon.ts` (`setTemplateImage(true)`); `src/main/main.ts:163` (no `setTitle`/`setToolTip`) |
| 26 | Hardened runtime, minimal entitlements | PASS | `electron-builder.yml:27`; `build/entitlements.mac.plist:7` (allow-jit only); Electron fuses at `electron-builder.yml:15-21` (RunAsNode, NODE_OPTIONS, and inspect disabled; asar-only plus integrity) |
| 27 | Session ID validation in the core | PASS | `cos/sessions.py:29,72`; CLI at `cos/cli.py:317` |
| 28 | Status makes no model call | PASS | `cos/cli.py:233-256` (only `ModelClient.loaded_models` → `GET /api/ps`, 2 s); test `test_cli_status_makes_zero_model_calls_and_writes_no_audit` |
| 29 | Turn shape validated before display (M15A-002) | PASS | core `cos/sessions.py:48-68` (write and read); shell `src/main/cos.ts:39-55,125-135` |

## Where the UI's state comes from

| UI element | Source |
|---|---|
| Chat feed turns | `cos history --session default --json`, reloaded after every successful ask. **Fallback:** if that reload fails, the new turn is shown from the `cos ask --json` result plus the question Owen typed (`src/renderer/App.tsx:230`). |
| Answer footer (engine, tools, ms) | Only `fast_path`, `model`, `tools_used`, and `total_ms` from the turn's JSON (`App.tsx:56-66`) |
| Status dot | The latest `cos status --json` (launch, every 30 s, and after every ask, brief, or stop/resume). Amber only while a request this window started is in flight (`messages.ts:24-31`). |
| Stop/Resume label | `status.kill_switch`; disabled when status is unknown (`App.tsx:259`). The tray label comes from a fresh `cos status` taken when the menu opens. |
| Brief card | `cos brief --json` `lines`; display-only, not saved |
| Error cards | Fixed text per `error_kind` (`messages.ts:4-19`). Raw cos errors are never shown, except the shell's own setup message (a path or a `desktop.json` problem). |
| Pin and shield state | **Electron window state**, not cos state. It is owned by the main process and pushed to the renderer (`window-state` event, return value of `setPin`/`setProtection`). |
| Pending bubble and "Thinking…" | The question Owen just typed, shown until cos answers; it is replaced by the cos record |

## Dependencies (all exact-pinned devDependencies; the packaged app ships none)

| Package | Version | Why |
|---|---|---|
| electron | 44.5.1 | Shell runtime (binary downloaded on first use, not at install) |
| electron-builder | 26.15.3 | Packaging (dev only) |
| vite | 8.3.2 | Renderer bundler |
| @tailwindcss/vite | 4.3.3 | Tailwind's official Vite integration (part of Tailwind CSS v4) |
| tailwindcss | 4.3.3 | Styling |
| react / react-dom | 19.3.0 | UI (bundled into `dist/renderer` by Vite) |
| typescript | 7.0.2 | Typecheck and main/preload compilation |
| @types/react, @types/react-dom | 19.3.0 | Types for allowed packages |
| @types/node | 26.6.3 | Types for the main process |

The lockfile has 385 entries, mostly electron-builder's tree. There are no UI component, state,
or HTTP client libraries. The test runner is Node's built-in `node:test`.
`npm ci` reports two install scripts not covered by `allowScripts`: `electron-winstaller` (Windows
only) and, on some runs, `fsevents`. **Neither was approved, and none is needed.**

## Deviations from the prompt (for the reviewer to accept or reject)

| ID | Deviation | Reason |
|---|---|---|
| D1 | The preload exposes `onEvent(listener)`, which is not in the prompt's list. (`minimize()` was removed per M15A-010, so the bridge has 10 functions.) | Tray actions (Daily Brief, Stop/Resume, Screen protection) must reach the window. It is one fixed channel (`chief:event`), main → renderer only, with three event kinds (`brief-requested`, `status-changed`, `window-state`) and no cos payload. The preload replays the last window state to a late subscriber. |
| D2 | `cos ask --json` also returns `total_ms`. | So the answer footer can be rendered from the ask JSON when the history reload fails. Additive. |
| D3 | The shell adds two error kinds, `setup` and `timeout`. | They describe failures before or around a cos call: missing `cos`, a bad `desktop.json`, or an execFile timeout. cos's own kinds are passed through unchanged, and unknown kinds become `internal`. |
| D4 | Copy uses `document.execCommand("copy")`. | `navigator.clipboard` needs a clipboard permission, and the app denies every permission. |
| D5 | Escape hides the window. | A convenience for a summonable window, using the allowed `hide()`. |
| D6 | The renderer is served from a custom `app://chief/` protocol, not `file://`. | It enables CSP response headers in production (`file://` responses don't pass through `onHeadersReceived`) and confines loading to the bundle directory. |
| D7 | TypeScript compiles main and preload; Vite builds only the renderer (no electron-vite). | Fewer dependencies. The preload compiles as a classic script (`tsconfig.preload.json`) so the sandboxed loader needs no `exports`. |

## Known gaps

| Gap | Class |
|---|---|
| **Projector via HDMI or USB-C mirroring.** Content protection removes the window from screen *capture*, but a hardware-mirrored display shows the screen directly, so Chief is probably visible on a mirrored projector. The guide now opens its live checks with **Classroom projector** (hide with ⌃⌥C before connecting, or use Extended display) and adds live check 7.8 (M15A-001). Auto-hiding on a mirrored display is M1.5B work. | **BLOCKER for classroom use until tested; not a code defect** |
| Content protection depends on each capture path honoring macOS window sharing settings, and some ScreenCaptureKit-based apps may not. The live checks (screenshot, QuickTime, AirPlay) are the proof; video-call apps should be tested too. | ACCEPTED-M1.5A, live check |
| Not launched by Claude: `npm run dev`, the packaged app, windows, the tray, the hotkey, or the macOS dialogs. All UI behavior is verified only by typecheck, static checks, and Owen's live checks. | ACCEPTED-M1.5A |
| `cos status` runs `audit verify` over the whole log on every 30 s poll, so its cost grows with the log. | DEFERRED-M2 |
| Session files grow without a limit, and `history` reads the whole file. | DEFERRED-M2 |
| `history` and `status` write no audit records (deliberate: read-only and polled). | ACCEPTED |
| The tray menu opens after a fresh `cos status` call, which takes about 0.1–0.3 s. | ACCEPTED |
| No main-process guard against concurrent asks. The renderer disables input, and IPC accepts only the app's own frame. | ACCEPTED |
| Ad-hoc test package with hardened runtime may fail library validation at launch. Use Owen's identity. | ACCEPTED |
| No app icon (Electron default), no login item, no notarization, no auto-update. | DEFERRED-M1.5B |
| A kill switch set after cos's post-response check but before printing still prints the answer. This is existing M1 behavior and is unchanged. | ACCEPTED-M1 |

## Reviewer instructions

You are an independent security and architecture reviewer. You did not write this code.
- Do not modify files, push, or merge. Do not launch the app, register hotkeys, or open windows.
- You may run `python3.12 -m unittest discover -s tests/cos -p 'test_*.py'` and, in
  `apps/chief-desktop`, `npm ci && npm run typecheck && npm test && npm run build`.
- Scope: `git diff 3708de2 HEAD` on branch `feature/cos-m15a` (verify the SHA-256 above).

**Review focus**
1. **Preload surface.** `src/preload/preload.ts`: exactly the listed functions minus
   `minimize` (M15A-010) plus `onEvent` (D1)? Any way to reach `ipcRenderer` or an arbitrary channel from the page?
2. **execFile usage.** `src/main/cos.ts`, `src/main/args.ts`: is any path to a shell, `exec`, or
   argument injection possible? Does a question beginning with `-` stay a question? Is the
   environment minimal?
3. **CSP.** Are the meta and header values identical and complete? Can anything weaken them in
   dev or prod?
4. **Navigation blocking.** Are `will-navigate`, `will-redirect`, `setWindowOpenHandler`, and
   `will-attach-webview` applied to every WebContents? Is the `app://` handler safe against path
   traversal?
5. **Permission handler.** Are all request, check, and device permissions denied? Does
   `onBeforeRequest` leave any network path open in packaged builds?
6. **Content protection.** Is it on at every launch, and does the toggle behave as described?
   Assess the mirroring gap.
7. **State provenance.** Does any UI element show cos state (answers, footer, status, kill switch,
   models) that did not come from cos JSON? Check the fallback at `App.tsx:230`.
8. **Core additions.** `cos/sessions.py`, `cos/cli.py`: session ID traversal, file modes, caps,
   read-only history and status, `error_kind` values, unchanged exit codes, and Raycast
   compatibility.

**Output format**: a JSON array only, with no prose outside it:

```json
[
  {
    "id": "M15A-001",
    "severity": "BLOCKER | MAJOR | MINOR | INFO",
    "category": "preload | execfile | csp | navigation | permissions | network | content-protection | state-provenance | core | packaging | other",
    "path": "apps/chief-desktop/src/main/cos.ts:65",
    "evidence": "what the code does, quoted or paraphrased, and how you verified it",
    "required_condition": "the condition that must hold for this finding to be closed"
  }
]
```

Return `[]` if you find nothing. Also accept or reject deviations D1–D7, each as an `INFO`
finding with category `other`.
