# Charades Game — Planning Lane

Last updated: 2026-07-04

```text
Status: planning-only — not implementation approval
Closure: complete_charades_game_planning_lane
Classification: Tier 2 app planning lane
Inventory row: 30
Category: arcade / game module
Runtime classroom app: blocked
Student data: blocked — absolute
Database/API/integration: blocked
AI generation / local models: blocked
```

## Purpose

Plan charades prompt cards with generic action labels.

**Planning lane only. Runtime implementation is not approved.**

## Teacher Workflow (Planned)

1. Owen opens future utility on classroom display or teacher device (**not built**).
2. Select mode or preset from fake/local labels only.
3. Run activity using display labels — no student roster binding.
4. End session; **no log retained** by default.

## Classroom Use Cases

- Smartboard or projector display for whole-class activities.
- Teacher-only control; aggregate or generic labels only.
- Offline/local future posture — no network required.

## Display / Interaction Modes (Non-Runtime)

• Prompt card labels
• Category placeholders
• Timer display concept (labels only)

## Fake / Local Examples

See `assistant/classroom-utilities/samples/charades-game-planning/`. Fixtures are `fake_local_planning_only`.

Primary fixture label: `example-charades-prompt-label`

## Text-Only Wireframe (Concept)

```text
+------------------------------------------+
|  Charades Game          [ mode selector ]       |
|                                          |
|         ( main display label area )      |
|                                          |
|  [ teacher control — start / reset ]     |
+------------------------------------------+
No student names. No persistence.
```

## Blocked Capabilities

```text
runtime app / HTML / JS / React
student data / rosters / grades / behavior logs
database / API / OAuth / network
Drive / NAS / iCloud / Canvas
real curriculum content / AI generation / Ollama
audio / animation runtime / widgets / shortcuts
```

## Future Implementation Approval Path

Separate explicit Owen runtime mission required. Cite this doc and `bin/chief-of-staff --app-ecosystem-planning-lanes-status` PASS.

## Non-Activation

`complete_charades_game_planning_lane` is documentation only. No runtime authorized.

