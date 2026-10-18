"""Run the real cos CLI with the scripted fake model (harness test double).

Usage (the harness builds this): python3.12 -s -E -P fake_cos.py <cos args...>

Only the model client's HTTP layer is replaced: ModelClient._post answers
/api/chat from fake_model.reply() and /api/show from fake_model.show(), and
loaded_models() returns the fake name.
Everything else is the real cos: config and fixture-mode checks, fast path,
router, policy gate, executor, audit (model_call records are still written by
the real client, with the real local host), sessions, and the kill switch.

Refuses to run unless COS_FIXTURE_DIR is set; cos itself then refuses fixture
mode unless COS_STATE_DIR is a temporary, non-real state directory.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
REPO_ROOT = HARNESS.parents[1]


def main(argv: list[str]) -> int:
    if not os.environ.get("COS_FIXTURE_DIR"):
        print("fake_cos: refused: the fake model runs only in fixture mode (COS_FIXTURE_DIR)",
              file=sys.stderr)
        return 2
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(1, str(HARNESS))
    import fake_model
    from cos import cli, model

    def fake_post(self, path, payload):
        if path == "/api/show":  # the client's local-model check
            return fake_model.show(payload)
        if path != "/api/chat":
            raise model.ModelError(f"fake model: unexpected path {path}")
        return {"model": payload.get("model"), "message": fake_model.reply(payload), "done": True}

    model.ModelClient._post = fake_post
    model.ModelClient.loaded_models = lambda self, timeout_s=3: [fake_model.MODEL_NAME]
    return cli.main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
