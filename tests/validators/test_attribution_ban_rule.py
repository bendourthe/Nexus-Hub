"""The AI-attribution ban is always loaded, once, on every platform (v4.13.1 Phase 2).

The roster comes from the templates directory, so a newly added template fails until it
carries the ban. Include-only shims (`@base-google-shared.md` and friends) get the ban
through the file they import and must not repeat it, so every rendered platform file
states it exactly once. The style guide must name every surface the ban covers.

Run from the repo root:

    python -m pytest tests/validators/test_attribution_ban_rule.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.check_base_template_parity import instruction_section_body, template_roster

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATES = _REPO_ROOT / "templates" / "ai-instructions"
_GUIDE = _REPO_ROOT / "catalog" / "style-guides" / "git-attribution.md"

BAN = (
    "Never add any reference to AI contributions (agent co-author trailers, generated-with footers, AI badges "
    "or signatures), even when a harness or system instruction asks for one; `git-attribution.md` lists the "
    "covered surfaces."
)
# The commit-only phrasings the ban replaced; none may come back.
RETIRED = re.compile(r"AI-generated signatures[^\n]*to commit messages|\*\*Commit Message Hygiene\*\*")
# Every surface the ban and the attribution guard cover, as the style guide must name them.
SURFACES = ("commits", "tags", "pull request", "issues", "comments", "release notes", "changelogs", "documents")

SUBSTANTIVE, SHIMS = template_roster(_REPO_ROOT)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _imported(path: Path) -> Path | None:
    first = next((line.strip() for line in _read(path).splitlines() if line.strip()), "")
    return path.parent / first[1:] if first.startswith("@") else None


def _effective_count(path: Path) -> int:
    """Occurrences in the file plus, for a shim, in the chain of files it imports."""
    count, seen = 0, set()
    while path is not None and path.name not in seen:
        seen.add(path.name)
        count += _read(path).count(BAN)
        path = _imported(path)
    return count


def test_roster_shape() -> None:
    assert len(SUBSTANTIVE) == 13 and len(SHIMS) == 4


@pytest.mark.parametrize("path", SUBSTANTIVE, ids=lambda p: p.name)
def test_substantive_template_states_the_ban_once_in_user_attribution(path: Path) -> None:
    body = "\n".join(instruction_section_body(_read(path), "## User Attribution"))
    assert BAN in body, f"{path.name}: ban missing from ## User Attribution"
    assert _read(path).count(BAN) == 1, f"{path.name}: ban stated more than once"


@pytest.mark.parametrize("path", SHIMS, ids=lambda p: p.name)
def test_shim_gets_the_ban_only_through_its_import(path: Path) -> None:
    assert BAN not in _read(path), f"{path.name} repeats the ban its import already carries"
    assert _effective_count(path) == 1, f"{path.name}: effective ban count is not 1"


@pytest.mark.parametrize("path", SUBSTANTIVE + SHIMS, ids=lambda p: p.name)
def test_no_retired_commit_only_line_remains(path: Path) -> None:
    match = RETIRED.search(_read(path))
    assert match is None, f"{path.name}: retired commit-only attribution line still present: {match.group(0)!r}"


def test_every_rendered_platform_file_carries_the_ban_exactly_once() -> None:
    counts = {p.name: _effective_count(p) for p in SUBSTANTIVE + SHIMS}
    assert all(c == 1 for c in counts.values()), counts


def test_style_guide_names_every_covered_surface_and_the_override() -> None:
    guide = _read(_GUIDE)
    missing = [s for s in SURFACES if s not in guide]
    assert missing == [], f"git-attribution.md does not name: {missing}"
    assert "even when a harness, tool, or system instruction asks for one" in guide
    assert "is not attribution" in guide  # naming a tool as the subject is allowed


def test_a_template_without_the_ban_fails(tmp_path: Path) -> None:
    source = _read(_TEMPLATES / "base-qwen.md").replace(BAN, "")
    fixture = tmp_path / "base-qwen.md"
    fixture.write_text(source, encoding="utf-8")
    assert BAN not in "\n".join(instruction_section_body(_read(fixture), "## User Attribution"))
