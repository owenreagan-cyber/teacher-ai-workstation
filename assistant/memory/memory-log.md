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

### Initial planning phase

- File changed: assistant/memory/*
- What changed: Created initial Phase 1C memory structure.
- Reason: Establish explicit Markdown memory before adding connectors, databases, or automatic indexing.
- Triggered by: Phase 1C implementation.
- Reviewed by: Owen
- Notes: Memory is manually editable and explicitly included only by CLI flags.
