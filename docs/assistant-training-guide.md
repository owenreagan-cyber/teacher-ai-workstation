# Assistant Training Guide

This guide explains how Owen should train the Teacher AI Chief of Staff without broad private-data ingestion.

## Recommended training path

1. Collect 10 approved writing samples.
2. Anonymize them.
3. Add only approved examples to `assistant/training/writing-samples/approved-samples.md`.
4. Use contrastive pairs to show what to avoid and what to prefer.
5. Run shadow mode before trusting new workflows.
6. Keep the feedback log updated.
7. Run a monthly meta-trainer review.
8. Run `assistant/training/eval-prompts.md` after major context changes.
9. Use `assistant/workflows/request-training-materials.md` when the assistant needs better examples.
10. Avoid full-drive and full-inbox scanning at first.

## Writing sample rules

- Use real examples only after anonymization.
- Do not include student names, grades, IEPs, discipline details, parent contact info, private school records, or confidential staff/admin documents.
- Raw samples go in `raw-inbox.md` only for review.
- Approved samples are the only samples used for writing style.

## Monthly improvement rhythm

Each month, review:

- Shadow mode comparison scores
- Feedback log patterns
- What Owen edited most often
- New approved samples
- Prompt/context changes
- Observed effect of those changes
- One specific improvement to implement next month

## Safety reminder

Training should make the assistant more teachable before making it more powerful.

## Training with the Phase 1B CLI

Use the CLI to train the assistant safely:

- Run `bin/chief-of-staff --workflow request-training-materials --question "What should I give you first?"`.
- Add approved writing samples manually after anonymization and review.
- Run `--dry-run` before real model calls.
- Use `--show-context` to confirm exactly what files are included.
- Use `--status` to debug setup.
- Run `assistant/training/eval-prompts.md` after context changes.
- Update `assistant/training/feedback-log.md` after outputs are used, edited, or rejected.
