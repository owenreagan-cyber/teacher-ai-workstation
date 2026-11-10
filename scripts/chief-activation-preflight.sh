#!/usr/bin/env bash
# Chief: P0.2b activation preflight.
#
# Read-only. Verifies the installed application, the prepared backup, the
# candidate package and the production state, then reports PASS/WARN/FAIL.
# It never copies, installs, starts, stops or edits anything.
#
# Expected hashes are overridable so the same script works before and after an
# activation:
#   CHIEF_EXPECTED_INSTALLED_ASAR   default: the pre-P0.2b bundle (24c9df4)
#   CHIEF_EXPECTED_CANDIDATE_ASAR   default: the P0.2a candidate
#   CHIEF_EXPECTED_BACKUP_ASAR      default: the pre-P0.2c installed bundle; set this
#                                   to the bundle that was backed up, so the backup
#                                   check stays meaningful after activation replaces
#                                   the installed app
#   CHIEF_CANDIDATE                 candidate bundle path
#   CHIEF_BACKUP                    backup bundle path
#
# Exit 0 for PASS/WARN, 1 if any FAIL is reported.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
INSTALLED="${CHIEF_INSTALLED:-/Applications/Chief.app}"
CANDIDATE="${CHIEF_CANDIDATE:-${ROOT}/apps/chief-desktop/release/p0.2a-candidate/mac-arm64/Chief.app}"
BACKUP="${CHIEF_BACKUP:-${HOME}/ChiefBackups/pre-p0.2b-24c9df4/Chief.app}"
EXPECTED_INSTALLED_ASAR="${CHIEF_EXPECTED_INSTALLED_ASAR:-193377246224b378aa5535db2632c59f30f45ba73a0e4218b8035b071bba6115}"
EXPECTED_CANDIDATE_ASAR="${CHIEF_EXPECTED_CANDIDATE_ASAR:-529c221ca296b634559f374d6a2d71fbd3e940d79ad4e3bc361d09df9ef92506}"
EXPECTED_BACKUP_ASAR="${CHIEF_EXPECTED_BACKUP_ASAR:-193377246224b378aa5535db2632c59f30f45ba73a0e4218b8035b071bba6115}"
STATE_DIR="${COS_STATE_DIR:-${HOME}/Library/Application Support/ChiefOfStaff}"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n## %s\n' "$1"; }

asar_hash() {
  [ -f "$1/Contents/Resources/app.asar" ] || { printf 'missing'; return; }
  shasum -a 256 "$1/Contents/Resources/app.asar" | awk '{print $1}'
}

signed() {
  codesign --verify --deep --strict "$1" >/dev/null 2>&1 && printf 'OK' || printf 'INVALID'
}

plist() {
  plutil -extract "$2" raw "$1/Contents/Info.plist" 2>/dev/null || printf 'unknown'
}

section 'Installed application'
if [ -d "${INSTALLED}" ]; then
  installed_hash="$(asar_hash "${INSTALLED}")"
  pass "installed bundle present: ${INSTALLED}"
  if [ "${installed_hash}" = "${EXPECTED_INSTALLED_ASAR}" ]; then
    pass "installed app.asar matches the recorded baseline (${installed_hash:0:12}…)"
  else
    warn "installed app.asar is ${installed_hash:0:12}…, expected ${EXPECTED_INSTALLED_ASAR:0:12}… (already activated, or drifted)"
  fi
  [ "$(signed "${INSTALLED}")" = "OK" ] && pass 'installed signature valid' || fail 'installed signature invalid'
  pass "installed identity: $(plist "${INSTALLED}" CFBundleIdentifier) $(plist "${INSTALLED}" CFBundleShortVersionString)"
else
  fail "installed bundle missing: ${INSTALLED}"
fi

section 'Prepared backup'
if [ -d "${BACKUP}" ]; then
  backup_hash="$(asar_hash "${BACKUP}")"
  pass "backup present: ${BACKUP}"
  if [ "${backup_hash}" = "${EXPECTED_BACKUP_ASAR}" ]; then
    pass "backup matches the recorded pre-activation baseline (${backup_hash:0:12}…)"
  elif [ -n "${installed_hash:-}" ] && [ "${backup_hash}" = "${installed_hash}" ]; then
    pass "backup is byte-identical to the installed app"
  else
    fail "backup app.asar ${backup_hash:0:12}… matches neither the expected baseline nor the installed app"
  fi
  [ "$(signed "${BACKUP}")" = "OK" ] && pass 'backup signature valid' || fail 'backup signature invalid'
  [ -f "${BACKUP}/../manifest.txt" ] || [ -f "$(dirname "${BACKUP}")/manifest.txt" ] \
    && pass 'backup manifest present' || warn 'backup manifest missing'
else
  fail "backup missing: ${BACKUP}"
fi

section 'Candidate package'
if [ -d "${CANDIDATE}" ]; then
  cand_hash="$(asar_hash "${CANDIDATE}")"
  pass "candidate present: ${CANDIDATE}"
  if [ "${cand_hash}" = "${EXPECTED_CANDIDATE_ASAR}" ]; then
    pass "candidate app.asar matches the certified hash (${cand_hash:0:12}…)"
  else
    fail "candidate app.asar ${cand_hash:0:12}… != certified ${EXPECTED_CANDIDATE_ASAR:0:12}…"
  fi
  [ "$(signed "${CANDIDATE}")" = "OK" ] && pass 'candidate signature valid' || fail 'candidate signature invalid'
  cand_id="$(plist "${CANDIDATE}" CFBundleIdentifier)"
  [ "${cand_id}" = "local.chief-of-staff.desktop" ] && pass "bundle id ${cand_id}" || fail "unexpected bundle id ${cand_id}"
  arch="$(file "${CANDIDATE}/Contents/MacOS/Chief" 2>/dev/null | sed 's/.*: //')"
  case "${arch}" in
    *arm64*) pass "architecture arm64" ;;
    *) fail "unexpected architecture: ${arch}" ;;
  esac
else
  fail "candidate missing: ${CANDIDATE}"
fi

section 'Candidate contents'
if [ -f "${CANDIDATE}/Contents/Resources/app.asar" ]; then
  python3 - "${CANDIDATE}/Contents/Resources/app.asar" <<'PY' || fail 'candidate contents could not be inspected'
import json, struct, sys
raw = open(sys.argv[1], "rb").read()
hl = struct.unpack("<I", raw[4:8])[0]
jl = struct.unpack("<I", raw[12:16])[0]
hdr = json.loads(raw[16:16 + jl].decode())
base = 8 + hl

def walk(node, prefix=""):
    out = {}
    for name, meta in node.get("files", {}).items():
        path = f"{prefix}/{name}" if prefix else name
        if "files" in meta:
            out.update(walk(meta, path))
        else:
            out[path] = (int(meta.get("offset", 0)), int(meta.get("size", 0)))
    return out

files = walk(hdr)
required = ["out/main/cosd/client.js", "out/main/ipc-cosd.js", "out/shared/devices.js",
            "out/main/notifications.js", "out/main/chief-runtime.js"]
missing = [f for f in required if f not in files]
if missing:
    print(f"FAIL: candidate is missing {missing}")
    sys.exit(1)
print("PASS: cosd client, task IPC, devices, notifications and runtime are packaged")

renderer = [f for f in files if f.startswith("dist/renderer/assets/index-") and f.endswith(".js")]
if not renderer:
    print("FAIL: renderer bundle missing")
    sys.exit(1)
offset, size = files[renderer[0]]
js = raw[base + offset: base + offset + size].decode("utf-8", "replace")
for label in ("Devices", "Pairing", "Task center", "Queue"):
    if label not in js:
        print(f"FAIL: renderer is missing '{label}'")
        sys.exit(1)
print("PASS: renderer exposes Devices, Pairing, Task center and Queue")
if "Raycast" in js:
    print("FAIL: renderer mentions Raycast; independence is broken")
    sys.exit(1)
print("PASS: renderer has no Raycast dependency")
PY
else
  fail 'candidate app.asar unavailable'
fi

section 'Runtime dependency'
if [ -x "${ROOT}/scripts/chief-cosd-dependency-status.sh" ]; then
  set +e
  dep_out="$("${ROOT}/scripts/chief-cosd-dependency-status.sh" 2>&1)"
  dep_rc=$?
  set -e
  if [ "${dep_rc}" -ne 0 ]; then
    fail 'pairing dependency check reported FAIL'
  elif printf '%s\n' "${dep_out}" | grep -Eq '^WARN: [^0-9]'; then
    warn 'cryptography is not installed in the default runtime (pairing fails closed); activation needs CHIEF_PYTHON or an approved install'
  else
    pass 'pairing dependency ready'
  fi
else
  fail 'dependency readiness script missing'
fi

section 'Production state'
if [ -d "${STATE_DIR}" ]; then
  mode="$(stat -f '%Lp' "${STATE_DIR}")"
  [ "${mode}" = "700" ] && pass "state directory mode ${mode}" || fail "state directory mode ${mode} (must be 700)"
  if [ -f "${STATE_DIR}/cosd/api.token" ]; then
    token_mode="$(stat -f '%Lp' "${STATE_DIR}/cosd/api.token")"
    [ "${token_mode}" = "600" ] && pass 'token present with mode 600 (contents not read)' || fail "token mode ${token_mode} (must be 600)"
  else
    pass 'no cosd token yet (daemon has not run against production state)'
  fi
  if [ -d "${STATE_DIR}/cosd" ]; then
    [ "$(stat -f '%Lp' "${STATE_DIR}/cosd")" = "700" ] \
      && pass 'cosd state subdirectory mode 700' \
      || warn "cosd state subdirectory mode $(stat -f '%Lp' "${STATE_DIR}/cosd"); cosd will correct it on start"
  fi
  for entry in audit.jsonl config.json sessions cache; do
    [ -e "${STATE_DIR}/${entry}" ] && pass "existing state preserved: ${entry}"
  done
else
  warn "state directory absent: ${STATE_DIR}"
fi

section 'Processes and startup'
if pgrep -f 'from cosd\.cli import main' >/dev/null 2>&1; then
  warn "a cosd process is running: $(pgrep -f 'from cosd\.cli import main' | head -1)"
else
  pass 'no cosd process running'
fi
if pgrep -f 'Chief.app/Contents/MacOS/Chief' >/dev/null 2>&1; then
  pass "Chief.app is running (pid $(pgrep -f 'Chief.app/Contents/MacOS/Chief' | head -1))"
else
  pass 'Chief.app is not running'
fi
if ls "${HOME}/Library/LaunchAgents" 2>/dev/null | grep -qi 'chief\|cosd'; then
  fail 'a Chief LaunchAgent exists; activation must not install one'
else
  pass 'no Chief LaunchAgent installed'
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[ "${FAIL_COUNT}" -gt 0 ] && exit 1
exit 0
