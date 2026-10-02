"""M1.5A core additions: sessions, history, status, error kinds. Synthetic data only."""
from __future__ import annotations

import contextlib
import io
import json
import stat
import unittest
from unittest import mock

from support import FakeHttp, StateDirTest, answer

from cos import cli, sessions
from cos.egress import EgressError
from cos.model import ModelClient, ModelError
from cos.policy import KillSwitch
from cos.sessions import (SessionIdError, TurnError, append_turn, check_session_id, history_messages,
                          read_session, read_turns)


def turn(i, chars=10):
    return {"ts": f"2026-10-01T07:{i:02d}:00-04:00", "question": f"q{i} " + "x" * chars,
            "answer": f"a{i} " + "y" * chars, "tools_used": [], "fast_path": False,
            "model": "fake-model", "notices": [], "total_ms": 5}


class CliCase(StateDirTest):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class ScriptedChat:
    """Patches ModelClient.chat; records the messages of each call."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, messages, tools=None, fmt=None):  # not bound: patched as an instance
        self.calls.append([dict(m) for m in messages])
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        return item, "fake-model"


class SessionIdTests(unittest.TestCase):
    def test_valid_ids(self):
        for sid in ("default", "a", "work-2026", "0" * 40):
            self.assertEqual(check_session_id(sid), sid)

    def test_invalid_ids_rejected(self):
        for sid in ("../x", "A", "", "a" * 41, "a/b", "a.b", "default\n", " a", None, 7):
            with self.assertRaises(SessionIdError, msg=repr(sid)):
                check_session_id(sid)


class SessionStoreTests(StateDirTest):
    def test_create_append_and_modes(self):
        self.config()
        append_turn(self.state, "default", turn(1))
        append_turn(self.state, "default", turn(2))
        turns = read_turns(self.state, "default")
        self.assertEqual([t["question"][:2] for t in turns], ["q1", "q2"])
        self.assertEqual(set(turns[0]), set(sessions.TURN_FIELDS))
        sdir = self.state / "sessions"
        self.assertEqual(stat.S_IMODE(sdir.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((sdir / "default.jsonl").stat().st_mode), 0o600)

    def test_missing_session_reads_empty_and_creates_nothing(self):
        self.config()
        self.assertEqual(read_turns(self.state, "nope"), [])
        self.assertFalse((self.state / "sessions").exists())

    def test_history_capped_by_turns(self):
        msgs = history_messages([turn(i) for i in range(15)])
        self.assertEqual(len(msgs), 2 * sessions.MAX_TURNS)
        self.assertTrue(msgs[0]["content"].startswith("q5"))
        self.assertTrue(msgs[-1]["content"].startswith("a14"))
        self.assertEqual([m["role"] for m in msgs[:2]], ["user", "assistant"])

    def test_history_capped_by_chars_keeps_newest(self):
        msgs = history_messages([turn(i, chars=2000) for i in range(10)], max_chars=9000)
        self.assertEqual(len(msgs), 4)  # two turns of ~4010 chars fit, a third does not
        self.assertTrue(msgs[-1]["content"].startswith("a9"))
        self.assertLessEqual(sum(len(m["content"]) for m in msgs), 9000)

    def test_torn_line_is_skipped(self):
        self.config()
        append_turn(self.state, "default", turn(1))
        with open(self.state / "sessions" / "default.jsonl", "a") as fh:
            fh.write('{"ts": "broken\n')
        append_turn(self.state, "default", turn(2))
        self.assertEqual(len(read_turns(self.state, "default")), 2)

    def test_append_after_torn_last_line_without_newline_survives(self):
        """se-bad-006: a last line with no trailing newline must not swallow the next turn."""
        self.config()
        append_turn(self.state, "default", turn(1))
        path = self.state / "sessions" / "default.jsonl"
        with open(path, "a") as fh:
            fh.write('{"ts": "2026-09-30T08:')  # torn: no newline
        append_turn(self.state, "default", turn(2))
        turns, skipped = read_session(self.state, "default")
        self.assertEqual([t["question"][:2] for t in turns], ["q1", "q2"])
        self.assertEqual(skipped, 1)
        self.assertTrue(path.read_bytes().endswith(b"\n"))

    def test_append_to_clean_file_adds_no_blank_line(self):
        self.config()
        append_turn(self.state, "default", turn(1))
        append_turn(self.state, "default", turn(2))
        raw = (self.state / "sessions" / "default.jsonl").read_bytes()
        self.assertEqual(raw.count(b"\n"), 2)
        self.assertNotIn(b"\n\n", raw)


class TurnValidationTests(CliCase):
    """M15A-002: every turn is shape-checked on write and on read."""

    BAD = {
        "tools_used not a list": dict(tools_used="time.now"),
        "tools_used item not str": dict(tools_used=["time.now", 3]),
        "fast_path is a string": dict(fast_path="false"),
        "total_ms negative": dict(total_ms=-1),
        "total_ms is a string": dict(total_ms="5"),
        "total_ms is a bool": dict(total_ms=True),
        "model is a number": dict(model=7),
        "notices item not str": dict(notices=[None]),
        "answer is null": dict(answer=None),
    }

    def write_lines(self, lines):
        self.config()
        sdir = self.state / "sessions"
        sdir.mkdir(mode=0o700, exist_ok=True)
        (sdir / "default.jsonl").write_text("".join(l + "\n" for l in lines), encoding="utf-8")

    def test_each_malformed_line_is_skipped_valid_lines_return(self):
        cases = {name: json.dumps({**turn(1), **patch}) for name, patch in self.BAD.items()}
        missing = turn(1)
        del missing["notices"]
        cases["notices missing"] = json.dumps(missing)
        cases["non-JSON line"] = "this is not json {"
        cases["JSON but not an object"] = "[1, 2, 3]"
        for name, bad in cases.items():
            with self.subTest(name):
                self.write_lines([json.dumps(turn(1)), bad, json.dumps(turn(2))])
                turns, skipped = read_session(self.state, "default")
                self.assertEqual([t["question"][:2] for t in turns], ["q1", "q2"])
                self.assertEqual(skipped, 1)

    def test_history_json_array_unchanged_and_skip_count_on_stderr(self):
        self.write_lines([json.dumps(turn(1)), "garbage", json.dumps({**turn(2), "fast_path": "yes"}),
                          json.dumps(turn(3))])
        code, out, err = self.run_cli("history", "--session", "default", "--json")
        self.assertEqual(code, 0)
        turns = json.loads(out)
        self.assertIsInstance(turns, list)
        self.assertEqual([t["question"][:2] for t in turns], ["q1", "q3"])
        self.assertEqual(json.loads(err), {"skipped_lines": 2})

    def test_skip_count_zero_when_clean(self):
        code, out, err = self.run_cli("history", "--session", "default", "--json")
        self.assertEqual((json.loads(out), json.loads(err)), ([], {"skipped_lines": 0}))

    def test_extra_fields_are_dropped(self):
        self.write_lines([json.dumps({**turn(1), "secret": "x"})])
        self.assertEqual(set(read_turns(self.state, "default")[0]), set(sessions.TURN_FIELDS))

    def test_invalid_turn_is_never_written(self):
        self.config()
        for name, patch in self.BAD.items():
            with self.subTest(name), self.assertRaises(TurnError):
                append_turn(self.state, "default", {**turn(1), **patch})
        self.assertFalse((self.state / "sessions" / "default.jsonl").exists())

    def test_malformed_history_lines_are_not_sent_to_the_model(self):
        self.write_lines([json.dumps({**turn(1), "answer": None}), json.dumps(turn(2))])
        chat = ScriptedChat(answer("ok"))
        with mock.patch.object(ModelClient, "chat", chat):
            code, _, _ = self.run_cli("ask", "--session", "default", "--json", "tell me something")
        self.assertEqual(code, 0)
        convo = [m["content"][:2] for m in chat.calls[0] if m["role"] in ("user", "assistant")]
        self.assertEqual(convo, ["q2", "a2", "te"])


class AskSessionTests(CliCase):
    def test_session_turns_become_history_and_new_turn_is_appended(self):
        chat = ScriptedChat(answer("first answer"), answer("second answer"))
        with mock.patch.object(ModelClient, "chat", chat):
            code, out, _ = self.run_cli("ask", "--session", "default", "--json", "tell me a joke")
            self.assertEqual(code, 0)
            first = json.loads(out)
            code, out, _ = self.run_cli("ask", "--session", "default", "--json", "another one")
        second = json.loads(out)
        for key in ("ok", "answer", "tools_used", "model", "notices", "fast_path"):
            self.assertIn(key, second)
        self.assertEqual(second["session_id"], "default")
        self.assertEqual(first["answer"], "first answer")
        self.assertIn("ts", second)
        history = [m for m in chat.calls[1] if m["role"] in ("user", "assistant")]
        self.assertEqual([m["content"] for m in history],
                         ["tell me a joke", "first answer", "another one"])
        turns = read_turns(self.state, "default")
        self.assertEqual([t["answer"] for t in turns], ["first answer", "second answer"])
        self.assertEqual(turns[1]["model"], "fake-model")
        self.assertIsInstance(turns[1]["total_ms"], int)

    def test_ask_history_is_capped(self):
        self.config()
        for i in range(14):
            append_turn(self.state, "s1", turn(i))
        chat = ScriptedChat(answer("ok"))
        with mock.patch.object(ModelClient, "chat", chat):
            self.run_cli("ask", "--session", "s1", "--json", "tell me something")
        convo = [m for m in chat.calls[0] if m["role"] in ("user", "assistant")]
        self.assertEqual(len(convo), 2 * sessions.MAX_TURNS + 1)

    def test_without_session_nothing_is_recorded_and_json_has_null_session(self):
        with mock.patch.object(ModelClient, "chat", ScriptedChat(answer("hi"))):
            code, out, _ = self.run_cli("ask", "--json", "hello there")
        self.assertEqual(code, 0)
        self.assertIsNone(json.loads(out)["session_id"])
        self.assertFalse((self.state / "sessions").exists())

    def test_fast_path_records_into_session(self):
        with mock.patch.object(ModelClient, "chat", side_effect=AssertionError("no model call")):
            code, out, _ = self.run_cli("ask", "--session", "default", "--json", "what time is it")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["fast_path"])
        turns = read_turns(self.state, "default")
        self.assertEqual(len(turns), 1)
        self.assertTrue(turns[0]["fast_path"])
        self.assertIsNone(turns[0]["model"])
        self.assertEqual(turns[0]["tools_used"], ["time.now"])

    def test_stopped_ask_with_session_appends_nothing(self):
        self.run_cli("stop", "test")
        for q in ("what time is it", "tell me a joke"):
            code, out, _ = self.run_cli("ask", "--session", "default", "--json", q)
            self.assertEqual(code, cli.EXIT_STOPPED)
            self.assertEqual(json.loads(out)["error_kind"], "stopped")
        self.assertEqual(read_turns(self.state, "default"), [])
        self.assertFalse((self.state / "sessions").exists())

    def test_invalid_session_ids_are_usage_errors(self):
        for sid in ("../x", "A", "", "a" * 41):
            code, out, _ = self.run_cli("ask", "--session", sid, "--json", "hello")
            self.assertEqual(code, cli.EXIT_USAGE, sid)
            self.assertEqual(json.loads(out)["error_kind"], "usage")
            code, out, _ = self.run_cli("history", "--session", sid, "--json")
            self.assertEqual(code, cli.EXIT_USAGE, sid)
        self.assertFalse((self.state / "sessions").exists())
        self.assertEqual(list(self.state.parent.glob("x*")), [])


class ErrorKindTests(CliCase):
    def test_model_unavailable(self):
        down = ModelError("request to 127.0.0.1 failed: connection refused")
        with mock.patch.object(ModelClient, "chat", ScriptedChat(down)):
            code, out, _ = self.run_cli("ask", "--session", "default", "--json", "hello there")
        self.assertEqual(code, cli.EXIT_MODEL)
        payload = json.loads(out)
        self.assertEqual(payload["ok"], False)
        self.assertEqual(payload["error_kind"], "model_unavailable")
        self.assertIn("error", payload)
        self.assertEqual(read_turns(self.state, "default"), [])

    def test_usage(self):
        code, out, _ = self.run_cli("ask", "--json")
        self.assertEqual(code, cli.EXIT_USAGE)
        self.assertEqual(json.loads(out)["error_kind"], "usage")

    def test_internal_has_no_traceback(self):
        with mock.patch.object(ModelClient, "chat", side_effect=RuntimeError("boom secret")):
            code, out, err = self.run_cli("ask", "--json", "hello there")
        self.assertEqual(code, cli.EXIT_INTERNAL)
        payload = json.loads(out)
        self.assertEqual(payload["error_kind"], "internal")
        self.assertNotIn("Traceback", out + err)
        self.assertNotIn("boom secret", out)

    def test_stopped_brief(self):
        self.run_cli("stop")
        code, out, _ = self.run_cli("brief", "--json")
        self.assertEqual(code, cli.EXIT_STOPPED)
        self.assertEqual(json.loads(out)["error_kind"], "stopped")


class HistoryTests(CliCase):
    def test_returns_turns_with_all_fields(self):
        self.config()
        append_turn(self.state, "default", turn(1))
        code, out, _ = self.run_cli("history", "--session", "default", "--json")
        self.assertEqual(code, 0)
        turns = json.loads(out)
        self.assertEqual(len(turns), 1)
        self.assertEqual(set(turns[0]), {"ts", "question", "answer", "tools_used", "fast_path",
                                         "model", "notices", "total_ms"})

    def test_missing_session_is_empty_and_read_only(self):
        code, out, _ = self.run_cli("history", "--session", "default", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), [])
        self.assertFalse((self.state / "sessions").exists())
        self.assertFalse((self.state / "audit.jsonl").exists())

    def test_history_does_not_modify_session(self):
        self.config()
        append_turn(self.state, "default", turn(1))
        path = self.state / "sessions" / "default.jsonl"
        before = path.read_bytes()
        self.run_cli("history", "--session", "default", "--json")
        self.assertEqual(path.read_bytes(), before)

    def bad_session(self, kind, sid="default"):
        """Make sessions/<sid>.jsonl a directory, a symlink, or an unreadable file."""
        self.config()
        sdir = self.state / "sessions"
        sdir.mkdir(mode=0o700, exist_ok=True)
        path = sdir / f"{sid}.jsonl"
        if kind == "directory":
            path.mkdir(mode=0o700)
        elif kind == "symlink":
            target = self.state / f"{sid}-target.jsonl"
            target.write_text(json.dumps(turn(1)) + "\n", encoding="utf-8")
            path.symlink_to(target)
        else:
            path.write_text(json.dumps(turn(1)) + "\n", encoding="utf-8")
            path.chmod(0o000)  # removable with the temp dir: deletion needs only the dir's mode
        return path

    def test_bad_session_path_is_a_clean_refusal(self):
        """se-bad-007 / se-bad-008: history refuses like ask, never with a traceback."""
        for kind in ("directory", "symlink", "unreadable"):
            for command in ("history", "ask"):
                with self.subTest(kind=kind, command=command):
                    sid = f"{kind}-{command}"
                    self.bad_session(kind, sid)
                    argv = [command, "--session", sid, "--json"]
                    argv += ["what time is it"] if command == "ask" else []
                    code, out, err = self.run_cli(*argv)
                    self.assertEqual(code, cli.EXIT_INTERNAL)
                    payload = json.loads(out)
                    self.assertEqual((payload["ok"], payload["error_kind"]), (False, "internal"))
                    self.assertIn(f"session {sid} cannot be read", payload["error"])
                    self.assertNotIn("Traceback", out + err)
                    code, out, err = self.run_cli(*[a for a in argv if a != "--json"])
                    self.assertEqual(code, cli.EXIT_INTERNAL)
                    self.assertEqual(out, "")
                    self.assertIn(f"cos: session {sid} cannot be read", err)
                    self.assertNotIn("Traceback", err)

    def test_symlinked_session_target_is_never_read_or_written(self):
        self.bad_session("symlink")
        target = self.state / "default-target.jsonl"
        before = target.read_bytes()
        code, out, _ = self.run_cli("ask", "--session", "default", "--json", "what time is it")
        self.assertEqual(code, cli.EXIT_INTERNAL)
        self.assertNotIn("answer", json.loads(out))
        self.assertEqual(target.read_bytes(), before)

    def test_history_works_while_stopped(self):
        self.run_cli("stop")
        code, out, _ = self.run_cli("history", "--session", "default", "--json")
        self.assertEqual((code, json.loads(out)), (0, []))


class StatusTests(CliCase):
    FIELDS = {"ok", "kill_switch", "kill_switch_reason", "model", "fallback_model",
              "ollama_reachable", "loaded_models", "audit", "version"}

    def test_fields_with_ollama_up(self):
        http = FakeHttp([{"models": [{"name": "qwen3.6:35b"}]}])
        report = cli.status_report(self.config(), http=http)
        self.assertEqual(set(report), self.FIELDS)
        self.assertTrue(report["ollama_reachable"])
        self.assertEqual(report["loaded_models"], ["qwen3.6:35b"])
        self.assertEqual(report["audit"], "empty")
        self.assertFalse(report["kill_switch"])
        self.assertIsNone(report["kill_switch_reason"])
        self.assertEqual([c["method"] for c in http.calls], ["GET"])
        self.assertTrue(http.calls[0]["url"].endswith("/api/ps"))

    def test_ollama_down(self):
        http = FakeHttp([EgressError("request to 127.0.0.1 failed: refused")])
        report = cli.status_report(self.config(), http=http)
        self.assertFalse(report["ollama_reachable"])
        self.assertEqual(report["loaded_models"], [])

    def test_kill_switch_reported_with_reason(self):
        KillSwitch(self.config().state_dir).stop("lunch")
        report = cli.status_report(self.config(), http=FakeHttp([EgressError("down")]))
        self.assertTrue(report["kill_switch"])
        self.assertIn("lunch", report["kill_switch_reason"])

    def test_cli_status_makes_zero_model_calls_and_writes_no_audit(self):
        def fake_request(method, url, **kw):
            self.assertEqual(method, "GET")
            self.assertTrue(url.endswith("/api/ps"))
            self.assertEqual(kw.get("timeout"), cli.STATUS_TIMEOUT_S)
            return b'{"models": []}'

        with mock.patch.object(ModelClient, "chat", side_effect=AssertionError("no model call")), \
                mock.patch.object(cli.egress, "request", fake_request), \
                mock.patch("cos.model.egress.request", fake_request):
            code, out, _ = self.run_cli("status", "--json")
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(set(report), self.FIELDS)
        self.assertTrue(report["ollama_reachable"])
        self.assertFalse((self.state / "audit.jsonl").exists())

    def test_cli_status_with_ollama_down(self):
        def refused(method, url, **kw):
            raise EgressError("request to 127.0.0.1 failed: connection refused")

        with mock.patch.object(cli.egress, "request", refused):
            code, out, _ = self.run_cli("status", "--json")
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(out)["ollama_reachable"])

    def test_audit_states(self):
        self.run_cli("stop")  # writes an audit record
        report = cli.status_report(self.config(), http=FakeHttp([EgressError("down")]))
        self.assertEqual(report["audit"], "ok")
        (self.state / "audit.jsonl").write_text("tampered\n")
        report = cli.status_report(self.config(), http=FakeHttp([EgressError("down")]))
        self.assertEqual(report["audit"], "fail")


if __name__ == "__main__":
    unittest.main()
