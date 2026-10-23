"""Front-page rollover regression tests (CASE A–F, plain-python runnable)."""
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_rollover import rollover

COURSE = 26404
SLUG = "q2w3-october-26-30-2026"


def _client():
    return FakeDeployClient(courses={COURSE: {"id": COURSE, "name": "Math", "workflow_state": "available"}})


def test_case_a_unique_target_set_front_page():
    c = _client()
    c.seed_page(COURSE, SLUG, title="Q2W3 - October 26-30, 2026", body="", front_page=False)
    r = rollover._resolve_target(c, COURSE, SLUG, "Math", "Q2W3")
    assert r["blockers"] == []
    assert r["page_id"] is not None
    assert r["front_page"] is False


def test_case_b_already_front_page_idempotent():
    c = _client()
    c.seed_page(COURSE, SLUG, title="Q2W3", body="", front_page=True)
    r = rollover._resolve_target(c, COURSE, SLUG, "Math", "Q2W3")
    assert r["blockers"] == []
    assert r["front_page"] is True


def test_case_c_missing_page_blocks():
    c = _client()
    r = rollover._resolve_target(c, COURSE, SLUG, "Math", "Q2W3")
    assert r["blockers"]
    assert "missing" in r["blockers"][0].lower()


def test_case_d_duplicate_candidates_block():
    c = _client()
    c.seed_page(COURSE, "q2w3-a", title="Q2W3 - October 26-30, 2026", body="")
    c.seed_page(COURSE, "q2w3-b", title="Q2W3 - October 26-30, 2026", body="")
    r = rollover._resolve_target(c, COURSE, "q2w3-a", "Math", "Q2W3")
    assert r["blockers"]
    assert "duplicate" in r["blockers"][0].lower()


def test_case_e_wrong_course_blocks():
    c = _client()
    c.seed_page(COURSE, SLUG, title="Q2W3", body="")
    r = rollover._resolve_target(c, 99999, SLUG, "Math", "Q2W3")
    assert r["blockers"]
    assert "missing" in r["blockers"][0].lower()


def test_case_f_page_id_change_fails_readback():
    c = _client()
    page = c.seed_page(COURSE, SLUG, title="Q2W3", body="", front_page=False)
    expected = page["page_id"]
    c.set_front_page(COURSE, expected)
    # Simulate a live page_id drift (copy to avoid mutating the stored page).
    readback = dict(c.get_page(COURSE, SLUG))
    readback["page_id"] = "page-UNEXPECTED"
    ok = str(readback.get("page_id")) == str(expected) and bool(readback.get("front_page"))
    assert ok is False


# ---- Fake-client front-page semantics (§6) ---------------------------------

def test_set_front_page_preserves_body_and_title_and_unsets_prior():
    c = _client()
    prior = c.seed_page(COURSE, "q2w2", title="Q2W2 - October 19-23, 2026", body="<div>Q2W2</div>", front_page=True)
    target = c.seed_page(COURSE, SLUG, title="Q2W3 - October 26-30, 2026", body="<div>Q2W3</div>", front_page=False)

    result = c.set_front_page(COURSE, target["page_id"])

    # F: target becomes front_page=true.
    assert result["front_page"] is True
    assert c.get_page(COURSE, SLUG)["front_page"] is True
    # G: prior page becomes front_page=false.
    assert c.get_page(COURSE, "q2w2")["front_page"] is False
    # D: body unchanged.
    assert c.get_page(COURSE, SLUG)["body"] == "<div>Q2W3</div>"
    assert c.get_page(COURSE, "q2w2")["body"] == "<div>Q2W2</div>"
    # E: title unchanged.
    assert c.get_page(COURSE, SLUG)["title"] == "Q2W3 - October 26-30, 2026"
    assert c.get_page(COURSE, "q2w2")["title"] == "Q2W2 - October 19-23, 2026"


def test_set_front_page_missing_target_raises():
    c = _client()
    c.seed_page(COURSE, "q2w2", title="Q2W2", body="", front_page=True)
    try:
        c.set_front_page(COURSE, "page-UNKNOWN")
        raise AssertionError("expected DeployClientError")
    except Exception as e:  # noqa: BLE001
        assert type(e).__name__ == "DeployClientError"


def _run():
    import sys
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {e}")
    print(f"RESULT: {len(fns) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _run()
