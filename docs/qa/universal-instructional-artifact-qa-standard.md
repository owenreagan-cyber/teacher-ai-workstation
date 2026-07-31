# Universal Instructional Artifact QA Standard

Last updated: 2026-07-30

Status: **Standing acceptance gate for every instructional artifact built or reviewed in the Teacher AI Workstation project.**

## Purpose

Creating files is not the same as completing an instructional package.

An instructional artifact may be described as **finished**, **complete**, **ready**, **classroom-ready**, or **fully validated** only after it has completed the full eight-stage validation sequence in this standard.

This standard applies to:

- lesson presentations
- worksheets
- guided notes
- reading checks
- quizzes and assessments
- teacher keys
- teacher scripts
- review activities
- lesson packages
- student handouts
- printable classroom resources
- multi-artifact instructional packages

Existing package-readiness systems may confirm that required files and metadata exist. This standard determines whether those files are actually suitable for classroom use.

## Status semantics

| Status | Meaning |
| --- | --- |
| **PASS** | Classroom-ready. All required validation stages were completed and no blocking issue remains. |
| **WARN** | Usable, but teacher review is still required. Every warning must be explained. |
| **FAIL** | Blocking issues remain. The artifact is not deliverable or classroom-ready. |

A numeric score never overrides a FAIL.

A missing required validation step cannot be silently treated as PASS.

## Required eight-stage workflow

### 1. Source validation

Confirm that instructional content is supported by the provided curriculum, approved source material, standards, or teacher direction.

Required checks:

- no invented academic facts
- no unsupported claims
- no accidental contradiction of source material
- vocabulary and definitions match approved sources
- examples remain accurate
- answer keys are derived from the approved content
- uncertain or missing source information is clearly identified

A package with unsupported or fabricated academic content receives **FAIL**.

### 2. Content-priority validation

Classify instructional content before final design:

| Priority | Meaning |
| --- | --- |
| **Critical** | Required for the learning objective or assessment |
| **High Priority** | Strongly supports understanding or successful practice |
| **Supporting** | Helpful enrichment, context, examples, or reinforcement |
| **Omit** | Duplicative, distracting, unsupported, or beyond the lesson scope |

Required checks:

- critical ideas are present
- high-priority ideas receive appropriate emphasis
- supporting content does not overwhelm essential learning
- omitted content is intentionally excluded
- student cognitive load remains appropriate

### 3. Cross-artifact alignment

Multi-artifact packages require an alignment table.

Minimum alignment fields:

| Element | Presentation | Student Resource | Teacher Key/Script | Assessment |
| --- | --- | --- | --- | --- |
| Learning objective | | | | |
| Critical content | | | | |
| Vocabulary | | | | |
| Guided practice | | | | |
| Independent practice | | | | |
| Answer support | | | | |

Required checks:

- the same learning objective drives all artifacts
- vocabulary is consistent
- examples do not conflict
- student questions are taught before assessment
- answer keys match student versions
- teacher directions match student-facing materials
- page and item references are accurate

Misaligned answer keys, missing instruction for assessed content, or contradictory artifacts receive **FAIL**.

### 4. Educational suitability

Evaluate the artifact for the intended grade, subject, lesson context, and available time.

Required checks:

- grade-appropriate language
- manageable cognitive load
- clear directions
- suitable lesson pacing
- sufficient guided practice
- sufficient independent practice
- appropriate response demands
- realistic completion time
- accessibility and readability
- no unnecessary teacher explanation required to decode the resource

Automated educational-layout checks may inform this stage but do not replace teacher judgment.

### 5. Visual and layout QA

Every page and slide must be rendered and visually inspected.

Required checks:

- no clipping
- no overlap
- no hidden content
- no accidental blank pages or slides
- readable font sizes
- sufficient contrast
- consistent visual hierarchy
- appropriate spacing
- sufficient student writing space
- diagrams and maps remain legible
- answer choices and matching sections align correctly
- projector slides are readable from the back of the room
- print resources remain usable in grayscale where required

For multi-page or multi-slide resources, inspect every rendered page or slide, not only the first page or a sample.

### 6. Technical QA

Required checks:

- files open successfully
- expected file formats are present
- pagination is correct
- page size and orientation are correct
- links work where applicable
- fonts and embedded assets render correctly
- teacher and student versions correspond
- print-safe margins are preserved
- generated output contains no unresolved placeholders
- filenames are clear and stable
- no private data, tokens, temporary paths, or machine-specific metadata are exposed

For DOCX, PPTX, or HTML sources, authoritative pagination validation requires export to PDF when a printable classroom artifact is expected.

### 7. Classroom simulation

Run three classroom-use perspectives.

#### Teacher test

Confirm that the teacher can:

- understand the lesson sequence
- locate all required materials
- teach from the presentation or script
- identify expected answers
- manage transitions
- complete the lesson in the available time

#### Student test

Confirm that a student can:

- understand what to do
- read all text
- locate response spaces
- follow the sequence
- complete the work without unnecessary confusion
- distinguish examples from required responses

#### Substitute-teacher test

Confirm that a capable substitute can:

- identify the objective
- follow the lesson sequence
- understand activity directions
- use the key or script
- determine when the lesson is complete
- avoid relying on undocumented teacher knowledge

A package that depends on hidden instructions or unexplained teacher knowledge receives WARN or FAIL depending on classroom impact.

### 8. Final acceptance report

Every artifact or package must end with a documented acceptance report.

Use this format:

## Final Instructional Artifact Acceptance Report

| Category | Status | Evidence / Notes |
| --- | --- | --- |
| Source validation | PASS/WARN/FAIL | |
| Content-priority validation | PASS/WARN/FAIL | |
| Cross-artifact alignment | PASS/WARN/FAIL | |
| Educational suitability | PASS/WARN/FAIL | |
| Visual and layout QA | PASS/WARN/FAIL | |
| Technical QA | PASS/WARN/FAIL | |
| Classroom simulation | PASS/WARN/FAIL | |
| Tooling confidence | PASS/WARN/FAIL | |

**Overall status:** PASS / WARN / FAIL

**Teacher review still required:** Yes / No

**Blocking issues:**

- None, or list each blocking issue.

**Warnings:**

- None, or explain every warning.

**Artifacts inspected:**

- List every file, page range, or slide range reviewed.

**Validators and commands run:**

- List each command and result.
- State explicitly when a validator was unavailable.

## Mechanical validation policy

Use Teacher AI Workstation validators whenever they are available.

Common entry point:

```bash
python3 scripts/artifact_quality/run_preflight.py --help
```

When a required validator is unavailable, fails to run, or does not support the artifact type:

1. record **WARN** for tooling confidence
2. run every available render and visual check
3. perform manual inspection
4. do not claim the missing check passed
5. explain the validation gap in the final report

When a critical validation-tool test fails, automated findings are provisional until tooling confidence is restored.

## Completion language

### Overall PASS

> The package passed source, alignment, instructional, visual, pagination, answer-key, and technical validation and is ready for classroom use.

Use this statement only when every required stage has been completed and no unresolved warning requires teacher review.

### Overall WARN

> The package passed the required classroom-use checks with the warnings listed below. Teacher review is still recommended before use.

Every warning must be listed and explained.

### Overall FAIL

> The package is not ready for classroom use. The following blocking issues must be corrected before delivery.

Every blocking issue must be listed.

## Prohibited completion claims

Do not use the following solely because files were generated or exported:

- finished
- complete
- ready
- classroom-ready
- fully validated
- print-ready
- approved
- final

These terms require evidence from the full acceptance sequence.

## Relationship to existing systems

This standard complements:

- `docs/instructional-artifact-quality-foundation.md`
- `docs/instructional-artifact-quality-operator-guide.md`
- artifact profiles under `configs/artifact-profiles/`
- standards under `standards/instructional-artifacts/`
- lesson-package metadata and readiness gates

Metadata checks answer:

> Does the package contain the expected files and fields?

This standard answers:

> Are those files accurate, aligned, usable, and classroom-ready?

## Non-activation boundary

This document defines review and acceptance policy only.

It does not activate:

- lesson generation
- file scanning
- OCR
- document indexing
- embeddings
- external APIs
- Canvas or Google integrations
- automatic distribution
- student-data processing
