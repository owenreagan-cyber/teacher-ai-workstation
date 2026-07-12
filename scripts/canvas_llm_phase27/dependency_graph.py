from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class DependencyGraphError(ValueError):
    pass


@dataclass
class DependencyGraphResult:
    order: list[str]
    cycles: list[list[str]]
    blocked: set[str]
    missing: list[tuple[str, str]]
    duplicates: list[tuple[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "order": self.order,
            "cycles": self.cycles,
            "blocked": sorted(self.blocked),
            "missing": [{"from": f, "to": t} for f, t in self.missing],
            "duplicates": [{"from": f, "to": t} for f, t in self.duplicates],
        }


def build_dependency_graph(
    object_ids: list[str],
    edges: list[tuple[str, str]],
    initially_blocked: set[str] | None = None,
) -> DependencyGraphResult:
    """Build a dependency graph over `object_ids` with directed edges
    (dependent -> dependency, i.e. "dependent depends on dependency").

    - Detects duplicate edges.
    - Detects edges referencing objects not in `object_ids` ("missing").
    - Detects cycles (returned, never included in the topological order).
    - Computes a deterministic topological order for the acyclic subset.
    - Propagates "blocked" status: anything depending (transitively) on a
      blocked object, a missing dependency, or a cycle member is blocked.
    """
    known = set(object_ids)
    seen_edges: set[tuple[str, str]] = set()
    duplicates: list[tuple[str, str]] = []
    missing: list[tuple[str, str]] = []
    clean_edges: list[tuple[str, str]] = []

    for dependent, dependency in edges:
        if (dependent, dependency) in seen_edges:
            duplicates.append((dependent, dependency))
            continue
        seen_edges.add((dependent, dependency))
        if dependent not in known or dependency not in known:
            missing.append((dependent, dependency))
            continue
        clean_edges.append((dependent, dependency))

    # adjacency: dependency -> [dependents that require it]
    dependents_of: dict[str, list[str]] = {oid: [] for oid in object_ids}
    depends_on: dict[str, list[str]] = {oid: [] for oid in object_ids}
    for dependent, dependency in clean_edges:
        dependents_of[dependency].append(dependent)
        depends_on[dependent].append(dependency)

    # Tarjan-style cycle detection via DFS coloring.
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {oid: WHITE for oid in object_ids}
    cycles: list[list[str]] = []
    cycle_members: set[str] = set()

    def visit(node: str, stack: list[str]) -> None:
        color[node] = GRAY
        stack.append(node)
        for dep in sorted(depends_on[node]):
            if color[dep] == WHITE:
                visit(dep, stack)
            elif color[dep] == GRAY:
                idx = stack.index(dep)
                cycle = stack[idx:] + [dep]
                cycles.append(cycle)
                cycle_members.update(cycle)
        stack.pop()
        color[node] = BLACK

    for oid in sorted(object_ids):
        if color[oid] == WHITE:
            visit(oid, [])

    # Topological order (Kahn's algorithm) over the acyclic subset only.
    acyclic = [oid for oid in object_ids if oid not in cycle_members]
    acyclic_set = set(acyclic)
    in_degree = {
        oid: len([d for d in depends_on[oid] if d in acyclic_set]) for oid in acyclic
    }
    ready = sorted([oid for oid in acyclic if in_degree[oid] == 0])
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for dependent in sorted(dependents_of.get(node, [])):
            if dependent not in acyclic_set:
                continue
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                ready.append(dependent)
                ready.sort()

    # Blocked propagation: seed set, missing-dependency dependents, cycle
    # members, then transitive closure over "depends on a blocked node".
    blocked: set[str] = set(initially_blocked or set())
    blocked.update(cycle_members)
    for dependent, _dependency in missing:
        blocked.add(dependent)

    changed = True
    while changed:
        changed = False
        for oid in object_ids:
            if oid in blocked:
                continue
            if any(dep in blocked for dep in depends_on[oid]):
                blocked.add(oid)
                changed = True

    return DependencyGraphResult(
        order=order, cycles=cycles, blocked=blocked, missing=missing, duplicates=duplicates
    )
