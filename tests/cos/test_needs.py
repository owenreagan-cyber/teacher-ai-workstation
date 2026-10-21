"""cos needs: each provider, dedupe by id, resolved items, the canvas provider missing, present, and
broken. Synthetic data only; temp state directories and temp repo roots."""
from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
from pathlib import Path

from support import REPO_ROOT, CmdResult, FIXED_NOW, StateDirTest

from cos import cli, needs
from cos.config import Place
from cos.tools import ToolContext

KEY_ARGV = ["/usr/bin/security", "find-generic-password", "-s", "chief-search-brave"]


class Runner:
    """Answers the Keychain presence check and the canvas command; records every argv."""

    def __init__(self, key_present=True, canvas: CmdResult | Exception | None = None):
        self.key_present, self.canvas, self.calls = key_present, canvas, []

    def __call__(self, argv, timeout, cwd=None):
        self.calls.append(list(argv))
        if argv == KEY_ARGV:
            return CmdResult(0 if self.key_present else 44, "keychain: attributes only\n")
        if argv[-2:][0].endswith("canvas-weekly-status") and argv[-1] == "--json":
            if isinstance(self.canvas, Exception):
                raise self.canvas
            return self.canvas
        raise AssertionError(f"unexpected command {argv}")


class NeedsTests(StateDirTest):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory(prefix="cos-needs-repo-")
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.places = {"home": Place("home", "Sims, NC", 35.76, -78.06)}

    def gather(self, runner=None, **cfg):
        cfg.setdefault("places", self.places)
        cfg.setdefault("repo_root", self.repo)
        config = self.config(**cfg)
        ctx = ToolContext(config=config, clock=lambda: FIXED_NOW, run=runner or Runner())
        return needs.gather(config, ctx, FIXED_NOW)

    def ids(self, got):
        return [i["id"] for i in got["items"]]

    def write_owner(self, items):
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "needs.json").write_text(json.dumps({"items": items}), encoding="utf-8")

    def add_canvas_command(self):
        cmd = self.repo / "bin" / "canvas-weekly-status"
        cmd.parent.mkdir(parents=True, exist_ok=True)
        cmd.write_text("#!/bin/sh\nexit 99\n")  # never executed: the runner is faked
        cmd.chmod(0o700)
        return cmd

    # ------------------------------------------------------------------ config

    def test_healthy_setup_has_no_config_items(self):
        got = self.gather()
        self.assertEqual(self.ids(got), ["canvas:not-connected"])
        self.assertEqual(got["providers"]["config"], {"ok": True, "count": 0})

    def test_config_problems(self):
        got = self.gather(Runner(key_present=False), places={}, auto_search=False)
        by_id = {i["id"]: i for i in got["items"]}
        self.assertEqual(by_id["config:places-missing"]["kind"], "suggestion")
        self.assertEqual(by_id["config:places-missing"]["action"], {"type": "page", "label": "Open Settings", "page": "settings"})
        key = by_id["config:search-key"]
        self.assertEqual(key["action"]["type"], "command")
        self.assertEqual(by_id["config:auto-search-off"]["kind"], "info")
        unnamed = self.gather(places={"home": Place("home", "Home", 35.76, -78.06)})
        self.assertIn("config:home-unnamed", self.ids(unnamed))

    def test_keychain_check_never_reads_the_secret(self):
        runner = Runner()
        self.gather(runner)
        self.assertIn(KEY_ARGV, runner.calls)
        self.assertTrue(all("-w" not in argv for argv in runner.calls))

    # ------------------------------------------------------------------ owner list

    def test_owner_list_items_and_resolved(self):
        self.write_owner([
            {"id": "pick-title", "kind": "decision", "title": "Pick the SM5 homework title",
             "reason": "Titles must match.", "created_at": "2026-10-01T09:00:00-04:00",
             "action": {"type": "open_link", "label": "Open doc", "url": "https://example.com/doc"}},
            {"id": "done-one", "kind": "decision", "title": "Old", "reason": "Old", "created_at": "", "resolved": True},
            {"id": "canvas:not-connected", "resolved": True},
        ])
        got = self.gather()
        self.assertEqual(self.ids(got), ["pick-title"])  # resolved ids vanish from every provider
        action = got["items"][0]["action"]
        self.assertEqual(action["type"], "open_link")
        self.assertRegex(action["link_id"], r"^lnk-[0-9a-f]{16}$")
        self.assertEqual(got["resources"], [{"id": action["link_id"], "url": "https://example.com/doc"}])
        self.assertNotIn("https://", json.dumps(got["items"]))

    def test_owner_list_is_seeded_with_nothing(self):
        self.gather()
        self.assertFalse((self.state / "needs.json").exists())

    def test_damaged_owner_list_is_one_info_item(self):
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "needs.json").write_text("{nope", encoding="utf-8")
        got = self.gather()
        self.assertEqual(got["items"][0]["id"], "owner:unreadable")
        self.write_owner([{"id": "x", "kind": "decision", "title": "t", "reason": "r", "extra": 1}])
        got = self.gather()
        self.assertEqual(got["items"][0]["id"], "owner:unreadable")
        self.assertIn("unknown keys", got["items"][0]["reason"])

    def test_non_https_links_and_unknown_pages_are_dropped(self):
        self.write_owner([
            {"id": "a", "kind": "suggestion", "title": "t", "reason": "r",
             "action": {"type": "open_link", "label": "x", "url": "http://localhost:4310/"}},
            {"id": "b", "kind": "suggestion", "title": "t", "reason": "r", "action": {"type": "page", "label": "x", "page": "files"}},
            {"id": "c", "kind": "suggestion", "title": "t", "reason": "r", "action": {"type": "deep_link", "label": "x", "target": "chief://settings"}},
        ])
        items = {i["id"]: i for i in self.gather()["items"]}
        self.assertIsNone(items["a"]["action"])
        self.assertIsNone(items["b"]["action"])
        self.assertEqual(items["c"]["action"], {"type": "page", "label": "x", "page": "settings"})

    def test_dedupe_by_id_first_provider_wins(self):
        self.write_owner([{"id": "config:search-key", "kind": "decision", "title": "Mine", "reason": "r"},
                          {"id": "dup", "kind": "decision", "title": "First", "reason": "r"},
                          {"id": "dup", "kind": "decision", "title": "Second", "reason": "r"}])
        got = self.gather(Runner(key_present=False))
        self.assertEqual(self.ids(got).count("config:search-key"), 1)
        self.assertEqual(next(i for i in got["items"] if i["id"] == "config:search-key")["source"], "config")
        self.assertEqual([i["title"] for i in got["items"] if i["id"] == "dup"], ["First"])

    # ------------------------------------------------------------------ canvas

    def test_canvas_missing_is_one_info_item(self):
        got = self.gather()
        item = got["items"][-1]
        self.assertEqual((item["id"], item["kind"], item["title"]),
                         ("canvas:not-connected", "info", "Canvas planner status isn't connected yet."))

    def test_canvas_present_maps_action_items(self):
        self.add_canvas_command()
        out = {"action_items": [
            {"kind": "decision", "title": "Approve Q2W3 agenda", "reason": "Ready for review",
             "deep_link": "https://canvas.example.edu/courses/1/pages/q2w3"},
            {"kind": "suggestion", "title": "Check homework titles", "reason": "Two differ"},
            {"kind": "weird", "title": "Fallback kind", "reason": "x"},
            {"kind": "decision"},
        ]}
        runner = Runner(canvas=CmdResult(0, json.dumps(out)))
        got = self.gather(runner)
        canvas = [i for i in got["items"] if i["source"] == "canvas"]
        self.assertEqual([i["kind"] for i in canvas], ["decision", "suggestion", "info"])
        self.assertTrue(all(i["id"].startswith("canvas:") for i in canvas))
        self.assertEqual(canvas[0]["action"]["type"], "open_link")
        self.assertEqual(len(got["resources"]), 1)
        again = self.gather(Runner(canvas=CmdResult(0, json.dumps(out))))
        self.assertEqual(self.ids(got), self.ids(again))  # stable ids
        self.assertIn([str(self.repo / "bin" / "canvas-weekly-status"), "--json"], runner.calls)

    def test_canvas_broken_is_one_info_item(self):
        self.add_canvas_command()
        for result in (CmdResult(2, ""), CmdResult(0, "not json"), CmdResult(0, "{}"), TimeoutError()):
            got = self.gather(Runner(canvas=result))
            self.assertEqual([i["id"] for i in got["items"] if i["source"] == "canvas"], ["canvas:unreadable"], result)

    # ------------------------------------------------------------------ harness

    def write_report(self, run_id, started, certification, reasons):
        d = self.repo / "evals" / "reports" / run_id
        d.mkdir(parents=True)
        (d / "summary.json").write_text(json.dumps({
            "run": {"run_id": run_id, "model_mode": "real" if "real" in run_id else "fake", "started": started,
                    "ended": started},
            "certification": certification, "certification_reasons": reasons}), encoding="utf-8")

    def test_harness_failed_certification_is_a_decision(self):
        self.write_report("20261019-real", "2026-10-19T10:00:00", True, [])
        self.write_report("20261020-real", "2026-10-20T10:00:00", False, ["CERT-003 failed"])
        self.write_report("20261021-fake", "2026-10-21T10:00:00", True, [])
        got = self.gather()
        h = [i for i in got["items"] if i["source"] == "harness"]
        self.assertEqual(len(h), 1)
        self.assertEqual((h[0]["kind"], h[0]["reason"], h[0]["id"]),
                         ("decision", "CERT-003 failed", "harness:certification:20261020-real"))

    def test_harness_passing_or_uncommitted_only_adds_nothing(self):
        self.write_report("20261020-real", "2026-10-20T10:00:00", False, [needs.UNCOMMITTED])
        self.assertEqual([i for i in self.gather()["items"] if i["source"] == "harness"], [])
        self.write_report("20261021-real", "2026-10-21T10:00:00", True, [])
        self.assertEqual([i for i in self.gather()["items"] if i["source"] == "harness"], [])

    def test_one_failing_provider_never_hides_the_others(self):
        (self.repo / "evals" / "reports").mkdir(parents=True)
        with unittest_mock_patch(needs, "harness_provider", lambda *a: 1 / 0):
            got = self.gather()
        self.assertEqual(got["providers"]["harness"]["ok"], False)
        self.assertIn("canvas:not-connected", self.ids(got))


@contextlib.contextmanager
def unittest_mock_patch(module, name, value):
    old = getattr(module, name)
    setattr(module, name, value)
    try:
        yield
    finally:
        setattr(module, name, old)


class NeedsCliTests(StateDirTest):
    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(list(argv))
        return code, out.getvalue()

    def setUp(self):
        super().setUp()
        self._old = os.environ.get("COS_FIXTURE_DIR")
        os.environ["COS_FIXTURE_DIR"] = str(REPO_ROOT / "evals" / "fixtures" / "default")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("COS_FIXTURE_DIR", None)
        else:
            os.environ["COS_FIXTURE_DIR"] = self._old
        super().tearDown()

    def test_needs_json_and_home_section(self):
        code, out = self.run_cli("needs", "--json")
        self.assertEqual(code, 0)
        got = json.loads(out)
        self.assertEqual([i["id"] for i in got["items"]], ["canvas:not-connected"])
        self.assertEqual(set(got["providers"]), {"config", "owner_list", "canvas", "harness"})
        code, out = self.run_cli("home", "--json")
        snap = json.loads(out)
        self.assertEqual(snap["needs"]["status"], "current")
        self.assertEqual([i["id"] for i in snap["needs"]["data"]["items"]], ["canvas:not-connected"])
        self.assertEqual(snap["resources"], [])

    def test_home_lifts_need_links_into_resources(self):
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "needs.json").write_text(json.dumps({"items": [
            {"id": "d", "kind": "decision", "title": "t", "reason": "r",
             "action": {"type": "open_link", "label": "Open", "url": "https://example.com/x"}}]}))
        snap = json.loads(self.run_cli("home", "--json")[1])
        lid = snap["needs"]["data"]["items"][0]["action"]["link_id"]
        self.assertEqual(snap["resources"], [{"id": lid, "url": "https://example.com/x"}])
        self.assertNotIn("example.com", json.dumps(snap["needs"]))

    def test_needs_refused_while_stopped(self):
        self.run_cli("stop", "test")
        code, out = self.run_cli("needs", "--json")
        self.assertEqual(code, cli.EXIT_STOPPED)
        self.assertEqual(json.loads(out)["error_kind"], "stopped")
