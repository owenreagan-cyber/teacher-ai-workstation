"""Tool registry: declarations, argument validation, and the model-facing schema.

Every tool declares name, description, parameters (a small JSON-schema
subset), side_effect, data_class, timeout_s, and router keywords. A tool marked
fast_path_only is never offered to the model, and the policy gate denies it to
any caller except the deterministic fast path. Canonical
names use dots (time.now); the wire name sent to the model uses underscores
(time_now) because many models are trained on that format.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

SIDE_EFFECTS = frozenset({"none", "local_write", "external_write"})
DATA_CLASSES = frozenset({"P0", "P1", "P2"})
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
JSON_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool}


class RegistryError(Exception):
    pass


class ArgumentError(Exception):
    pass


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict
    side_effect: str
    data_class: str
    timeout_s: float
    func: Callable[[dict], dict]
    keywords: tuple[str, ...] = field(default=())
    fast_path_only: bool = False

    @property
    def wire_name(self) -> str:
        return self.name.replace(".", "_")


def _check_schema(schema: dict, where: str) -> None:
    if not isinstance(schema, dict) or schema.get("type") != "object":
        raise RegistryError(f"{where}: parameters must be a JSON object schema")
    props = schema.get("properties", {})
    if not isinstance(props, dict):
        raise RegistryError(f"{where}: properties must be an object")
    for key, spec in props.items():
        if not isinstance(spec, dict) or spec.get("type") not in JSON_TYPES:
            raise RegistryError(f"{where}: property {key!r} needs a simple type")
    for key in schema.get("required", []):
        if key not in props:
            raise RegistryError(f"{where}: required {key!r} not in properties")
    if schema.get("additionalProperties", False) is not False:
        raise RegistryError(f"{where}: additionalProperties must be false")


def validate_args(tool: Tool, args) -> dict:
    if not isinstance(args, dict):
        raise ArgumentError("arguments must be a JSON object")
    props = tool.parameters.get("properties", {})
    extra = set(args) - set(props)
    if extra:
        raise ArgumentError(f"unexpected arguments: {sorted(extra)}")
    for key in tool.parameters.get("required", []):
        if key not in args:
            raise ArgumentError(f"missing required argument {key!r}")
    for key, value in args.items():
        spec = props[key]
        want = JSON_TYPES[spec["type"]]
        if isinstance(value, bool) and spec["type"] != "boolean":
            raise ArgumentError(f"argument {key!r} must be {spec['type']}")
        if not isinstance(value, want):
            raise ArgumentError(f"argument {key!r} must be {spec['type']}")
        if "enum" in spec and value not in spec["enum"]:
            raise ArgumentError(f"argument {key!r} must be one of {spec['enum']}")
        if spec["type"] == "string" and len(value) > spec.get("maxLength", 200):
            raise ArgumentError(f"argument {key!r} too long")
        for bound, ok in (("minimum", lambda a, b: a >= b), ("maximum", lambda a, b: a <= b)):
            if bound in spec and not ok(value, spec[bound]):
                raise ArgumentError(f"argument {key!r} violates {bound} {spec[bound]}")
    return args


class Registry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self.disabled: dict[str, str] = {}  # tool name -> why it was refused registration

    def disable(self, name: str, reason: str) -> None:
        self.disabled[name] = reason

    def register(self, tool: Tool) -> Tool:
        if not NAME_RE.match(tool.name):
            raise RegistryError(f"bad tool name {tool.name!r}")
        if tool.name in self._tools:
            raise RegistryError(f"duplicate tool {tool.name!r}")
        if any(t.wire_name == tool.wire_name for t in self._tools.values()):
            raise RegistryError(f"wire name collision for {tool.name!r}")
        if tool.side_effect not in SIDE_EFFECTS:
            raise RegistryError(f"{tool.name}: unknown side_effect {tool.side_effect!r}")
        if tool.data_class not in DATA_CLASSES:
            raise RegistryError(f"{tool.name}: unknown data_class {tool.data_class!r}")
        if not (isinstance(tool.timeout_s, (int, float)) and 0 < tool.timeout_s <= 120):
            raise RegistryError(f"{tool.name}: timeout_s must be in (0, 120]")
        if not tool.description.strip():
            raise RegistryError(f"{tool.name}: description required")
        _check_schema(tool.parameters, tool.name)
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Tool | None:
        """Look up by canonical or wire name."""
        if name in self._tools:
            return self._tools[name]
        for tool in self._tools.values():
            if tool.wire_name == name:
                return tool
        return None

    def all(self) -> list[Tool]:
        return [self._tools[k] for k in sorted(self._tools)]

    @staticmethod
    def model_schema(tool: Tool) -> dict:
        return {"type": "function", "function": {
            "name": tool.wire_name,
            "description": tool.description,
            "parameters": tool.parameters,
        }}
