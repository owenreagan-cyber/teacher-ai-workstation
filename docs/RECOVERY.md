# Recovery Runbook: R1 Initialization Persistence Fix

## Scope

This recovery documents Phase R0/R1 stabilization for week-state initialization and persistence, without changing business-rule generation logic.

Targeted implementation surface:

- `.local/reference-apps/thales-academic-os-v2/apps/web/src/store.ts`
- `.local/reference-apps/thales-academic-os-v2/apps/web/src/test/initialization.test.ts`

## What was fixed

1. Added a characterization test to lock expected boot behavior:
   - Restore `lastSelectedWeek` on mount.
   - Preserve persisted `plannerData` on mount.
2. Replaced hardcoded startup overwrite behavior with a state-store flow:
   - Resolve `selectedWeek` from `localStorage.lastSelectedWeek` first.
   - Fallback to calendar-derived week only when no saved week exists.
3. Added explicit store lifecycle methods:
   - `persistState()` writes `selectedWeek` to `lastSelectedWeek`.
   - `loadState()` restores `selectedWeek` from `lastSelectedWeek`.
4. Wired persistence to `setWeek()` so week changes are immediately durable.
5. Wired `loadState()` during boot and rehydration.

## Rollback plan (if StateStore fails)

1. Revert the store persistence patch in `apps/web/src/store.ts`.
2. Keep characterization tests and run them to confirm baseline failure mode is reproduced.
3. Temporarily disable `loadState()` boot invocation and keep only read-only hydration.
4. Restore fallback-only initialization (`calendarService.getWeekId(initialContext)`) if boot is blocked.
5. Re-run initialization test suite and verify app can mount without state corruption.

## Operational notes

- This fix preserves existing generation/business engines.
- No Canvas deployment logic was changed.
- No Supabase function files were changed.
