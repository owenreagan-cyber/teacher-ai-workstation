# Production Registry Source-Reference Contract

Last updated: 2026-07-02

```text
Status: metadata_boundary_refinement_planning
Classification: source-reference contract planning — non-resolving labels only
Authority: supplements docs/curriculum-builder-production-registry-metadata-source-boundaries.md
```

## Non-Activation

This contract does not authorize source auto-resolution, integrations, file reads, or production writes.

## Non-Resolving Principle

`source_reference` fields are **opaque human-readable labels**. Code must not parse them as paths, IDs, URLs for fetch, or API targets.

## Allowed Shape

```json
{
  "source_reference": {
    "display_label": "Sample textbook — teacher shelf copy",
    "source_type": "print_resource",
    "location_note": "Example binder, shelf row placeholder",
    "citation_note": "Optional non-resolving note"
  }
}
```

## Field Contract

| Field | Purpose | Value shape | Example (fake) | Blocked | Validator expectation | Required |
| --- | --- | --- | --- | --- | --- | --- |
| `display_label` | Human label for where resource lives | Short string ≤ 200 | `Sample textbook — shelf copy` | Drive IDs, URLs | No `http://`, `https://`, `drive.google.com` | yes |
| `source_type` | Label semantics enum | Enum (below) | `print_resource` | Credentials | Enum membership | yes |
| `location_note` | Owen location note | String ≤ 300 | `Example binder, row 2` | NAS mount paths, iCloud paths | No absolute paths; no `://` | optional |
| `citation_note` | Optional citation note | String ≤ 300 | `Non-resolving label only` | Copied curriculum text | Length cap | optional |

## Allowed `source_type` Values (Label Semantics Only)

| Value | Meaning | Not allowed |
| --- | --- | --- |
| `manual_label` | Generic manual label | API target |
| `print_resource` | Physical print resource label | ISBN fetch |
| `drive_label` | Drive **label** Owen typed | Drive file ID, live URL |
| `local_label` | Local folder **label** Owen typed | Absolute path for code |
| `nas_label` | NAS **label** Owen typed | Mount path, SMB URL |
| `icloud_label` | iCloud **label** Owen typed | iCloud path for code |
| `canvas_label` | Canvas **label** Owen typed | Course/module ID, API URL |

These values describe **how Owen thinks about the source** — they are not integration endpoints.

## Blocked Patterns (Future Validator)

| Pattern | Reason |
| --- | --- |
| `https://`, `http://` | Live fetch URL |
| `drive.google.com`, `docs.google.com` | Drive resolution |
| `canvas.instructure.com` | Canvas resolution |
| `/Volumes/`, `smb://`, `file://` | Resolvable paths |
| OAuth, API key field names | Integration artifacts |
| UUID/file-id patterns in labels | Resolvable IDs |

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-blocked-field-guardrails.md` | Full blocked categories |
| `docs/curriculum-builder-production-registry-manual-metadata-field-contract.md` | Parent record contract |
