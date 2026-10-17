#!/usr/bin/env bash
# Bounded subprocess runner with clean child cleanup (portable; no GNU timeout).
#
# Usage:
#   cos-run-bounded.sh <timeout_seconds> <command...>
#
# Runs <command...> forwarding stdout/stderr. If it exceeds <timeout_seconds>,
# the child is terminated (TERM then KILL) and the runner returns 124. There is
# no background watchdog process, so no orphan processes and no stdout pipe is
# held open (safe for use inside command substitution).
#
# Exit codes:
#   0   child exited 0
#   124 timeout (child terminated)
#   N   child exited with code N
set -u

timeout_secs="${1:-}"
if [[ -z "${timeout_secs}" ]] || ! [[ "${timeout_secs}" =~ ^[0-9]+$ ]]; then
  echo "cos-run-bounded: invalid timeout '${timeout_secs:-}'" >&2
  exit 2
fi
shift

if [[ $# -eq 0 ]]; then
  echo "cos-run-bounded: no command provided" >&2
  exit 2
fi

"$@" &
child_pid=$!

elapsed=0
while kill -0 "${child_pid}" 2>/dev/null; do
  if (( elapsed >= timeout_secs )); then
    kill -TERM "${child_pid}" 2>/dev/null || true
    sleep 1
    kill -KILL "${child_pid}" 2>/dev/null || true
    break
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done

wait "${child_pid}" 2>/dev/null
rc=$?

if [[ "${rc}" == "143" || "${rc}" == "137" ]]; then
  echo "cos-run-bounded: TIMED OUT after ${timeout_secs}s" >&2
  exit 124
fi

exit "${rc}"
