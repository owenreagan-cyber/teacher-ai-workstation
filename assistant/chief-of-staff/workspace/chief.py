#!/usr/bin/env python3
"""Phase K human CLI for the deterministic Phase J intelligence layer."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

from human_interface import (
    InterfaceValidationError,
    REVIEW_STATES,
    build_interface_status,
    build_review_queue,
    load_interface_policy,
    render_evidence,
    render_explanation,
    render_recovery,
    render_relationships,
    render_review_queue,
    render_status,
)

from query_layer import (
    DeterministicQueryLayer,
    QuerySecurityError,
    QueryValidationError,
    SCOPES,
    make_query,
)


def _add_scope(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--scope", choices=sorted(SCOPES), default="all")
    parser.add_argument(
        "--allow-restricted",
        action="store_true",
        help="provide the explicit workspace.restricted.read grant",
    )
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")


def _add_filters(parser: argparse.ArgumentParser, *, relationships: bool = False) -> None:
    parser.add_argument("--confidence", choices=("high", "medium", "low", "unknown"))
    parser.add_argument("--review-state", choices=sorted(REVIEW_STATES))
    if relationships:
        parser.add_argument(
            "--relationship-type",
            choices=(
                "belongs_to_project", "representation_of", "used_by_application",
                "deployed_to", "mirrored_to", "backed_up_by", "version_of",
                "supersedes", "referenced_by_registry", "expected_artifact_of",
            ),
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chief",
        description="Deterministic read-only Chief of Staff query and explanation layer",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    explain_parser = subparsers.add_parser("explain", help="explain what an entity is and why it is known")
    explain_parser.add_argument("entity")
    _add_scope(explain_parser)

    related_parser = subparsers.add_parser("related", help="show deterministic relationships")
    related_parser.add_argument("entity")
    _add_scope(related_parser)
    _add_filters(related_parser, relationships=True)

    evidence_parser = subparsers.add_parser("evidence", help="show supporting evidence and provenance")
    evidence_parser.add_argument("entity")
    _add_scope(evidence_parser)
    _add_filters(evidence_parser)

    uncertain_parser = subparsers.add_parser("uncertain", help="surface unresolved items without treating them as failures")
    _add_scope(uncertain_parser)
    uncertain_parser.add_argument("--review-state", choices=sorted(REVIEW_STATES))

    recovery_parser = subparsers.add_parser("recovery", help="explain recovery candidates without executing recovery")
    recovery_parser.add_argument("entity")
    _add_scope(recovery_parser)

    status_parser = subparsers.add_parser("status", help="show fixed-input query-layer status")
    status_parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser


def _permissions(args: argparse.Namespace) -> list[str]:
    return ["workspace.restricted.read"] if getattr(args, "allow_restricted", False) else []


def _filters(args: argparse.Namespace) -> dict[str, str]:
    return {
        key: value
        for key in ("relationship_type", "confidence", "review_state")
        if (value := getattr(args, key, None)) is not None
    }


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(
    argv: Sequence[str] | None = None,
    *,
    layer: DeterministicQueryLayer | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        load_interface_policy()
        active_layer = layer or DeterministicQueryLayer()
        permissions = _permissions(args)
        if args.command == "status":
            result: Any = build_interface_status(active_layer)
            if args.json:
                _print_json(result)
            else:
                print(render_status(result))
            return 0
        if args.command == "explain":
            result = active_layer.explain(
                args.entity, scope=args.scope, permission_grants=permissions
            )
            if args.json:
                _print_json(result)
            else:
                evidence = active_layer.why(
                    args.entity, scope=args.scope, permission_grants=permissions
                )
                relationships = active_layer.related_to(
                    args.entity, scope=args.scope, permission_grants=permissions
                )
                print(render_explanation(result, evidence, relationships))
            return 0
        if args.command == "uncertain":
            result = build_review_queue(
                active_layer,
                scope=args.scope,
                permission_grants=permissions,
                review_state=args.review_state,
            )
            _print_json(result) if args.json else print(render_review_queue(result))
            return 0

        query_types = {
            "related": "relationship_lookup",
            "evidence": "evidence_lookup",
            "recovery": "recovery_candidate_lookup",
        }
        query = make_query(
            query_types[args.command],
            args.entity,
            scope=args.scope,
            filters=_filters(args),
            permission_grants=permissions,
            query_id=f"query:cli:{args.command}",
        )
        response = active_layer.execute(query)
        if args.json:
            _print_json(response)
        else:
            renderers = {
                "related": render_relationships,
                "evidence": render_evidence,
                "recovery": render_recovery,
            }
            print(renderers[args.command](
                args.entity, response["results"], response["uncertainties"]
            ))
        return 0
    except (
        OSError, KeyError, TypeError, ValueError, QuerySecurityError,
        QueryValidationError, InterfaceValidationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
