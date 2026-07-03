# Classroom Utility — Student-Data Boundaries

Last updated: 2026-07-03

```text
Status: negative boundary documentation
Authority: absolute student-data prohibition unless explicit Owen mission
PASS on planning status does not lift these blocks
```

## Purpose

Define what counts as student data in classroom utility lanes and what fake/local planning fixtures may include.

## What Counts as Student Data (Blocked)

| Category | Examples | State |
| --- | --- | --- |
| Identifiers | Real student names, IDs, emails | blocked — absolute |
| Rosters | Class lists with real names | blocked |
| Grades | Scores, report card data | blocked |
| Behavior | Incident notes tied to real students | blocked |
| Accommodations | IEP/504 content, accommodation details | blocked |
| Work samples | Photos or text of student work | blocked |
| Parent contact | Phone, email, messaging content | blocked |
| Attendance / pass logs | Real hall-pass or attendance records | blocked |
| Seating tied to identity | Real name-to-seat assignments | blocked |
| Economy ledgers | Real coin/point balances per student | blocked — high scrutiny |

## Fake/Local Fixture Data Allowed

| Pattern | Example | Rule |
| --- | --- | --- |
| Generic labels | `example-student-a`, `example-team-red` | clearly fake |
| Seat labels | `example-seat-01` | no name mapping |
| Pass templates | `example-pass-template` | no real usage log |
| Reward placeholders | `example-reward-placeholder` | no real ledger |
| Job labels | `example-line-leader` | role label only |

Fixtures must include `fixture_classification: fake_local_planning_only` where JSON is used.

## Must Never Appear in Planning Fixtures

```text
real student names
real rosters
real grades
real behavior notes
real accommodations / IEP text
student work
parent contact info
live school IDs
Drive/Canvas/NAS/iCloud paths
URLs
API tokens / OAuth fields
generation prompts for execution
```

## Owen Approval Required

| Action | Gate |
| --- | --- |
| Any real student data in repo | explicit Owen mission + privacy review |
| Per-app implementation | separate mission per app |
| Integrations (Drive, Canvas, etc.) | separate integration missions |
| AI analysis of classroom behavior | blocked by default |

## What Remains Blocked

Runtime apps, real data storage, automation, network calls, and production registry mutation — even when planning templates exist.

## Orchestrated Boundary Proof

```bash
bin/chief-of-staff --classroom-utility-templates-status
bash tests/classroom-utility-templates-status-test.sh
```

## Non-Activation

Markdown boundary doc only. Does not implement runtime guards beyond repo status/test patterns.
