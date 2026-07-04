# Teacher Knowledge Vault — UGREEN NAS Connector Approval Packet

Last updated: 2026-07-04

```text
Status: NAS connector boundary — fake metadata only; no mount/scan
runtime_implemented: false in M7
```

## Future Read-Only Metadata (Level 2, Future Only)

May eventually list: share label, folder label, display name, extension, size, modified time, source path label, availability status.

## Blocked Without Separate Approval

mounting NAS shares, scanning NAS root, writing to NAS, moving/renaming/deleting files, syncing to/from NAS, accessing private/non-curriculum shares, content extraction, student data.

M7 implements none of this.

Fixture: `assistant/teacher-knowledge-vault/m7/fake-nas-metadata-records.json`
