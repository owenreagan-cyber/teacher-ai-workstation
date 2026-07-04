# ADR-0003: Local-First and Approval-Gated Processing

**Status:** Accepted (M0 freeze)  
**Date:** 2026-07-04  
**Context:** Processing can leak data, incur costs, or mutate files silently.  
**Decision:** Local-first where possible; approval-gated OCR, AI, cloud API, connectors, file ops. No background bulk jobs without mission approval.  
**Consequences:** Escalation ladder; auditable operations.  
**Blocked runtime:** Autonomous scanning, bulk OCR, default cloud AI.  
**Validation hooks:** `docs/teacher-knowledge-vault/document-understanding-pipeline.md`
