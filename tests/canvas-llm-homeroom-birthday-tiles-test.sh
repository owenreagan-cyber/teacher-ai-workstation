#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM Homeroom birthday-tile tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODULE="scripts/canvas_llm_phase22/homeroom_newsletter.py"
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$MODULE"

python3 - <<'PY'
import sys
from pathlib import Path

root = Path('.').resolve()
sys.path.insert(0, str(root))
from scripts.canvas_llm_phase22 import homeroom_newsletter as h

students = [("Ava", "September 4"), ("Timothy", "September 16"), ("Charlotte", "September 17")]

# 1. One tile per student, first name only, exact known date.
section = h.render_birthday_section("September", students)
assert section.count("min-width: 220px") == 3, "expected exactly one tile per student"
for name in ("Ava", "Timothy", "Charlotte"):
    assert name in section, f"missing first name {name!r}"
for date in ("September 4", "September 16", "September 17"):
    assert date in section, f"missing date {date!r}"
# No legacy sentence-card wording — the tiles carry the names/dates themselves.
assert "Happy Birthday to" not in section
print("PASS one tile per student with first name only and exact date")

# 2. Rotating soft color palette: distinct light tints per tile.
for tint in ("#fff0f5", "#eef7ff", "#fff6e8"):
    assert tint in section, f"missing soft tint {tint!r}"
for accent in ("#c51062", "#0065a7", "#b65a00"):
    assert accent in section, f"missing accent {accent!r}"
assert "flex-wrap: wrap" in section
print("PASS rotating soft palette and responsive flex layout")

# 3. Section omitted entirely when no birthdays are supplied.
assert h.render_birthday_section("September", []) == ""
assert "September Birthdays" not in h.render_birthday_section("September", [])
print("PASS empty birthday list omits the entire section")

# 4. Replacement swaps the sentence card for tiles without touching other content.
legacy = (
    '  <div style="display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 22px;">\n'
    '    <div style="flex: 1 1 260px; background: linear-gradient(90deg, #fdf2f8, #faf5ff); border: 1px solid #f5d0fe; border-radius: 16px; padding: 22px; text-align: center;">\n'
    '        <div style="font-size: 34px;">\U0001F382 \U0001F389</div>\n'
    '        <h2 style="margin: 5px 0 12px; color: #a21caf; font-size: 23px;">September Birthdays</h2>\n'
    '        <p style="margin: 0; font-size: 17px;"><strong>Happy Birthday to Ava on September 4, Timothy on September 16, and Charlotte on September 17!</strong></p>\n'
    '    </div>\n'
    '</div>\n'
)
wrapped = '<div style="max-width:900px;">\n' + legacy + '<p>Other section preserved.</p>\n</div>\n'
new = h.replace_birthday_section(wrapped, "September", students)
assert "Happy Birthday to" not in new
assert new.count("min-width: 220px") == 3
assert "Other section preserved." in new
print("PASS replacement swaps the card for tiles and preserves other sections")

# 5. Canonical contract doc persists the birthday-tile rules.
contract = root / "docs/programs/canvas-llm/canonical-context-pack/newsletter-homeroom-contract.md"
text = contract.read_text(encoding="utf-8")
for needle in [
    "one birthday student = one birthday tile",
    "first name only unless Owen explicitly says otherwise",
    "soft rotating color palette",
    "display:flex; flex-wrap:wrap",
    "omit the entire birthday section",
    "never invent birthdays",
    "homeroom_newsletter.py",
]:
    assert needle in text, f"missing contract text: {needle!r}"
print("PASS canonical contract doc persists the birthday-tile rules")

# 6. Canonical example asset exists, non-empty, and matches the standard.
example = root / "docs/programs/canvas-llm/canonical-context-pack/examples/homeroom-birthday-tiles-example.html"
assert example.is_file() and example.stat().st_size > 0
body = example.read_text(encoding="utf-8")
assert "flex-wrap: wrap" in body
for name in ("Ava", "Timothy", "Charlotte"):
    assert name in body
print("PASS canonical birthday-tile example asset is persisted")

print("PASS: Homeroom birthday-tile standard complete")
PY

echo "PASS: Canvas LLM Homeroom birthday-tile tests complete"
