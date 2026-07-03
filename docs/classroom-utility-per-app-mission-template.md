# Classroom Utility — Per-App Mission Template

Last updated: 2026-07-03

```text
Status: planning-only mission template
Closure: complete_classroom_utility_per_app_mission_templates
Classification: reusable Cursor mission scaffold — not implementation approval
```

## Purpose

Canonical reusable template for future **Classroom Utility per-app** planning missions. Copy and adapt this structure when Owen approves a scoped planning or implementation mission for a single classroom utility app candidate.

**This template does not authorize runtime apps, student data, or integrations.**

## Mission

Describe the single app candidate, planning-only vs implementation scope, and explicit Owen authorization required.

## Baseline / Current State

```text
Latest local main commit:
Dashboard / validate-all posture:
Production registry parked state:
CAL1 / templates status:
Prior related missions merged:
```

## Authority Docs

Minimum reads before editing:

```text
docs/engineering-constitution.md
docs/implementation-approval-gate.md
docs/classroom-utility-student-data-boundaries.md
docs/classroom-utility-app-candidate-matrix.md
docs/classroom-app-lab-prototype-rescue-foundation.md
docs/classroom-app-lab-non-activation-boundaries.md
docs/classroom-utility-templates/<app>-planning-template.md
```

## Approved Repo Edits vs Blocked Runtime/Product Writes

### Approved (planning missions)

```text
planning docs
fake/local fixtures
read-only status scripts
negative tests
proposal updates
roadmap coherence updates
```

### Blocked unless separate explicit mission

```text
runtime classroom apps
student data (names, rosters, grades, behavior logs, IEP)
real seating charts / pass logs / prize ledgers
parent/student communication
Drive/Canvas/NAS/iCloud/API/OAuth/network
AI generation
production registry writes
--write / writer scripts
```

## Approved Scope

Define per-app planning deliverables: docs, fake fixtures, status checks, boundary cross-links.

## Out-of-Scope Items

List app-specific runtime, data, and integration boundaries.

## Fake/Local Fixtures

Use `assistant/classroom-utilities/samples/planning/` with labels like `example-student-a`, `example-seat-01`. No real names or school data.

## Blocked Student-Data Boundaries

Cross-link `docs/classroom-utility-student-data-boundaries.md`. State fake-label-only posture.

## Validation Requirements

```text
bin/chief-of-staff --dashboard
bin/chief-of-staff --classroom-utility-templates-status
bin/chief-of-staff --classroom-app-lab-status
targeted per-app tests if added
```

Dashboard and validate-all must remain 0 WARN / 0 FAIL unless documented otherwise.

## Autonomous Workflow

```text
1. Confirm clean main, create branch.
2. Read authority docs and app planning template.
3. Implement approved planning scope only.
4. Run validation stack.
5. Self-review for student-data and runtime false approval.
6. PR lifecycle per senior-engineer rules.
```

## Escalation Conditions

Stop if work requires student data, runtime apps, integrations, registry mutation, or Owen architecture decisions not in mission scope.

## Definition of Done

Planning mission done when docs/fixtures/status/tests prove planning-only state; production registry parked; no runtime activation.

## Final Report Format

```text
Branch / PR / merge commit / main commit / working tree
Validation table (dashboard, templates status, validate-all, smoke)
App planning proof (docs, fixtures, runtime blocked, student data blocked)
Production registry parked-state proof
Safety confirmation
Recommended next mission
```

## Preserved Invariants

| Invariant | State |
| --- | --- |
| No student data unless explicitly approved | absolute |
| No real rosters / grades / behavior logs | blocked |
| No real student names | blocked |
| No runtime app execution | blocked |
| No integrations | blocked |
| No AI generation | blocked |
| Fake/local fixtures only | required |
| Planning-only until Owen approves implementation | required |

## Related

| Document | Role |
| --- | --- |
| `docs/classroom-utility-app-candidate-matrix.md` | Candidate prioritization |
| `docs/classroom-utility-templates/` | Per-app planning templates |
| `bin/chief-of-staff --classroom-utility-templates-status` | Lane closure proof |

## Non-Activation

`complete_classroom_utility_per_app_mission_templates` is a documentation closure marker only.
