# Teacher Knowledge Vault — Version Candidate Model

Last updated: 2026-07-04

```text
Status: architecture model — M3 fake fixtures only
Overwrite: never automatic
```

## Version Candidate Scenarios

- Similar resource identity with different modified date or version label
- Same lesson/resource with updated file
- Same content with teacher-edited changes
- Canvas copy older/newer than Drive copy
- AI-generated revision related to original resource
- Student-facing version derived from teacher-only resource — must not leak restricted content

## Rules

- Versions are relationships, not overwrites
- Latest is **not** automatically canonical
- Canonical representation requires teacher approval
- Event log must preserve version decisions
- `auto_merge: false` and `requires_teacher_approval: true`

Fixture: `assistant/teacher-knowledge-vault/m3/fake-version-candidates.json`

Cross-reference: M1 `fake-relationships.json` (`version_candidate`)
