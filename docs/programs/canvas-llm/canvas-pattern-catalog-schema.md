# Canvas Pattern Catalog Schema

```text
Status: phase_4_static_pattern_schema
Classification: schema documentation and fake/local examples only
Runtime activation: no
```

## Purpose

The future pattern catalog will record reviewed Canvas patterns without treating unreviewed examples as official style. Phase 4 defines categories and fields only. It does not extract from Canvas, ingest real curriculum, learn teacher style, generate content, run RAG/embeddings, or approve official "Mr. Reagan" voice behavior.

## Required Pattern Fields

- `pattern_id`
- `pattern_category`
- `pattern_name`
- `description`
- `source_reference_ids`
- `evidence_ids`
- `source_class`
- `evidence_level`
- `verification_status`
- `approval_status`
- `confidence_level`
- `example_status`
- `not_authority_reason`

## Pattern Categories

| Category | Future use | Phase 4 note |
| --- | --- | --- |
| Canvas HTML/page style patterns | Reviewed HTML structures | Fake/local schema examples only |
| Page banners | Banner placement and semantics | No official banner style asserted |
| Spacing | Reviewed spacing observations | No invented spacing promoted |
| Color palette | Reviewed colors from approved sources | No fictional palette promoted |
| Fonts and sizes | Reviewed type choices | No official font asserted |
| Centering and placement | Layout behavior | Schema only |
| Containers/cards/tables/buttons | Component patterns | Schema only |
| Assignment setup patterns | Assignment metadata patterns | Future-only |
| Page setup patterns | Page organization patterns | Future-only |
| Module structure patterns | Module/week sequencing | Future-only |
| File naming patterns | Naming conventions | Future-only; no Drive/NAS/iCloud scan |
| Folder organization patterns | Folder grouping conventions | Future-only; no filesystem scan |
| Announcement writing style patterns | Announcement traits | Future-only; no live Canvas |
| "Mr. Reagan" voice/style traits | Reviewed voice sample metadata | Not a style model; fake examples are not authority |
| Course fact candidates | Source-backed facts | Future-only |
| Source-backed Q&A candidates | Question/answer candidates | Future-only; no generation/RAG |

## Example Status Values

- `fake_local_schema_example`
- `manual_redacted_example`
- `reviewed_source_example`
- `proposal_candidate`
- `blocked`

Any pattern with `fake_local_schema_example` must include a `not_authority_reason` explaining that it is fictional and not official style.
