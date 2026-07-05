# Teacher Knowledge Vault — Runtime Manual Import Blockers

Last updated: 2026-07-04

```text
Status: hard blockers for future runtime import
Fixture: assistant/teacher-knowledge-vault/m7d/fake-import-blockers.json
```

## Hard Blockers

| Blocker | Description |
| --- | --- |
| Student data | Any student names, IDs, or student-facing sensitive content |
| Secrets/tokens/OAuth | access_token, refresh_token, api_key, oauth values |
| Real Drive/Canvas IDs | Unless explicitly approved in a later mission |
| Private URLs | http:// or https:// in inventory fields |
| Raw local paths | /Users/, /home/, C:\ with usernames |
| Copied curriculum text | Real lesson/worksheet content in repo |
| Extracted document text | OCR/extraction output fields |
| Answer-key/test content | In student-facing fields |
| `99_DO_NOT_SCAN` normal import | Must not map into searchable/indexable records |
| Import without preview | M7c import preview must precede any future write |
| Import without rollback plan | Rollback/removal plan required |
| Production catalog without approval | Canonical/production target requires separate gate |
| Connector output without connector approval | M7 connector runtime must be separately approved |
| Bundled organization | rename/move/copy/delete/archive combined with import |
| Network/API/OAuth required | Import must not require external access |
| File reads/scanning/OCR/AI | Content access blocked at import gate |

Blockers are enforced at the approval gate. M7d creates fake blocker examples only.
