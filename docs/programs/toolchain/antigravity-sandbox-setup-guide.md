# Antigravity Sandbox Setup Guide

Status: documentation/status only.

This guide describes a future disposable sandbox evaluation path. It does not authorize installing Antigravity, running `agy`, running `agy init`, running `agy migrate`, creating active `.antigravity` config in the primary repo, or activating runtime agent behavior.

## Required disposable sandbox steps

1. Create a disposable clone outside the primary repo.
2. Immediately remove origin in the sandbox before evaluation.
3. Create `SANDBOX_ONLY_DO_NOT_MERGE.md` at sandbox root.
4. Create `VALIDATION_JOURNAL.md` at sandbox root from `docs/programs/toolchain/antigravity-validation-journal-template.md`.
5. Confirm no credentials, secrets, Canvas API/OAuth, Drive/NAS/iCloud, Supabase/Firebase, student data, production writes, or real curriculum ingestion are available.
6. Keep all observations in `VALIDATION_JOURNAL.md`.
7. Do not merge the sandbox branch into main.
8. If any output is valuable, manually copy only the reviewed changes into a normal primary-repo branch.

## Required sentinel text

`SANDBOX_ONLY_DO_NOT_MERGE.md` must say that the clone is disposable, has no origin, has no credentials, and cannot be merged directly into the primary repo.

## Stop conditions

Stop immediately if evaluation would require credentials, Canvas API/OAuth/live reads/writes, Drive/NAS/iCloud, Supabase/Firebase, student data, active writes, production data, local model probing, Mac system changes, runtime agent behavior, or direct sandbox-to-main merge.
