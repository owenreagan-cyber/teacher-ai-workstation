# Memory Log

Memory changes should be manually logged when meaningful memory files are edited.

Memory log entries help explain why the assistant's context changed over time.

## Template

### YYYY-MM-DD

- File changed:
- What changed:
- Reason:
- Triggered by: manual review / workflow run / feedback / roadmap update / correction
- Reviewed by:
- Notes:

## Entries

### YYYY-MM-DD: Phase 1D intake review queue added

- File changed: assistant/intake/* and assistant/memory/*
- What changed: Added intake review queue as the preferred review path before new material becomes memory.
- Reason: Prevent raw material from becoming memory or approved context without human review.
- Triggered by: Phase 1D implementation.
- Reviewed by: Owen
- Notes: Replace YYYY-MM-DD with the actual implementation date when this phase is run.

### Initial planning phase

- File changed: assistant/memory/*
- What changed: Created initial Phase 1C memory structure.
- Reason: Establish explicit Markdown memory before adding connectors, databases, or automatic indexing.
- Triggered by: Phase 1C implementation.
- Reviewed by: Owen
- Notes: Memory is manually editable and explicitly included only by CLI flags.
