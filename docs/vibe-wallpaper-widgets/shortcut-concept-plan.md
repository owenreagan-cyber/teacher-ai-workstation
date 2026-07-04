# Shortcut Concept Plan

Last updated: 2026-07-04

```text
Status: planning-only
Shortcut install approval: none
Shortcut execution approval: none
```

## Purpose

This plan lists helpful shortcut ideas while keeping Shortcuts installation and execution blocked.

## Safe Concepts

- Open Chief of Staff dashboard: concept card only.
- Show next safe mission: concept card only.
- Start classroom timer: blocked unless a later mission explicitly approves launch behavior.
- Switch teacher focus mode: blocked because it implies Mac/system mutation.
- Closeout checklist: concept card only; no automation.

## Safety Boundaries

Shortcut concepts must not include shortcut payloads, `.shortcut` files, AppleScript, shell commands, URL schemes, OAuth, API calls, or file paths outside the repo. No shortcut may be installed, run, exported, signed, or synced in this lane.

## Chief Of Staff Verification

Chief of Staff may verify the planning docs and fake examples. It must not invoke the Shortcuts CLI, run AppleScript, open apps, or change system state.

## Future Gate

Any future shortcut mission must be Owen-approved and must specify exact shortcut behavior, input/output, installation path, rollback, and test proof. Planning docs do not approve installation or execution.
