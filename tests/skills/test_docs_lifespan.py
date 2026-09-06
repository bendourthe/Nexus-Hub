"""Phase 2 lifespan-axis regression tests for docs-layout-refactor."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py"
SKILL = ROOT / "catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md"
REFERENCE = ROOT / "catalog/skills/code-cleanup/docs-layout-refactor/references/link-integrity.md"
CONSISTENCY = ROOT / "catalog/skills/workflow/documentation-consistency/SKILL.md"


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_docs_lifespan", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = _load_module()


def _git(repo: Path, *args: str, date: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if date:
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    bucket = repo / "docs/v1/v1.0"
    bucket.mkdir(parents=True)
    (bucket / "before.md").write_text("before\n", encoding="utf-8")
    (bucket / "after.md").write_text("initial\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "tag.gpgSign", "false")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "initial", date="2026-01-01T12:00:00+00:00")
    _git(repo, "tag", "v1.0.0")
    (bucket / "after.md").write_text("changed after close\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "late edit", date="2026-01-02T12:00:00+00:00")
    return repo


def test_unrecognized_living_subtree_uses_admission_test(tmp_path: Path) -> None:
    file_path = tmp_path / "docs/operator-notes/current-main.md"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("Current production operating model.\n", encoding="utf-8")

    assert AUDIT.lifespan_fast_path("docs/operator-notes/current-main.md") is None
    assert AUDIT.classify_lifespan("never") == "living"


def test_lifespan_contradiction_fires_only_after_release_close(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "lifespan-contradictions",
            "--root",
            str(repo / "docs"),
            "--repo-root",
            str(repo),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 1
    findings = json.loads(result.stdout)
    assert [item["file"] for item in findings] == ["docs/v1/v1.0/after.md"]
    assert findings[0]["release_tag"] == "v1.0.0"
    assert findings[0]["release_close_date"] < findings[0]["offending_commit_date"]


def test_lifespan_contradiction_rule_has_one_definition_and_two_consumers() -> None:
    skill = SKILL.read_text(encoding="utf-8")
    reference = REFERENCE.read_text(encoding="utf-8")
    consistency = CONSISTENCY.read_text(encoding="utf-8")

    canonical_phrase = "newest file commit"
    assert reference.count(canonical_phrase) == 1
    assert canonical_phrase not in skill
    assert canonical_phrase not in consistency
    assert "references/link-integrity.md" in skill
    assert "docs-layout-refactor/references/link-integrity.md" in consistency


def test_skill_stays_within_tier_two_size_target() -> None:
    assert len(SKILL.read_text(encoding="utf-8").splitlines()) <= 500
