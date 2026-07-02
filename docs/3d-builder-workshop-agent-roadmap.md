# 3D Builder Workshop Agent — Roadmap

Last updated: 2026-07-02

```text
Classification: 3D Builder Workshop Agent — Future / Approval-Gated
Program: J (see docs/master-build-roadmap.md)
Current status: planning only — not connected
Legacy parked-track name: 3D Design Factory Agent
Readiness stack: 3d-agent/ (policies, workflows, verification — groundwork only)
```

## Purpose

**3D Builder Workshop Agent** is a separate future agent/sub-agent for classroom object creation. It is **not** part of Curriculum Builder lesson generation and must not be treated as Canvas, lesson planning, or curriculum export work.

Chief of Staff coordinates and gates this agent but does **not** own the 3D asset library or directly generate 3D files.

## Role

Design, source, organize, test, and eventually produce classroom objects such as:

- toys and fidgets
- bulletin board decals and seasonal decorations
- teacher tools and desk organizers
- classroom management objects
- custom action figures / mascots (student-safe, non-copyright)
- rewards, tokens, badges
- curriculum manipulatives
- labels, signage, hallway display elements

## Core Subtracks

| Subtrack | Examples |
| --- | --- |
| Classroom Toys & Fidgets | desk pets, quiet fidgets |
| Bulletin Board Decals | letters, seasonal decorations |
| Teacher Tools | desk organizers, supply labels |
| Classroom Management Objects | behavior system pieces, economy tokens |
| Custom Action Figures / Mascots | classroom mascots (no copyrighted characters) |
| Rewards / Tokens / Badges | achievement badges, reading group tokens |
| Curriculum Manipulatives | math manipulatives, display objects |
| Desk / Label / Signage Tools | nameplates, hallway elements |

## Safety Boundaries

- No sharp objects.
- No weapon-like objects.
- No student-identifying objects without approval.
- No copyrighted character copies unless manually approved.
- No automatic slicing or printing at first.
- No live printer integration until a later hardware mission.
- No student data.
- No classroom deployment without teacher approval.
- No public publishing without explicit approval.

Advisory-only principle (from `3d-agent/README.md`): the agent may warn and classify; the **human operator** makes the final print decision.

## Chief of Staff Workflow (Future)

```text
idea intake
  → safety check
  → object category
  → design prompt
  → builder routing
  → print readiness checklist
  → teacher approval
```

## Possible Future Tools (Inactive)

- Tinkercad, Blender, Fusion 360
- Bambu Studio, OrcaSlicer
- MakerWorld / Printables references (manual only)
- Lovable for catalog UI (future; Program G1)
- Cursor for local registry/tools

Existing readiness: `docs/3d-printing-roadmap.md`, `3d-agent/`

## Builder Brain (Long-Term)

Improve over time in four areas — starting with **rules, metadata, scorecards, and local preference memory**, not custom model training:

1. Source finding
2. File/design creation
3. Testing, scoring, and library building
4. Feedback and preference learning

### Future Data Structures (Planning)

- `builder_preferences.json`
- `asset_index.json`
- `source_index.json`
- `quality_scores.json`
- `project_outcomes.json`
- `printability_scorecards.json`

### Source Scoring Criteria (Planning)

License clarity, remix allowed, commercial use, file type usefulness, model quality, printability, part count, color compatibility, AMS compatibility, community rating/downloads, source reputation, preview images, print profile availability, request match, ease of modification.

### Printability Tests (Planning)

Geometry validity, watertight/manifold status, scale/dimensions, build plate fit, thin walls, overhang risk, support risk, part count, color count, assembly complexity, file load success, preview render success, slicer import success (later).

## Blocked Until Explicit Approval

- web search, source downloads, scraping
- file generation, CAD generation, SVG generation
- Blender scripts, Meshy prompts
- STL export, 3MF export
- slicer integration, printer integration, automatic print jobs
- model training, fine-tuning
- APIs, OAuth, network calls
- student data, public publishing

## Future Chief of Staff Commands (Roadmap Only)

- `bin/chief-of-staff --3d-builder-status`
- `bin/chief-of-staff --3d-builder-intake-status`
- `bin/chief-of-staff --3d-builder-library-status`
- `bin/chief-of-staff --3d-builder-safety-status`
- `bin/chief-of-staff --3d-builder-roadmap-status`

Do not add active commands without an explicit implementation mission.

## Non-Activation

Planning documentation only. No 3D file generation, slicing, printing, automation, or student-data workflows.
