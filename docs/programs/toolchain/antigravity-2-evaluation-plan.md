# Antigravity 2.0 Evaluation Plan

Status: documentation/status only.

## Classification

Antigravity 2.0 is classified as [CANDIDATE], [SANDBOX-ONLY], [BLOCKED-IN-PRIMARY], and [MANUAL-COPY-ONLY].

This plan does not authorize install or execution. It does not authorize `agy`, `agy init`, `agy migrate`, active `.antigravity` config, Mac system changes, network/API/OAuth integrations, runtime agent behavior, local model probing, or production writes.

## Mission

Evaluate whether Antigravity 2.0 could ever assist repo engineering without weakening local-first boundaries, student-data protections, Canvas safety, or Chief of Staff read-only status semantics.

## Evaluation questions

1. Can Antigravity operate in a disposable clone with no credentials and no upstream remote?
2. Can it be constrained to repo-local docs/status edits only?
3. Does it create hidden config, background processes, agent execution state, or migration files?
4. Can outputs be reviewed as plain diffs and manually copied into the primary repo without direct merge?
5. Does it preserve PASS/WARN/FAIL status semantics and never reinterpret a passing status as runtime authorization?

## Required evidence from a future sandbox

- A `SANDBOX_ONLY_DO_NOT_MERGE.md` sentinel at sandbox root.
- A `VALIDATION_JOURNAL.md` filled from the approved template.
- Proof that `origin` was removed before any evaluation.
- Proof that credentials, Canvas API/OAuth/live reads/writes, Drive/NAS/iCloud, Supabase/Firebase, network integrations, production writes, and student data were not used.
- Diff review notes showing any useful result can be manually copied only.

## Primary repo rule

The primary repo remains blocked for Antigravity activation. No active setup may be performed here.
