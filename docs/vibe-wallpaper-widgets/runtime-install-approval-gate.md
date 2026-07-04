# Runtime / Install Approval Gate

Last updated: 2026-07-04

```text
Status: active gate for this planning lane
Runtime approval: none
Install approval: none
Owen approval required: yes
```

## Gate Rules

- Planning docs do not approve widget installation.
- Wallpaper concepts do not approve changing wallpaper.
- Shortcut concepts do not approve installing or running shortcuts.
- Visual workshop concepts do not approve app execution.
- Fake examples do not approve production config.
- Chief of Staff may report status only.
- Owen must explicitly approve any future runtime/install mission.
- Each future mission must specify exactly what is approved.

## Still Blocked

- Mac system changes remain blocked.
- Widget and shortcut installation remain blocked.
- Homebrew installs remain blocked.
- App execution remains blocked.
- Executable UI pages/components remain blocked.
- External integrations remain blocked.
- AI generation/runtime behavior remains blocked.
- Local model/Ollama execution remains blocked.
- Production registry writes remain blocked.

## Required Future Approval Packet

A future packet must include:

- Exact artifact and path.
- Exact allowed action.
- Exact blocked actions.
- Rollback plan.
- Validation commands.
- Safety proof for student data, real curriculum content, integrations, AI runtime behavior, local models, and production writes.

Without that packet and Owen approval, the only valid state is planning/docs/status/tests.
