"""Tests for scripts/validate_solution_frontmatter.py."""

from __future__ import annotations

from pathlib import Path


SCRIPT = "validate_solution_frontmatter.py"


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


CLEAN_BUG_DOC = """\
---
title: "Auth token expiry test flakes under clock skew"
slug: flaky-auth-token-clock-skew
track: bug
category: bug
component: testing
tags: ["auth", "flaky-test", "time"]
created: 2026-05-30
updated: 2026-05-30
symptoms:
  - "test_auth_token_expiry intermittently returns 200 instead of 401"
root_cause: "race: token refresh vs request"
resolution_type: code-fix
related: []
---

# Auth token expiry test flakes under clock skew

Body text here.
"""

CLEAN_KNOWLEDGE_DOC = """\
---
title: "How the installer copies top-level scripts"
slug: installer-copies-scripts-by-explicit-name
track: knowledge
category: knowledge
component: tooling
tags: ["installer", "cross-platform"]
created: 2026-05-30
updated: 2026-05-30
applies_when: "adding a new scripts/<name>.py and wiring it into both installers"
related: []
---

# How the installer copies top-level scripts

Body text here.
"""


def test_clean_bug_doc_passes(tmp_path: Path, runner) -> None:
    write(tmp_path / "docs" / "solutions" / "bug" / "flaky.md", CLEAN_BUG_DOC)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_clean_knowledge_doc_passes(tmp_path: Path, runner) -> None:
    write(tmp_path / "docs" / "solutions" / "knowledge" / "installer.md", CLEAN_KNOWLEDGE_DOC)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_unquoted_hash_comment_is_flagged(tmp_path: Path, runner) -> None:
    doc = """\
---
title: Fix the #2 retry path
slug: bad-hash
track: knowledge
category: knowledge
component: backend
tags: ["retry"]
created: 2026-05-30
updated: 2026-05-30
applies_when: "retry path"
---

Body.
"""
    write(tmp_path / "docs" / "solutions" / "knowledge" / "bad.md", doc)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "title" in result.stderr
    assert "#" in result.stderr


def test_unquoted_colon_space_is_flagged(tmp_path: Path, runner) -> None:
    doc = """\
---
title: "ok title"
slug: bad-colon
track: bug
category: bug
component: backend
tags: ["x"]
created: 2026-05-30
updated: 2026-05-30
symptoms:
  - "a symptom"
root_cause: race: token refresh vs request
resolution_type: code-fix
---

Body.
"""
    write(tmp_path / "docs" / "solutions" / "bug" / "bad.md", doc)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "root_cause" in result.stderr


def test_reserved_indicator_list_item_is_flagged(tmp_path: Path, runner) -> None:
    doc = """\
---
title: "ok"
slug: bad-list
track: bug
category: bug
component: backend
tags: ["x"]
created: 2026-05-30
updated: 2026-05-30
symptoms:
  - "@reboot job never fired"
  - '*glob expansion blew up'
root_cause: "cron config"
resolution_type: config-change
---

Body.
"""
    # The first item is quoted (safe); the second begins with '*' but the
    # surrounding single quotes make it safe too -- so this doc is CLEAN.
    write(tmp_path / "docs" / "solutions" / "bug" / "ok-list.md", doc)
    assert runner(SCRIPT, tmp_path).returncode == 0

    bad = doc.replace("  - '*glob expansion blew up'", "  - *glob expansion blew up")
    write(tmp_path / "docs" / "solutions" / "bug" / "bad-list.md", bad)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "reserved" in result.stderr.lower()


def test_inline_flow_reserved_item_is_flagged(tmp_path: Path, runner) -> None:
    doc = CLEAN_KNOWLEDGE_DOC.replace(
        'tags: ["installer", "cross-platform"]', "tags: [#hotpath, installer]"
    )
    write(tmp_path / "docs" / "solutions" / "knowledge" / "flow.md", doc)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "tags" in result.stderr


def test_quoting_fixes_the_hazards(tmp_path: Path, runner) -> None:
    # A value containing both ' #' and ': ' is safe once quoted.
    doc = CLEAN_KNOWLEDGE_DOC.replace(
        'applies_when: "adding a new scripts/<name>.py and wiring it into both installers"',
        'applies_when: "when: handling a #tagged path"',
    )
    write(tmp_path / "docs" / "solutions" / "knowledge" / "quoted.md", doc)
    assert runner(SCRIPT, tmp_path).returncode == 0


def test_malformed_opening_delimiter_is_flagged(tmp_path: Path, runner) -> None:
    doc = "---frontmatter\ntitle: x\n---\n\nBody.\n"
    write(tmp_path / "docs" / "solutions" / "bug" / "malformed.md", doc)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "delimiter" in result.stderr.lower()


def test_missing_closing_delimiter_is_flagged(tmp_path: Path, runner) -> None:
    doc = "---\ntitle: x\nslug: y\n\nBody with no closing delimiter.\n"
    write(tmp_path / "docs" / "solutions" / "bug" / "noclose.md", doc)
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "closing" in result.stderr.lower()


def test_no_solutions_dir_passes(tmp_path: Path, runner) -> None:
    # No docs/solutions present -> nothing to scan -> clean.
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_explicit_missing_target_is_usage_error(tmp_path: Path, runner) -> None:
    result = runner(SCRIPT, tmp_path, [str(tmp_path / "does-not-exist.md")])
    assert result.returncode == 2
