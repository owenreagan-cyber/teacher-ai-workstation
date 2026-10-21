"""cos config get / set: validation, unknown and non-settable keys refused, atomic write, file
mode, audit record. Temp state directories only."""
from __future__ import annotations

import contextlib
import io
import json
import os
import stat
from unittest import mock

from support import StateDirTest

from cos import cli, config
from cos.audit import verify

PLACES = {"home": {"name": "Sims, NC", "latitude": 35.76, "longitude": -78.06},
          "work": {"name": "Clayton, NC", "latitude": 35.65, "longitude": -78.46},
          "gym": {"name": "Test Gym", "latitude": 35.7, "longitude": -78.1}}


class ConfigCliTests(StateDirTest):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue()

    def set(self, key, value):
        return self.run_cli("config", "set", "--json", key, json.dumps(value))

    def audit_records(self):
        path = self.state / "audit.jsonl"
        return [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []

    def test_get_reports_effective_values(self):
        code, out = self.run_cli("config", "get", "--json")
        self.assertEqual(code, 0)
        got = json.loads(out)
        self.assertEqual(got["values"]["places"]["home"]["name"], "Sims, NC")
        self.assertEqual(got["values"]["auto_search"], True)
        self.assertEqual(got["values"]["model"], "qwen3.6:35b")
        self.assertEqual(got["settable"], ["places", "auto_search", "model", "model_keep_alive"])
        self.assertTrue(got["path"].endswith("config.json"))
        self.assertFalse((self.state / "config.json").exists(), "get writes nothing")

    def test_set_round_trips_and_keeps_other_keys(self):
        (self.state).mkdir(parents=True, exist_ok=True)
        (self.state / "config.json").write_text(json.dumps({"search_daily_limit": 7}), encoding="utf-8")
        code, out = self.set("places", PLACES)
        self.assertEqual(code, 0, out)
        self.assertEqual(set(json.loads(out)["values"]["places"]), {"home", "work", "gym"})
        self.assertEqual(json.loads(out)["values"]["search_daily_limit"], 7)
        code, out = self.set("auto_search", False)
        self.assertEqual(json.loads(out)["values"]["auto_search"], False)
        code, out = self.set("model_keep_alive", "30m")
        self.assertEqual(json.loads(self.run_cli("config", "get", "--json")[1])["values"]["model_keep_alive"], "30m")
        written = json.loads((self.state / "config.json").read_text())
        self.assertEqual(written["search_daily_limit"], 7)
        self.assertEqual(written["places"], PLACES)

    def test_validation_refuses_and_writes_nothing(self):
        bad = [("places", {"home": {"name": "X", "latitude": 95, "longitude": 0}}),
               ("places", {"Home!": {"name": "X", "latitude": 1, "longitude": 1}}),
               ("places", {"home": {"name": "X", "latitude": 1, "longitude": 1, "zoom": 3}}),
               ("auto_search", "yes"),
               ("model_keep_alive", "forever"),
               ("model", "gpt-oss:120b-cloud"),
               ("model", "")]
        for key, value in bad:
            code, out = self.set(key, value)
            self.assertEqual(code, cli.EXIT_USAGE, (key, value))
            self.assertEqual(json.loads(out)["error_kind"], "usage")
            self.assertFalse((self.state / "config.json").exists(), (key, value))
        code, out = self.run_cli("config", "set", "--json", "auto_search", "not json")
        self.assertEqual(code, cli.EXIT_USAGE)

    def test_unknown_and_non_settable_keys_are_refused(self):
        code, out = self.set("colour", "blue")
        self.assertEqual(code, cli.EXIT_USAGE)
        self.assertIn("unknown config key", json.loads(out)["error"])
        code, out = self.set("ollama_url", "http://example.com")
        self.assertEqual(code, cli.EXIT_USAGE)
        self.assertIn("can't be changed here", json.loads(out)["error"])
        self.assertFalse((self.state / "config.json").exists())

    def test_write_is_atomic_and_private(self):
        self.set("auto_search", False)
        path = self.state / "config.json"
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual([p.name for p in self.state.iterdir() if p.name.startswith(".config")], [])
        with mock.patch("cos.config.os.replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                config.write_config_value("auto_search", True, self.state)
        self.assertEqual(json.loads(path.read_text())["auto_search"], False, "a failed write leaves the old file")
        self.assertEqual([p.name for p in self.state.iterdir() if p.name.startswith(".config")], [])

    def test_change_is_audited_without_coordinates(self):
        self.set("places", PLACES)
        self.set("auto_search", False)
        changes = [r for r in self.audit_records() if r["kind"] == "config_change"]
        self.assertEqual([(r["key"], r["value"]) for r in changes], [("places", ["gym", "home", "work"]), ("auto_search", False)])
        self.assertNotIn("35.76", (self.state / "audit.jsonl").read_text())
        self.assertTrue(verify(self.state / "audit.jsonl").ok)
        self.set("colour", "blue")
        self.assertEqual(len([r for r in self.audit_records() if r["kind"] == "config_change"]), 2)

    def test_double_dash_and_plain_output(self):
        code, out = self.run_cli("config", "set", "--json", "--", "auto_search", "false")
        self.assertEqual((code, json.loads(out)["values"]["auto_search"]), (0, False))
        code, out = self.run_cli("config", "get")
        self.assertIn("auto_search: false", out)
        self.assertEqual(os.stat(self.state).st_mode & 0o777, 0o700)
