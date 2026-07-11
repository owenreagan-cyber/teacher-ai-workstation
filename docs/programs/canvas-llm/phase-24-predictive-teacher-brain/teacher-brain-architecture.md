# Teacher Brain Architecture

Phase 24 implements a deterministic, explainable Teacher Brain with a narrow local-first pipeline:

1. Load the sanitized pacing knowledge base and committed owner rules.
2. Apply the source hierarchy in order:
   - owner-confirmed hard rules
   - explicit current-year pacing-guide entry
   - approved teacher correction
   - repeated FPK pacing-guide pattern
   - predictive suggestion
   - unresolved
3. Predict instructional events with provenance, explanation, confidence, review state, and override state.
4. Persist only local correction memory under ignored `.local` paths.
5. Validate that the output remains preview-only and warning-safe.

Canvas is a deployment target, not the instructional source of truth. Prediction, validation, preview, and approval happen locally before any future write workflow.

Phase 24 does not activate:

- Canvas writes
- OAuth
- multi-tenancy
- Google APIs
- OCR
- embeddings
- vector databases
- external scanning
