# Selected Local Folder Path Policy

Last updated: 2026-07-05

**M2c documents future requirements only.** No real folder path is scanned in M2c.

## Allowed only in future M2d (explicit Owen approval)

- one tiny Owen-selected local test folder
- non-synced local folder preferred
- controlled test folder created specifically for metadata-only trials
- metadata-only stat discovery
- no recursive deep scan by default
- no content reads, OCR, AI, or organization operations

## Blocked by default

| Class | Examples |
| --- | --- |
| User home areas | home directory, Desktop, Documents, Downloads |
| Cloud/sync | Google Drive, iCloud Drive, NAS mounts |
| External/school | Canvas exports, school shared drives, external drives |
| Curriculum | whole curriculum library, broad curriculum roots |
| Sensitive | student-data-likely folders, secrets, answer keys without teacher-only policy |
| Policy | `99_DO_NOT_SCAN` |
| System | system folders, app support, hidden dotfolders |
| Other | Git repos (except this repo unless approved), large folders, unknown recursive trees |

Use placeholder paths in fixtures only, e.g. `/LOCAL_TEST_FOLDER_PLACEHOLDER/OwenSelectedTinyTestFolder`.

No arbitrary path input.
