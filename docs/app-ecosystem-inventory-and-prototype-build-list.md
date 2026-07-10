# App Ecosystem Inventory and Prototype Build List

Last updated: 2026-07-03

```text
Status: documentation/status only
Closure: complete_app_ecosystem_inventory_and_prototype_build_list
Classification: planning inventory — not implementation approval
Proof: bin/chief-of-staff --app-ecosystem-inventory-status
Planning lanes program: complete_app_ecosystem_planning_lanes_program
Runtime approval gate: complete_app_runtime_approval_gate_program — `--app-runtime-approval-gate-status` — `--app-ecosystem-planning-lanes-status`
Blocked Tier 4–7 summary: docs/proposals/blocked/high-risk-app-planning-blocked-summary.md
Source: Owen planning input + repo discovery — not repo authority alone
Chief of Staff chooses app priority for Owen: no
Runtime classroom apps: blocked
Student data: blocked — absolute
```

## Purpose

Consolidate Owen's full known **app / tool / game ecosystem** (52 canonical concepts) into one deduplicated, risk-classified inventory and prototype build list. Agent quick-start: `AGENTS.md`. This supersedes the earlier 9-app classroom utility candidate matrix as the **master planning map** — the matrix remains valid for templates already built.

**This document does not approve app runtime, databases, APIs, student data, or AI generation.**

## Source Status Notice

| Source | Role |
| --- | --- |
| Owen uploaded/planning lists (2026-07) | Planning input only — not implementation approval |
| `docs/classroom-utility-app-candidate-matrix.md` | Repo-backed 9-app subset; templates exist |
| `docs/proposals/ideas/external-planning-input-intake-map.md` | External idea classification |
| Repo search (CAL1, Lovable, 3D, Presentation Engine, Health Monitor) | Repo-discovered candidates section |

## Deduplication / Alias Policy

1. **One canonical row per product concept** — aliases listed in the Aliases column.
2. **Tier 7** marks archives and near-duplicates (do not double-count toward build priority).
3. **Thales Academic OS**, **Thales OS Morning Preview**, and **Command Center** share a family — canonical row 14 with cross-refs.
4. **AI Coupon Factory**, **Pass Forge**, **Sensei Studio** → canonical row 13.
5. **GradeMate**, **Automatic Student Worksheet Grader**, **AI Rubric & Writing Grader** → rows 15 and 28 (extension relationship documented).
6. **Desk Layout Design Architect**, **Ultimate Design Architect**, **Design Architect Interview** → related but distinct rows 19, 31, 52.
7. If Owen adds aliases later, update this inventory — do not fork parallel lists.

## App Category Taxonomy

`classroom management` · `behavior / discipline` · `reward economy` · `arcade / game module` · `presentation / display` · `curriculum prep` · `worksheet / assessment` · `Canvas / LMS admin` · `developer utility` · `design / print utility` · `3D / spatial / layout` · `personal utility` · `infrastructure layer` · `legacy archive`

## Risk Classification Legend

| Code | Meaning |
| --- | --- |
| `—` | Not applicable / no meaningful exposure in planning-only mode |
| `low` | Fake labels only; aggregate/non-identifying planning safe |
| `med` | Student-adjacent if real data bound |
| `high` | Student names, grades, behavior, parent comm, or economy ledgers if live |
| `blocked` | Must not implement without explicit Owen mission + safety gates |

## Complete Inventory (52 Canonical Concepts)

| # | Canonical name | Aliases | Category | Tier | SD | BH | GR | PC | CU | DB | API | INT | OCR | AI | Status | Safe planning-only next step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ClassPass | hall pass app | classroom management | 4 | high | med | — | — | — | med | med | med | — | med | template ready | fake pass label template only |
| 2 | Smart Seating | seat map app | classroom management | 4 | med | — | — | — | — | med | — | — | — | — | template ready | fake seat grid labels |
| 3 | Prize Board | recognition board | reward economy | 4 | med | — | — | — | — | med | — | — | — | — | template ready | reward placeholder labels |
| 4 | Coin Store Ledger | classroom economy | reward economy | 4 | high | med | — | — | — | high | — | — | — | — | template ready | fake coin labels only |
| 5 | Noise Meter | UA noise meter | classroom management | 2 | low | — | — | — | — | — | — | — | high | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | threshold labels; no live mic |
| 6 | Spelling Studio | literacy shell | curriculum prep | 3 | med | — | — | — | high | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | fake word-list labels |
| 7 | Classroom Arcade | arcade hub | arcade / game module | 1 | low | — | — | — | low | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | mode labels; no executable games |
| 8 | UA Jobs Management | classroom jobs | classroom management | 4 | med | — | — | — | — | med | — | — | — | — | template ready | job role labels only |
| 9 | Email Responder | parent email automation | Canvas / LMS admin | 4 | high | — | — | high | — | — | high | high | — | high | blocked intake | boundary doc only |
| 10 | Titanium Realm | Zenith, Sovereign Edition | behavior / discipline | 4 | high | high | — | — | — | high | — | — | — | high | planning input | wireframe labels only |
| 11 | Glow/Grow App | AI behavior hub | behavior / discipline | 4 | high | high | — | med | — | high | med | — | — | high | planning input | behavior label concepts only |
| 12 | Classroom Timer & Stopwatch | timer display | presentation / display | 1 | — | — | — | — | — | — | — | — | — | — | **Level 3 runtime prototype** | `--classroom-timer-stopwatch-runtime-status` |
| 13 | AI Coupon Factory | Pass Forge, Sensei Studio | reward economy | 4 | med | — | — | — | — | — | — | — | — | med | planning input | generic coupon templates; no names |
| 14 | Thales Academic OS | Command Center, Pacing Pilot | infrastructure layer | 5 | med | — | — | — | high | high | high | high | — | high | insufficient repo runtime | architecture sketch docs only |
| 15 | GradeMate | worksheet grader | worksheet / assessment | 4 | high | — | high | — | high | med | — | — | high | high | planning input | fake answer key labels |
| 16 | Student Mystery Draw | Star Student, High Fliers | reward economy | 4 | high | — | — | — | — | med | — | — | — | — | planning input | fake draw placeholders |
| 17 | Titanium Jackpot | slot reel module | arcade / game module | 5 | med | — | — | — | — | med | — | — | — | med | planning input | game shell labels; no payouts |
| 18 | Interactive Bingo Caller | bingo randomizer | arcade / game module | 1 | low | — | — | — | low | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | number/card labels only |
| 19 | Desk Layout Design Architect | classroom layout | 3D / spatial / layout | 1 | — | — | — | — | — | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | grid wireframe; no roster bind |
| 20 | Codebase Ingestor | ZIP directory auditor | developer utility | 5 | — | — | — | — | — | — | — | — | — | — | planning input | developer boundary doc |
| 21 | Student Word Cloud Art | word cloud generator | design / print utility | 4 | high | — | — | — | med | — | — | — | — | med | planning input | fake word list only |
| 22 | Daily Schedule Card Designer | schedule publisher | design / print utility | 1 | — | — | — | — | — | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | schedule card wireframe |
| 23 | Canvas LMS Link Extractor | link fetcher | Canvas / LMS admin | 5 | — | — | — | — | — | — | high | high | — | — | blocked | integration posture packet only |
| 24 | Let's Make a Deal Curtain Game | curtain game | arcade / game module | 1 | low | — | — | — | — | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | game show wireframe |
| 25 | Shurley English Chapter Parser | slide architect | curriculum prep | 3 | — | — | — | — | high | — | — | — | high | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | fake chapter outline labels |
| 26 | Daily Agenda and Announcement Engine | morning agenda | presentation / display | 2 | — | — | — | — | low | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | announcement wireframe |
| 27 | Shared AI Common Core Layer | infrastructure master | infrastructure layer | 5 | — | — | — | — | high | high | high | — | — | high | blocked | architecture doc only |
| 28 | AI Rubric & Writing Grader | GradeMate extension | worksheet / assessment | 4 | high | — | high | med | high | med | — | — | — | high | planning input | rubric template labels |
| 29 | Time Bomb Vocabulary Game | vocabulary timer game | arcade / game module | 2 | low | — | — | — | med | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | fake vocab list |
| 30 | Charades Game | gesture randomizer | arcade / game module | 2 | low | — | — | — | — | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | prompt cards wireframe |
| 31 | Ultimate Design Architect | Omni-Prompt Portal | design / print utility | 3 | — | — | — | — | — | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | prompt template docs |
| 32 | Custom Mystery Picker | mystery selector | reward economy | 4 | high | — | — | — | — | med | — | — | — | — | planning input | fake picker labels |
| 33 | Shurley Sentence Diagrammer | blueprint builder | curriculum prep | 3 | — | — | — | — | high | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | fake sentence labels |
| 34 | Valentine Holiday Pass Generator | holiday pass | design / print utility | 3 | med | — | — | — | — | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | generic pass art; no student names |
| 35 | Code Cracker | Vault Cracker Game | arcade / game module | 1 | low | — | — | — | low | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | puzzle wireframe |
| 36 | Live Session Auto-Burst Presentation Engine | auto-burst slides | presentation / display | 2 | — | — | — | — | med | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | static slide plan labels |
| 37 | Omni-App System Health Monitor | safety diff analyzer | developer utility | 6 | — | — | — | — | — | — | — | — | — | — | repo partial | cross-link workstation health monitor docs |
| 38 | Pyramid Game | word association | arcade / game module | 1 | low | — | — | — | low | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | category label cards |
| 39 | Word Scramble | anagram solver | arcade / game module | 1 | low | — | — | — | med | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | fake scrambled words |
| 40 | Thales OS Morning Preview Banner | announcement engine | presentation / display | 2 | — | — | — | — | low | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | banner wireframe |
| 41 | Canvas Creator | homework resource sync | Canvas / LMS admin | 5 | med | — | — | — | high | high | high | high | — | high | blocked | manual copy workflow docs only |
| 42 | Trivia Showdown | trivia game | arcade / game module | 2 | low | — | — | — | med | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | fake question labels |
| 43 | Power Up Packet Maker | packet builder | curriculum prep | 3 | — | — | — | — | high | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | packet outline wireframe |
| 44 | iPad Optimizer Prompt Generator | iPad layout prompts | design / print utility | 1 | — | — | — | — | — | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | prompt template doc |
| 45 | Reading Test Maker | reading assessment builder | worksheet / assessment | 4 | high | — | high | — | high | med | — | — | — | high | planning input | fake passage labels |
| 46 | GentleGrader | React security review | developer utility | 4 | med | — | high | — | high | — | — | — | — | med | planning input | security checklist doc; no grading runtime |
| 47 | Note-Taking Prompt Engine | note app prompts | personal utility | 1 | — | — | — | — | — | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | prompt library doc |
| 48 | Investment Strategy Calculator | paycheck bridge | personal utility | 6 | — | — | — | — | — | — | — | — | — | — | planning input | personal finance worksheet fake |
| 49 | Constitution Prompts Architect | civics prompts | curriculum prep | 3 | — | — | — | — | high | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | fake civics topic labels |
| 50 | Class Pass Early Build Archive | early ClassPass archive | legacy archive | 7 | med | — | — | — | — | — | — | — | — | — | archive | reference only; see row 1 |
| 51 | Science Worksheet Portal | worksheet portal | curriculum prep | 3 | — | — | — | — | high | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | fake science topic labels |
| 52 | Design Architect Interview System | architect interview | design / print utility | 2 | — | — | — | — | — | — | — | — | — | **planning lane complete** | `--app-ecosystem-planning-lanes-status` | interview question wireframe |

**Primary user:** Owen (teacher) for all classroom-facing concepts unless marked personal/dev.

## Prototype / Build Priority Tiers

### Tier 1 — Safest planning-only candidates (planning lanes complete)

Classroom Timer & Stopwatch · Interactive Bingo Caller · Desk Layout Design Architect · Daily Schedule Card Designer · Pyramid Game · Word Scramble · Code Cracker · Let's Make a Deal Curtain Game · Classroom Arcade · Note-Taking Prompt Engine · iPad Optimizer Prompt Generator

### Tier 2 — Safe planning; careful boundary wording (planning lanes complete)

Noise Meter · Time Bomb Vocabulary Game · Charades Game · Trivia Showdown · Thales OS Morning Preview Banner · Live Session Auto-Burst (presentation labels) · Design Architect Interview System · Daily Agenda Engine

### Tier 3 — Valuable; planning lanes complete; Owen decision required before implementation

Spelling Studio · Shurley Chapter Parser · Shurley Sentence Diagrammer · Power Up Packet Maker · Constitution Prompts Architect · Science Worksheet Portal · Ultimate Design Architect · Valentine/Holiday Pass Generator

### Tier 4 — High-risk: student data / behavior / grades / parent comm

ClassPass · Smart Seating · Prize Board · Coin Store Ledger · UA Jobs · Titanium Realm · Glow/Grow · GradeMate · AI Rubric Grader · Student Mystery Draw · Custom Mystery Picker · Email Responder · Student Word Cloud · AI Coupon/Pass with names · Reading Test Maker · GentleGrader (assessment-adjacent)

### Tier 5 — High-risk: API / database / integration / generation

Canvas LMS Link Extractor · Canvas Creator · Thales Academic OS · Shared AI Common Core Layer · Codebase Ingestor · Titanium Jackpot · Live Session Auto-Burst (generation path)

### Tier 6 — Personal / dev tools (outside CAL1 classroom utility lane)

Investment Strategy Calculator · Omni-App Health Monitor (cross-link `docs/teacher-workstation-health-monitor.md`)

### Tier 7 — Duplicate / alias / archive

Class Pass Early Build Archive (→ ClassPass) · AI Coupon Factory aliases (→ row 13) · Thales OS banner (→ Thales family row 14)

## Repo-Discovered Candidates (Insufficient Evidence for 52-List)

| Candidate | Repo anchor | Classification |
| --- | --- | --- |
| Lovable Classroom App Builder | `docs/lovable-classroom-app-builder-status-foundation.md` | planning only; API blocked |
| 3D Builder Workshop Agent | 3D builder status scripts | planning only; export blocked |
| Widget / Shortcut Builder | widget-shortcut-builder docs | Mac install blocked |
| Teacher Workstation Health Monitor | health monitor status | ops docs; not classroom app |
| Presentation Engine renderer | `docs/presentation-engine-renderer-foundation.md` | planning complete; runtime blocked |

## Recommended Next App Planning Missions (Owen Chooses)

1. **Tier 1–3 planning lanes complete** — see `docs/app-ecosystem-planning-lanes-program.md`; `--app-ecosystem-planning-lanes-status` (27 lanes incl. Timer).
2. Owen picks **which app** receives a **runtime implementation mission** next — not implied by planning closure.
3. **Do not** start Tier 4–7 without decision packet + `docs/proposals/blocked/high-risk-app-planning-blocked-summary.md` review.
4. Cross-link: `docs/proposals/blocked/classroom-utility-app-priority-decision-packet.md`


## Relationship to Prior Docs

| Document | Relationship |
| --- | --- |
| `docs/classroom-utility-app-candidate-matrix.md` | 9-app subset; templates built — still valid |
| `docs/classroom-utilities/classroom-timer-stopwatch-planning.md` | First Tier 1 planning lane — `complete_classroom_timer_stopwatch_planning_lane` |
| `docs/owen-architecture-decision-packets.md` | Decision packet #3 references this inventory |

## Proof

```bash
bin/chief-of-staff --app-ecosystem-inventory-status
bash tests/app-ecosystem-inventory-status-test.sh
bin/chief-of-staff --app-ecosystem-planning-lanes-status
bash tests/app-ecosystem-planning-lanes-status-test.sh
bin/chief-of-staff --app-runtime-approval-gate-status
bash tests/app-runtime-approval-gate-status-test.sh
```

## Non-Activation

`complete_app_ecosystem_inventory_and_prototype_build_list` is a documentation closure marker only. No app priority is chosen for Owen. No runtime, student data, database, API, integration, OCR, or AI generation is authorized.