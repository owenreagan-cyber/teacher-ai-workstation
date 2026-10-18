# Personal Workspace Intelligence Authority Boundary

## Ownership

| Domain | Owner |
| --- | --- |
| Curriculum source content | Subject repositories |
| Production classroom resources | Resource Registry projection |
| Curriculum asset identity and representations | Teacher Knowledge Vault |
| Software project state | Project Registry |
| Application concepts and installed-instance records | Application Registry |
| Storage locations and policy | Storage Registry |
| Future file observations | Personal Workspace Intelligence |
| Cross-domain relationships | Personal Workspace Intelligence |
| Recommendations | Chief of Staff |
| Capabilities, approvals, and audit requirements | Permission/Approval system |
| Future actions | Separately approved action gateway |

Workspace Intelligence references records owned elsewhere. It never silently
copies ownership, promotes an observation to authority, or overwrites an owning
system.

## Authority

Authority is scoped. `authority_role: canonical` is invalid without an
`authority_scope` and a subject. Supported roles are canonical, deployment,
mirror, backup, archive, and unknown. Supported scopes are source_code,
curriculum_binary, registry_metadata, classroom_deployment, backup_recovery,
and application_bundle.

A representation can be canonical for one scope and noncanonical for another.
Newer does not mean canonical. A backup does not become canonical because of a
timestamp. A deployment is not source-code, curriculum-binary, or registry-
metadata authority. Unknown is preferred to an unsupported claim. Conflicting
canonical claims for one subject and scope fail validation.

## Identity

Physical observation, logical resource, representation, and instructional
context identities are independent. Paths are never global logical-resource
identities. Hash equality, when hashing is separately approved in a future
phase, establishes equal bytes rather than equal authority or purpose.

## Static policy boundary

Phase B declares policy only. Locator references are symbolic and are not
resolved. No connection state asserts a live observation. Project records do
not contain Git observations. Application records contain concepts only and no
installed instances.

Permanent prohibitions in this phase include filesystem enumeration, content
reads, hashing, application inspection or launch, Git inspection, cloud or
backup connection, inventory generation, recommendations from real data, file
mutation, AI, OCR, embeddings, and background watchers.

`/Users/owen` is permanently prohibited as a recursive scan root. Future
discovery can operate only on an explicitly approved source and subtree under
a separately approved mission.

## Phase C observation boundary

Phase C adds schemas and policies for future host-local evidence. It creates no
observation store and performs no observation. Inventory-run approval grants
scope only to a future bounded run; it does not grant authority to observed
items. Observation snapshots must declare `authority_claim: none`.

Recommendations remain non-actions. They cannot approve, plan, or execute a
mutation. The cloud-agent view remains disabled, and its future contract admits
only sanitized projections after classification, redaction, validation, and
audit gates. Retention age has no authority effect and never authorizes deletion.

Phase E keeps the project concept (`project:history`), physical observation, and
local Git representation as separate identities. Repository presence, branch,
HEAD, and dirty metadata are evidence only. They do not determine importance,
activity, production status, abandonment, or canonical authority.

Phase F also separates the Grade 4 Writing application concept, installed
instance, and physical observation. Bundle existence, display name, identifier,
version, and content type are metadata evidence only. Discovery does not grant
launch, execution, installation, update, signing, private-data, or application
management authority.

Phase G connects only identities already evidenced by the approved Phase D, E,
and F artifacts. A relationship is a reviewable assertion with an evidence
package, not an ownership transfer or authority claim. `observed` never means
authoritative; `inferred` never means true; owner and registry assertions require
their own explicit evidence. Conflicts remain unresolved, drift preserves the
prior relationship, and no relationship can create permissions or actions.

Phase H treats recovery candidates as review opportunities, never restoration
authority. Backup, mirror, and archive contexts retain those roles; a timestamp
cannot promote any candidate to canonical. Candidate confidence describes the
evidence, not ownership. Recovery recommendations can request review only and
have `action_state: not_an_action`. Live missing-resource detection and recovery
execution remain disabled.

The Phase H enhancement keeps confidence and recovery risk independent. High
confidence can coexist with medium or high risk when authority, age, sensitivity,
provenance, relationships, or scope remain uncertain. Shared evidence packages
always have `authority_effect: none` and `permission_effect: none`. An
`expected_artifact_of` relationship states an expectation only and never claims
present availability.

Phase I produces only a sanitized, read-only compatibility projection. It
preserves reported authority—including `unknown`—but cannot create or change it.
The projection is metadata-only, non-authoritative, non-executable, and contains
no action capabilities. No local or cloud AI connection is enabled.

Phase J adds a deterministic explanation layer over two static registries and
the exact approved Phase D/E/F/G artifacts. Queries and scopes filter existing
assertions only; they cannot strengthen confidence, complete unknown authority,
approve review state, or create permission. Every explanation and query response
has `action_authority: none`. Restricted records require the explicit
`workspace.restricted.read` grant, and unknown classification never silently
qualifies as teacher-only, student-safe, or restricted.

Phase K formats Phase J results for a human and creates no new intelligence.
Interface health labels, review-queue placement, presentation order, and review
state do not create or change source authority. A recommendation remains
`not_an_action`; the interface cannot approve it, persist a decision, or execute
it. Review states and confidence are independent dimensions. Every human view
ends with an explicit statement that no action is available.

Phase L defines AI as a future reasoning consumer of a sanitized explanation,
never a source of truth or authority. AI output cannot promote inference to
fact, inflate confidence beyond cited evidence, change authority, grant a
permission, approve recovery, or execute an action. Authority changes,
canonical replacement, restore, delete, movement of canonical resources,
permission changes, and cloud export approval remain human decisions. Future
agent grant documents are architecture-only and cannot confer action authority.

Phase L.5D preserves that boundary while defining a local-model context adapter.
The adapter consumes only deterministic explanation, relationship, and evidence
outputs; its sanitized package cannot strengthen confidence, resolve uncertainty,
promote authority, change review state, or grant access. Naming Ollama and Qwen
in a request contract does not authorize connection or execution. Structured
responses remain candidates until deterministic validation succeeds, and even a
valid response has no permission, action, approval, or authority effect.

Phase L.5E permits a model to explain one sanitized entity but grants no new
authority. The deterministic explanation and evidence remain controlling. Qwen
cannot promote unknown authority, approve review state, invent permission,
change confidence, request a source, or authorize an action. A response that
changes any of those states is rejected and withheld. Successful validation
means only that the candidate stayed inside the evidence contract; it does not
make the model an authority.

Phase L.5F further removes model prose from the trusted explanation path. A
future model may select only supplied reference IDs and exact state enums. The
deterministic validator decides acceptance, and the deterministic renderer owns
all factual wording. Safe rejection codes create observability but no authority,
permission, recommendation, or action effect.
