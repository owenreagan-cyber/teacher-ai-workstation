# Intake Review Queue

The intake folder is for candidate material that may become approved Chief of Staff context later.

Intake is a review queue, not automatic memory. Raw material is not approved context, is not automatically loaded by the CLI, and must be reviewed by Owen before promotion.

Approved material can be summarized into `approved-context.md`, approved writing samples, memory files, or workflow docs. Rejected material should be documented without being used as context. Quarantined material is material that appears sensitive, private, unsafe, unclear, or not ready for use.

The assistant may recommend classifications, but Owen makes the final decision.

## Required Rule

Nothing in `assistant/intake/raw/`, `assistant/intake/quarantine-files/`, `assistant/intake/approved-files/`, or `assistant/intake/rejected-context.md` should be automatically included in model context.

## approved-context.md vs approved-files/

- `approved-context.md` is for Markdown summaries of reviewed and approved material.
- `approved-files/` is for actual reviewed files, such as PDFs, docs, exports, or artifacts.
- The CLI reads `approved-context.md` only when explicitly requested.
- The CLI never reads `approved-files/` automatically.
- In Phase 1D, use sanitized Markdown summaries instead of passing `approved-files/` with `--context`.
- A later reviewed-file workflow can add explicit file use if Owen approves it.
- `approved-files/` is ignored by Git except for `.gitkeep` to prevent accidental commits of real files.
