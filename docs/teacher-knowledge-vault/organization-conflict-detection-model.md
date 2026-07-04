# Teacher Knowledge Vault — Organization Conflict Detection Model

Last updated: 2026-07-04

```text
Status: conflict policy — fake detections in M5 fixtures
```

## Conflict Types That Block or Require Manual Review

| Conflict | Effect |
| --- | --- |
| target filename already exists | no-overwrite block |
| target folder missing | manual review |
| destination under `99_DO_NOT_SCAN` | blocked |
| teacher-only into student-facing | leakage block |
| answer key/test into student-facing | leakage block |
| cloud placeholder/unavailable source | blocked |
| symlink escapes approved root | blocked |
| duplicate candidate unresolved | manual review |
| version candidate unresolved | manual review |
| canonical representation not selected | manual review |
| file changed since preview | re-preview required |
| source missing since preview | blocked |
| rollback unavailable | execution blocked |
| would overwrite existing file | no-overwrite block |
| crosses unapproved source boundary | blocked |
| touches Drive/NAS/Canvas without connector approval | blocked |

Fixture: `assistant/teacher-knowledge-vault/m5/fake-conflict-detections.json`
