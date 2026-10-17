#!/usr/bin/env bash
# Canvas page identity + slug/redirect hardening tests (pure, synthetic, zero writes).
set -euo pipefail

echo "Running Canvas page identity + slug hardening tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile scripts/canvas_llm_deploy/page_identity.py
echo "PASS page_identity.py compiles"

# Cases A–F + fatality/warning semantics live in the module self-test.
python3 -m scripts.canvas_llm_deploy.page_identity self-test
echo "PASS page identity classification self-test (cases A-F)"

python3 - <<'PY'
import sys
sys.path.insert(0, '.')
from scripts.canvas_llm_deploy import page_identity as pi

# ---- Regression: title-driven slug change is NOT a failure ----
# Before: page_id 123, slug old-name.
# After title update: page_id 123, canonical slug new-name.
# Old slug may still redirect to 123.

c = pi.classify_page_identity(
    known_page_id=123, current_slug="new-name", current_page_id=123,
    old_slug="old-name", old_slug_resolves_to=123,
)
assert c == pi.LEGACY_SLUG_REDIRECTS_SAME_PAGE, c
assert not pi.slug_change_is_fatal(c)

c2 = pi.classify_page_identity(
    known_page_id=123, current_slug="new-name", current_page_id=123,
    old_slug="old-name", old_slug_resolves_to=None,
)
assert c2 == pi.CANONICAL_SLUG_CHANGED_SAME_PAGE, c2
assert not pi.slug_change_is_fatal(c2)
assert pi.slug_change_is_warning(c2)

# ---- Duplicate protection: legacy slug A + canonical slug B, both -> page_id X,
# is ONE page, NOT two. Fatal only when a distinct page_id is involved.
assert pi.classify_page_identity(
    known_page_id=798072, current_slug="B", current_page_id=798072,
    old_slug="A", old_slug_resolves_to=798072,
) == pi.LEGACY_SLUG_REDIRECTS_SAME_PAGE  # one page
assert pi.slug_change_is_fatal(pi.classify_page_identity(
    known_page_id=798072, current_slug="B", current_page_id=798072,
    old_slug="A", old_slug_resolves_to=999999,  # different page -> conflict
)) is True

print("PASS regression: slug change is non-fatal; alias is one page, not a duplicate")
PY

# ---- Deployment readback: page_id continuity is the success signal ----
python3 - <<'PY'
import sys
sys.path.insert(0, '.')
from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_deploy.coordinator import _verify_page

client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math", "workflow_state": "available"}})
# Seed page under legacy slug.
page = client.seed_page(26404, "old-name", title="Q2W3", body="<div id='kl_wrapper_3'>x</div><p>Reminders</p>")
pid = page["page_id"]

# Simulate title-driven canonical slug change: store now keyed by new slug,
# same page_id. Old slug remains as a redirect alias (both resolve same object).
client.pages[(26404, "new-name")] = dict(page, url="new-name")
# Legacy alias entry still maps to the same page object.
client.pages[(26404, "old-name")] = dict(page, url="new-name")

counts = {"GET": 0}
# Verify by canonical slug (page_id continuity + body markers) -> PASS.
ok, detail = _verify_page(client, 26404, "new-name", pid, "Q2W3", counts)
assert ok, detail
assert "old-name" not in detail  # slug change is not surfaced as failure

# Verify by legacy alias slug -> same page_id, still PASS.
ok2, _ = _verify_page(client, 26404, "old-name", pid, "Q2W3", counts)
assert ok2, "legacy slug redirect must still resolve and verify"

# Zero writes performed by this test.
assert client._write_counts == {"POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0, "GET": 0}
print("PASS deployment readback: page_id continuity, slug change non-fatal, legacy alias resolves")
PY

# ---- No duplicate page creation: plan pages are UPDATE-only (never CREATE) ----
python3 - <<'PY'
import sys
sys.path.insert(0, '.')
from scripts.canvas_llm_deploy import plan as planmod

plan = planmod.build_plan(2, 3)
pages = plan.get("pages", [])
for p in pages:
    assert p.get("action") == "UPDATE", f"page action must be UPDATE, got {p.get('action')!r}"
assert plan.get("counts", {}).get("deletes", 0) == 0
print("PASS plan builder never emits page CREATE (update-in-place only)")
PY

echo "PASS Canvas page identity + slug hardening tests complete"
echo "PASS Canvas page identity + slug hardening tests complete"
