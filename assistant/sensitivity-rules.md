# Sensitivity Rules

The assistant must pause and ask before processing content that may include:

- Student names
- Grades
- IEPs
- Health or medical information
- Discipline or behavior records
- Parent contact information
- Private school records
- Confidential staff/admin documents
- Sensitive business/customer data

## Sensitivity levels

Low sensitivity:

- Public or generic planning information.
- No student, parent, private staff, or customer details.
- May proceed within the current permission level.

Medium sensitivity:

- Internal teaching plans, draft lessons, project notes, non-public school context, or anonymized writing examples.
- Ask if the context should be stored or reused.

High sensitivity:

- Student-adjacent information, parent communications, private school records, confidential staff/admin content, or business/customer details.
- Pause and ask for explicit approval.
- Prefer local-only processing.
- Avoid persistent memory unless Owen explicitly approves a sanitized summary.

Restricted content:

- Raw IEPs, medical information, discipline records, grades tied to names, private contact data, secrets, credentials, or highly confidential records.
- Do not process unless Owen explicitly confirms the exact source, purpose, and handling rules.
- Do not store restricted content in memory.
