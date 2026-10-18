"""One message from Owen in, one answer out: the path every surface (cos ask, cos chat) uses.

  1. The deterministic fast path (cos/fastpath.py): the typed "search …" command, exact
     time / date / weather / Mac questions, social replies, unload, loaded models, next action.
  2. The router (cos/intent.py) labels everything else, with patterns first and the local model
     as the fallback.
  3. The label picks the path:
       weather        written by code from weather.today for a named place (cos/weather_answer.py)
       brief          the full deterministic brief (no model)
       capabilities   a fixed answer from cos/capabilities.py (no model)
       local_files    the not-built-yet answer (no model, never web search)
       mail           the not-built-yet answer (no model, never web search)
       anything else  the agent loop (model + read-only tools); web.search is never offered to it

Every fixed answer is audited (request, route, answer) and honors the kill switch like the
fast path: if it is set, nothing is answered.
"""
from __future__ import annotations

import time

from cos import weather_answer
from cos.agent import AgentResult, Stopped
from cos.audit import text_digest
from cos.brief import BRIEF_TOOLS, format_brief, gather
from cos.capabilities import answer_for, capabilities_answer
from cos.config import weather_places
from cos.executor import run_tool
from cos.intent import Route, classify
from cos.model import ModelError

FIXED_LABELS = frozenset({"capabilities", "local_files", "mail"})


class Responder:
    def __init__(self, rt, make_fastpath, make_agent):
        """rt: cli.Runtime. make_fastpath(rt) and make_agent(rt) build the fast path and the agent
        (the agent, and its memory files, only when a path needs it)."""
        self.rt = rt
        self.fastpath = make_fastpath(rt)
        self._make_agent = make_agent
        self._agent = None

    @property
    def agent(self):
        if self._agent is None:
            self._agent = self._make_agent(self.rt)
        return self._agent

    def _model_label(self, message: str, previous: str | None) -> str | None:
        """The model's label. A ModelError propagates: a message no pattern matched needs the
        model anyway, so the answer is "local model unavailable" rather than a second wait."""
        try:
            return self.agent.classify(message, previous)
        except ModelError as e:
            self.rt.audit("route_model_failed", error=str(e)[:200])
            raise

    def answer(self, question: str, previous: dict | None = None, history: list[dict] | None = None,
               mode: str = "ask") -> AgentResult:
        """previous: the last turn of this conversation ({"question", "intent", ...}) or None.
        history: prior turns as chat messages for the agent. Raises Stopped or ModelError."""
        result = self.fastpath.answer(question, mode=mode)
        if result is not None:
            return result
        route = classify(question, previous, model_label=self._model_label)
        self.rt.audit("route", label=route.label, source=route.source, rule=route.rule)
        if route.label == "weather":
            result = self._weather(question, previous, mode)
        elif route.label == "brief":
            result = self._brief(question, mode)
        elif route.label in FIXED_LABELS:
            result = self._fixed(question, route, mode)
        else:
            result = self.agent.run(question, history=history, mode=mode)
        result.intent = route.label
        return result

    # ------------------------------------------------------------------------- fixed paths

    def _closer(self, label: str, started: float, timing: dict):
        def close(kind, **fields):
            self.rt.audit(kind, path="router", intent=label, model_ms=0, tool_ms=timing.get("tool_ms", 0),
                          total_ms=int((time.monotonic() - started) * 1000), **fields)
        return close

    def _fixed(self, question: str, route: Route, mode: str) -> AgentResult:
        started, timing = time.monotonic(), {}
        close = self._closer(route.label, started, timing)
        self.rt.audit("request", mode=mode, path="router", intent=route.label, prompt=text_digest(question),
                      tools_offered=[])
        if self.rt.kill_switch.is_set():
            close("request_stopped", reason="kill_switch")
            raise Stopped("kill switch is set")
        if route.label == "capabilities":
            text = capabilities_answer(self.rt.registry, self.rt.config)
        elif route.label == "mail" and route.rule == "mail_send":
            text = answer_for("mail_send")
        else:
            text = answer_for(route.label)
        close("answer", tools_used=[], chars=len(text))
        return AgentResult(text, [], None, fast_path=True)

    def _weather(self, question: str, previous: dict | None, mode: str) -> AgentResult:
        """Weather for a named place, written by code. A place Chief doesn't know gets the fixed
        answer and no tool call; a follow-up keeps the place of the previous weather question."""
        started, timing = time.monotonic(), {"tool_ms": 0}
        close = self._closer("weather", started, timing)
        self.rt.audit("request", mode=mode, path="router", intent="weather", prompt=text_digest(question),
                      tools_offered=["weather.today"])
        if self.rt.kill_switch.is_set():
            close("request_stopped", reason="kill_switch")
            raise Stopped("kill switch is set")
        places = weather_places(self.rt.config)
        prev_q = (previous or {}).get("question") if (previous or {}).get("intent") == "weather" else None
        req = weather_answer.parse(question, places, prev_q) if places else None
        if places and req is None:
            text = weather_answer.unknown_place_answer(places)
            close("answer", tools_used=[], chars=len(text))
            return AgentResult(text, [], None, fast_path=True)
        args = {"place": req.place.key} if req else {}
        decision = self.rt.gate.decide("weather.today", args, subject="router")
        tool = self.rt.registry.get("weather.today")
        if not decision.allowed or tool is None:
            if decision.rule == "kill_switch":
                close("request_stopped", reason="kill_switch")
                raise Stopped("kill switch is set")
            close("answer", tools_used=[], denied=decision.rule)
            return AgentResult(f"I can't check the weather right now ({decision.reason}).", [], None, fast_path=True)
        tool_started = time.monotonic()
        result = run_tool(tool, args, decision, audit=self.rt.audit)
        timing["tool_ms"] = int((time.monotonic() - tool_started) * 1000)
        if self.rt.kill_switch.is_set():
            close("request_stopped", reason="kill_switch")
            raise Stopped("kill switch was set during the weather call")
        if req is None:
            text = f"Weather is unavailable: {result.get('error', 'no weather places are set')}."
        else:
            text, _shown = weather_answer.render(req, result, places)
        close("answer", tools_used=[tool.name], chars=len(text))
        return AgentResult(text, [tool.name], None, fast_path=True)

    def _brief(self, question: str, mode: str) -> AgentResult:
        started, timing = time.monotonic(), {"tool_ms": 0}
        close = self._closer("brief", started, timing)
        self.rt.audit("request", mode=mode, path="router", intent="brief", prompt=text_digest(question),
                      tools_offered=list(BRIEF_TOOLS))
        if self.rt.kill_switch.is_set():
            close("request_stopped", reason="kill_switch")
            raise Stopped("kill switch is set")
        results = gather(self.rt.registry, self.rt.gate, audit=self.rt.audit, timing=timing)
        if self.rt.kill_switch.is_set():  # set while the brief was gathered: show nothing from it
            close("request_stopped", reason="kill_switch")
            raise Stopped("kill switch was set during the brief")
        used = [name for name in BRIEF_TOOLS if self.rt.registry.get(name) is not None
                and not str(results.get(name, {}).get("error", "")).startswith("denied:")]
        text = "\n".join(format_brief(results))
        close("answer", tools_used=used, chars=len(text))
        return AgentResult(text, used, None, fast_path=True)
