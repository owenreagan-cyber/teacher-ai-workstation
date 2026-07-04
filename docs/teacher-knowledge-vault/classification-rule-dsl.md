# Teacher Knowledge Vault — Classification Rule DSL

Last updated: 2026-07-04

Rules are **data**, not buried TypeScript. Must be explainable, testable, evidence-producing, and approval-gated.

Fixture: `assistant/teacher-knowledge-vault/samples/fake-classification-rule.yaml`

```yaml
classification: fake_local_planning_only
rule:
  id: saxon_power_up_placeholder
  version: 1
detect:
  contains:
    - "Power Up"
    - "Intermediate 5"
extract:
  fields:
    power_up_letter: "[A-K]"
rename:
  pattern: "math_g5_saxon_power_up_{power_up_letter}_v1.pdf"
destination:
  path: "01_MATH/03_power_ups/individual_power_up_letters/"
confidence:
  rule: 0.98
requires_review: true
runtime_approved: false
```

No rule engine executes in M0/M1.
