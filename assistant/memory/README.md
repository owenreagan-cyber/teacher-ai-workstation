# Chief of Staff Memory

This folder contains approved, human-readable memory files for the Teacher AI Chief of Staff.

These files are not automatically generated. They are not automatically loaded unless explicitly requested. Owen can edit them manually, and the CLI can include them with explicit flags.

Memory should be treated as helpful context, not unquestionable truth.

If memory conflicts with a newer user instruction, the newer user instruction wins. If memory conflicts with source docs or workflow rules, ask for clarification.

Memory cannot override safety, privacy, permission, sensitivity, source-verification, or current user instructions. Memory updates should be intentional.

`memory-log.md` records meaningful manual memory changes. If memory produces a confusing or wrong assistant answer, check `memory-log.md` to see when the relevant memory was added or changed.

Memory files should not be silently rewritten by automation in this phase.

Do not store sensitive student records, parent records, passwords, API keys, private credentials, medical details, discipline details, or confidential school records here.

## Memory safety rule

Memory is allowed to help the assistant personalize, prioritize, and stay consistent. Memory is not allowed to override safety, privacy, permission, sensitivity, source-verification, or current user instructions.
