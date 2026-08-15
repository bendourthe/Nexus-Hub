#!/usr/bin/env python3
"""Assert identical postconditions after a real cross-platform installer run."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_SCRIPTS = (
    "merge_permissions.py",
    "nexus_hub_cli.py",
    "run_trigger_evals.py",
    "validate_permission_baseline.py",
)


def _metadata_paths(value: Any, prefix: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}"
            if isinstance(key, str) and key.startswith("_"):
                findings.append(child_path)
            findings.extend(_metadata_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_metadata_paths(child, f"{prefix}[{index}]") )
    return findings


def collect_findings(home: Path, workspace: Path) -> list[str]:
    findings: list[str] = []
    install_root = home / ".nexus-hub"
    settings_path = workspace / ".claude" / "settings.local.json"
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"permission baseline is missing or invalid at {settings_path}: {exc}"]

    allow = settings.get("permissions", {}).get("allow") if isinstance(settings, dict) else None
    if not isinstance(allow, list) or not allow:
        findings.append("permission baseline has no non-empty permissions.allow list")
    metadata = _metadata_paths(settings)
    if metadata:
        findings.append(f"merged config leaked template metadata: {', '.join(metadata)}")

    for name in EXPECTED_SCRIPTS:
        if not (install_root / "scripts" / name).is_file():
            findings.append(f"expected installed script is missing: {name}")
    if not (install_root / "VERSION").is_file():
        findings.append("installed VERSION marker is missing")
    return findings


def _launcher(home: Path) -> list[str]:
    install_root = home / ".nexus-hub"
    if os.name == "nt":
        return [str(install_root / "bin" / "nexus-hub.cmd"), "--version"]
    return [str(install_root / "bin" / "nexus-hub"), "--version"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args(argv)
    home = args.home.resolve()
    workspace = args.workspace.resolve()
    findings = collect_findings(home, workspace)
    if not findings:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        env["NEXUS_HUB_HOME"] = str(home / ".nexus-hub")
        command = _launcher(home)
        try:
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            findings.append(f"installed nexus-hub launcher did not run: {exc}")
        else:
            output = (result.stdout + result.stderr).strip()
            if result.returncode != 0 or not output.startswith("nexus-hub "):
                findings.append(f"installed nexus-hub --version failed ({result.returncode}): {output}")
    if findings:
        for finding in findings:
            print(f"installer smoke: FAIL: {finding}", file=sys.stderr)
        return 1
    print("installer smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
