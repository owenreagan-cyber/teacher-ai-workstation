# Chief Production Activation — P0.2c

```text
Status: ACTIVATED and verified (application + daemon + connectivity)
Activated: 2026-11-09
Repository main at activation: 0670d0e2b0fb6eb1948f47bfb05be06e6d5046f6
Owner approval: Stage C and Stage D approved explicitly in P0.2c
```

This record is the authoritative deployment state of Chief. It supersedes the deployment sections
of `master-chief-operational-certification.md`, which remains the P0.1/P0.2a remediation record.

---

## 1. Application

| | Previous | Now |
| --- | --- | --- |
| Bundle path | `/Applications/Chief.app` | `/Applications/Chief.app` |
| Version | `0.1.0` | `0.1.0` |
| Bundle identifier | `local.chief-of-staff.desktop` | `local.chief-of-staff.desktop` |
| Source commit | `24c9df4` (2026-10-21) | `e469f3b` desktop tree (unchanged through `0670d0e`) |
| `app.asar` SHA-256 | `193377246224b378aa5535db2632c59f30f45ba73a0e4218b8035b071bba6115` | `529c221ca296b634559f374d6a2d71fbd3e940d79ad4e3bc361d09df9ef92506` |
| Architecture | arm64 | arm64 |
| Electron | 44.5.1 | 44.5.1 |
| Signature | Apple Development, Team `98F559Y354` | same, hardened runtime, not notarized |
| Runtime mode | `bin/cos` CLI fallback only | `cosd` persistent runtime |

The candidate was **not** rebuilt for P0.2c: `git diff e469f3b..HEAD -- apps/chief-desktop` is empty,
so the certified package still corresponds to current approved desktop source. Everything that
changed since (`bin/cos`, `bin/cosd`, scripts, docs, requirements) is runtime-side and is picked up
from the repository at execution time.

---

## 2. Backups (both verified before use)

| What | Path | Verification |
| --- | --- | --- |
| Previous application | `~/ChiefBackups/stage-c-app-20261109-222038/Chief.app` | asar `1933…` byte-identical to the replaced bundle; `codesign --verify --deep --strict` OK; `manifest.txt` records identity, hash, signature, source commit |
| Production state | `~/ChiefBackups/stage-c-state-20261109-222038/ChiefOfStaff` | 10 files, per-file SHA-256 identical to the live state at copy time; no SQLite existed, so no WAL-consistency concern |
| Earlier P0.2b backup | `~/ChiefBackups/pre-p0.2b-24c9df4/` | left untouched |

The replaced bundle also remains on disk at `/Applications/Chief.app.stage-c-replaced`.

No backup was overwritten. No backup lives inside the repository.

---

## 3. Python runtime

| Item | Value |
| --- | --- |
| Marker | `~/.chief-runtime/python` (mode `0600`) → `~/.chief-runtime/venv/bin/python` |
| Runtime root mode | `0700` |
| Python | 3.12.13 (venv, `sys.prefix` = the venv) |
| `cryptography` | 50.0.2 (declared `>=42,<51`) |
| Transitive | `cffi 2.1.1`, `pycparser 3.12` |
| Global installs | none |
| System Python | unchanged |
| Interpreter contract | 13/13 tests; both `bin/cos` and `bin/cosd` resolve `CHIEF_PYTHON` → marker → `python3.12` → Homebrew |
| Readiness gate | `PASS 4 / WARN 0 / FAIL 0` (`--require` exits 0) |

`ps` shows the Homebrew framework binary because a venv `python` is a symlink to it. Interpreter
selection was proven separately: a recording wrapper installed as the marker was invoked by
`bin/cosd` when starting the daemon.

---

## 4. `cosd` identity

| Field | Value |
| --- | --- |
| PID | 34750 (single instance) |
| Bind | `127.0.0.1:8765` — loopback only; `lsof` shows no other listener |
| Health | `{"ok": true, "service": "cosd", "version": "0.1.0"}` |
| Status | running, `stale_pid: false` |
| LaunchAgent | **none** (no automatic startup) |
| Tailscale / gateway | not activated |

---

## 5. Production state

| Item | Value |
| --- | --- |
| Location | `~/Library/Application Support/ChiefOfStaff/` |
| Root mode | `0700` |
| `cosd/` mode | `0700` (created by the P0.2a fix) |
| `api.token` | present, mode `0600`, never printed |
| Token leakage | 0 occurrences outside `api.token` (state files and audit) |
| Database | `cosd/tasks.sqlite3`, `PRAGMA integrity_check` = **ok**, `journal_mode` = **wal** |
| New files | `api.token`, `auth.meta.json`, `cosd.pid`, `tasks.sqlite3` (+ `-wal`, `-shm`) |

### Existing data preserved

`config.json`, `desktop.json`, `search_usage.json`, `sessions/default.jsonl`, `audit.initialized`
are hash-identical to the pre-activation backup. `audit.jsonl` was **appended only**: the first
3,706,587 bytes hash-identical to the backup, preserving the hash chain, with new entries for the
activation's own operations.

No database was migrated, recreated, or deleted. No credential was rotated.

---

## 6. Authentication and security

| Check | Result |
| --- | --- |
| Bearer auth on health/status | PASS |
| Invalid token | **HTTP 401** |
| Loopback-only bind | PASS |
| Token not logged | PASS |
| Kill switch | `cos stop` → `ask` refused with `error_kind: stopped` → `cos resume` cleared |
| Private directory permissions | PASS (`0700` root and `cosd/`, `0600` token) |
| LaunchAgent | none |

---

## 7. Task persistence and recovery

- Registry started empty (no prior production tasks).
- One **synthetic, non-consequential** task (`P0.2c activation check`, kind `ask`, fixture question)
  was created through the API.
- Daemon stopped and restarted; the task retained its id and `created_at` (`0fb50167…`,
  `2026-11-09T22:21:12Z`), proving durable persistence across restart.
- The task was then cancelled (`state: CANCELLED`) to leave the queue clean.
- Queue and worker endpoints respond; `workers` is empty (no autonomous workers configured).
- Recovery/lease/checkpoint behavior remains covered by `tests/cosd` (90 tests), not re-simulated on
  production data.

---

## 8. Device registry and pairing

| Item | State |
| --- | --- |
| Registry | initialized, **empty** (`{"devices": [], "total": 0}`) |
| Enrollment | none |
| Invitations / codes | none created |
| Credential rotation | none |
| Pairing dependency | available (`X25519AesGcmEnvelope`) |
| Pairing operations | **disabled pending a fix** |

**Open security defect.** `test_concurrent_redemption_has_one_winner` intermittently fails on CI
(Linux) because a losing concurrent redemption reaches
`cosd/devices/pairing/service.py:137` with `protocol_version = NULL` and raises `TypeError` instead
of a clean `DeviceError` (HTTP 409). It is pre-existing (only the original feature commit `439f90e`
touches that file) and was not reproducible locally in 25 runs. Until it is fixed and reviewed under
D-010, no device may be enrolled or invited. This does not affect chat, tasks, or the daemon.

---

## 9. Chief.app connectivity

Verified with a single launch (owner-approved):

| Field | Value |
| --- | --- |
| PID | 59176 |
| Executable | `/Applications/Chief.app/Contents/MacOS/Chief` |
| Socket | `Chief 59176 → 127.0.0.1:8765` **ESTABLISHED**, paired with `cosd 34750` |
| Daemon activity after launch | `home_refresh`, `model_warm` in the audit log |
| Fallback | not used for the verified path (a fallback would open no socket) |

The established socket is the decisive evidence: the app is talking to the daemon, not silently
running standalone. Window contents were **not** inspected or automated.

---

## 10. Raycast independence

| Check | Result |
| --- | --- |
| Raycast imports/dependencies in the app | 0 |
| `Raycast` string in the packaged renderer | absent |
| Chat, sessions, tasks, queue, devices, runtime, notifications, recovery | all reach the daemon through the app's own IPC bridge and `bin/cos` |
| Raycast modified | no |

Raycast happens to be installed and running on this Mac, so an "uninstalled" run was not performed —
the requirement is proven structurally (no dependency, no shared state), which is the stronger claim.

---

## 11. Rollback

Prepared and verified before replacement:

```bash
./bin/cosd stop
rm -rf /Applications/Chief.app
mv /Applications/Chief.app.stage-c-replaced /Applications/Chief.app
shasum -a 256 /Applications/Chief.app/Contents/Resources/app.asar   # 1933772…6115
codesign --verify --deep --strict /Applications/Chief.app
```

State is preserved. `<state>/cosd/` may be left in place (the old app ignores it) or removed only if
the owner explicitly chooses to discard the new runtime state. No rollback path deletes
`audit.jsonl`, `config.json`, `sessions/`, or `cache/`.

---

## 12. Known limitations

1. **Pairing is disabled** by the open concurrency defect (§8).
2. **No automatic startup.** `cosd` runs because it was started explicitly; after a reboot it must be
   started again (`bin/cosd start`). A LaunchAgent is intentionally not installed.
3. **The app depends on the repository checkout** at `~/Projects/teacher-ai-workstation` for
   `bin/cos` (`src/main/config.ts: DEFAULT_COS_PATH`).
4. **Not notarized** — signed with an Apple Development identity; another Mac would see a Gatekeeper
   warning.
5. **Memory writing, multi-worker model routing, and D-018 approval UI** remain unimplemented; the
   Agents section is a placeholder.
6. **Preflight script**: `scripts/chief-activation-preflight.sh` compares the backup against the
   installed hash, so after activation it reports one FAIL unless `CHIEF_EXPECTED_BACKUP_ASAR` is
   supplied. Fixed in the same change set as this document.

---

## 13. Acceptance matrix

| Requirement | Expected | Actual |
| --- | --- | --- |
| Candidate integrity | PASS | **PASS** |
| Existing application backup | PASS | **PASS** |
| Python runtime | PASS | **PASS** |
| cryptography | PASS | **PASS** (50.0.2) |
| Production permissions | PASS | **PASS** |
| `cosd` startup | PASS | **PASS** |
| Authenticated API | PASS | **PASS** |
| Persistent tasks | PASS | **PASS** (survives restart) |
| Device registry preservation | PASS | **PASS** (empty, untouched) |
| Chief.app connection | PASS | **PASS** (established socket) |
| Raycast independence | PASS | **PASS** (structural) |
| Rollback readiness | PASS | **PASS** |
| Device pairing | expected available | **WARN — disabled pending fix** |

Every row marked PASS was executed and observed in this mission. Nothing was inferred from a
previous mission or from a passing unit test alone.

---

## 14. Next steps

1. Fix the pairing concurrency defect with a regression test and cross-model review (D-010); then
   re-enable enrollment.
2. Decide whether `cosd` should start at login (single LaunchAgent, owner-approved) or remain manual.
3. Begin P1 (mission and approval infrastructure) against the now-live runtime.
