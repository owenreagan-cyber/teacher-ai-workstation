# Phase 1A Chief of Staff Safety and Training Prompt

Use this prompt to recreate or review the Phase 1A documentation layer.

## Task

Create the safety, training, and workflow foundation for the Teacher AI Chief of Staff before any app implementation.

This is a planning/docs architecture task only. Do not build React, local APIs, connectors, Canvas tools, autonomous agents, MCP servers, desktop-control agents, Docker, Supabase, Firestore, MongoDB, or real data ingestion.

## Product definition

The Teacher AI Chief of Staff is a local-first, permission-based assistant that helps Owen plan, search, remember, draft, organize, troubleshoot, and make decisions across teaching, app development, projects, files, and writing.

Teaching is primary. App development, troubleshooting, project planning, writing style, and future 3D printing coordination are secondary support areas.

## Required policies

- Role and behavior policy
- Memory policy
- Permissions model
- Source map
- Writing style profile
- Failure and recovery policy
- Sensitivity rules
- Model routing

## Confidence scale

High:

- Retrieved directly from an approved source file in this session.
- Source is available and can be cited or named.
- Minimal inference required.

Medium:

- Inferred from approved context with reasonable confidence.
- Source context exists, but the assistant is connecting or summarizing ideas.

Low:

- Generated from base model knowledge only.
- No approved source was provided.
- Must be treated as unverified.

Unknown:

- The assistant cannot determine the source.
- Treat as unverified.
- Ask for source material or confirmation before use.

## Raw inbox warning

`assistant/training/writing-samples/raw-inbox.md` must include:

This file must never be automatically loaded as assistant context. It is a staging area only. Content moves to approved-samples.md only after manual human review.

Approved samples are the only samples used for writing style.

## Eval prompt regression suite

Create 5-10 standard eval prompts covering:

- Parent email draft
- Student-facing explanation
- Lesson idea
- Project review
- Troubleshooting help
- Request for training materials
- Sensitivity escalation
- "I don't know / no source" behavior
- Future 3D coordination handoff

Run these after major changes to writing style, role docs, workflows, or memory docs.

## Monthly review structure

The monthly review must include:

- Shadow mode comparison scores from the past month
- Feedback log patterns
- What got edited most often
- New approved samples added
- Prompt/context changes made
- Observed effect of those changes
- One specific improvement to implement next month

## 3D coordination placeholder

Do not build the 3D Design Agent yet.

The Chief of Staff can currently handle project notes, vendor research notes, scheduling, priority planning, collecting design ideas, and deciding whether a task should be routed to the future 3D agent.

Future 3D agent tasks include design files, filament specs, printer/slicer settings, OpenSCAD/CadQuery code, product pricing, print-failure diagnosis, prototype logs, product listing drafts, copyright/IP checks, classroom fidgets/prizes, and business product ideas.

Future handoff protocol:

1. Classify request.
2. Check personal/classroom/business mode.
3. Gather required inputs.
4. Identify safety/IP concerns.
5. Pass structured design brief to 3D agent.
6. Receive summary back into project memory.

## Standard workflow footer

Every workflow should end with:

- Sources used
- Known facts
- Assumptions
- Verify before use
- Confidence
- Next action
