"""Local Ollama client (urllib via the egress module only).

The base URL must be http://127.0.0.1 or http://localhost; anything else is
refused in the constructor, before any request. Egress enforces the port.
Uses Ollama's native /api/chat with tool calling and optional structured
output (format). Falls back to the fallback model once if the primary fails.

Every request sends "think" (config model_think, default false): Qwen3 models
reason before answering unless told not to, which costs most of the latency.
Every request also sends options.num_ctx (config model_num_ctx, default 16384)
and keep_alive (config model_keep_alive, default "2h"), so the model stays loaded.

Local models only: before every chat request the client refuses a cloud model
name (":cloud" / "-cloud") and asks Ollama's /api/show (same local host, via
egress) for the model's details; a model that reports remote_host or
remote_model is an Ollama cloud model and is refused (CloudModelRefused, audited
as model_refused, no chat request sent, no fallback). The details it checked are
recorded in the model_call audit record as local_check.
"""
from __future__ import annotations

import json
import time
import urllib.parse

from cos import egress
from cos.config import is_cloud_model_name

LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost"})


class ModelRefused(Exception):
    """The model endpoint is not local."""


class CloudModelRefused(Exception):
    """The model is an Ollama cloud model (by name or by /api/show). It is never called."""


class ModelError(Exception):
    def __init__(self, message, malformed_tool_call=False):
        super().__init__(message)
        self.malformed_tool_call = malformed_tool_call


def check_local(base_url: str) -> str:
    try:
        parts = urllib.parse.urlsplit(base_url)
        parts.port  # noqa: B018 - raises on a bad port
    except ValueError as e:
        raise ModelRefused(f"unparseable model base url ({e})")
    if parts.scheme != "http" or parts.hostname not in LOCAL_HOSTS or parts.username or parts.password:
        raise ModelRefused(f"model base url must be local Ollama (http://127.0.0.1:11434), got {base_url!r}")
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        raise ModelRefused("model base url must not carry a path or query")
    return f"http://{parts.netloc}"


class ModelClient:
    def __init__(self, base_url: str, model: str, fallback_model: str | None = None,
                 timeout_s: float = 300, audit=None, http=egress.request, think: bool = False,
                 num_ctx: int = 16384, keep_alive: str = "2h"):
        self.base_url = check_local(base_url)
        self.host = urllib.parse.urlsplit(self.base_url).netloc
        self.model = model
        self.fallback_model = fallback_model
        self.timeout_s = timeout_s
        self.audit = audit
        self.http = http
        self.think = bool(think)
        self.num_ctx = int(num_ctx)
        self.keep_alive = str(keep_alive)

    def _post(self, path: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        raw = self.http("POST", self.base_url + path, body=body,
                        headers={"Content-Type": "application/json"},
                        timeout=self.timeout_s, audit=self.audit)
        return json.loads(raw)

    def _refuse(self, model: str, reason: str, remote_host=None):
        if self.audit is not None:
            self.audit("model_refused", model=model, host=self.host, reason=reason, remote_host=remote_host)
        raise CloudModelRefused(f"model {model!r} is an Ollama cloud model ({reason}); "
                                "cos uses local models only")

    def check_local_model(self, model: str) -> dict:
        """Refuse a cloud model (CloudModelRefused); return the local details /api/show reports.
        A failed /api/show is a ModelError (the model is not called)."""
        if is_cloud_model_name(model):
            self._refuse(model, "cloud model name")
        try:
            info = self._post("/api/show", {"model": model})
        except egress.EgressError as e:
            text = e.body.decode("utf-8", "replace") if e.body else ""
            raise ModelError(f"model check (/api/show) failed: {e} {text[:200]}".strip())
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ModelError(f"model check (/api/show): invalid JSON: {e}")
        if not isinstance(info, dict):
            raise ModelError("model check (/api/show): response is not an object")
        if info.get("remote_host") or info.get("remote_model"):
            self._refuse(model, "/api/show reports a remote host", str(info.get("remote_host") or "")[:200] or None)
        details = info.get("details") if isinstance(info.get("details"), dict) else {}
        return {"remote_host": None, **{k: details.get(k) for k in
                                        ("format", "family", "parameter_size", "quantization_level")}}

    def _chat_once(self, model: str, messages, tools, fmt) -> dict:
        payload = {"model": model, "messages": messages, "stream": False, "think": self.think,
                   "options": {"num_ctx": self.num_ctx}, "keep_alive": self.keep_alive}
        if tools:
            payload["tools"] = tools
        if fmt is not None:
            payload["format"] = fmt
        started = time.monotonic()
        ok, err, malformed, refused, local_check = False, None, False, False, None
        try:
            local_check = self.check_local_model(model)
            data = self._post("/api/chat", payload)
            msg = data.get("message")
            if not isinstance(msg, dict):
                raise ModelError("model response has no message")
            ok = True
            return msg
        except egress.EgressError as e:
            text = e.body.decode("utf-8", "replace") if e.body else ""
            malformed = "tool call" in text.lower() and "pars" in text.lower()
            err = f"{e} {text[:200]}".strip()
            raise ModelError(err, malformed_tool_call=malformed)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            err = f"invalid JSON from model: {e}"
            raise ModelError(err)
        except ModelError as e:
            err = str(e)
            raise
        except CloudModelRefused:
            refused = True  # audited as model_refused; no chat request was sent
            raise
        finally:
            if self.audit is not None and not refused:
                self.audit("model_call", model=model, host=self.host, ok=ok,
                           think=self.think, num_ctx=self.num_ctx, keep_alive=self.keep_alive,
                           model_ms=int((time.monotonic() - started) * 1000),
                           tools_offered=len(tools or []), local_check=local_check, error=err)

    def chat(self, messages, tools=None, fmt=None) -> tuple[dict, str]:
        """Return (message, model_used)."""
        try:
            return self._chat_once(self.model, messages, tools, fmt), self.model
        except ModelError as e:
            if e.malformed_tool_call or not self.fallback_model:
                raise
            return self._chat_once(self.fallback_model, messages, tools, fmt), self.fallback_model

    def loaded_models(self, timeout_s: float = 3) -> list[str]:
        raw = self.http("GET", self.base_url + "/api/ps", timeout=timeout_s, audit=self.audit)
        return [m.get("name", "?") for m in json.loads(raw).get("models", [])]
