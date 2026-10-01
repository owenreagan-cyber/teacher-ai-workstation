# cos M1 — Review bundle

```text
Milestone:        M1 — Simple Siri (fully local, read-only)
Branch:           feature/cos-m1 (worktree ~/Projects/taw-cos-m1), from main 31cb330
Reviewed range:   31cb330..d7bbbee (code); this bundle is committed on top
Diff SHA-256:     3c505e7fac121c5f3aa51d55b2168164989291c6a7343f7d6bc0922e1dffb36a
                  = shasum -a 256 of `git diff 31cb330..d7bbbee`
Tests:            83 passed, 0 failed (python3.12 -m unittest discover -s tests/cos -p 'test_*.py')
Builder:          Claude Code · Reviewer: one fresh cross-model reviewer (security / authority code)
Not done:         no push, no merge
```

## Commits

| SHA | Step | Summary |
|---|---|---|
| `70633f3` | 1 + 3 | cos core: CLI, local model loop, policy gate, kill switch, audit chain, egress allowlist, tools, tests; adds `CHIEF-OF-STAFF.md` |
| `e32639d` | 2 | Swift EventKit reader helper (read-only JSON) |
| `d7bbbee` | 4 | Raycast extension (Ask Chief, Daily Brief) |
| (this) | 5 | live-check instructions and this bundle |

Step 3 (the control foundation) landed in the Step 1 commit because the agent loop needs it.

## Diff stat (31cb330..d7bbbee)

```text
 .gitignore                                                     |   3 +
 CHIEF-OF-STAFF.md                                              | 364 +++++
 apps/raycast-chief-of-staff/README.md                          |  44 ++
 apps/raycast-chief-of-staff/assets/icon.png                    | Bin 0 -> 4064 bytes
 apps/raycast-chief-of-staff/package.json                       |  55 ++
 apps/raycast-chief-of-staff/src/ask-chief.tsx                  |  55 ++
 apps/raycast-chief-of-staff/src/cos.ts                         |  44 ++
 apps/raycast-chief-of-staff/src/daily-brief.tsx                |  30 ++
 apps/raycast-chief-of-staff/tsconfig.json                      |  16 +
 bin/cos                                                        |  16 +
 cos/__init__.py                                                |   3 +
 cos/__main__.py                                                |   5 +
 cos/agent.py                                                   | 191 +++
 cos/audit.py                                                   | 110 ++
 cos/brief.py                                                   | 109 ++
 cos/cli.py                                                     | 196 +++
 cos/config.py                                                  | 114 ++
 cos/egress.py                                                  |  96 ++
 cos/executor.py                                                |  48 +
 cos/helpers/eventkit-reader/Package.swift                      |  23 +
 cos/helpers/eventkit-reader/Sources/eventkit-reader/Info.plist |  20 +
 cos/helpers/eventkit-reader/Sources/eventkit-reader/main.swift | 137 ++
 cos/identity.md                                                |  32 +
 cos/memory.py                                                  |  70 +
 cos/model.py                                                   | 103 ++
 cos/policy.py                                                  | 105 ++
 cos/registry.py                                                | 128 ++
 cos/tools/__init__.py                                          |  56 +
 cos/tools/calendar.py                                          |  86 +
 cos/tools/mac_status.py                                        | 101 ++
 cos/tools/reminders.py                                         |  47 +
 cos/tools/status_scripts.py                                    |  46 +
 cos/tools/time_tool.py                                         |  59 +
 cos/tools/weather.py                                           |  93 ++
 tests/cos/fixtures/ (10 synthetic files)                       |  48 +
 tests/cos/support.py                                           | 119 ++
 tests/cos/test_agent.py                                        | 166 +++
 tests/cos/test_brief_and_cli.py                                | 133 ++
 tests/cos/test_control.py                                      | 249 +++
 tests/cos/test_egress_and_model.py                             | 192 +++
 tests/cos/test_tools.py                                        | 197 +++
 50 files changed, 3709 insertions(+)
```

## Architecture in one screen

```text
bin/cos (python3.12 -s -E -P) → cos/cli.py
  ask/chat → agent.py: keyword router (≤6 tools) → model.py (local Ollama only)
                │  tool call → policy.py gate (kill switch → registered → side_effect none → args)
                │            → executor.py (timeout, size cap) → tools/*
                └─ ≤6 rounds; malformed tool JSON retried once, then dropped and noted
  brief      → brief.py: same gate + executor, no model, ≤15 lines
  every HTTP → egress.py allowlist {http 127.0.0.1|localhost:11434, https api.open-meteo.com:443}
  every step → audit.py hash-chained JSONL (request, model_call, tool_call, decision, tool_result, answer)
State: ~/Library/Application Support/ChiefOfStaff/ (0700; files 0600; COS_STATE_DIR override for tests)
```

Trusted path (stdlib-only Python 3.12): `policy.py`, `registry.py`, `executor.py`,
`egress.py`, `audit.py`, `config.py`. The whole `cos/` package is stdlib-only.

## Tool list (`cos tools`)

| Tool | side_effect | data_class | timeout | Source |
|---|---|---|---|---|
| `time.now` | none | P2 | 2 s | clock; days and weekdays until a date |
| `weather.today` | none | P2 | 15 s | Open-Meteo, coordinates rounded to 2 dp, 30-min cache |
| `mac.status` | none | P1 | 15 s | `pmset -g batt`, `memory_pressure`, `df -k /`, `sysctl kern.boottime`, Ollama `/api/ps` |
| `calendar.today` | none | P1 | 20 s | `eventkit-reader events --days 1` |
| `reminders.due` | none | P1 | 20 s | `eventkit-reader reminders --due-within-days 1` |
| `status.daily` | none | P1 | 25 s | `bin/chief-of-staff --daily-status` (output unchanged, capped at 4000 chars) |
| `status.next_action` | none | P1 | 25 s | `bin/chief-of-staff --next-action` |
| `status.local_llm` | none | P1 | 25 s | `bin/chief-of-staff --local-llm-workstation-status` |

## Test output

```text
$ python3.12 -m unittest discover -s tests/cos -p 'test_*.py'
Ran 83 tests in 0.180s
OK

per module:  test_agent 17 · test_brief_and_cli 8 · test_control 23 · test_egress_and_model 13 · test_tools 22
```

Coverage against the prompt's required tests:

| Required | Where |
|---|---|
| Every tool against mocked command/API output | `test_tools.py` (all 8 tools + registry contents) |
| A policy-gate deny case for each rule | `test_control.PolicyGateTests`: unregistered, side_effect, bad_arguments, kill_switch, gate_error, gate_timeout |
| Audit chain integrity and tamper | `AuditChainTests`: edit, rehashed edit, delete, reorder, 4-thread concurrent append |
| Kill switch blocks everything | gate (tools + model), agent before the model and mid-turn, brief gather, CLI ask/brief |
| Egress refuses cloud model hosts and any non-allowlisted host | `test_egress_and_model.py`: Anthropic, OpenAI, Gemini, OpenRouter, Mistral plus 14 other forms; asserts no socket is opened; structural test that only `egress.py` imports networking modules |
| Model client refuses a non-local base URL | `ModelClientLocalOnlyTests` (9 URLs) plus egress refusal if `base_url` is mutated later |
| Agent loop malformed-JSON retry | retry-then-succeed, twice-then-drop-with-note, Ollama parse-error path |
| Brief formatting deterministic | exact 14-line expected output; ≤15 lines with 12 events and 9 reminders |
| State directory created 0700 | under umask 022, tightening of a 0755 dir, files 0600 |

### Dev smoke checks (run by Claude Code with a scratch `COS_STATE_DIR`)

- Real `mac.status`, `time.now`, and the 3 status tools ran against this Mac. All exited 0 and
  none were truncated. EventKit was **not** run (no permission prompts were triggered).
- One live `cos ask "what time is it"` against local `qwen3.6:35b`: correct answer,
  `Tools used: time.now`, 19 s cold. The audit chain for that request has 7 records and verifies
  (request → model_call → tool_call → decision → tool_result → model_call → answer, all on host
  `127.0.0.1:11434`).
- Open-Meteo was never called (no coordinates are configured yet).

## D1 change for the state directory (applied by Owen, 2026-10-01)

Owen applied and verified this change, reporting: integrity PASS, hook 371/371, boundary 33/33.

1. `tools/dev_safety/dev_guard.py` (recovery branch `feature/cos-pacing-intelligence`):
   `DENIED_ROOT_RELS` gains `"Library/Application Support/ChiefOfStaff"`, and the hook is
   reinstalled to `~/.claude/hooks/cos/dev_guard.py` with a matching SHA.
2. `.claude/settings.json` `permissions.deny` (Read+Edit form; Write rules removed):
   ```json
   "Read(~/Library/Application Support/ChiefOfStaff/**)",
   "Edit(~/Library/Application Support/ChiefOfStaff/**)"
   ```

Tests never touch the real directory. `support.StateDirTest` sets `COS_STATE_DIR` to a fresh
temporary directory for every test.

## Known gaps

**Wrapped status scripts (output passed through unchanged, per Owen):**
1. **Stale lines.** `--daily-status` prints `Canvas LLM: frozen (stop marker active)`, but recent
   `main` commits (#358–#360) show active Canvas work. The brief repeats this line as a status
   highlight.
2. **Parse warnings.** `--next-action` prints `WARN: major program not found in build queue`,
   `Recommended major program: (not parsed)`,
   `WARN: implementation gate missing not approved by default wording`, and
   `WARN: canvas llm stop marker wording incomplete`.
3. **`--approval-queue-status` crashes.** It fails with
   `TypeError: '>' not supported between instances of 'NoneType' and 'str'`, so it is not wrapped.
4. **`--dashboard` is too slow.** It takes about 101 s, so it is not wrapped.

**Platform and surfaces:**

5. **EventKit permission goes to the launching app.** macOS attributes the grant to the app that
   launches the helper (Terminal or Raycast), not the helper itself. Giving the helper its own
   identity would need an `.app` bundle launched with `open --stdout`. Deferred.
6. **Raycast extension not type-checked or built.** npm dependencies were not installed during
   development (new network download, so Owen does it in the live checks).
7. **Weather never called live.** Open-Meteo is covered only by the fixture until Owen sets
   coordinates.

**Control layer:**

8. **The audit log is tamper-evident, not tamper-proof.** Someone with write access to the state
   directory could rewrite the whole chain. There is no external anchor and no rotation.
9. **The kill switch doesn't interrupt work already running.** It is checked before every model
   call and every tool call. An in-flight Ollama request (up to `model_timeout_s`, 300 s) runs to
   completion. Any tool call it proposes is then denied, but a plain-text final answer from that
   request is still printed.
10. **Timed-out tool threads can't be killed.** The executor's timeout returns an error, but a
    Python thread cannot be killed. Subprocess-backed tools pass their own `timeout` to
    `subprocess.run`, and HTTP has its own timeout, so nothing lingers in practice.

**Behaviour limits:**

11. **The router is keyword-only.** Questions with no matching keyword are offered no tools.
12. **School-day math ignores holidays.** `time.now` counts Mon–Fri only.
13. **Chat history has no retention policy.** It sits in `history/` (0700 directory, 0600 files)
    and grows without limit.
14. **Memory loads a stale "Now" section.** The `active-priorities.md` "Now" section contains
    July 2026 entries; it is loaded condensed and as-is.

**Repo and process:**

15. **Not in CI.** The `cos` tests are not wired into `.github/workflows`; run them locally with
    the command above.
16. **Missing reference.** `CHIEF-OF-STAFF.md` says the M1 spec lives in `PROMPT-M1.md`, but that
    file is not in the repo; the spec was pasted into the session.
17. **D1 isn't committed on `main`.** The D1 source (`tools/dev_safety/`) and the CoS design docs
    live only on `feature/cos-pacing-intelligence`. Owen chose option (a): build M1 on `main` and
    consolidate in a separate PR.

## Instructions for the fresh reviewer

You are reviewing `feature/cos-m1`, range `31cb330..d7bbbee`. Check the diff hash in the header
first. Do not modify files. Focus areas, in priority order:

1. **Egress and local-only:** can any path in `cos/` make a network request that does not go
   through `egress.request`, or reach a host outside the allowlist (redirects, proxies,
   userinfo, IPv6, DNS tricks, `base_url` mutation)?
2. **Authority:** can a model-proposed tool call execute without an allow decision? Does every
   gate failure deny? Can a non-`none` side effect run?
3. **Audit:** are records written for every request, model call, tool call, and decision? Is
   `verify` sound?
4. **Prompt injection:** is tool output (calendar titles, status text) ever treated as
   instructions or used to choose tools beyond what the model proposes?
5. **Privacy:** what student-adjacent data could reach disk outside the 0700 state directory,
   or leave the Mac?
6. **Tests:** do they prove what they claim? Any non-determinism?

Return findings as a JSON array, one object per finding:

```json
[
  {
    "id": "M1-001",
    "severity": "blocking | major | minor | info",
    "category": "egress | authority | audit | privacy | injection | correctness | tests | docs",
    "path": "cos/egress.py:61",
    "evidence": "What you observed, quoting code or a concrete input → output.",
    "required_condition": "The specific, testable condition that resolves the finding."
  }
]
```

Return `[]` if you find nothing. Blocking findings are fixed once and then reconfirmed.
