# Phase L.5F Grounding Contract

Phase L.5F diagnoses the Phase L.5E grounding rejection and aligns the future
model response with deterministic validation. It performs no model execution.

## Forensic limit

The rejected L.5E candidate was not retained. Its exact violation is therefore
unknown and must not be reconstructed or guessed. Deterministic inspection can
identify the likely mismatch surface: the v1 contract required exact prose and
several nested records even though the model's role was only explanation.

## Existing v1 contract audit

`schemas/local-model-response.schema.json` remains the v1 prose-oriented
contract. It requires:

| Collection | v1 requirement |
| --- | --- |
| known claims | Every entity summary appears at least once and is copied exactly; paraphrases fail. Each claim cites one or more context evidence IDs. |
| evidence claims | Every evidence `claim`, identity, and confidence appears at least once and is copied exactly. |
| unknown claims | Every uncertainty appears at least once and is copied exactly, with no evidence and `unknown` confidence. |
| confidence | The complete context confidence array copied exactly. |
| authority | The complete authority-context array copied exactly. |
| review state | The complete review-state array copied exactly. |
| relationships | No relationship claim type exists. Relationship prose can pass only when it is already an exact evidence claim. |
| actions/access | Actions, recommendations, permissions, and access claims are empty. |

Evidence citations are IDs, not prose. The prompt required known claims to cite
every supplied evidence ID, but the v1 validator required only a nonempty valid
subset. Evidence claims cite their one matching evidence ID. Claim ordering was
not enforced, and duplicate grounded claims were not prohibited; copied
confidence, uncertainty, authority, and review arrays did require exact order.
These prompt/schema/validator differences were real ambiguity even though all
paths remained fail closed. The controlled context currently contains one entity, five evidence
items, four uncertainties, six confidence entries, six review-state entries,
one authority entry, and three relationships.

The L.5E prompt communicated most exact-copy rules, but it left the model to
generate claim objects, claim IDs, exact prose, citations, nested copied arrays,
and partly implicit cardinality simultaneously. Relationships were present in
context but had no response claim type, which added another implicit boundary.
That wide and partially inconsistent generation surface most likely caused the
rejection. This is an architectural likelihood, not a claim about the unretained
response.

## Versioned v2 contract

`schemas/local-model-response-v2.schema.json` is a separate closed-reference
contract. The v1 schema and validator remain available and unchanged for Phase
L.5D compatibility.

The v2 model output contains no trusted factual prose. It selects stable IDs:

```json
{
  "schema_version": 2,
  "response_id": "local-model-response-v2:application-concept:grade-4-writing-launcher",
  "request_id": "local-model-request:application-concept:grade-4-writing-launcher",
  "context_id": "ai-context-package:application-concept:grade-4-writing-launcher",
  "task": "explain",
  "subject_ref": "application-concept:grade-4-writing-launcher",
  "known_refs": ["known:001"],
  "evidence_refs": ["evidence:001", "evidence:002", "evidence:003", "evidence:004", "evidence:005"],
  "uncertainty_refs": ["uncertainty:001", "uncertainty:002", "uncertainty:003", "uncertainty:004"],
  "relationship_refs": [],
  "confidence": "high",
  "authority": "unknown",
  "review_state": "unreviewed",
  "action_authority": "none",
  "actions": [],
  "recommendations": [],
  "permissions": [],
  "access_claims": []
}
```

## Cardinality

| Field | Cardinality |
| --- | --- |
| `subject_ref` | Exactly the one supplied subject |
| `known_refs` | Exactly all supplied known refs, once each |
| `evidence_refs` | Exactly all supplied evidence refs, once each |
| `uncertainty_refs` | Exactly all supplied uncertainty refs, once each |
| `relationship_refs` | Exactly zero; relationship generation is excluded |
| confidence/authority/review state | Exact supplied enum |
| action authority | Exactly `none` |
| actions/recommendations/permissions/access | Exactly zero |

Order is deterministic in the supplied vocabulary and ideal response. Validation
requires exact membership and count, not a model-authored semantic ordering.
Duplicate refs fail. IDs cannot be combined or invented. Labels and prose cannot
be inferred by the model.

## Closed vocabulary and renderer

`build_response_vocabulary()` assigns deterministic `known:NNN`,
`evidence:NNN`, and `uncertainty:NNN` references. Only public selection fields
enter the prompt; private lookup maps remain inside the deterministic process.

After validation, `render_validated_explanation_v2()` resolves those references
against the original validated `AIContextPackage`. The renderer—not the
model—owns factual wording. A rejected response cannot be rendered.

## Safe diagnostics

`GroundingValidationResult` reports only a finite violation code, a structural
JSON pointer, and an expected source type. It never includes a rejected value.
The code set is:

- `KNOWN_CLAIM_MISSING`, `KNOWN_CLAIM_UNSUPPORTED`
- `EVIDENCE_CLAIM_MISSING`, `EVIDENCE_CLAIM_UNSUPPORTED`, `EVIDENCE_COUNT_MISMATCH`
- `UNCERTAINTY_MISSING`, `UNCERTAINTY_UNSUPPORTED`, `UNCERTAINTY_COUNT_MISMATCH`
- `AUTHORITY_CHANGED`, `REVIEW_STATE_CHANGED`, `CONFIDENCE_CHANGED`
- `RELATIONSHIP_UNSUPPORTED`
- `ACTION_CONTENT_PRESENT`, `RECOMMENDATION_CONTENT_PRESENT`
- `ACCESS_CLAIM_PRESENT`, `PERMISSION_CLAIM_PRESENT`
- `UNKNOWN_RESPONSE_FIELD`, `MISSING_REQUIRED_FIELD`, `INVALID_ENUM_VALUE`
- `DUPLICATE_REFERENCE`, `IDENTITY_MISMATCH`, `INVALID_STRUCTURE`

Diagnostics are in memory, non-persistent, and explicitly record that raw output
and hidden reasoning were not retained. They do not repair or normalize output.

## Prompt/schema consistency

The v2 prompt rules and cardinality metadata are shared constants. The
consistency validator checks required fields, reference uniqueness, empty
capability collections, and an explicit prompt rule for every contract field.
Schema and prompt disagreement fails before a future model request.

## Security and deferred runtime

Loopback, exact-model, one-task, one-attempt, timeout, no-tool, no-vision,
no-proxy, no-fallback, no-action, no-persistence, and no-source-access controls
remain unchanged. Phase L.5F does not call or inspect Ollama. A second live
attempt is deferred to a separately authorized phase.
