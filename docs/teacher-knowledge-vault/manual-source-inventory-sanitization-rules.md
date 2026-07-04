# Teacher Knowledge Vault — Manual Source Inventory Sanitization Rules

Last updated: 2026-07-04

```text
Status: validation rules — repo fixtures only; no runtime scanning
```

## Sanitization Rules

- no real-looking Google Drive IDs
- no real-looking Canvas IDs
- no URLs except fake placeholders
- no local absolute paths with usernames
- no student-data field names or values
- no copied curriculum text
- no extracted text
- no answer-key/test content
- no OAuth/secrets/token strings
- `runtime_connected` must be false
- `runtime_ingested` must be false
- API/network metrics must remain zero
- manual records must preserve `10_TEACHER_ONLY` and `99_DO_NOT_SCAN` policies

Fixture: `assistant/teacher-knowledge-vault/m7b/fake-sanitization-results.json`
