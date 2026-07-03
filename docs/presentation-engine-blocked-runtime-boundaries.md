# Presentation Engine — Blocked Runtime Boundaries

Last updated: 2026-07-03

```text
Status: negative boundary documentation
Authority: blocks runtime activation unless explicit Owen mission
PASS on status commands does not lift these blocks
```

## Purpose

Explicit list of capabilities that remain **blocked** for Presentation Engine and classroom display lanes. Status PASS proves planning coherence only.

## Blocked Runtime Behavior

| Capability | State | Proof |
| --- | --- | --- |
| Runtime rendering | blocked | No renderer scripts; status negative checks |
| Slide export (HTML/PPTX/Keynote/Google Slides) | blocked | No export commands |
| AI generation | blocked | No generation commands; no prompt fields in fixtures |
| Auto lesson creation | blocked | Implementation gate |
| Real curriculum ingestion | blocked | Metadata boundary; fake fixtures only |
| File parsing (textbook/worksheet/assessment) | blocked | No parsers in repo for this lane |
| OCR | blocked | Constitution hard boundary |
| Screenshots | blocked | No capture automation |
| Image generation | blocked | No image-gen commands |

## Blocked Integrations

| Integration | State |
| --- | --- |
| Google Drive | blocked |
| Google Slides automation | blocked |
| Canvas API / Canvas IDs | blocked |
| NAS paths | blocked |
| iCloud paths | blocked |
| OAuth | blocked |
| Network API calls | blocked |
| PowerPoint automation | blocked |
| Keynote automation | blocked |
| Canva | blocked |
| Lovable API | blocked |

## Blocked Data and Content

| Category | State |
| --- | --- |
| Real Saxon or textbook text | blocked |
| Worksheet questions | blocked |
| Assessment content | blocked |
| Answer keys | blocked |
| Copied curriculum content | blocked |
| Student names or identifiers | blocked — absolute |
| Student data workflows | blocked — absolute |
| Real curriculum file paths | blocked |
| Drive URLs | blocked |

## Blocked Production Registry Actions

| Action | State |
| --- | --- |
| Second production record | blocked |
| Writer scripts | blocked |
| Active `--write` / `--curriculum-registry-write` | blocked |
| Sentinel removal/rename | blocked |
| Metadata pilot expansion beyond first record | blocked pending Owen decision |

## Blocked Commands (Must Not Exist)

```text
--presentation-engine-render
--presentation-engine-export
--presentation-engine-generate
--presentation-engine-ingest
```

Status scripts verify absence of runtime renderer, export, and generation shell invocations in Presentation Engine paths.

## Safe Allowed Today

| Activity | Classification |
| --- | --- |
| Planning docs | approved in this mission |
| Fake/local JSON fixtures | approved |
| Read-only status command | approved |
| Negative tests | approved |
| Roadmap/status cross-links | approved |

## Orchestrated Boundary Proof

```bash
bin/chief-of-staff --presentation-engine-renderer-foundation-status
bash tests/presentation-engine-renderer-foundation-status-test.sh
```

## Non-Activation

This boundary doc is Markdown only. It does not implement guards in runtime code beyond existing repo status/test patterns.
