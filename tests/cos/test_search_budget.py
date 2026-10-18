"""Search budget: daily and monthly caps on real Brave calls, counted in the state dir; fixture mode never counts."""
from __future__ import annotations

import json
from datetime import datetime

from support import EDT, REPO_ROOT, StateDirTest, make_ctx
from test_web_search import Recorder, SearchHttp, keychain

from cos import fixture
from cos.config import ConfigError, load_config
from cos.fastpath import FastPath
from cos.policy import KillSwitch, PolicyGate
from cos.tools import build_registry, web_search
from cos.tools.web_search import USAGE_FILE, SearchBudget

ARGS = {"query": "synthetic radar", "query_source": "typed"}


class Clock:
    def __init__(self, when):
        self.now = when

    def __call__(self):
        return self.now


class BudgetTests(StateDirTest):
    def setUp(self):
        super().setUp()
        self.clock = Clock(datetime(2026, 10, 1, 23, 50, tzinfo=EDT))
        self.http = SearchHttp()
        self.audit = Recorder()

    def ctx(self, daily=3, monthly=5):
        return make_ctx(self.config(search_daily_limit=daily, search_monthly_limit=monthly), run=keychain(),
                        http=self.http, audit=self.audit, clock=self.clock.now)

    def search(self, ctx):
        ctx.clock = self.clock
        return web_search.search(ctx, ARGS)

    def usage(self):
        return json.loads((self.state / USAGE_FILE).read_text())

    def test_daily_limit_refuses_without_a_provider_call(self):
        ctx = self.ctx(daily=3)
        for _ in range(3):
            self.assertNotIn("error", self.search(ctx))
        res = self.search(ctx)
        self.assertEqual(res, {"error": "Search limit reached for today: 3/3. Resets tomorrow.", "limit_reached": True})
        self.assertEqual(len(self.http.calls), 3)
        self.assertEqual(self.usage(), {"days": {"2026-10-01": 3}, "months": {"2026-10": 3}})
        self.assertEqual(self.audit.of("search_refused")[0]["reason"], "daily_limit")
        self.assertEqual(len(self.audit.of("egress_request")), 3)

    def test_daily_count_resets_at_local_midnight(self):
        ctx = self.ctx(daily=1, monthly=10)
        self.search(ctx)
        self.assertTrue(self.search(ctx).get("limit_reached"))
        self.clock.now = datetime(2026, 10, 2, 0, 1, tzinfo=EDT)
        self.assertNotIn("error", self.search(ctx))
        self.assertEqual(self.usage()["days"], {"2026-10-01": 1, "2026-10-02": 1})
        self.assertEqual(self.usage()["months"], {"2026-10": 2})

    def test_monthly_limit_and_reset_on_the_first(self):
        ctx = self.ctx(daily=10, monthly=2)
        self.search(ctx)
        self.clock.now = datetime(2026, 10, 2, 9, 0, tzinfo=EDT)
        self.search(ctx)
        res = self.search(ctx)
        self.assertEqual(res["error"], "Search limit reached for this month: 2/2. Resets on November 1.")
        self.assertEqual(len(self.http.calls), 2)
        self.clock.now = datetime(2026, 11, 1, 7, 0, tzinfo=EDT)
        self.assertNotIn("error", self.search(ctx))
        self.assertEqual(self.usage()["months"], {"2026-10": 2, "2026-11": 1})

    def test_december_resets_on_january_first(self):
        self.clock.now = datetime(2026, 12, 15, 9, 0, tzinfo=EDT)
        ctx = self.ctx(daily=5, monthly=0)
        self.assertEqual(self.search(ctx)["error"],
                         "Search limit reached for this month: 0/0. Resets on January 1.")
        self.assertEqual(self.http.calls, [])

    def test_failed_provider_calls_still_count(self):
        from cos.egress import EgressError
        self.http.body = EgressError("HTTP 500 from api.search.brave.com", status=500)
        ctx = self.ctx(daily=1)
        self.assertIn("failed", self.search(ctx)["error"])
        self.assertTrue(self.search(ctx).get("limit_reached"))

    def test_missing_key_is_not_counted(self):
        ctx = self.ctx(daily=1)
        ctx.run = keychain(key="", code=44)
        self.search(ctx)
        self.assertFalse((self.state / USAGE_FILE).exists())

    def test_unreadable_usage_file_pauses_search(self):
        ctx = self.ctx()
        self.state.mkdir(parents=True, exist_ok=True)
        for raw in ("{not json", "[]", '{"days": 3, "months": {}}'):
            (self.state / USAGE_FILE).write_text(raw)
            res = self.search(ctx)
            self.assertTrue(res["limit_reached"])
            self.assertIn("unreadable", res["error"])
        self.assertEqual(self.http.calls, [])

    def test_usage_file_is_private(self):
        self.search(self.ctx())
        self.assertEqual((self.state / USAGE_FILE).stat().st_mode & 0o777, 0o600)

    def test_fast_path_answers_with_the_limit_message_and_calls_no_model(self):
        ctx = self.ctx(daily=0)
        reg = build_registry(ctx)
        fp = FastPath(reg, PolicyGate(reg, KillSwitch(self.state)), ctx.clock, audit=self.audit,
                      summarize=lambda *a: (_ for _ in ()).throw(AssertionError("model called")))
        res = fp.answer("search synthetic radar")
        self.assertEqual(res.answer, "Search limit reached for today: 0/0. Resets tomorrow.")
        self.assertTrue(res.fast_path)
        self.assertEqual(self.http.calls, [])


class FixtureNeverCountsTests(StateDirTest):
    def fixture_search(self, daily=2):
        cfg = self.config(fixture_dir=REPO_ROOT / "evals" / "fixtures" / "default", search_daily_limit=daily)
        ctx = fixture.fixture_context(cfg)
        return fixture.build_fixture_registry(ctx).get("web.search").func(ARGS)

    def test_fixture_calls_never_count(self):
        for _ in range(5):
            self.assertNotIn("error", self.fixture_search(daily=2))
        self.assertFalse((self.state / USAGE_FILE).exists())

    def test_fixture_mode_still_enforces_a_seeded_count(self):
        self.state.mkdir(parents=True, exist_ok=True)
        seeded = '{"days": {"2026-10-01": 2}, "months": {"2026-10": 2}}'
        (self.state / USAGE_FILE).write_text(seeded)
        res = self.fixture_search(daily=2)
        self.assertEqual(res["error"], "Search limit reached for today: 2/2. Resets tomorrow.")
        self.assertEqual((self.state / USAGE_FILE).read_text(), seeded)


class BudgetConfigTests(StateDirTest):
    def write(self, data):
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "config.json").write_text(json.dumps(data))

    def test_defaults(self):
        cfg = load_config()
        self.assertEqual((cfg.search_daily_limit, cfg.search_monthly_limit), (30, 600))

    def test_custom_and_invalid_limits(self):
        self.write({"search_daily_limit": 5, "search_monthly_limit": 0})
        cfg = load_config()
        self.assertEqual((cfg.search_daily_limit, cfg.search_monthly_limit), (5, 0))
        for bad in (-1, "30", 2.5, True, None):
            self.write({"search_daily_limit": bad})
            with self.assertRaises(ConfigError):
                load_config()

    def test_budget_class_counts_only_when_recording(self):
        clock = lambda: datetime(2026, 10, 1, 9, tzinfo=EDT)  # noqa: E731
        self.state.mkdir(parents=True, exist_ok=True)
        dry = SearchBudget(self.state, 1, 1, clock, record=False)
        self.assertEqual(dry.acquire(), (None, None))
        self.assertEqual(dry.acquire(), (None, None))
        self.assertFalse((self.state / USAGE_FILE).exists())


if __name__ == "__main__":
    import unittest
    unittest.main()
