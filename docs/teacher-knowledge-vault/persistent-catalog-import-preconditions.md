# Persistent Catalog Import Preconditions (Future)

Last updated: 2026-07-05

Required preconditions before any **future** persistent catalog write (M7g or later). M7f does not execute import.

## Owen and mission gates

- Owen explicitly approves a separate runtime mission.
- Target catalog path is fixed, documented, and reviewed.
- Target catalog is local and not in synced/curriculum folders unless separately approved.

## Safety and evidence gates

- Backup/export plan exists and is reviewed before write.
- Rollback/removal plan exists.
- M7c fixture validator passes on committed fixtures.
- M7d approval packet requirements satisfied (fake evidence in M7f fixtures).
- M7e disposable test catalog import proof passes (bounded `.tmp/` path only).
- Input source is committed fake/sanitized fixture or separately approved sanitized manual inventory.
- No arbitrary external path input.
- No student data, secrets, tokens, or private URLs.
- No real Drive/Canvas IDs unless separately approved.
- No content reads, extraction/OCR/AI, or organization bundled with import.
- `99_DO_NOT_SCAN` remains blocked/non-indexable.
- Teacher-only remains restricted-indexable.

See `assistant/teacher-knowledge-vault/m7f/fake-persistent-catalog-approval-packet.json`.
