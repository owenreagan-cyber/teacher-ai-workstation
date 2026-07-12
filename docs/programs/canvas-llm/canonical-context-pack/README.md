# Canvas LLM Canonical Context Pack

This directory is the authoritative 2026–2027 context pack for the Teacher AI Workstation Canvas LLM builder.

Purpose:

- define the current owner-approved product rules;
- index canonical curriculum maps and configuration;
- define teacher input and Canvas output contracts;
- record naming conventions, calendar logic, resource rules, announcement rules, newsletter rules, approval rules, and publishing sequence;
- compare legacy applications against current canonical behavior;
- preserve unresolved owner decisions explicitly;
- provide one validated source bundle for Claude, Copilot, Cursor, or future coding agents.

This is a single-user, local-first teacher workstation.

It is not:

- a district platform;
- a multi-tenant SaaS product;
- a Supabase or Firebase application;
- a student information system;
- an autonomous ungated Canvas publisher.

Canonical precedence:

1. current owner-approved 2026–2027 rules;
2. current canonical config under `config/curriculum/`;
3. current validators and deterministic rule engines;
4. current read-only Canvas metadata;
5. validated historical behavior;
6. legacy application evidence;
7. fixtures and prototype behavior.

Legacy behavior must never silently override current rules.
## Validation status

```text
Status: validated
Product mode: single-user-local-first
School year: 2026-2027
```

Validation command:

```bash
bin/chief-of-staff --canvas-llm-canonical-context-pack-status
```

The validation gate confirms:

- all 20 required Markdown contracts are present and non-empty;
- the manifest is valid and marked `validated`;
- the editable SQLite weekly model is the production source of truth;
- synthetic fixtures remain test-only;
- standalone Reading and standalone Spelling announcements are allowed;
- Reading and Spelling announcements combine only when both assessments occur in the same canonical instructional week;
- Reading Test 14 has no Checkout 14;
- Spelling Test 25 remains owner-source-required;
- resource visibility and assessment-security rules remain enforced;
- Phase 27 comparison, approval, dependency, ledger, transport, and read-back safety remain authoritative;
- export is not Canvas publication;
- ignored legacy apps remain evidence only.

## Recovery boundary

This Context Pack is the canonical input contract for subsequent Canvas LLM recovery and convergence work.

It does not itself:

- modify Phase 22–27 runtime behavior;
- authorize Canvas writes;
- resolve outstanding owner decisions;
- promote synthetic fixture data into production;
- promote ignored legacy applications into the tracked implementation.

The next implementation gate is a no-write convergence audit followed by one real-SQLite Math vertical slice.
