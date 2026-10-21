# PROMPT — CANVAS-PLANNER-1: Weekly Planner redesign + Chief status contract

Approved by Owen on 2026-10-20. The design is the "Canvas Weekly Planner Redesign" canvas
(7 screens). This spec is the written version of it, so you don't need to see the canvas.

## Where you are

- **Repo:** `~/Projects/teacher-ai-workstation`, worktree `~/Projects/taw-cp1`, branch
  `feature/canvas-planner-1` (Owen created it from `origin/main`).
- **Read first:**
  - `AGENTS.md`
  - `CHIEF-OF-STAFF.md`
  - `docs/DECISIONS.md` (D-018, D-022, D-023, D-024, D-025)
  - `docs/programs/canvas-llm/` (contracts and the canonical context pack)
  - `scripts/teacher_workstation/`, `apps/teacher-workstation/`, `scripts/canvas_planner_app/`
  - `scripts/canvas_llm_intake/`, `scripts/canvas_llm_deploy/`
- **Git limits:** don't push or merge. Owen reviews and merges.
- **Canvas:** no live Canvas writes in this phase. Read-only Canvas GET calls are allowed only
  where the existing code already does them. Test against the existing fake/sandbox
  transports.

## The architecture rule

- **The Canvas/Pacing domain owns** week planning, source sync, lesson interpretation,
  assignments, pages, announcements, approvals, and the Friday rollover.
- **Chief of Staff** only reads a status contract and opens deep links.
- **The LLM** interprets and reviews. **Deterministic code** is authoritative for course IDs,
  assignment groups, due dates, page identity, approval state, scheduling, Canvas writes,
  and ledgers.

---

## PART A — Investigate and reconcile (read-only; stop and report)

Do Part A first. Don't change code. Write `docs/canvas-planner-1-findings.md`, then **stop
and report**. Owen approves before Part B.

1. **Current architecture map:**
   - every planner/workstation screen and route
   - the state files under `.local/`
   - week resolution
   - the approval store
   - the deploy and preflight path
   - the rollover engine
   - which modules generate pages, announcements, assignments, and reminders
2. **Branch reconciliation:** compare `wip/canvas-live-q1w9` (the Q1W5–Q1W9 scripts, grade
   entry, and earlier planner work) with `main`. For each file or group, say whether it is
   superseded, still needed, or a duplicate, and what would have to be merged before
   building on it.
3. **Scheduled-jobs inventory:** every LaunchAgent and LaunchDaemon related to this repo,
   with what each runs and when. Include `com.teacher-ai-workstation.grade-check`. Grades
   are the strictest area under D-022: describe exactly what that job reads and writes.
4. **Reusable interfaces vs missing ones,** measured against Part B.
5. **Proposed status contract** (B8) adjusted to the real code, plus the deep-link scheme.
6. **Risks,** and the order you'd build Part B in.

---

## PART B — Build (after Owen approves Part A)

### B1. The five stages

The planner's left sidebar, top to bottom:
- **Week** (overview)
- **1 · Source**
- **2 · Plan**
- **3 · AI review** (badge = open "needs you" count)
- **4 · Preview & approve** (badge = courses to review)
- **5 · Friday**
- then **Completed weeks** and **Settings**

Remove the separate Assignments, Announcements, Questions, Deploy, and System Status
destinations: their content moves into the stages (questions become "needs you" items;
system status moves under Settings).

The sidebar footer shows the true mode, in plain words: "Planning. Nothing goes to Canvas
until Friday 4 PM, or until you choose Publish now."

### B2. Week overview (home)

- **Header:** the week ("Q2W3 · October 26–30") with previous and next week buttons, plus
  "Goes live Friday, October 23 at 4:00 PM, once all 5 are approved."
- **One primary Next button** that always names the single next action ("Next: Review
  Math"). It's computed by code from the week state, in this order: unresolved source
  change, then plan flags, then AI "needs you", then courses to approve. When all are done,
  it reads "Ready for Friday 4 PM."
- **Summary banner** in plain language ("Almost ready for Friday. 4 courses need your
  review, and AI flagged 2 things.").
- **Courses × stages grid:**
  - rows: Math, Reading/Spelling, Language Arts, Science, Homeroom newsletter
  - columns: Source, Plan, Assignments, Page + announcement
  - one action button per row (Review / Fix flag)
  - teacher-facing words only: never `math:page not approved`, never raw state names,
    never hashes
- **Cards:** Pacing source (name, tab, last synced, Resync) and AI check (open findings,
  one line each).

### B3. Source

- **Source panel:** sheet name, tab, last-synced time, connection state. Buttons: **Resync**,
  **Change sheet**, **Open in Google Sheets**.
- **Change sheet** previews the spreadsheet name, tab, detected week columns, subjects, and
  sample values before saving it as the source.
- **Resync never applies on its own.** It computes a delta and shows a "the sheet changed"
  card:
  - each changed cell (old → new)
  - which lessons, assignments, page and announcement it affects
  - which of Owen's edits are kept
  - which subjects are unchanged
  - buttons: **Apply change** / **Keep my current plan**
- **Pacing grid:** subjects × Mon–Fri with dates, exactly as pulled. Cells Owen edited show
  an "Edited" badge.
- **Footer:** **Edit this week** and **Looks right · Continue to Plan**.
- **Daily check:** compare the sheet to the last sync once a day. When something changed,
  expose a `suggestion` action item (B8) like "Pacing changed for Q2W3: Math Tuesday L40 →
  L41."

### B4. Plan

- **One tab per course,** with flag counts on each tab.
- **One table per course,** with a row per day:
  **Day · Sheet says · Your lesson plan (In Class + At Home) · Assignments it will create**
  (each assignment shows its name, group, and due).
  - Reminders show as dashed chips on the day they post.
  - Every cell is editable in place. An edit stores an owner override with an "Edited"
    badge, and a resync never erases it.
  - Editing a lesson updates the proposed assignment beside it.
- **AI notes appear on the row:** a short reason, plus one-click actions such as **Add it**
  or **No, leave it**. Suggestions are blue and non-blocking. "Needs you" items are amber
  and block approval of that course until answered.
- **Saving is automatic, with history:** each sync, edit, AI suggestion accepted or
  declined, approval, and publish is recorded and can be undone.
- **Footer:** **Add an assignment** and **[Course] is planned · See AI review**.

### B5. AI review

- **Runs automatically** after any change, with a delay so edits settle first. There is no
  "run" button.
- **Per-course tiles:** Passed / N needs you.
- **"Needs you" list:** each item has a title, a one-sentence reason, **evidence** (the
  exact sheet cell, plan field, or rule it relied on, in mono text), and two one-click
  answers. For example: "Language Arts: Chapter 5 Test has no reminder · Evidence: sheet,
  Tue 10/27 'Ch5 Test' · [Add reminder for Monday] [Not needed]".
- **"What it checked":**
  - plan matches the sheet
  - Owen's edits kept
  - no missing assignments
  - no assignments without a lesson
  - assessments and reminders
  - each course only mentions its own subject
  - page and announcement agree
  - how shorthand was read

  Each check shows ✓ or "N to check."
- **Output is structured:** PASS / WARN / NEEDS_OWEN / FAIL per check and per finding, with
  evidence. The AI never edits, approves, or publishes.
- **If the model can't run,** show "AI review unavailable" with the reason, and let Owen
  approve anyway after confirming. Never silently PASS, and never block forever.
- **Model choice** follows D-026: use what's available and best for review. Record the model
  used on each run.

### B6. Preview & approve

- **One screen per course:**
  - the **page preview** (left) and **announcement preview** (right), each rendered from the
    **exact HTML** that would be sent, in a frame styled like Canvas content in Owen's page
    standard
  - a Desktop / Phone width toggle
  - the announcement shows its posting time and course
  - its embedded agenda comes from the same HTML as the page
- **Below the previews:** the course's assignments and reminders, with their approval state.
- **"AI check passed"** line (or the open findings).
- **Primary button: Approve [Course]**, which approves page, announcement, assignments, and
  reminders together, tied to their exact content hashes.
- **Secondary:** **Review individual items** and **Edit announcement**.
- **Hashes and page IDs** live under Settings → Technical details only.
- **Re-approval state:** when an approved item changes, show:
  - "Why: the announcement changed after you approved it," with a one-line reason
  - tiles saying what changed and what is still approved
  - the old and new text highlighted
  - **Approve this version** in one click

  Any change to what families see requires re-approval. There's no automatic inheritance
  of approval for "format only" changes.

### B7. Friday

- **Header:** "Friday, October 23 at 4:00 PM · in N days", plus an **Automatic rollover**
  switch.
- **All or nothing, by default:** if any course or the Homeroom newsletter isn't approved,
  show **"Friday rollover is blocked. Nothing publishes until all 5 are approved."** Nothing
  publishes automatically.
- **Friday 1:00 PM reminder:** if anything is still open, expose a `decision` action item
  for Chief.
- **Readiness list** per course, in plain words.
- **"At 4:00 PM, the planner will":**
  1. Make each course's page its home page.
  2. Post the weekly updates.
  3. Create the approved assignments and reminders.
  4. Carry the Homeroom newsletter forward.
  5. Read everything back from Canvas and confirm it matches what was approved.
- **Buttons:**
  - **Dry run now** (every step checked against Canvas, nothing changed)
  - **Publish approved courses only…** (manual, with a warning that families will see mixed
    weeks)
- **Last week:** its result from the rollover ledger, with links to the live pages.
- **Don't create a second scheduler.** Use the existing rollover engine, and the job found in
  Part A.

### B8. Status contract for Chief (D-024)

Provide a local function plus a CLI that returns JSON without network calls:
`bin/canvas-weekly-status --json`. It reads cached local state only. Shape:

```json
{
  "domain": "canvas_weekly_planning",
  "contract_version": 1,
  "generated_at": "ISO",
  "week": {"code": "Q2W3", "label": "October 26–30", "state": "NEEDS_OWEN",
           "source_synced_at": "ISO", "rollover_at": "ISO", "rollover_state": "BLOCKED"},
  "courses": [{"id": "math", "name": "Math",
               "stages": {"source": "done", "plan": "done", "ai_review": "passed",
                          "assignments": "approved", "preview": "to_review"}}],
  "next_action": {"title": "Review Math", "deep_link": "..."},
  "action_items": [{"id": "stable-id", "kind": "decision|suggestion|info",
                    "priority": "high|normal", "course": "language_arts",
                    "title": "Chapter 5 Test has no reminder",
                    "reason": "...", "evidence": "...",
                    "deep_link": "...", "created_at": "ISO", "updated_at": "ISO"}],
  "completed": [{"week": "Q2W2", "result": "...", "verified_at": "ISO"}]
}
```

- **Week states:** SOURCE_SYNCED, PLANNED, AI_REVIEWED, NEEDS_OWEN, READY_TO_PUBLISH,
  HELD_UNTIL_4PM, EXECUTING, PUBLISHED_VERIFIED, BLOCKED.
- **Stable `id`s:** an item disappears when it's resolved.
- **Teacher-facing text** in `title` and `reason`.
- **Deep links:** `http://127.0.0.1:4310/#week/q2w3[/<course>[/plan|ai|preview]]`, plus
  `#week/q2w3/source` and `#week/q2w3/friday`.
- **Server not running:** provide `bin/teacher-workstation --open "<route>"`, which starts the
  server if it isn't running and opens the route.

### B9. Decisions to add to `docs/DECISIONS.md`

- **D-027 (Canvas weekly planning):**
  - the planner owns the workflow
  - Chief reads `canvas-weekly-status` and opens deep links only
  - the LLM reviews with evidence, and is never authoritative
  - approval is per course and tied to exact content
  - any change to what families see needs re-approval with a diff
- **D-028 (Friday rollover):**
  - all or nothing by default
  - a 1 PM reminder when anything is open
  - partial publish only as a manual action with a warning
  - read-back verification after every publish

## Tests

- **Contract tests:** shape, stable ids, freshness fields, no network.
- **Resync delta:** changed cells, kept overrides, unchanged subjects, and nothing applied
  without a click.
- **Plan:** overrides survive a resync; editing a lesson updates its assignment.
- **AI review:** findings carry evidence; unavailable gives UNAVAILABLE, never PASS; the AI
  can't write.
- **Approval:** hash-tied; a change creates the re-approval state with a correct diff.
- **Friday:** blocked when anything is unapproved; dry run makes no writes; partial publish
  requires an explicit confirm.
- **Preview:** renders the exact HTML that would be sent; the page and announcement agenda
  come from one source.
- **Server protection** (REL-1) still passes for every new mutating route.
- **Repo validation:** the existing 167-command set has no new failures.

## Report

- the Part A findings (then stop)
- for Part B: commit SHAs, screenshots or descriptions of each screen, test counts, the
  contract output for Q2W3, open risks, and Owen's exact steps to try the new planner
- `git status -sb`
