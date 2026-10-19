#!/usr/bin/env bash
# Canvas agenda date standardization regression tests (deterministic, no Canvas).
# Verifies the canonical date formatter + banner + reminder dates use the
# required "Day of the week, Month day" format (never abbreviated/numeric).
set -euo pipefail

echo "Running Canvas agenda date standardization tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

python3 - <<'PY'
import sys
from datetime import datetime
sys.path.insert(0, '.')

from scripts.canvas_llm_phase3 import pacing_extractor as pe
from scripts.canvas_llm_phase3 import canvas_preview as cp
from scripts.canvas_llm_intake import intake

# ---- Canonical single-date format ----
assert pe.format_weekday_date(datetime(2026, 10, 19)) == "Monday, October 19"
assert pe.format_weekday_date(datetime(2026, 10, 20)) == "Tuesday, October 20"
assert pe.format_weekday_date(datetime(2026, 10, 23)) == "Friday, October 23"
# no leading zero, no year
assert pe.format_weekday_date(datetime(2026, 10, 9)) == "Friday, October 9"
assert pe.format_weekday_date(datetime(2026, 10, 10)) == "Saturday, October 10"

# ISO string form.
assert pe.format_weekday_date_iso("2026-10-20") == "Tuesday, October 20"
assert pe.format_weekday_date_iso("bogus") == "bogus"  # fail-safe, never corrupt

# ---- Canonical date range ----
assert pe.format_date_range(datetime(2026, 10, 19), datetime(2026, 10, 23)) \
    == "Monday, October 19 through Friday, October 23"
# cross-month boundary
assert pe.format_date_range(datetime(2026, 10, 30), datetime(2026, 11, 3)) \
    == "Friday, October 30 through Tuesday, November 3"
# year boundary
assert pe.format_date_range(datetime(2026, 12, 31), datetime(2027, 1, 1)) \
    == "Thursday, December 31 through Friday, January 1"

print("PASS canonical date formatter (single + range + cross-month/year)")

# ---- Banner subtitle uses the canonical range ----
html = cp.build_agenda_html("Q2W2", {"Monday": {"in_class": ["Lesson 41"], "at_home": None}})
assert "Monday, October 19 through Friday, October 23" in html, html
for bad in ("October 19\u201323", "October 19-23", "10/19", "2026-10-19", "Mon 10"):
    assert bad not in html, f"forbidden date form {bad!r} in banner"
print("PASS banner uses 'Monday, October 19 through Friday, October 23'")

# ---- Reminder dates use canonical single-date form (not ISO) ----
rows, meta = pe.fetch_pacing(fresh=False)
week = pe.extract_week(rows, "Q2W2", meta)
math_rem = intake._reminders_for(week, "math")
assert any("Tuesday, October 20" in r for r in math_rem), math_rem
assert not any("2026-10-20" in r for r in math_rem), math_rem

read_rem = intake._reminders_for(week, "reading_spelling")
assert any("Friday, October 23" in r for r in read_rem), read_rem
assert not any("2026-10-23" in r for r in read_rem), read_rem
print("PASS reminder dates use 'Day, Month day' (no ISO)")

print("PASS: Canvas agenda date standardization tests complete")
PY

echo "PASS Canvas agenda date standardization tests complete"
