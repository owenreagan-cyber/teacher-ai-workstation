<!--
REPO STATUS: STATIC EXTERNAL PLANNING INPUT ONLY
AUTHORITY: NOT REPO AUTHORITY / NOT OWEN APPROVAL / NOT IMPLEMENTATION APPROVAL
GOVERNANCE: This document contains exploratory notes and taxonomy classification input.
It does not authorize schemas, validators, fixtures, parsers, commands, runtime features, local model execution, integrations, student data handling, real curriculum ingestion, or production writes.
-->

# PLANNING MEMO

**To:** Owen Reagan

**From:** External Planning & Product Discovery Analyst

**Date:** July 3, 2026

**Subject:** Discovery & Classification Architecture: Local-First Teacher AI Workstation

---

## 1. Executive Summary & Role Boundary

This planning memo establishes a static framework for classifying teacher workflows, identifying structural pain points, and mapping out a local-first product discovery architecture.

> ⚠️ **STRICT REPOSITORY BOUNDARY NOTICE:** This document serves strictly as **External Planning Input**. It does NOT constitute repository authority, Owen approval, or implementation approval. It does NOT authorize schemas, validators, fixtures, commands, runtime behavior, integrations, active generation, or production writes.

---

## 2. Core Workflow Classification Matrix

To guide product discovery, teacher needs are classified into three primary workflow lanes. This structural taxonomy identifies where a local workstation framework can provide conceptual layout planning without executing active generation or processing data.

### Workflow Taxonomy Table

| Workflow Domain | Core Teacher Need | Primary Pain Point | Local AI Opportunity |
| --- | --- | --- | --- |
| **Curriculum & Lesson Design** | Formatting, adapting, and structuring raw educational standards into daily pacing guides. | High cognitive friction spent restructuring public text into clean Markdown/text formats. | **Static Template Planning:** Conceptual layouts and blueprint design for universal structures without real-time content assembly. |
| **Asset & Material Management** | Organizing worksheets, study sets, and review materials locally without cloud lock-in. | Siloed files across multiple devices; brittle search capabilities across locally stored materials. | **Future Metadata Workflow Planning:** Designing taxonomy field ideas for manual tagging and structure concepts. |
| **Administrative & Routine Text** | Drafting parent updates, newsletters, and general classroom announcements. | Repetitive writing cycles eating into instructional preparation time. | **Placeholder Template Planning:** Mapping the visual scaffolding for communication blueprints. |

---

## 3. High-Priority Pain Point Identification

### 1. The "Clean Markdown" Tax

* **The Issue:** Teachers spend significant time converting rich text, PDF layout artifacts, and messy web formatting into clean, scannable text for personal workstations.
* **Future Mitigation Strategy:** Designing deterministic, plain-text template blueprints that outline manual formatting guidelines to enforce structural uniformity across file assets.

### 2. High-Friction Metadata Cataloging

* **The Issue:** Educational materials lose context over time. A file named `Unit_2_Review.txt` tells a teacher little about its target grade, concept dependencies, or structural complexity.
* **Future Mitigation Strategy:** Developing uniform manual metadata guidelines to establish consistent, human-applied naming conventions and tag locations within local markdown files before saving to disk.

---

## 4. Proposed Metadata & Classification Field Ideas (Planning Reference Only)

To enable manual offline organization across local storage, the workstation may eventually need a unified classification system. Below are suggested static metadata field ideas for asset discovery planning.

### Static Metadata Field Ideas

* **`asset_domain`**: Example categories may include Mathematics, Language Arts, Classroom Management.
* **`pedagogical_layer`**: Example categories may include Direct Instruction, Independent Practice, Spiral Review, Assessment Blueprint.
* **`structural_format`**: Example categories may include Markdown Document, Plain Text List, Task Card Matrix.
* **`concept_dependency_tags`**: Planning-only prerequisite tags that could describe what students should know before using an asset.
* **`local_storage_tier`**: Planning-only archival classification, such as Active Term or Historical Reference.

These are field ideas only. They are not schemas, accepted keys, validators, fixtures, parsers, commands, or runtime requirements.

---

## 5. Blocked Capabilities & Operational Gates

To maintain a zero-risk security and governance profile, specific capabilities are blocked or restricted pending clear repository governance updates.

### Blocked Capabilities List

* **Student Data:** Absolute prohibition on names, rosters, grades, accommodations, IEP details, behavior notes, or student work.
* **Real Curriculum Ingestion & Copied Content:** No real curriculum sources, textbooks, worksheets, tests, or answer keys may be pulled in, copied, or stored.
* **Drive/NAS/iCloud/Canvas Access:** No integration, indexing, or connectivity with cloud drives, network storage, school folders, or Canvas exports.
* **API/OAuth/Network Integration:** No live integrations, external API communication, token exchanges, or network-bound connections.
* **File/Folder Scanning & OCR:** No automatic file system watching, folder parsing, indexing, or optical character recognition processing.
* **Embeddings & RAG:** No generation of vector embeddings, localized vector database setups, or Retrieval-Augmented Generation workflows.
* **AI Generation & Runtime Behavior:** No active generation engines, runtime script executions, or content creation behaviors are authorized. No real lesson generation, worksheet generation, slide generation, or student-facing material creation.
* **Local Model/Ollama Execution:** No local inference, LLM orchestration, or background AI model execution.
* **Production Registry Writes & Scripts:** No production registry database modifications, active `--write` CLI parameters, or writer script executions.

### Status Gate Matrix

```text
[SAFE FOR PLANNING & DOCS] --> Metadata taxonomy, pain point mapping, structural layout blueprints
[PROPOSAL CANDIDATES] --> Planning notes for manual tagging concepts, with no active schema, validator, fixture, parser, or runtime behavior
[BLOCKED / FORBIDDEN] --> Content ingestion, active AI generation, live local system operations
```

---

## 6. Next Discovery Steps & Classification Status

### Safe Planning-Only

* Refining the structural metadata field list to ensure broad domain coverage for elementary education concepts.
* Drafting visual layouts for completely empty, static user-interface wireframes.

### Proposal Candidates

* Drafting a markdown frontmatter planning note as a future proposal candidate, with no active schema, validator, fixture, parser, or runtime behavior.

### Blocked Pending Owen Decision

* Establishing the exact technical directory tree layout for storing manual text assets.

### Blocked Due to Student Data

* Designing templates intended to structure classroom rosters, grade sheets, or individualized learning plans.

### Blocked Due to Real Curriculum Content

* Populating test templates with specific, real-world textbook or assessment questions.

### Blocked Due to Integration/API/OAuth/Network

* Planning synchronization protocols between local directories and external school learning management systems.

### Blocked Due to Runtime/Generation

* Proposing back-end execution modules, Ollama controller logic, automated parsing tasks, or markdown generation scripts.

---

## Repo Cross-References

| Artifact | Role |
| --- | --- |
| `docs/proposals/ideas/gemini-discovery-classification-architecture-intake.md` | Repo theme classification (not memo authority) |
| `docs/proposals/blocked/gemini-discovery-classification-runtime-boundaries.md` | Blocked runtime summary |
| `docs/proposals/ideas/external-planning-input-intake-map.md` | External intake governance |
