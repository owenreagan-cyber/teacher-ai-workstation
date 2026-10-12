# Canvas Archaeology

Old repositories, superseded logic, and useful precedents. Read-only reference; do not migrate large amounts of old code blindly, and do not copy old Supabase/Firebase architecture into the current repo unless specifically required.

```text
Status: reference record
```

## Legacy/reference repositories

| Repo | Classification | Notes |
| --- | --- | --- |
| `/Users/owen/Projects/pacing-sync-pilot-8c50be47` | SUPERSEDED | Vite/React + Supabase pacing app. Contains `ANNOUNCEMENT_LOGIC.md`, `AUDIT_REPORT.md`. Do not copy Supabase architecture. |
| `/Users/owen/Projects/canvas-weekly-agenda-generator` | SUPERSEDED | Vite/React + TS agenda generator. Historical agenda-generation logic. |
| `/Users/owen/Projects/Thalescanvasgemini` | SUPERSEDED | Firebase/Supabase app with `firebase-blueprint.json`, `vercel.json`. Do not copy. |
| `/Users/owen/Projects/_Archive/2026-08-28-classroom-old/teacher-ai-workstation-q1w3` | SUPERSEDED | Older snapshot of this repo (Q1W3 era). Useful for diffing prior state. |
| `/Users/owen/Projects/teacher-ai-workstation-chief-of-staff-recovery` | EXPERIMENTAL | Chief-of-Staff recovery worktree. |
| `/Users/owen/Projects/teacher-ai-workstation-chief-of-staff-v1-phase1` | EXPERIMENTAL | Chief-of-Staff v1 phase-1 worktree. |
| `/Users/owen/Projects/teacher-ai-workstation-local-test` | EXPERIMENTAL | Local test clone. |
| `/Users/owen/Projects/thales-legacy-discovery` | EXPERIMENTAL | Empty scaffold (`extracted/`, `notes/`, `reports/`, `sources/` all empty). Placeholder for a legacy-discovery pass; nothing assessable. |

## Classification vocabulary

```text
CURRENT            — active authority
USEFUL_PRECEDENT   — historical behavior worth keeping as evidence
SUPERSEDED         — retained for history, not active
EXPERIMENTAL       — exploratory worktree/prototype
UNKNOWN            — not yet assessed
```

## Useful precedents (repo-local)

- Q1W9 production precedent: `scripts/canvas-llm/q1w9_build.py`, `q1w9_verify.py`, `q1w9_homeroom_repair.py`, `q1w9_picnic_link_fix.py`
- Canonical agenda HTML standard (Q1W1-derived): `docs/programs/canvas-llm/phase-22-predictive-weekly-planning-workstation/standards/canvas-weekly-agenda-html-standard-2026-2027.html`
- Live Q1W7 Math agenda sample (preserved): `config/curriculum/canvas/templates/samples/math-weekly-agenda-q1w7.html`

## Migration rule table

For each useful legacy rule, record: source repo, source file, rule/behavior, whether current, whether superseded, whether it should be migrated.

| Source repo | Source file | Rule/behavior | Current? | Superseded? | Migrate? |
| --- | --- | --- | --- | --- | --- |
| pacing-sync-pilot-8c50be47 | `ANNOUNCEMENT_LOGIC.md` | announcement drafting logic | no | yes | no (reference only) |
| canvas-weekly-agenda-generator | `src/` | agenda generation | no | yes | no (superseded by operating contract) |
| Thalescanvasgemini | `functions/`, `firebase-blueprint.json` | Supabase/Firebase architecture | no | yes | no (explicitly excluded) |

Older Supabase architecture must not be copied into the current repo. See `docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md` §15 for the de-scoped features list.
