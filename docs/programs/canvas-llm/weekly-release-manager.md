# Canvas Weekly Release Manager

The weekly release manager is the owner-facing package for one instructional week. It discovers the week, assembles the staged drafts, and asks for one approval. Publication remains `rollover.execute` through `scripts/canvas_llm_deploy/weekly_release.py`. There is no second Canvas writer.

## Workflow

1. Discover the academic year, quarter, and week from `config/curriculum/canvas/instructional-weeks-2026-2027.json`.
2. A date outside an instructional week selects the next week. A gap that contains a weekday is reported as an instructional break. An ordinary weekend is not. The manager does not invent lessons, holidays, or newsletter text.
3. Build the release from the staged intake packet: Math, Reading/Spelling, Language Arts, the quarter's rotating subject, and Homeroom.
4. Review one package: source hash, agenda hash, plan fingerprint, dates, and each artifact as CREATE, UPDATE, SKIP, or BLOCKED.
5. Approve with the exact phrase `APPROVE Q2W5`. That phrase writes the existing granular approval records. It does not approve a different week or a changed draft.
6. Publish with the exact phrase `ROLLOVER Q2W5` and `--production`. The manager checks hashes, records the week-scoped authorization, runs read-only preflight, then calls the rollover engine. The engine finalizes, writes the rollover ledger, and Chief of Staff reads that evidence back.

Assessment date, first-notice time, reminder time, weekly announcement time, and a late owner-selected time stay separate. A passed Friday 4:00 PM America/New_York window requires an owner time. It does not move an assessment date.

## Commands

```bash
bin/chief-of-staff --canvas-weekly-release --status
bin/chief-of-staff --canvas-weekly-release --prepare --week q2w5
bin/chief-of-staff --canvas-weekly-release --review --week q2w5
bin/chief-of-staff --canvas-weekly-release --review --week q2w5 --live-readonly
bin/chief-of-staff --canvas-weekly-release --approve --week q2w5 --confirm "APPROVE Q2W5" --owner-time 2026-11-08T05:01:00Z
bin/chief-of-staff --canvas-weekly-release --publish --week q2w5 --confirm "ROLLOVER Q2W5" --production
```

`--publish` without `--production` stops before any Canvas client is constructed. `--live-readonly` is GET-only and still requires the week authorization before credentials are read. `--status`, `--prepare`, and `--review` do not approve or publish.

The existing commands stay in place:

```bash
bin/canvas-weekly-rollover
bin/chief-of-staff --friday-rollover-status
```

## Recovery

| State | Meaning | Resume |
| --- | --- | --- |
| `NOT_STARTED` | No intake manifest | Prepare the week through intake |
| `PREPARED` | Staged, not yet approved | Review |
| `AWAITING_APPROVAL` | Source exists and approval is pending | Approve the current hashes |
| `APPROVED` | Granular approval matches the current plan | Preflight, then publish |
| `PREFLIGHT_BLOCKED` | A gate failed before publication | Fix the named blocker; no success ledger |
| `PARTIALLY_PUBLISHED` | The rollover stopped after a failed write or finalizer | Rerun the same command; completed readback is skipped |
| `PUBLICATION_VERIFIED` | Publication ledger verified | Finish the rollover record |
| `ROLLOVER_INCOMPLETE` | Intake and publication ledger agree; rollover record does not | Rerun; Canvas is not written again |
| `FULLY_COMPLETED` | Intake, publication ledger, and rollover ledger agree | Rerun reports already complete |

A changed page, assignment, announcement, source hash, or plan fingerprint invalidates its approval. The package returns to review.

## Adding a future week

Stage the week with the existing intake command and the instructional-week calendar. Add the subject drafts, assessment notices, assignments, Homeroom page, and family announcement. Then use the commands above. Do not create a new publisher or a one-off prompt per subject.

## Troubleshooting

- `publication time must be a future timezone-aware instant`: choose the next America/New_York calendar day. Do not reuse a Friday that has passed.
- `homeroom page content is missing` or `homeroom family announcement is missing`: stage both files. The manager will not draft them.
- `manifest source hash does not match`: the rollover package and the intake manifest describe different content. Rebuild; do not copy the agenda hash into `source_hash`.
- `BLOCKED: weekly publication requires --production`: the preview commands are working. Live publication is a separate explicit command.
- A `BLOCKED` reconciliation row for a duplicate title needs a teacher choice. The manager will not pick between two Canvas objects.
