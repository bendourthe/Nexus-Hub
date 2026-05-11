"""Tests for scripts/package_skill.py (Phase 7 / A16).

Covers:
    - happy path: a fixture skill with valid frontmatter packages successfully
    - the produced archive is a valid ZIP
    - SKILL.md sits at the archive root (round-trip extraction layout matches
      the source skill folder)
    - bundled subdirectories survive the round-trip (scripts/, references/,
      assets/, plus arbitrary siblings like themes/ or templates/)
    - .gitkeep placeholders are excluded from the archive
    - missing required frontmatter fields cause SystemExit(1)
    - non-kebab-case `name` causes SystemExit(1)
    - --validate-only succeeds without writing an archive

Run with: pytest catalog/hooks/tests/test_package_skill.py -v
"""

from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PACKAGER_FILE = _REPO_ROOT / "scripts" / "package_skill.py"


def _load_packager():
    spec = importlib.util.spec_from_file_location("package_skill", _PACKAGER_FILE)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["package_skill"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_pkg = _load_packager()


# ── Fixture builders ───────────────────────────────────────────────────────

VALID_FRONTMATTER = """---
name: fixture-skill
description: A fixture skill used by the package_skill.py test suite.
summary_l0: "Fixture skill for packaging tests."
overview_l1: "Used by catalog/hooks/tests/test_package_skill.py to exercise the .skill archive packager. Not registered in any data/ file."
---

# Fixture Skill

Body content.
"""


def _make_skill(
    tmp_path: Path,
    skill_md_body: str = VALID_FRONTMATTER,
    bundle_files: dict[str, str] | None = None,
) -> Path:
    skill_dir = tmp_path / "fixture-skill"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill_md_body, encoding="utf-8")
    if bundle_files:
        for rel, body in bundle_files.items():
            target = skill_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
    return skill_dir


# ── Happy path ─────────────────────────────────────────────────────────────


def test_packages_minimal_skill(tmp_path: Path):
    skill_dir = _make_skill(tmp_path)
    output = tmp_path / "out.skill"

    result = _pkg.package_skill(skill_dir=skill_dir, output_path=output)

    assert result == output.resolve()
    assert output.is_file()
    assert zipfile.is_zipfile(output)


def test_archive_contains_skill_md_at_root(tmp_path: Path):
    skill_dir = _make_skill(tmp_path)
    output = tmp_path / "out.skill"

    _pkg.package_skill(skill_dir=skill_dir, output_path=output)

    with zipfile.ZipFile(output) as zf:
        names = zf.namelist()
    assert "SKILL.md" in names


def test_bundled_subdirs_survive_round_trip(tmp_path: Path):
    bundle = {
        "scripts/run.sh": "#!/usr/bin/env bash\necho hi\n",
        "references/runbook.md": "# Runbook\n",
        "assets/logo.svg": "<svg/>\n",
        "themes/editorial.json": "{}\n",
    }
    skill_dir = _make_skill(tmp_path, bundle_files=bundle)
    output = tmp_path / "out.skill"

    _pkg.package_skill(skill_dir=skill_dir, output_path=output)

    with zipfile.ZipFile(output) as zf:
        names = set(zf.namelist())

    assert "scripts/run.sh" in names
    assert "references/runbook.md" in names
    assert "assets/logo.svg" in names
    assert "themes/editorial.json" in names


def test_gitkeep_excluded(tmp_path: Path):
    skill_dir = _make_skill(tmp_path, bundle_files={"scripts/.gitkeep": ""})
    output = tmp_path / "out.skill"

    _pkg.package_skill(skill_dir=skill_dir, output_path=output)

    with zipfile.ZipFile(output) as zf:
        names = zf.namelist()
    assert all(not n.endswith(".gitkeep") for n in names)


def test_default_output_uses_frontmatter_name(tmp_path: Path, monkeypatch):
    skill_dir = _make_skill(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = _pkg.package_skill(skill_dir=skill_dir, output_path=None)

    assert result is not None
    assert result.name == "fixture-skill.skill"
    assert result.is_file()


# ── Validation failures ────────────────────────────────────────────────────


def test_missing_skill_md_raises(tmp_path: Path):
    empty_dir = tmp_path / "no-skill-md"
    empty_dir.mkdir()
    with pytest.raises(SystemExit) as exc:
        _pkg.package_skill(skill_dir=empty_dir, output_path=tmp_path / "x.skill")
    assert exc.value.code == 1


def test_missing_required_frontmatter_field_raises(tmp_path: Path):
    body = """---
name: missing-description
summary_l0: "no description"
---

# Body
"""
    skill_dir = _make_skill(tmp_path, skill_md_body=body)
    with pytest.raises(SystemExit) as exc:
        _pkg.package_skill(skill_dir=skill_dir, output_path=tmp_path / "x.skill")
    assert exc.value.code == 1


def test_no_frontmatter_raises(tmp_path: Path):
    skill_dir = _make_skill(tmp_path, skill_md_body="# Body only, no frontmatter\n")
    with pytest.raises(SystemExit) as exc:
        _pkg.package_skill(skill_dir=skill_dir, output_path=tmp_path / "x.skill")
    assert exc.value.code == 1


def test_non_kebab_case_name_raises(tmp_path: Path):
    body = """---
name: NotKebabCase
description: Bad name format.
---
"""
    skill_dir = _make_skill(tmp_path, skill_md_body=body)
    with pytest.raises(SystemExit) as exc:
        _pkg.package_skill(skill_dir=skill_dir, output_path=tmp_path / "x.skill")
    assert exc.value.code == 1


def test_missing_skill_dir_raises(tmp_path: Path):
    with pytest.raises(SystemExit) as exc:
        _pkg.package_skill(
            skill_dir=tmp_path / "does-not-exist",
            output_path=tmp_path / "x.skill",
        )
    assert exc.value.code == 1


# ── --validate-only mode ────────────────────────────────────────────────────


def test_validate_only_does_not_write_archive(tmp_path: Path):
    skill_dir = _make_skill(tmp_path)
    output = tmp_path / "should-not-exist.skill"

    result = _pkg.package_skill(
        skill_dir=skill_dir,
        output_path=output,
        validate_only=True,
    )

    assert result is None
    assert not output.exists()


def test_validate_only_still_fails_invalid_frontmatter(tmp_path: Path):
    body = """---
description: missing name
---
"""
    skill_dir = _make_skill(tmp_path, skill_md_body=body)
    with pytest.raises(SystemExit) as exc:
        _pkg.package_skill(
            skill_dir=skill_dir,
            output_path=tmp_path / "x.skill",
            validate_only=True,
        )
    assert exc.value.code == 1


# ── CLI entry-point ────────────────────────────────────────────────────────


def test_main_cli_packages(tmp_path: Path, monkeypatch):
    skill_dir = _make_skill(tmp_path)
    output = tmp_path / "cli.skill"

    rc = _pkg.main([str(skill_dir), "--output", str(output)])

    assert rc == 0
    assert output.is_file()
    assert zipfile.is_zipfile(output)


def test_main_cli_validate_only(tmp_path: Path):
    skill_dir = _make_skill(tmp_path)
    output = tmp_path / "cli.skill"

    rc = _pkg.main([str(skill_dir), "--output", str(output), "--validate-only"])

    assert rc == 0
    assert not output.exists()
