"""Contract tests for the living docs architecture (v3.21.0 Phase 3)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = (
    ROOT
    / "catalog"
    / "skills"
    / "code-cleanup"
    / "docs-layout-refactor"
    / "SKILL.md"
)
SETUP = ROOT / "catalog" / "skills" / "project-setup" / "setup-project" / "SKILL.md"
SETUP_CMD = ROOT / "catalog" / "commands" / "setup.md"
UPDATE_CMD = ROOT / "catalog" / "commands" / "update.md"
PLAN_CMD = ROOT / "catalog" / "commands" / "plan.md"
DECISION = (
    ROOT
    / "docs"
    / "decisions"
    / "implemented"
    / "architecture"
    / "2026-08-24-living-docs-handbooks-and-decisions.md"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_docs_layout_refactor_lists_required_vs_self_gated_paths() -> None:
    text = _read(LAYOUT)
    assert "## Required living docs architecture" in text
    assert "**Required**" in text
    assert "**Self-gated**" in text
    assert "docs/handbooks/" in text
    assert "docs/decisions/" in text
    assert "docs/testing/" in text
    assert "docs/validation/" in text
    assert "never invent" in text.lower() or "Never invent" in text or "never invent" in text
    assert "Generated `html/` is never hand-edited" in text
    assert "document-to-interactive-html" in text
    assert "docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/handbooks/" in text


def test_setup_project_scaffolds_handbooks_and_decisions() -> None:
    text = _read(SETUP)
    assert "docs/handbooks/" in text
    assert "docs/decisions/" in text
    assert "Never overwrite inherited files" in text or "never overwrite inherited files" in text
    assert "Never invent `docs/testing/`" in text or "docs/testing/" in text
    cmd = _read(SETUP_CMD)
    assert "docs/handbooks/" in cmd
    assert "docs/decisions/" in cmd


def test_update_release_regenerates_html_and_snapshots_handbooks() -> None:
    text = _read(UPDATE_CMD)
    assert "Handbook markdown against the code" in text
    assert "Living docs canonicalize" in text
    assert "regenerate-and-fail-on-stale" in text
    assert "Fail the release when generated output is missing or stale" in text
    assert "Living-reference snapshot" in text
    assert "docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/handbooks/" in text
    assert "last-phase evidence" in text


def test_plan_mentions_handbook_check_without_copying_the_template() -> None:
    text = _read(PLAN_CMD)
    assert "living handbook architecture check" in text
    assert "does not duplicate the template" in text
    assert len(text.splitlines()) < 150


def test_living_docs_decision_record_exists_with_required_sections() -> None:
    text = _read(DECISION)
    assert "Status: implemented" in text
    assert "## Problem" in text
    assert "## Decision" in text
    assert "## Alternatives considered" in text
    assert "## Consequences" in text
    assert "docs/validation/" in text
    assert "v4.0" in text


def test_v4_lifespan_plan_consumes_handbooks_equivalent() -> None:
    path = (
        ROOT
        / "docs"
        / "releases"
        / "v4"
        / "v4.0"
        / "plans"
        / "v4.0.0-docs-lifespan-tree-and-enforcement.md"
    )
    text = _read(path)
    assert "has no equivalent" not in text
    assert "docs/releases/v3/v3.21/plans/v3.21.0-plan-implement-lifecycle-and-docs-architecture.md" in text
    assert "docs/archives/v<M>/v<M>.<m>/handbooks/" in text
    assert "regenerate-and-fail-on-stale" in text
    assert "docs/handbooks/" in text
