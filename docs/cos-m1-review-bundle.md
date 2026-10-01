# cos M1 — Review bundle

```text
Milestone:        M1 — Simple Siri (fully local, read-only)
Branch:           feature/cos-m1 (worktree ~/Projects/taw-cos-m1), from main 31cb330
Original review:  31cb330..d7bbbee, diff SHA-256 3c505e7fac121c5f3aa51d55b2168164989291c6a7343f7d6bc0922e1dffb36a
Hardening pass:   4ce9521..<hardening commit> (one checkpoint: COS-M1-001..005 plus addendum A-F)
Hardening diff:   SHA-256 6d3ba006e72e8dba1b8a816dd65b1940a7a79319d34bf8d2a36acac2c40b4964
                  = git diff 4ce9521 <hardening commit> -- . ':(exclude)docs/cos-m1-review-bundle.md' | shasum -a 256
Tests:            114 passed, 0 failed (83 original + 31 new)
                  python3.12 -m unittest discover -s tests/cos -p 'test_*.py'
Not done:         no push, no merge
```

**Entry point.** `bin/cos` is the public entry point for the Chief of Staff, and the Raycast
extension calls it. `bin/chief-of-staff` is legacy: `cos` may wrap its read-only status commands
(M1 wraps three, each gated by a static contract check), but new features are not added to it.

## Development incident during this pass (read first)

The hardening task said not to trigger Calendar or Reminders permission. One test triggered it.

1. **What happened.** A new regression test ran `cos brief` through the real CLI. The rebuilt
   helper `.app` was at its default path, so cos launched it for real with `events` and
   `reminders`. Before this pass, the helper prompted when access was undetermined. Both prompts
   appeared and were approved within the test's 15-second window.
2. **Current state.** `status` (read-only, no prompt) reports `calendar: ok`, `reminders: ok`
   for the **ad-hoc-signed** helper identity `local.chief-of-staff.eventkit-reader`.
   Terminal and Raycast did not receive a grant from this; the helper was its own responsible
   process.
3. **Data.** The events and reminders read during that test went only to temporary files in a
   temporary test state directory. Both were deleted when the test finished. Nothing was
   printed, logged to a persistent audit, or committed.
4. **Fixes in this checkpoint:**
   - every cos launch passes `COS_EVENTKIT_NO_PROMPT=1` (verified through `open --env`), so
     cos itself can never prompt;
   - `tests/cos/support.py` points the default helper path at a nonexistent location and makes
     any test that tries to run `/usr/bin/open` or the helper fail;
   - the CLI brief test uses synthetic tools.

   After these fixes the suite takes 2 s instead of 32 s, and no helper process runs.
5. **Owen action.** Reset the grant before the live checks: `docs/cos-m1-live-checks.md`
   step 2.0 (`tccutil reset Calendar|Reminders local.chief-of-staff.eventkit-reader`). I did
   not change TCC state myself.

## Independent findings and dispositions

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| COS-M1-001 | MAJOR | A model response that arrives after `cos stop` could still be shown | **Fixed.** `Agent._model_turn` checks the gate before the request and again immediately after the response returns, before tool calls are interpreted or text is returned. A post-response deny audits `decision(subject=model_call, phase=after_response, allowed=false)` and `model_response_discarded`, then raises `Stopped`, and the CLI prints only the stopped error. No cancellation machinery. |
| COS-M1-002 | MAJOR | EventKit grant attributed to Terminal or Raycast | **Fixed.** The helper is now `ChiefOfStaffEventKitReader.app` with a stable bundle id, launched only via LaunchServices (`open -W -n -g -j --env COS_EVENTKIT_NO_PROMPT=1 --stdout F --stderr F App --args …`). The helper refuses EventKit commands (`wrong_launch`) unless it is inside the expected bundle **and** is its own TCC-responsible process. Docs state that macOS has no read-only EventKit tier and read-only behavior is enforced in code. Verification below. |
| COS-M1-003 | MINOR | The egress claim was broader than the mechanism | **Fixed.** `egress.py` docstring now scopes itself to cos's own HTTP and documents the subprocess boundary. New `cos/tools/script_contract.py` statically checks each wrapped `bin/chief-of-staff` command (details below). A violating command is **not registered**; its reason goes to `registry.disabled` and `cos tools` shows it as DISABLED. |
| COS-M1-004 | MINOR | A missing audit log was reported as healthy | **Fixed.** The first append creates `audit.initialized` (0600). `verify` returns `ok`, `uninitialized` (no log, no marker), or `fail` (tampered, or marker present while the log is missing or empty). `cos audit verify` prints OK / EMPTY / FAIL and exits 1 on FAIL. |
| COS-M1-005 | MINOR | Model-call authority decisions were not audited | **Fixed.** `PolicyGate.check_model_call(phase)` writes a `decision` record (`subject=model_call`, `phase`, `allowed`, `rule`, `reason`) for both allow and deny. Tool decisions now carry `subject=tool_call`. |

### Addendum

| Item | Result |
|---|---|
| A. Signing and LaunchServices | `scripts/cos-build-eventkit-helper.sh [identity]` builds the `.app` and signs it, ad-hoc by default. I tested ad-hoc only and never touched the keychain. Owen runs it with `"Apple Development: <Name> (<TEAMID>)"` (live checks 2.1). Launch is through `open`, and attribution was verified without a prompt (below). |
| B. Known-gaps table | Below. Every gap is classified BLOCKER / ACCEPTED-M1 / DEFERRED-M2+. |
| C. Legacy label | Brief lines copied from wrapped `bin/chief-of-staff` output now read `Workstation status (legacy): …`. The legacy scripts are unchanged. |
| D. Latency | `model_call.model_ms`, `tool_result.tool_ms`, and request-closing records (`answer`, `request_stopped`, `request_failed`, and brief `answer`) carry `model_ms`, `tool_ms`, `total_ms`. |
| E. Entry point | Stated in `CHIEF-OF-STAFF.md` §3 "Entry points" (and its decision list) and at the top of this bundle. |
| F. Raycast hygiene | `.gitignore` covers `apps/raycast-chief-of-staff/node_modules/`, `dist/`, the generated `raycast-env.d.ts`, and the helper `build/`. `package-lock.json` is committed. |

## EventKit architecture result (COS-M1-002 / addendum A)

The helper was verified without any permission prompt. `identity` uses no EventKit; `status` only
reads `authorizationStatus`, which never prompts.

| Launch | `ppid` | responsible pid | `self_responsible` | `events` / `status` |
|---|---|---|---|---|
| Bare `Contents/MacOS/eventkit-reader` from a shell | shell | 686 = `/System/Applications/Utilities/Terminal.app` | false | refused: `wrong_launch` |
| `open … App --args identity` (LaunchServices) | 1 (launchd) | itself | **true** | allowed |
| Same path through cos's Python launcher (minimal env) | 1 | itself | true; `no_prompt: true` (env reached the helper) | allowed |

Before the incident above, `status` via LaunchServices returned `not_determined` for both, which
shows the helper's TCC identity is separate from Terminal's. The responsible pid comes from
`responsibility_get_pid_responsible_for_pid` via `dlsym`. If that API is unavailable the helper
fails closed (`wrong_launch`).

Signing: an ad-hoc build gives `Identifier=local.chief-of-staff.eventkit-reader`,
`Signature=adhoc`, and `designated => cdhash …`. That changes on every rebuild, so a grant can be
orphaned. An Apple Development signature gives a designated requirement of identifier plus team,
which is stable across rebuilds.

The read-only surface is enforced by tests: the helper's `case` commands are exactly `events`,
`reminders`, `status`, `identity`, and `--version`; the source contains no EventKit mutation API
(`save(`, `remove(`, `commit(`, …); and every EventKit command calls `requireOwnIdentity()`.

## COS-M1-003 — static contract for wrapped status commands

For each wrapped flag, `check_flag` scans the code that actually runs:
- top-level `bin/chief-of-staff` statements before the argument loop (other flags' `if` blocks
  and uncalled functions are skipped);
- the flag's dispatch arm;
- every function called from those, transitively;
- every script launched via `bash`/`sh`/`source`/`python`, recursively.

It rejects:
- network-capable commands (curl, wget, nc, ssh, git fetch/push, ollama, open, osascript, …)
  and `/dev/tcp|udp`;
- mutating commands (rm, mv, tee, mkdir, …) and file redirections other than `/dev/null`;
- `eval`, `bash -c` / `python -c`, awk `system()`/pipes/redirects, `sed -i`, dynamic command
  names, and unresolvable launched scripts;
- in Python: network, subprocess, and file-mutation imports or calls (via `ast`).

Results on the real repo:
- `--daily-status`, `--next-action`, `--local-llm-workstation-status`: **0 violations**.
  The checker visited the dispatch arm, `resolve_repo_root`, `is_repo_root`, `script_dir`,
  `source_dir`, `die`, `usage`, and the launched script.
- `--approval-queue-status` (not wrapped): flagged, because
  `scripts/canvas_llm_phase22/approval_queue.py:272` calls `.unlink()`.

## Files changed in the hardening checkpoint

```text
new:      cos/tools/script_contract.py               static network-free/read-only contract
new:      scripts/cos-build-eventkit-helper.sh        build + sign ChiefOfStaffEventKitReader.app
new:      tests/cos/test_hardening.py                 27 regression tests (001-005, D, helper source)
new:      apps/raycast-chief-of-staff/package-lock.json
moved:    cos/helpers/eventkit-reader/Sources/eventkit-reader/Info.plist -> App/Info.plist (bundle plist, LSUIElement)
modified: cos/agent.py            post-response kill-switch gate, discard + request_stopped, timing
modified: cos/policy.py           check_model_call(phase) audited; subject on decisions
modified: cos/audit.py            initialization marker; VerifyResult ok/uninitialized/fail
modified: cos/cli.py              audit verify OK/EMPTY/FAIL; brief timing; DISABLED tools listed
modified: cos/brief.py            "Workstation status (legacy):" label; tool timing
modified: cos/egress.py           scope + subprocess boundary documented
modified: cos/executor.py, cos/model.py   tool_ms / model_ms field names
modified: cos/registry.py         registry.disabled
modified: cos/tools/__init__.py   eventkit_app; status tools registered via contract
modified: cos/tools/calendar.py   LaunchServices launch, --env no-prompt, output polling, wrong_launch
modified: cos/tools/status_scripts.py     contract gate at registration
modified: cos/helpers/eventkit-reader/Package.swift   no linker-embedded plist
modified: cos/helpers/eventkit-reader/Sources/eventkit-reader/main.swift  identity, attribution guard, lazy store
modified: tests/cos/support.py, test_agent.py, test_brief_and_cli.py, test_control.py, test_tools.py
modified: apps/raycast-chief-of-staff/package.json, README.md
modified: .gitignore, CHIEF-OF-STAFF.md, docs/cos-m1-live-checks.md, docs/cos-m1-review-bundle.md
```

## Test results

```text
$ python3.12 -m unittest discover -s tests/cos -p 'test_*.py'
Ran 114 tests in 1.955s
OK

per module: test_agent 17 · test_brief_and_cli 8 · test_control 23 · test_egress_and_model 13
            test_hardening 27 · test_tools 26          (original 83 + new 31 = 114)
egress/local-only alone: test_egress_and_model.py — Ran 13 tests, OK
git diff --check: clean
```

The new tests cover:
- **001:** a blocking fake model, released after `cos stop`, for plain-text and tool-call
  responses; a CLI-level test asserts no model text is printed and the exit code is 3.
- **005:** denied and allowed model-call decisions are audited, and a stopped `cos ask` writes
  the denial to the on-disk chain.
- **004:** never initialized, valid, tampered, initialized-then-deleted, and
  initialized-then-truncated logs.
- **003:**
  - the three real commands pass and the approval-queue script is caught;
  - 20 synthetic violation forms are detected;
  - a clean script with "curl" in comments, strings, and quoted heredocs passes;
  - nested and Python launches are followed;
  - called functions and the prelude are checked, while uncalled functions are not;
  - a missing dispatch block or unresolvable script fails closed;
  - a violating command is not registered.
- **D:** timing fields on all record types, including brief.
- **002:** launch argv uses `open` with `--env COS_EVENTKIT_NO_PROMPT=1`, never the bare
  binary; temp output is removed; `wrong_launch` and no-output are handled; the helper source
  is checked statically; the test suite is shown unable to reach the real helper.

CLI check with a scratch state dir:
- fresh → `EMPTY: no audit log yet (never initialized)`, exit 0;
- after `stop` and `ask` → `OK: chain intact (5 records)`, exit 0;
- log moved away → `FAIL: audit log is missing but was initialized`, exit 1.

`cos tools` lists 8 tools with none disabled.

## Raycast static validation

- `npm install` inside `apps/raycast-chief-of-staff/` only installed 87 packages, pinned in
  `package-lock.json`. npm 11 skipped esbuild's postinstall script; I left it unapproved, and the
  build works without it.
- The first `tsc --noEmit` **failed** (TS2786 on every JSX component): `@raycast/api@1.104.25`
  bundles `@types/react@19.0.10`, while the package declared `@types/react@^18`. I aligned the
  dev types with the API (`@types/react@^19.0.10`, `@types/node@^22.19.17`) and pinned
  `@raycast/api@^1.104.25`. **`npm run typecheck` (new script, `tsc --noEmit`) → exit 0.**
- **`npm run build` (`ray build -e dist`) → "built extension successfully"** (compiled both
  entry points, generated types, checked TypeScript). It writes its output into
  `~/.config/raycast/extensions/chief-of-staff/` rather than the repo. Because that folder is
  how Raycast imports extensions, I moved the folder my build created
  (`~/.config/raycast/extensions/`, timestamps 02:23) into my session scratchpad, leaving
  Owen's existing `~/.config/raycast/{ai,config.json}` untouched. The Raycast app was not
  opened or automated.
- **`npm run lint` (`ray lint`): not run.** The package declares no ESLint or Prettier
  configuration or dependencies, so lint has nothing to run against. Deferred (gap 27).

## Known gaps, classified

| # | Gap | Class | Reason |
|---|---|---|---|
| 1 | `--daily-status` prints the stale `Canvas LLM: frozen` line (repeated in the brief) | ACCEPTED-M1 | Output passes through unchanged by Owen's decision; it is now labeled "Workstation status (legacy)". |
| 2 | `--next-action` parse WARNs (`major program not found`, `(not parsed)`, gate/stop-marker wording) | ACCEPTED-M1 | Legacy script content, passed through unchanged; fixing it is outside M1. |
| 3 | `--approval-queue-status` crashes (TypeError), and its script deletes a file | DEFERRED-M2+ | Not wrapped; the contract check would refuse it anyway. Fix in the legacy track. |
| 4 | `--dashboard` takes about 101 s | DEFERRED-M2+ | Not wrapped; too slow for an interactive tool. |
| 5 | EventKit grant owned by Terminal or Raycast | ACCEPTED-M1 (residual) | Resolved by 002. Residual: the build stays ad-hoc until Owen signs with Apple Development (live checks 2.1), which is an owner step, not a code gap. |
| 6 | Raycast extension not type-checked or built | ACCEPTED-M1 (residual) | Resolved: typecheck and build pass. Residual: lint (gap 27). |
| 7 | Open-Meteo never called live | ACCEPTED-M1 | Fixture-tested; Owen's live check covers it once coordinates are set. |
| 8 | Audit log is tamper-evident, not tamper-proof; no rotation | ACCEPTED-M1 | Local, single-user threat model; anchoring and rotation fit with M3 memory work. |
| 9 | Kill switch during an in-flight model call | ACCEPTED-M1 (residual) | Resolved by 001 (response discarded). Residual: the Ollama request still runs to completion (up to 300 s) on the local GPU; cancellation was explicitly out of scope. |
| 10 | A timed-out tool thread cannot be killed | ACCEPTED-M1 | Subprocess and HTTP tools carry their own timeouts; nothing lingers in practice. |
| 11 | Keyword-only router | ACCEPTED-M1 | Router v1 is the M2 milestone. |
| 12 | School-day math ignores holidays | DEFERRED-M2+ | Needs the school calendar, which belongs to the Canvas/pacing track. |
| 13 | Chat history has no retention policy | DEFERRED-M2+ | It sits in the 0700 directory; retention belongs to M3 memory. |
| 14 | `active-priorities.md` "Now" section is stale (July) | ACCEPTED-M1 | Memory is read as-is by design; content cleanup is Owen's. |
| 15 | cos tests not wired into CI | DEFERRED-M2+ | Run locally; CI wiring belongs to the consolidation work. |
| 16 | `PROMPT-M1.md` referenced but not in the repo | ACCEPTED-M1 | Documentation pointer only; the spec was supplied in the session. |
| 17 | D1 source and CoS design docs only on `feature/cos-pacing-intelligence` | DEFERRED-M2+ | Option (a): consolidate in a separate Stage 0 PR. D1 is active locally. |
| 18 | **Ad-hoc helper currently holds full Calendar and Reminders access (development incident)** | **BLOCKER** | It must be reset (live checks 2.0) before the live checks, so the only grant is to Owen's signed build. Owen's action; I did not change TCC state. |
| 19 | `egress.py` is not an OS firewall; the subprocess contract is a denylist | ACCEPTED-M1 | The review asked for exactly this narrowing. Obfuscated or unknown network tools could evade a denylist; an OS sandbox is out of M1. |
| 20 | Contract check depends on `bin/chief-of-staff` layout (column-0 functions, the main `while` loop) | ACCEPTED-M1 | It fails closed: a layout change disables the tool rather than trusting it. |
| 21 | `open -W` can return before a fast helper finishes ("Unable to block on application") | ACCEPTED-M1 | Handled by polling for a complete JSON line until the timeout. |
| 22 | Attribution guard uses the private `responsibility_get_pid_responsible_for_pid` | ACCEPTED-M1 | Looked up with `dlsym`; if Apple removes it, the helper fails closed (`wrong_launch`). |
| 23 | First grant needs the explicit commands; cos reports `not_determined` until then | ACCEPTED-M1 | By design: cos never prompts. |
| 24 | `ray build` / `ray develop` write to `~/.config/raycast/extensions/` | ACCEPTED-M1 | That is how Raycast imports private extensions; it is documented in the README. |
| 25 | esbuild postinstall not approved under npm 11 | ACCEPTED-M1 | The build succeeds without it; approving install scripts is Owen's call. |
| 26 | Helper read-only checks are source-text tests, not a binary audit | ACCEPTED-M1 | Proportionate for an approximately 200-line helper; the reviewer can read the source. |
| 27 | No ESLint/Prettier configuration, so `ray lint` is not run | DEFERRED-M2+ | Adding lint dependencies and configuration is new tooling, not hardening. |
| 28 | Deleting both `audit.jsonl` and `audit.initialized` looks like never-initialized | ACCEPTED-M1 | It needs write access to the 0700 state directory (same limit as gap 8). |

## Architecture in one screen (after hardening)

```text
bin/cos (public entry point; python3.12 -s -E -P) → cos/cli.py
  ask/chat → agent.py: keyword router (≤6 tools)
               gate.check_model_call(before_request) → model.py (local Ollama only)
               gate.check_model_call(after_response)  → deny ⇒ discard response, Stopped
               tool call → gate.decide (kill switch → registered → side_effect none → args)
                         → executor.py (timeout, size cap) → tools/*
  brief    → brief.py: same gate + executor, no model, ≤15 lines, legacy lines labeled
  HTTP     → egress.py allowlist {http 127.0.0.1|localhost:11434, https api.open-meteo.com:443}
  subprocs → fixed argv (mac.status) · `open` LaunchServices → ChiefOfStaffEventKitReader.app
             · bin/chief-of-staff flags gated by script_contract.py at registration
  audit    → audit.py hash chain + audit.initialized marker; decisions for model and tool calls;
             model_ms / tool_ms / total_ms
State: ~/Library/Application Support/ChiefOfStaff/ (0700; files 0600; COS_STATE_DIR for tests)
```

## Instructions for the fresh reviewer

Review `4ce9521..<hardening commit>`. Check the hardening diff hash in the header first, and do
not modify files. Confirm each finding's disposition:

1. **001:** can any model output reach the CLI, or a tool call execute, after the switch is set
   mid-request?
2. **002:** can the helper touch EventKit when it is not its own responsible process? Can cos
   ever prompt? Does any helper command mutate?
3. **003:** can a wrapped command reach the network or write files without the contract
   flagging it? Are the false-negative paths acceptable for M1?
4. **004 / 005:** are all authority decisions in the chain, and does `verify` distinguish the
   three states?

Return findings as a JSON array (`[]` if none):

```json
[
  {
    "id": "M1-H-001",
    "severity": "blocking | major | minor | info",
    "category": "egress | authority | audit | privacy | injection | correctness | tests | docs",
    "path": "cos/agent.py:110",
    "evidence": "What you observed, quoting code or a concrete input → output.",
    "required_condition": "The specific, testable condition that resolves the finding."
  }
]
```
