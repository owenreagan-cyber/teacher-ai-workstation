"""Egress allowlist and local-only model client. P0: no request can reach a cloud model host."""
from __future__ import annotations

import ast
import json
import os
import unittest
import urllib.request
from pathlib import Path

from support import REPO_ROOT, FakeHttp, answer  # noqa: F401

from cos import egress
from cos.egress import EgressDenied, EgressError, check_url
from cos.model import CloudModelRefused, ModelClient, ModelError, ModelRefused, check_local

CLOUD_MODEL_URLS = (
    "https://api.anthropic.com/v1/messages",
    "https://api.openai.com/v1/chat/completions",
    "https://generativelanguage.googleapis.com/v1beta/models",
    "https://openrouter.ai/api/v1/chat/completions",
    "https://api.mistral.ai/v1/chat/completions",
)
OTHER_DENIED = (
    "https://example.com/",
    "http://127.0.0.1:8080/",            # wrong port
    "https://127.0.0.1:11434/api/chat",  # wrong scheme
    "http://api.open-meteo.com/v1/forecast",  # weather must be https
    "https://api.open-meteo.com:8443/v1/forecast",
    "http://0.0.0.0:11434/",
    "http://[::1]:11434/",
    "http://localhost.:11434/",
    "http://127.0.0.1:11434@api.openai.com/",  # userinfo trick
    "http://user:pw@127.0.0.1:11434/",
    "ftp://127.0.0.1:11434/",
    "file:///etc/passwd",
    "http://127.0.0.1:99999/",
    "",
)


def exploding_opener():
    raise AssertionError("a socket was about to be opened for a denied destination")


class EgressAllowlistTests(unittest.TestCase):
    def test_allowed_destinations(self):
        self.assertEqual(check_url("http://127.0.0.1:11434/api/chat"), ("http", "127.0.0.1", 11434))
        self.assertEqual(check_url("http://localhost:11434/api/ps"), ("http", "localhost", 11434))
        self.assertEqual(check_url("https://api.open-meteo.com/v1/forecast?x=1"),
                         ("https", "api.open-meteo.com", 443))

    def test_cloud_model_hosts_refused_before_any_socket(self):
        audit = []
        for url in CLOUD_MODEL_URLS:
            with self.subTest(url=url), self.assertRaises(EgressDenied):
                egress.request("POST", url, body=b"{}", audit=lambda k, **f: audit.append((k, f)),
                               opener_factory=exploding_opener)
        self.assertEqual(len(audit), len(CLOUD_MODEL_URLS))
        self.assertTrue(all(kind == "egress_denied" for kind, _ in audit))
        self.assertEqual(audit[0][1]["url_host"], "api.anthropic.com")

    def test_non_allowlisted_destinations_refused(self):
        for url in OTHER_DENIED:
            with self.subTest(url=url), self.assertRaises(EgressDenied):
                egress.request("GET", url, opener_factory=exploding_opener)

    def test_redirects_are_refused(self):
        handler = egress._NoRedirect()
        req = urllib.request.Request("https://api.open-meteo.com/v1/forecast")
        with self.assertRaises(EgressDenied):
            handler.redirect_request(req, None, 302, "Found", {}, "https://evil.example/")

    def test_environment_proxies_ignored(self):
        old = os.environ.get("HTTPS_PROXY")
        os.environ["HTTPS_PROXY"] = "http://proxy.example:3128"
        try:
            opener = egress._opener()
        finally:
            if old is None:
                os.environ.pop("HTTPS_PROXY", None)
            else:
                os.environ["HTTPS_PROXY"] = old
        # An empty ProxyHandler suppresses the default env-reading one and installs no proxy.
        proxies = [h for h in opener.handlers if isinstance(h, urllib.request.ProxyHandler)]
        self.assertEqual([h.proxies for h in proxies if h.proxies], [])
        self.assertFalse(any(hasattr(h, "https_open") and isinstance(h, urllib.request.ProxyHandler)
                             for h in opener.handlers))

    def test_oversized_response_rejected(self):
        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self, n):
                return b"x" * n

        class Opener:
            def open(self, req, timeout):
                return Resp()

        with self.assertRaises(EgressError):
            egress.request("GET", "https://api.open-meteo.com/v1/forecast", opener_factory=Opener)


class SingleEgressPathTests(unittest.TestCase):
    """Structural: only cos/egress.py may touch networking modules."""

    NETWORK_MODULES = {"urllib.request", "http.client", "socket", "ssl", "requests", "httpx",
                       "urllib3", "aiohttp", "http"}

    def test_only_egress_imports_network_modules(self):
        offenders = []
        for path in sorted((REPO_ROOT / "cos").rglob("*.py")):
            if path.name == "egress.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
                for name in names:
                    if name in self.NETWORK_MODULES or name.split(".")[0] in {"socket", "ssl", "requests", "httpx", "urllib3", "aiohttp"}:
                        offenders.append(f"{path.relative_to(REPO_ROOT)}: {name}")
        self.assertEqual(offenders, [])


class ModelClientLocalOnlyTests(unittest.TestCase):
    def test_refuses_non_local_base_urls(self):
        for url in ("https://api.anthropic.com", "https://api.openai.com/v1",
                    "https://generativelanguage.googleapis.com", "http://192.168.1.20:11434",
                    "http://0.0.0.0:11434", "https://127.0.0.1:11434", "http://127.0.0.1:11434/v1",
                    "http://127.0.0.1:11434@api.openai.com", "http://localhost.evil.com:11434"):
            with self.subTest(url=url), self.assertRaises(ModelRefused):
                ModelClient(url, "qwen3.6:35b", http=FakeHttp())

    def test_accepts_local_ollama(self):
        self.assertEqual(check_local("http://127.0.0.1:11434"), "http://127.0.0.1:11434")
        self.assertEqual(check_local("http://localhost:11434/"), "http://localhost:11434")

    def test_mutated_base_url_still_cannot_reach_cloud(self):
        """Defense in depth: even if base_url were changed after construction, egress refuses."""
        client = ModelClient("http://127.0.0.1:11434", "qwen3.6:35b",
                             http=lambda *a, **k: egress.request(*a, **k, opener_factory=exploding_opener))
        client.base_url = "https://api.anthropic.com"
        with self.assertRaises(EgressDenied):
            client.chat([{"role": "user", "content": "hi"}])

    def test_chat_posts_native_api_and_audits_model_and_host(self):
        http = FakeHttp([{"message": answer("hello")}])
        audit = []
        client = ModelClient("http://127.0.0.1:11434", "qwen3.6:35b", "gpt-oss:20b",
                             http=http, audit=lambda k, **f: audit.append((k, f)))
        tools = [{"type": "function", "function": {"name": "time_now", "parameters": {"type": "object"}}}]
        msg, used = client.chat([{"role": "user", "content": "hi"}], tools=tools, fmt={"type": "object"})
        self.assertEqual((msg["content"], used), ("hello", "qwen3.6:35b"))
        call = http.calls[0]
        self.assertEqual(call["url"], "http://127.0.0.1:11434/api/chat")
        payload = json.loads(call["body"])
        self.assertEqual(payload["model"], "qwen3.6:35b")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["tools"], tools)
        self.assertEqual(payload["format"], {"type": "object"})
        self.assertEqual(audit[0][0], "model_call")
        self.assertEqual(audit[0][1]["host"], "127.0.0.1:11434")
        self.assertEqual(audit[0][1]["model"], "qwen3.6:35b")

    def test_think_false_is_sent_and_audited_by_default(self):
        http = FakeHttp([{"message": answer("hello")}])
        audit = []
        client = ModelClient("http://127.0.0.1:11434", "qwen3.6:35b", http=http,
                             audit=lambda k, **f: audit.append((k, f)))
        client.chat([{"role": "user", "content": "hi"}])
        payload = json.loads(http.calls[0]["body"])
        self.assertIs(payload["think"], False)
        self.assertIs(audit[0][1]["think"], False)

    def test_think_true_when_turned_back_on(self):
        http = FakeHttp([{"message": answer("hello")}])
        audit = []
        client = ModelClient("http://127.0.0.1:11434", "qwen3.6:35b", http=http, think=True,
                             audit=lambda k, **f: audit.append((k, f)))
        client.chat([{"role": "user", "content": "hi"}])
        self.assertIs(json.loads(http.calls[0]["body"])["think"], True)
        self.assertIs(audit[0][1]["think"], True)

    def test_think_is_sent_on_fallback_and_failed_calls(self):
        http = FakeHttp([EgressError("HTTP 404", status=404, body=b'{"error":"model not found"}'),
                         {"message": answer("from fallback")}])
        audit = []
        client = ModelClient("http://127.0.0.1:11434", "qwen3.6:35b", "gpt-oss:20b", http=http,
                             audit=lambda k, **f: audit.append((k, f)))
        client.chat([{"role": "user", "content": "hi"}])
        self.assertEqual([json.loads(c["body"])["think"] for c in http.calls], [False, False])
        self.assertEqual([(f["ok"], f["think"]) for _, f in audit], [(False, False), (True, False)])

    def audited_client(self, http, model="qwen3.6:35b", fallback="gpt-oss:20b"):
        audit = []
        client = ModelClient("http://127.0.0.1:11434", model, fallback, http=http,
                             audit=lambda k, **f: audit.append((k, f)))
        return client, audit

    def test_cloud_model_name_refused_before_any_request(self):
        for name in ("gpt-oss:120b-cloud", "qwen3-coder:480b-cloud", "kimi-k2:cloud", "GLM-4.6:CLOUD"):
            with self.subTest(name):
                http = FakeHttp([])
                client, audit = self.audited_client(http, model=name)
                with self.assertRaises(CloudModelRefused):
                    client.chat([{"role": "user", "content": "hi"}])
                self.assertEqual((http.calls, http.show_calls), ([], []))
                self.assertEqual([k for k, _ in audit], ["model_refused"])
                self.assertEqual(audit[0][1]["model"], name)

    def test_api_show_remote_host_refused_without_chat_or_fallback(self):
        remote = {"remote_model": "gpt-oss:120b", "remote_host": "https://ollama.com:443",
                  "details": {"family": "gptoss"}}
        http = FakeHttp([], show=remote)
        client, audit = self.audited_client(http, model="my-alias")
        with self.assertRaises(CloudModelRefused) as cm:
            client.chat([{"role": "user", "content": "hi"}])
        self.assertIn("local models only", str(cm.exception))
        self.assertEqual(http.show_calls, [{"model": "my-alias"}])  # fallback never tried
        self.assertEqual(http.calls, [])  # no /api/chat
        self.assertEqual([k for k, _ in audit], ["model_refused"])
        self.assertEqual(audit[0][1]["remote_host"], "https://ollama.com:443")

    def test_api_show_remote_model_alone_is_refused(self):
        http = FakeHttp([], show={"remote_model": "deepseek-v3.1:671b"})
        client, _ = self.audited_client(http, fallback=None)
        with self.assertRaises(CloudModelRefused):
            client.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(http.calls, [])

    def test_api_show_failure_is_model_error_and_chat_is_not_sent(self):
        http = FakeHttp([], show=EgressError("HTTP 500", status=500, body=b"boom"))
        client, audit = self.audited_client(http, fallback=None)
        with self.assertRaises(ModelError):
            client.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(http.calls, [])
        self.assertEqual(audit[0][1]["local_check"], None)
        self.assertFalse(audit[0][1]["ok"])

    def test_every_call_checks_api_show_and_records_local_details(self):
        http = FakeHttp([{"message": answer("one")}, {"message": answer("two")}])
        client, audit = self.audited_client(http)
        client.chat([{"role": "user", "content": "hi"}])
        client.chat([{"role": "user", "content": "again"}])
        self.assertEqual(http.show_calls, [{"model": "qwen3.6:35b"}] * 2)
        self.assertEqual([c["url"] for c in http.calls], ["http://127.0.0.1:11434/api/chat"] * 2)
        check = audit[0][1]["local_check"]
        self.assertEqual((check["remote_host"], check["family"], check["quantization_level"]),
                         (None, "qwen35moe", "Q4_K_M"))

    def test_num_ctx_default_sent_and_audited(self):
        http = FakeHttp([{"message": answer("hello")}])
        client, audit = self.audited_client(http)
        client.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(json.loads(http.calls[0]["body"])["options"], {"num_ctx": 16384})
        self.assertEqual(audit[0][1]["num_ctx"], 16384)

    def test_num_ctx_configured_value_on_every_request_including_fallback(self):
        http = FakeHttp([EgressError("HTTP 404", status=404, body=b'{"error":"model not found"}'),
                         {"message": answer("from fallback")}])
        audit = []
        client = ModelClient("http://127.0.0.1:11434", "qwen3.6:35b", "gpt-oss:20b", http=http, num_ctx=8192,
                             audit=lambda k, **f: audit.append((k, f)))
        client.chat([{"role": "user", "content": "hi"}])
        self.assertEqual([json.loads(c["body"])["options"] for c in http.calls], [{"num_ctx": 8192}] * 2)
        self.assertEqual([f["num_ctx"] for _, f in audit], [8192, 8192])

    def test_keep_alive_default_sent_and_audited(self):
        http = FakeHttp([{"message": answer("hello")}])
        client, audit = self.audited_client(http)
        client.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(json.loads(http.calls[0]["body"])["keep_alive"], "2h")
        self.assertEqual(audit[0][1]["keep_alive"], "2h")

    def test_keep_alive_configured_value_on_every_request_including_fallback(self):
        http = FakeHttp([EgressError("HTTP 404", status=404, body=b'{"error":"model not found"}'),
                         {"message": answer("from fallback")}])
        audit = []
        client = ModelClient("http://127.0.0.1:11434", "qwen3.6:35b", "gpt-oss:20b", http=http,
                             keep_alive="30m", audit=lambda k, **f: audit.append((k, f)))
        client.chat([{"role": "user", "content": "hi"}])
        self.assertEqual([json.loads(c["body"])["keep_alive"] for c in http.calls], ["30m", "30m"])
        self.assertEqual([f["keep_alive"] for _, f in audit], ["30m", "30m"])

    def test_warm_sends_one_empty_prompt_load_and_audits_model_warm(self):
        http = FakeHttp([{"done": True}, {"models": [{"name": "qwen3.6:35b"}]}])
        audit = []
        client = ModelClient("http://127.0.0.1:11434", "qwen3.6:35b", "gpt-oss:20b", http=http,
                             keep_alive="30m", num_ctx=8192, audit=lambda k, **f: audit.append((k, f)))
        result = client.warm()
        self.assertTrue(result["loaded"])
        self.assertEqual(http.show_calls, [{"model": "qwen3.6:35b"}])
        load, ps = http.calls
        self.assertEqual((load["method"], load["url"]), ("POST", "http://127.0.0.1:11434/api/generate"))
        self.assertEqual(json.loads(load["body"]), {"model": "qwen3.6:35b", "prompt": "", "keep_alive": "30m",
                                                    "options": {"num_ctx": 8192}})
        self.assertEqual((ps["method"], ps["url"]), ("GET", "http://127.0.0.1:11434/api/ps"))
        self.assertEqual([k for k, _ in audit], ["model_warm"])
        rec = audit[0][1]
        self.assertEqual((rec["ok"], rec["loaded"], rec["keep_alive"], rec["host"]),
                         (True, True, "30m", "127.0.0.1:11434"))

    def test_warm_reports_not_loaded(self):
        http = FakeHttp([{"done": True}, {"models": [{"name": "gpt-oss:20b"}]}])
        client, audit = self.audited_client(http)
        self.assertFalse(client.warm()["loaded"])
        self.assertEqual(audit[0][1]["loaded"], False)

    def test_warm_with_ollama_down_is_model_error_with_one_failed_record(self):
        down = EgressError("request to 127.0.0.1 failed: connection refused")
        http = FakeHttp([], show=down)
        client, audit = self.audited_client(http)
        with self.assertRaises(ModelError):
            client.warm()
        self.assertEqual(http.calls, [])
        self.assertEqual([(k, f["ok"]) for k, f in audit], [("model_warm", False)])

    def test_warm_refuses_a_cloud_model(self):
        http = FakeHttp([], show={"remote_host": "https://ollama.com:443", "remote_model": "x"})
        client, audit = self.audited_client(http)
        with self.assertRaises(CloudModelRefused):
            client.warm()
        self.assertEqual(http.calls, [])
        self.assertEqual([k for k, _ in audit], ["model_refused"])

    def test_falls_back_once_on_primary_failure(self):
        http = FakeHttp([EgressError("HTTP 404", status=404, body=b'{"error":"model not found"}'),
                         {"message": answer("from fallback")}])
        client = ModelClient("http://127.0.0.1:11434", "qwen3.6:35b", "gpt-oss:20b", http=http)
        msg, used = client.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(used, "gpt-oss:20b")
        self.assertEqual(json.loads(http.calls[1]["body"])["model"], "gpt-oss:20b")

    def test_malformed_tool_call_error_is_flagged_and_not_retried_on_fallback(self):
        http = FakeHttp([EgressError("HTTP 500", status=500,
                                     body=b'{"error":"error parsing tool call: invalid character"}')])
        client = ModelClient("http://127.0.0.1:11434", "qwen3.6:35b", "gpt-oss:20b", http=http)
        with self.assertRaises(ModelError) as cm:
            client.chat([{"role": "user", "content": "hi"}])
        self.assertTrue(cm.exception.malformed_tool_call)
        self.assertEqual(len(http.calls), 1)


if __name__ == "__main__":
    unittest.main()
