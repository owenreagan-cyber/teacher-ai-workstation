# Candidate v0.2 Production Registry Path (Blocked Skeleton)

```text
Status: blocked_skeleton_only
Classification: manual-only candidate path — not production
Production writes: blocked
Real records: none
fake_fixture_only: N/A — directory is empty by design
```

## Purpose

Non-production path skeleton for a **future** Owen-approved production registry. Defines local-first directory shape only. No `registry.json`, no record files, no writer.

## Directory Shape

```text
candidate-v0-2-production/
  README.md                    (this file)
  BLOCKED-NO-WRITES.sentinel   (blocked-write marker)
  records/                     (empty — future manual-only records would live here after separate mission)
```

## Rules

- **Do not** add real curriculum metadata or source references here without an approved write mission
- **Do not** copy v0.2 fake fixtures into this path
- **Do not** remove `BLOCKED-NO-WRITES.sentinel` without Owen-approved production mission
- Dry-run candidates in `samples/registry-v0-2-dry-run/` must **not** auto-promote here
- v0 `registry/v0/registry.json` remains read-only fictional reference; canonical production authority is `registry/v0-2/production-registry.json` (one governed record)

## Owen Decisions Still Required

See `docs/curriculum-builder-production-registry-path-options.md` and Owen § J checklist items 1, 2, 10, 11.

## Status Proof

```bash
bin/chief-of-staff --curriculum-production-registry-governance-status
```

## Non-Activation

This skeleton does not activate writes, intake, or integrations.
