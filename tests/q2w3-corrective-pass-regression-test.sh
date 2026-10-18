#!/usr/bin/env bash
# Q2W3 corrective-pass regression tests (Science reminders + weekly announcement identity).
# Synthetic, deterministic, no Canvas writes.
set -euo pipefail

echo "Running Q2W3 corrective-pass regression tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

python3 - <<'PY'
import sys
sys.path.insert(0, '.')

from scripts.canvas_llm_deploy import preflight as pf
from scripts.canvas_llm_intake import intake
from scripts.canvas_llm_phase3 import pacing_extractor as pe

# ---- Science reminder: active + content + no Test/Quiz -> non-empty ----
rows, meta = pe.fetch_pacing(fresh=False)
week = pe.extract_week(rows, "Q2W3", meta)
reminders = intake._reminders_for(week, "science")
assert len(reminders) > 0, "Science reminder must be non-empty"
assert any("electricity" in r.lower() or "Collisions" in r or "Crash Lab" in r for r in reminders), reminders
for r in reminders:
    for bad in ("Test", "Quiz", "Assessment"):
        assert bad not in r, f"Science reminder must not contain {bad!r}: {r}"
print("PASS Science reminder non-empty + no Test/Quiz/Assessment")

# ---- Weekly announcement identity (cases A-F) ----
proposed_q2w3 = {"title": "Math Canvas Weekly Update", "week_code": "Q2W3",
                 "delayed_post_at": "2026-10-23T20:00:00Z", "agenda_hash": "hash-q2w3"}

# A: same title, different week, different body -> PRIOR_WEEK_SAME_TITLE
live_prior = [{"title": "Math Canvas Weekly Update", "delayed_post_at": "2026-10-16T20:00:00Z",
               "message": '<div id="kl_wrapper_3">Q2W2 agenda</div>'}]
assert pf.classify_weekly_announcement(proposed_q2w3, live_prior) == "PRIOR_WEEK_SAME_TITLE"

# B: same title, same week, same body -> EXACT_MATCH
live_exact = [{"title": "Math Canvas Weekly Update", "week_code": "Q2W3",
               "delayed_post_at": "2026-10-23T20:00:00Z", "agenda_hash": "hash-q2w3"}]
assert pf.classify_weekly_announcement(proposed_q2w3, live_exact) == "EXACT_MATCH"

# C: same title, same week, different body -> BODY_CHANGED_SAME_WEEK
live_changed = [{"title": "Math Canvas Weekly Update", "week_code": "Q2W3",
                 "delayed_post_at": "2026-10-23T20:00:00Z", "agenda_hash": "hash-old"}]
assert pf.classify_weekly_announcement(proposed_q2w3, live_changed) == "BODY_CHANGED_SAME_WEEK"

# D: same title only, no trustworthy identity -> not EXACT_MATCH
live_title_only = [{"title": "Math Canvas Weekly Update", "delayed_post_at": None, "message": ""}]
assert pf.classify_weekly_announcement(proposed_q2w3, live_title_only) == "PRIOR_WEEK_SAME_TITLE"

# E: prior-week same-title must NOT idempotent-skip current week
assert pf.classify_weekly_announcement(proposed_q2w3, live_prior) != "EXACT_MATCH"

# F: true current-week exact duplicate -> safe skip
assert pf.classify_weekly_announcement(proposed_q2w3, live_exact) == "EXACT_MATCH"

# Embedded agenda hash extraction (from the opening <div).
assert pf._embedded_agenda_hash('<p>x</p><div id="kl_wrapper_3">agenda</div>') == pf._sha('<div id="kl_wrapper_3">agenda</div>')

print("PASS weekly announcement identity cases A-F")
PY

echo "PASS Q2W3 corrective-pass regression tests complete"
echo "PASS Q2W3 corrective-pass regression tests complete"
