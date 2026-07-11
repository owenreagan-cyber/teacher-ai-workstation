# Phase 25 Curriculum Source Intelligence + Resource Resolver

Status: local-first resource identity and resolver layer.

Phase 25 consumes Phase 24 predictions, derives resource requirements, resolves approved curriculum resources from local registry metadata, and produces a preview-only packet that only carries verified resources into the Phase 23 handoff.

This phase does not call Canvas, send email, activate Google APIs, scan folders, use OCR, use embeddings, or rely on a vector database. The registry is deterministic and local-first, and unresolved resources stay in the review queue instead of being invented.

Primary entry points:

- `python3 scripts/canvas_llm_phase25/resolve_resources.py build-demo`
- `python3 scripts/canvas_llm_phase25/resolve_resources.py validate <packet.json>`
- `python3 scripts/canvas_llm_phase25/resolve_resources.py self-test`
- `bash tests/canvas-llm-phase-25-curriculum-source-intelligence-test.sh`
