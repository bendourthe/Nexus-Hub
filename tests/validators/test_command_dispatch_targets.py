"""Every command's dispatch target resolves to a catalog skill or a shipped script.

A command file is a thin dispatcher (catalog/style-guides/command-scope-mechanism.md):
its indented `<scope> -> <target>` lines name the skill, or the script, that does the
work. A target that does not exist leaves the command with no procedure on any
platform, which is how `/usage` pointed at a removed `check-usage` skill from v3.2.0
until v4.13.11 (v4.13.9 BG-12).

The v3.0.0 consolidation left 19 more targets naming removed v3.x command bodies.
v4.13.11 re-pointed each to the catalog skill or script that does the work today, or
wrote the procedure into the command where none exists, so the set must stay empty.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMMANDS = REPO / "catalog" / "commands"
ARROW = re.compile(r"^\s{4,}\S.*?\s+->\s+(.+)$")
SCRIPT_DIRS = (REPO / "catalog" / "hooks", REPO / "scripts")



def _skills() -> set[str]:
    return {p.parent.name for p in (REPO / "catalog" / "skills").glob("*/*/SKILL.md")}


def _targets(text: str) -> list[str]:
    """Skill or script names on the right of each dispatcher arrow.

    A command (`/skills list`), a platform built-in (`built-in`, `update-config
    (built-in)`), a pipeline of other scopes (`release -> docs -> version -> ...`),
    and prose with spaces are not catalog targets and are skipped.
    """
    found = []
    for line in text.splitlines():
        match = ARROW.match(line)
        if not match:
            continue
        rhs = re.sub(r"[\w.-]+\s*\(built-in\)", "", match.group(1))
        rhs = re.sub(r"\([^()]*\)", "", rhs)  # parenthetical notes are prose
        if " -> " in rhs:
            continue
        for part in re.split(r",|\s\+\s|\s/\s", rhs):
            part = part.strip()
            if not part or part.startswith("/"):
                continue
            token = part.split()[0]
            if token == "built-in" or not re.fullmatch(r"[A-Za-z0-9_.-]+", token):
                continue
            if len(part.split()) > 1 and not part.split()[1].startswith("--"):
                continue  # prose such as "integration gate -> docs -> ..."
            found.append(token)
    return found


def _resolves(token: str, skills: set[str]) -> bool:
    if token.endswith((".py", ".sh", ".ps1")):
        return any((d / token).is_file() for d in SCRIPT_DIRS)
    return token in skills


def _dangling() -> set[tuple[str, str]]:
    skills = _skills()
    out = set()
    for path in sorted(COMMANDS.glob("*.md")):
        for token in _targets(path.read_text(encoding="utf-8")):
            if not _resolves(token, skills):
                out.add((path.stem, token))
    return out


def test_usage_dispatches_to_the_shipped_probe() -> None:
    text = (COMMANDS / "usage.md").read_text(encoding="utf-8")
    targets = _targets(text)
    assert targets == ["_usage_probe.py"], targets
    assert (REPO / "catalog" / "hooks" / "_usage_probe.py").is_file()
    assert "-> check-usage" not in text


def test_no_command_dispatches_to_a_missing_target() -> None:
    dangling = _dangling()
    assert not dangling, f"dispatch targets that resolve to no skill or script: {sorted(dangling)}"


def test_no_skill_body_names_the_removed_check_usage_skill() -> None:
    hits = [p.relative_to(REPO).as_posix() for p in (REPO / "catalog").rglob("*.md")
            if "check-usage" in p.read_text(encoding="utf-8")
            and p != COMMANDS / "usage.md"]
    assert not hits, hits
