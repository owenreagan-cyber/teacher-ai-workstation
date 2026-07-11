# Phase 24 Predictive Teacher Brain

Status: local-first prediction engine and FPK rule layer.

Phase 24 predicts the next instructional week from owner-confirmed rules, current-year pacing entries, approved teacher corrections, and repeated FPK patterns. It remains preview-only and does not write to Canvas, send email, activate Google APIs, scan external storage, or resolve student data.

Primary entry points:

- `python3 scripts/canvas_llm_phase24/predict_week.py --week Q1W5 --input fixtures/canvas-llm/phase-24/predictive-teacher-brain.json --output <path>`
- `python3 scripts/canvas_llm_phase24/validate_prediction.py <predicted-week.json>`
- `bash tests/canvas-llm-phase-24-predictive-teacher-brain-test.sh`
