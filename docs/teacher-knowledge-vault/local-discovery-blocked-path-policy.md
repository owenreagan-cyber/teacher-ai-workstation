# Teacher Knowledge Vault — Local Discovery Blocked Path Policy

Last updated: 2026-07-04

```text
Status: policy documentation only
Applies to: future selected-folder discovery (not active)
```

## Absolute Exclusions

| Path class | Policy |
| --- | --- |
| `99_DO_NOT_SCAN/` | Non-discoverable, non-indexable, non-extractable |
| Student data folders | Rosters, grades, accommodations, IEPs, behavior logs — blocked |
| Answer keys/tests in student-facing mode | Blocked from student-facing discovery runs |
| Hidden system folders | Blocked or flagged |
| `.git/` | Blocked |
| `node_modules/` | Blocked |
| Application bundles (`.app`) | Blocked |
| Package/cache folders | Blocked |
| Backup/system folders | Blocked |

## Scope Exclusions (Never Approved by Default)

- All home-directory recursive scans
- All Google Drive root scans
- All iCloud root scans
- All NAS root scans
- All Canvas/Drive API scans
- Symlink targets outside approved root are blocked (`symlink_status: escape_blocked`)
- Cloud placeholder files not locally available
- Unknown external volumes unless explicitly approved

## `10_TEACHER_ONLY` Handling

`10_TEACHER_ONLY` may be **restricted-indexable** later under teacher-only guardrails. Discovery must:

- Label paths as `indexing_policy: restricted_indexable`
- Set `teacher_only_risk: elevated`
- Never treat as student-facing
- Route through restricted review

## `99_DO_NOT_SCAN` Handling

Discovery must emit `blocked_reason: do_not_scan_absolute_exclusion` and never create review queue items in normal review.

Fixture: `assistant/teacher-knowledge-vault/m2/fake-blocked-path-examples.json`
