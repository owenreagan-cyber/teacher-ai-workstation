# Title Cleaner Validator Preview Spec

## Status

Preview-only validator spec.

## Purpose

The Title Cleaner Validator checks whether Phase 19D machine-readable title cleaner data is internally consistent and ready for future implementation planning.

It does not normalize live Canvas content.

It does not modify Canvas.

## Required Checks

The validator must check:

1. Required Phase 19D input files exist.
2. Required JSON files parse successfully.
3. `title-normalization-rules.json` declares preview-only behavior.
4. `never_silently_mutate_canvas` is true.
5. `ambiguous_input_requires_review` is true.
6. Canonical Math Test pattern exists: `SM5: Test {number}`.
7. Canonical Math Fact Test pattern exists: `SM5: Fact Test {number}`.
8. Canonical Math Study Guide pattern exists: `SM5: Study Guide {number}`.
9. Canonical ELA Test pattern exists: `ELA4: Test {number}`.
10. Canonical Reading Test pattern exists: `RM4: Test {number}`.
11. Canonical Spelling Test pattern exists: `RM4: Spelling Test {number}`.
12. Spelling rules do not output standalone `SP4:` or `SPELL4:` as canonical outputs.
13. Fixtures include close-input Math cases.
14. Fixtures include Spelling-to-RM4 cases.
15. Fixtures include ambiguous review-required cases.
16. All normalizer rules reference known rule IDs from `rules.json`.
17. All evidence references used by rules exist in `evidence.json`.
18. All link source/target IDs are resolvable.
19. No validator behavior authorizes Canvas writes.
20. No validator behavior reads raw `.local` metadata.

## Expected Result

The validator must emit PASS/WARN/FAIL lines.

Phase 19E should pass with:

```text
FAIL: 0
```

Warnings are allowed only for future implementation notes.

## Non-Goals

The validator does not:

- execute regex normalization
- edit Canvas objects
- read Canvas data
- fetch live data
- create assignments
- create pages
- create announcements
- move or rename files
- implement app UI
