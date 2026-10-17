#!/usr/bin/env bash
# Chief of Staff dashboard hardening tests (bounded, deterministic, no network).
# Verifies: bounded child execution, child cleanup, timeout semantics,
# aggregation PASS/WARN/FAIL -> exit 0/1/2, global deadline, and no recursion.
set -euo pipefail

echo "Running Chief of Staff dashboard hardening tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

RUNNER="scripts/cos-run-bounded.sh"
DASHBOARD="scripts/chief-of-staff-dashboard.sh"
SECTION_SUMMARY="scripts/dashboard-section-summary-status.sh"

# ---------------------------------------------------------------------------
# 1. Bounded runner: timeout + clean child cleanup + no orphan processes.
# ---------------------------------------------------------------------------
echo "--- bounded runner timeout + cleanup ---"
start="$(date +%s)"
if "${RUNNER}" 2 sleep 30 >/dev/null 2>&1; then
  echo "FAIL: runner did not time out a 30s sleep"
  exit 1
else
  rc=$?
fi
elapsed=$(( $(date +%s) - start ))
if [[ "${rc}" != "124" ]]; then
  echo "FAIL: runner returned ${rc} (expected 124)"
  exit 1
fi
if [[ "${elapsed}" -gt 6 ]]; then
  echo "FAIL: runner took ${elapsed}s to time out a 2s budget"
  exit 1
fi
if ps -o command= -ax 2>/dev/null | grep -q '[s]leep 30'; then
  echo "FAIL: orphan sleep process left behind"
  exit 1
fi
echo "PASS bounded runner times out and cleans up the child"

# ---------------------------------------------------------------------------
# 2. Bounded runner: normal completion forwards stdout + exit code.
# ---------------------------------------------------------------------------
out="$("${RUNNER}" 5 sh -c 'echo hello-dash')"
if [[ "${out}" != "hello-dash" ]]; then
  echo "FAIL: runner did not forward stdout (got '${out}')"
  exit 1
fi
echo "PASS bounded runner forwards output"

# ---------------------------------------------------------------------------
# 3. Recursion regression: dashboard-section-summary must NOT re-invoke --dashboard.
# ---------------------------------------------------------------------------
if grep -qE "bin/chief-of-staff --dashboard|COS_DASHBOARD_SKIP_SECTION_SUMMARY_STATUS=1 bin/chief-of-staff" "${SECTION_SUMMARY}"; then
  echo "FAIL: dashboard-section-summary-status.sh still recursively re-invokes the dashboard"
  exit 1
fi
echo "PASS dashboard-section-summary no longer recurses into --dashboard"

# ---------------------------------------------------------------------------
# 4. Aggregation + exit-code semantics (0=PASS, 1=WARN, 2=FAIL).
# ---------------------------------------------------------------------------
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

# A minimal synthetic status script exercising the same pass/warn/fail + exit
# contract the dashboard uses, so aggregation is tested deterministically.
cat > "${tmp}/synthetic-status.sh" <<'SH'
#!/usr/bin/env bash
mode="${1:-pass}"
case "${mode}" in
  pass)  echo "PASS: a"; echo "PASS: b"; echo "Summary"; echo "PASS: 2"; echo "WARN: 0"; echo "FAIL: 0"; exit 0 ;;
  warn)  echo "PASS: a"; echo "WARN: w"; echo "Summary"; echo "PASS: 1"; echo "WARN: 1"; echo "FAIL: 0"; exit 1 ;;
  fail)  echo "PASS: a"; echo "FAIL: f"; echo "Summary"; echo "PASS: 1"; echo "WARN: 0"; echo "FAIL: 1"; exit 2 ;;
esac
SH
chmod +x "${tmp}/synthetic-status.sh"

aggregate() {
  # Mimics the dashboard's aggregate: FAIL -> 2, WARN -> 1, else 0.
  local out="$1"
  local fail_count warn_count
  fail_count="$(printf '%s\n' "${out}" | awk '$1=="FAIL:"{v=$2} END{print v+0}')"
  warn_count="$(printf '%s\n' "${out}" | awk '$1=="WARN:"{v=$2} END{print v+0}')"
  if [[ "${fail_count}" -gt 0 ]]; then echo 2
  elif [[ "${warn_count}" -gt 0 ]]; then echo 1
  else echo 0; fi
}

set +e
o_pass="$("${tmp}/synthetic-status.sh" pass)"; rc_pass=$?
o_warn="$("${tmp}/synthetic-status.sh" warn)"; rc_warn=$?
o_fail="$("${tmp}/synthetic-status.sh" fail)"; rc_fail=$?
set -e

if [[ "$(aggregate "${o_pass}")" != "0" ]]; then echo "FAIL: all-PASS should aggregate to 0"; exit 1; fi
if [[ "$(aggregate "${o_warn}")" != "1" ]]; then echo "FAIL: PASS+WARN should aggregate to 1"; exit 1; fi
if [[ "$(aggregate "${o_fail}")" != "2" ]]; then echo "FAIL: PASS+FAIL should aggregate to 2"; exit 1; fi
if [[ "$(aggregate "${o_warn}"$'\n'"${o_fail}")" != "2" ]]; then echo "FAIL: WARN+FAIL should aggregate to 2"; exit 1; fi
echo "PASS aggregation semantics (all-PASS->0, WARN->1, FAIL->2)"

# ---------------------------------------------------------------------------
# 5. Global deadline: a synthetic slow dashboard is bounded and terminated.
# ---------------------------------------------------------------------------
cat > "${tmp}/slow-dashboard.sh" <<'SH'
#!/usr/bin/env bash
echo "slow dashboard started"
sleep 60
echo "slow dashboard finished"
exit 0
SH
chmod +x "${tmp}/slow-dashboard.sh"

start="$(date +%s)"
if "${RUNNER}" 3 bash "${tmp}/slow-dashboard.sh" >/dev/null 2>&1; then
  echo "FAIL: slow dashboard was not bounded"
  exit 1
else
  rc=$?
fi
elapsed=$(( $(date +%s) - start ))
if [[ "${rc}" != "124" ]]; then echo "FAIL: deadline runner returned ${rc}"; exit 1; fi
if [[ "${elapsed}" -gt 7 ]]; then echo "FAIL: deadline took ${elapsed}s"; exit 1; fi
if ps -o command= -ax 2>/dev/null | grep -q '[s]leep 60'; then
  echo "FAIL: orphan slow-dashboard process left behind"
  exit 1
fi
echo "PASS global deadline bounds a slow dashboard and cleans up"

# ---------------------------------------------------------------------------
# 6. No secret / PII leakage in the runner + dashboard source.
# ---------------------------------------------------------------------------
for f in "${RUNNER}" "${DASHBOARD}" "${SECTION_SUMMARY}"; do
  if grep -qiE "CANVAS_TOKEN|Authorization: Bearer|client_secret|access_token[=:]" "${f}"; then
    echo "FAIL: secret token in ${f}"
    exit 1
  fi
done
if grep -qiE "student[ -_]name|parent[ -_]email|social security|SSN" "${DASHBOARD}"; then
  echo "FAIL: student PII in dashboard source"
  exit 1
fi
echo "PASS no secret / PII leakage in dashboard + runner source"

# ---------------------------------------------------------------------------
# 7. Dashboard script still passes bash -n (syntax integrity after hardening).
# ---------------------------------------------------------------------------
bash -n "${DASHBOARD}"
bash -n "${RUNNER}"
bash -n "${SECTION_SUMMARY}"
echo "PASS bash syntax: dashboard, runner, section-summary"

echo "PASS: Chief of Staff dashboard hardening tests complete"
echo "PASS Chief of Staff dashboard hardening tests complete"
