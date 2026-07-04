# Vibe / Wallpaper / Widgets Planning Gate

Last updated: 2026-07-04

```text
Status: documentation/status/tests only
Closure: complete_vibe_wallpaper_widgets_planning_gate_program
Runtime approval: none
Install approval: none
Mac system changes: blocked
Authority: planning gate for visual environment ideas; does not override repo safety gates
```

## Purpose

This gate defines what "vibe" means for Teacher AI Workstation and keeps visual-environment ideas in a safe planning lane. It covers wallpaper concepts, widget concepts, shortcut concepts, teacher dashboard visual direction, classroom utility visual language, and future 3D workshop direction without installing, executing, or changing anything on the Mac.

## What Vibe Means Here

Vibe is the local teacher workstation's visible working posture: calm enough for repeated daily use, lively enough to make classroom prep feel welcoming, and practical enough to support quick decisions before and during class.

Vibe is not a runtime shell, wallpaper changer, widget installer, shortcut runner, or Mac automation layer. Vibe is a planning language for future approved surfaces.

## Approved In This Lane

- Planning docs and gate docs.
- Fake/local illustrative examples.
- Static concept descriptions and text wireframes.
- Read-only status proof.
- Tests that verify the lane remains planning-only.
- Cross-links in command, dashboard, roadmap, coherence, proposal, and capability-map surfaces.

## Blocked In This Lane

- Widget installation.
- Shortcut installation or execution.
- Wallpaper changes.
- Mac system changes.
- Homebrew installs.
- App execution.
- Executable HTML/CSS/JS pages or runtime visual shells.
- External APIs, OAuth, network integrations, Drive/NAS/iCloud/Canvas access.
- Folder scanning, OCR, embeddings, RAG, AI generation/runtime behavior, local model/Ollama execution.
- Student data, real curriculum ingestion, copied textbook/worksheet/test/answer-key content.
- Production registry writes, active `--write`, writer scripts, or a second production registry record.

## Chief Of Staff Role

Chief of Staff may report the planning status of this lane and verify that required docs, fake examples, and safety boundaries exist. Chief of Staff must not install widgets, install shortcuts, run shortcuts, change wallpaper, launch visual apps, change macOS settings, call external services, or create runtime artifacts.

## Future Approval Gate

Any future runtime/install mission must be separately approved by Owen. That mission must name the exact artifact, exact allowed action, allowed path, rollback plan, validation commands, and blocked behavior. Planning docs and fake examples never count as runtime approval.

## Evidence

- Teacher vibe brief: `docs/vibe-wallpaper-widgets/teacher-workstation-vibe-brief.md`
- Wallpaper concepts: `docs/vibe-wallpaper-widgets/wallpaper-concept-plan.md`
- Widget concepts: `docs/vibe-wallpaper-widgets/widget-concept-plan.md`
- Shortcut concepts: `docs/vibe-wallpaper-widgets/shortcut-concept-plan.md`
- Visual workshop concepts: `docs/vibe-wallpaper-widgets/visual-workshop-concept-plan.md`
- Runtime/install gate: `docs/vibe-wallpaper-widgets/runtime-install-approval-gate.md`
- Fake examples: `assistant/vibe-wallpaper-widgets/samples/`
- Status proof: `bin/chief-of-staff --vibe-wallpaper-widgets-planning-status`
