# Operations

Commands, workflows, and local-path conventions for the FPK Canvas Builder.

```text
Status: active governance (read-only / documentation + config consolidation)
```

## Credentials

- Location: `~/.config/teacher-ai-workstation/canvas.env` (mode 0600)
- Loaded env-first by `scripts/canvas_llm_phase22/canvas_credentials.py`
- Never print the token; never persist it into repo files

## Launch wrapper

```bash
bin/canvas-launch
```

Delegates to `scripts/canvas_llm_phase22/canvas_launcher.py`. The wrapper never handles or prints the token.

## Validation stack

```bash
bash -n bin/canvas-launch
python3 -m json.tool config/fpk/identity.json
python3 -m json.tool config/fpk/pacing-source.json
python3 -m json.tool config/fpk/canvas-courses.json
python3 -m json.tool config/fpk/communication-policy.json
python3 -m json.tool config/fpk/rule-authority.json
python3 -m json.tool config/fpk/weekly-lifecycle.json
python3 -m json.tool config/fpk/learning-layer.schema.json
python3 -m json.tool config/fpk/live-canvas-behavior.json
```

Existing Canvas validators (read-only):

```bash
bin/chief-of-staff --canvas-llm-canonical-context-pack-status
```

See `docs/programs/canvas-llm/canonical-context-pack/context-pack-manifest.json` for the canonical status command.

## Local paths (gitignored)

| Path | Purpose |
| --- | --- |
| `.local/canvas-llm/` | Canvas staging output, raw snapshots, fetched metadata |
| `.local/learning/` | Future local-LLM learning layer (schema in `config/fpk/learning-layer.schema.json`) |

Raw/live Canvas snapshots and fetched metadata stay local and gitignored per repo policy. Never track credentials or token files.

## Local learning layer

Intended local path: `.local/learning/`

```text
teacher-corrections.jsonl
approved-language.jsonl
artifact-precedent.jsonl
promoted-rules.json
rejected-suggestions.jsonl
```

Schema only in this phase. No embeddings, vector DB, or fine-tuning. See `config/fpk/learning-layer.schema.json`.

## Read-only guarantee (live Canvas)

Any exploration script must allow GET only and forbid POST/PUT/PATCH/DELETE, never print `CANVAS_API_TOKEN`, and never persist the token into repo files.

Phase 2 GET-only sweep completed (2026-10-11). Reusable read-only sweep tool: `scripts/canvas-llm/phase2_live_sweep.py` (static GET-only scan + normalized output under `.local/canvas-llm/phase2-live-sweep/`). The detailed plan is `docs/programs/canvas-llm/canvas-get-only-sweep-plan.md`.

## Live-read canonical facts

- Assignment-group IDs + agenda-module IDs: `config/fpk/canvas-courses.json`
- Placement / observer / conversation capability: `config/fpk/live-canvas-behavior.json`

Both are `LIVE_CANVAS_PRECEDENT` (verified by GET), not `OWNER_POLICY`.

## Guarded live deployment pattern

Proven workflow for updating an existing rolling page (Homeroom or subject) in place:

```text
SOURCE CONTENT  (owner-approved)
+ THEME         (approved/candidate)
+ COMPATIBILITY CONTRACT
        ↓
ASSEMBLED PREVIEW  (local, gitignored)
        ↓
VALIDATION  (content checklist, UTF-8/mojibake, privacy, Canvas-safe HTML)
        ↓
BACKUP  (GET current body → .local, before any write)
        ↓
EXISTING PAGE UPDATE ONLY  (PUT; never POST a replacement page)
        ↓
READBACK VERIFICATION  (GET + checklist)
```

Required guards:

- verify page identity (`page_id` + slug) before write
- preserve slug and title
- preserve `front_page` status
- preserve `published` state
- backup the current body locally before any write
- verify via GET readback after every write

Never:

- create replacement pages for existing rolling pages
- deploy unverified assembled content

## Canvas readback normalization (not corruption)

- Canvas prepends `<link rel="stylesheet" ... canvas_global_app.css>` and appends
  `<script ... canvas_global_app.js>` around submitted page bodies. These are
  platform wrappers, not generated content; validators must ignore them.
- Canvas may normalize HTML entities — e.g. `Water Bottles & Drinks` reads back
  as `Water Bottles &amp; Drinks`. This renders identically; do not treat normal
  HTML escaping as corruption.
