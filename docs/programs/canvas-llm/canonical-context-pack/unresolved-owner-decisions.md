# Unresolved Owner Decisions

Highest authority for resolved 2026–2027 rules:

```text
docs/programs/canvas-llm/2026-2027-fpk-canvas-operating-contract.md
```

The following items remain genuinely unresolved.

## Spelling Test 25

Current canonical data contains Tests 1–24.

Decision/evidence required:

- exact Test 25 word list;
- exact focus words or focus-word rule;
- capitalization and punctuation;
- confirmation that Test 25 belongs to the 2026–2027 sequence.

Do not generate or validate Test 25 until the exact source is approved.

## Live Canvas assignment-group IDs

Numeric assignment-group IDs must be resolved from teacher-initiated read-only Canvas metadata.

The system must not:

- hardcode production IDs in repo config;
- guess IDs from archived years;
- treat logical group names as sufficient without live verification.

## Live Canvas module IDs

Numeric module IDs and module item IDs require the same live-read boundary.

Logical module names may be committed; numeric IDs must be verified before publication.

## Live Canvas metadata dependencies

Before any future approved write, the system should verify:

- course exists and matches expected subject/year;
- current assignment-group membership;
- current module placement;
- current page and assignment URLs when referenced.

A mismatch blocks publication.
