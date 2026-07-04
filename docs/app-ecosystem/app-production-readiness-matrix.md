# App Production Readiness Matrix

Last updated: 2026-07-04

```text
Status: documentation/status only — not runtime approval
Closure: complete_app_runtime_approval_gate_program
Proof: bin/chief-of-staff --app-runtime-approval-gate-status
Runtime-approved apps: 0
Chief of Staff chooses app priority for Owen: no
```

## Production Readiness Levels

| Level | Name | Meaning |
| --- | --- | --- |
| 0 | Inventory only | Listed in 52-app inventory; no planning lane |
| 1 | Planning lane complete | Tier 1–3 planning doc + fixtures |
| 2 | Runtime approval packet drafted | This mission — **not runtime approved** |
| 3 | Owen-approved runtime implementation mission | Requires explicit Owen prompt |
| 4 | Local-only runtime prototype merged | Future — blocked until Level 3 |
| 5 | Classroom-safe local utility validation | Future |
| 6 | Widget/shortcut/Mac wrapper proposal | Future — blocked |
| 7 | Integration/generation expansion proposal | Future — blocked |

**This mission moves Tier 1–3 apps to Level 2 only.**

## Readiness State Summary

- `duplicate_or_superseded`: **1**
- `out_of_scope`: **1**
- `planning_complete_needs_owen_decision`: **10**
- `planning_complete_runtime_candidate`: **16**
- `proposal_only_blocked_ai_generation`: **3**
- `proposal_only_blocked_integration`: **5**
- `proposal_only_blocked_real_curriculum`: **2**
- `proposal_only_blocked_student_data`: **12**
- `proposal_only_insufficient_repo_evidence`: **2**

- `runtime_approved`: **0**

## Full Matrix (52 Apps)

| ID | App | Tier | Level | Readiness state | Runtime approved | Packet |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ClassPass | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 2 | Smart Seating | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 3 | Prize Board | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 4 | Coin Store Ledger | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 5 | Noise Meter | 2 | 2 | `planning_complete_needs_owen_decision` | no | `noise-meter-implementation-packet.md` |
| 6 | Spelling Studio | 3 | 2 | `planning_complete_needs_owen_decision` | no | `spelling-studio-implementation-packet.md` |
| 7 | Classroom Arcade | 1 | 2 | `planning_complete_runtime_candidate` | no | `classroom-arcade-implementation-packet.md` |
| 8 | UA Jobs Management | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 9 | Email Responder | 4 | 0 | `proposal_only_blocked_integration` | no | — |
| 10 | Titanium Realm | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 11 | Glow/Grow App | 4 | 0 | `proposal_only_blocked_ai_generation` | no | — |
| 12 | Classroom Timer & Stopwatch | 1 | 2 | `planning_complete_runtime_candidate` | no | `classroom-timer-stopwatch-implementation-packet.md` |
| 13 | AI Coupon Factory | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 14 | Thales Academic OS | 5 | 0 | `proposal_only_blocked_integration` | no | — |
| 15 | GradeMate | 4 | 0 | `proposal_only_blocked_real_curriculum` | no | — |
| 16 | Student Mystery Draw | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 17 | Titanium Jackpot | 5 | 0 | `proposal_only_blocked_ai_generation` | no | — |
| 18 | Interactive Bingo Caller | 1 | 2 | `planning_complete_runtime_candidate` | no | `interactive-bingo-caller-implementation-packet.md` |
| 19 | Desk Layout Design Architect | 1 | 2 | `planning_complete_runtime_candidate` | no | `desk-layout-design-architect-implementation-packet.md` |
| 20 | Codebase Ingestor | 5 | 0 | `proposal_only_blocked_integration` | no | — |
| 21 | Student Word Cloud Art | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 22 | Daily Schedule Card Designer | 1 | 2 | `planning_complete_runtime_candidate` | no | `daily-schedule-card-designer-implementation-packet.md` |
| 23 | Canvas LMS Link Extractor | 5 | 0 | `proposal_only_blocked_integration` | no | — |
| 24 | Let's Make a Deal Curtain Game | 1 | 2 | `planning_complete_runtime_candidate` | no | `lets-make-a-deal-curtain-game-implementation-packet.md` |
| 25 | Shurley English Chapter Parser | 3 | 2 | `planning_complete_needs_owen_decision` | no | `shurley-chapter-parser-implementation-packet.md` |
| 26 | Daily Agenda and Announcement Engine | 2 | 2 | `planning_complete_runtime_candidate` | no | `daily-agenda-announcement-engine-implementation-packet.md` |
| 27 | Shared AI Common Core Layer | 5 | 0 | `proposal_only_blocked_ai_generation` | no | — |
| 28 | AI Rubric & Writing Grader | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 29 | Time Bomb Vocabulary Game | 2 | 2 | `planning_complete_runtime_candidate` | no | `time-bomb-vocabulary-game-implementation-packet.md` |
| 30 | Charades Game | 2 | 2 | `planning_complete_runtime_candidate` | no | `charades-game-implementation-packet.md` |
| 31 | Ultimate Design Architect | 3 | 2 | `planning_complete_needs_owen_decision` | no | `ultimate-design-architect-implementation-packet.md` |
| 32 | Custom Mystery Picker | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 33 | Shurley Sentence Diagrammer | 3 | 2 | `planning_complete_needs_owen_decision` | no | `shurley-sentence-diagrammer-implementation-packet.md` |
| 34 | Valentine Holiday Pass Generator | 3 | 2 | `planning_complete_needs_owen_decision` | no | `valentine-holiday-pass-generator-implementation-packet.md` |
| 35 | Code Cracker | 1 | 2 | `planning_complete_runtime_candidate` | no | `code-cracker-implementation-packet.md` |
| 36 | Live Session Auto-Burst Presentation Engine | 2 | 2 | `planning_complete_needs_owen_decision` | no | `live-session-auto-burst-presentation-implementation-packet.md` |
| 37 | Omni-App System Health Monitor | 6 | 0 | `proposal_only_insufficient_repo_evidence` | no | — |
| 38 | Pyramid Game | 1 | 2 | `planning_complete_runtime_candidate` | no | `pyramid-game-implementation-packet.md` |
| 39 | Word Scramble | 1 | 2 | `planning_complete_runtime_candidate` | no | `word-scramble-implementation-packet.md` |
| 40 | Thales OS Morning Preview Banner | 2 | 2 | `planning_complete_runtime_candidate` | no | `thales-os-morning-preview-banner-implementation-packet.md` |
| 41 | Canvas Creator | 5 | 0 | `proposal_only_blocked_integration` | no | — |
| 42 | Trivia Showdown | 2 | 2 | `planning_complete_runtime_candidate` | no | `trivia-showdown-implementation-packet.md` |
| 43 | Power Up Packet Maker | 3 | 2 | `planning_complete_needs_owen_decision` | no | `power-up-packet-maker-implementation-packet.md` |
| 44 | iPad Optimizer Prompt Generator | 1 | 0 | `proposal_only_insufficient_repo_evidence` | no | — |
| 45 | Reading Test Maker | 4 | 0 | `proposal_only_blocked_real_curriculum` | no | — |
| 46 | GentleGrader | 4 | 0 | `proposal_only_blocked_student_data` | no | — |
| 47 | Note-Taking Prompt Engine | 1 | 2 | `planning_complete_runtime_candidate` | no | `note-taking-prompt-engine-implementation-packet.md` |
| 48 | Investment Strategy Calculator | 6 | 0 | `out_of_scope` | no | — |
| 49 | Constitution Prompts Architect | 3 | 2 | `planning_complete_needs_owen_decision` | no | `constitution-prompts-architect-implementation-packet.md` |
| 50 | Class Pass Early Build Archive | 7 | 0 | `duplicate_or_superseded` | no | — |
| 51 | Science Worksheet Portal | 3 | 2 | `planning_complete_needs_owen_decision` | no | `science-worksheet-portal-implementation-packet.md` |
| 52 | Design Architect Interview System | 2 | 2 | `planning_complete_runtime_candidate` | no | `design-architect-interview-system-implementation-packet.md` |

## Cross-Links

- Runtime approval gate: `docs/app-ecosystem/runtime-implementation-approval-gate.md`
- Boundary checklist: `docs/app-ecosystem/runtime-app-boundary-checklist.md`
- Planning lanes program: `docs/app-ecosystem-planning-lanes-program.md`
- Tier 4–7 blocked: `docs/proposals/blocked/high-risk-app-planning-blocked-summary.md`
- First candidate detail: `docs/app-ecosystem/implementation-packets/classroom-timer-stopwatch-runtime-approval-packet.md`

## Non-Activation

No app in this matrix is runtime-approved. Level 2 means packet drafted only.
