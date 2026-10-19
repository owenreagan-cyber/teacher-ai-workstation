"""One message from Owen in, one answer out: the path every surface (cos ask, cos chat) uses.

  1. The deterministic fast path (cos/fastpath.py): the typed "search …" command, exact
     time / date / weather / Mac questions, social replies, unload, loaded models, next action.
  2. The router (cos/intent.py) labels everything else, with patterns first and the local model
     as the fallback.
  3. The label picks the path:
       web_lookup     an automatic web search (D-022) when auto_search is on: the query is built by
                      cos/search_query.py from Owen's own messages, shown as "Searched: …", and
                      capped by the daily and monthly limits; when it is off, nothing is searched
       weather        written by code from weather.today for a named place (cos/weather_answer.py)
       reminders      a plain "what reminders are due" is listed by code; other questions go to
                      the agent
       brief          the full deterministic brief (no model)
       capabilities   a fixed answer from cos/capabilities.py (no model)
       local_files    the not-built-yet answer (no model, never web search)
       mail           the not-built-yet answer (no model, never web search)
       anything else  the agent loop (model + read-only tools); web.search is never offered to it

Every fixed answer is audited (request, route, answer) and honors the kill switch like the
fast path: if it is set, nothing is answered. Every answer, whatever the path, keeps only URLs
that came from that turn's tool results (guards.strip_urls).
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
from cos.guards import strip_urls
from cos.intent import REMINDER_LIST, Route, classify, normalize
from cos.model import ModelError
from cos.search_query import build as build_query
from cos.tools.web_search import AUTO_SOURCE

FIXED_LABELS = frozenset({"capabilities", "local_files", "mail"})
# Live data code fetches before the model answers a question on that topic (never invented).
PREFETCH = {"time": ("time.now",), "calendar": ("calendar.today",), "reminders": ("reminders.due",),
            "mac_status": ("mac.status",)}
MIN_QUERY_WORDS = 2
MAX_LISTED_REMINDERS = 10


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
        if result is None:
            result = self._routed(question, previous, history, mode)
        result.answer, removed = strip_urls(result.answer, result.allowed_urls)
        if removed:
            self.rt.audit("answer_guard", guard="urls", removed=removed)
        return result

    def _routed(self, question: str, previous: dict | None, history: list[dict] | None,
                mode: str) -> AgentResult:
        route = classify(question, previous, model_label=self._model_label)
        self.rt.audit("route", label=route.label, source=route.source, rule=route.rule)
        if route.label == "web_lookup":
            result = self._web_lookup(question, previous, mode)
        elif route.label == "weather":
            result = self._weather(question, previous, mode)
        elif route.label == "reminders" and REMINDER_LIST.fullmatch(normalize(question)):
            result = self._reminders(question, mode)
        elif route.label == "brief":
            result = self._brief(question, mode)
        elif route.label in FIXED_LABELS:
            result = self._fixed(question, route, mode)
        else:
            result = self.agent.run(question, history=history, mode=mode,
                                    prefetch=() if route.rule == "action" else PREFETCH.get(route.label, ()))
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

    def _rewrite(self, message: str, previous_query: str) -> str | None:
        try:
            return self.agent.rewrite_query(message, previous_query)
        except ModelError as e:  # code joins the two instead
            self.rt.audit("search_query_rewrite_failed", error=str(e)[:200])
            return None

    def _web_lookup(self, question: str, previous: dict | None, mode: str) -> AgentResult:
        """Search the web automatically. The query is built from Owen's own messages; a follow-up
        may join the previous turn's query only when that turn was a web_lookup too."""
        query = build_query(question, previous, rewrite=self._rewrite)
        self.rt.audit("search_query", source=query.source, chars=len(query.text))
        if len(query.text.split()) < MIN_QUERY_WORDS:  # "search" alone is not a question for the web
            return self.agent.run(question, mode=mode)
        if not self.rt.config.auto_search:
            started, timing = time.monotonic(), {}
            close = self._closer("web_lookup", started, timing)
            self.rt.audit("request", mode=mode, path="router", intent="web_lookup", prompt=text_digest(question),
                          tools_offered=[])
            if self.rt.kill_switch.is_set():
                close("request_stopped", reason="kill_switch")
                raise Stopped("kill switch is set")
            text = (f"Auto web search is off, so I didn't search the web. Type \"search {query.text}\" to "
                    "search, or turn Auto web search on from the menu bar icon.")
            close("answer", tools_used=[], chars=len(text), auto_search=False)
            return AgentResult(text, [], None, fast_path=True)
        return self.fastpath.search(question, query.text, mode, source=AUTO_SOURCE)

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

    def _reminders(self, question: str, mode: str) -> AgentResult:
        """The reminders that are due, listed by code. Titles are quoted as data (D-002)."""
        started, timing = time.monotonic(), {"tool_ms": 0}
        close = self._closer("reminders", started, timing)
        self.rt.audit("request", mode=mode, path="router", intent="reminders", prompt=text_digest(question),
                      tools_offered=["reminders.due"])
        decision = self.rt.gate.decide("reminders.due", {}, subject="router")
        tool = self.rt.registry.get("reminders.due")
        if not decision.allowed or tool is None:
            if decision.rule == "kill_switch":
                close("request_stopped", reason="kill_switch")
                raise Stopped("kill switch is set")
            close("answer", tools_used=[], denied=decision.rule)
            return AgentResult(f"I can't read your reminders right now ({decision.reason}).", [], None, fast_path=True)
        tool_started = time.monotonic()
        result = run_tool(tool, {}, decision, audit=self.rt.audit)
        timing["tool_ms"] = int((time.monotonic() - tool_started) * 1000)
        if self.rt.kill_switch.is_set():
            close("request_stopped", reason="kill_switch")
            raise Stopped("kill switch was set during the reminders call")
        text = reminders_text(result)
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


def reminders_text(result: dict) -> str:
    if "error" in result:
        return f"Reminders are unavailable: {result['error']}."
    items = [it for it in result.get("reminders") or [] if isinstance(it, dict)]
    if not items:
        return "No reminders are due."
    lines = [f"{len(items)} reminder{'' if len(items) == 1 else 's'} due:"]
    for it in items[:MAX_LISTED_REMINDERS]:
        tag = f"overdue since {it['due']}" if it.get("overdue") else f"due {it.get('due') or 'today'}"
        lines.append(f"- \u201c{it.get('title')}\u201d ({tag})")
    if len(items) > MAX_LISTED_REMINDERS:
        lines.append(f"…and {len(items) - MAX_LISTED_REMINDERS} more.")
    return "\n".join(lines)
