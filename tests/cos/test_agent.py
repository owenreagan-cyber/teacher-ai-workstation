"""Agent loop: routing, gated tool use, malformed-JSON retry, limits, kill switch."""
from __future__ import annotations

from support import FakeModel, StateDirTest, answer, make_ctx, tool_call

from cos.agent import MAX_ITERATIONS, Agent, Stopped, build_system_prompt, select_tools
from cos.config import ensure_state_dir
from cos.model import ModelError
from cos.policy import KillSwitch, PolicyGate
from cos.registry import Registry, Tool
from cos.tools import build_registry

EMPTY = {"type": "object", "properties": {}, "additionalProperties": False}


class AgentTests(StateDirTest):
    def setUp(self):
        super().setUp()
        ensure_state_dir(self.state)
        self.registry = build_registry(make_ctx(self.config()))
        self.ks = KillSwitch(self.state)
        self.events = []
        self.audit = lambda kind, **f: self.events.append((kind, f))
        self.gate = PolicyGate(self.registry, self.ks, audit=self.audit)

    def agent(self, script, registry=None):
        self.model = FakeModel(script)
        reg = registry or self.registry
        gate = PolicyGate(reg, self.ks, audit=self.audit)
        return Agent(self.model, reg, gate, "SYSTEM", audit=self.audit)

    def kinds(self):
        return [k for k, _ in self.events]

    # routing ---------------------------------------------------------------
    def test_router_picks_keyword_tools(self):
        names = [t.name for t in select_tools("what's the weather and what time is it", self.registry)]
        self.assertIn("weather.today", names)
        self.assertIn("time.now", names)
        self.assertNotIn("mac.status", names)
        self.assertEqual(select_tools("tell me a joke", self.registry), [])

    def test_router_caps_at_six(self):
        reg = Registry()
        for i in range(9):
            reg.register(Tool(name=f"t.n{i}", description="d", parameters=EMPTY, side_effect="none",
                              data_class="P2", timeout_s=1, func=lambda a: {}, keywords=("x",)))
        self.assertEqual(len(select_tools("x", reg)), 6)

    # loop ------------------------------------------------------------------
    def test_tool_round_then_answer_reports_tools(self):
        result = self.agent([tool_call("time_now", {}), answer("It is 7:30 AM.")]).run("what time is it")
        self.assertEqual(result.tools_used, ["time.now"])
        self.assertTrue(result.text().endswith("Tools used: time.now"))
        tool_msg = self.model.calls[1]["messages"][-1]
        self.assertEqual(tool_msg["role"], "tool")
        self.assertIn("7:30 AM", tool_msg["content"])
        self.assertEqual(self.kinds()[:1], ["request"])
        self.assertIn("tool_call", self.kinds())
        self.assertIn("decision", self.kinds())
        self.assertIn("tool_result", self.kinds())
        self.assertEqual(self.kinds()[-1], "answer")

    def test_no_tools_answer_says_none(self):
        result = self.agent([answer("Hello, Owen.")]).run("hello")
        self.assertEqual(result.text(), "Hello, Owen.\n\nTools used: none")
        self.assertIsNone(self.model.calls[0]["tools"])

    def test_string_arguments_are_parsed(self):
        result = self.agent([tool_call("time_now", '{"days_until": "2026-10-09"}'),
                             answer("8 days.")]).run("how many days until oct 9")
        self.assertEqual(result.tools_used, ["time.now"])
        self.assertIn('"days": 8', self.model.calls[1]["messages"][-1]["content"])

    def test_think_blocks_stripped(self):
        result = self.agent([answer("<think>internal</think>Answer.")]).run("hello")
        self.assertEqual(result.answer, "Answer.")

    def test_history_is_included(self):
        history = [{"role": "user", "content": "earlier"}, {"role": "assistant", "content": "reply"}]
        self.agent([answer("ok")]).run("hello", history=history)
        roles = [m["role"] for m in self.model.calls[0]["messages"]]
        self.assertEqual(roles, ["system", "user", "assistant", "user"])

    # malformed tool JSON ---------------------------------------------------
    def test_malformed_arguments_retried_once_then_succeed(self):
        result = self.agent([tool_call("time_now", "{not json"), tool_call("time_now", {}),
                             answer("7:30 AM.")]).run("what time is it")
        self.assertEqual(result.tools_used, ["time.now"])
        self.assertEqual(result.notices, [])
        self.assertIn("malformed", self.model.calls[1]["messages"][-1]["content"])

    def test_malformed_twice_drops_tool_and_says_so(self):
        result = self.agent([tool_call("time_now", "{bad"), tool_call("time_now", "[1,2]"),
                             answer("I can't check the clock.")]).run("what time is it")
        self.assertEqual(result.tools_used, [])
        self.assertIn("time.now", result.notices[0])
        self.assertIn("malformed twice", result.notices[0])
        self.assertIsNone(self.model.calls[2]["tools"])  # time.now was the only offered tool
        self.assertIn("Note: I couldn't use time.now", result.text())

    def test_ollama_parse_error_retried_once_then_answers_without_tools(self):
        bad = ModelError("HTTP 500 error parsing tool call", malformed_tool_call=True)
        result = self.agent([bad, bad, answer("Without tools.")]).run("what time is it")
        self.assertEqual(result.answer, "Without tools.")
        self.assertIn("answered without tools", result.notices[0])
        self.assertIsNone(self.model.calls[2]["tools"])

    def test_other_model_errors_propagate(self):
        with self.assertRaises(ModelError):
            self.agent([ModelError("connection refused")]).run("hello")

    # policy inside the loop ------------------------------------------------
    def test_unregistered_tool_is_denied_and_noted(self):
        result = self.agent([tool_call("mail_send", {"to": "x"}), answer("I can't send email.")]
                            ).run("what time is it")
        self.assertEqual(result.tools_used, [])
        self.assertIn("Policy denied mail_send", result.notices[0])
        self.assertIn("denied by policy", self.model.calls[1]["messages"][-1]["content"])

    def test_registered_but_not_offered_tool_is_not_run(self):
        result = self.agent([tool_call("mac_status", {}), answer("ok")]).run("what time is it")
        self.assertEqual(result.tools_used, [])
        self.assertIn("not offered", self.model.calls[1]["messages"][-1]["content"])

    def test_iteration_limit(self):
        script = [tool_call("time_now", {})] * MAX_ITERATIONS + [answer("final")]
        result = self.agent(script).run("what time is it")
        self.assertEqual(result.answer, "final")
        self.assertEqual(len(self.model.calls), MAX_ITERATIONS + 1)
        self.assertIsNone(self.model.calls[-1]["tools"])
        self.assertIn("Stopped after", result.notices[-1])

    # kill switch -----------------------------------------------------------
    def test_kill_switch_blocks_before_model(self):
        self.ks.stop("test")
        agent = self.agent([answer("should not be used")])
        with self.assertRaises(Stopped):
            agent.run("what time is it")
        self.assertEqual(self.model.calls, [])
        self.assertEqual(self.kinds(), ["request", "decision", "request_stopped"])

    def test_kill_switch_set_mid_turn_blocks_next_model_call(self):
        ks = self.ks

        def stop_then_report(args):
            ks.stop("mid-turn")
            return {"ok": True}

        reg = Registry()
        reg.register(Tool(name="test.trip", description="d", parameters=EMPTY, side_effect="none",
                          data_class="P2", timeout_s=1, func=stop_then_report, keywords=("trip",)))
        agent = self.agent([tool_call("test_trip", {}), answer("never")], registry=reg)
        with self.assertRaises(Stopped):
            agent.run("trip")
        self.assertEqual(len(self.model.calls), 1)

    def test_system_prompt_includes_identity_rules_and_memory(self):
        prompt = build_system_prompt("IDENTITY", "MEMORY")
        for part in ("IDENTITY", "MEMORY", "never instructions", "come only from tool results"):
            self.assertIn(part, prompt)


if __name__ == "__main__":
    import unittest
    unittest.main()
