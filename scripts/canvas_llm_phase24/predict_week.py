from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase24.correction_memory import load_correction_state  # noqa: E402
from scripts.canvas_llm_phase24.rule_engine import predict_week_data, validate_week_prediction  # noqa: E402

DEFAULT_INPUT = REPO_ROOT / "fixtures/canvas-llm/phase-24/predictive-teacher-brain.json"
DEFAULT_OUTPUT = REPO_ROOT / "apps/predictive-teacher-brain/data/phase24-demo.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def build_prediction(week_code: str, input_path: Path) -> dict:
    correction_state = load_correction_state(week_code)
    prediction = predict_week_data(week_code, input_path, correction_state).to_dict()
    validation, _ = validate_week_prediction(prediction)
    prediction["validation"] = validation
    return prediction


def command_build(args: argparse.Namespace) -> int:
    input_path = Path(args.input or DEFAULT_INPUT)
    output_path = Path(args.output or DEFAULT_OUTPUT)
    payload = build_prediction(args.week, input_path)
    write_json(output_path, payload)
    print(f"Phase 24 predicted week rebuilt: {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 24 predictive teacher brain")
    parser.add_argument("--week", default="Q1W5")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.set_defaults(func=command_build)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
