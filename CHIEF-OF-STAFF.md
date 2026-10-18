# Chief of Staff — Developer README

Status: A+ PLAN (post-audit) · 2026-10-01
Owner: Owen · Builder: Claude Code · Reviewer: one fresh reviewer per phase (cross-model for
security, privacy, and authority work)

Supersedes the scattered plans in ROADMAP Revisions 2–4, the feature catalog, and the agent
research report. Those remain as history; this file is the entry point.

**Audit outcome (2026-09-30).** Three plans were audited blind (Claude Code, with a Cursor audit
as confirmation). This plan ("A") ranked first in both; the competing GPT and early Gemini drafts
were rejected as written. This revision ("A+") applies the audit's fixes:
Gmail starts read-only; a hard monthly cloud budget; a smaller, fully local Milestone 1; plus the
sealed Canvas approval packet with post-write readback, local Mail/Calendar triage, and a decision
log where new decisions supersede old ones. Caveat: author and both auditors may share a model
family.

---

## What lives where

Since MERGE-1 (2026-10-18), the Chief stack and the Teacher Workstation share one repo history.

| Area | Path |
|---|---|
| Teacher Workstation, Canvas, and dashboard | Existing `main` paths: `bin/chief-of-staff`, `scripts/`, `apps/teacher-workstation/` and the other workstation apps, `config/`, `docs/programs/`, `tests/` |
| Chief core | `cos/`, `bin/cos` |
| Chief desktop | `apps/chief-desktop/` |
| Evals | `evals/` |
| Developer safety | `tools/dev_safety/` |
| Decisions | `docs/DECISIONS.md` |
| Plan | `docs/NEXT-PHASES.md` |
| Earlier workspace architecture (`assistant/chief-of-staff/workspace/`) | On branch `wip/canvas-live-q1w9`; reference only, not yet merged |

---

## 1. What the Chief of Staff is

A local, Mac-resident assistant that Owen calls with a hotkey, talks to in plain language, and
that coordinates all of his AI workers: local Qwen models and cloud services (Claude, Claude Code,
Cursor, Codex, Gemini, Lovable, and others). It decides which worker handles each task, keeps
student data on the Mac, and asks before anything consequential happens.

- **"Simple Siri" first:** call it up, chat, time, weather, Mac status, calendar, reminders,
  email triage, daily brief, project awareness.
- **"Advanced Siri" next:** knowledge search across approved sources, specialist agents
  (Canvas, Lessons), proactive notices, impact analysis.
- **Autonomy last:** acting without per-action approval comes only after the control layer is
  proven.

The Chief of Staff is the **brain and dispatcher**. Specialists and cloud agents are **hands**.
Outside products were studied for logic and features to rebuild, not to adopt.

---

## 2. Non-negotiables

1. **Student data is processed by AI only on local models.** Rosters, grades, behavior records,
   parent email, anything linkable to a student. It may stay in the school systems where it already
   lives (school Gmail, Canvas). It never goes to a cloud AI service, cloud sync, or any new
   third-party system. Enforced in code. *(Wording pending Owen's confirmation.)*
2. **External content is data, never instructions.** Email, web pages, documents, and cloud-agent
   output can inform, never command.
3. **Deterministic code owns authority.** Models propose; the policy gate decides; the executor
   acts. Unknown, failed, or timed-out checks resolve to *deny*.
4. **Nothing consequential without approval.** Anything that affects other people (Canvas
   posts, parent email) or changes files and repos is approved by Owen until a later stage
   explicitly relaxes it.
5. **Owen owns his data.** Memory, skills, logs, and settings live in plain files and SQLite on
   his machine.

---

## 3. What exists today

| Location | Contents | Role |
|---|---|---|
| `~/Projects/teacher-ai-workstation` (GitHub `owenreagan-cyber/teacher-ai-workstation`) | `bin/chief-of-staff` CLI (~4,250-line bash dispatcher), `assistant/memory/` (projects, preferences, decisions, priorities, teaching context, writing style), intake review queue, status/dashboard/approval/blocker scripts, `assistant/` policies (permissions, sensitivity, memory, model routing), Canvas LLM program phases 15–27 (weekly planning, rule engine, curriculum source intelligence, renderer, deployment planner, write gate, connector, readiness diff) plus the approved live weekly Canvas deployment and refresh tooling (PRs #374–#384), `config/curriculum/` (week scaffold, SM5 maps), canonical context pack and 2026–27 operating contract; since MERGE-1 also the Chief stack (see "What lives where") | **Product home.** The Canvas builder and the `cos` core live here. |
| `~/Projects/teacher-ai-workstation-chief-of-staff-recovery` | Design docs at `assistant/chief-of-staff/workspace/` (ARCHITECTURE, ROADMAP, STATUS, HISTORY), parked M-track controlled-execution code, D1 developer safety profile (`.claude/settings.json`, `tools/dev_safety/`) at commit `4a2679f`; branch `feature/cos-pacing-intelligence` | Design, safety, parked autonomy work. |
| `~/Projects/teacher-ai-workstation-chief-of-staff-v1-phase1` (`fecd0ab`) | Phase 1 snapshot | Read-only reference. |
| `~/Projects/math-presenter-studio` | Lesson build, staging, certification pipeline | Future Lesson specialist. |
| `~/.teacher-ai-workstation/` | Local runtime state | Non-sensitive under D-022. The installed D1 profile still denies it until the light profile is installed. |

### Entry points
- **`bin/cos` is the public entry point** for the Chief of Staff (`cos ask`, `chat`, `brief`,
  `stop`/`resume`, `tools`, `audit verify`), and the Raycast extension calls it.
- **`bin/chief-of-staff` is legacy.** `cos` may wrap its read-only status commands as tools
  (M1 wraps `--daily-status`, `--next-action`, and `--local-llm-workstation-status`, each gated by
  a static network-free/read-only check), but new features are not added to it.

### Works today
- **Chat:** one-shot `cos ask` and multi-turn `cos chat`, on the local model, with tool calling
  (`cos tools` lists them).
- **Sessions:** conversations are saved and can be resumed (`cos history`).
- **Daily brief** (`cos brief`) and the **home card** in the desktop window (see "Home card").
- **Desktop window:** Chief.app (Electron + React) with a menu bar icon and the
  Control+Option+C hotkey, plus the Raycast launcher. Both call the same `cos` core.
- **Tools:** time and date, weather, today's calendar (EventKit), reminders due, Mac status,
  and **web search** (Brave; typed "search …" command, daily and monthly caps; see
  "Web search").
- **Start at login** for the packaged app, with the model warmed in the background.
- **Safety plumbing:** kill switch (`cos stop` / `cos resume`), hash-chained audit log
  (`cos audit verify`), and the eval harness (`evals/harness/run.py`).
- Legacy read-only status: daily status, dashboard, approval and blocker queues, next action
  (`bin/chief-of-staff`).
- Canvas weekly-production, readiness, and approved live-deployment tooling on `main` (per its
  own phase status; this includes real Canvas writes behind the approval and write gate, and,
  since REL-1, the local server's route protection).
- D1.1 safety for Claude Code, versioned in `tools/dev_safety/`: the Claude Code Bash
  sandbox (macOS Seatbelt) as the boundary, plus the `dev_guard` hook as a second layer
  (credentials, Claude Code state, the ChiefOfStaff state folder; git, inline-code,
  destructive-command, and process-listing denials; it also still denies
  `~/.teacher-ai-workstation` and `~/Downloads`). The D-022 light profile (localhost, GitHub
  fetch, and general web allowed; those two folders no longer denied) is not live yet: it
  needs Owen's go-ahead and install. Limits: `tools/dev_safety/README.md`.

### Missing
Automatic web search by intent (D-011 as revised; today only the typed command searches),
local file search (D-021), email (D-013), notifications, voice, conversational memory writing,
project awareness from real repos, proactive monitoring, routing between local and cloud
workers (M2 router, D-020, D-026), delegation to cloud agents, the multi-agent orchestrator and
MCP adapters (D-023, D-024, D-025), and the iPhone app (D-007).

### Recent history (short)
- Roadmap Revision 3 committed at `4a2679f` with D1.
- M5E controlled-execution pilot BLOCKED by independent review of its one-off driver; run
  closed cleanly, evidence preserved. M-track parked until L2 autonomy is needed.
- SM5 curriculum-identity draft and Canvas pacing mission drafted; open owner decisions remain
  (see §13).

## Daily use (P1a messenger)

The compact window (Chief.app), Raycast, and `bin/cos ask` all reach the same `cos` core.

### Web search

Type a message that starts with **`search`**, **`look up`**, **`google`**, or **`web search`**:

```sh
bin/cos ask "search weather radar wilson nc"
bin/cos ask "look up photosynthesis for kids"
```

- Only the whole message counts: "search my calendar" is a web search for "my calendar";
  "what's the search engine" and "can you search for …" are ordinary questions, and the model
  cannot search on its own (D-011, CERT-009).
- The words after the command go to Brave Search exactly as typed (trimmed, at most 200
  characters). **They leave the Mac: never type student names or other student details**
  (D-001).
- The answer is 2–4 sentences from the local model, followed by numbered sources. If the local
  model is unavailable, you get the raw results list instead. Results are untrusted data (D-002).
- The kill switch (`cos stop`) blocks search like every other tool.
- The query text and its source (`typed`) are recorded in the audit log; the API key never is.
- **Budget:** at most 30 searches a day and 600 a month by default (local time). Every real call
  to Brave counts, even one that fails. At either limit Chief answers, for example, "Search limit
  reached for today: 30/30. Resets tomorrow." and makes no call. Change the limits in
  `config.json` in the state directory (`"search_daily_limit": 30, "search_monthly_limit": 600`;
  0 turns search off). Counts live in `search_usage.json` there; if that file is damaged, search
  pauses until you delete it.
- In the desktop app, answers built from results show "Search by Brave".

#### Web search setup (once)

1. Get a Brave Search API key: sign in at <https://api-dashboard.search.brave.com>, subscribe to
   a Search plan (a free tier is enough if one is offered), then **API Keys → Add API key** and
   copy the key.
2. Store it in the macOS Keychain. The command prompts for the key twice and does not echo it,
   so it never lands in your shell history:

   ```sh
   security add-generic-password -a "$USER" -s chief-search-brave -w
   ```

3. Check that it is stored (prints nothing secret), then test:

   ```sh
   security find-generic-password -s chief-search-brave >/dev/null && echo "key stored"
   bin/cos ask "search weather radar wilson nc"
   ```

To replace the key, run `security delete-generic-password -s chief-search-brave` and repeat
step 2. Until a key is stored, a search answers "web search not set up" and points here.

### Home card

The compact window opens with a card instead of an empty chat: a greeting, the date, the next
event and today's event count, reminders due (and how many are overdue), and a one-line weather
summary.

- It is built by `cos brief --json` (the `card` field), deterministically, with no model.
- Tap it to see the full brief. After your first question it shrinks to a one-line header; tap
  that to open it again. It rebuilds itself when a new day starts.
- Missing data shows plainly: "Nothing scheduled", "Calendar unavailable" (EventKit not
  granted), "Weather unavailable". It never shows an error trace.
- It appears only inside the window, which is hidden from screenshots and screen sharing by
  default. The menu bar icon, window title, and notifications never show card content.

### Personality

`cos/personality.md` is Chief's voice: tone, length, when to use your name, and honesty rules.
**Edit it freely**; the next question uses the new text (no restart).

- It is loaded into the system prompt after `cos/identity.md` and before the tool rules and a
  fixed block of safety rules. Those rules always come after it and say they win, so the
  personality can change how Chief sounds but not what Chief is allowed to do or claim.
- Keep it under about 3,000 characters; longer text is cut off.
- If the file is missing, Chief runs without it.
- The harness `personality` suite checks the voice against the local model
  (`python3.12 evals/harness/run.py --suite personality --model real`), including a check that
  Chief never offers an action it can't do ("Let me know if you'd like me to send …").

### Start at login

The installed Chief.app adds itself as a login item on its first run. At login it starts hidden
in the menu bar and loads the local model in the background (`cos warm`), so the first question
after the hotkey (Control+Option+C) does not wait for a cold model.

- Turn it off or on from the menu bar icon: **Start at login**. The choice is remembered, and the
  checkbox follows macOS (System Settings → General → Login Items) if you change it there.
- Only the packaged app registers itself; `npm run dev` never does.

---

## 4. Architecture

```text
 SURFACES   Raycast hotkey chat · menu bar icon · notifications · Finder "Send to Chief of Staff"
            · voice (later) · Siri/Shortcuts App Intents (later) · iPad read-only brief (later)
               │  local socket / 127.0.0.1, token-authenticated
 ┌─────────────▼──────────────────── cosd (Chief of Staff daemon) ─────────────────────────┐
 │ Session manager ─ Context builder (identity + core profile + relevant memory/skills)    │
 │ Planner loop (model proposes)                                                            │
 │ ROUTER ─ data-class gate → task type → eligible workers → local-first escalation         │
 │ POLICY GATE (deterministic, fail-closed) → APPROVAL QUEUE → EXECUTOR (hash-checked)       │
 │ Quarantine reader (tool-less; untrusted content → structured data)                        │
 │ Memory: core profile (git) · typed memory items · session history (FTS5) · skills         │
 │ Scheduler (launchd + change detection) · Audit log (append-only, hash-chained)            │
 │ Credential broker (Keychain; models never see tokens)                                     │
 └─────────────┬───────────────────────────────┬────────────────────────────┬──────────────┘
          LOCAL WORKERS                   CLOUD MODELS                  CLOUD AGENTS
          Ollama via LiteLLM:             via LiteLLM:                  via CLI adapters:
          qwen3.6:35b (general)           Claude · Gemini · GPT         Claude Code · Codex
          qwen3.6:27b-coding              (P1/P2 only)                  Cursor CLI · Gemini CLI
          gpt-oss:20b (fast/fallback)                                   Lovable (handoff + GitHub)
                                                                         (P2 only; return diffs)
          TOOLS: time · weather · Mac status · Calendar/Reminders (EventKit) · Mail (read-only first)
                 · approved files · existing bin/chief-of-staff scripts · Canvas toolchain
          SPECIALISTS: Canvas (pacing, build/render, deploy via write gate) · Lessons (Math Presenter)
```

---

## 5. Code stack

| Layer | Choice | Notes |
|---|---|---|
| Daemon | Python 3.12, `uv`, asyncio server on a Unix socket (or FastAPI on 127.0.0.1), launchd agent | Python matches existing tooling, LiteLLM, and FastMCP. |
| Trusted path (policy gate, router class gate, executor, audit) | stdlib-only Python | Same rule as D1: the safety boundary must not depend on third-party packages. |
| Schemas | Pydantic v2 outside the trusted path; stdlib validation inside it | |
| Storage | SQLite (WAL) + FTS5; `sqlite-vec` for embeddings (Stage 3); plain Markdown for core profile and skills | Owen-owned files. |
| Model routing | LiteLLM proxy (existing) → Ollama (local) and cloud APIs | Separate virtual keys: `local-only` key for any session carrying student data; cloud keys carry a model allowlist and a hard monthly `max_budget`. |
| Local models | `qwen3.6:35b`, `qwen3.6:27b-coding`, `gpt-oss:20b` on Ollama.app | Roster changes go in the model registry, not code. |
| Cloud models | Claude, Gemini, GPT through LiteLLM | P1 needs a standing grant; P0 never. |
| Cloud agents | Headless CLIs: `claude -p`, `codex exec`, Cursor CLI, Gemini CLI; Lovable via prompt handoff + GitHub sync | Verify each CLI's flags at adapter time. |
| Tools export | Internal registry; optional MCP server (FastMCP) exposing a P2-only tool profile | Lets Claude Desktop/Cursor reuse safe tools. |
| Calendar / Reminders | Small Swift CLI using EventKit | Local; no OAuth app approval needed. |
| Email | Stage 2: local Apple Mail read-only (or Gmail `gmail.readonly`). Drafts come later and are enforced in code: Google's `gmail.compose` scope also permits sending, so no OAuth scope guarantees drafts-only. | School mail may need IT approval. |
| Weather | National Weather Service or Open-Meteo (no key) | |
| Surfaces | Raycast extension (TypeScript), SwiftBar plugin (menu bar) then optional SwiftUI `MenuBarExtra`, `terminal-notifier`, `mlx-whisper` + `say` for voice | Raycast is already installed. |
| Tests | `pytest`; adversarial suites for privacy egress and prompt injection | |
| Dev safety | D1 profile + probes (existing) | Extend denials to any new student-data paths. |

---

## 6. Logic plan — router, data classes, escalation

### Data classes (assigned by source, in code)
| Class | Examples | Allowed workers |
|---|---|---|
| **P0** student-identifiable | rosters, grades, behavior, parent email, student work | local models only |
| **P1** personal | personal email, calendar, finances | local; cloud models only with a standing grant |
| **P2** general work | code, curriculum sources, published materials, web research | any worker |

A session's class is the most restrictive class of anything it has touched.

### Router decision steps
1. **Data class gate** (code): P0 → local only, no delegation.
2. **Task type**: quick question · summarize · write · code change · app/UI build · web research ·
   long-document reasoning · schedule/admin.
3. **Eligible workers** from the worker registry (location, allowed classes, strengths, cost,
   speed, interface, writes or not).
4. **Local first, escalate on rules**: context too long for local, needs the web, frontier-level
   coding, or the local self-check fails. Every escalation records its reason.
5. **Approval** for any delegation that writes. P2 model calls need none.
6. **Log** worker, reason, cost, latency, outcome; repeated outcomes produce *proposed* routing
   rules Owen can publish.

### Worker registry (shape)
```yaml
- id: qwen-35b     kind: model  location: local  classes: [P0,P1,P2]  writes: false
- id: claude-api   kind: model  location: cloud  classes: [P1,P2]     writes: false
- id: claude-code  kind: agent  location: cloud  classes: [P2]        writes: true  interface: cli
- id: lovable      kind: agent  location: cloud  classes: [P2]        writes: true  interface: handoff+github
```

---

## 7. Control plan — policy, approvals, audit

- **Every tool declares** its side effect (none / local write / external effect), data classes,
  and default mode (auto / ask / deny).
- **Policy gate**: plain rules file, unit-tested, evaluated before every action. Fail closed.
- **Approval records** (request → decision) answerable from any surface: Raycast, menu bar,
  notification, later iPad. Typed responses: *approve*, *edit then approve*, *answer a question*,
  *deny*. Batched to avoid approval fatigue.
- **Who-is-affected rule**: anything other people will see (Canvas posts, email to parents)
  always asks; actions affecting only Owen can be lighter.
- **Graduated autonomy** (Stage 6): an action moves from *ask* to *auto* only after a track record
  of approved runs and Owen's sign-off; auto-runs are capped.
- **Executor** runs only the exact approved action (hash match), takes a checkpoint before file
  writes, and records the result.
- **Audit log**: append-only, hash-chained; who asked, which worker, what was approved, what ran.
- **Kill switch**: one command revokes all grants and stops all Chief of Staff jobs.
- **Cost cap**: cloud spend is capped per month on the LiteLLM keys (hard stop), not only logged.
- **Canvas writes**: a sealed approval packet (SHA-256 of the exact change set) is approved by
  Owen; the deployer applies only a matching packet, then reads back from Canvas and verifies
  byte-for-byte; any mismatch fails closed and is reported.

---

## 8. Delegation plan — cloud agents

- **Missions, not chats.** A delegation carries objective, repo, allowed paths, project rules,
  and tests to run.
- **Artifacts back, never direct changes.** Coding agents work on a branch or worktree; the Chief
  of Staff runs tests and shows the diff; Owen merges. Lovable output arrives through GitHub sync.
- **Adapters are thin CLI wrappers** with JSON results, timeouts, and cost tracking.
- **Credentials** come from the broker at call time; models never see them.
- **Results are untrusted** until verified (tests, review).
- **Never P0** to any cloud agent.

Adapter order: Claude Code → Codex → Cursor CLI → Gemini CLI → Lovable.

---

## 9. Memory plan

| Layer | Storage | Rules |
|---|---|---|
| Identity / persona | `identity.md` | Name, owner, role, capabilities, never-do list. Protected. |
| Core profile | existing `assistant/memory/*.md`, git-tracked | Always loaded (small). Changes need approval and are committed. |
| Memory items | SQLite: kind, text, status, due, source, class, confidence, confirmed_by | "Remember that…" creates a *pending* item Owen confirms. Scoped paths (`/school/math`, `/dev/cos`). |
| Session history | SQLite FTS5 + nightly local summaries | "What did we decide last week?" |
| Skills | `skills/*/SKILL.md` | Drafted after successful multi-step tasks; approved before use; loaded only when relevant. |
| Knowledge | trigger-described items, approved-folder index (Stage 3) | Loads only when its trigger matches. |
| Owner decisions log | dated, Owen-authored entries with effective periods; a new entry explicitly supersedes the old one | Source of truth for teaching rules (homework, agenda posting, titles). |

---

## 10. UI plan

### Surface rules (apply to every surface)
- **Surfaces display and request; the core decides.** Routing, policy, approvals, data
  classification, execution, audit, and memory authority live in the core. No surface can change
  them.
- **Runtime and privacy badges are read-only telemetry** from the router's execution records. A
  badge can never select a model. Overrides are a separate request that goes back through the
  router and policy gate.
- **Approval buttons send an approval ID only.** The core retrieves the sealed packet, verifies
  its hash, and runs the policy gate. A surface never builds or edits the authoritative packet.
- **Data-class-aware rendering.** Notifications, window titles, previews, clipboard, and anything
  screenshot-visible never show student-identifiable content outside the Workbench's own panes.
  A notification says "student-related update," not the student's name or grade. Raycast Cloud
  Sync stays off.
- **The model never resizes or opens windows on its own.** The Workbench opens on Owen's action,
  or when an artifact or approval needs detailed review.

### Surfaces by phase

| Phase | Surface | What Owen gets |
|---|---|---|
| U1 | Raycast "Ask Chief" with global hotkey | Chat from anywhere; shows which worker answered and why; one-click "use a different worker". |
| U1 | Ask / Do toggle | Plan-only vs act. |
| U2 | Raycast "Approvals" | Approval cards with exact preview; approve / edit / answer / deny; batch. |
| U2 | Menu bar icon (SwiftBar) | Idle / working / N approvals / error; latest brief. |
| U2 | Notifications | Deep-link to the pending decision; rate-limited. |
| U2 | Raycast "Remember" | Propose a memory; confirm. |
| U3 | Named routines | "Morning", "end of day", "prep next week". |
| U3 | Daily brief with feedback | "You missed X" / "this was useless" updates its rules. |
| U3 | Tools & workers settings | Every tool and worker with auto / ask / deny and on/off. |
| U4 | **Workbench** (with Stage 4: first real artifacts — Canvas packages, delegated diffs) | Expanded window (~1080×720): conversation, execution plan, approval packet, artifact Preview / Source / Diff, task context, worker provenance. Launched on demand, not always running. Requires the core daemon. |
| U4 | Provenance inspector | Click the runtime badge: worker, location, data class, cloud eligibility, tools used, external writes, session ID — read from the audit record. |
| U4 | Finder Quick Action | "Send to Chief of Staff" on a file or selected text. |
| U5 | Voice | Push-to-talk (`mlx-whisper`), spoken replies (`say`). |
| U5 | App Intents | Siri/Shortcuts can call "Ask Chief of Staff" and "Today's brief" (P1/P2 results only). |
| U6 | iPad brief | Read-only P1/P2 view over the local network. |

Workbench framework is an open decision (see §13). A compact "Messenger" window is optional:
keep one compact chat surface (Raycast first) rather than maintaining two.

---

## 11. Phase plan

| Stage | Milestone | Exit criterion |
|---|---|---|
| **0 One home** | 0.1 Verify repo relationships (remotes, shared history, local vs GitHub HEAD) | Written answer on how the repos relate. |
| | 0.2 Consolidate into `teacher-ai-workstation`; bring design docs + D1 across; archive recovery repo | One repo; README section "What the Chief of Staff is and how to run it". |
| **1 Simple Siri** | **M1 (≤2 weeks, fully local, read-only):** `cos` CLI (`cos ask`, `cos chat`, `cos brief`, `cos stop`); identity + existing memory files loaded read-only; local Qwen via Ollama only; tool registry with time/date, weather, Mac status, read-only Calendar and Reminders (EventKit helper), existing status scripts; stdlib policy gate (deny unregistered tools), hash-chained audit log, kill switch; network egress allowlist; Raycast "Ask Chief" hotkey; daily brief | Automated tests pass, including one proving no request can reach a cloud model host; Owen uses the hotkey and brief daily for a week. |
| | **M2:** Router v1 (worker registry, data-class gate, local-first escalation) with one cloud model behind a capped LiteLLM key; approval queue for the first write tools; menu bar icon and notifications; Ask/Do toggle | Every answer shows its worker and reason; P0 egress test proves cloud refused; budget cap enforced. |
| | **M3:** Memory v2 (pending "remember", typed items, scoped recall); project awareness | A preference taught in chat is used next session; "What am I working on?" is accurate. |
| **2 Personal assistant** | Local Mail triage (Apple Mail read-only) with quarantine reader; Reminders writes with approval; named routines; correctable daily brief; drafts later, enforced in code | Brief read every school day for two weeks; zero unapproved writes. |
| **3 Knowledge** | Approved-folder index (content-hash cache, incremental), selected Drive folders, session search, owner decisions log | "Find the decision about X" returns the source passage. |
| **4 Specialists + delegation** | Cloud agent adapters (Claude Code → Codex → Cursor CLI → Gemini CLI → Lovable); Canvas specialist C0–C3; Lesson specialist | One delegated coding mission returns a tested diff; one Canvas week built and deployed through the write gate with approval. |
| **5 Advanced Siri** | Monitors that skip the model when nothing changed; impact analysis; learned routing rules (approved); voice; App Intents; Finder action | Proactive notices are useful and ≤3/day. |
| **6 Autonomy** | Resume parked M-track (driver hardening, controlled execution, permission conformance, repair loop); graduated autonomy; isolated session for any computer-use agent | Each auto-promoted action has a clean approved track record. |

### Canvas specialist track (Stage 4, may start early on its own branch)
| # | Milestone | Exit criterion |
|---|---|---|
| C0 | Inventory existing Canvas LLM phases 15–27, Math Presenter schedule logic, legacy Pacing Pilot: extend / wrap / retire | One map of what the specialist is made of; no duplicate rule engines. |
| C1 | Pacing readiness: "Is SM5 ready for next week?" from the pacing guide, owner rules, read-only Canvas snapshot (Owen runs the fetcher; token in Keychain; GET-only) | Correct report for a real week. |
| C2 | Build/render agenda pages, announcements, assignments from pacing + rules using the existing renderer | Weekly package generated locally for review. |
| C3 | Deploy through the existing write gate using a sealed approval packet; post-write readback must match | One real week deployed with no manual Canvas fixes and every readback matching. |

**First milestone to build:** M1 — fully local, read-only Simple Siri (see `PROMPT-M1.md`).

---

## 12. Development workflow

- **Roles:** Claude Code builds; one fresh reviewer per phase (cross-model for security, privacy,
  authority, delegation, and control code); Owen decides and merges.
- **Unit of work:** one feature branch per feature; subphases as commits; each phase ends with
  tests passing and a review bundle (diff, test output, known gaps).
- **Review format:** JSON findings (id, severity, category, path, evidence, required condition);
  blocking findings fixed once, then reconfirmed.
- **Owner stops:** architecture changes, new dependencies, privacy questions, destructive
  actions, teacher-rule ambiguity, merge/push.
- **Safety:** D1 hook profile (see `tools/dev_safety/README.md` for what it does and does not
  cover); synthetic fixtures for anything student-shaped; lock-free git
  reads; no push without Owen.
- **Fewer voices:** planning models are consulted for architecture and large phase prompts, not
  relayed on every step.

---

## 13. Open questions, decisions, and ideas

### Decisions Owen needs to make
- **Student-data wording** (§2 #1): confirm or edit. Needed before M2.
- **Monthly cloud budget cap and first cloud model** (Claude suggested). Needed before M2.
- **`cos` as the single entry point**, wrapping `bin/chief-of-staff`. Decided in M1: `bin/cos` is the
  public entry point; `bin/chief-of-staff` is legacy that `cos` may wrap (see §3 Entry points).
- **NAS backups** of student data: default no until decided.
- **Thales email:** is API access allowed by school IT? Default path: Apple Mail read-only.
- **P1 standing grants:** which personal sources may go to which cloud models.
- **iPad:** any P0 view on the local network? Default: no.

### SM5 curriculum decisions (for the Canvas specialist)
- Course name as printed on the teacher's manual (Saxon Math 4 — Course 1 vs Saxon Math 5 vs 5/4).
- Confirm `SM5: Lesson {n} Homework` as the canonical Canvas title.
- Classwork grade title.
- Test cadence and final Written Assessment number (pacing guide may give dated occurrences;
  cadence rules need explicit evidence).
- Whether Investigations are taught and appear on agenda pages.
- Assigned practice (daily #1–10) vs Canvas graded homework (Mon/Wed): confirm the two rule
  families.

### Technical unknowns
- **Workbench framework:** SwiftUI (native, low idle cost, no Node supply chain, matches Owen's
  existing SwiftUI work) vs Tauri vs Electron. The requirement is the expanded-workspace behavior,
  not the framework. Decide at Stage 4.
- Qwen 35B tool-calling reliability with a growing tool menu (mitigation: ≤6 tools per turn,
  structured outputs, retry once then stop).
- Lovable programmatic access (API vs handoff + GitHub).
- Exact headless flags for Cursor CLI and Gemini CLI at adapter time.
- Local embedding model choice for Stage 3 (benchmark on Owen's documents).
- Whether macOS 27 Siri App Intents are stable enough to justify Swift work before Stage 5.

### Ideas parked for later
- Two-model cross-check on high-stakes outputs (Genspark-style).
- Learned routing from outcome logs, published only with approval.
- Hermes Agent as a sandboxed P2-only sidecar for research and errands.
- Natural-language scheduling ("every Friday, check next week's Canvas").
- School / Personal profiles with separate memory.
- Finder and selected-text "Send to Chief of Staff".
- Weekly "kill list" review to retire unused features and keep maintenance small.

### Parked work (kept, not active)
- M-track controlled execution: driver hardening (M5E-H), fresh controlled execution, full
  permission conformance probe (M5F-P), fail → repair → retest loop (M5F). Resume at Stage 6.
- M6 Mac health beyond read-only status (see `MAC-SYSTEMS-HEALTH-RECOVERY.md`).
- Revision 3 pacing intelligence detail (P0–P6) folds into Canvas C0–C1.
