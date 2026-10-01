"""Answer-quality judge: extension point for E1 Part 2.

Part 1 ships only the interface. run.py calls get_judge(name).evaluate(case,
record) for every turn record and stores the result under record["judge"].
A Part 2 judge returns {"status": "scored", "score": ..., "rationale": ...,
"judge": <name>} (or "error"); deterministic checks never depend on it, and
it must not change any CERT result.
"""
from __future__ import annotations


class Judge:
    name = "none"

    def evaluate(self, case: dict, record: dict) -> dict:
        return {"status": "not_run"}


JUDGES = {"none": Judge}


def get_judge(name: str | None = None) -> Judge:
    return JUDGES[name or "none"]()
