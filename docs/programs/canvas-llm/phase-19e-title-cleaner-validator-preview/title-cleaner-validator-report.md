# Title Cleaner Validator Preview Report

## Status

Generated preview report.

## Command

```bash
scripts/canvas-llm-phase-19e-title-cleaner-validator-preview.py
```

## Result

```text
Canvas LLM Phase 19E Title Cleaner Validator Preview
----------------------------------------------------
PASS: Phase 19D evidence.json exists
PASS: Phase 19D rules.json exists
PASS: Phase 19D links.json exists
PASS: Phase 19D title-normalization-rules.json exists
PASS: Phase 19D title-normalization-fixtures.md exists
PASS: evidence.json parses
PASS: rules.json parses
PASS: links.json parses
PASS: title-normalization-rules.json parses
PASS: normalization status is preview_only
PASS: never_silently_mutate_canvas is true
PASS: ambiguous_input_requires_review is true
PASS: canonical pattern present: ELA4: Test {number}
PASS: canonical pattern present: RM4: Spelling Test {number}
PASS: canonical pattern present: RM4: Test {number}
PASS: canonical pattern present: SM5: Fact Test {number}
PASS: canonical pattern present: SM5: Study Guide {number}
PASS: canonical pattern present: SM5: Test {number}
PASS: Spelling canonical outputs do not use SP4 or SPELL4
PASS: fixture includes SM5 Test close input
PASS: fixture includes spaced SM5 close input
PASS: fixture includes Math Fact Test close input
PASS: fixture includes Math Study Guide close input
PASS: fixture includes ELA Test close input
PASS: fixture includes Reading Test close input
PASS: fixture includes Spelling Test close input
PASS: fixture includes SP4 Spelling correction input
PASS: fixture includes ambiguous Test input
PASS: fixture includes needs_review confidence
PASS: NORM-CANVAS-MATH-TEST-001 references known rule RULE-CANVAS-TITLE-MATH-TEST-001
PASS: NORM-CANVAS-MATH-FACT-TEST-001 references known rule RULE-CANVAS-TITLE-MATH-FACT-TEST-001
PASS: NORM-CANVAS-MATH-STUDY-GUIDE-001 references known rule RULE-CANVAS-TITLE-MATH-STUDY-GUIDE-001
PASS: NORM-CANVAS-ELA-TEST-001 references known rule RULE-CANVAS-PREFIX-ELA-001
PASS: NORM-CANVAS-READING-TEST-001 references known rule RULE-CANVAS-PREFIX-READING-001
PASS: NORM-CANVAS-SPELLING-TEST-001 references known rule RULE-CANVAS-PREFIX-SPELLING-001
PASS: RULE-CANVAS-PREFIX-MATH-001 evidence ref exists: EV-CANVAS-0001
PASS: RULE-CANVAS-PREFIX-READING-001 evidence ref exists: EV-CANVAS-0002
PASS: RULE-CANVAS-PREFIX-SPELLING-001 evidence ref exists: EV-CANVAS-0002
PASS: RULE-CANVAS-PREFIX-ELA-001 evidence ref exists: EV-CANVAS-0003
PASS: RULE-CANVAS-TITLE-MATH-TEST-001 evidence ref exists: EV-CANVAS-0004
PASS: RULE-CANVAS-TITLE-MATH-FACT-TEST-001 evidence ref exists: EV-CANVAS-0004
PASS: RULE-CANVAS-TITLE-MATH-STUDY-GUIDE-001 evidence ref exists: EV-CANVAS-0004
PASS: RULE-CANVAS-GRADING-MATH-STUDY-GUIDE-001 evidence ref exists: EV-CANVAS-0005
PASS: RULE-CANVAS-NORMALIZER-TITLE-001 evidence ref exists: EV-CANVAS-0006
PASS: LINK-CANVAS-0001 has stable link ID
PASS: LINK-CANVAS-0001 source ID resolves
PASS: LINK-CANVAS-0001 target ID resolves
PASS: LINK-CANVAS-0002 has stable link ID
PASS: LINK-CANVAS-0002 source ID resolves
PASS: LINK-CANVAS-0002 target ID resolves
PASS: LINK-CANVAS-0003 has stable link ID
PASS: LINK-CANVAS-0003 source ID resolves
PASS: LINK-CANVAS-0003 target ID resolves
PASS: LINK-CANVAS-0004 has stable link ID
PASS: LINK-CANVAS-0004 source ID resolves
PASS: LINK-CANVAS-0004 target ID resolves
PASS: LINK-CANVAS-0005 has stable link ID
PASS: LINK-CANVAS-0005 source ID resolves
PASS: LINK-CANVAS-0005 target ID resolves
PASS: LINK-CANVAS-0006 has stable link ID
PASS: LINK-CANVAS-0006 source ID resolves
PASS: LINK-CANVAS-0006 target ID resolves
PASS: LINK-CANVAS-0007 has stable link ID
PASS: LINK-CANVAS-0007 source ID resolves
PASS: LINK-CANVAS-0007 target ID resolves
PASS: normalizer blocks canvas_write
PASS: normalizer blocks student_data_access
PASS: Phase 19E boundary blocks Canvas API calls
PASS: Phase 19E boundary blocks Canvas writes
PASS: Phase 19E boundary blocks student data access
PASS: Phase 19E boundary blocks raw `.local` metadata reads or commits
PASS: Phase 19E boundary blocks school Canvas URL commits
PASS: validator is local preview-only
PASS: validator does not call Canvas APIs
PASS: validator does not fetch live Canvas data
PASS: validator does not write to Canvas
PASS: validator does not access student data
PASS: validator does not read raw .local metadata
PASS: validator does not implement app behavior

Summary
-------
PASS: 79
WARN: 0
FAIL: 0
```

## Interpretation

The Phase 19D seed rule catalog and title cleaner preview data are machine-checkable.

This report does not authorize Canvas writes or implementation.
