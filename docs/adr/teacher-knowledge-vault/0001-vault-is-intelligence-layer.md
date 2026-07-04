# ADR-0001: Teacher Knowledge Vault Is Intelligence Layer, Not File Storage

**Status:** Accepted (M0 freeze)  
**Date:** 2026-07-04  
**Context:** Curriculum assets scatter across Drive, NAS, Canvas, and local copies.  
**Decision:** Vault is metadata, identity, rule, search, governance, and review layer. Drive/NAS are canonical storage.  
**Consequences:** Catalog stores references, not file blobs. Mac local paths are staging only.  
**Blocked runtime:** Vault-as-file-server, canonical copy on Mac.  
**Validation hooks:** `docs/teacher-knowledge-vault/v1-architecture-spec.md`; `--teacher-knowledge-vault-m0-architecture-freeze-status`
