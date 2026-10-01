"""Fixture mode (COS_FIXTURE_DIR) for the evals harness. Synthetic data only.

The "real" state directory is always patched to a temp path here, so even a
broken guard could not touch Owen's real state.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support import REPO_ROOT, StateDirTest

from cos import cli, config, fixture
from cos.audit import verify
from cos.model import ModelClient
from cos.registry import Tool

FIXTURES = REPO_ROOT / "evals" / "fixtures" / "default"


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class EnvMixin:
    def patch_env(self, **values):
        saved = {k: os.environ.get(k) for k in values}

        def restore():
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.addCleanup(restore)
        for k, v in values.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class FixtureRefusalTests(EnvMixin, unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="cos-fixture-refusal-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.fake_real = self.root / "Library" / "Application Support" / "ChiefOfStaff"
        patcher = mock.patch.object(config, "DEFAULT_STATE_DIR", self.fake_real)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.patch_env(COS_FIXTURE_DIR=str(FIXTURES))

    def assert_refused(self, *argv, words="fixture mode refused"):
        code, out, err = run_cli(*argv)
        self.assertEqual(code, cli.EXIT_USAGE, (out, err))
        self.assertIn(words, out + err)
        return out, err

    def test_refused_without_state_dir(self):
        self.patch_env(COS_STATE_DIR=None)
        out, _ = self.assert_refused("ask", "--json", "--", "what time is it", words="requires COS_STATE_DIR")
        self.assertEqual(json.loads(out)["error_kind"], "usage")
        for argv in (["status", "--json"], ["history", "--session", "default"], ["brief"], ["stop"]):
            self.assert_refused(*argv)
        self.assertFalse(self.fake_real.exists(), "the real state dir must not be created")

    def test_refused_with_blank_state_dir(self):
        self.patch_env(COS_STATE_DIR="  ")
        self.assert_refused("ask", "--", "what time is it")
        self.assertFalse(self.fake_real.exists())

    def test_refused_when_state_dir_is_the_real_one(self):
        self.fake_real.mkdir(parents=True)
        link = self.root / "link-to-real"
        link.symlink_to(self.fake_real)
        variants = [self.fake_real, f"{self.fake_real}/", self.fake_real / "sub",
                    str(self.fake_real).upper(), link, link / "nested",
                    self.fake_real / ".." / "ChiefOfStaff"]
        for variant in variants:
            with self.subTest(state_dir=str(variant)):
                self.patch_env(COS_STATE_DIR=str(variant))
                self.assert_refused("ask", "--json", "--", "what time is it", words="real Chief of Staff")
                self.assert_refused("status", "--json")
        self.assertEqual(list(self.fake_real.iterdir()), [], "nothing created in the real state dir")

    def test_refused_when_fixture_dir_missing_or_blank(self):
        self.patch_env(COS_STATE_DIR=str(self.root / "state"))
        self.patch_env(COS_FIXTURE_DIR=str(self.root / "no-such-fixtures"))
        self.assert_refused("ask", "--", "what time is it", words="fixture directory not found")
        self.patch_env(COS_FIXTURE_DIR="")
        self.assert_refused("ask", "--", "what time is it", words="set but empty")
        self.assertFalse((self.root / "state").exists())

    def test_temp_state_dir_is_accepted(self):
        self.patch_env(COS_STATE_DIR=str(self.root / "state"))
        code, out, err = run_cli("ask", "--json", "--", "what time is it")
        self.assertEqual(code, 0, err)
        self.assertIn("2:30 PM", json.loads(out)["answer"])


class Recorder:
    """Records and refuses every subprocess launch and socket connection."""

    def __init__(self, test):
        self.calls = []

        def refuse(kind):
            def f(*args, **kwargs):
                self.calls.append((kind, repr(args)[:200]))
                raise AssertionError(f"fixture mode made a {kind} call: {args!r}")
            return f
        for target, name in ((subprocess, "run"), (subprocess, "Popen"), (os, "system"),
                             (socket.socket, "connect"), (socket, "create_connection")):
            p = mock.patch.object(target, name, refuse(f"{target.__name__}.{name}"))
            p.start()
            test.addCleanup(p.stop)


class ScriptedOllama:
    """Stands in for the local Ollama HTTP layer (ModelClient._post); records paths."""

    def __init__(self, *messages):
        self.messages = list(messages)
        self.paths = []

    def __call__(self, client, path, payload):
        self.paths.append((client.base_url, path))
        return {"message": self.messages.pop(0)}


class FixtureModeTests(EnvMixin, StateDirTest):
    def setUp(self):
        super().setUp()
        self.patch_env(COS_FIXTURE_DIR=str(FIXTURES), TZ="America/New_York")
        self.recorder = Recorder(self)

    def scripted(self, *messages):
        ollama = ScriptedOllama(*messages)
        p = mock.patch.object(ModelClient, "_post", lambda client, path, payload: ollama(client, path, payload))
        p.start()
        self.addCleanup(p.stop)
        return ollama

    def audit_records(self):
        return [json.loads(l) for l in (self.state / "audit.jsonl").read_text().splitlines()]

    def test_tools_read_fixtures_without_subprocess_or_network(self):
        rt = cli.build_runtime()
        self.assertEqual(rt.config.fixture_dir, FIXTURES.resolve())
        results = {t.name: t.func({}) for t in rt.registry.all()}
        self.assertEqual(results["time.now"]["time"], "2:30 PM")
        self.assertEqual(results["time.now"]["display"], "Thursday, October 1, 2026")
        self.assertEqual((results["weather.today"]["now_f"], results["weather.today"]["high_f"],
                          results["weather.today"]["conditions"]), (68, 74, "partly cloudy"))
        self.assertEqual(results["mac.status"]["battery_pct"], 82)
        self.assertEqual([e["title"] for e in results["calendar.today"]["events"]],
                         ["Test All-Day Event C", "Test Event A", "Test Event B"])
        self.assertEqual(results["calendar.today"]["events"][1]["start"], "9:00 AM")
        rems = results["reminders.due"]
        self.assertEqual((rems["count"], rems["overdue"], rems["reminders"][0]["title"]),
                         (3, 1, "Test Reminder B"))
        self.assertIn("Test Mission Alpha", results["status.daily"]["output"])
        self.assertIn("Test Focus Item 1", results["status.next_action"]["output"])
        self.assertIn("test-model-a", results["status.local_llm"]["output"])
        for name, result in results.items():
            self.assertNotIn("error", result, name)
        self.assertEqual(self.recorder.calls, [])

    def test_tool_context_refuses_commands_and_requests(self):
        rt = cli.build_runtime()
        with self.assertRaises(fixture.FixtureError):
            rt.ctx.run(["/bin/echo", "x"], timeout=1)
        with self.assertRaises(Exception):
            rt.ctx.http("GET", "https://api.open-meteo.com/v1/forecast")
        denied = [r for r in self.audit_records() if r["kind"] == "egress_denied"]
        self.assertEqual(denied[-1]["url_host"], "api.open-meteo.com")
        self.assertEqual(self.recorder.calls, [])

    def test_tool_without_a_fixture_reader_returns_an_error(self):
        rt = cli.build_runtime()
        tool = Tool("new.thing", "synthetic", {"type": "object", "properties": {}, "additionalProperties": False},
                    "none", "P2", 1, func=lambda args: self.fail("real tool function ran"))
        result = fixture._reader(tool, rt.ctx, FIXTURES)({})
        self.assertIn("no fixture reader", result["error"])

    def test_missing_fixture_file_is_an_error_result(self):
        partial = self.state.parent / "partial-fixtures"
        partial.mkdir()
        shutil.copy(FIXTURES / "clock.json", partial / "clock.json")
        self.patch_env(COS_FIXTURE_DIR=str(partial))
        rt = cli.build_runtime()
        for name in ("weather.today", "mac.status", "calendar.today", "reminders.due", "status.daily"):
            self.assertIn("not present", rt.registry.get(name).func({})["error"], name)
        self.assertEqual(self.recorder.calls, [])

    def test_bad_fixture_clock_refuses_to_start(self):
        bad = self.state.parent / "bad-clock"
        bad.mkdir()
        (bad / "clock.json").write_text('{"now": "2026-10-01T14:30:00"}')  # no timezone
        self.patch_env(COS_FIXTURE_DIR=str(bad))
        code, out, err = run_cli("ask", "--", "what time is it")
        self.assertEqual(code, cli.EXIT_USAGE)
        self.assertIn("timezone", err)

    def test_audit_records_carry_fixture_flag(self):
        ollama = self.scripted(
            {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "calendar_today", "arguments": {}}}]},
            {"role": "assistant", "content": "You have Test Event A and Test Event B."})
        self.assertEqual(run_cli("ask", "--json", "--", "what time is it")[0], 0)
        code, out, _ = run_cli("ask", "--json", "--session", "fx", "--", "what's on my calendar today")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["tools_used"], ["calendar.today"])
        self.assertEqual(run_cli("brief", "--json")[0], 0)
        self.assertEqual(run_cli("stop", "test")[0], 0)
        self.assertEqual(run_cli("ask", "--", "what time is it")[0], cli.EXIT_STOPPED)
        self.assertEqual(run_cli("resume")[0], 0)
        records = self.audit_records()
        kinds = {r["kind"] for r in records}
        self.assertTrue({"request", "decision", "tool_result", "model_call", "answer", "kill_switch",
                         "request_stopped"} <= kinds, kinds)
        self.assertTrue(all(r.get("fixture") is True for r in records))
        self.assertTrue(verify(self.state / "audit.jsonl").ok)
        self.assertEqual({path for _, path in ollama.paths}, {"/api/chat"})
        self.assertEqual({base for base, _ in ollama.paths}, {"http://127.0.0.1:11434"})
        model_hosts = {r["host"] for r in records if r["kind"] == "model_call"}
        self.assertEqual(model_hosts, {"127.0.0.1:11434"})
        self.assertEqual(self.recorder.calls, [])

    def test_fixture_flag_cannot_be_overridden_by_a_record_field(self):
        rt = cli.build_runtime()
        record = rt.audit("note", fixture=False)
        self.assertIs(record["fixture"], True)

    def test_status_reports_fixture_mode(self):
        p = mock.patch.object(ModelClient, "loaded_models", lambda self, timeout_s=3: [])
        p.start()
        self.addCleanup(p.stop)
        code, out, _ = run_cli("status", "--json")
        self.assertEqual(code, 0)
        self.assertIs(json.loads(out)["fixture"], True)
        code, out, _ = run_cli("status")
        self.assertIn("FIXTURE MODE", out)
        self.patch_env(COS_FIXTURE_DIR=None)
        code, out, _ = run_cli("status", "--json")
        self.assertNotIn("fixture", json.loads(out))


class NoFixtureModeTests(StateDirTest):
    def test_audit_records_have_no_fixture_field_outside_fixture_mode(self):
        os.environ.pop("COS_FIXTURE_DIR", None)
        rt = cli.build_runtime()
        self.assertIsNone(rt.config.fixture_dir)
        self.assertNotIn("fixture", rt.audit("note"))


if __name__ == "__main__":
    unittest.main()
