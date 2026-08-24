"""Aggregate test: every framework-declaring skill ships references/standards.md.

One data-driven test over the live catalog, not one test per skill (test-retention
policy in AGENTS.md). Each declared frontmatter ID must appear in that file.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_SKILLS = REPO_ROOT / "catalog" / "skills"
BUILDER_PATH = REPO_ROOT / "scripts" / "build_framework_coverage.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_framework_coverage", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_framework_skill_has_standards_naming_every_id() -> None:
    builder = _load_builder()
    failures: list[str] = []
    scanned = 0
    for skill_md in sorted(CATALOG_SKILLS.rglob("SKILL.md")):
        content = skill_md.read_text(encoding="utf-8")
        tags = builder.parse_framework_tags(content)
        if not tags:
            continue
        scanned += 1
        declared_ids: list[str] = []
        for ids in tags.values():
            declared_ids.extend(ids)
        standards = skill_md.parent / "references" / "standards.md"
        if not standards.is_file():
            failures.append(f"{skill_md.parent.name}: missing references/standards.md")
            continue
        body = standards.read_text(encoding="utf-8")
        missing = [control_id for control_id in declared_ids if control_id not in body]
        if missing:
            failures.append(
                f"{skill_md.parent.name}: references/standards.md omits {missing}"
            )
    assert scanned > 0, "expected at least one framework-declaring skill in the catalog"
    assert not failures, "framework-declaring skills missing standards coverage:\n" + "\n".join(
        failures
    )
