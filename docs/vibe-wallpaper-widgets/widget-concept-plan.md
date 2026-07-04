# Widget Concept Plan

Last updated: 2026-07-04

```text
Status: planning-only
Widget install approval: none
```

## Purpose

This plan records useful widget concepts without creating, installing, syncing, or running widgets.

## Safe Concepts

- Chief of Staff status glance: read-only PASS/WARN/FAIL summary concept.
- Class period timer glance: concept only; Timer remains the only runtime-approved app and is not launched by this lane.
- Build queue card: current safe next mission and blocked gates.
- Approval queue card: Owen decisions needed before runtime/install work.
- Closeout card: end-of-day checklist concept with no automation.

## Safety Boundaries

Widget concepts do not approve widget files, install scripts, desktop placement, background jobs, LaunchAgents, or app wrappers. Fake concept cards must stay metadata-only.

## Chief Of Staff Verification

Chief of Staff may verify that concepts are documented and blocked. It must not install widgets, inspect macOS widget state, launch apps, use external services, or create runtime UI files.

## Future Gate

A widget implementation mission must be separately approved by Owen and must name the exact widget platform, exact install behavior, local files, rollback path, and proof that student data, integrations, and background automation remain blocked unless explicitly approved.
