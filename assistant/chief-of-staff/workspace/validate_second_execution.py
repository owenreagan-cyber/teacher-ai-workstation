#!/usr/bin/env python3
"""Synthetic-only Phase L.5G gate validation; never contacts Ollama."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path

from controlled_execution import build_pre_live_gate, finalize_execution
from ollama_runtime import execute_local_explanation


ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


class SyntheticTransport:
    def __init__(self, candidate):
        self.candidate = candidate
        self.post_calls = 0

    def post_json(self, endpoint, route, payload, **kwargs):
        self.post_calls += 1
        return {
            "model": "qwen3.5:35b",
            "message": {"content": json.dumps(self.candidate)},
            "total_duration": 100,
            "load_duration": 20,
            "prompt_eval_count": 50,
            "eval_count": 25,
        }


def available():
    return {
        "status": "available", "failure_code": "none", "message": "available",
        "endpoint": "http://127.0.0.1:11434", "runtime_available": True,
        "model_present": True, "model": "qwen3.5:35b",
    }


def execute(gate, candidate):
    transport = SyntheticTransport(candidate)
    result = execute_local_explanation(
        gate["context"], gate["request"], preflight=available(),
        transport=transport,
        wall_clock=iter(("2026-09-21T18:00:00Z", "2026-09-21T18:00:01Z")).__next__,
        monotonic=iter((1.0, 2.0)).__next__,
    )
    return finalize_execution(result, gate["context"], gate["request"]), transport


def main() -> int:
    gate = build_pre_live_gate()
    accepted, accepted_transport = execute(gate, gate["ideal_response"])
    rejected_candidate = copy.deepcopy(gate["ideal_response"])
    rejected_candidate["evidence_refs"].pop()
    rejected, rejected_transport = execute(gate, rejected_candidate)
    runner_source = (ROOT / "run_second_controlled_ollama_explain.py").read_text(encoding="utf-8")
    checks = [
        Check("PASS" if gate["status"] == "PASS" else "FAIL", "second.gate", "deterministic pre-live gate passes"),
        Check("PASS" if gate["context_summary"]["identity"] == "application-concept:grade-4-writing-launcher" else "FAIL", "second.entity", "fixed Writing Launcher identity is canonicalized"),
        Check("PASS" if gate["context_summary"]["authority"] == "unknown" and gate["context_summary"]["action_authority"] == "none" else "FAIL", "second.authority", "authority remains unknown and non-actionable"),
        Check("PASS" if gate["vocabulary_summary"]["known_ref_count"] == 1 and gate["vocabulary_summary"]["evidence_ref_count"] == 5 and gate["vocabulary_summary"]["uncertainty_ref_count"] == 4 and gate["vocabulary_summary"]["relationship_ref_count"] == 0 else "FAIL", "second.cardinality", "current vocabulary has exact 1/5/4/0 cardinality"),
        Check("PASS" if gate["ideal_validation"]["accepted"] else "FAIL", "second.round_trip", "ideal v2 response validates before runtime"),
        Check("PASS" if accepted["outcome"] == "PASS" and accepted_transport.post_calls == 1 else "FAIL", "second.synthetic_acceptance", "synthetic accepted path uses one attempt"),
        Check("PASS" if accepted["explanation"].startswith("Subject: Grade 4 Writing Launcher") else "FAIL", "second.renderer", "accepted refs render deterministic explanation"),
        Check("PASS" if rejected["outcome"] == "SAFE REJECTION" and rejected_transport.post_calls == 1 else "FAIL", "second.synthetic_rejection", "synthetic rejection stops after one attempt"),
        Check("PASS" if "EVIDENCE_CLAIM_MISSING" in rejected["audit"]["violation_codes"] else "FAIL", "second.diagnostics", "safe rejection exposes finite code only"),
        Check("PASS" if not accepted["audit"]["persisted"] and not rejected["audit"]["persisted"] else "FAIL", "second.audit", "execution audits remain in memory"),
        Check("PASS" if runner_source.count("execute_local_explanation(") == 1 and "while " not in runner_source else "FAIL", "second.one_request", "runner has one execution site and no retry loop"),
        Check("PASS" if "tools" not in gate["ideal_response"] and gate["ideal_response"]["actions"] == [] else "FAIL", "second.security", "v2 result has no tools or actions"),
    ]
    for item in checks:
        print(f"{item.level}: {item.code}: {item.message}")
    totals = {level: sum(item.level == level for item in checks) for level in ("PASS", "WARN", "FAIL")}
    print(f"Summary: PASS={totals['PASS']} WARN={totals['WARN']} FAIL={totals['FAIL']}")
    return 1 if totals["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
