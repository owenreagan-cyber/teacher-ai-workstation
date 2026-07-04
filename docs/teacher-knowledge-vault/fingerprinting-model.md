# Teacher Knowledge Vault — Fingerprinting Model

Last updated: 2026-07-04

## Fingerprint Types

Binary hash, normalized filename, text, page, image, structural metadata, semantic (future only — approval-gated).

## Staged Escalation

1. Exact hash → 2. Filename/path/metadata → 3. Native text → 4. OCR text → 5. Embeddings (future)

Fixture: `assistant/teacher-knowledge-vault/samples/fake-fingerprint-set.json`, M1 `fake-fingerprints.json`
