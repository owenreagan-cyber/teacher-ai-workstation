# Widget and Shortcut Builder — Fake Catalog Index

Last updated: 2026-07-02

```text
Status: fake_fixture_only
Program: Widget and Shortcut Builder — Program F1
Classification: metadata-only catalog index — no install
```

## Purpose

Markdown index for the **fake widget/shortcut catalog** used by Program F1 planning foundations. This index documents catalog rows only; it does not install widgets, shortcuts, or automation.

## Canonical Fake Fixture

| Artifact | Path | Role |
| --- | --- | --- |
| Fake catalog JSON | `assistant/widget-shortcut/samples/fake-widget-shortcut-catalog.json` | Metadata-only widget/shortcut/quick-action rows |
| Status proof | `bin/chief-of-staff --widget-shortcut-status` | Read-only catalog foundation status |

## Catalog Summary (Fake Rows)

| Type | Count | Notes |
| --- | ---: | --- |
| Widgets | 2 | Chief of Staff Status, Local LLM Status — planning only |
| Shortcuts | 2 | Dashboard, Curriculum Registry status — no execution |
| Quick actions | 1 | Phase-1 proof concept — no automation |

## Safety Flags (All False / Blocked)

- `widget_install_allowed`: false
- `shortcut_install_allowed`: false
- `shortcut_execution_allowed`: false
- `mac_system_mutation_allowed`: false
- `network_calls_allowed`: false
- `student_data_allowed`: false

## Related Documents

| Document | Role |
| --- | --- |
| `docs/widget-shortcut-builder-catalog-foundation.md` | F1 closure index |
| `docs/widget-shortcut-builder-non-activation-boundaries.md` | Non-activation boundaries |
| `docs/mac-workstation-experience-foundation.md` | E1 cross-link |

## Non-Activation

No widget install, shortcut install, shortcut execution, AppleScript, Mac settings mutation, automation, network calls, student data, or real curriculum content.
