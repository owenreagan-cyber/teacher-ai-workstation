# Resource Registry Schema

Phase 25 uses a synthetic, committed registry schema for canonical resource identity.

Required identity fields:

- `resourceId`
- `canonicalName`
- `subject`
- `resourceType`
- `verificationStatus`
- `availabilityStatus`
- `visibility`
- `deploymentPolicy`
- `canvasStatus`

Supported optional fields:

- `program`
- `grade`
- `lessonRef`
- `lessonNumber`
- `assessmentNumber`
- `unit`
- `chapter`
- `applicability`
- `sourceProvider`
- `sourceReference`
- `contentHash`
- `filename`
- `fileSize`
- `modifiedAt`
- `notes`
- `provenance`
- `revision`
- `aliases`

Applicability remains structured and deterministic. It may describe exact lesson numbers, lesson ranges, parity, assessment families, subject-wide reusable resources, curriculum-sequence reuse, week-specific entries, or occurrence-only records.
