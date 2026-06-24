# What This Is Not

This document defines boundaries for the Teacher AI Workstation so the system does not quietly expand into something unsafe or unclear.

## Not an autonomous agent with unrestricted access

This workstation is not designed to give an AI agent unrestricted access to the Mac, accounts, browser sessions, files, secrets, printers, or external services.

The goal is supervised capability, not uncontrolled autonomy.

## Not a password manager

1Password is the password manager.

This repository must not store:

- Passwords.
- API keys.
- Recovery codes.
- Passkeys.
- Tokens.
- MFA codes.
- 1Password account recovery information.

The repo may document where secrets belong, but it must not contain the secrets.

## Not a school IT management system

This workstation may support Owen's teaching workflow, but it is not a replacement for school-managed systems, device management, or IT policy.

It should not attempt to override school policy or manage school infrastructure.

## Not a student data system

This repository must not become a database for:

- Student records.
- Grades.
- Parent information.
- Behavior notes.
- Medical information.
- Accommodation information.
- Confidential school documents.

Student-related data should remain in approved school systems.

## Not a production server

This Mac and repository are for workstation setup, development, teaching support, and local automation. They are not a production hosting environment.

Do not treat local scripts as production services unless a future phase explicitly designs and approves that.

## Not a replacement for human review

The workstation can assist with planning, setup, coding, documentation, 3D design readiness, and status checks. It does not replace human judgment.

Human review remains required for:

- Account access.
- Secrets.
- Paid services.
- Student data.
- Commercial product decisions.
- Physical printing.
- Safety-sensitive designs.
- External sharing.

## Not a print-ready 3D design authority

AI-generated 3D files must not be called print-ready by default.

Approved wording:

- Slicer-ready pending human verification.
- Ready for Bambu Studio review.
- Needs geometry/dimension/support/color/IP/safety review.

Not approved wording:

- Print-ready.
- Sale-ready.
- Commercially safe.

unless the required human checks have actually happened.

## Not a place for invisible automation

The system should not silently change settings, create accounts, retrieve secrets, configure apps, or run destructive operations.

Every meaningful action should be either:

- Review-only.
- Explicitly approved.
- Reported clearly after completion.