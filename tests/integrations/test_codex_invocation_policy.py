"""Tests for the Codex invocation-policy sidecar mapping (v3.17.5 Phase 6).

Codex expresses Claude's `disable-model-invocation` through a different file, a
different key, and the OPPOSITE polarity. The polarity is the whole risk: a
mapping that copies the value across produces `allow_implicit_invocation: true`
for a skill that asked not to be auto-invoked, which is the precise inverse of
the author's intent and looks correct in a diff. These tests assert the
inversion explicitly.

The second risk is destroying an authored sidecar. OpenAI's `agents/openai.yaml`
also carries interface and dependency metadata this mapping cannot reconstruct,
so a skill shipping its own must be left alone.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.integrations._catalog_adapters import (  # noqa: E402
    _declares_manual_only,
    codex_invocation_policy,
)


class _Manifest:
    def __init__(self) -> None:
        self.logs: list[str] = []
        self.tracked: list[str] = []

    def log(self, key: str, msg: str) -> None:
        self.logs.append(msg)

    def track(self, key: str, path: str) -> None:
        self.tracked.append(path)


class _Ctx:
    def __init__(self, dry_run: bool = False, overwrite: bool = True) -> None:
        self.dry_run = dry_run
        self.overwrite = overwrite
        self.manifest = _Manifest()


def make_skill(root: Path, name: str, policy: str | None) -> Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    extra = f"{policy}\n" if policy else ""
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test skill.\n{extra}---\n\n# {name}\n",
        encoding="utf-8",
    )
    return d


def sidecar_of(skill_dir: Path) -> Path:
    return skill_dir / "agents" / "openai.yaml"


def test_manual_only_skill_gets_an_inverted_sidecar(tmp_path):
    """disable-model-invocation: true -> allow_implicit_invocation: false."""
    skill = make_skill(tmp_path, "deploy", "disable-model-invocation: true")
    actions = codex_invocation_policy(_Ctx(), "codex", tmp_path)
    assert len(actions) == 1
    body = sidecar_of(skill).read_text(encoding="utf-8")
    assert "allow_implicit_invocation: false" in body
    assert "allow_implicit_invocation: true" not in body
    assert "policy:" in body


def test_the_sidecar_documents_the_inversion(tmp_path):
    """A reader of the generated file must not mistake false for a copy error."""
    skill = make_skill(tmp_path, "deploy", "disable-model-invocation: true")
    codex_invocation_policy(_Ctx(), "codex", tmp_path)
    body = sidecar_of(skill).read_text(encoding="utf-8")
    assert "inverted" in body.lower()
    assert "Nexus-Hub" in body


@pytest.mark.parametrize("policy", [None, "disable-model-invocation: false"])
def test_no_sidecar_when_the_field_is_absent_or_false(tmp_path, policy):
    """Codex's default already matches ours, so emitting anything is noise."""
    skill = make_skill(tmp_path, "ordinary", policy)
    actions = codex_invocation_policy(_Ctx(), "codex", tmp_path)
    assert actions == []
    assert not sidecar_of(skill).exists()


def test_an_authored_sidecar_is_left_alone(tmp_path):
    """It carries interface/dependency metadata this mapping cannot rebuild."""
    skill = make_skill(tmp_path, "branded", "disable-model-invocation: true")
    sidecar = sidecar_of(skill)
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    authored = 'interface:\n  display_name: "Branded"\n'
    sidecar.write_text(authored, encoding="utf-8")

    ctx = _Ctx()
    actions = codex_invocation_policy(ctx, "codex", tmp_path)

    assert actions == []
    assert sidecar.read_text(encoding="utf-8") == authored
    assert any("kept-authored-sidecar" in m for m in ctx.manifest.logs)


def test_regenerating_our_own_sidecar_is_idempotent(tmp_path):
    make_skill(tmp_path, "deploy", "disable-model-invocation: true")
    first = codex_invocation_policy(_Ctx(), "codex", tmp_path)
    second = codex_invocation_policy(_Ctx(), "codex", tmp_path)
    assert first[0].action == "created"
    assert second[0].action == "unchanged"


def test_only_declaring_skills_are_touched_in_a_mixed_tree(tmp_path):
    make_skill(tmp_path, "manual", "disable-model-invocation: true")
    make_skill(tmp_path, "auto", None)
    make_skill(tmp_path, "explicit-false", "disable-model-invocation: false")
    actions = codex_invocation_policy(_Ctx(), "codex", tmp_path)
    assert len(actions) == 1
    assert "manual" in actions[0].path


def test_a_missing_skills_dir_is_a_no_op(tmp_path):
    assert codex_invocation_policy(_Ctx(), "codex", tmp_path / "nope") == []


def test_a_directory_without_skill_md_is_skipped(tmp_path):
    (tmp_path / "scaffold").mkdir()
    assert codex_invocation_policy(_Ctx(), "codex", tmp_path) == []


def test_dry_run_plans_command_sidecars_from_source_when_dest_is_empty(tmp_path):
    """dry_run does not write SKILL.md, so dest scan alone would under-count."""
    repo = tmp_path / "repo"
    (repo / "catalog" / "commands").mkdir(parents=True)
    (repo / "catalog" / "skills" / "demo").mkdir(parents=True)
    (repo / "catalog" / "commands" / "implement.md").write_text(
        "# implement\n\nDo the work.\n", encoding="utf-8"
    )
    (repo / "catalog" / "skills" / "demo" / "SKILL.md").write_text(
        "---\nname: demo\ndescription: x\n---\n\n# demo\n", encoding="utf-8"
    )
    ctx = _Ctx(dry_run=True)
    ctx.repo_root = repo
    dest = tmp_path / "empty-skills"
    actions = codex_invocation_policy(ctx, "codex", dest)
    assert len(actions) == 1
    assert actions[0].action == "created"
    assert "implement" in actions[0].path
    assert "openai.yaml" in actions[0].path.replace("\\", "/")


@pytest.mark.parametrize(
    "line,expected",
    [
        ("disable-model-invocation: true", True),
        ("disable-model-invocation: True", True),
        ("disable-model-invocation: false", False),
        ("disable-model-invocation: TRUE", True),
        ("user-invocable: false", False),
        (None, False),
    ],
)
def test_frontmatter_detection(tmp_path, line, expected):
    skill = make_skill(tmp_path, "probe", line)
    assert _declares_manual_only(skill / "SKILL.md") is expected


def test_detection_ignores_a_body_mention(tmp_path):
    """The field only counts inside the frontmatter block."""
    d = tmp_path / "prose"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: prose\ndescription: x\n---\n\n"
        "Set `disable-model-invocation: true` to make a skill manual-only.\n",
        encoding="utf-8",
    )
    assert _declares_manual_only(d / "SKILL.md") is False


def test_a_file_without_frontmatter_is_not_manual_only(tmp_path):
    d = tmp_path / "bare"
    d.mkdir()
    (d / "SKILL.md").write_text("# Just a heading\n", encoding="utf-8")
    assert _declares_manual_only(d / "SKILL.md") is False


def test_the_shipped_catalog_declares_no_manual_only_skill():
    """Documents today's state: the mapping is wired but not yet exercised."""
    catalog = REPO_ROOT / "catalog" / "skills"
    declaring = [
        p.parent.name
        for p in catalog.rglob("SKILL.md")
        if _declares_manual_only(p)
    ]
    assert declaring == [], (
        f"skills now declare disable-model-invocation: {declaring}. That is "
        "fine, but the Codex sidecar will now be emitted for them; confirm the "
        "installer smoke expectations still hold."
    )
