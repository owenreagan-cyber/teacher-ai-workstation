# ADR-0004: Connector SDK Contract Instead of Hardcoded Connectors

**Status:** Accepted (M0 freeze)  
**Date:** 2026-07-04  
**Context:** Sources differ in APIs; catalog must stay agnostic.  
**Decision:** Frozen Connector SDK with discover/list/metadata/capabilities; normalized SourceItems.  
**Consequences:** No Drive/NAS logic in catalog core. M1 fixtures are not connectors.  
**Blocked runtime:** All connectors in M0/M1; OAuth; network.  
**Validation hooks:** `docs/teacher-knowledge-vault/connector-sdk-contract.md`
