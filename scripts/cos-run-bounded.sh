#!/usr/bin/env bash
# Bounded subprocess runner with process-group containment (portable; no GNU
# timeout; works with macOS /bin/bash 3.2).
#
# Usage:
#   cos-run-bounded.sh <timeout_seconds> <command...>
#
# Runs <command...> in its own process group, forwarding stdout/stderr. If it
# exceeds <timeout_seconds>, or this runner is interrupted (INT/TERM), the
# WHOLE group (child, grandchildren, anything they spawned without leaving the
# group) gets TERM, then a short grace period, then KILL. On EXIT the runner
# also sweeps any group members left behind after a normal child exit.
#
# The watchdog is a separate process group with all output sent to /dev/null,
# so it never holds the caller's stdout pipe open (safe inside $(...)), and the
# runner returns as soon as the child exits (no polling delay).
#
# Nested runners: each level exports COS_BOUNDED_DEPTH and halves its grace
# period, so an inner runner finishes its own TERM -> KILL sweep before the
# outer runner's grace period ends.
#
# Exit codes (the child's code is passed through unchanged; status scripts and
# the dashboard use 0/1/2):
#   0    PASS  (child exited 0)
#   1    WARN  (child exited 1)
#   2    FAIL  (child exited 2, or runner usage error)
#   124  TIMEOUT: the runner terminated the group after <timeout_seconds>.
#        124 is never produced by a child exit code being remapped; it always
#        means a timeout, and the runner prints
#        "cos-run-bounded: TIMED OUT after <N>s" to stderr as evidence.
#   130  runner interrupted by INT (group terminated)
#   143  runner terminated by TERM (group terminated)
#   N    any other child exit code, passed through
#
# Environment:
#   COS_BOUNDED_GRACE_SECS  TERM -> KILL grace at depth 0 (default 2).
#   COS_BOUNDED_DEPTH       Set by the runner for nested calls; do not set.
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

depth="${COS_BOUNDED_DEPTH:-0}"
[[ "${depth}" =~ ^[0-9]+$ ]] || depth=0
grace_secs="${COS_BOUNDED_GRACE_SECS:-2}"
[[ "${grace_secs}" =~ ^[0-9]+$ ]] || grace_secs=2
# Grace in tenths of a second, halved per nesting level, minimum 0.2s.
grace_tenths=$(( (grace_secs * 10) >> (depth > 6 ? 6 : depth) ))
(( grace_tenths < 2 )) && grace_tenths=2
export COS_BOUNDED_DEPTH=$((depth + 1))

child_pid=""
watchdog_pid=""
timed_out=0
stopping=0

group_alive() {
  kill -0 -- "-$1" 2>/dev/null
}

# TERM the whole group, wait up to the grace period, then KILL what is left.
stop_group() {
  local pgid="$1"
  local i=0
  [[ -n "${pgid}" ]] || return 0
  group_alive "${pgid}" || return 0
  kill -TERM -- "-${pgid}" 2>/dev/null
  while (( i < grace_tenths )) && group_alive "${pgid}"; do
    sleep 0.1
    i=$((i + 1))
  done
  if group_alive "${pgid}"; then
    kill -KILL -- "-${pgid}" 2>/dev/null
  fi
  return 0
}

stop_watchdog() {
  if [[ -n "${watchdog_pid}" ]]; then
    kill -KILL -- "-${watchdog_pid}" 2>/dev/null
    wait "${watchdog_pid}" 2>/dev/null
    watchdog_pid=""
  fi
  return 0
}

on_timeout() {
  timed_out=1
  stop_group "${child_pid}"
}

on_signal() {
  local code="$1"
  if (( stopping == 0 )); then
    stopping=1
    stop_group "${child_pid}"
  fi
  exit "${code}"
}

on_exit() {
  stop_watchdog
  stop_group "${child_pid}"
}

trap on_timeout USR1
trap 'on_signal 130' INT
trap 'on_signal 143' TERM
trap on_exit EXIT

# Job control on only while forking, so each background job gets its own
# process group; off again so foreground helpers (sleep) never touch the tty.
set -m
if [[ -t 0 ]]; then
  # A background process group cannot read the terminal; never let it stop.
  "$@" </dev/null &
else
  "$@" &
fi
child_pid=$!
(
  trap - INT TERM USR1 EXIT
  sleep "${timeout_secs}"
  kill -USR1 "$$" 2>/dev/null
) </dev/null >/dev/null 2>&1 &
watchdog_pid=$!
set +m

rc=0
while :; do
  wait "${child_pid}" 2>/dev/null
  rc=$?
  kill -0 "${child_pid}" 2>/dev/null || break
done

stop_watchdog

if (( timed_out == 1 )); then
  stop_group "${child_pid}"
  echo "cos-run-bounded: TIMED OUT after ${timeout_secs}s" >&2
  exit 124
fi

exit "${rc}"
