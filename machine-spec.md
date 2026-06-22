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

## Phase 0 boundary

Phase 0 is setup only.

Phase 0 intentionally avoids the React app, Canvas tools, agents, Docker, Supabase, Firestore, MongoDB, and production classroom content workflows.

## Future worksheet and print requirements

- Worksheet outputs must include answer keys later.
- Worksheet outputs must use smart/logical page breaks later.
- Generated printable outputs must be tested against browser print preview and physical Ricoh print certification later.
