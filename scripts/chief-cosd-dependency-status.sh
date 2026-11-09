#!/usr/bin/env bash
# Chief: cosd pairing dependency readiness.
#
# Read-only. This check never installs a package, never starts the daemon and
# never touches the state directory. It answers one question: can the runtime
# that `bin/cosd` actually selects perform authenticated credential delivery?
#
# Classification:
#   PASS  dependency installed and the real cipher is wired in
#   WARN  dependency absent, and pairing is correctly unavailable (fail closed)
#   FAIL  dependency absent while pairing is advertised, or installed but the
#         real cipher is not wired in
#
# Exit code is 0 for PASS and WARN, 1 for FAIL, so it can gate activation.
#
# Usage: scripts/chief-cosd-dependency-status.sh [--require]
#   --require  treat a missing dependency as FAIL (activation readiness gate)
set -euo pipefail

REQUIRE=0
for arg in "$@"; do
  case "${arg}" in
    --require) REQUIRE=1 ;;
    -h|--help) sed -n '2,25p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) printf 'FAIL: unknown argument: %s\n' "${arg}" >&2; exit 1 ;;
  esac
done

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n## %s\n' "$1"; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"

section 'Interpreter'

# Mirror bin/cos and bin/cosd exactly: CHIEF_PYTHON, then the isolated runtime
# marker, then python3.12 from PATH, then Homebrew. Reporting on a different
# interpreter than the one the runtime actually uses would make this gate lie.
PY=""
if [ -n "${CHIEF_PYTHON:-}" ]; then
  PY="${CHIEF_PYTHON}"
elif [ -f "${HOME}/.chief-runtime/python" ]; then
  PY="$(cat "${HOME}/.chief-runtime/python")"
  if [ ! -x "${PY}" ]; then
    fail "runtime marker points at a non-executable interpreter: ${PY}"
    printf '\n## Summary\n'
    printf 'PASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
    exit 1
  fi
elif command -v python3.12 >/dev/null 2>&1; then
  PY="$(command -v python3.12)"
elif [ -x /opt/homebrew/bin/python3.12 ]; then
  PY=/opt/homebrew/bin/python3.12
elif command -v python3 >/dev/null 2>&1 &&
     [ "$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)" = "3.12" ]; then
  # CI installs Python 3.12 as `python3` before it creates a python3.12 symlink.
  PY="$(command -v python3)"
fi

if [ -z "${PY}" ]; then
  fail 'python3.12 not found (bin/cosd would exit 127)'
  printf '\n## Summary\n'
  printf 'PASS: %s\nWARN: %s\nFAIL: %s\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"
  exit 1
fi

PY_VERSION="$("${PY}" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null || echo unknown)"
if [ "${PY_VERSION%%.*}" = "3" ] && [ "$(printf '%s' "${PY_VERSION}" | cut -d. -f2)" = "12" ]; then
  pass "interpreter ${PY} is Python ${PY_VERSION} (matches bin/cosd pin)"
else
  warn "interpreter ${PY} is Python ${PY_VERSION}; bin/cosd pins 3.12"
fi

section 'cryptography'

PROBE="$(
  cd "${ROOT}" && PYTHONPATH="${ROOT}" "${PY}" - <<'PY' 2>/dev/null || echo "probe_failed=1"
import json

result = {"importable": False, "version": "", "cipher": "", "usable": False, "error": ""}
try:
    import cryptography

    result["importable"] = True
    result["version"] = getattr(cryptography, "__version__", "unknown")
except Exception as exc:  # noqa: BLE001 - report, never install
    result["importable"] = False
    result["error"] = type(exc).__name__

try:
    from cosd.devices.pairing.crypto import default_envelope_cipher

    cipher = default_envelope_cipher()
    result["cipher"] = type(cipher).__name__
    result["algorithm"] = getattr(cipher, "algorithm", "unknown")
    result["usable"] = result["algorithm"] != "unavailable"
except Exception as exc:  # noqa: BLE001 - wiring itself is broken
    result["cipher"] = "unavailable"
    result["algorithm"] = "unknown"
    result["error"] = (result["error"] + " " + type(exc).__name__).strip()

print(json.dumps(result))
PY
)"

field() {
  printf '%s' "${PROBE}" | "${PY}" -c 'import json,sys; d=json.load(sys.stdin); print(d.get(sys.argv[1], ""))' "$1" 2>/dev/null || true
}

IMPORTABLE="$(field importable)"
VERSION="$(field version)"
CIPHER="$(field cipher)"
ALGORITHM="$(field algorithm)"
USABLE="$(field usable)"

if [ "${IMPORTABLE}" = "True" ] && [ "${USABLE}" = "True" ]; then
  pass "cryptography ${VERSION} importable; envelope cipher ${CIPHER} (${ALGORITHM})"
elif [ "${IMPORTABLE}" = "True" ] && [ "${USABLE}" != "True" ]; then
  fail "cryptography ${VERSION} is importable but ${CIPHER} reports '${ALGORITHM}': pairing would be unavailable despite the dependency"
elif [ "${IMPORTABLE}" != "True" ] && [ "${USABLE}" = "True" ]; then
  fail "pairing advertises ${CIPHER} without an importable cryptography package"
elif [ "${REQUIRE}" -eq 1 ]; then
  fail "cryptography is not installed; pairing credential delivery cannot run (required for activation)"
else
  warn "cryptography is not installed; pairing is correctly unavailable (owner approval returns 503 crypto_unavailable)"
fi

section 'Documented requirement'

REQ_FILE="${ROOT}/requirements-cosd-pairing.txt"
if [ -f "${REQ_FILE}" ]; then
  if grep -Eq '^[[:space:]]*cryptography[[:space:]]*>=' "${REQ_FILE}"; then
    pass 'requirements-cosd-pairing.txt pins cryptography>=42'
  else
    fail 'requirements-cosd-pairing.txt does not pin cryptography>=42'
  fi
else
  fail 'requirements-cosd-pairing.txt is missing'
fi

section 'Reproducible install path'

if [ -f "${ROOT}/docs/operations/master-chief-operational-certification.md" ] &&
   grep -Fq 'requirements-cosd-pairing.txt' "${ROOT}/docs/operations/master-chief-operational-certification.md"; then
  pass 'isolated-venv install procedure is documented'
else
  warn 'isolated-venv install procedure is not documented in the operational certification record'
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
