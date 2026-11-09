#!/usr/bin/env bash
# Chief: both entrypoints must resolve the same Python 3.12 interpreter, and an
# explicit CHIEF_PYTHON must be honoured or refused -- never silently ignored.
#
# This is the contract that lets P0.2b run an isolated Chief-owned venv as the
# one runtime for both `bin/cos` and `bin/cosd`. Read-only: it only asks for
# --version, and it never touches the real state directory.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
TMP_STATE="$(mktemp -d "${TMPDIR:-/tmp}/chief-interp-XXXXXX")"
cleanup() { rm -rf "${TMP_STATE}"; }
trap cleanup EXIT

export COS_STATE_DIR="${TMP_STATE}/state"
PASS_COUNT=0
FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

default_py="$(command -v python3.12 || true)"
[ -z "${default_py}" ] && [ -x /opt/homebrew/bin/python3.12 ] && default_py=/opt/homebrew/bin/python3.12

if [ -z "${default_py}" ]; then
  fail 'no python3.12 available to test against'
  printf '\nSummary\nPASS: %s\nFAIL: %s\n' "${PASS_COUNT}" "${FAIL_COUNT}"
  exit 1
fi

# 1. A missing explicit interpreter fails loudly.
for entry in cos cosd; do
  set +e
  out="$(CHIEF_PYTHON=/nonexistent/python3.12 "${ROOT}/bin/${entry}" --version 2>&1)"
  rc=$?
  set -e
  if [ "${rc}" -eq 127 ] && printf '%s' "${out}" | grep -q 'not executable'; then
    pass "${entry}: missing CHIEF_PYTHON exits 127 with a clear message"
  else
    fail "${entry}: missing CHIEF_PYTHON gave rc=${rc} out=${out}"
  fi
done

# 2. A non-interpreter explicit path is refused (not executed blindly).
for entry in cos cosd; do
  set +e
  out="$(CHIEF_PYTHON=/bin/true "${ROOT}/bin/${entry}" --version 2>&1)"
  rc=$?
  set -e
  if [ "${rc}" -eq 127 ]; then
    pass "${entry}: non-Python CHIEF_PYTHON is refused"
  else
    fail "${entry}: non-Python CHIEF_PYTHON gave rc=${rc}"
  fi
done

# 3. Each entrypoint runs on the pinned interpreter by default.
default_cos_py=""
for entry in cos cosd; do
  set +e
  cp_out="$(COS_PYTHON_PROBE=1 "${ROOT}/bin/${entry}" --version 2>&1)"
  rc=$?
  set -e
  if [ "${rc}" -eq 0 ]; then
    pass "${entry}: default interpreter runs (${cp_out%%$'\n'*})"
  else
    fail "${entry}: default interpreter failed rc=${rc}: ${cp_out}"
  fi
done

# 4. An explicit Python 3.12 interpreter is accepted and used by both.
for entry in cos cosd; do
  set +e
  out="$(CHIEF_PYTHON="${default_py}" "${ROOT}/bin/${entry}" --version 2>&1)"
  rc=$?
  set -e
  if [ "${rc}" -eq 0 ]; then
    pass "${entry}: explicit Python 3.12 accepted"
  else
    fail "${entry}: explicit Python 3.12 rejected rc=${rc}: ${out}"
  fi
done

# 5. The isolated-runtime marker is honoured when no CHIEF_PYTHON is set.
#    This is what lets a Finder-launched app use the venv without launchd env.
FAKEHOME="${TMP_STATE}/home"
mkdir -p "${FAKEHOME}/.chief-runtime"
MARKER_PY="${TMP_STATE}/marker-python"
cat > "${MARKER_PY}" <<MARKER
#!/usr/bin/env bash
exec "${default_py}" "\$@"
MARKER
chmod +x "${MARKER_PY}"
printf '%s' "${MARKER_PY}" > "${FAKEHOME}/.chief-runtime/python"

for entry in cos cosd; do
  set +e
  out="$(HOME="${FAKEHOME}" PATH="/usr/bin:/bin" CHIEF_PYTHON= "${ROOT}/bin/${entry}" --version 2>&1)"
  rc=$?
  set -e
  if [ "${rc}" -eq 0 ]; then
    pass "${entry}: ~/.chief-runtime/python marker honoured without launchd env"
  else
    fail "${entry}: runtime marker ignored rc=${rc}: ${out}"
  fi
done

# 5b. A stale marker fails closed rather than silently using another Python.
printf '%s' "/nonexistent/venv/bin/python" > "${FAKEHOME}/.chief-runtime/python"
for entry in cos cosd; do
  set +e
  out="$(HOME="${FAKEHOME}" CHIEF_PYTHON= "${ROOT}/bin/${entry}" --version 2>&1)"
  rc=$?
  set -e
  if [ "${rc}" -eq 127 ]; then
    pass "${entry}: stale runtime marker fails closed"
  else
    fail "${entry}: stale runtime marker gave rc=${rc}"
  fi
done

# 6. Both entrypoints agree on which interpreter they execute.
#    A shim earlier on PATH records each invocation, then execs the real 3.12.
FAKEBIN="${TMP_STATE}/bin"
mkdir -p "${FAKEBIN}"
CALLS="${TMP_STATE}/calls.log"
: > "${CALLS}"
cat > "${FAKEBIN}/python3.12" <<SHIM
#!/usr/bin/env bash
printf '%s\n' "\$0" >> "${CALLS}"
exec "${default_py}" "\$@"
SHIM
chmod +x "${FAKEBIN}/python3.12"

set +e
PATH="${FAKEBIN}:${PATH}" "${ROOT}/bin/cos" --version >/dev/null 2>&1
cos_rc=$?
PATH="${FAKEBIN}:${PATH}" "${ROOT}/bin/cosd" --version >/dev/null 2>&1
cosd_rc=$?
set -e

calls="$(wc -l < "${CALLS}" | tr -d ' ')"
if [ "${cos_rc}" -eq 0 ] && [ "${cosd_rc}" -eq 0 ] && [ "${calls}" -eq 2 ]; then
  pass "bin/cos and bin/cosd both resolve python3.12 through PATH (${calls} invocations)"
else
  fail "interpreter resolution disagreed: cos_rc=${cos_rc} cosd_rc=${cosd_rc} calls=${calls}"
fi

printf '\nSummary\nPASS: %s\nFAIL: %s\n' "${PASS_COUNT}" "${FAIL_COUNT}"
[ "${FAIL_COUNT}" -gt 0 ] && exit 1
exit 0
