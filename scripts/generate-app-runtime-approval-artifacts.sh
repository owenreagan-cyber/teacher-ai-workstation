#!/usr/bin/env bash
# One-time generator for runtime approval packets and readiness matrix. Not invoked by status/dashboard.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

python3 <<'PY'
import json
from pathlib import Path

root = Path('.')
planning = json.loads((root / 'assistant/app-ecosystem/samples/planning-lanes-manifest.json').read_text())
canonical = json.loads((root / 'assistant/app-ecosystem/samples/canonical-inventory-ids.json').read_text())

planning_by_slug = {e['slug']: e for e in planning['tier_1_3_lanes']}

# Inventory tier map (52 canonical rows)
TIER = {
    'classpass': 4, 'smart-seating': 4, 'prize-board': 4, 'coin-store-ledger': 4,
    'noise-meter': 2, 'spelling-studio': 3, 'classroom-arcade': 1,
    'ua-jobs-management': 4, 'email-responder': 4, 'titanium-realm': 4,
    'glow-grow-app': 4, 'classroom-timer-stopwatch': 1, 'ai-coupon-factory': 4,
    'thales-academic-os': 5, 'grademate': 4, 'student-mystery-draw': 4,
    'titanium-jackpot': 5, 'interactive-bingo-caller': 1,
    'desk-layout-design-architect': 1, 'codebase-ingestor': 5,
    'student-word-cloud-art': 4, 'daily-schedule-card-designer': 1,
    'canvas-lms-link-extractor': 5, "lets-make-a-deal-curtain-game": 1,
    'shurley-chapter-parser': 3, 'daily-agenda-announcement-engine': 2,
    'shared-ai-common-core-layer': 5, 'ai-rubric-writing-grader': 4,
    'time-bomb-vocabulary-game': 2, 'charades-game': 2,
    'ultimate-design-architect': 3, 'custom-mystery-picker': 4,
    'shurley-sentence-diagrammer': 3, 'valentine-holiday-pass-generator': 3,
    'code-cracker': 1, 'live-session-auto-burst': 2,
    'omni-app-health-monitor': 6, 'pyramid-game': 1, 'word-scramble': 1,
    'thales-morning-preview-banner': 2, 'canvas-creator': 5,
    'trivia-showdown': 2, 'power-up-packet-maker': 3,
    'ipad-optimizer-prompt-generator': 1, 'reading-test-maker': 4,
    'gentlegrader': 4, 'note-taking-prompt-engine': 1,
    'investment-strategy-calculator': 6, 'constitution-prompts-architect': 3,
    'class-pass-early-build-archive': 7, 'science-worksheet-portal': 3,
    'design-architect-interview-system': 2,
}

PLANNING_SLUG_ALIASES = {
    'live-session-auto-burst': 'live-session-auto-burst-presentation',
    'thales-morning-preview-banner': 'thales-os-morning-preview-banner',
}

def classify(slug, tier, name):
    planning_slug = PLANNING_SLUG_ALIASES.get(slug, slug)
    if planning_slug in planning_by_slug:
        lane = planning_by_slug[planning_slug]
        t = lane['tier']
        if t == 3:
            return 'planning_complete_needs_owen_decision', 2
        if planning_slug in ('live-session-auto-burst-presentation', 'noise-meter'):
            return 'planning_complete_needs_owen_decision', 2
        if planning_slug == 'classroom-timer-stopwatch':
            return 'planning_complete_runtime_candidate', 2
        return 'planning_complete_runtime_candidate', 2
    if slug == 'class-pass-early-build-archive':
        return 'duplicate_or_superseded', 0
    if tier == 7:
        return 'duplicate_or_superseded', 0
    if tier == 6:
        if slug == 'omni-app-health-monitor':
            return 'proposal_only_insufficient_repo_evidence', 0
        return 'out_of_scope', 0
    if slug in ('canvas-lms-link-extractor', 'canvas-creator', 'thales-academic-os', 'codebase-ingestor'):
        return 'proposal_only_blocked_integration', 0
    if slug in ('shared-ai-common-core-layer', 'titanium-jackpot', 'glow-grow-app'):
        return 'proposal_only_blocked_ai_generation', 0
    if slug in ('grademate', 'reading-test-maker', 'shurley-chapter-parser', 'shurley-sentence-diagrammer'):
        return 'proposal_only_blocked_real_curriculum', 0
    if slug == 'email-responder':
        return 'proposal_only_blocked_integration', 0
    if tier == 4:
        return 'proposal_only_blocked_student_data', 0
    if tier == 5:
        return 'proposal_only_blocked_integration', 0
    return 'proposal_only_insufficient_repo_evidence', 0

entries = []
for item in canonical['entries']:
    slug = item['slug']
    tier = TIER.get(slug, 0)
    state, level = classify(slug, tier, item['canonical_name'])
    planning_slug = PLANNING_SLUG_ALIASES.get(slug, slug)
    lane = planning_by_slug.get(planning_slug)
    packet = None
    if lane and level == 2:
        packet = f"docs/app-ecosystem/implementation-packets/{planning_slug}-implementation-packet.md"
    entries.append({
        'inventory_id': item['id'],
        'canonical_name': item['canonical_name'],
        'slug': slug,
        'planning_slug': planning_slug if lane else None,
        'tier': tier,
        'readiness_state': state,
        'production_readiness_level': level,
        'runtime_approved': False,
        'planning_doc': lane['doc'] if lane else None,
        'implementation_packet': packet,
    })

packet_dir = root / 'docs/app-ecosystem/implementation-packets'
packet_dir.mkdir(parents=True, exist_ok=True)

def write_packet(lane, state):
    slug = lane['slug']
    name = lane['name']
    tier = lane['tier']
    path = packet_dir / f'{slug}-implementation-packet.md'
    owen_gate = 'Tier 3 Owen decision required before runtime mission.' if tier == 3 else 'Owen explicit runtime implementation mission required.'
    special = ''
    if slug == 'live-session-auto-burst-presentation':
        special = '\n**Note:** Display-label planning only; AI generation path remains blocked.\n'
    if slug == 'noise-meter':
        special = '\n**Note:** Live microphone/OCR paths blocked; visual threshold labels only if approved.\n'
    fixture = lane.get('fixture') or 'assistant/classroom-utilities/samples/classroom-timer-stopwatch-planning/'
    content = f"""# {name} — Runtime Implementation Packet

Last updated: 2026-07-04

```text
Status: Level 2 — runtime approval packet drafted — NOT runtime approved
Readiness state: {state}
Production readiness level: 2 (packet drafted)
Runtime approved: no
Planning lane: complete
Inventory tier: {tier}
Owen approval required: yes — explicit implementation mission
```

## Planning Sources

- Planning doc: `{lane['doc']}`
- Fixture: `{fixture}`
- Closure: `{lane['closure']}`

## Classroom Use Summary

Teacher-facing classroom utility per planning lane. Fake/local labels only until Owen approves runtime.

{special}

## Current vs Recommended State

| Field | Value |
| --- | --- |
| Current readiness level | 2 — packet drafted |
| Recommended next state | 3 — Owen-approved runtime implementation mission only |
| Runtime approved | **no** |

## Proposed Local-Only Implementation Surface (If Ever Approved)

- Static HTML/CSS/JS page under `docs/classroom-utilities/` or approved local path — **not built**
- Teacher-controlled display; no student roster binding
- Offline/local; no network

## Explicitly Blocked Runtime Surfaces

```text
runtime execution in this repo state
student names / rosters / grades / behavior logs
real curriculum ingestion / copied content
database / API / OAuth / network calls
localStorage / sessionStorage persistence (unless separately approved)
audio playback / animations (unless separately approved)
widgets / shortcuts / Mac app install
AI generation / local models / Ollama
production registry writes / --write
```

## Risk Summary

| Risk | Level |
| --- | --- |
| Student data | blocked — absolute |
| Curriculum data | blocked unless fake labels only |
| Integration | blocked |
| AI generation | blocked |
| Persistence | blocked by default |
| Audio/animation | blocked unless separately approved |
| Widget/shortcut/Mac | blocked |

## Required Owen Approval

{owen_gate}

Owen must use explicit wording in a separate mission prompt, e.g.:

> "I approve runtime implementation for {name} local-only prototype per the implementation packet and runtime approval gate."

## Required Validation Before Implementation

- `--app-runtime-approval-gate-status` PASS
- `--app-ecosystem-planning-lanes-status` PASS
- App planning status PASS (if per-app command exists)
- `docs/app-ecosystem/runtime-implementation-approval-gate.md` cited

## Required Validation After Implementation

- Dashboard / validate-all / phase-1 / smoke PASS
- No student data; no forbidden integrations
- Status command for app (if added)

## Escalation Triggers

- Any student roster binding request
- Any network/API/OAuth requirement
- Any real curriculum file intake
- Any production registry write
- Any AI generation path

## Non-Activation

This packet does not authorize runtime implementation.
"""
    path.write_text(content)

for lane in planning['tier_1_3_lanes']:
    slug = lane['slug']
    tier = lane['tier']
    if tier == 3 or slug in ('live-session-auto-burst-presentation', 'noise-meter'):
        state = 'planning_complete_needs_owen_decision'
    elif slug == 'classroom-timer-stopwatch':
        state = 'planning_complete_runtime_candidate'
    else:
        state = 'planning_complete_runtime_candidate'
    write_packet(lane, state)

# Readiness matrix markdown
counts = {}
for e in entries:
    counts[e['readiness_state']] = counts.get(e['readiness_state'], 0) + 1

matrix_md = """# App Production Readiness Matrix

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

"""
for state in sorted(counts.keys()):
    matrix_md += f"- `{state}`: **{counts[state]}**\n"
matrix_md += "\n- `runtime_approved`: **0**\n\n"

matrix_md += "## Full Matrix (52 Apps)\n\n"
matrix_md += "| ID | App | Tier | Level | Readiness state | Runtime approved | Packet |\n"
matrix_md += "| --- | --- | --- | --- | --- | --- | --- |\n"
for e in entries:
    pkt = e['implementation_packet'] or '—'
    if pkt != '—':
        pkt = f"`{Path(pkt).name}`"
    matrix_md += f"| {e['inventory_id']} | {e['canonical_name']} | {e['tier']} | {e['production_readiness_level']} | `{e['readiness_state']}` | no | {pkt} |\n"

matrix_md += """
## Cross-Links

- Runtime approval gate: `docs/app-ecosystem/runtime-implementation-approval-gate.md`
- Boundary checklist: `docs/app-ecosystem/runtime-app-boundary-checklist.md`
- Planning lanes program: `docs/app-ecosystem-planning-lanes-program.md`
- Tier 4–7 blocked: `docs/proposals/blocked/high-risk-app-planning-blocked-summary.md`
- First candidate detail: `docs/app-ecosystem/implementation-packets/classroom-timer-stopwatch-runtime-approval-packet.md`

## Non-Activation

No app in this matrix is runtime-approved. Level 2 means packet drafted only.
"""

(root / 'docs/app-ecosystem/app-production-readiness-matrix.md').write_text(matrix_md)

manifest = {
    'version': '2026-07-04-v1',
    'program_closure': 'complete_app_runtime_approval_gate_program',
    'runtime_approved_count': 0,
    'tier_1_3_packet_count': len(planning['tier_1_3_lanes']),
    'readiness_state_counts': counts,
    'entries': entries,
    'approval_gate_doc': 'docs/app-ecosystem/runtime-implementation-approval-gate.md',
    'boundary_checklist_doc': 'docs/app-ecosystem/runtime-app-boundary-checklist.md',
    'readiness_matrix_doc': 'docs/app-ecosystem/app-production-readiness-matrix.md',
    'first_candidate_packet': 'docs/app-ecosystem/implementation-packets/classroom-timer-stopwatch-runtime-approval-packet.md',
}
(root / 'assistant/app-ecosystem/samples/runtime-approval-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f"packets: {len(planning['tier_1_3_lanes'])}")
print(f"matrix entries: {len(entries)}")
print("counts:", counts)
PY
