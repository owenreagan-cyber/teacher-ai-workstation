# Teacher Knowledge Vault — Search Result Safety Modes

Last updated: 2026-07-04

```text
Status: filtering policy — fake mode examples in M3 fixtures
```

## Search Modes

| Mode | Purpose |
| --- | --- |
| **teacher_planning** | Full teacher workspace — may show restricted flags |
| **student_facing** | Student-safe results only |
| **canvas_facing** | Defaults to student-facing restrictions |
| **assessment_validation** | Alignment/leakage checks — no answer content exposure |
| **admin_governance** | Blocked counts and status — not protected content |

## Filtering Rules

### Teacher Planning Mode

- May show teacher-only metadata and `restricted_indexable` flags
- May surface duplicate/version candidates requiring review
- Must still exclude `99_DO_NOT_SCAN`

### Student-Facing Mode

- Must hide teacher-only answer keys, tests, manuals
- Must apply `student_mode_leakage_filter`
- Must block assessment/answer-key representations

### Canvas-Facing Mode

- Defaults to student-facing restrictions unless explicitly teacher-only publish workflow
- Canvas-only resources flagged for reconciliation review

### Assessment Validation Mode

- May use teacher-only metadata for alignment checks
- Must not expose answer content in results

### Admin/Governance Mode

- May show blocked counts, approval-required actions, reconciliation flags
- Must not expose protected `99_DO_NOT_SCAN` content

Fixture: `assistant/teacher-knowledge-vault/m3/fake-search-results-by-mode.json`
