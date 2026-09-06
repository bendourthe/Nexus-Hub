#!/usr/bin/env python3
"""Assert every SKILL.md satisfies the agentskills.io open-standard contract.

The standard requires `name` and `description` present and non-empty, `name`
1-64 characters matching `^[a-z0-9]+(-[a-z0-9]+)*$`, and `description` 1-1024
characters. This guard proves that contract in `make validate` and CI, replacing
an untested claim with a checked one. Thirteen pre-existing pushy descriptions
exceed 1024 characters and are grandfathered by name in
`OVERLONG_DESCRIPTION_ALLOWLIST`; a new over-long description is a hard error.

Deliberate non-goals (do not add them here):

- Name-equals-directory is already a hard rule in `scripts/validate_skills.py`.
  Re-implementing it would create two places to fix one rule.
- A blanket ban on `<` / `>` in frontmatter would regress Nexus-Hub's v3.15.2
  semantic placeholder lint, which is strictly more precise, and would reject
  legitimate CLI notation such as `<path>`.

Additional top-level keys beyond the standard's recognized set (`name`,
`description`, `license`, `compatibility`, `metadata`, `allowed-tools`) are
permitted by the standard. They are reported as INFORMATION, never as failures.

Repo-internal, stdlib-only, READ-ONLY (never edits files). No installer copy
step; listed in `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py`.

Usage:
    python scripts/check_agentskills_conformance.py
    python scripts/check_agentskills_conformance.py --root .
    python scripts/check_agentskills_conformance.py --json

Exit codes:
    0  every scanned SKILL.md satisfies the contract (or none were found)
    1  one or more contract failures (all collected before exit)
    2  usage / IO error (root missing, a SKILL.md unreadable)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MIN, NAME_MAX = 1, 64
DESCRIPTION_MIN, DESCRIPTION_MAX = 1, 1024
STANDARD_KEYS = frozenset(
    {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
)
SKILLS_GLOB = "catalog/skills/*/*/SKILL.md"

# Nexus-Hub's pushy-description convention (verbatim trigger phrases + SKIP)
# predates this guard and already exceeds the agentskills.io 1024-character
# description cap on these skills. Absence of a name from this set is never
# an exemption: a NEW over-long description is a hard failure. Tracked as
# known-gap WN-v3201-1; remove a name when that skill's description is trimmed.
OVERLONG_DESCRIPTION_ALLOWLIST = frozenset(
    {
        "agentic-endpoint-hardening",
        "continuous-learning",
        "cross-artifact-analyzer",
        "deepseek-harness",
        "document-to-interactive-html",
        "mcp-builder",
        "product-strategy",
        "project-constitution",
        "session-query",
        "skill-create",
        "skill-eval-loop",
        "skill-stocktake",
        "tasks-to-issues",
    }
)


def unquote(value: str) -> str:
    """Strip one matching pair of surrounding quotes, if present."""
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1]
    return text


def parse_frontmatter(content: str) -> dict[str, str] | None:
    """Return top-level frontmatter keys as unquoted strings, or None."""
    if not content.startswith("---"):
        return None
    end = content.find("\n---", 3)
    if end == -1:
        return None
    fields: dict[str, str] = {}
    for line in content[3:end].splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = unquote(value.strip())
    return fields


def find_skill_files(root: Path) -> list[Path]:
    """Return every catalog/skills/<category>/<name>/SKILL.md under root."""
    return sorted(root.glob(SKILLS_GLOB))


def check_skill(path: Path, fields: dict[str, str]) -> tuple[list[dict[str, str]], bool]:
    """Return (failures, grandfathered_overlong) for one skill."""
    skill_name = fields.get("name") or path.parent.name
    failures: list[dict[str, str]] = []
    grandfathered_overlong = False
    name = fields.get("name", "")
    description = fields.get("description", "")

    if not name:
        failures.append(
            {
                "skill": skill_name,
                "path": path.as_posix(),
                "field": "name",
                "message": f"{path}: name is missing or empty",
            }
        )
    else:
        if not (NAME_MIN <= len(name) <= NAME_MAX):
            failures.append(
                {
                    "skill": skill_name,
                    "path": path.as_posix(),
                    "field": "name",
                    "message": (
                        f"{path}: name is {len(name)} characters "
                        f"(must be {NAME_MIN}-{NAME_MAX})"
                    ),
                }
            )
        if not NAME_RE.fullmatch(name):
            failures.append(
                {
                    "skill": skill_name,
                    "path": path.as_posix(),
                    "field": "name",
                    "message": (
                        f"{path}: name {name!r} must match "
                        f"{NAME_RE.pattern}"
                    ),
                }
            )

    if not description:
        failures.append(
            {
                "skill": skill_name,
                "path": path.as_posix(),
                "field": "description",
                "message": f"{path}: description is missing or empty",
            }
        )
    elif len(description) > DESCRIPTION_MAX:
        if skill_name in OVERLONG_DESCRIPTION_ALLOWLIST:
            grandfathered_overlong = True
        else:
            failures.append(
                {
                    "skill": skill_name,
                    "path": path.as_posix(),
                    "field": "description",
                    "message": (
                        f"{path}: description is {len(description)} characters "
                        f"(must be {DESCRIPTION_MIN}-{DESCRIPTION_MAX})"
                    ),
                }
            )
    return failures, grandfathered_overlong


def scan(root: Path) -> tuple[list[dict[str, str]], list[str], int, list[str], list[str]]:
    """Return (failures, extra_keys, skills_scanned, io_errors, grandfathered)."""
    failures: list[dict[str, str]] = []
    extra_keys: set[str] = set()
    io_errors: list[str] = []
    grandfathered: list[str] = []
    files = find_skill_files(root)
    for path in files:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            io_errors.append(f"{path}: cannot read ({exc})")
            continue
        fields = parse_frontmatter(content)
        if fields is None:
            failures.append(
                {
                    "skill": path.parent.name,
                    "path": path.as_posix(),
                    "field": "frontmatter",
                    "message": f"{path}: no valid YAML frontmatter (must start with ---)",
                }
            )
            continue
        extra_keys.update(key for key in fields if key not in STANDARD_KEYS)
        skill_failures, was_grandfathered = check_skill(path, fields)
        failures.extend(skill_failures)
        if was_grandfathered:
            grandfathered.append(fields.get("name") or path.parent.name)
    return failures, sorted(extra_keys), len(files), io_errors, grandfathered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root to scan (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report on stdout",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 2

    failures, extra_keys, scanned, io_errors, grandfathered = scan(root)
    if io_errors:
        for message in io_errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 2

    payload = {
        "ok": not failures,
        "skills_scanned": scanned,
        "failures": failures,
        "information": {
            "extra_top_level_keys": extra_keys,
            "grandfathered_overlong_descriptions": grandfathered,
        },
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if failures else 0

    print(f"Scanned {scanned} skills under {root / 'catalog' / 'skills'}")
    if extra_keys:
        print(
            "INFO: extra top-level keys beyond the agentskills.io recognized "
            f"set (permitted): {', '.join(extra_keys)}"
        )
    if grandfathered:
        print(
            "INFO: grandfathered over-1024-character descriptions "
            f"({len(grandfathered)}): {', '.join(grandfathered)}"
        )
    if failures:
        print(f"\n--- {len(failures)} ERROR(S) ---")
        for item in failures:
            print(f"  ERROR: {item['message']}")
        print(
            f"\nRESULT: FAIL ({len(failures)} agentskills.io contract "
            f"failures, {scanned} skills scanned)"
        )
        return 1

    print(f"RESULT: PASS (0 errors, {scanned} skills scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
