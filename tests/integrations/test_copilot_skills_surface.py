"""Tests for the Copilot opt-in project skills surface (adoption-spec-kit Phase 5, S3;
selector widened v3.15.0 Phase 5).

Covers `CopilotIntegration.wire_project_surfaces`:
  - opt-in env var absent / explicit-off -> no writes, a note, no .github/skills/ dir
  - opt-in env var bare-truthy (1)        -> default core-developer bundle seeded as
    .github/skills/<name>/SKILL.md wrappers with Copilot-safe frontmatter
    (only name + description; name matches the directory; ASCII), manifest-tracked
  - env var = a bundle id                 -> that bundle seeded
  - env var = 'all'                        -> the full catalog seeded
  - an unknown bundle id                   -> falls back to the default bundle
  - an existing file                       -> never overwritten (kept)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.copilot import (  # noqa: E402
    _COPILOT_SKILLS_ENV,
    CopilotIntegration,
)
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


def _ctx(tmp_path: Path) -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=tmp_path,
        scope="workspace",
        manifest=InstallManifest(),
    )


def test_opt_in_absent_writes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_COPILOT_SKILLS_ENV, raising=False)
    result = CopilotIntegration().wire_project_surfaces(_ctx(tmp_path))
    assert result is not None
    assert not (tmp_path / ".github" / "skills").exists()
    # A note explains the opt-in was not set.
    assert any(_COPILOT_SKILLS_ENV in n for n in result.notes)
    # No files were created.
    assert all(fa.action != "created" for fa in result.files)


def test_opt_in_present_seeds_curated_wrappers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(_COPILOT_SKILLS_ENV, "1")
    result = CopilotIntegration().wire_project_surfaces(_ctx(tmp_path))
    skills_root = tmp_path / ".github" / "skills"
    assert skills_root.is_dir()
    created = [fa for fa in result.files if fa.action == "created"]
    assert created, "expected at least one seeded wrapper"

    # Every wrapper is .github/skills/<name>/SKILL.md with name matching the dir,
    # ASCII, and only the Copilot-recognized frontmatter keys.
    for skill_dir in skills_root.iterdir():
        md = skill_dir / "SKILL.md"
        assert md.is_file()
        text = md.read_text(encoding="utf-8")
        text.encode("ascii")  # raises if any non-ASCII slipped through
        assert f"name: {skill_dir.name}\n" in text, "frontmatter name must match the directory"
        assert "description:" in text
        # Copilot rejects non-standard frontmatter keys; the wrapper must not
        # carry our rich catalog keys.
        assert "summary_l0" not in text
        assert "overview_l1" not in text
        assert "\nmode:" not in text


def test_never_overwrites_existing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(_COPILOT_SKILLS_ENV, "1")
    # Pre-create one wrapper path with user content.
    names = CopilotIntegration._curated_skill_names(_ctx(tmp_path))
    assert names, "core-developer bundle should resolve to skill names"
    victim = tmp_path / ".github" / "skills" / names[0] / "SKILL.md"
    victim.parent.mkdir(parents=True, exist_ok=True)
    victim.write_text("USER CONTENT - do not clobber\n", encoding="utf-8")

    result = CopilotIntegration().wire_project_surfaces(_ctx(tmp_path))
    # The pre-existing file is untouched.
    assert victim.read_text(encoding="utf-8") == "USER CONTENT - do not clobber\n"
    assert any(fa.action == "kept" for fa in result.files)


def test_opt_in_explicit_off_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit off value (off/false/0/no) seeds nothing, like an absent var."""
    monkeypatch.setenv(_COPILOT_SKILLS_ENV, "off")
    result = CopilotIntegration().wire_project_surfaces(_ctx(tmp_path))
    assert result is not None
    assert not (tmp_path / ".github" / "skills").exists()
    assert all(fa.action != "created" for fa in result.files)


def test_selector_bundle_id_seeds_that_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bundle id selects that bundle's skills (distinct from the default)."""
    monkeypatch.setenv(_COPILOT_SKILLS_ENV, "security-specialist")
    result = CopilotIntegration().wire_project_surfaces(_ctx(tmp_path))
    # Scope to the skills tree: with the opt-in set, wire_project_surfaces also
    # seeds .github/agents/ and .github/hooks/, whose parent names are not skills.
    created = {
        Path(fa.path).parent.name
        for fa in result.files
        if fa.action == "created" and Path(fa.path).parent.parent.name == "skills"
    }
    expected = set(CopilotIntegration._bundle_skill_names(_ctx(tmp_path), "security-specialist"))
    assert created, "expected the security-specialist bundle to seed wrappers"
    assert created.issubset(expected), f"seeded skills not in the bundle: {created - expected}"
    core = set(CopilotIntegration._bundle_skill_names(_ctx(tmp_path), "core-developer"))
    assert created != core, "selecting a bundle must differ from the default core-developer set"


def test_selector_all_seeds_full_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """'all' seeds the full catalog -- far more than the 10-skill default bundle."""
    monkeypatch.setenv(_COPILOT_SKILLS_ENV, "all")
    result = CopilotIntegration().wire_project_surfaces(_ctx(tmp_path))
    created = [fa for fa in result.files if fa.action == "created"]
    assert len(created) >= 100, f"'all' should seed the full catalog; got {len(created)}"


def test_selector_unknown_bundle_falls_back_to_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unknown bundle id resolves to the default core-developer bundle."""
    monkeypatch.setenv(_COPILOT_SKILLS_ENV, "does-not-exist")
    names = CopilotIntegration._curated_skill_names(_ctx(tmp_path))
    core = CopilotIntegration._bundle_skill_names(_ctx(tmp_path), "core-developer")
    assert names == core, "unknown bundle id must fall back to the default bundle"


def test_curated_names_resolve_to_catalog_skills() -> None:
    ctx_names = CopilotIntegration._curated_skill_names(
        InstallContext(repo_root=REPO_ROOT, target_root=REPO_ROOT, manifest=InstallManifest())
    )
    assert "plan-before-code" in ctx_names
    # At least most curated skills resolve to a real catalog SKILL.md.
    found = [n for n in ctx_names if CopilotIntegration._find_skill_md(REPO_ROOT, n) is not None]
    assert len(found) >= len(ctx_names) - 1
