# Canvas LLM Approval and Export States

```text
Status: documentation/status only. This placeholder schema is inert planning text. It does not create runtime schema files, parsers, importers, loaders, validators, database tables, Canvas API clients, Google Drive clients, OAuth flows, network calls, automation, lesson generation, generated lesson drafts, generated review notes, or student-data handling.
```

## 1. Purpose

This document defines allowed placeholder state vocabulary for future Canvas LLM drafts. States are planning terms only. The repository does not move items through states and no workflow engine is added by this doc.

## 2. Approval States

| State | Meaning | Allowed During Foundation | Notes |
| --- | --- | --- | --- |
| `not_started` | Placeholder exists but no draft content exists. | Yes (vocabulary only) | Default starting state. |
| `drafted` | Future state only; a draft has been created locally. | Vocabulary only | No draft is created in this PR. |
| `needs_teacher_review` | Future local draft requires teacher review. | Vocabulary only | Teacher must review before export. |
| `teacher_revised` | Teacher has manually changed draft content. | Vocabulary only | May return to review. |
| `approved_for_export` | Teacher has approved for export (not publish). | Vocabulary only | Required before export. |
| `exported` | Content exported to local/manual package; not published to Canvas. | Vocabulary only | Export ≠ publish. |
| `blocked` | Item cannot proceed due to missing info or safety issue. | Vocabulary only | No automatic repair. |
| `rejected` | Teacher rejected the draft. | Vocabulary only | Must not proceed to export. |

During the current foundation, these are vocabulary terms only. The repo does not move items through states. No workflow engine is added.

## 3. Export States

| State | Meaning | Canvas Impact | Notes |
| --- | --- | --- | --- |
| `not_ready` | Export package cannot be built yet. | None | Default. |
| `draft_ready` | Draft exists but not yet review-ready. | None | Future local state only. |
| `review_ready` | Draft is ready for teacher review. | None | No Canvas API. |
| `approved` | Teacher approved content for export planning. | None | Not live approval on Canvas. |
| `export_ready` | Local export package may be assembled. | None | Still not published. |
| `exported` | Local/manual export package produced. | None | Does not mean published to Canvas. |
| `blocked` | Export blocked by safety or missing metadata. | None | No automatic fix. |
| `failed` | Export attempt failed in a future implementation. | None | Not active in foundation. |

`exported` does not mean published to Canvas. Export means local/manual export package only unless a future connector is explicitly approved.

## 4. Future Live Connector States

Future-only connector planning terms (not active):

| State | Meaning |
| --- | --- |
| `pending` | Connector job queued for future processing. |
| `validated` | Payload passed future validation checks. |
| `dry_run_complete` | Dry-run preview completed without mutation. |
| `approved_for_publish` | Teacher approved publish after dry-run. |
| `publishing` | Connector in progress (future only). |
| `published` | Live Canvas mutation completed (future only). |
| `publish_failed` | Publish attempt failed (future only). |
| `rollback_needed` | Rollback required after failed publish. |
| `rollback_complete` | Rollback completed successfully. |

These states are not active. They are future connector planning terms only. They cannot be used to imply current publish behavior.

## 5. Required State Transition Rules

### Allowed transitions (documented only; not enforced)

```text
not_started -> drafted
drafted -> needs_teacher_review
needs_teacher_review -> teacher_revised
needs_teacher_review -> approved_for_export
teacher_revised -> needs_teacher_review
teacher_revised -> approved_for_export
approved_for_export -> export_ready
export_ready -> exported
any review state -> blocked
any review state -> rejected
```

### Forbidden transitions (documented only; not enforced)

```text
not_started -> exported
drafted -> exported
needs_teacher_review -> exported
teacher_revised -> exported without approved_for_export
approved_for_export -> published
exported -> published
```

No current code enforces these rules. This PR only documents them. Enforcement would require a future approved implementation PR.

## 6. Human Approval Rule

No Canvas LLM draft may be exported without teacher approval.

No future live Canvas publishing may occur unless a separate future connector has:

- dry-run
- diff preview
- rollback/export manifest
- explicit teacher approval
- explicit network activation approval PR

## 7. Blocked and Rejected Handling

- **`blocked`** means missing information, safety concern, unsupported subject/resource, or unresolved placeholder. It does not trigger generation, publishing, or automatic repair.
- **`rejected`** means the teacher chose not to use the draft. It does not trigger generation, publishing, or automatic repair.

## 8. Relationship to Safety Contract

See `docs/canvas-llm-safety-and-approval-contract.md` for foundation prohibitions, approval gates, and human approval principles. This document extends the safety contract with export-state vocabulary and transition rules. Manual export package planning is in `docs/canvas-llm-manual-export-package-plan.md`. Manual export review checklists are in `docs/canvas-llm-manual-export-review-checklist.md`.

## 9. Non-Activation Boundary

This document does not implement a state machine. It does not add parsers, importers, loaders, runtime validators, databases, app code, Canvas integration, Drive integration, generation, or student data handling.

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
