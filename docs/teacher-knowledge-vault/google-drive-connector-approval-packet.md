# Teacher Knowledge Vault — Google Drive Connector Approval Packet

Last updated: 2026-07-04

```text
Status: Drive connector boundary — fake metadata only; no OAuth/API
runtime_implemented: false in M7
```

## Future Read-Only Metadata (Level 2, Future Only)

May eventually list: file ID placeholder, display name, MIME type, parent folder label, modified time, size, owner/shared status if safe, Drive path label if safe, shortcut/placeholder status.

## Blocked Without Separate Approval

OAuth, API calls, reading Drive files, scanning entire Drive root, downloading files, modifying Drive, moving/renaming/deleting Drive files, syncing folders, reading student data, reading private/non-curriculum areas, reading file contents.

M7 implements none of this; it only documents the future boundary and fake examples.

Fixture: `assistant/teacher-knowledge-vault/m7/fake-drive-metadata-records.json`
