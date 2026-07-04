# ADR-0008: Document Understanding Escalation Ladder

**Status:** Accepted (M0 freeze)  
**Date:** 2026-07-04  
**Context:** OCR and cloud AI are expensive if applied broadly.  
**Decision:** Layer 0–5 escalation; cache by hash; no bulk background OCR; cloud requires cost gate.  
**Consequences:** Cost-minimizing pipeline. M0/M1 document only.  
**Blocked runtime:** OCR, AI, cloud API in M0/M1.  
**Validation hooks:** `docs/teacher-knowledge-vault/document-understanding-pipeline.md`
