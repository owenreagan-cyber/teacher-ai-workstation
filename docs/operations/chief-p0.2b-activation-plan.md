# Chief P0.2b — Controlled Production Activation Plan

```text
Status: PREPARED — awaiting owner activation
Activation performed: NO
Scope: Stage A preparation and verification only
Baseline main: e469f3b141852c57dc63f94e13e21312e410328c
Candidate: apps/chief-desktop/release/p0.2a-candidate/mac-arm64/Chief.app
Prepared: 2026-11-09
```

This document is the exact, bounded procedure for the first production activation of Chief.app and
`cosd`. Everything in Stage A has been executed and verified. Everything in **§7 Stage B** requires
Owen's explicit confirmation and has **not** been performed.

---

## 1. Baseline

| Item | Value |
| --- | --- |
| Repository `main` = `origin/main` | `e469f3b141852c57dc63f94e13e21312e410328c` |
| Working tree | clean apart from preserved `assistant.zip`, `assets/audio-clips/` |
| Installed application | `/Applications/Chief.app` |
| Installed `app.asar` SHA-256 | `193377246224b378aa5535db2632c59f30f45ba73a0e4218b8035b071bba6115` |
| Installed source commit | `24c9df4` (2026-10-21) |
| Running process | PID 94583, started 2026-11-08 15:53:29, parent launchd |
| Production `cosd` | never started; no `cosd/` under the state root |
| Production state root | `~/Library/Application Support/ChiefOfStaff`, mode `0700` |

---

## 2. Runtime architecture decision

**Chosen: Option A — a dedicated Chief-owned virtual environment, selected by an explicit
interpreter contract.**

| Option | Verdict |
| --- | --- |
| **A. Chief-owned venv** at `~/.chief-runtime/venv`, selected via `CHIEF_PYTHON` or the marker `~/.chief-runtime/python` | **Accepted** |
| B. Existing Homebrew Python 3.12 with managed dependencies | **Rejected** |
| C. Vendored wheels or a repo-local interpreter | **Rejected** — repository bloat and supply-chain opacity |

Why B is not just discouraged but **technically unworkable here**: `bin/cos` and `bin/cosd` exec
Python with `-s -E -P`. `-s` disables the user site-packages directory, so a
`pip install --user` of `cryptography` would be **invisible to the runtime**. The only ways to make B
work are a global install (forbidden) or editing the launcher flags (weakens isolation).

Why C is rejected: it puts binaries in version control and makes upgrades indistinguishable from
source changes.

### Interpreter contract (implemented this mission)

Both `bin/cos` and `bin/cosd` resolve in this order:

1. `CHIEF_PYTHON` — explicit override, validated.
2. `~/.chief-runtime/python` — a one-line marker file written by the activation procedure.
3. `python3.12` on `PATH`.
4. `/opt/homebrew/bin/python3.12`.

An explicit interpreter (1 or 2) must be executable and must report **Python 3.12**, otherwise the
entrypoint exits `127` with a message. A stale venv therefore **fails closed** instead of silently
falling back to another interpreter.

The marker file exists so a Finder-launched app — which inherits launchd's minimal environment, not
a shell profile — still uses the venv. No `launchctl setenv`, no LaunchAgent and no PATH mutation is
required.

Covered by `tests/chief-interpreter-test.sh`: 13 assertions including marker precedence, stale-marker
failure, and agreement between both entrypoints.

---

## 3. Dependency readiness

| Item | Value |
| --- | --- |
| Supported interpreter | `python3.12` 3.12.13 (Homebrew) |
| Declared requirement | `cryptography>=42,<51` (upper bound is a reviewed change) |
| Verified version | `cryptography 50.0.2` in an isolated venv |
| System Python 3.12 | **no `cryptography`** — pairing correctly unavailable |
| Fail-closed path | owner approval returns `503 crypto_unavailable` |

`requirements-cosd-pairing.txt` gained an explicit upper bound so a future major release cannot be
pulled in silently.

Readiness gate: `scripts/chief-cosd-dependency-status.sh`.

| Runtime | Result |
| --- | --- |
| System 3.12 | `PASS: 3 / WARN: 1 / FAIL: 0` |
| Isolated venv | `PASS: 4 / WARN: 0 / FAIL: 0` |
| Venv with `--require` | exit 0 |

---

## 4. Candidate integrity (verified this mission)

| Check | Result |
| --- | --- |
| `app.asar` SHA-256 | `529c221ca296b634559f374d6a2d71fbd3e940d79ad4e3bc361d09df9ef92506` — matches P0.2a |
| `app.asar` size | 2,259,976 bytes, 272 entries |
| Bundle identifier | `local.chief-of-staff.desktop` |
| Version | `0.1.0` |
| Architecture | arm64 (thin) |
| Signature | Apple Development `KXYQ8895ZL`, Team `98F559Y354`, hardened runtime, not notarized |
| `codesign --verify --deep --strict` | OK |
| Electron | 44.5.1 |
| Embedded asar integrity | `ElectronAsarIntegrity` present and enforced by build fuses |

### IPC and feature surface in the packaged bundle

| Check | Result |
| --- | --- |
| IPC handlers vs preload bridge | **48 / 48**, no orphans in either direction |
| Task channels | `chief:tasks-list`, `task-get/create/cancel/retry/history` |
| Device channels | 12 registry + credential channels |
| Enrollment channels | 6 pairing channels |
| `cosd` control channels | 5 (connection, reconnect, start, stop, restart) |
| Queue and runtime | `chief:queue`, `chief:runtime-snapshot` |
| Packaged modules | `cosd/client`, `cosd/connection`, `cosd/event-stream`, `ipc-cosd`, `devices`, `notifications`, `chief-runtime` |
| Renderer surface | Devices, Pairing, Task center, Queue, Agents & builds, Settings |

### Raycast independence

- String `Raycast` **absent** from the packaged renderer bundle.
- No `raycast` import or dependency in `apps/chief-desktop/src`.
- All capability paths go through the in-process IPC bridge, `bin/cos`, or `cosd`.

---

## 5. Backup provenance (created this mission)

| Field | Value |
| --- | --- |
| Path | `~/ChiefBackups/pre-p0.2b-24c9df4/Chief.app` |
| Copy method | `ditto` (preserves signature and bundle metadata) |
| `app.asar` SHA-256 | `193377246224b378aa5535db2632c59f30f45ba73a0e4218b8035b071bba6115` |
| Signature | valid (`codesign --verify --deep --strict`) |
| Version / id | `0.1.0` / `local.chief-of-staff.desktop` |
| Source commit | `24c9df4` |
| Manifest | `~/ChiefBackups/pre-p0.2b-24c9df4/manifest.txt` (identity, hash, signature, provenance) |
| Existing historical backups | none existed; nothing was overwritten |

Verification: the backup's `app.asar` hash is byte-identical to the installed bundle's.

---

## 6. Production state preflight

| Check | Result |
| --- | --- |
| State root `~/Library/Application Support/ChiefOfStaff` | present, mode **0700**, owner `owen` |
| Existing entries (names only) | `audit.initialized`, `audit.jsonl`, `cache/`, `config.json`, `desktop.json`, `eventkit/`, `search_usage.json`, `sessions/` |
| Token | **absent** (`cosd/` does not exist) — no credential to preserve or rotate |
| `cosd/` subdirectory | absent; will be created `0700` on first start by the P0.2a fix |
| Keychain references | none created by `cosd` (device registry never used in production) |
| LaunchAgents | **none** for Chief or `cosd` |
| Running `cosd` | none |
| Running Chief.app | PID 94583 |

The P0.2a permission correction is safe here: it chmods only the two directories, never their
contents, and the state root is already `0700`.

**No existing state will be migrated, deleted or rotated.** The only new artifact of activation is
`<state>/cosd/`.

---

## 7. Stage B — activation procedure (REQUIRES OWNER APPROVAL)

Do not execute any step below without Owen's explicit confirmation. Each step is bounded.

```bash
cd ~/Projects/teacher-ai-workstation

# 0. Preflight must be green apart from the known dependency warning.
./scripts/chief-activation-preflight.sh

# 1. Create the isolated runtime (owner-approved install; no global pip).
mkdir -p ~/.chief-runtime && chmod 700 ~/.chief-runtime
python3.12 -m venv ~/.chief-runtime/venv
~/.chief-runtime/venv/bin/python -m pip install --upgrade pip
~/.chief-runtime/venv/bin/python -m pip install -r requirements-cosd-pairing.txt
printf '%s\n' "$HOME/.chief-runtime/venv/bin/python" > ~/.chief-runtime/python

# 2. The dependency gate must now be PASS, not WARN.
CHIEF_PYTHON="$HOME/.chief-runtime/venv/bin/python" \
  ./scripts/chief-cosd-dependency-status.sh --require

# 3. Quit Chief.app from the menu bar (owner action; do not force-quit).

# 4. Record what is being replaced, then verify the backup again.
shasum -a 256 /Applications/Chief.app/Contents/Resources/app.asar
shasum -a 256 ~/ChiefBackups/pre-p0.2b-24c9df4/Chief.app/Contents/Resources/app.asar

# 5. Install the certified candidate.
mv /Applications/Chief.app /Applications/Chief.app.p0.2b-replaced
ditto apps/chief-desktop/release/p0.2a-candidate/mac-arm64/Chief.app /Applications/Chief.app

# 6. Verify what actually landed.
shasum -a 256 /Applications/Chief.app/Contents/Resources/app.asar
#   expect 529c221ca296b634559f374d6a2d71fbd3e940d79ad4e3bc361d09df9ef92506
codesign --verify --deep --strict /Applications/Chief.app
CHIEF_EXPECTED_INSTALLED_ASAR=529c221ca296b634559f374d6a2d71fbd3e940d79ad4e3bc361d09df9ef92506 \
  ./scripts/chief-activation-preflight.sh

# 7. Start production cosd once, in the foreground-checked way.
./bin/cosd start
./bin/cosd health
./bin/cosd status

# 8. Verify the runtime is the daemon, not the CLI fallback.
#    Chief.app shows the runtime state in Settings; the status payload must report
#    host 127.0.0.1 and the daemon pid.

# 9. Owner launches Chief.app from /Applications (single launch, no automation).
```

No LaunchAgent is created. No Tailscale. No device is enrolled. No credential is rotated.

### Deployment-state distinction

- **Step 6 completes:** the application is *installed*.
- **Step 7 completes:** the daemon is *running*.
- **Step 8/9 complete:** the pair is *verified*.
- Only then may this be described as **deployed**. Until Owen confirms step 9, the classification
  remains PREPARED.

---

## 8. Post-activation verification

| Check | Command / evidence |
| --- | --- |
| Loopback-only bind | `lsof -nP -iTCP:$(bin/cosd status | …) -sTCP:LISTEN` → `127.0.0.1` only |
| Bearer auth succeeds | `bin/cosd status` |
| Invalid auth rejected | bearer probe → 401 |
| Token not logged | grep the state tree for the token value → only `api.token` |
| Kill switch | `bin/cos stop` → `cos ask` refused → `bin/cos resume` |
| Task registry | `bin/cosd tasks list` |
| Queue state | `bin/cosd queue status` |
| Device registry intact | `bin/cosd devices list` (no enrollment) |
| Pairing available | `scripts/chief-cosd-dependency-status.sh --require` → PASS |
| App uses daemon | Settings/runtime snapshot reports `cosd`, not fallback |
| Raycast absent | app runs with Raycast never installed |

Automated where possible; the GUI checks in the last two rows require Owen.

---

## 9. Rollback

Prepared before activation. Rollback never deletes state.

```bash
# 1. Stop only the daemon this activation started.
./bin/cosd stop

# 2. Restore the verified prior bundle.
rm -rf /Applications/Chief.app
mv /Applications/Chief.app.p0.2b-replaced /Applications/Chief.app

# 3. Or, from the independent backup:
#    ditto ~/ChiefBackups/pre-p0.2b-24c9df4/Chief.app /Applications/Chief.app

# 4. Verify the restored bundle.
shasum -a 256 /Applications/Chief.app/Contents/Resources/app.asar
#   expect 193377246224b378aa5535db2632c59f30f45ba73a0e4218b8035b071bba6115
codesign --verify --deep --strict /Applications/Chief.app
```

State handling on rollback:

- `<state>/cosd/` (token, auth metadata, SQLite) **is preserved**. The old application does not use
  it, and the new one can resume from it after a later retry.
- `audit.jsonl`, `config.json`, `sessions/`, `cache/` are untouched.
- The runtime marker `~/.chief-runtime/python` may be left in place; the old application does not
  read it. Removing it is optional and non-destructive.

---

## 10. What this mission did **not** do

- Did not replace `/Applications/Chief.app`.
- Did not start a production `cosd`.
- Did not create or modify production state.
- Did not install `cryptography`, globally or in a venv.
- Did not create a LaunchAgent.
- Did not enroll a device or touch credentials.
- Did not launch, focus, or automate the visible application.

---

## 11. Owner approval checkpoints

Stage B needs explicit approval for each of:

1. Replacing `/Applications/Chief.app`.
2. Starting production `cosd`.
3. Creating production runtime state (`<state>/cosd/`).
4. Installing `cryptography` into `~/.chief-runtime/venv` and writing the runtime marker.
5. Launching Chief.app to confirm daemon connectivity.

Approval for one does not imply approval for the rest.
