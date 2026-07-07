# Canvas LLM Phase 13: Historical Academic + Homeroom Course Fetch Approval Gate

## Status

Phase 13 records the approved direction for future Canvas API access across historical academic courses, current operational courses, and Homeroom/newsletter courses.

This phase is an approval, scope, and safety gate only.

Phase 13 does not perform a Canvas API call, live fetch, file download, Canvas write, rename, move, delete, database write, RAG, embedding, local model execution, or lesson generation.

## Strategic goal

The near-term Canvas goal is operational readiness before July 20.

Canvas is the student/parent-facing curriculum distribution layer. It already contains many preloaded files from prior school/IT workflows. Those files need to be inventoried, mapped, renamed, and filed cleanly so the AI agent can understand which Canvas file to pull for each circumstance.

The local curriculum library remains important for future Lesson Creator work, teacher-only materials, tests, manuals, answer keys, and private source files. That broader local library classification is intentionally pushed back for now.

## User approval recorded

The user approves future Canvas API access when a later phase explicitly requires it and remains inside the approved safety boundaries.

The user approves using relevant Canvas courses for read-only metadata analysis, including:

- historical academic courses
- current operational courses
- Homeroom/newsletter courses

Course IDs must still be supplied or discovered through an approved course-listing gate before any fetch phase runs. Phase 13 does not fetch or enumerate courses.

## Course roles

### Historical academic courses

Historical academic courses may be used as read-only pattern sources for:

- real file volume
- folder structure
- module structure
- module item relationships
- file references
- page metadata
- announcement metadata
- assignment metadata needed for file/module/page relationships
- year-to-year comparison
- course-to-course comparison
- naming/folder cleanup rules
- upload-intake naming rules

Historical academic courses must not be used to ingest student data, submissions, grades, rosters, analytics, messages, discussion replies, file bodies, page bodies, announcement bodies, or assignment bodies unless separately approved in a later gate.

### Current operational courses

Current operational courses may be used as the target readiness context for Canvas organization.

Current operational courses may be compared against historical academic courses to identify missing files, incomplete module structures, naming gaps, folder gaps, and readiness blockers.

No Canvas write, rename, move, delete, upload, publish, or update action is approved by Phase 13.

### Homeroom/newsletter courses

Homeroom/newsletter courses are a separate course class.

They should not be evaluated against normal academic Canvas curriculum-file guidelines. Homeroom is used for weekly homeroom and school reminders, and its Canvas guidelines are different.

Homeroom may be analyzed later for newsletter structure, layout evolution, section order, reminder categories, parent communication patterns, and future newsletter template design.

A later phase may request separate approval for limited Homeroom page/announcement body review if layout and appearance analysis requires it. Phase 13 does not approve body ingestion.

## Approved future metadata categories

A later approved fetch phase may read metadata for:

- course metadata
- folders metadata
- files metadata
- modules metadata
- module_items metadata
- pages metadata
- announcements metadata
- assignments metadata only when needed for file/module/page relationship mapping

## Pages scope

Pages are approved for metadata and relationship mapping only.

Allowed page metadata may include:

- page ID or URL slug
- title
- published status when available
- created_at or updated_at when available
- front_page flag when available
- module relationship when referenced by module_items
- attachment/link reference metadata when available without body ingestion

Blocked for pages:

- page body/html content
- embedded content extraction
- full text copying
- summarizing page body
- RAG/embeddings from page body
- tracked real Canvas URLs
- student interactions or comments

## Announcements scope

Announcements are approved for metadata and relationship mapping only.

Allowed announcement metadata may include:

- announcement ID
- title
- posted_at or delayed_post_at when available
- published/locked status when available
- course relationship
- attachment/file reference metadata when available without message-body ingestion

Blocked for announcements:

- announcement body/message text
- replies/comments
- discussion entries
- student interactions
- read receipts
- full text copying
- summarizing announcement body
- RAG/embeddings from announcement body
- tracked real Canvas URLs

## Blocked endpoints and data classes

Future fetch phases must continue to block:

- users
- students
- enrollments
- rosters
- submissions
- grades
- analytics
- attendance
- conversations/messages
- discussion entries/replies
- quiz responses
- student comments/interactions
- file downloads
- file contents
- page bodies
- announcement bodies
- assignment bodies unless separately approved
- Canvas writes
- renames
- moves
- deletes
- uploads
- publishing changes
- production writes
- canonical catalog writes
- knowledge DB writes
- runtime database writes
- RAG
- embeddings
- local model/Ollama execution
- lesson generation
- tracked tokens/secrets
- tracked school Canvas URLs
- committed `.local/...` fetched metadata

## Future Phase 14 expectation

A later Phase 14 may perform a real read-only Canvas metadata fetch.

Expected Phase 14 rules:

- use approved API credentials only from local environment
- fetch only approved metadata categories
- write raw fetched metadata only to ignored `.local/...`
- never commit raw fetched metadata
- summarize counts and validation results only
- preserve PASS/WARN/FAIL semantics
- compare historical/current/Homeroom course roles carefully
- keep Homeroom separate from academic-course scoring
- perform no Canvas writes

## Future analysis goals

Future analysis should help answer:

- Which Canvas files already exist?
- Which files are referenced by modules?
- Which files are referenced by pages or announcements?
- Which files appear unreferenced?
- Which folders are overloaded or messy?
- Which filenames need cleanup?
- Which naming conventions appear across historical courses?
- Which course structures changed year to year?
- Which current operational courses are missing expected files or folders?
- Which Homeroom newsletter layouts worked best?
- Which upload-intake naming rules should be used going forward?

## Validation

Run:

```bash
bin/chief-of-staff --canvas-llm-phase-13-status
```

The status check proves:

- Phase 13 approval doc exists
- historical academic course role is defined
- current operational course role is defined
- Homeroom/newsletter course role is defined
- pages metadata is approved
- announcements metadata is approved
- body ingestion remains blocked
- student data remains blocked
- Canvas writes remain blocked
- `.local/...` fetched metadata remains ignored/untracked
- Phase 12 still passes
