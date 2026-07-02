# Chief of Staff Agent Core

Last updated: 2026-07-02

```text
Program: Chief of Staff v1 Agent Core — Program B1
Status: foundation complete (read-only)
Classification: local-first control plane — not a specialist builder
```

## Purpose

Chief of Staff is the **central workstation control plane** for Teacher AI Workstation. It coordinates, validates, summarizes, recommends, routes, tracks, proves, reports, and enforces approval boundaries.

## Responsibilities

| Responsibility | Description |
| --- | --- |
| Coordinate | Connect teacher intent to the right foundation track or future program |
| Validate | Run PASS/WARN/FAIL status and proof surfaces |
| Summarize | Aggregate dashboard, build queue, and active priorities |
| Recommend | Deterministic next-action from repo-local sources |
| Route | Point work to specialist tools per `docs/ai-tool-routing-matrix.md` |
| Track | Maintain memory, intake, and program status visibility |
| Prove | Enforce pre-merge proof workflow |
| Report | Daily/weekly operating summaries (planned B2+) |
| Enforce boundaries | Implementation gate, Canvas stop marker, non-activation rules |

## Chief of Staff Must Not Become

Chief of Staff orchestrates. It **must not become** any specialist builder listed below.

| System | Relationship |
| --- | --- |
| Curriculum Builder | Separate metadata/contracts pipeline |
| Curriculum Library | Separate library foundation |
| Lesson Planning engine | Scaffold only; no generation |
| Renderer | Interface foundation only |
| Local Retrieval engine | Planning only |
| Canvas integration | Frozen; stop marker active |
| Lovable | Future external app-builder (Program G1) |
| Gemini / ChatGPT / Claude | External cloud tools; manual or future API |
| Cursor | Repo implementation agent |
| Local LLM / Ollama | Future inference runtime (Program D) |
| Health Monitor | Future observe/report program (Program H) |
| System Updater | Future approved-update program (Program I) |
| Mac Workstation Experience | Future modes/surfaces (Program E) |
| Widget/Shortcut Builder | Future catalogs (Program F) |
| 3D Builder Workshop Agent | Future sub-agent (Program J) |
| Integration engine | Last-stage connectors (Program G) |
| Automation engine | Blocked unless explicit mission |

## Program B1 Deliverables

| Artifact | Location |
| --- | --- |
| Command surface index | `docs/chief-of-staff-command-index-v1.md` |
| Command manifest | `assistant/chief-of-staff/v1/command-surface-manifest.json` |
| `--commands` | `bin/chief-of-staff --commands` |
| Operating model | `docs/chief-of-staff-operating-model.md` |
| Proof workflow | `docs/chief-of-staff-proof-workflow.md` |
| Foundation closure | `docs/chief-of-staff-v1-foundation.md` |
| Status proof | `bin/chief-of-staff --chief-of-staff-v1-status` |

## Cross-References

- Master roadmap Program B: `docs/master-build-roadmap.md`
- AI tool routing: `docs/ai-tool-routing-matrix.md`, `assistant/model-routing.md`
- Capability map: `docs/teacher-workstation-capability-map.md`
- Phase 3 closure: `docs/teacher-workstation-foundation-v0.md`

## Non-Activation

Documentation and read-only status only. No lesson generation, APIs, OAuth, network calls, automation, or student data.
