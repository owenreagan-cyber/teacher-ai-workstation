# Teacher Knowledge Vault — Intake-to-Vault Approval Gate

Last updated: 2026-07-04

```text
Status: planning-only
Automatic intake promotion: blocked
Vault write runtime: blocked
Student data: blocked — absolute
```

## Purpose

Define the **human approval gate** before any candidate intake material may be promoted into Teacher Knowledge Vault. M0 freezes this gate as documentation only — no promotion runtime exists.

## Promotion Chain (Inactive)

```text
intake candidate → review decision → approved-context (optional) → [Owen gate] → knowledge vault file (blocked)
```

See `assistant/intake/intake-policy.md` for intake review outcomes. Vault promotion is a **separate** step from approved-context listing.

## Required Checks Before Future Promotion

| Check | Requirement |
| --- | --- |
| Intake reviewed | Item has approved or approved-after-sanitizing decision |
| Sanitization | No student names, parent info, grades, or confidential records |
| Summary-only | Reference summary — not raw file copy or full Drive dump |
| Source traceability | Intake item ID or approved-context reference recorded |
| Owen confirmation | Explicit approval to create vault file |
| Privacy review | Matches `assistant/memory-policy.md` Knowledge Vault row |

## Blocked Promotion Sources

- raw intake folders
- unreviewed quarantine material
- full Gmail or Drive exports
- copyrighted content copied in full
- proprietary school materials without approval
- automatic classifier or AI summarizer output without human review

## Fake Fixture Reference

`assistant/teacher-knowledge-vault/samples/fake-intake-promotion-record.json` models a fictional promotion record with `"vault_promotion_approved": false` and `"runtime_approved": false`.

## Future Runtime (Blocked)

No command such as `--promote-intake-to-vault` exists. Any future promotion workflow requires:

1. Separate Owen mission per `docs/implementation-approval-gate.md`
2. Manual file creation per `docs/teacher-knowledge-vault/manual-entry-plan.md`
3. Update to `assistant/memory/memory-log.md`

## Proof

```bash
bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status
```
