"""Tests for the per-skill bundled-resource orphan detector in scripts/validate_skills.py.

The orphan detector enforces the AGENTS.md "Per-skill Bundled Resources"
convention: every file under a skill's `scripts/`, `references/`, or `assets/`
subdirectory MUST be referenced at least once from SKILL.md (or from another
file under `references/` that is itself referenced from SKILL.md). The only
exempt filename is `.gitkeep`, which is allowed as a placeholder for an empty
future-expansion subdirectory.

Run with: pytest catalog/hooks/tests/test_skill_bundles.py -v
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# ── Module loading ─────────────────────────────────────────────────────────
# scripts/validate_skills.py is a top-level script; load it via importlib so
# we can call validate_skill_bundles() directly without invoking the CLI.

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VALIDATOR_FILE = _REPO_ROOT / "scripts" / "validate_skills.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_skills", _VALIDATOR_FILE)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["validate_skills"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_vs = _load_validator()


# ── Fixture builder ────────────────────────────────────────────────────────


def _make_skill(tmp_path: Path, skill_md_body: str, bundle_files: dict[str, str]) -> Path:
    """Build a fixture skill directory with a SKILL.md and arbitrary bundled files.

    `bundle_files` maps relative paths (e.g. 'scripts/foo.py') to file contents.
    """
    skill_dir = tmp_path / "fixture-skill"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill_md_body, encoding="utf-8")
    for rel, body in bundle_files.items():
        target = skill_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    return skill_dir


# ── Tests ──────────────────────────────────────────────────────────────────


def test_orphan_in_scripts_is_warned(tmp_path: Path):
    """A file under scripts/ that SKILL.md never names triggers a warning."""
    skill_md = (
        "---\nname: fixture\n---\n"
        "# Fixture\n\n"
        "Body that does not name the bundled file.\n"
    )
    skill_dir = _make_skill(
        tmp_path,
        skill_md,
        {"scripts/orphan.py": "# orphan script\n"},
    )

    warnings = _vs.validate_skill_bundles(skill_dir, skill_md)

    assert len(warnings) == 1
    assert "orphan.py" in warnings[0]
    assert "either reference this file from SKILL.md or remove it" in warnings[0]


def test_referenced_file_is_silent(tmp_path: Path):
    """A file mentioned by basename in SKILL.md is not reported."""
    skill_md = (
        "---\nname: fixture\n---\n"
        "# Fixture\n\n"
        "See `scripts/run-eval.py` for the eval driver.\n"
    )
    skill_dir = _make_skill(
        tmp_path,
        skill_md,
        {"scripts/run-eval.py": "# referenced script\n"},
    )

    warnings = _vs.validate_skill_bundles(skill_dir, skill_md)

    assert warnings == []


def test_gitkeep_is_exempt(tmp_path: Path):
    """`.gitkeep` placeholders are tolerated even when not referenced."""
    skill_md = "---\nname: fixture\n---\n# Fixture\n"
    skill_dir = _make_skill(
        tmp_path,
        skill_md,
        {"scripts/.gitkeep": ""},
    )

    warnings = _vs.validate_skill_bundles(skill_dir, skill_md)

    assert warnings == []


def test_reference_from_another_reference_satisfies_audit(tmp_path: Path):
    """A bundled file is OK if a `references/*.md` (itself referenced from SKILL.md)
    names it. This lets a top-level reference act as a TOC for sub-resources.
    """
    skill_md = (
        "---\nname: fixture\n---\n"
        "# Fixture\n\n"
        "See `references/index.md` for the full asset catalog.\n"
    )
    bundle = {
        "references/index.md": "Catalog: see `assets/diagram.svg`.\n",
        "assets/diagram.svg": "<svg/>",
    }
    skill_dir = _make_skill(tmp_path, skill_md, bundle)

    warnings = _vs.validate_skill_bundles(skill_dir, skill_md)

    assert warnings == []


def test_mix_of_orphan_and_referenced_only_reports_orphan(tmp_path: Path):
    skill_md = (
        "---\nname: fixture\n---\n"
        "# Fixture\n\n"
        "Use `scripts/keep.py` to drive the workflow.\n"
    )
    bundle = {
        "scripts/keep.py": "# referenced\n",
        "scripts/drop.py": "# orphan\n",
    }
    skill_dir = _make_skill(tmp_path, skill_md, bundle)

    warnings = _vs.validate_skill_bundles(skill_dir, skill_md)

    assert len(warnings) == 1
    assert "drop.py" in warnings[0]
    assert "keep.py" not in warnings[0]


def test_orphan_in_assets_subdir_is_warned(tmp_path: Path):
    """The audit recurses into nested directories under assets/."""
    skill_md = "---\nname: fixture\n---\n# Fixture\n\nNo asset references.\n"
    skill_dir = _make_skill(
        tmp_path,
        skill_md,
        {"assets/themes/editorial.json": '{"name":"editorial"}'},
    )

    warnings = _vs.validate_skill_bundles(skill_dir, skill_md)

    assert len(warnings) == 1
    assert "editorial.json" in warnings[0]


def test_no_subdirs_returns_empty(tmp_path: Path):
    """Skills with no scripts/references/assets directories return zero warnings."""
    skill_md = "---\nname: fixture\n---\n# Fixture\n"
    skill_dir = _make_skill(tmp_path, skill_md, {})

    warnings = _vs.validate_skill_bundles(skill_dir, skill_md)

    assert warnings == []


def test_validator_cli_bundles_only_mode_runs_clean_on_real_catalog(tmp_path: Path):
    """`python scripts/validate_skills.py --bundles-only` must exit 0 against
    the real catalog. Pre-existing orphan warnings are tolerated; the only
    failure path is an unreadable file or a real error."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(_VALIDATOR_FILE), "--bundles-only"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"validate_skills.py --bundles-only failed:\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "RESULT: PASS" in result.stdout


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
