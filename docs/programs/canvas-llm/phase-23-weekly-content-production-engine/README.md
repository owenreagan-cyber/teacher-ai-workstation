# Phase 23 Weekly Content Production Engine

Status: local-first weekly production packet engine.

Phase 23 takes one canonical instructional week and builds a preview-only weekly production packet with:

- Canvas weekly page drafts
- linked assignment drafts
- approved resource matches
- assessment reminders
- Canvas-style HTML previews
- text previews
- validation, provenance, privacy, and risk output

The engine reuses Phase 22 canonical curriculum helpers, then layers packet assembly and packet validation on top. It does not write to Canvas, publish content, send email, or track `.local/...` artifacts.

Primary entry points:

- `python3 scripts/canvas_llm_phase23/phase23_content_engine.py build-demo`
- `python3 scripts/canvas_llm_phase23/phase23_content_engine.py serve --host 127.0.0.1 --port 8775`
- `python3 scripts/canvas_llm_phase23/phase23_content_engine.py validate <packet.json>`
- `bash tests/canvas-llm-phase-23-weekly-content-production-engine-test.sh`

