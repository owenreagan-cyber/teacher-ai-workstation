"""Quarter/week live authorization. No Canvas credentials and no network."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_deploy import live_authorization as auth
from scripts.canvas_llm_deploy.client import LiveDeployClient
from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_storage import isolated_storage

NOW = datetime.now(timezone.utc)
FUTURE = (NOW + timedelta(days=2)).isoformat().replace("+00:00", "Z")
EXPIRY = (NOW + timedelta(days=9)).isoformat().replace("+00:00", "Z")
SOURCE = "source-hash"
FINGERPRINT = "plan-fingerprint"
COURSES = [26404, 26442, 28171, 28166, 26429]


def _manifest(**overrides) -> dict:
    manifest = imf.new_manifest(
        quarter=2, week=5, week_code="Q2W5",
        date_range={"start": "2026-11-09", "end": "2026-11-13"},
    )
    manifest["source_hash"] = SOURCE
    manifest["plan_fingerprint"] = FINGERPRINT
    manifest.update(overrides)
    return manifest


def _authorize(**overrides):
    fields = dict(
        school_year=auth.SCHOOL_YEAR,
        quarter=2,
        week=5,
        source_hash=SOURCE,
        plan_fingerprint=FINGERPRINT,
        publication_time=FUTURE,
        course_ids=COURSES,
        authorized_by="OWNER_UI",
        reason="Owen authorized the Q2W5 late release",
        expires_at=EXPIRY,
    )
    fields.update(overrides)
    return auth.authorize_live_transport(**fields)


def test_q1w2_flag_does_not_authorize_q2w5_and_makes_no_request():
    calls = {"credentials": 0, "network": 0}
    original_load = __import__(
        "scripts.canvas_llm_phase22.canvas_credentials", fromlist=["load_credentials"]
    ).load_credentials
    original_open = __import__("urllib.request", fromlist=["urlopen"]).urlopen

    def credentials(*args, **kwargs):
        calls["credentials"] += 1
        raise AssertionError("credentials were loaded")

    def network(*args, **kwargs):
        calls["network"] += 1
        raise AssertionError("Canvas was called")

    import os
    import urllib.request
    import scripts.canvas_llm_phase22.canvas_credentials as credentials_mod
    os.environ["CANVAS_LLM_LIVE_Q1W2_APPROVED"] = "1"
    os.environ["CANVAS_LLM_DEPLOYMENT_MODE"] = "live"
    credentials_mod.load_credentials = credentials
    urllib.request.urlopen = network
    try:
        with isolated_storage():
            imf.save_manifest(2, 5, _manifest())
            try:
                LiveDeployClient(quarter=2, week=5)
                raise AssertionError("Q2W5 client must be blocked")
            except auth.LiveAuthorizationError:
                pass
    finally:
        credentials_mod.load_credentials = original_load
        urllib.request.urlopen = original_open
        os.environ.pop("CANVAS_LLM_LIVE_Q1W2_APPROVED", None)
        os.environ.pop("CANVAS_LLM_DEPLOYMENT_MODE", None)
    assert calls == {"credentials": 0, "network": 0}


def test_q2w5_record_does_not_authorize_q1w2_or_other_scopes():
    with isolated_storage():
        imf.save_manifest(2, 5, _manifest())
        _authorize()
        for quarter, week in ((1, 2), (2, 4), (3, 5)):
            imf.save_manifest(quarter, week, _manifest(quarter=quarter, week=week, week_code=f"Q{quarter}W{week}"))
            copied = auth.authorization_path(quarter, week)
            copied.parent.mkdir(parents=True, exist_ok=True)
            copied.write_text(auth.authorization_path(2, 5).read_text(encoding="utf-8"), encoding="utf-8")
            try:
                auth.require_scoped_live_transport(quarter=quarter, week=week, now=NOW)
                raise AssertionError(f"Q{quarter}W{week} must be blocked")
            except auth.LiveAuthorizationError:
                pass
        record = auth.load_authorization(2, 5)
        record["school_year"] = "2025-2026"
        auth.authorization_path(2, 5).write_text(json.dumps(record), encoding="utf-8")
        try:
            auth.require_scoped_live_transport(quarter=2, week=5, now=NOW)
            raise AssertionError("wrong year must be blocked")
        except auth.LiveAuthorizationError:
            pass


def test_unauthorized_course_does_not_request():
    import urllib.request
    from scripts.canvas_llm_phase22 import canvas_connection_manager as transport
    calls = {"network": 0}
    original = urllib.request.urlopen

    def network(*args, **kwargs):
        calls["network"] += 1
        raise AssertionError("Canvas was called")

    urllib.request.urlopen = network
    try:
        with isolated_storage():
            imf.save_manifest(2, 5, _manifest())
            _authorize()
            auth.require_scoped_live_transport(quarter=2, week=5, now=NOW)
            client = transport.Phase22LiveCanvasClient("https://example.invalid", "test-token-not-real")
            try:
                client.request("POST", "/api/v1/courses/28165/pages", {"wiki_page[title]": "nope"})
                raise AssertionError("history course must be blocked")
            except auth.LiveAuthorizationError:
                pass
    finally:
        urllib.request.urlopen = original
        auth.clear_scope()
    assert calls["network"] == 0


def test_valid_q2w5_authorization_and_rejections():
    with isolated_storage():
        imf.save_manifest(2, 5, _manifest())
        _authorize()
        record = auth.require_scoped_live_transport(quarter=2, week=5, now=NOW)
        assert record["source_hash"] == SOURCE
        auth.require_authorized_course(26404)
        try:
            auth.require_authorized_course(28165)
            raise AssertionError("history course is outside this authorization")
        except auth.LiveAuthorizationError:
            pass
        manifest = _manifest(plan_fingerprint="changed")
        imf.save_manifest(2, 5, manifest)
        try:
            auth.require_scoped_live_transport(quarter=2, week=5, now=NOW)
            raise AssertionError("changed fingerprint must be blocked")
        except auth.LiveAuthorizationError:
            pass
        imf.save_manifest(2, 5, _manifest(source_hash="changed"))
        try:
            auth.require_scoped_live_transport(quarter=2, week=5, now=NOW)
            raise AssertionError("changed source hash must be blocked")
        except auth.LiveAuthorizationError:
            pass
        imf.save_manifest(2, 5, _manifest())
        record = auth.load_authorization(2, 5)
        record["expires_at"] = "2026-11-01T00:00:00Z"
        auth.authorization_path(2, 5).write_text(json.dumps(record), encoding="utf-8")
        try:
            auth.require_scoped_live_transport(quarter=2, week=5, now=NOW)
            raise AssertionError("expired authorization must be blocked")
        except auth.LiveAuthorizationError:
            pass
        auth.authorization_path(2, 5).unlink()
        try:
            auth.require_scoped_live_transport(quarter=2, week=5, now=NOW)
            raise AssertionError("missing authorization must be blocked")
        except auth.LiveAuthorizationError:
            pass
        text = (imf.staging_dir(2, 5) / "intake-manifest.json").read_text(encoding="utf-8")
        assert "PUBLISHED_VERIFIED" not in text


def test_future_dated_authorization_is_rejected():
    """An otherwise-valid record dated after the clock is forged, not authorization."""
    with isolated_storage():
        imf.save_manifest(2, 5, _manifest())
        _authorize()
        record = auth.load_authorization(2, 5)
        record["authorized_at"] = (NOW + timedelta(days=2)).isoformat().replace("+00:00", "Z")
        auth.authorization_path(2, 5).write_text(json.dumps(record), encoding="utf-8")
        try:
            auth.require_scoped_live_transport(quarter=2, week=5, now=NOW)
            raise AssertionError("future-dated authorization must be blocked")
        except auth.LiveAuthorizationError as exc:
            assert "future-dated" in str(exc)
        # The same record is accepted once the clock catches up to it.
        auth.require_scoped_live_transport(quarter=2, week=5, now=NOW + timedelta(days=2))
        auth.clear_scope()


def test_invalid_authorization_creates_no_ledgers():
    with isolated_storage():
        imf.save_manifest(2, 5, _manifest())
        before = (imf.staging_dir(2, 5) / "intake-manifest.json").read_bytes()
        try:
            LiveDeployClient(quarter=2, week=5)
            raise AssertionError("missing authorization must block the client")
        except auth.LiveAuthorizationError:
            pass
        assert (imf.staging_dir(2, 5) / "intake-manifest.json").read_bytes() == before
        from scripts.canvas_llm_deploy import ledger
        assert ledger.load_ledger(2, 5) is None
        assert ledger.load_published_verified(2, 5) is None
        from scripts.canvas_llm_rollover import ledger as rollover_ledger
        assert rollover_ledger.load_rollover_ledger(2, 5) is None


def test_valid_week_authorization_still_requires_live_deployment_mode():
    import os
    saved = os.environ.get("CANVAS_LLM_DEPLOYMENT_MODE")
    os.environ.pop("CANVAS_LLM_DEPLOYMENT_MODE", None)
    calls = {"credentials": 0}
    import scripts.canvas_llm_phase22.canvas_credentials as credentials_mod
    original_load = credentials_mod.load_credentials

    def credentials(*args, **kwargs):
        calls["credentials"] += 1
        raise AssertionError("credentials were loaded")

    credentials_mod.load_credentials = credentials
    try:
        with isolated_storage():
            imf.save_manifest(2, 5, _manifest())
            _authorize()
            try:
                LiveDeployClient(quarter=2, week=5)
                raise AssertionError("live mode must still be required")
            except RuntimeError as exc:
                assert "CANVAS_LLM_DEPLOYMENT_MODE" in str(exc)
    finally:
        credentials_mod.load_credentials = original_load
        if saved is None:
            os.environ.pop("CANVAS_LLM_DEPLOYMENT_MODE", None)
        else:
            os.environ["CANVAS_LLM_DEPLOYMENT_MODE"] = saved
    assert calls["credentials"] == 0


def test_q2w5_scope_does_not_remain_for_the_unscoped_client():
    import os
    keys = (
        "CANVAS_LLM_LIVE_Q1W2_APPROVED",
        "CANVAS_LLM_DEPLOYMENT_MODE",
        "CANVAS_LLM_LIVE_TRANSPORT_TEST",
    )
    saved = {key: os.environ.get(key) for key in keys}
    for key in keys:
        os.environ.pop(key, None)
    try:
        with isolated_storage():
            imf.save_manifest(2, 5, _manifest())
            _authorize()
            auth.require_scoped_live_transport(quarter=2, week=5, now=NOW)
            try:
                LiveDeployClient()
                raise AssertionError("unscoped client must stay behind the Q1W2 gate")
            except RuntimeError:
                pass
            auth.require_authorized_course(28165)
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_q1w2_environment_gate_still_rejects_an_unscoped_client_without_the_flag():
    import os
    keys = (
        "CANVAS_LLM_LIVE_Q1W2_APPROVED",
        "CANVAS_LLM_DEPLOYMENT_MODE",
        "CANVAS_LLM_LIVE_TRANSPORT_TEST",
    )
    saved = {key: os.environ.get(key) for key in keys}
    for key in keys:
        os.environ.pop(key, None)
    try:
        LiveDeployClient()
        raise AssertionError("unscoped live client must stay behind the Q1W2 gate")
    except RuntimeError as exc:
        assert "CANVAS_LLM_DEPLOYMENT_MODE" in str(exc) or "CANVAS_LLM_LIVE_Q1W2_APPROVED" in str(exc)
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _run():
    failed = 0
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print(f"RESULT: {len(tests) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _run()
