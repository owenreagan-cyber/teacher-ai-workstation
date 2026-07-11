# Phase 22 Predictive Weekly Planning Workstation

Durable local-first SQLite workstation for startup/week selection, yearly pacing import/review, weekly plans, guided builder, resource registry, editable draft generation, revision restore, backup/export, daily brief, and preview-only scheduling/deployment.

Architecture: Python standard-library HTTP server, JSON API, SQLite WAL migrations, static frontend. Default DB: `.local/canvas-llm/phase-22-predictive-weekly-planning/workstation.sqlite3`; override with `--db` or `PHASE22_DB_PATH`.

Canonical sources: committed curriculum maps and Phase 22 owner rules. Autosave uses 700 ms debounced PATCH, blur/visibility saves, retries, and conflict indicators. Resolvers cover Math, Fact Test, Reading, Spelling, and course mapping safety. Resources follow Teacher Knowledge Vault metadata foundations with audience, sensitivity, verification, SHA-256, local path, and Canvas reference metadata.

Drafts are local and editable: agenda pages, Math assessment families, Reading/Spelling combined agenda content, Language Arts assignments, announcements, newsletter, daily teacher brief, and deployment preview. History and Science do not generate assignments.

Safety: no Canvas writes, no email sends, no fake links, no tracked `.local` artifacts. Unresolved: Canvas due time only. Reading Test 14 has no Checkout.

Commands: `python3 scripts/canvas_llm_phase22/phase22_workstation.py init-db`, `python3 scripts/canvas_llm_phase22/phase22_workstation.py serve --host 127.0.0.1 --port 8765`, `bash tests/canvas-llm-phase-22-predictive-weekly-planning-workstation-test.sh`.
