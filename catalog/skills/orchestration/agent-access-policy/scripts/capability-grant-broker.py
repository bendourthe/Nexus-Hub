#!/usr/bin/env python3
"""Deny-by-default capability authorization for agent actions.

Authorization is pure and side-effect-free. Execution is a separate, explicit
operation that requires a reachable sandbox command prefix and never invokes a
shell string.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

EXIT_AUTHORIZED = 0
EXIT_USAGE_ERROR = 2
EXIT_DENIED = 3
EXIT_EXECUTION_ERROR = 4


class Capability(str, Enum):
    """Dangerous effects an action may require."""

    NETWORK = "network"
    WRITE = "write"
    USE_SECRET = "use_secret"
    DESTRUCTIVE_TEST = "destructive_test"


class RequestError(ValueError):
    """Raised when request data is malformed rather than unauthorized."""


@dataclass(frozen=True)
class Grant:
    """Validated grant data supplied by an authorization boundary."""

    authorization_source: str | None
    capabilities: frozenset[Capability]
    writable_paths: tuple[str, ...]
    network_destinations: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionPlan:
    """Least-privilege plan containing only resources this action requests."""

    command: tuple[str, ...]
    capabilities: tuple[str, ...]
    writable_paths: tuple[str, ...]
    network_destinations: tuple[str, ...]
    authorization_source: str
    mode: str = "plan-only"
    sandbox_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        payload = asdict(self)
        payload["command"] = list(self.command)
        payload["capabilities"] = list(self.capabilities)
        payload["writable_paths"] = list(self.writable_paths)
        payload["network_destinations"] = list(self.network_destinations)
        return payload


@dataclass(frozen=True)
class Decision:
    """Authorization result with machine-branchable status and reasons."""

    authorized: bool
    reasons: tuple[str, ...]
    plan: ExecutionPlan | None = None

    @property
    def exit_code(self) -> int:
        """Return the broker exit code for this decision."""

        return EXIT_AUTHORIZED if self.authorized else EXIT_DENIED

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            "status": "authorized" if self.authorized else "denied",
            "reasons": list(self.reasons),
            "plan": self.plan.to_dict() if self.plan else None,
        }


_REQUEST_KEYS = {
    "command",
    "required_capabilities",
    "requested_write_paths",
    "requested_network_destinations",
    "grant",
}
_GRANT_KEYS = {
    "authorization_source",
    "capabilities",
    "writable_paths",
    "network_destinations",
}


def _string_list(value: Any, field: str, *, non_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise RequestError(f"{field} must be a list of strings")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise RequestError(f"{field} must contain only non-empty strings")
        result.append(item.strip())
    if non_empty and not result:
        raise RequestError(f"{field} must not be empty")
    if len(result) != len(set(result)):
        raise RequestError(f"{field} must not contain duplicates")
    return tuple(result)


def _string_sequence(
    value: Any, field: str, *, non_empty: bool = False
) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise RequestError(f"{field} must be a list of strings")
    return _string_list(list(value), field, non_empty=non_empty)


def _capability_set(value: Any, field: str) -> frozenset[Capability]:
    names = _string_list(value, field)
    parsed: set[Capability] = set()
    for name in names:
        try:
            parsed.add(Capability(name))
        except ValueError as exc:
            allowed = ", ".join(capability.value for capability in Capability)
            raise RequestError(
                f"{field} contains unknown capability {name!r}; allowed: {allowed}"
            ) from exc
    return frozenset(parsed)


def _absolute_path(value: str, field: str) -> str:
    if "\x00" in value:
        raise RequestError(f"{field} contains a null byte")
    normalized = os.path.normcase(os.path.normpath(value))
    if not os.path.isabs(normalized):
        raise RequestError(f"{field} entries must be absolute paths")
    return normalized


def _normalize_paths(values: Iterable[str], field: str) -> tuple[str, ...]:
    return tuple(_absolute_path(value, field) for value in values)


def _normalize_destinations(values: Iterable[str], field: str) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        destination = value.strip().lower()
        if not destination or any(character.isspace() for character in destination):
            raise RequestError(f"{field} contains an invalid destination")
        normalized.append(destination)
    return tuple(normalized)


def _under_scope(path: str, scope: str) -> bool:
    try:
        return os.path.commonpath((path, scope)) == scope
    except ValueError:
        return False


def parse_grant(value: Any) -> Grant:
    """Validate a grant object without deciding whether it authorizes an action."""

    if not isinstance(value, Mapping):
        raise RequestError("grant must be an object")
    unknown = set(value) - _GRANT_KEYS
    if unknown:
        raise RequestError(
            f"grant contains unknown fields: {', '.join(sorted(unknown))}"
        )
    if "capabilities" not in value:
        raise RequestError("grant.capabilities is required")

    source_value = value.get("authorization_source")
    if source_value is not None and not isinstance(source_value, str):
        raise RequestError("grant.authorization_source must be a string")
    source = source_value.strip() if isinstance(source_value, str) else None
    source = source or None

    writable = _string_list(value.get("writable_paths", []), "grant.writable_paths")
    destinations = _string_list(
        value.get("network_destinations", []), "grant.network_destinations"
    )
    return Grant(
        authorization_source=source,
        capabilities=_capability_set(value["capabilities"], "grant.capabilities"),
        writable_paths=_normalize_paths(writable, "grant.writable_paths"),
        network_destinations=_normalize_destinations(
            destinations, "grant.network_destinations"
        ),
    )


def authorize(
    command: Any,
    required_capabilities: Any,
    grant: Grant | Mapping[str, Any],
    *,
    requested_write_paths: Any = None,
    requested_network_destinations: Any = None,
) -> Decision:
    """Return a least-privilege plan or an explicit denial.

    Documentation that asks for an action is not authorization. In particular,
    a model-written approval line is not a security boundary; the caller must
    supply a grant whose authorization source comes from its trusted boundary.
    """

    command_tuple = _string_list(command, "command", non_empty=True)
    required = _capability_set(required_capabilities, "required_capabilities")
    parsed_grant = grant if isinstance(grant, Grant) else parse_grant(grant)
    write_paths = _normalize_paths(
        _string_list(
            [] if requested_write_paths is None else requested_write_paths,
            "requested_write_paths",
        ),
        "requested_write_paths",
    )
    destinations = _normalize_destinations(
        _string_list(
            []
            if requested_network_destinations is None
            else requested_network_destinations,
            "requested_network_destinations",
        ),
        "requested_network_destinations",
    )

    reasons: list[str] = []
    if parsed_grant.authorization_source is None:
        reasons.append("grant has no authorization source")

    missing = sorted(
        capability.value for capability in required - parsed_grant.capabilities
    )
    if missing:
        reasons.append(f"ungranted capabilities: {', '.join(missing)}")

    if write_paths and Capability.WRITE not in required:
        reasons.append(
            "requested write paths were not declared with the write capability"
        )
    if Capability.WRITE in required:
        if not write_paths:
            reasons.append(
                "write capability requires at least one requested write path"
            )
        if not parsed_grant.writable_paths:
            reasons.append("write capability has no writable path scope")
        for path in write_paths:
            if not any(
                _under_scope(path, scope) for scope in parsed_grant.writable_paths
            ):
                reasons.append(f"write path is outside the grant scope: {path}")

    if destinations and Capability.NETWORK not in required:
        reasons.append(
            "requested network destinations were not declared with the network capability"
        )
    if Capability.NETWORK in required:
        if not destinations:
            reasons.append(
                "network capability requires at least one requested destination"
            )
        if not parsed_grant.network_destinations:
            reasons.append("network capability has no destination allowlist")
        allowed_destinations = set(parsed_grant.network_destinations)
        for destination in destinations:
            if destination not in allowed_destinations:
                reasons.append(
                    f"network destination is outside the grant allowlist: {destination}"
                )

    if reasons:
        return Decision(authorized=False, reasons=tuple(reasons))

    plan = ExecutionPlan(
        command=command_tuple,
        capabilities=tuple(sorted(capability.value for capability in required)),
        writable_paths=write_paths,
        network_destinations=destinations,
        authorization_source=parsed_grant.authorization_source,
    )
    return Decision(
        authorized=True,
        reasons=("all required capabilities and scopes are authorized",),
        plan=plan,
    )


def authorize_request(value: Any) -> Decision:
    """Validate and authorize the JSON request shape used by the CLI."""

    if not isinstance(value, Mapping):
        raise RequestError("request must be an object")
    unknown = set(value) - _REQUEST_KEYS
    if unknown:
        raise RequestError(
            f"request contains unknown fields: {', '.join(sorted(unknown))}"
        )
    missing = {"command", "required_capabilities", "grant"} - set(value)
    if missing:
        raise RequestError(f"request is missing fields: {', '.join(sorted(missing))}")
    return authorize(
        value["command"],
        value["required_capabilities"],
        value["grant"],
        requested_write_paths=value.get("requested_write_paths", []),
        requested_network_destinations=value.get("requested_network_destinations", []),
    )


def execute_in_sandbox(
    plan: ExecutionPlan, sandbox_prefix: Sequence[str] | None
) -> tuple[int, dict[str, Any]]:
    """Execute an authorized plan through a reachable list-based sandbox prefix."""

    if sandbox_prefix is None:
        return EXIT_DENIED, {
            "status": "denied",
            "reasons": ["execution requested but no sandbox was supplied"],
            "plan": plan.to_dict(),
        }
    prefix = _string_sequence(sandbox_prefix, "sandbox_prefix", non_empty=True)
    executable = prefix[0]
    reachable = (
        Path(executable).is_file()
        if os.path.isabs(executable)
        else shutil.which(executable)
    )
    if not reachable:
        return EXIT_DENIED, {
            "status": "denied",
            "reasons": [
                f"execution requested but sandbox is not reachable: {executable}"
            ],
            "plan": plan.to_dict(),
        }

    completed = subprocess.run([*prefix, *plan.command], shell=False, check=False)
    payload = {
        "status": "executed" if completed.returncode == 0 else "execution-error",
        "reasons": [],
        "plan": plan.to_dict(),
        "child_exit_code": completed.returncode,
    }
    exit_code = EXIT_AUTHORIZED if completed.returncode == 0 else EXIT_EXECUTION_ERROR
    return exit_code, payload


def _load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _sandbox_prefix(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RequestError(f"sandbox prefix is not valid JSON: {exc.msg}") from exc
    return _string_list(decoded, "sandbox_prefix", non_empty=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Authorize a typed agent action; plan-only unless --execute is supplied."
    )
    parser.add_argument(
        "--request",
        required=True,
        help="JSON request path, or - for stdin",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute only through the reachable --sandbox-prefix-json command",
    )
    parser.add_argument(
        "--sandbox-prefix-json",
        help='JSON argv prefix for the sandbox, for example ["sandbox-runner","--"]',
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point with distinct authorized, denied, and data-error exits."""

    args = _parser().parse_args(argv)
    try:
        request = _load_json(args.request)
        decision = authorize_request(request)
        if args.sandbox_prefix_json and not args.execute:
            raise RequestError("--sandbox-prefix-json requires --execute")
        if not decision.authorized:
            print(json.dumps(decision.to_dict(), indent=2, sort_keys=True))
            return EXIT_DENIED
        if args.execute:
            assert decision.plan is not None
            exit_code, payload = execute_in_sandbox(
                decision.plan, _sandbox_prefix(args.sandbox_prefix_json)
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
            return exit_code
        print(json.dumps(decision.to_dict(), indent=2, sort_keys=True))
        return EXIT_AUTHORIZED
    except (OSError, json.JSONDecodeError, RequestError) as exc:
        print(
            json.dumps(
                {"status": "usage-error", "reasons": [str(exc)], "plan": None},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
