# Teacher AI Chief of Staff

The Teacher AI Chief of Staff is the first major product after Phase 0.

It is a local-first, permission-based assistant that helps Owen plan, search, remember, draft, organize, troubleshoot, and make decisions across teaching, app development, projects, files, and writing.

## Primary focus

- Teaching
- Lesson support
- Project memory
- Writing style
- Planning
- Guided troubleshooting

## Secondary support

- App development
- Technical debugging
- Future 3D printing coordination

## Future approved sources

The assistant may eventually connect to these sources only after explicit approval:

- User-selected local files
- Approved local folders
- Obsidian vault
- Approved Google Drive folders
- Selected Gmail labels or email exports
- GitHub repositories
- Generated Teacher OS artifacts
- Future 3D agent/project files

## Not allowed yet

The assistant must not:

- Silently ingest everything
- Scan all Drive or Gmail
- Access student-sensitive data without explicit approval
- Send emails
- Publish Canvas content
- Control the desktop
- Run background automations
- Modify or delete files without confirmation

Phase 1A is documentation, safety, and training architecture only. It does not build the React app, local API, connectors, MCP servers, autonomous agents, desktop control, or real data ingestion.

## Memory

Phase 1C adds inspectable Markdown memory in `assistant/memory/`.

Memory is explicitly included by CLI flags. It should not contain sensitive student, parent, or confidential data.

Memory supports project continuity, writing style, preferences, teaching context, decisions, and active priorities.

Use `bin/chief-of-staff --memory-status` and `bin/chief-of-staff --validate-memory` before important memory-assisted runs.

`assistant/memory/memory-log.md` records meaningful memory changes.
