"""Shared test helpers: temp state dirs, fake clock/runner/http/model. Synthetic data only."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Display times are rendered in local time; pin it so tests are deterministic anywhere.
os.environ["TZ"] = "America/New_York"
time.tzset()

from cos.config import Config, REPO_ROOT as COS_REPO_ROOT  # noqa: E402
from cos.tools import CmdResult, ToolContext  # noqa: E402
import cos.tools.calendar as _calendar  # noqa: E402
import subprocess as _subprocess  # noqa: E402

# Safety: tests must never reach the real EventKit helper app or launch apps.
# A built helper at the default path would otherwise be launched by any test
# that uses real tools, and EventKit could show a permission prompt.
_calendar.DEFAULT_APP = Path("/nonexistent/cos-tests/ChiefOfStaffEventKitReader.app")
_real_subprocess_run = _subprocess.run


def _guarded_run(argv, *args, **kwargs):
    first = argv[0] if isinstance(argv, (list, tuple)) and argv else argv
    if str(first) in ("/usr/bin/open", "open") or "eventkit-reader" in str(first):
        raise AssertionError(f"tests must not launch apps or the EventKit helper: {argv!r}")
    return _real_subprocess_run(argv, *args, **kwargs)


_subprocess.run = _guarded_run

FIXTURES = Path(__file__).resolve().parent / "fixtures"
EDT = timezone(timedelta(hours=-4), "EDT")
FIXED_NOW = datetime(2026, 10, 1, 7, 30, tzinfo=EDT)  # a Thursday


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class StateDirTest(unittest.TestCase):
    """Gives every test its own COS_STATE_DIR temp directory."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="cos-test-")
        self.state = Path(self._tmp.name) / "ChiefOfStaff"
        self._old_env = os.environ.get("COS_STATE_DIR")
        os.environ["COS_STATE_DIR"] = str(self.state)

    def tearDown(self):
        if self._old_env is None:
            os.environ.pop("COS_STATE_DIR", None)
        else:
            os.environ["COS_STATE_DIR"] = self._old_env
        self._tmp.cleanup()

    def config(self, **overrides) -> Config:
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        base = dict(model="qwen3.6:35b", fallback_model="gpt-oss:20b",
                    ollama_url="http://127.0.0.1:11434", model_timeout_s=5,
                    latitude=None, longitude=None, state_dir=self.state, repo_root=COS_REPO_ROOT)
        base.update(overrides)
        return Config(**base)


class FakeRunner:
    """Maps argv tails to CmdResult; records calls; fails on anything unexpected."""

    def __init__(self, table: dict):
        self.table = table
        self.calls = []

    def __call__(self, argv, timeout, cwd=None):
        self.calls.append((list(argv), timeout, cwd))
        key = tuple(argv[-3:]) if tuple(argv[-3:]) in self.table else argv[-1]
        if key in self.table:
            value = self.table[key]
            if isinstance(value, Exception):
                raise value
            return value if isinstance(value, CmdResult) else CmdResult(0, value)
        raise AssertionError(f"unexpected command {argv}")


class FakeOpenRunner:
    """Stands in for `/usr/bin/open ... --stdout F App.app --args ...`: writes the scripted
    helper output for the given helper argv into F. Never launches anything."""

    def __init__(self, table: dict):
        self.table = table
        self.calls = []

    def __call__(self, argv, timeout, cwd=None):
        self.calls.append(list(argv))
        assert argv[0] == "/usr/bin/open", argv
        helper_args = tuple(argv[argv.index("--args") + 1:])
        out = Path(argv[argv.index("--stdout") + 1])
        value = self.table[helper_args]
        if isinstance(value, Exception):
            raise value
        out.write_text(value if value.endswith("\n") else value + "\n", encoding="utf-8")
        return CmdResult(0, "")


def fake_helper_app(root: Path) -> Path:
    app = root / "ChiefOfStaffEventKitReader.app"
    exe = app / "Contents" / "MacOS" / "eventkit-reader"
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_text("#!/bin/sh\nexit 99\n")  # never executed: the runner is faked
    return app


LOCAL_SHOW = {"details": {"format": "gguf", "family": "qwen35moe", "parameter_size": "35.5B",
                          "quantization_level": "Q4_K_M"}, "capabilities": ["completion", "tools"]}


class FakeHttp:
    """Scripted responses in order. Ollama's /api/show (the client's local-model check) is
    answered from `show` (default: a local model) and recorded in show_calls, not calls."""

    def __init__(self, responses=None, show=LOCAL_SHOW):
        self.responses = list(responses or [])
        self.calls = []
        self.show = show
        self.show_calls = []

    def __call__(self, method, url, body=None, headers=None, timeout=30, audit=None):
        if url.endswith("/api/show"):
            self.show_calls.append(json.loads(body))
            if isinstance(self.show, Exception):
                raise self.show
            return json.dumps(self.show).encode()
        self.calls.append({"method": method, "url": url, "body": body, "headers": headers})
        if not self.responses:
            raise AssertionError(f"unexpected http call {url}")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item if isinstance(item, bytes) else json.dumps(item).encode()


class FakeModel:
    """Returns scripted messages (dicts) or raises scripted exceptions."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def chat(self, messages, tools=None, fmt=None):
        self.calls.append({"messages": [dict(m) for m in messages], "tools": tools})
        if not self.script:
            raise AssertionError("model called more times than scripted")
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item, "fake-model"


def make_ctx(config, run=None, http=None, clock=FIXED_NOW, **kw) -> ToolContext:
    return ToolContext(config=config, clock=lambda: clock, run=run or FakeRunner({}),
                       http=http or FakeHttp(), **kw)


def tool_call(name, arguments):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"function": {"name": name, "arguments": arguments}}]}


def answer(text):
    return {"role": "assistant", "content": text}
