# Validation Tiers

Teacher AI Workstation uses layered validation. Each tier has a distinct purpose and runtime budget. Do not run deep tiers during fast smoke or routine CLI checks.

## Fast smoke

**Command:**

```bash
COS_VALIDATE_INCLUDE_SMOKE=1 bash tests/smoke-chief-of-staff-cli.sh
```

**Purpose:**

- Quick Chief of Staff CLI sanity
- Refusal gates (raw inbox, rejected samples, intake raw folder, non-approved intake)
- Lightweight command routing (`--help`, `--commands`, workflows, dry-run, intake routing)

**Expected runtime:** seconds to a few minutes.

**Must not include:**

- `bin/chief-of-staff --dashboard`
- `bin/chief-of-staff --validate-all`
- `bin/chief-of-staff --whole-system-coherence-status`
- Full M0–M7e Teacher Knowledge Vault preservation chains
- Duplicated full status CLI + status test suites
- Curriculum contract suites or production registry deep validators

Smoke includes a grep boundary guard so deep-validation entry points cannot silently re-enter the smoke script.

## Focused feature validation

**Purpose:** Run one feature's status command and/or its focused status test.

**Examples:**

```bash
bin/chief-of-staff --teacher-knowledge-vault-m7e-local-test-catalog-status
bash tests/teacher-knowledge-vault-m7e-local-test-catalog-status-test.sh
bin/chief-of-staff --teacher-knowledge-vault-m7g-persistent-working-catalog-status
bash tests/teacher-knowledge-vault-m7g-persistent-working-catalog-status-test.sh
bin/chief-of-staff --teacher-knowledge-vault-m2b-repo-staging-metadata-status
bash tests/teacher-knowledge-vault-m2b-repo-staging-metadata-status-test.sh
bin/chief-of-staff --teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status
bash tests/teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status-test.sh
bin/chief-of-staff --teacher-knowledge-vault-m2d-selected-folder-status
bash tests/teacher-knowledge-vault-m2d-selected-folder-metadata-scan-test.sh
bash tests/teacher-knowledge-vault-m2d-selected-folder-preflight-test.sh
bash tests/curriculum-contract-suite-v0-test.sh
```

Use when changing a single lane or milestone.

## Dashboard

**Command:**

```bash
bin/chief-of-staff --dashboard
```

**Purpose:** Aggregate local health across tracks with PASS/WARN/FAIL section summaries.

**Performance notes:**

- Runs many individual status scripts sequentially (~100 subchecks).
- Sets `COS_TKV_SKIP_PRESERVATION=1` so Teacher Knowledge Vault M0–M7e scripts do not re-run nested preservation chains (each milestone is invoked once by the dashboard).
- Still includes `scripts/phase-1-status.sh` by design; use focused validation when changing a single lane.

**Exit code semantics:** Dashboard exits `0` when the script completes, even if the Summary reports non-zero FAIL rows. Only `CRITICAL_FAILURE` (for example, missing repo root) forces exit `1`. Read the Summary block; exit `0` is not a green-all-clear signal.

## Validate-all

**Command:**

```bash
bin/chief-of-staff --validate-all
```

**Purpose:** Deeper project validation across foundation scripts, validators, and optional smoke (`COS_VALIDATE_INCLUDE_SMOKE=1`).

**Performance notes:**

- Orchestrates foundation/status tracks plus direct validators and test suites.
- Sets `COS_TKV_SKIP_PRESERVATION=1` for the same vault deduplication as dashboard.
- Skips `scripts/phase-1-status.sh` unless `COS_VALIDATE_INCLUDE_PHASE1=1`.
- Does not re-run dashboard; overlaps on many of the same status scripts.

**Exit code semantics:** Validate-all exits non-zero when any orchestrated track or test suite fails (`TRACK_FAILURE`).

## Coherence

**Command:**

```bash
bin/chief-of-staff --whole-system-coherence-status
```

**Purpose:** Whole-system consistency checks across planning lanes and governance surfaces.

## Deep vault preservation

**Purpose:** M0–M7e Teacher Knowledge Vault preservation and safety chains.

**Examples:**

```bash
bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status
bash tests/teacher-knowledge-vault-m7e-local-test-catalog-import-test.sh
bash tests/teacher-knowledge-vault-m7g-persistent-working-catalog-import-test.sh
bash tests/teacher-knowledge-vault-m2b-repo-staging-metadata-discovery-test.sh
bash tests/teacher-knowledge-vault-m2d-selected-folder-metadata-scan-test.sh
```

Run individually or via dashboard / validate-all — not during fast smoke.
