# Master Chief — Operational Certification (P0.1 and P0.2a)

```text
Status: certification record (evidence-based)
Scope: discovery, reconciliation, runtime certification, remediation, candidate packaging
Implementation approval: none granted by this document
Audited: 2026-11-09 (P0.1)
Remediated: 2026-11-09 (P0.2a)
Source commit at audit: 98b9dfc6b1ff40b7a9d09eaeefddfe184cbb56fa
Production activation: NOT authorized — see §15
```

This record replaces the earlier assumption that "no Chief.app exists". Chief.app exists, is
running, and its provenance is now established byte-for-byte.

The headline finding is a **version gap, not an absence**: the installed application is a real,
signed build of this repository from **2026-10-21** (`24c9df4`), about eighteen days and five
desktop commits behind current `main`. It predates the persistent `cosd` runtime integration
entirely.

---

## 1. Application identity

### Running application

| Field | Result |
| --- | --- |
| Running | **Yes** — verified by process inspection, not by launching it |
| PID | 94583 (main), parent PID 1 (launchd), started **Sun 2026-11-08 15:53:29** |
| Helper processes | 3 (renderer, GPU, network) |
| Executable | `/Applications/Chief.app/Contents/MacOS/Chief` |
| Bundle path | `/Applications/Chief.app` |
| Bundle identifier | `local.chief-of-staff.desktop` |
| Version | `0.1.0` |
| Build date | 2026-10-21 07:41:34 (bundle signing timestamp; binary mtime 07:41:34) |
| Source commit | **`24c9df4`** — "UI-1 section 5: fixes carried over" (2026-10-21 00:27:56 -0400) |
| Electron version | 44.5.1 (Electron Framework `CFBundleVersion`) |
| Architecture | arm64 (thin) |
| Code signature | `Apple Development: ofr32081@aol.com (KXYQ8895ZL)`, Team `98F559Y354`, hardened runtime, **not notarized**, `codesign --verify --deep --strict` = valid |
| Runtime mode | Standalone desktop client calling `bin/cos` through `execFile` (no daemon) |
| Confidence | **HIGH** for the running process and bundle; **HIGH** for source commit (byte-identical rebuild) |

### Installed application

Same bundle as the running one — `/Applications/Chief.app`, not a second copy. No bundle exists in
`~/Applications`, and no other `Chief.app` exists under `~/Projects` except the packaging output
inside this repository.

`Release/mac-arm64/Chief.app` in `apps/chief-desktop` is **byte-identical** to the installed bundle
(app.asar SHA-256 matches exactly), so the installed application is a direct copy of this repo's
own packaging output.

---

## 2. Source / package reconciliation

| Layer | Version | Commit | app.asar SHA-256 | Status |
| --- | --- | --- | --- | --- |
| Repository source (`main`) | 0.1.0 | `98b9dfc` | n/a | Current, includes `cosd` |
| Development runtime (`out/`, `dist/`) | 0.1.0 | `98b9dfc` | n/a | Rebuilt during this audit |
| Packaged application (`release/mac-arm64`) | 0.1.0 | `24c9df4` | `193377246224b378aa5535db2632c59f30f45ba73a0e4218b8035b071bba6115` | Oct 21, preserved |
| Installed application (`/Applications`) | 0.1.0 | `24c9df4` | `1933772…6115` (identical) | Running |
| Running application | 0.1.0 | `24c9df4` | same inode source | Running |
| Candidate package (this audit) | 0.1.0 | `98b9dfc` | `529c221ca296b634559f374d6a2d71fbd3e940d79ad4e3bc361d09df9ef92506` | Built, **not installed** |

### How the source commit was proven

Version numbers alone were not trusted. The installed `app.asar` was unpacked read-only and
compared against a clean rebuild of commit `24c9df4` in a temporary worktree:

| Payload | Files compared | Byte-identical |
| --- | --- | --- |
| `out/main`, `out/preload`, `out/shared` (tsc output) | 15 | **15 / 15** |
| `dist/renderer` (vite output) | 13 | **13 / 13** |
| **Total** | **28** | **28 / 28** |

The renderer content hashes also reproduce exactly (`index-DWCtdLQF.js`, `index-TEdulZHO.css`),
which is a content-addressed match, not a timestamp coincidence.

### What the installed build is missing

The installed asar contains 29 entries and exactly the UI-1 module set. It has **no** `cosd/`
client, **no** Devices screen, **no** Task center, **no** notifications, and **no** runtime ops.

| Capability | Installed `24c9df4` | Current source `98b9dfc` |
| --- | --- | --- |
| Chat, sessions, brief, Today, Settings | Yes | Yes |
| Agents & builds page | Present, task center absent | Task center backed by `cosd` |
| Persistent `cosd` client | **No** | Yes |
| Tasks / queue / runtime snapshot | **No** | Yes |
| Device registry UI | **No** | Yes |
| Pairing / enrollment UI | **No** | Yes |
| Notifications | **No** | Yes |

---

## 3. Python and dependency readiness

| Item | Result |
| --- | --- |
| Pinned interpreter | `python3.12` → **3.12.13** (Homebrew `/opt/homebrew/opt/python@3.12`) |
| Default `python3` | 3.15.2 — **not** used by `bin/cos` or `bin/cosd` |
| PyYAML | 6.0.3 — present |
| PyMuPDF | 1.28.2 — present |
| `cryptography` | **absent** from the system 3.12 environment |
| Declared requirement | `requirements-cosd-pairing.txt`: `cryptography>=42` |
| Effect of absence | Daemon still starts; owner approval of pairing fails closed with `503 crypto_unavailable` |
| Virtual environments in repo | None |
| Global install performed | **No** |

### Clean-environment reproduction

An isolated temporary venv (no global changes) was created and the declared requirement installed:

```bash
python3.12 -m venv "$VENV"
"$VENV/bin/python" -m pip install -r requirements-cosd-pairing.txt
```

Result: `cryptography 50.0.2`, and the pairing suite ran **64 tests with 0 skipped** (versus 64
tests with 4 skipped on the system interpreter). The dependency declaration is therefore
**sufficient and reproducible**; the gap is installation state, not an incomplete manifest.

---

## 4. `cosd` lifecycle certification

Performed against a temporary `COS_STATE_DIR` and a non-default port. The real state directory was
never used for mutation, no LaunchAgent was installed, and no production daemon was touched.

| Check | Result | Evidence |
| --- | --- | --- |
| Start | PASS | `{"ok": true, "pid": …, "host": "127.0.0.1", "port": …}` |
| Loopback-only bind | PASS | `lsof` shows only `TCP 127.0.0.1:<port> (LISTEN)` |
| Health | PASS | `{"ok": true, "service": "cosd", "version": "0.1.0"}` |
| Authenticated status | PASS | Running, pid, port, health, `stale_pid: false` |
| Deterministic ask | PASS | Fixture answer `2:30 PM … October 1, 2026`, `fast_path: true`, `tools_used: ["time.now"]`, no model call |
| Task create | PASS | `QUEUED`, schema v2, data class `internal` |
| Idempotency | PASS | Repeat create returned the same task id with `reused: true` |
| Task retrieval | PASS | `tasks list` / `tasks show` return the record |
| Queue status | PASS | `{"paused": false, "task_counts": {…}, "active_leases": 0}` |
| Worker status | PASS | `{"ok": true, "workers": []}` |
| Invalid token | PASS | HTTP **401** |
| Graceful stop | PASS | `{"ok": true, "stopped": true}`; no daemon process remains |
| Restart | PASS | New pid, same port |
| Persistent task recovery | PASS | Task created before stop still present after restart |
| Token rotation | PASS | `version: 2`, token file rewritten, client re-authenticated |
| Kill switch | PASS | `cos ask` returns `stopped by kill switch`; `cos resume` clears it |
| SQLite WAL | PASS | `journal_mode = wal` |
| Duplicate start | PASS | `cosd: cosd is already running`; single daemon |
| Token not logged | PASS | Token value appears in 0 state files other than `api.token`; 0 audit-log hits |
| State directory mode | **WARN** | `<state>/cosd` is `0755` (see §9) |
| Token file mode | PASS | `0600` |

### Interrupted-task recovery

Live interruption was not simulated on a running daemon (that would require killing a process).
Coverage comes from the automated suite, which exercises startup recovery, leases, checkpoints and
attempt recording: `tests/cosd` — **80 tests, OK**.

---

## 5. Automated QA results

| Suite | Result |
| --- | --- |
| `tests/cos` | **403 tests, OK** |
| `tests/cosd` | **80 tests, OK** |
| `tests/cosd/devices` | **89 tests, OK** |
| `tests/cosd/devices/pairing` (system Python) | **64 tests, OK (4 skipped — cryptography)** |
| `tests/cosd/devices/pairing` (clean venv) | **64 tests, OK, 0 skipped** |
| Chief desktop `npm test` | **98 tests pass, 0 fail** |
| Desktop static checks | **610 passed, 0 failed** |
| CI (GitHub Actions, `main`) | green at `98b9dfc` |

---

## 6. Device registry and pairing

Certified through the isolated suites rather than by enrolling real hardware.

| Capability | Verified by | Result |
| --- | --- | --- |
| Device identity, stable ids | `tests/cosd/devices` | PASS |
| Permission profiles | `tests/cosd/devices` | PASS |
| Credential references (Keychain-backed) | `tests/cosd/devices` | PASS |
| Rotation, expiration, revocation | `tests/cosd/devices` | PASS |
| Pairing invitation, one-time code, QR payload | pairing suite | PASS |
| Replay prevention, rate limiting | pairing suite | PASS |
| Owner approval, permission selection | pairing suite | PASS |
| X25519 / HKDF / AES-GCM delivery envelope | pairing suite + real crypto venv | PASS |
| Enrollment audit | pairing suite | PASS |
| Remote enrollment / Tailscale / gateway | not implemented | **Not activated** |

No real device was enrolled, no Keychain entry was modified, no existing credential was revoked, and
no network listener was opened beyond loopback.

---

## 7. Chief.app feature inventory (current source)

| Area | Implementation | Evidence |
| --- | --- | --- |
| Chat + streaming | Implemented | `chief:ask`, `chief:cancel-ask`, SSE task events |
| Sessions / history | Implemented | `chief:history`, `cos history` |
| Status | Implemented | `chief:status` via `cosd` with CLI fallback |
| Tasks / Task center | Implemented | `chief:tasks-list`, `task-create/get/cancel/retry/history` |
| Queue + runtime controls | Implemented | `chief:queue`, `cosd-start/stop/restart`, `runtime-snapshot` |
| Device registry UI | Implemented | `Devices.tsx`, 14 device/enrollment channels |
| Pairing UI | Implemented | Pending enrollments + owner approval |
| Connection recovery / reconnect | Implemented | `cosd-connection`, `cosd-reconnect`, auth-failure handling |
| Standalone CLI fallback | Implemented | `chief-runtime.ts` falls back to `bin/cos` |
| Notifications | Implemented | `notifications.ts`, `ops-prefs` |
| Settings + model selection | Implemented | `config-get` / `config-set` (`model`, `keep_alive`, places, auto-search) |
| Today dashboard | Implemented | `cos home --json`, per-section freshness |
| Builds card | Implemented (real) | `cos/home.py: builds_from_git` |
| **Agents** | **Placeholder** | `cos/home.py`: `Source("agents", …, {"available": False, "items": []})`; `AgentsCard` is a static empty state |
| Memory writing | **Not implemented** | `cos/memory.py` loads memory; no write/remember path |
| Model routing (multi-worker) | **Not implemented** | Single configured model + intent fast path; M2 router is future work |
| Approval packets (D-018 UI) | **Not implemented** | No approval surface beyond device-enrollment approval |

IPC bridge integrity: **47 channels exposed by the preload, 47 handlers registered, 0 orphans in
either direction.** The preload exposes named functions only — no generic passthrough.

---

## 8. Raycast independence

| Check | Result |
| --- | --- |
| `raycast` imports/requires in `apps/chief-desktop/src` | 0 |
| Runtime dependency on Raycast in `package.json` | none (only `qrcode`) |
| `cos` / `cosd` dependency on Raycast | none |
| Comments mentioning Raycast | 4 docstrings/help strings only — cosmetic, no behavior |
| All app capabilities reachable without Raycast | yes (47-channel IPC bridge, `bin/cos`, `cosd`) |

Removing or never installing Raycast does not affect chat, sessions, memory, routing, tasks,
queue, devices, notifications, runtime, or recovery. Raycast remains optional.

---

## 9. Security findings

| Finding | Severity | Detail |
| --- | --- | --- |
| **`<state>/cosd` directory mode is `0755`, not `0700`** | **WARN → RESOLVED in P0.2a** | `cosd/auth.py:ensure_token()` created the directory with a bare `mkdir(parents=True, exist_ok=True)`, and `cosd/storage.py:_ensure_private_dir()`'s `mkdir(mode=0o700)` was a **no-op on an existing directory**, so it was never chmod-ed. Fixed by one authoritative `cos.config.ensure_private_dir()` that creates 0700, tightens an existing wider directory, does not recurse, and raises when the mode cannot be established. See §15. |
| `cryptography` missing in the operational interpreter | WARN | Pairing approval fails closed (`503 crypto_unavailable`). Fail-closed is correct; the dependency is simply not installed. |
| Application not notarized | INFO | `notarize: false` in `electron-builder.yml`; signed with an Apple Development identity and hardened runtime. Expected for local use; Gatekeeper on another Mac would warn. |
| Token handling | PASS | Token never appears in logs, audit entries, or any state file other than `api.token` (`0600`). |
| Network exposure | PASS | Loopback only; no external listener; no gateway; no Tailscale. |
| Raycast Cloud Sync | N/A | Not installed or required. |

---

## 10. Candidate package provenance

| Field | Value |
| --- | --- |
| Path | `apps/chief-desktop/release/p0.1-candidate/mac-arm64/Chief.app` |
| Source commit | `98b9dfc6b1ff40b7a9d09eaeefddfe184cbb56fa` |
| Version / bundle id | `0.1.0` / `local.chief-of-staff.desktop` |
| Architecture | arm64 |
| Bundle size | 289 MB |
| `app.asar` size | 2,259,976 bytes (272 entries) |
| `app.asar` SHA-256 | `529c221ca296b634559f374d6a2d71fbd3e940d79ad4e3bc361d09df9ef92506` |
| Signature | Apple Development `KXYQ8895ZL`, Team `98F559Y354`, hardened runtime |
| `codesign --verify --strict` | OK |
| Notarization | None (by configuration) |
| Installed | **No** |
| Replaces existing app | **No** |

Build command:

```bash
cd apps/chief-desktop
npm run build
./node_modules/.bin/electron-builder --mac dir --arm64 \
  --config.directories.output=release/p0.1-candidate
```

Reproducibility notes: the build requires an Electron 44.5.1 download and a signing identity. The
same source rebuilt twice produces the same `out/` and `dist/` payload hashes; the outer bundle
differs because of signing timestamps.

The previously installed artifact in `release/mac-arm64/` was **not overwritten**.

---

## 11. Known limitations

1. The installed application is 18 days behind `main` and cannot use `cosd`, tasks, devices, or
   pairing, because those did not exist at `24c9df4`.
2. `cosd` has never run in production on this Mac — no `cosd` subdirectory exists under
   `~/Library/Application Support/ChiefOfStaff`.
3. The installed build therefore runs on the `bin/cos` CLI fallback path, which is slower and has no
   durable task state.
4. Agents are a placeholder; memory is read-only; model routing is a single configured model plus an
   intent fast path.
5. Approval packets (D-018) have no user interface yet — only device enrollment approval exists.
6. Interrupted-task recovery is proven by unit tests, not by a live kill/restart experiment.
7. The candidate package has not been launched. Launching would take window focus; that requires
   owner testing.

---

## 12. Installation procedure (owner approval required)

Not performed by this mission.

```bash
# 1. Quit the running app first (owner action; do not force-quit).
# 2. Preserve the current bundle as a rollback point.
mv /Applications/Chief.app /Applications/Chief.app.p0.1-previous

# 3. Install the certified candidate.
cp -R ~/Projects/teacher-ai-workstation/apps/chief-desktop/release/p0.1-candidate/mac-arm64/Chief.app \
      /Applications/Chief.app

# 4. Verify what actually landed.
shasum -a 256 /Applications/Chief.app/Contents/Resources/app.asar   # expect 529c221c…92506
codesign --verify --deep --strict /Applications/Chief.app

# 5. Optional but recommended: install the pairing requirement into the operating environment.
python3.12 -m pip install --user --break-system-packages -r requirements-cosd-pairing.txt

# 6. Launch and confirm the Devices page appears and Status reports cosd.
```

Do not install a LaunchAgent and do not enable automatic startup as part of P0.1.

### Rollback

```bash
# Quit Chief, then:
rm -rf /Applications/Chief.app
mv /Applications/Chief.app.p0.1-previous /Applications/Chief.app
shasum -a 256 /Applications/Chief.app/Contents/Resources/app.asar   # expect 1933772…6115
```

The old bundle is preserved inside the repo too (`release/mac-arm64/Chief.app`), so the Oct 21 build
is recoverable even if `/Applications` is wiped.

---

## 13. PASS / WARN / FAIL matrix

| # | Area | Result | Basis |
| --- | --- | --- | --- |
| 1 | Application discovery | **PASS** | Running process, executable, bundle, signature, version all identified |
| 2 | Source / package reconciliation | **WARN** | Proven exactly, but installed is 18 days behind source; divergence is real and unresolved by design |
| 3 | Python dependency readiness | **WARN** | Core deps present; `cryptography` missing operationally; venv proves the manifest is sufficient |
| 4 | `cosd` lifecycle | **PASS** | Start, health, stop, restart, duplicate-start refusal, loopback bind |
| 5 | Authentication | **PASS** | Token auth, 401 on invalid, rotation, no logging |
| 6 | Persistence | **PASS** | Task survives restart; WAL enabled; idempotency holds |
| 7 | Recovery | **PASS** | 80-test suite covers startup recovery, leases, checkpoints |
| 8 | Device registry | **PASS** | 89 tests |
| 9 | Pairing | **PASS** / **WARN** | 64/64 with crypto in venv; system interpreter has 4 skips |
| 10 | Chief.app integration | **WARN** | Source is complete (47/47 IPC); the installed build lacks the entire `cosd` generation |
| 11 | Raycast independence | **PASS** | Zero code dependency; 4 comments only |
| 12 | Reproducible packaging | **PASS** | Byte-identical provenance proof; candidate built, signed, hashed, not installed |
| 13 | Security | **WARN** | `0755` state dir; no notarization; otherwise clean |
| 14 | Documentation | **PASS** | This record plus roadmap and README updates |

A successful build is not deployment. A running application is not current source. A passing suite
is not a healthy production state. All three distinctions are preserved above.

---

## 14. Next steps

1. **Owner decision:** approve or decline installing the candidate package (§12).
2. ~~Fix the directory mode~~ — **done in P0.2a** (§15).
3. ~~Install the pairing requirement~~ — **procedure and readiness check added in P0.2a**; the
   package itself is still not installed in the operating interpreter.
4. **Certify `cosd` as the production runtime** after installation: start it once against the real
   state root, confirm Chief.app reports `cosd` rather than CLI fallback, then record the evidence.
5. **Do not claim P0 complete** until an installed build with `cosd` is running and its `app.asar`
   hash is recorded here.

---

## 15. P0.2a — remediation and activation preflight (2026-11-09)

P0.2a resolved the two source-level findings from P0.1 and produced a fresh candidate. **It did
not install, replace, or launch anything, and it did not start a production daemon.**

### 15.1 Private state-directory permissions

`cos/config.py` now owns one authoritative mechanism:

```python
ensure_private_dir(path)   # create 0700, tighten an existing wider dir, verify, else raise
ensure_state_dir(path)     # ensure_private_dir(state_dir())
ensure_private_subdir(...) # ensure_private_dir(ensure_state_dir(root) / name)
```

Behavior, which is what the regression tests pin:

- A new directory is created `0700`.
- An existing `0755` directory is chmod-ed to `0700` in place.
- An already-`0700` directory is left untouched (same inode, same mtime).
- Only the named directory changes — **no recursion**, contained files keep their modes.
- If the mode still cannot be established after chmod, `StatePermissionError` is raised so startup
  fails closed instead of serving from an exposed directory.

Call sites converted: `cosd/auth.py` (`ensure_token`, `rotate_token`), `cosd/storage.py`,
`cosd/devices/storage.py`, `cosd/lifecycle.py`. `cosd/launchagent.py` intentionally still targets
`~/Library/LaunchAgents`, which is not a private state directory.

`cosd` now secures **both** the state root and `<state>/cosd`:

| Before | After |
| --- | --- |
| root `0755`, `cosd/` `0755` | root `0700`, `cosd/` `0700`, token `0600` |

Verified against a live daemon started on a temporary state root that was deliberately pre-created
at `0755`.

### 15.2 Reproducible pairing dependency

`bin/cosd` pins `python3.12` (PATH, then `/opt/homebrew/bin/python3.12`). That interpreter still
does not have `cryptography`, so pairing fails closed today by design.

Documented, reproducible procedure that does **not** touch the global interpreter or the default
Python:

```bash
python3.12 -m venv ~/.chief-runtime/venv
~/.chief-runtime/venv/bin/python -m pip install -r requirements-cosd-pairing.txt
```

Then either run the daemon with that interpreter, or install into the pinned user environment once
the owner approves it. The requirement stays `cryptography>=42`; fail-closed behavior is unchanged.

Automated readiness check: `scripts/chief-cosd-dependency-status.sh`.

| State | Result | Exit |
| --- | --- | --- |
| `cryptography` importable, real cipher wired | **PASS** | 0 |
| absent, pairing correctly unavailable | **WARN** | 0 |
| absent but pairing advertised, or installed but not wired | **FAIL** | 1 |
| absent with `--require` (activation gate) | **FAIL** | 1 |

It never installs, never starts the daemon, and never touches state. Current machine:

```
PASS: interpreter /opt/homebrew/bin/python3.12 is Python 3.12.13 (matches bin/cosd pin)
WARN: cryptography is not installed; pairing is correctly unavailable (503 crypto_unavailable)
PASS: requirements-cosd-pairing.txt pins cryptography>=42
PASS: isolated-venv install procedure is documented
PASS: 3  WARN: 1  FAIL: 0
```

Against a venv with the dependency installed, the same check reports `PASS: 4, WARN: 0, FAIL: 0`
with `X25519AesGcmEnvelope`.

### 15.3 Regression tests

New file `tests/cosd/test_state_permissions.py`, 10 tests:

| # | Case | Test |
| --- | --- | --- |
| 1 | New directory created at 0700 | `test_new_cosd_directory_is_created_at_0700`, `test_state_root_is_created_at_0700` |
| 2 | Existing permissive directory corrected | `test_world_readable_directory_is_corrected_in_place` |
| 3 | Existing 0700 left untouched | `test_already_private_directory_is_left_alone` |
| 4 | Existing token stays 0600 and unchanged | `test_existing_token_and_metadata_are_preserved`, `test_rotation_keeps_private_directory_and_file_modes` |
| 5 | Existing database and rows intact | `test_existing_database_and_rows_survive_correction` |
| 6 | Cannot secure → fail closed | `test_unsecurable_directory_raises`, `test_token_creation_fails_closed_when_directory_cannot_be_secured` |
| — | No recursion into contents | `test_correction_is_not_recursive` |

### 15.4 Full test results

| Suite | Result |
| --- | --- |
| `tests/cos` | **403 tests, OK** |
| `tests/cosd` | **90 tests, OK** (80 existing + 10 new), 0 skipped |
| `tests/cosd/devices` | **89 tests, OK** |
| `tests/cosd/devices/pairing` (venv with `cryptography 50.0.2`) | **64 tests, OK, 0 skipped** |
| Chief desktop `npm test` | **98 pass, 0 fail, 0 skipped** |
| Desktop static checks | **610 passed, 0 failed** |
| Dependency readiness | PASS/WARN/FAIL as above |

### 15.5 P0.2a candidate

| Field | Value |
| --- | --- |
| Path | `apps/chief-desktop/release/p0.2a-candidate/mac-arm64/Chief.app` |
| Source commit | `0471e51` + P0.2a changes |
| Version / bundle id / arch | `0.1.0` / `local.chief-of-staff.desktop` / arm64 |
| `app.asar` SHA-256 | `529c221ca296b634559f374d6a2d71fbd3e940d79ad4e3bc361d09df9ef92506` |
| `app.asar` size | 2,259,976 bytes (272 entries) |
| Signature | Apple Development `KXYQ8895ZL`, Team `98F559Y354`, hardened runtime, not notarized |
| `codesign --verify --strict` | OK |
| Installed / launched | **No** |

The asar hash is identical to the P0.1 candidate because every P0.2a change is Python-side; the
Electron bundle does not embed the runtime. Package contents confirm `cosd` client, task IPC,
devices, notifications and runtime modules; the renderer bundle contains Devices, Pairing, Task
center and Queue, and the string `Raycast` does not appear in it.

**Installation caveat:** the desktop app resolves the runtime at
`~/Projects/teacher-ai-workstation/bin/cos` (`src/main/config.ts`). Installing the app without that
checkout at that path yields a client with no runtime.

### 15.6 Updated matrix

| # | Area | P0.1 | Now |
| --- | --- | --- | --- |
| 2 | Source/package reconciliation | WARN | **WARN** — installed app still `24c9df4` |
| 3 | Python dependency readiness | WARN | **WARN** — procedure + check added; not installed |
| 9 | Pairing | PASS/WARN | **PASS** in venv, **WARN** operationally |
| 13 | Security | WARN | **WARN → PASS** for state-directory permissions; per-user install remains WARN |
| 14 | Documentation | PASS | **PASS** |

### 15.7 Activation decision

**Not activated.** The production application and daemon remain untouched: `/Applications/Chief.app`
still has asar `1933772…6115`, the running process is unchanged, no `cosd` was started against the
real state root, and no LaunchAgent exists. Installing the candidate and activating `cosd` require
explicit owner approval in P0.2b.
