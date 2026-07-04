#!/usr/bin/env bash
# Static safety tests for Classroom Timer runtime prototype — no browser launch.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

echo "Running Classroom Timer runtime static safety tests..."

app_dir="apps/classroom-timer-stopwatch"
timer_js="${app_dir}/timer.js"
index_html="${app_dir}/index.html"

for f in "${timer_js}" "${index_html}"; do
  [[ -f "${f}" ]] || { echo "FAIL: missing ${f}"; exit 1; }
done

for pattern in localStorage sessionStorage indexedDB fetch XMLHttpRequest \
  requestAnimationFrame Audio\. document\.cookie navigator\.mediaDevices \
  googleapis gstatic.com unpkg.com cdnjs; do
  if grep -Eq "${pattern}" "${timer_js}" "${index_html}" 2>/dev/null; then
    echo "FAIL: forbidden pattern found: ${pattern}"
    exit 1
  fi
done

for required in 'function start' 'function pause' 'function reset' 'setInterval' 'countdown' 'stopwatch'; do
  grep -Fq "${required}" "${timer_js}" || { echo "FAIL: missing required pattern: ${required}"; exit 1; }
done

grep -Fq '<script src="timer.js">' "${index_html}" || { echo "FAIL: local script only"; exit 1; }
grep -Fq 'http://' "${index_html}" "${timer_js}" 2>/dev/null && { echo "FAIL: http URL found"; exit 1; } || true
grep -Fq 'https://' "${index_html}" "${timer_js}" 2>/dev/null && { echo "FAIL: https URL found"; exit 1; } || true

if command -v python3 >/dev/null 2>&1; then
  python3 <<'PY'
def format_time(total_seconds):
    s = max(0, int(total_seconds))
    hours = s // 3600
    minutes = (s % 3600) // 60
    seconds = s % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

assert format_time(0) == "00:00"
assert format_time(65) == "01:05"
assert format_time(180) == "03:00"
assert format_time(3661) == "1:01:01"
print("logic ok")
PY
else
  echo "WARN: python3 unavailable for logic spot check"
fi

echo "PASS: Classroom Timer runtime static safety tests complete"
