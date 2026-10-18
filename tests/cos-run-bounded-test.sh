#!/usr/bin/env bash
# Process-group containment tests for scripts/cos-run-bounded.sh
# (bounded, deterministic, no network). Checks that no process from the
# bounded group survives a timeout, an interrupt, or a nested timeout, that
# exit codes pass through with 124 kept distinct, and that the runner adds no
# per-call delay.
set -euo pipefail

echo "Running cos-run-bounded containment tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

RUNNER="${REPO_ROOT}/scripts/cos-run-bounded.sh"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/cos-run-bounded-test.XXXXXX")"
trap 'rm -rf "${tmp}"' EXIT
export COS_BOUNDED_GRACE_SECS=1

fail() {
  echo "FAIL: $1"
  exit 1
}

wait_for_file() {
  local path="$1"
  local i=0
  while [[ ! -s "${path}" ]]; do
    (( i < 100 )) || fail "timed out waiting for ${path}"
    sleep 0.1
    i=$((i + 1))
  done
}

assert_gone() {
  local what="$1"
  local pid="$2"
  if kill -0 "${pid}" 2>/dev/null; then
    kill -KILL "${pid}" 2>/dev/null || true
    fail "${what} (pid ${pid}) survived"
  fi
}

assert_group_gone() {
  local what="$1"
  local pgid="$2"
  if kill -0 -- "-${pgid}" 2>/dev/null; then
    kill -KILL -- "-${pgid}" 2>/dev/null || true
    fail "${what} (process group ${pgid}) still has members"
  fi
}

# A leaf that ignores TERM (and passes the ignore on to its sleep children).
cat > "${tmp}/stubborn.sh" <<'SH'
#!/usr/bin/env bash
trap '' TERM
echo $$ > "$1"
while :; do sleep 0.2; done
SH
chmod +x "${tmp}/stubborn.sh"

# A child that starts the stubborn leaf as a grandchild and waits on it.
cat > "${tmp}/parent.sh" <<'SH'
#!/usr/bin/env bash
echo $$ > "$1"
"$(dirname "$0")/stubborn.sh" "$2" &
wait
SH
chmod +x "${tmp}/parent.sh"

# ---------------------------------------------------------------------------
# 1. Timeout: a grandchild that ignores TERM does not survive.
# ---------------------------------------------------------------------------
start="$(date +%s)"
set +e
"${RUNNER}" 1 "${tmp}/parent.sh" "${tmp}/t1-child.pid" "${tmp}/t1-grandchild.pid" 2>"${tmp}/t1.err"
rc=$?
set -e
elapsed=$(( $(date +%s) - start ))
[[ "${rc}" == "124" ]] || fail "timeout returned ${rc} (expected 124)"
grep -q 'cos-run-bounded: TIMED OUT after 1s' "${tmp}/t1.err" || fail "no timeout evidence on stderr"
(( elapsed <= 5 )) || fail "timeout took ${elapsed}s for a 1s budget"
child="$(cat "${tmp}/t1-child.pid")"
grandchild="$(cat "${tmp}/t1-grandchild.pid")"
assert_gone "child" "${child}"
assert_gone "TERM-ignoring grandchild" "${grandchild}"
assert_group_gone "bounded group" "${child}"
echo "PASS timeout kills the whole group, including a TERM-ignoring grandchild"

# ---------------------------------------------------------------------------
# 2. Interrupt: INT (and TERM) to the runner terminate the whole group.
# ---------------------------------------------------------------------------
for sig in INT TERM; do
  rm -f "${tmp}/t2-child.pid" "${tmp}/t2-grandchild.pid"
  # Job control so the runner does not start with INT ignored (as it would as
  # a plain background job of a non-interactive shell).
  set -m
  "${RUNNER}" 60 "${tmp}/parent.sh" "${tmp}/t2-child.pid" "${tmp}/t2-grandchild.pid" &
  runner_pid=$!
  set +m
  wait_for_file "${tmp}/t2-grandchild.pid"
  kill "-${sig}" "${runner_pid}"
  set +e
  wait "${runner_pid}"
  rc=$?
  set -e
  if [[ "${sig}" == "INT" ]]; then expected=130; else expected=143; fi
  [[ "${rc}" == "${expected}" ]] || fail "${sig} returned ${rc} (expected ${expected})"
  child="$(cat "${tmp}/t2-child.pid")"
  grandchild="$(cat "${tmp}/t2-grandchild.pid")"
  assert_gone "child after ${sig}" "${child}"
  assert_gone "grandchild after ${sig}" "${grandchild}"
  assert_group_gone "bounded group after ${sig}" "${child}"
done
echo "PASS interrupted run (INT -> 130, TERM -> 143) leaves no group member"

# ---------------------------------------------------------------------------
# 3. Nested bounded calls.
# ---------------------------------------------------------------------------
out="$("${RUNNER}" 10 "${RUNNER}" 5 sh -c 'echo nested-ok; exit 1')" && rc=0 || rc=$?
[[ "${out}" == "nested-ok" ]] || fail "nested call did not forward stdout (got '${out}')"
[[ "${rc}" == "1" ]] || fail "nested call returned ${rc} (expected 1)"

# Outer times out while the inner runner (longer budget) is still running.
start="$(date +%s)"
set +e
"${RUNNER}" 1 "${RUNNER}" 60 "${tmp}/parent.sh" "${tmp}/t3-child.pid" "${tmp}/t3-grandchild.pid" 2>/dev/null
rc=$?
set -e
elapsed=$(( $(date +%s) - start ))
[[ "${rc}" == "124" ]] || fail "nested outer timeout returned ${rc} (expected 124)"
(( elapsed <= 5 )) || fail "nested timeout took ${elapsed}s"
child="$(cat "${tmp}/t3-child.pid")"
grandchild="$(cat "${tmp}/t3-grandchild.pid")"
assert_gone "inner child" "${child}"
assert_gone "inner TERM-ignoring grandchild" "${grandchild}"
assert_group_gone "inner bounded group" "${child}"

# Inner times out first; the outer runner reports the inner 124 as-is.
set +e
"${RUNNER}" 30 "${RUNNER}" 1 "${tmp}/parent.sh" "${tmp}/t4-child.pid" "${tmp}/t4-grandchild.pid" 2>/dev/null
rc=$?
set -e
[[ "${rc}" == "124" ]] || fail "nested inner timeout returned ${rc} (expected 124)"
assert_gone "inner child" "$(cat "${tmp}/t4-child.pid")"
assert_gone "inner grandchild" "$(cat "${tmp}/t4-grandchild.pid")"
echo "PASS nested bounded calls forward output and contain both levels"

# ---------------------------------------------------------------------------
# 4. Exit codes pass through; 124 stays distinct from child signal exits.
# ---------------------------------------------------------------------------
for code in 0 1 2 7; do
  set +e
  "${RUNNER}" 5 sh -c "exit ${code}"
  rc=$?
  set -e
  [[ "${rc}" == "${code}" ]] || fail "exit ${code} passed through as ${rc}"
done
set +e
"${RUNNER}" 5 sh -c 'kill -TERM $$' 2>/dev/null
rc=$?
set -e
[[ "${rc}" == "143" ]] || fail "child killed by its own TERM reported ${rc} (expected 143, not 124)"
set +e
"${RUNNER}" 2>/dev/null
rc=$?
set -e
[[ "${rc}" == "2" ]] || fail "usage error returned ${rc} (expected 2)"
echo "PASS exit codes 0/1/2/N pass through; 124 only means timeout"

# ---------------------------------------------------------------------------
# 5. Leftover background members are swept when the child exits normally.
# ---------------------------------------------------------------------------
cat > "${tmp}/leaves-behind.sh" <<'SH'
#!/usr/bin/env bash
"$(dirname "$0")/stubborn.sh" "$1" >/dev/null 2>&1 &
while [[ ! -s "$1" ]]; do sleep 0.05; done
echo $$ > "$2"
exit 0
SH
chmod +x "${tmp}/leaves-behind.sh"
"${RUNNER}" 10 "${tmp}/leaves-behind.sh" "${tmp}/t5-leftover.pid" "${tmp}/t5-child.pid"
assert_gone "leftover background process" "$(cat "${tmp}/t5-leftover.pid")"
assert_group_gone "group after normal exit" "$(cat "${tmp}/t5-child.pid")"
echo "PASS leftover group members are swept on normal exit"

# ---------------------------------------------------------------------------
# 6. No per-call delay: 20 quick bounded calls stay well under 5s.
# ---------------------------------------------------------------------------
start="$(date +%s)"
for _ in $(seq 1 20); do
  "${RUNNER}" 30 true
done
elapsed=$(( $(date +%s) - start ))
(( elapsed < 5 )) || fail "20 quick bounded calls took ${elapsed}s"
echo "PASS bounded runner returns as soon as the child exits (20 calls in ${elapsed}s)"

echo "PASS: cos-run-bounded containment tests complete"
