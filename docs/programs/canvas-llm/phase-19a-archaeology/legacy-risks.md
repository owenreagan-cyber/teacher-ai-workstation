# Canvas LLM Phase 19A Legacy Risks

## Status

Analysis-only risk register.

## Risk Scale

```text
HIGH = likely to cause unsafe writes, wrong Canvas content, privacy exposure, or lost teacher logic
MEDIUM = likely to cause drift, confusion, duplicate work, or bad previews
LOW = manageable documentation or cleanup risk
```

## Risk Register

| Risk | Level | Evidence | Impact | Recommendation |
|---|---:|---|---|---|
| Old Canvas pages treated as automatically correct | HIGH | Historical metadata and old generators | Future pages may preserve outdated formats | Treat old pages as evidence only; apply FPK guidelines and owner-approved rules. |
| Missing `pacing-sync-pilot` repo | MEDIUM | Availability check found missing directory | Potential evidence gap | Treat as unavailable unless Owen provides checkout/archive. |
| Hardcoded historical course IDs | HIGH | Legacy constants/course maps | Future writes could target old courses | Use approved manifest/governed config only. |
| Direct Canvas mutation functions | HIGH | deploy pages/assignments/announcements, sync services | Accidental Canvas changes | Keep blocked until explicit write gate. |
| File rename/move automation | HIGH | Orphan sweeper/resource/file organizer concepts | Could corrupt file organization | Preview-only first; future one-operation human-approved gate. |
| Standalone Spelling announcement generation | HIGH | Conflicts with Together Logic | Duplicate/confusing parent communication | Block standalone Spelling announcements. |
| Study Guide grading conflict | HIGH | Legacy 100 percent/omit vs owner 0 points/exclude | Gradebook impact | Use owner-approved rule only. |
| Assignment title drift | HIGH | Multiple old builders/formats | Duplicate assignments or failed matching | Canonical title table and alias mapping required. |
| AI classification overreach | HIGH | AI missing-assets / file classify concepts | Hallucinated resources | Deterministic checks first; AI advisory only. |
| Newsletter birthdays/private data | HIGH | Newsletter features include birthday handling | Student privacy exposure | Separate approval; local-only until reviewed. |
| Page generator extra content | MEDIUM | Old generators add notes/fallbacks | Violates simplicity | Constrain to FPK/current owner rules. |
| Inline style / CIDI uncertainty | MEDIUM | Legacy Canvas HTML generators | Inconsistent Canvas output | Define style policy before generation. |
| Current target courses empty shells | MEDIUM | Phase 18 metadata | Setup requires staged process | Preview relationship/action packets before write. |
| History/Science assignment drift | MEDIUM | Historical assignments vs page-only preference | Unwanted assignments | Only generate assignments when explicit exception exists. |
| Teacher Memory overreach | HIGH | Memory resolver can influence output | Learned mistakes become rules | Memory never overrides safety/canonical rules. |
| Canvas Brain pattern overreach | MEDIUM | Pattern suggestions from snapshots | Legacy formats promoted | Keep suggestions classified until reviewed. |
| Old prompt rules treated as authority | MEDIUM | Gemini/prompt helper logic | Prompt drift becomes system rule | Prompts are low authority; tables decide rules. |
| Publish/front-page changes | HIGH | Legacy deploy assumptions | Silent publish changes | Separate publish gate required. |

## Highest Priority Mitigations

1. Establish canonical rule tables before implementation.
2. Keep Canvas writes disabled.
3. Separate historical evidence from current target authority.
4. Use approved manifest/governed config for course IDs.
5. Hard-lock Reading/Spelling Together Logic.
6. Hard-lock Friday rules.
7. Resolve Power Up and Fact Test maps before generation.
8. Keep file operations preview-only.
9. Keep AI advisory-only.
10. Build Medical Center diagnostics before write features.

## Safety Boundary

This risk register does not authorize:

- Canvas writes
- live Canvas fetches
- file operations
- app implementation
- refactors
- migrations
- generation
