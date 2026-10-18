#!/usr/bin/env python3
"""Run the one separately authorized Phase L.5G local-model request."""

from __future__ import annotations

import json

from controlled_execution import build_pre_live_gate, finalize_execution
from ollama_runtime import execute_local_explanation, load_runtime_policy, preflight_ollama


def main() -> int:
    gate = build_pre_live_gate()
    if gate["status"] != "PASS":
        print(json.dumps({
            "outcome": "PREFLIGHT STOP",
            "deterministic_gate": {"status": "FAIL", "errors": gate["errors"]},
        }, indent=2, sort_keys=True))
        return 2

    policy = load_runtime_policy()
    runtime_preflight = preflight_ollama(policy=policy)
    if runtime_preflight["status"] != "available":
        print(json.dumps({
            "outcome": "PREFLIGHT STOP",
            "deterministic_gate": {"status": "PASS", "errors": []},
            "runtime_preflight": runtime_preflight,
        }, indent=2, sort_keys=True))
        return 2

    result = execute_local_explanation(
        gate["context"],
        gate["request"],
        preflight=runtime_preflight,
        policy=policy,
    )
    final = finalize_execution(result, gate["context"], gate["request"])
    report = {
        "outcome": final["outcome"],
        "deterministic_gate": {"status": "PASS", "errors": []},
        "runtime_preflight": runtime_preflight,
        "context_summary": gate["context_summary"],
        "vocabulary_summary": gate["vocabulary_summary"],
        "execution": final["execution"],
        "explanation": final["explanation"],
        "explanation_provenance": (
            "Rendered from validated deterministic Chief of Staff context. "
            "No model-generated factual prose is trusted."
            if final["outcome"] == "PASS"
            else "No trusted explanation produced."
        ),
        "audit": final["audit"],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if final["outcome"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
