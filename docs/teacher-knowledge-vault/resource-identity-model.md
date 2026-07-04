# Teacher Knowledge Vault — Resource Identity Model

Last updated: 2026-07-04

```text
Principle: A file is not the resource
```

## Core Entities

Resource, Representation, Source Item, Source, Version, Fingerprint, Relationship, Collection.

## Example (Fictional)

**Resource:** Math Lesson 21 Homework

**Representations:** Drive PDF, Canvas file, scanned copy, student-facing version, teacher-only answer key, AI-adapted version (all fictional fixtures).

## Policies

- Duplicates are **candidates** — not auto-merged
- Versions are **related** — not overwritten
- Teacher-only representations: restricted-indexable
- Student-facing: leakage checks required

Fixtures: `fake-resource-identity.json`, `fake-representation-source-map.json`, M1 `fake-resources.json` / `fake-representations.json`

ADR: `docs/adr/teacher-knowledge-vault/0005-resource-representation-source-identity.md`
