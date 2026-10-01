"""Regression tests for the independent M1 review (COS-M1-001..005) and addendum D."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import stat
import threading
from pathlib import Path
from unittest import mock

from support import REPO_ROOT, FakeModel, StateDirTest, answer, make_ctx, tool_call

from cos import cli
from cos.agent import Agent, Stopped
from cos.audit import AuditLog, marker_path, verify
from cos.config import ensure_state_dir
from cos.model import ModelClient
from cos.policy import KillSwitch, PolicyGate
from cos.registry import Registry, Tool
from cos.tools import build_registry, script_contract, status_scripts

EMPTY = {"type": "object", "properties": {}, "additionalProperties": False}


class BlockingModel:
    """chat() signals it has started, then blocks until the test releases it."""

    def __init__(self, response):
        self.response = response
        self.started = threading.Event()
        self.release = threading.Event()
        self.calls = 0

    def chat(self, messages, tools=None, fmt=None):
        self.calls += 1
        self.started.set()
        if not self.release.wait(5):
            raise AssertionError("test never released the model")
        return self.response, "blocking-model"


class Recorder:
    def __init__(self):
        self.events = []

    def __call__(self, kind, **fields):
        self.events.append((kind, fields))

    def kinds(self):
        return [k for k, _ in self.events]


# ----------------------------------------------------------------------------- COS-M1-001

class KillSwitchInFlightTests(StateDirTest):
    """Kill switch set while a model request is in flight: result discarded, nothing shown."""

    def setUp(self):
        super().setUp()
        ensure_state_dir(self.state)
        self.ks = KillSwitch(self.state)
        self.audit = Recorder()
        self.ran = []
        self.registry = Registry()
        self.registry.register(Tool(name="test.probe", description="d", parameters=EMPTY,
                                    side_effect="none", data_class="P2", timeout_s=1,
                                    func=lambda a: self.ran.append(1) or {"ok": True},
                                    keywords=("probe",)))

    def run_in_flight(self, response, question="probe"):
        model = BlockingModel(response)
        agent = Agent(model, self.registry, PolicyGate(self.registry, self.ks, audit=self.audit),
                      "SYSTEM", audit=self.audit)
        box = {}

        def target():
            try:
                box["result"] = agent.run(question)
            except BaseException as e:  # noqa: BLE001 - captured for assertions
                box["error"] = e

        worker = threading.Thread(target=target)
        worker.start()
        self.assertTrue(model.started.wait(5), "model call never began")  # 1. call begins
        self.ks.stop("in-flight test")                                     # 2. kill switch on
        model.release.set()                                                # 3. model released
        worker.join(5)
        self.assertFalse(worker.is_alive())
        return box, model

    def test_plain_text_answer_is_discarded(self):
        box, model = self.run_in_flight(answer("LEAKED ANSWER"))
        self.assertNotIn("result", box)                                    # 4. nothing returned
        self.assertIsInstance(box["error"], Stopped)
        self.assertNotIn("LEAKED", str(box["error"]))
        self.assertEqual(model.calls, 1)
        decisions = [f for k, f in self.audit.events if k == "decision" and f["subject"] == "model_call"]
        self.assertEqual([(d["phase"], d["allowed"]) for d in decisions],
                         [("before_request", True), ("after_response", False)])
        self.assertIn("model_response_discarded", self.audit.kinds())
        self.assertEqual(self.audit.kinds()[-1], "request_stopped")
        self.assertNotIn("answer", self.audit.kinds())

    def test_tool_call_response_is_not_interpreted(self):
        box, _ = self.run_in_flight(tool_call("test_probe", {}))
        self.assertIsInstance(box.get("error"), Stopped)
        self.assertEqual(self.ran, [], "tool proposed by a discarded response must not run")
        self.assertNotIn("tool_call", self.audit.kinds())

    def test_cli_prints_no_model_answer(self):
        blocking = BlockingModel(answer("LEAKED CLI ANSWER"))
        out, err, box = io.StringIO(), io.StringIO(), {}

        def target():
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                box["code"] = cli.main(["ask", "--json", "hello there"])

        with mock.patch.object(ModelClient, "chat", lambda self, *a, **k: blocking.chat(*a, **k)):
            worker = threading.Thread(target=target)
            worker.start()
            self.assertTrue(blocking.started.wait(5))
            KillSwitch(self.state).stop("cli in-flight test")
            blocking.release.set()
            worker.join(5)
        self.assertEqual(box["code"], cli.EXIT_STOPPED)
        self.assertNotIn("LEAKED", out.getvalue() + err.getvalue())
        payload = json.loads(out.getvalue())
        self.assertFalse(payload["ok"])
        self.assertIn("kill switch", payload["error"])


# ----------------------------------------------------------------------------- COS-M1-005

class ModelCallDecisionAuditTests(StateDirTest):
    def test_denied_model_call_is_audited(self):
        ensure_state_dir(self.state)
        ks, audit = KillSwitch(self.state), Recorder()
        gate = PolicyGate(Registry(), ks, audit=audit)
        ks.stop("test")
        self.assertFalse(gate.check_model_call("before_request").allowed)
        kind, rec = audit.events[-1]
        self.assertEqual(kind, "decision")
        self.assertEqual((rec["subject"], rec["phase"], rec["allowed"], rec["rule"]),
                         ("model_call", "before_request", False, "kill_switch"))
        self.assertIn("kill switch", rec["reason"])

    def test_allowed_model_call_is_audited_too(self):
        ensure_state_dir(self.state)
        audit = Recorder()
        PolicyGate(Registry(), KillSwitch(self.state), audit=audit).check_model_call("before_request")
        self.assertEqual((audit.events[-1][1]["subject"], audit.events[-1][1]["allowed"]), ("model_call", True))

    def test_stopped_cli_ask_writes_model_call_denial_to_chain(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(["stop", "audit test"])
            code = cli.main(["ask", "--json", "what time is it"])
        self.assertEqual(code, cli.EXIT_STOPPED)
        records = [json.loads(l) for l in (self.state / "audit.jsonl").read_text().splitlines()]
        denials = [r for r in records if r["kind"] == "decision" and r.get("subject") == "model_call"]
        self.assertEqual(len(denials), 1)
        self.assertEqual((denials[0]["allowed"], denials[0]["rule"]), (False, "kill_switch"))
        self.assertEqual(verify(self.state / "audit.jsonl").status, "ok")


# ----------------------------------------------------------------------------- COS-M1-004

class AuditPresenceTests(StateDirTest):
    def setUp(self):
        super().setUp()
        ensure_state_dir(self.state)
        self.path = self.state / "audit.jsonl"

    def cli_verify(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["audit", "verify"])
        return code, out.getvalue()

    def test_never_initialized(self):
        self.assertEqual(verify(self.path).status, "uninitialized")
        code, out = self.cli_verify()
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("EMPTY: no audit log yet (never initialized)"))

    def test_valid_log_creates_private_marker(self):
        AuditLog(self.path).append("request", mode="ask")
        self.assertEqual(verify(self.path).status, "ok")
        marker = marker_path(self.path)
        self.assertTrue(marker.exists())
        self.assertEqual(stat.S_IMODE(os.stat(marker).st_mode), 0o600)
        self.assertEqual(self.cli_verify()[0], 0)

    def test_tampered_log(self):
        AuditLog(self.path).append("request", mode="ask")
        AuditLog(self.path).append("answer", chars=3)
        lines = self.path.read_text().splitlines()
        rec = json.loads(lines[0])
        rec["mode"] = "chat"
        self.path.write_text(json.dumps(rec) + "\n" + lines[1] + "\n")
        self.assertEqual(verify(self.path).status, "fail")
        code, out = self.cli_verify()
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("FAIL:"))

    def test_initialized_then_deleted(self):
        AuditLog(self.path).append("request", mode="ask")
        self.path.unlink()
        result = verify(self.path)
        self.assertEqual(result.status, "fail")
        self.assertIn("missing but was initialized", result.message)
        code, out = self.cli_verify()
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("FAIL: audit log is missing"))

    def test_initialized_then_truncated(self):
        AuditLog(self.path).append("request", mode="ask")
        self.path.write_text("")
        self.assertEqual(verify(self.path).status, "fail")


# ----------------------------------------------------------------------------- COS-M1-003

BIN_TEMPLATE = """#!/usr/bin/env bash
set -euo pipefail
{prelude}
if [ "${{1:-}}" = "--other-flag" ]; then
  exec curl https://example.invalid/
fi
VERSION="test"
die() {{
  printf '%s\\n' "$1" >&2
  exit 1
}}
resolve_repo_root() {{
{resolve_body}
}}
unused_helper() {{
  curl https://example.invalid/
}}
while [[ $# -gt 0 ]]; do
  case "$1" in
    --daily-status)
      repo_root="$(resolve_repo_root)"
      daily_status_script="${{repo_root}}/scripts/fake-status.sh"
      bash "${{daily_status_script}}"
      exit 0
      ;;
  esac
done
"""
CLEAN_SCRIPT = """#!/usr/bin/env bash
# This comment mentions curl and wget but is not code.
set -euo pipefail
pass() { printf 'PASS: %s\\n' "$1"; }
cat <<'EOF'
Network calls: no (curl is never used)
EOF
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' <<< "${x:-}" && pass 'x' || pass 'no curl'
branch="$(git branch --show-current 2>/dev/null || echo unknown)"
mission="$(awk '
  /^## Mission$/ { found = 1; next }
  found && /^[*][*]/ { print; exit }
' docs/roadmap.md)"
[[ -f docs/a.md ]] && pass "doc" || printf 'missing\\n' >&2
printf '%s\\n' "${branch}" > /dev/null
"""


class ScriptContractTests(StateDirTest):
    def make_repo(self, script=CLEAN_SCRIPT, prelude="", resolve_body='  printf "%s\\n" "$PWD"',
                  extra=None):
        root = self.state.parent / "repo"
        (root / "bin").mkdir(parents=True, exist_ok=True)
        (root / "scripts").mkdir(exist_ok=True)
        (root / "bin" / "chief-of-staff").write_text(
            BIN_TEMPLATE.format(prelude=prelude, resolve_body=resolve_body))
        (root / "scripts" / "fake-status.sh").write_text(script)
        for name, text in (extra or {}).items():
            (root / "scripts" / name).write_text(text)
        return root

    def test_real_wrapped_commands_satisfy_contract(self):
        for _, flag, _, _ in status_scripts.SCRIPTS:
            with self.subTest(flag=flag):
                self.assertEqual(script_contract.check_flag(REPO_ROOT, flag), [])

    def test_known_unsafe_legacy_command_is_detected(self):
        violations = script_contract.check_flag(REPO_ROOT, "--approval-queue-status")
        self.assertTrue(any("unlink" in v for v in violations), violations)

    def test_clean_synthetic_script_passes(self):
        self.assertEqual(script_contract.check_flag(self.make_repo(), "--daily-status"), [])

    def test_violations_in_launched_script(self):
        cases = {
            "curl": "curl -s https://example.invalid/\n",
            "wget in substitution": 'x="$(wget -qO- http://example.invalid)"\n',
            "pipe to nc": "printf hi | nc example.invalid 80\n",
            "/dev/tcp": "exec 3<>/dev/tcp/example.invalid/80\n",
            "git fetch": "git fetch origin\n",
            "git -C push": "git -C . push\n",
            "rm": "rm -f /tmp/x\n",
            "file redirect": "printf hi > out.txt\n",
            "append redirect": "printf hi >> out.txt\n",
            "python inline": "python3 -c 'import urllib.request'\n",
            "bash -c": "bash -c 'echo hi'\n",
            "eval": 'eval "$cmd"\n',
            "dynamic command": '"$tool" --flag\n',
            "awk system": "awk 'BEGIN { system(\"id\") }'\n",
            "sed -i": "sed -i '' s/a/b/ f.txt\n",
            "ssh": "ssh host true\n",
            "ollama": "ollama list\n",
            "env prefix": "env FOO=1 curl https://example.invalid\n",
            "backticks": "x=`curl https://example.invalid`\n",
            "unquoted heredoc substitution": "cat <<EOF\n$(curl https://example.invalid)\nEOF\n",
        }
        for label, body in cases.items():
            with self.subTest(label=label):
                root = self.make_repo(script="#!/usr/bin/env bash\n" + body)
                self.assertNotEqual(script_contract.check_flag(root, "--daily-status"), [], label)

    def test_python_launched_script_is_checked(self):
        root = self.make_repo(
            script='#!/usr/bin/env bash\npython3 "${repo_root:-.}/scripts/helper.py"\n',
            extra={"helper.py": "import urllib.request\nurllib.request.urlopen('http://x')\n"})
        violations = script_contract.check_flag(root, "--daily-status")
        self.assertTrue(any("urllib.request" in v for v in violations), violations)

    def test_nested_bash_script_is_followed(self):
        root = self.make_repo(script='#!/usr/bin/env bash\nbash "scripts/inner.sh"\n',
                              extra={"inner.sh": "curl https://example.invalid\n"})
        violations = script_contract.check_flag(root, "--daily-status")
        self.assertTrue(any("inner.sh" in v and "curl" in v for v in violations), violations)

    def test_called_function_and_prelude_are_checked_uncalled_function_is_not(self):
        root = self.make_repo(resolve_body="  curl https://example.invalid/")
        self.assertTrue(any("curl" in v for v in script_contract.check_flag(root, "--daily-status")))
        root = self.make_repo(prelude="wget https://example.invalid/")
        self.assertTrue(any("wget" in v for v in script_contract.check_flag(root, "--daily-status")))
        # unused_helper() and the --other-flag block both contain curl but never run.
        self.assertEqual(script_contract.check_flag(self.make_repo(), "--daily-status"), [])

    def test_missing_dispatch_block_fails_closed(self):
        violations = script_contract.check_flag(self.make_repo(), "--no-such-flag")
        self.assertTrue(violations and "dispatch block" in violations[0])

    def test_unresolvable_launched_script_fails_closed(self):
        root = self.make_repo(script='#!/usr/bin/env bash\nbash "$(pick_script)"\n')
        self.assertTrue(script_contract.check_flag(root, "--daily-status"))

    def test_violating_command_is_not_registered(self):
        root = self.make_repo(script="#!/usr/bin/env bash\ncurl https://example.invalid\n")
        reg = build_registry(make_ctx(self.config(repo_root=root)))
        self.assertIsNone(reg.get("status.daily"))
        self.assertIn("status.daily", reg.disabled)
        self.assertIn("curl", reg.disabled["status.daily"])
        self.assertIsNotNone(reg.get("time.now"), "other tools still register")

    def test_real_registry_has_all_three_status_tools(self):
        reg = build_registry(make_ctx(self.config()))
        self.assertEqual(reg.disabled, {})
        for name in ("status.daily", "status.next_action", "status.local_llm"):
            self.assertIsNotNone(reg.get(name))


# ----------------------------------------------------------------------------- addendum D

class LatencyFieldTests(StateDirTest):
    def test_timing_fields_on_model_tool_and_request_records(self):
        ensure_state_dir(self.state)
        audit = Recorder()
        http_responses = [{"message": tool_call("time_now", {})}, {"message": answer("7:30 AM")}]
        from support import FakeHttp
        model = ModelClient("http://127.0.0.1:11434", "qwen3.6:35b", http=FakeHttp(http_responses), audit=audit)
        reg = build_registry(make_ctx(self.config()))
        gate = PolicyGate(reg, KillSwitch(self.state), audit=audit)
        Agent(model, reg, gate, "SYSTEM", audit=audit).run("what time is it")
        by_kind = {}
        for kind, rec in audit.events:
            by_kind.setdefault(kind, []).append(rec)
        self.assertTrue(all(isinstance(r["model_ms"], int) for r in by_kind["model_call"]))
        self.assertTrue(all(isinstance(r["tool_ms"], int) for r in by_kind["tool_result"]))
        final = by_kind["answer"][-1]
        for key in ("model_ms", "tool_ms", "total_ms"):
            self.assertIsInstance(final[key], int)
        self.assertGreaterEqual(final["total_ms"], final["model_ms"])

    def test_brief_request_record_has_timing(self):
        out = io.StringIO()
        fake_registry = lambda ctx: build_registry(make_ctx(self.config()))  # synthetic tools only
        with contextlib.redirect_stdout(out), mock.patch.object(cli, "build_registry", fake_registry):
            cli.main(["brief"])
        records = [json.loads(l) for l in (self.state / "audit.jsonl").read_text().splitlines()]
        final = [r for r in records if r["kind"] == "answer"][-1]
        self.assertEqual(final["mode"], "brief")
        for key in ("model_ms", "tool_ms", "total_ms"):
            self.assertIsInstance(final[key], int)


# ----------------------------------------------------------------------------- COS-M1-002 (static)

class EventKitHelperSourceTests(StateDirTest):
    SOURCE = REPO_ROOT / "cos" / "helpers" / "eventkit-reader" / "Sources" / "eventkit-reader" / "main.swift"

    def test_helper_exposes_only_read_commands(self):
        src = self.SOURCE.read_text()
        commands = re.findall(r'^case "([^"]+)":', src, re.M)
        self.assertEqual(commands, ["events", "reminders", "status", "identity", "--version"])

    def test_helper_never_calls_eventkit_mutation_apis(self):
        src = self.SOURCE.read_text()
        for api in ("save(", "remove(", "commit(", "saveCalendar", "removeCalendar", "reset("):
            self.assertNotIn(api, src, api)

    def test_eventkit_commands_require_own_identity(self):
        src = self.SOURCE.read_text()
        for cmd in ("events", "reminders", "status"):
            block = src.split(f'case "{cmd}":', 1)[1].split("case ", 1)[0]
            self.assertIn("requireOwnIdentity()", block, cmd)
        self.assertIn('Bundle.main.bundleIdentifier == expectedBundleID', src)
        self.assertIn("responsible == getpid()", src)


if __name__ == "__main__":
    import unittest
    unittest.main()
