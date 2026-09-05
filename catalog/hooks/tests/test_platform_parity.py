"""Platform-parity audit for the 5 base AI-instruction templates.

Enforces memory/project_platform_agnostic.md: any rule, skill, command, or hook
change must be mirrored across all 5 platform templates (Claude, Gemini, Codex,
Cursor, OpenCode). This test codifies the verbatim-shared rule set so future
edits cannot silently drift one template out of sync.

Run with: pytest catalog/hooks/tests/test_platform_parity.py
Also runnable directly: python catalog/hooks/tests/test_platform_parity.py
"""
from __future__ import annotations

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
TEMPLATE_DIR = REPO_ROOT / "templates" / "ai-instructions"

PLATFORM_TEMPLATES = [
    "base-claude.md",
    "base-gemini.md",
    "base-codex.md",
    "base-cursor.md",
    "base-opencode.md",
]

# Rules every template MUST carry verbatim.
# Each entry is a substring match against the template body. Keep these short
# enough to survive minor reformatting but long enough to be unambiguous.
SHARED_RULES = [
    # Opus 4.7 batched clarifying-questions (Phase 1.5)
    "batch all clarifying questions into the first turn",
    # ASCII-only commit messages (v0.9.4 cross-platform policy)
    "Commit messages must be ASCII-only",
    # docs/todos.md tracker convention (v0.9.4)
    "docs/todos.md` as the project progress tracker",
    # Root-cause posture
    "Find root causes; no temporary fixes",
    # Scope discipline
    "Every changed line must trace directly to the user's request",
    # Output minimization
    "Suppress verbose progress bars, banners, and informational logs",
    # Line-wrap policy (prevents hard-wrapped markdown). v4.5.0 moved this rule
    # into the shared `## Writing Discipline` block, which is the phrasing every
    # template now carries; base-claude.md no longer has the older bullet.
    "no hard-wrapping of paragraph text",
]

# Rules the stale pre-v0.9.7 variant must NOT contain anywhere. Catches
# reintroduction regressions.
BANNED_SUBSTRINGS = [
    # The v0.9.6-era unbounded clarifying-questions rule
    "Ask clarifying questions before coding if requirements are ambiguous",
]


def _read(name: str) -> str:
    path = TEMPLATE_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Missing platform template: {path}")
    return path.read_text(encoding="utf-8")


def test_all_templates_exist():
    for name in PLATFORM_TEMPLATES:
        assert (TEMPLATE_DIR / name).is_file(), f"Missing template: {name}"


def test_shared_rules_present_in_all_templates():
    failures = []
    for name in PLATFORM_TEMPLATES:
        body = _read(name)
        for rule in SHARED_RULES:
            if rule not in body:
                failures.append((name, rule))
    if failures:
        lines = ["Shared rule missing from one or more templates:"]
        for name, rule in failures:
            lines.append(f"  {name}: {rule!r}")
        raise AssertionError("\n".join(lines))


def test_banned_substrings_absent_in_all_templates():
    failures = []
    for name in PLATFORM_TEMPLATES:
        body = _read(name)
        for banned in BANNED_SUBSTRINGS:
            if banned in body:
                failures.append((name, banned))
    if failures:
        lines = ["Banned (stale) substring present in one or more templates:"]
        for name, banned in failures:
            lines.append(f"  {name}: {banned!r}")
        raise AssertionError("\n".join(lines))


def test_effort_level_language_consistency():
    """None of the templates should hardcode a specific effortLevel default.

    Rationale: effortLevel is a harness setting (catalog/hooks/settings.json),
    not a platform-template setting. Embedding a hardcoded default here would
    create a second source of truth that drifts from settings.json. Templates
    may reference `effortLevel` as a concept but must not declare a default
    value.
    """
    allowed_phrases = [
        # Conceptual references are fine; only hardcoded defaults are banned.
    ]
    banned_defaults = [
        '"effortLevel": "xhigh"',
        '"effortLevel": "high"',
        '"effortLevel": "max"',
        '"effortLevel": "medium"',
        '"effortLevel": "low"',
    ]
    failures = []
    for name in PLATFORM_TEMPLATES:
        body = _read(name)
        for banned in banned_defaults:
            if banned in body:
                failures.append((name, banned))
    if failures:
        lines = ["Hardcoded effortLevel default found in a platform template:"]
        for name, banned in failures:
            lines.append(f"  {name}: {banned!r}")
        raise AssertionError("\n".join(lines))


def _run_all():
    """Manual runner - mirrors what pytest would do, with simple output."""
    tests = [
        test_all_templates_exist,
        test_shared_rules_present_in_all_templates,
        test_banned_substrings_absent_in_all_templates,
        test_effort_level_language_consistency,
    ]
    failures = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {t.__name__}\n{e}")
        except Exception as e:
            failures += 1
            print(f"ERROR: {t.__name__}: {e}")
        else:
            print(f"OK: {t.__name__}")
    if failures:
        print(f"\n{failures} test(s) failed.")
        sys.exit(1)
    print(f"\nAll {len(tests)} platform-parity tests passed.")


if __name__ == "__main__":
    _run_all()
