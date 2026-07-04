# Teacher Knowledge Vault — Canvas Connector Approval Packet

Last updated: 2026-07-04

```text
Status: Canvas connector boundary — deployment target, not storage
runtime_implemented: false in M7
```

Canvas is deployment/publishing target and reconciliation source, not canonical storage.

## Future Read-Only Metadata (Level 2, Future Only)

May eventually list: course label, module label, page/assignment/file label, Canvas item type, updated timestamp, published/unpublished status, linked file placeholder, source relationship label.

## Blocked Without Separate Approval

OAuth/developer token setup, API calls, reading real courses, reading files/pages/assignments/quizzes/modules, reading student submissions, grades, rosters, analytics, discussions, messages, accommodations, IEP/504 data, writing/publishing/updating Canvas, downloading Canvas files, content extraction, student data.

M7 implements none of this.

Fixture: `assistant/teacher-knowledge-vault/m7/fake-canvas-metadata-records.json`
