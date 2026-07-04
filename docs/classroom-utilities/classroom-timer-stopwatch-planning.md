# Classroom Timer & Stopwatch — Planning Lane

Last updated: 2026-07-04

```text
Status: planning-only — not implementation approval
Closure: complete_classroom_timer_stopwatch_planning_lane
Classification: Tier 1 single-app planning lane — Owen selected
Proof: bin/chief-of-staff --classroom-timer-stopwatch-planning-status
App ecosystem inventory: row 12 — docs/app-ecosystem-inventory-and-prototype-build-list.md
Runtime classroom app: blocked
Student data: blocked — absolute
Database/API/integration: blocked
AI generation / local models: blocked
```

## Purpose

Plan a future **local/offline classroom timer and stopwatch utility** for smartboard and teacher-display use — without implementing runtime app behavior, executable timer logic, or persistence.

**Owen selected this app for a planning lane only. Runtime implementation is not approved.**

Classroom Timer & Stopwatch would eventually help eliminate separate timer utilities by embedding instruction-goal countdowns, stopwatch loops, visual progress concepts, and quick timing presets for classroom activities. This mission documents that vision as **planning-only**.

## App Summary

| Dimension | Detail |
| --- | --- |
| Canonical name | Classroom Timer & Stopwatch |
| Category | presentation / display |
| Build tier | 1 (safest planning-only) |
| Primary user | Owen (teacher) |
| Student-facing | display-only future concept — no student accounts |
| Data posture | **no data saved** default (future) |
| Network | offline/local future posture — blocked until mission |

## Teacher Workflow (Planned)

1. Owen opens future timer utility on classroom display (smartboard or teacher Mac — **not built**).
2. Select mode: **countdown**, **stopwatch**, or **interval/loop** (planning labels only).
3. Apply quick preset (+1m, +3m, +5m, +10m) or custom duration label.
4. Start/pause/reset — teacher-only controls (concept).
5. Session ends; **no log retained** by default (future boundary).

## Classroom Display Workflow (Planned)

| Step | Display concept |
| --- | --- |
| Idle | Large clock label placeholder; mode selector |
| Countdown active | Full-screen minutes:seconds label; progress ring concept |
| Stopwatch active | Elapsed time label; lap markers as text-only placeholders |
| Interval loop | Round N of M label; between-round pause concept |
| Complete | Optional brief “time’s up” text state — **no audio in planning lane** |

## Smartboard Use Case

- High-contrast large typography for back-of-room visibility.
- Minimal chrome; teacher control on separate device or corner panel (future).
- No student names, scores, or roster binding on display.

## Display Mode Ideas (Non-Runtime)

| Mode | Planning description |
| --- | --- |
| Countdown timer | Single target duration; visual progress ring (text description) |
| Stopwatch | Count-up elapsed; optional lap list as fake labels |
| Interval / loop | Repeat N rounds with work/rest duration labels |
| Quick presets | +1m, +3m, +5m, +10m chip labels |

## Fake / Local Settings Examples

See `assistant/classroom-utilities/samples/classroom-timer-stopwatch-planning/`. All fixtures are `fake_local_planning_only` — not consumed by any runtime.

| Example preset label | Duration label | Mode |
| --- | --- | --- |
| `example-warmup-round` | 3:00 | countdown |
| `example-partner-share` | 5:00 | countdown |
| `example-exit-ticket` | 2:00 | countdown |
| `example-station-rotation` | 10:00 | interval (3 rounds) |
| `example-free-stopwatch` | — | stopwatch |

## Text-Only Wireframe Sketches

### Smartboard — Countdown Active

```text
+--------------------------------------------------+
|  [COUNTDOWN]          [STOPWATCH]    [INTERVAL]   |
|                                                  |
|                    05:00                         |
|              ((( progress ring )))               |
|                                                  |
|     [ +1m ]  [ +3m ]  [ +5m ]  [ +10m ]          |
|              [ PAUSE ]    [ RESET ]              |
+--------------------------------------------------+
Teacher-only controls — no student data on screen.
```

### Teacher Control Panel (Future Concept)

```text
Mode: Countdown | Preset: example-partner-share (5:00)
[ START ]  [ PAUSE ]  [ RESET ]
No data saved. Offline local default.
```

## No-Student-Data Proof

| Check | State |
| --- | --- |
| Student names on display | **blocked** |
| Rosters / seating | **not used** |
| Grades / assessment | **not used** |
| Behavior logs | **not used** |
| Persistence of sessions | **blocked** in planning default |
| Analytics / tracking | **blocked** |

## Blocked Capabilities

```text
runtime timer app
HTML/CSS/JS executable timer
React/Vue/Svelte components
browser execution page
widget / shortcut / Mac app
audio playback / alarm sounds
animation runtime
localStorage / database persistence
student data
API/OAuth/network
Drive/NAS/iCloud/Canvas
real curriculum binding
AI generation
local model/Ollama execution
```

## Future Implementation Approval Path

1. Owen approves separate **runtime implementation mission** (not this planning lane).
2. Mission must cite this doc + `--classroom-timer-stopwatch-planning-status` PASS.
3. Implementation remains offline/local-first unless integration mission approved.
4. Student-data boundaries from `docs/classroom-utility-student-data-boundaries.md` still apply.
5. No database without explicit data-governance mission.

## Chief of Staff Verification

```bash
bin/chief-of-staff --classroom-timer-stopwatch-planning-status
bash tests/classroom-timer-stopwatch-planning-status-test.sh
```

CoS verifies planning artifacts and boundaries only — does not run a timer or open a browser.

## Safe Cursor Extension (Later)

- Add fake preset JSON illustrations only.
- Expand wireframe text descriptions.
- Read-only status hardening.
- **Do not** add `.html`, `.js`, `.tsx`, or executable timer logic without runtime mission.

## Cross-Links

| Document | Role |
| --- | --- |
| `docs/app-ecosystem-inventory-and-prototype-build-list.md` | Master 52-app inventory (row 12) |
| `docs/proposals/blocked/classroom-utility-app-priority-decision-packet.md` | Owen priority context |
| `docs/classroom-utility-student-data-boundaries.md` | Student-data absolute block |
| `docs/classroom-utility-per-app-mission-template.md` | Reusable mission scaffold |

## Non-Activation

`complete_classroom_timer_stopwatch_planning_lane` is a documentation closure marker only. No runtime app, timer logic, or student data is authorized.
