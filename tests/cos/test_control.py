"""Policy gate, kill switch, executor, registry, audit chain, and state directory."""
from __future__ import annotations

import json
import os
import stat
import threading
import time

from support import StateDirTest

from cos.audit import GENESIS, AuditLog, verify
from cos.config import ConfigError, ensure_state_dir, load_config, open_private
from cos.executor import run_tool
from cos.policy import Decision, KillSwitch, PolicyGate
from cos.registry import ArgumentError, Registry, RegistryError, Tool, validate_args

EMPTY = {"type": "object", "properties": {}, "additionalProperties": False}


def make_tool(name="test.echo", side_effect="none", func=None, timeout_s=2, params=None):
    return Tool(name=name, description="synthetic test tool", parameters=params or EMPTY,
                side_effect=side_effect, data_class="P2", timeout_s=timeout_s,
                func=func or (lambda args: {"ok": True}))


class UnsafeRegistry(Registry):
    """Lets a test smuggle in a write tool, bypassing register() validation."""

    def force(self, tool):
        self._tools[tool.name] = tool


class PolicyGateTests(StateDirTest):
    def setUp(self):
        super().setUp()
        ensure_state_dir(self.state)
        self.registry = UnsafeRegistry()
        self.registry.register(make_tool())
        self.ks = KillSwitch(self.state)
        self.decisions = []
        self.gate = PolicyGate(self.registry, self.ks,
                               audit=lambda k, **f: self.decisions.append((k, f)))

    def test_allows_registered_read_only_tool(self):
        d = self.gate.decide("test.echo", {})
        self.assertEqual((d.allowed, d.rule), (True, "allow"))
        self.assertEqual(self.decisions[-1][0], "decision")

    def test_wire_name_resolves(self):
        self.assertTrue(self.gate.decide("test_echo", {}).allowed)

    def test_deny_unregistered(self):
        d = self.gate.decide("mail.send", {})
        self.assertEqual((d.allowed, d.rule), (False, "unregistered"))

    def test_deny_side_effect_not_none(self):
        for effect in ("local_write", "external_write", "weird"):
            with self.subTest(effect=effect):
                self.registry.force(make_tool(name=f"test.{effect}", side_effect=effect))
                d = self.gate.decide(f"test.{effect}", {})
                self.assertEqual((d.allowed, d.rule), (False, "side_effect"))

    def test_deny_bad_arguments(self):
        for args in ({"x": 1}, "not-a-dict", None, [1]):
            with self.subTest(args=args):
                d = self.gate.decide("test.echo", args)
                self.assertEqual((d.allowed, d.rule), (False, "bad_arguments"))

    def test_kill_switch_denies_everything(self):
        self.ks.stop("test")
        for name in ("test.echo", "mail.send"):
            d = self.gate.decide(name, {})
            self.assertEqual((d.allowed, d.rule), (False, "kill_switch"))
        self.assertFalse(self.gate.check_model_call().allowed)
        self.assertTrue(self.ks.resume())
        self.assertTrue(self.gate.decide("test.echo", {}).allowed)
        self.assertTrue(self.gate.check_model_call().allowed)

    def test_unreadable_kill_switch_counts_as_set(self):
        class Broken(KillSwitch):
            @property
            def path(self):
                raise OSError("permission denied")

            @path.setter
            def path(self, v):
                pass

        self.assertTrue(Broken(self.state).is_set())

    def test_exception_in_gate_denies(self):
        class Exploding(Registry):
            def get(self, name):
                raise RuntimeError("boom")

        gate = PolicyGate(Exploding(), self.ks)
        d = gate.decide("test.echo", {})
        self.assertEqual((d.allowed, d.rule), (False, "gate_error"))

    def test_timeout_in_gate_denies(self):
        class Slow(KillSwitch):
            def is_set(self):
                time.sleep(1)
                return False

        gate = PolicyGate(self.registry, Slow(self.state), timeout_s=0.05)
        d = gate.decide("test.echo", {})
        self.assertEqual((d.allowed, d.rule), (False, "gate_timeout"))


class ExecutorTests(StateDirTest):
    def test_refuses_without_allow_decision(self):
        with self.assertRaises(PermissionError):
            run_tool(make_tool(), {}, Decision(False, "unregistered", "x"))

    def test_timeout_becomes_error_result(self):
        tool = make_tool(func=lambda a: time.sleep(1) or {"late": True}, timeout_s=0.05)
        result = run_tool(tool, {}, Decision(True, "allow", "ok"))
        self.assertIn("timed out", result["error"])

    def test_exception_becomes_error_result(self):
        tool = make_tool(func=lambda a: 1 / 0)
        self.assertIn("ZeroDivisionError", run_tool(tool, {}, Decision(True, "allow", "ok"))["error"])


class RegistryTests(StateDirTest):
    def test_rejects_bad_declarations(self):
        bad = [make_tool(name="NoDots"), make_tool(side_effect="sometimes"),
               make_tool(timeout_s=0), make_tool(params={"type": "array"}),
               make_tool(params={"type": "object", "properties": {}, "additionalProperties": True})]
        for tool in bad:
            with self.subTest(tool=tool.name), self.assertRaises(RegistryError):
                Registry().register(tool)
        reg = Registry()
        reg.register(make_tool())
        with self.assertRaises(RegistryError):
            reg.register(make_tool())

    def test_validate_args(self):
        tool = make_tool(params={"type": "object", "properties": {
            "n": {"type": "integer", "minimum": 0, "maximum": 5},
            "s": {"type": "string", "maxLength": 4}}, "required": ["n"], "additionalProperties": False})
        self.assertEqual(validate_args(tool, {"n": 3}), {"n": 3})
        for args in ({}, {"n": True}, {"n": 9}, {"n": 1, "s": "toolong"}, {"n": "1"}):
            with self.subTest(args=args), self.assertRaises(ArgumentError):
                validate_args(tool, args)


class AuditChainTests(StateDirTest):
    def setUp(self):
        super().setUp()
        ensure_state_dir(self.state)
        self.path = self.state / "audit.jsonl"
        self.log = AuditLog(self.path)

    def _write_three(self):
        self.log.append("request", mode="ask")
        self.log.append("decision", tool="time.now", allowed=True)
        self.log.append("model_call", model="qwen3.6:35b", host="127.0.0.1:11434")

    def test_chain_links_and_verifies(self):
        self._write_three()
        records = [json.loads(l) for l in self.path.read_text().splitlines()]
        self.assertEqual([r["seq"] for r in records], [0, 1, 2])
        self.assertEqual(records[0]["prev"], GENESIS)
        self.assertEqual(records[1]["prev"], records[0]["hash"])
        self.assertEqual(verify(self.path), (True, 3, "chain intact (3 records)"))
        self.assertEqual(stat.S_IMODE(os.stat(self.path).st_mode), 0o600)

    def test_tamper_edit_detected(self):
        self._write_three()
        lines = self.path.read_text().splitlines()
        rec = json.loads(lines[1])
        rec["allowed"] = False
        lines[1] = json.dumps(rec)
        self.path.write_text("\n".join(lines) + "\n")
        ok, n, msg = verify(self.path)
        self.assertFalse(ok)
        self.assertIn("line 2", msg)

    def test_tamper_rehashed_record_breaks_next_link(self):
        from cos.audit import record_hash
        self._write_three()
        lines = self.path.read_text().splitlines()
        rec = json.loads(lines[1])
        rec["allowed"] = False
        rec["hash"] = record_hash(rec)
        lines[1] = json.dumps(rec)
        self.path.write_text("\n".join(lines) + "\n")
        ok, _, msg = verify(self.path)
        self.assertFalse(ok)
        self.assertIn("line 3", msg)

    def test_deleted_and_reordered_records_detected(self):
        self._write_three()
        lines = self.path.read_text().splitlines()
        for mutated in (lines[:1] + lines[2:], [lines[1], lines[0], lines[2]]):
            with self.subTest():
                self.path.write_text("\n".join(mutated) + "\n")
                self.assertFalse(verify(self.path)[0])

    def test_concurrent_appends_keep_chain(self):
        threads = [threading.Thread(target=lambda: [AuditLog(self.path).append("t") for _ in range(10)])
                   for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(verify(self.path), (True, 40, "chain intact (40 records)"))


class StateDirectoryTests(StateDirTest):
    def test_created_0700_even_with_permissive_umask(self):
        old = os.umask(0o022)
        try:
            ensure_state_dir()
        finally:
            os.umask(old)
        self.assertEqual(stat.S_IMODE(os.stat(self.state).st_mode), 0o700)

    def test_existing_wide_directory_is_tightened(self):
        self.state.mkdir(parents=True)
        os.chmod(self.state, 0o755)
        load_config()
        self.assertEqual(stat.S_IMODE(os.stat(self.state).st_mode), 0o700)

    def test_private_files_are_0600(self):
        ensure_state_dir()
        with open_private(self.state / "x.json", "w") as fh:
            fh.write("{}")
        self.assertEqual(stat.S_IMODE(os.stat(self.state / "x.json").st_mode), 0o600)

    def test_config_defaults_and_validation(self):
        cfg = load_config()
        self.assertEqual((cfg.model, cfg.fallback_model), ("qwen3.6:35b", "gpt-oss:20b"))
        self.assertEqual(cfg.state_dir, self.state)
        (self.state / "config.json").write_text(json.dumps({"latitude": 35.78, "longitude": -78.64}))
        self.assertEqual(load_config().latitude, 35.78)
        for bad in ({"latitude": 200}, {"cloud_key": "x"}, ["not", "object"]):
            with self.subTest(bad=bad):
                (self.state / "config.json").write_text(json.dumps(bad))
                with self.assertRaises(ConfigError):
                    load_config()


if __name__ == "__main__":
    import unittest
    unittest.main()
