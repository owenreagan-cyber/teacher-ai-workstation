# Canvas Knowledge Object Model

```text
Status: phase_4_static_object_model
Classification: schema documentation only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
```

## Common Required Fields

Every future Canvas knowledge object should carry:

- `object_id`
- `object_type`
- `title`
- `source_reference_ids`
- `evidence_ids`
- `source_class`
- `evidence_level`
- `verification_status`
- `approval_status`
- `confidence_level`
- `created_at`
- `updated_at`
- `blocked_data_flags`

`blocked_data_flags` must explicitly track student data, real curriculum ingestion, Canvas API/OAuth/live reads, Canvas writes/publishing, production course use, RAG/embeddings/generation, and runtime database writes.

## Object Types

| Object | Purpose | Required links |
| --- | --- | --- |
| Course | Future course container metadata | School year, source class, evidence, approval |
| School year | Year label and active/inactive status | Course, source class, approval |
| Course source class | Declares fake, manual, historical, sandbox, or production source | Evidence level, approval |
| Module | Canvas module structure | Course, week/lesson/page/assignment links |
| Week | Instructional week grouping | Course, module, lesson links |
| Lesson | Lesson-level instructional object | Module, page, assignment, objective links |
| Page | Canvas page object | Page sections, HTML blocks, banners, links, images |
| Page section | Logical page region | Page, HTML blocks, evidence |
| HTML block | Future reviewed HTML fragment pattern | Page section, pattern catalog, source reference |
| Banner | Page or module banner pattern | Page, pattern catalog, evidence |
| Callout | Highlighted instructional note or warning | Page section, pattern catalog |
| Table | Structured Canvas table pattern | Page section, source reference |
| Image | Image metadata only | Page, source reference, accessibility notes |
| Link | URL or Canvas-relative link metadata | Page, resource/file/source reference |
| Assignment | Assignment setup metadata | Course/module/lesson, rubric, source evidence |
| Rubric | Rubric criteria metadata | Assignment, standards/objectives |
| Announcement | Announcement metadata and future writing pattern | Course, source evidence |
| File | File metadata only | Folder/resource/source reference |
| Folder | Folder organization metadata | File/resource/course |
| Resource | Reusable instructional resource metadata | File/link/source/evidence |
| Standard | Standard reference metadata | Objective/lesson/assignment |
| Objective | Learning objective metadata | Lesson/standard/fact |
| Vocabulary term | Term, definition, usage source | Lesson/fact/source |
| Fact | Source-backed claim candidate | Evidence/source/reference |
| Question | Future question candidate | Answer/fact/evidence |
| Answer | Future answer candidate | Question/fact/evidence/source |
| Evidence | Reviewed support object | Source reference, source class, evidence level |
| Source reference | Pointer to source metadata | Source class/evidence/approval |
| Confidence score or level | Explicit certainty marker | Evidence and verification state |
| Verification status | Review state | Evidence and approval state |
| Approval status | Permission boundary | Evidence level and source class |
| Teacher style / "Mr. Reagan" voice sample | Future reviewed style sample metadata | Evidence/source/approval; no Phase 4 style model |

## Source-Backed Q&A Constraint

Future Q&A must not answer from memory, style inference, or generated guesses. The minimum relationship is:

```text
Question -> Answer -> Fact(s) -> Evidence -> Source Reference -> Source Class -> Evidence Level -> Approval Status
```

If any link is missing, stale, unverified, or blocked, the answer is not authoritative.

## Fake Fixture Constraint

Phase 4 examples must use `fake_local_fixture`, `Level 0`, `fixture_approved`, and `fake_local_example`. These examples demonstrate shape only and do not define official course facts, page styling, or teacher voice.
