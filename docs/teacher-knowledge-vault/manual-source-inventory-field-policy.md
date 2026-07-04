# Teacher Knowledge Vault — Manual Source Inventory Field Policy

Last updated: 2026-07-04

```text
Status: allowed/blocked field policy — M7b fixtures only
```

## Allowed Fields

source labels, sanitized folder labels, sanitized display names, generic source role, approximate item type, fake/sanitized modified date, audience risk labels, indexing policy labels, review state, source reconciliation flags

## Blocked Fields

student names, rosters, grades, accommodations, IEP/504 data, behavior logs, real OAuth IDs, real Drive IDs, real Canvas IDs, private URLs, access tokens, raw full local paths with usernames, answer-key content, test questions, copied curriculum text, extracted document text, file contents, hidden/private folder names, secret project names unrelated to curriculum

## Policy

Manual inventory records must use placeholder URIs (`fake-manual://`, `fake-drive://`, `fake-canvas://`) and sanitized labels only. No secrets, tokens, or real external IDs.
