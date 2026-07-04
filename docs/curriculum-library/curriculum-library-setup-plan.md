# Curriculum Library Setup Plan

Last updated: 2026-07-04

```text
Status: planning-only — not implementation approval
Closure: complete_curriculum_library_setup_and_manual_registry_foundation
Local folder creation: blocked — future Owen-approved mission only
Real curriculum ingestion: blocked
Folder scanning/indexing: blocked
Network/API/OAuth: blocked
Student data: blocked — absolute
Proof: bin/chief-of-staff --curriculum-library-foundation-status
```

## Purpose

Plan a **local-first Curriculum Library** on Owen's workstation: folder taxonomy, manual registry, Canvas-ready definitions, and file-classification approval gates — **without creating real folders**, scanning files, or activating Drive/NAS/iCloud/Canvas integrations.

This plan extends `docs/curriculum-library-v1-foundation.md` with setup and manual-registry planning artifacts.

## Relationship to Existing Foundation

| Layer | Document / artifact | Role |
| --- | --- | --- |
| v1 foundation closure | `docs/curriculum-library-v1-foundation.md` | Reference schema v0, storage strategy cross-links |
| Setup plan (this doc) | `docs/curriculum-library/curriculum-library-setup-plan.md` | Owen-facing setup sequence and mission boundaries |
| Manual registry | `docs/curriculum-library/manual-registry-plan.md` | CSV/manual entry planning |
| Folder taxonomy | `docs/curriculum-library/folder-taxonomy.md` | Planned directory layout (not created yet) |
| Canvas-ready folders | `docs/curriculum-library/canvas-ready-folder-definition.md` | Export/staging folder rules |
| Classification gate | `docs/curriculum-library/file-classification-approval-gate.md` | Human approval before any classification runtime |

## Planned Local Root (Not Created Yet)

Future Owen-approved mission may create:

```text
~/TeacherAI-Curriculum-Library/
```

**This mission does not create that path.** No `mkdir`, no home-directory writes, no folder bootstrap script.

## Setup Sequence (Planning Only)

1. Owen reviews folder taxonomy and Canvas-ready definitions.
2. Owen reviews manual registry CSV columns and fake sample rows.
3. Owen reviews file-classification approval gate before any auto-suggest runtime.
4. Future mission: Owen-approved local folder creation script creates `~/TeacherAI-Curriculum-Library/` skeleton only.
5. Future mission: manual registry entry workflow (still no scanning).

## Fake / Local Fixtures

| Fixture | Path |
| --- | --- |
| Folder tree (fictional) | `assistant/curriculum-library/samples/fake-folder-tree.json` |
| Manual registry CSV (fictional) | `assistant/curriculum-library/samples/fake-manual-registry.csv` |
| Classification suggestion (fictional) | `assistant/curriculum-library/samples/fake-classification-suggestion.json` |

All fixtures use `fake_local_planning_only` classification. No real paths, no real curriculum content.

## Blocked Until Separate Approval

```text
~/TeacherAI-Curriculum-Library/ creation on disk
folder scanning / crawling / indexing / OCR
embeddings / RAG / AI classification of real files
Drive / NAS / iCloud / Canvas API or OAuth
automatic source resolution
student data / rosters / grades
production registry writes / active --write
```

## Proof

```bash
bin/chief-of-staff --curriculum-library-foundation-status
bash tests/curriculum-library-foundation-status-test.sh
```

## Non-Activation

Documentation, fake fixtures, and read-only status only. PASS does not create folders or activate integrations.
