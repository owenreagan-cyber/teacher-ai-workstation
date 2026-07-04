# Teacher Knowledge Vault — Extraction Evidence Package

Last updated: 2026-07-04

```text
Status: evidence format — fake snippets only; supports Smart Rename
runtime_executed: false in M6
```

## Evidence Package Fields

| Field | Purpose |
| --- | --- |
| `extraction_method` | native / local_ocr / rule_inference |
| `extraction_scope` | metadata / first_page / selected_pages |
| `extracted_title_candidate` | Fake placeholder label |
| `extracted_heading_candidate` | Fake placeholder label |
| `extracted_curriculum_marker_candidate` | Fake placeholder label |
| `lesson_unit_candidate` | Fake placeholder label |
| `resource_type_candidate` | homework / teacher_manual / assessment |
| `audience_risk` | student_facing / teacher_only |
| `teacher_only_risk` | boolean |
| `leakage_risk` | boolean |
| `confidence_by_stage` | staged confidence object |
| `manual_review_reason` | low_confidence / teacher_only / leakage |
| `allowed_next_actions` | suggest_rename / route_review |
| `blocked_actions` | execute_rename / publish_canvas / student_facing_export |

## Integration

Extraction evidence supports smart rename suggestions, duplicate/version review, and resource package matching. Extraction does not move, rename, or publish files. Extraction does not make teacher-only content student-visible.

Fixture: `assistant/teacher-knowledge-vault/m6/fake-extraction-evidence-packages.json`
