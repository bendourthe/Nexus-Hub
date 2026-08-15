#!/usr/bin/env python3
"""Validate cross-installer capability parity from a declarative manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# A binary belongs here when an installer discovers or invokes it by executable
# name and its absence could otherwise skip capability silently. Shell builtins,
# core filesystem commands, and PowerShell cmdlets are excluded. Adding a newly
# introduced optional executable is deliberately a one-line data change.
EXTERNAL_BINARIES = (
    "apt-get",
    "brew",
    "code",
    "codex",
    "cursor",
    "jq",
    "node",
    "npm",
    "npx",
    "python",
    "python3",
    "rsync",
    "sudo",
    "uv",
    "winget",
)

DEFAULT_MANIFEST = Path("configs/installer-parity.json")


class ParityInputError(Exception):
    """The manifest or an installer could not be read safely."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ParityInputError(f"cannot read manifest {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ParityInputError(f"manifest {path} must contain a JSON object")
    return data


def _compile(pattern: object, label: str) -> re.Pattern[str]:
    if not isinstance(pattern, str) or not pattern:
        raise ParityInputError(f"{label} must be a non-empty regex string")
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise ParityInputError(f"invalid {label}: {exc}") from exc
    if compiled.groups != 1:
        raise ParityInputError(f"{label} must contain exactly one capture group")
    return compiled


def _read_installers(root: Path, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_installers = manifest.get("installers")
    if not isinstance(raw_installers, list) or len(raw_installers) < 2:
        raise ParityInputError("manifest must declare at least two installers")
    installers: dict[str, dict[str, Any]] = {}
    for entry in raw_installers:
        if not isinstance(entry, dict):
            raise ParityInputError("each installer entry must be an object")
        installer_id = entry.get("id")
        rel_path = entry.get("path")
        if not isinstance(installer_id, str) or not installer_id:
            raise ParityInputError("each installer needs a non-empty id")
        if installer_id in installers:
            raise ParityInputError(f"duplicate installer id: {installer_id}")
        if not isinstance(rel_path, str) or not rel_path:
            raise ParityInputError(f"installer {installer_id} needs a path")
        path = root / rel_path
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ParityInputError(f"cannot read installer {path}: {exc}") from exc
        installers[installer_id] = {
            "path": rel_path,
            "text": text,
            "functions": set(_compile(entry.get("function_pattern"), f"{installer_id}.function_pattern").findall(text)),
            "platforms": set(_compile(entry.get("platform_pattern"), f"{installer_id}.platform_pattern").findall(text)),
            "scripts": set(_compile(entry.get("script_reference_pattern"), f"{installer_id}.script_reference_pattern").findall(text)),
        }
    return installers


def _exception_map(raw: object, key: str, installer_ids: set[str], category: str) -> dict[str, set[str]]:
    if raw is None:
        return {}
    if not isinstance(raw, list):
        raise ParityInputError(f"{category} must be a list")
    result: dict[str, set[str]] = {}
    for entry in raw:
        if not isinstance(entry, dict) or not isinstance(entry.get(key), str):
            raise ParityInputError(f"each {category} entry needs {key}")
        reason = entry.get("reason")
        present = entry.get("installers")
        if not isinstance(reason, str) or not reason.strip():
            raise ParityInputError(f"{category} entry {entry[key]} needs a reason")
        if not isinstance(present, list) or not present or not all(isinstance(item, str) for item in present):
            raise ParityInputError(f"{category} entry {entry[key]} needs installers")
        present_set = set(present)
        if not present_set <= installer_ids:
            raise ParityInputError(f"{category} entry {entry[key]} names an unknown installer")
        result[entry[key]] = present_set
    return result


def _check_set_parity(
    installers: dict[str, dict[str, Any]],
    field: str,
    exceptions: dict[str, set[str]],
    category: str,
) -> list[str]:
    findings: list[str] = []
    ids = set(installers)
    values = set().union(*(entry[field] for entry in installers.values()))
    for value in sorted(values | set(exceptions)):
        present = {installer_id for installer_id, entry in installers.items() if value in entry[field]}
        if present == ids:
            if value in exceptions:
                findings.append(f"{category}: stale exception for {value}; it is present in every installer")
            continue
        if exceptions.get(value) != present:
            findings.append(f"{category}: {value} is present in {sorted(present)}, expected all {sorted(ids)} or an exact reasoned exception")
    return findings


def _check_platform_contract(installers: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> list[str]:
    expected = manifest.get("platforms")
    if not isinstance(expected, list) or not all(isinstance(item, str) and item for item in expected):
        raise ParityInputError("platforms must be a list of non-empty strings")
    expected_set = set(expected)
    exceptions = _exception_map(manifest.get("platform_exceptions"), "platform", set(installers), "platform_exceptions")
    findings = _check_set_parity(installers, "platforms", exceptions, "platform")
    observed = set().union(*(entry["platforms"] for entry in installers.values()))
    for missing in sorted(expected_set - observed):
        findings.append(f"platform: manifest key {missing} is not installed anywhere")
    for undeclared in sorted(observed - expected_set - set(exceptions)):
        findings.append(f"platform: installed key {undeclared} is absent from the manifest")
    return findings


def _check_functions(installers: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> list[str]:
    groups = manifest.get("function_groups")
    if not isinstance(groups, list):
        raise ParityInputError("function_groups must be a list")
    covered = {installer_id: set() for installer_id in installers}
    findings: list[str] = []
    for index, group in enumerate(groups, start=1):
        if not isinstance(group, dict) or not isinstance(group.get("reason"), str) or not group["reason"].strip():
            raise ParityInputError(f"function group {index} needs a reason")
        if not any(group.get(installer_id) for installer_id in installers):
            raise ParityInputError(f"function group {index} covers no function")
        for installer_id, installer in installers.items():
            names = group.get(installer_id, [])
            if not isinstance(names, list) or not all(isinstance(name, str) and name for name in names):
                raise ParityInputError(f"function group {index}.{installer_id} must be a string list")
            for name in names:
                if name in covered[installer_id]:
                    findings.append(f"function: {installer_id}.{name} is documented more than once")
                covered[installer_id].add(name)
                if name not in installer["functions"]:
                    findings.append(f"function: manifest counterpart {installer_id}.{name} is not defined")
    for installer_id, installer in installers.items():
        for name in sorted(installer["functions"] - covered[installer_id]):
            findings.append(f"function: {installer_id}.{name} has no documented counterpart or exception")
    return findings


def _check_external_dependencies(installers: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> list[str]:
    raw = manifest.get("external_dependencies")
    if not isinstance(raw, list):
        raise ParityInputError("external_dependencies must be a list")
    records: dict[str, dict[str, Any]] = {}
    for entry in raw:
        if not isinstance(entry, dict) or entry.get("binary") not in EXTERNAL_BINARIES:
            raise ParityInputError("each external dependency must name a binary from EXTERNAL_BINARIES")
        binary = entry["binary"]
        if binary in records:
            raise ParityInputError(f"duplicate external dependency: {binary}")
        records[binary] = entry

    findings: list[str] = []
    for binary in EXTERNAL_BINARIES:
        for installer_id, installer in installers.items():
            code = "\n".join(
                line for line in installer["text"].splitlines()
                if not line.lstrip().startswith("#")
            )
            executable_use = re.compile(
                rf"(?im)(?:command\s+-v\s+[\"']?|Get-Command\s+[\"']|^\s*|[;&|]\s*|!\s+|&\s+)"
                rf"{re.escape(binary)}(?:[\"']|\s|$)"
            )
            if not executable_use.search(code):
                continue
            record = records.get(binary)
            installer_record = record.get("installers", {}).get(installer_id) if record else None
            if not isinstance(installer_record, dict):
                findings.append(f"external-dependency: {installer_id} references {binary} without a documented fallback")
                continue
            reason = installer_record.get("reason")
            markers = installer_record.get("fallback_markers")
            if not isinstance(reason, str) or not reason.strip() or not isinstance(markers, list) or not markers:
                findings.append(f"external-dependency: {installer_id}.{binary} needs a reason and fallback markers")
                continue
            if not any(isinstance(marker, str) and marker in installer["text"] for marker in markers):
                findings.append(f"external-dependency: {installer_id}.{binary} fallback marker is missing from the installer")
    return findings


def validate(root: Path, manifest_path: Path) -> list[str]:
    manifest = _load_json(manifest_path)
    installers = _read_installers(root, manifest)
    script_exceptions = _exception_map(
        manifest.get("script_artifact_exceptions"),
        "artifact",
        set(installers),
        "script_artifact_exceptions",
    )
    findings = _check_set_parity(installers, "scripts", script_exceptions, "script-artifact")
    findings.extend(_check_platform_contract(installers, manifest))
    findings.extend(_check_functions(installers, manifest))
    findings.extend(_check_external_dependencies(installers, manifest))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else root / DEFAULT_MANIFEST
    try:
        findings = validate(root, manifest_path)
    except ParityInputError as exc:
        print(f"installer parity input error: {exc}", file=sys.stderr)
        return 2
    if findings:
        for finding in findings:
            print(f"installer parity: FAIL: {finding}", file=sys.stderr)
        return 1
    print("installer parity: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
