"""status.*: existing read-only bin/chief-of-staff status commands, wrapped.

bin/cos is the public entry point; bin/chief-of-staff is legacy that cos may
wrap. Output is passed through unchanged except for a size cap. --dashboard
(about 100 s) and --approval-queue-status (currently crashes, and its script
deletes a file) are not wrapped.

Each command must pass the static network-free / read-only contract in
script_contract.py at registration. A command that fails is not registered;
the reason is recorded in registry.disabled and shown by `cos tools`.
"""
from __future__ import annotations

import subprocess

from cos.registry import Tool
from cos.tools.script_contract import check_flag

OUTPUT_CAP = 4000
TIMEOUT_S = 20

SCRIPTS = (
    ("status.daily", "--daily-status",
     "Teacher AI Workstation daily status: git branch, roadmap mission, gates, Canvas state.",
     ("status", "daily", "project", "projects", "roadmap", "working on", "repo", "workstation")),
    ("status.next_action", "--next-action",
     "Recommended next action and daily focus from the Teacher AI Workstation roadmap.",
     ("next", "focus", "priority", "priorities", "should i", "work on", "working on", "mission")),
    ("status.local_llm", "--local-llm-workstation-status",
     "Local LLM workstation status report (Ollama setup checks).",
     ("llm", "ollama", "qwen", "local model", "models")),
)


def run_status(ctx, flag: str) -> dict:
    root = ctx.config.repo_root
    try:
        res = ctx.run([str(root / "bin" / "chief-of-staff"), flag], timeout=TIMEOUT_S, cwd=root)
    except subprocess.TimeoutExpired:
        return {"error": f"bin/chief-of-staff {flag} timed out after {TIMEOUT_S}s"}
    output = res.stdout
    truncated = len(output) > OUTPUT_CAP
    return {"command": f"bin/chief-of-staff {flag}", "exit_code": res.returncode,
            "output": output[:OUTPUT_CAP], "truncated": truncated}


def tools(ctx, on_disabled=None):
    out = []
    for name, flag, desc, kws in SCRIPTS:
        violations = check_flag(ctx.config.repo_root, flag)
        if violations:
            if on_disabled is not None:
                on_disabled(name, f"contract violation in bin/chief-of-staff {flag}: "
                                  + "; ".join(violations[:3]))
            continue
        out.append(Tool(
            name=name, description=desc,
            parameters={"type": "object", "properties": {}, "additionalProperties": False},
            side_effect="none", data_class="P1", timeout_s=TIMEOUT_S + 5,
            func=(lambda flag: (lambda args: run_status(ctx, flag)))(flag), keywords=kws,
        ))
    return out
