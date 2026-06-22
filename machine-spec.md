# Teacher AI Workstation Machine Spec

## Teacher context

- User: 4th grade teacher
- School: Thales Academy
- Curriculum and classroom needs include:
  - Language Arts / Shurley English
  - History
  - Science

## Output requirements for later phases

- Canvas outputs must be clean HTML later.
- Worksheets must include answer keys later.
- Printable outputs must pass print QA later.
- Presentations must include engagement and DOK 1-3 questions later.

## Workstation direction

- The workstation is MacBook-first.
- The AI strategy is local-first, with hybrid AI later.
- Local tools should support later teacher workflows without requiring cloud databases on Day 1.
- Terminal environment uses zsh with Starship, Zoxide, Atuin, Eza, Bat, FZF, Ripgrep, UV, LLM, and Fabric.
- Local AI memory is shared unified memory.
- Avoid running multiple large models in Ollama and LM Studio at the same time.
- Use `aiflush` before heavy coding/model switching if memory pressure is high.

## Assistant Agent Priority

- The Teacher AI Chief of Staff is the primary post-Phase-0 product.
- It is teaching-first.
- It supports lesson ideas, project memory, writing style, app development, and troubleshooting.
- It coordinates with a future 3D Design Agent later.
- It is permission-based.
- It is local-first where possible.
- It must not autonomously send, publish, modify, or delete without approval.

## Future 3D Design Agent Readiness

- 3D printing is both classroom/hobby and business work.
- Bambu Studio is the default slicer.
- OpenSCAD is the initial AI-friendly CAD path.
- Future 3D Agent should support business products, classroom fidgets/prizes, product memory, print QA, Bambu Studio verification, and copyright/IP/reference warnings.
- Personal/reference designs must stay separate from commercial products.
- The 3D Agent is advisory only and cannot block or stop prints.

## Phase 0 boundary

Phase 0 is setup only.

Phase 0 intentionally avoids the React app, Canvas tools, agents, Docker, Supabase, Firestore, MongoDB, and production classroom content workflows.

## Future worksheet and print requirements

- Worksheet outputs must include answer keys later.
- Worksheet outputs must use smart/logical page breaks later.
- Generated printable outputs must be tested against browser print preview and physical Ricoh print certification later.
