"""Policy gate and kill switch. Deterministic code owns authority.

Rules, in order (any failure, exception, or timeout inside the gate denies):
  1. kill switch set           -> deny everything
  2. tool not registered        -> deny
  3. side_effect is not "none"  -> deny (M1 has no write tools)
  4. arguments fail the schema  -> deny
  otherwise                     -> allow
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cos.config import open_private
from cos.registry import ArgumentError, Registry, validate_args

GATE_TIMEOUT_S = 2.0


@dataclass(frozen=True)
class Decision:
    allowed: bool
    rule: str
    reason: str


class KillSwitch:
    FLAG = "STOP"

    def __init__(self, state_dir: Path):
        self.path = Path(state_dir) / self.FLAG

    def is_set(self) -> bool:
        try:
            return self.path.exists()
        except OSError:
            return True  # cannot tell -> treat as stopped

    def reason(self) -> str:
        try:
            return self.path.read_text(encoding="utf-8").strip()
        except OSError:
            return ""

    def stop(self, reason: str = "") -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open_private(self.path, "w") as fh:
            fh.write(f"stopped {stamp} {reason}".strip() + "\n")

    def resume(self) -> bool:
        try:
            self.path.unlink()
            return True
        except FileNotFoundError:
            return False


class PolicyGate:
    def __init__(self, registry: Registry, kill_switch: KillSwitch, audit=None,
                 timeout_s: float = GATE_TIMEOUT_S):
        self.registry = registry
        self.kill_switch = kill_switch
        self.audit = audit
        self.timeout_s = timeout_s

    def _rules(self, tool_name: str, args) -> Decision:
        if self.kill_switch.is_set():
            return Decision(False, "kill_switch", "kill switch is set (cos resume to clear)")
        tool = self.registry.get(tool_name)
        if tool is None:
            return Decision(False, "unregistered", f"tool {tool_name!r} is not registered")
        if tool.side_effect != "none":
            return Decision(False, "side_effect",
                            f"{tool.name} has side_effect {tool.side_effect!r}; M1 allows none")
        try:
            validate_args(tool, args)
        except ArgumentError as e:
            return Decision(False, "bad_arguments", str(e))
        return Decision(True, "allow", f"{tool.name} is registered and read-only")

    def decide(self, tool_name: str, args, subject: str = "tool_call") -> Decision:
        box: list = []

        def run():
            try:
                box.append(self._rules(tool_name, args))
            except Exception as e:  # noqa: BLE001 - any gate failure denies
                box.append(Decision(False, "gate_error", f"policy gate error: {type(e).__name__}"))

        worker = threading.Thread(target=run, daemon=True)
        worker.start()
        worker.join(self.timeout_s)
        decision = box[0] if box else Decision(False, "gate_timeout", "policy gate timed out")
        if self.audit is not None:
            self.audit("decision", subject=subject, tool=str(tool_name)[:80],
                       allowed=decision.allowed, rule=decision.rule, reason=decision.reason)
        return decision

    def check_model_call(self, phase: str) -> Decision:
        """Authorize a model call. phase is "before_request" or "after_response"; a deny
        after the response means the caller must discard what the model returned."""
        try:
            stopped = self.kill_switch.is_set()
        except Exception:  # noqa: BLE001 - any gate failure denies
            stopped = True
        if stopped:
            decision = Decision(False, "kill_switch", "kill switch is set (cos resume to clear)")
        else:
            decision = Decision(True, "allow", "local model call")
        if self.audit is not None:
            self.audit("decision", subject="model_call", phase=phase, allowed=decision.allowed,
                       rule=decision.rule, reason=decision.reason)
        return decision
