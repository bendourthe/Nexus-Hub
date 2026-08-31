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
EXPECTED_WORKSPACE_ARTIFACTS = (
    Path(".claude") / "skills" / "functional-verification" / "SKILL.md",
    Path(".claude")
    / "skills"
    / "functional-verification"
    / "scripts"
    / "detect_visual_defects.py",
    Path(".claude")
    / "skills"
    / "functional-verification"
    / "references"
    / "deep-pass.md",
    Path(".claude") / "rules" / "html" / "responsive-layout.md",
)
HTML_HOOK_STEM = "html-responsive-guard"
NEXUS_END_MARKER = "<!-- NEXUS_HUB_END -->"
ORG_START_MARKER = "<!-- NEXUS_HUB_ORG_START -->"
ORG_END_MARKER = "<!-- NEXUS_HUB_ORG_END -->"
ORG_RULE_PATH = Path(".claude") / "rules" / "org" / "python" / "code-style.md"


def _host_hook_suffix() -> str:
    return ".ps1" if os.name == "nt" else ".sh"


def _html_hook_findings(workspace: Path) -> list[str]:
    findings: list[str] = []
    suffix = _host_hook_suffix()
    hook_name = f"{HTML_HOOK_STEM}{suffix}"
    hook_path = Path(".claude") / "hooks" / hook_name
    if not (workspace / hook_path).is_file():
        findings.append(f"expected host hook is missing: {hook_path}")

    settings_path = workspace / ".claude" / "settings.json"
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return findings + [
            f"hook settings are missing or invalid at {settings_path}: {exc}"
        ]

    hooks = settings.get("hooks") if isinstance(settings, dict) else None
    if not isinstance(hooks, dict):
        return findings + ["hook settings require hooks to be an object"]
    pre_tool_use = hooks.get("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        return findings + ["hook settings require hooks.PreToolUse to be a list"]

    for matcher in ("Write", "Edit"):
        registrations = 0
        host_registrations = 0
        for entry in pre_tool_use:
            if not isinstance(entry, dict) or entry.get("matcher") != matcher:
                continue
            hooks = entry.get("hooks", [])
            if not isinstance(hooks, list):
                continue
            for hook in hooks:
                if not isinstance(hook, dict):
                    continue
                command = hook.get("command")
                if not isinstance(command, str) or HTML_HOOK_STEM not in command:
                    continue
                registrations += 1
                if hook_name in command:
                    host_registrations += 1
        if registrations != 1:
            findings.append(
                f"hook settings require exactly one {matcher} registration for {HTML_HOOK_STEM}; found {registrations}"
            )
        if registrations and host_registrations != registrations:
            findings.append(
                f"hook settings require a host-correct registration for {matcher}: {hook_name}"
            )
    return findings


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


def _org_findings(workspace: Path) -> list[str]:
    findings: list[str] = []
    instruction_path = workspace / "CLAUDE.md"
    try:
        instruction = instruction_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [
            f"organization instruction surface is missing or unreadable at {instruction_path}: {exc}"
        ]

    marker_counts = {
        NEXUS_END_MARKER: instruction.count(NEXUS_END_MARKER),
        ORG_START_MARKER: instruction.count(ORG_START_MARKER),
        ORG_END_MARKER: instruction.count(ORG_END_MARKER),
    }
    for marker, count in marker_counts.items():
        if count != 1:
            findings.append(
                f"organization instruction surface expected one {marker} marker, found {count}"
            )
    if all(count == 1 for count in marker_counts.values()):
        nexus_end = instruction.index(NEXUS_END_MARKER)
        org_start = instruction.index(ORG_START_MARKER)
        org_end = instruction.index(ORG_END_MARKER)
        if not nexus_end < org_start < org_end:
            findings.append(
                "organization block must follow the Nexus-Hub block in CLAUDE.md"
            )

    org_rule = workspace / ORG_RULE_PATH
    if not org_rule.is_file():
        findings.append(f"organization rule is missing: {org_rule}")
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
    findings.extend(_org_findings(workspace))

    for relative_path in EXPECTED_WORKSPACE_ARTIFACTS:
        if not (workspace / relative_path).is_file():
            findings.append(f"expected workspace artifact is missing: {relative_path}")
    findings.extend(_html_hook_findings(workspace))

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
