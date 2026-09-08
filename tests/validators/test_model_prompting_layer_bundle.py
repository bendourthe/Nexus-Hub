"""The prompting profile layer must leave no orphan bundled file.

Every mirror `write_model_prompting_profile.py` emits is a bundled file, and
`AGENTS.md` requires every bundled file to be referenced from its SKILL.md.
Before the writer generated an index, the orphan-warning count grew by one per
profiled model: 1 after the first OpenAI profile, 11 after the v4.8.0 roster
sweep. An orphan is not cosmetic here -- the agent never loads a Tier-3
reference that nothing points at, so the mirrors were being generated and then
never read.

Named for the bundle rather than for freshness to stay distinct from
`test_check_model_prompting_freshness.py`, which grades the advisory
roster-drift check instead.
"""

from __future__ import annotations

import subprocess as _subprocess
import sys as _sys
from pathlib import Path

_BUNDLE = (
    Path(__file__).resolve().parents[2]
    / "catalog"
    / "skills"
    / "ai-development"
    / "model-prompting-research"
)
_MIRROR_INDEX = _BUNDLE / "references" / "model-profiles.md"


def test_generated_mirror_index_exists_and_is_marked_generated() -> None:
    assert _MIRROR_INDEX.is_file(), "the writer must generate references/model-profiles.md"
    text = _MIRROR_INDEX.read_text(encoding="utf-8")
    assert "GENERATED" in text, (
        "the index must say it is generated, or someone will hand-edit it and lose "
        "the change on the next write"
    )


def test_mirror_index_links_every_mirror_on_disk() -> None:
    """The property that actually prevents an orphan."""
    mirrors = sorted(p.name for p in (_BUNDLE / "references" / "models").glob("*.md"))
    assert mirrors, "no mirrors on disk; the layer is empty"
    text = _MIRROR_INDEX.read_text(encoding="utf-8")
    missing = [m for m in mirrors if f"models/{m}" not in text]
    assert not missing, f"mirror(s) not linked from the generated index: {missing}"


def test_skill_body_references_the_index() -> None:
    body = (_BUNDLE / "SKILL.md").read_text(encoding="utf-8")
    assert "references/model-profiles.md" in body


def test_bundle_audit_reports_no_orphan_for_this_skill() -> None:
    """End-to-end through the real auditor, which is the thing that warned."""
    repo = Path(__file__).resolve().parents[2]
    proc = _subprocess.run(
        [_sys.executable, str(repo / "scripts" / "validate_skills.py"), "--bundles-only", "--verbose"],
        capture_output=True,
        text=True,
        cwd=repo,
        check=False,
    )
    offenders = [
        line
        for line in proc.stdout.splitlines()
        if "model-prompting-research" in line and "not referenced" in line
    ]
    assert not offenders, "orphan bundled file(s) in the profile layer:\n" + "\n".join(offenders)
