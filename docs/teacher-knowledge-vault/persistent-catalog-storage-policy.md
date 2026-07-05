# Persistent Catalog Storage Policy (Future Requirements)

Last updated: 2026-07-05

**M7f documents future requirements only.** No persistent catalog path or database is created in M7f.

## Future local-first rules

A future persistent local working catalog must:

- remain local-first on Owen's workstation
- not live inside Google Drive, iCloud, or NAS synced folders by default
- not live in curriculum source folders
- not use `~/TeacherAI-Curriculum-Library/` until explicitly approved in a separate mission
- use a clearly named app data/cache location or repo-local generated path during early phases
- be clearly separated from:

  - disposable test catalog (M7e: `.tmp/teacher-knowledge-vault/m7e/`)
  - persistent local working catalog (future M7g candidate path — not created in M7f)
  - future production/canonical catalog

## Lifecycle requirements (future)

Before first persistent write, a future mission must document:

- fixed reviewed target path (no arbitrary user input)
- backup/export plan before first write
- import batch model with batch IDs
- rollback/removal plan for imported batches
- corruption recovery plan
- schema versioning / migrations policy

M7f creates fake review examples only under `assistant/teacher-knowledge-vault/m7f/`.
