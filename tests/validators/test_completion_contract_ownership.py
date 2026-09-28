"""The completion contract is the single owner of the completion predicates.

`catalog/skills/workflow/implement-phase/references/completion-contract.md`
defines the predicate ids. Commands and skills must refer to the contract, not
restate a predicate, so the definition of "done" cannot drift between the
command, the skill, and the checker. This test fails when a predicate id shows
up in distributed catalog text other than the contract itself.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    REPO_ROOT
    / "catalog"
    / "skills"
    / "workflow"
    / "implement-phase"
    / "references"
    / "completion-contract.md"
)

_ID = re.compile(r"`((?:gaps|evidence|tests|integration|release|cleanup)\.[a-z-]+)`")


def _predicate_ids() -> set[str]:
    return set(_ID.findall(CONTRACT.read_text(encoding="utf-8")))


def test_contract_defines_the_expected_predicates() -> None:
    ids = _predicate_ids()
    for expected in (
        "gaps.version",
        "evidence.file",
        "integration.merged",
        "release.github",
        "cleanup.worktree",
    ):
        assert expected in ids


def test_no_catalog_file_restates_a_predicate() -> None:
    ids = _predicate_ids()
    offenders = []
    for path in (REPO_ROOT / "catalog").rglob("*.md"):
        if path == CONTRACT:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = sorted(pid for pid in ids if f"`{pid}`" in text)
        if hits:
            offenders.append(f"{path.relative_to(REPO_ROOT)}: {hits}")
    assert not offenders, "predicate ids restated outside the contract:\n" + "\n".join(
        offenders
    )
