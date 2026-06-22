# Phase 0C 3D Agent Readiness Injector Prompt

Use this prompt to recreate or review the Phase 0C 3D Design Agent readiness layer.

## Task

Add 3D Design Agent readiness and verification foundations only. Do not build the full 3D agent, React app, autonomous agents, printer-control automation, Bambu cloud/network automation, marketplace scraping, or direct printer sending.

## Required context

- The teaching-focused Chief of Staff remains the primary product priority.
- The future 3D Design Agent is separate from but coordinated by the Chief of Staff.
- Owen and his partner use Bambu Studio and Bambu printers.
- Work must support personal, classroom, business/commercial, repair/replacement, and reference-only use modes.
- Reference-only means not assumed commercial-safe.
- Personal/reference designs and commercial product designs must be clearly separated.

## Required additions

- Brewfile entries for OpenSCAD and Bambu Studio.
- `~/3D-Printing` folder structure.
- `3d-agent/` policies, workflows, templates, examples, verification docs, and training docs.
- Partner workflow.
- Verification docs.
- OpenSCAD test suite.
- LLM routing for CAD.
- Bambu Studio verification guidance.
- Day 1 setup and 3D roadmap docs.

## Language rules

- Do not use "print-ready" language for AI-generated designs.
- Use "slicer-ready pending human verification" when appropriate.
- Use advisory-only printing principle language.
- Use the use mode question: personal, classroom, business/commercial, repair/replacement, or reference-only.
- Avoid language suggesting the software makes the final print decision.
- The agent can warn, classify, and recommend review, but cannot block, stop, disable, or prevent printing.
- The human operator makes the final print decision.

## Verification expectations

- Geometry checks
- Dimension checks
- Color/multicolor checks
- Image-to-3D conversion rules
- Support strategy
- Pre-slicer checklist
- OpenSCAD test suite
- Bambu Studio layer/support/color preview review

## Final validation

Run:

```bash
bash -n bootstrap.sh setup/*.sh
git diff --check
```
