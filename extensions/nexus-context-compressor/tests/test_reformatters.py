"""Semantic reformatters: git status, test failures, linter grouping."""

from __future__ import annotations

from nexus_context_compressor import compress_output
from nexus_context_compressor.reformatters import try_reformat
from nexus_context_compressor.tokens import count_tokens

_GIT_STATUS = """\
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
  (use "git add/rm <file>..." as appropriate to mark resolution)
  (use "git add --intent-to-add <file>..." to add a file, but not its content)
  (use "git restore --staged <file>..." to unstage)
  (use "git restore --source=HEAD --staged --worktree <file>..." to discard)
  (use "git checkout -- <file>..." to discard changes in working directory)
  (use "git add <file>..." to include in what will be committed)
	modified:   src/app/widget.py
	modified:   src/app/service.py
	modified:   src/app/routes.py
	modified:   src/app/models.py
	modified:   src/app/views.py
	modified:   tests/test_widget.py
	modified:   tests/test_service.py
	modified:   docs/guide.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
  (use "git add -N <file>..." to record intent to add)
  (use "git clean -n" to preview files that would be removed)
  (use "git clean -fd" to remove untracked files and directories)
	scratch.tmp
	notes.local.md
	debug.log

no changes added to commit (use "git add" and/or "git commit -a")
nothing added to commit but untracked files present (use "git add" to track)
"""

_PYTEST = """\
============================= test session starts ==============================
platform linux -- Python 3.12.4, pytest-8.2.0, pluggy-1.5.0
rootdir: /work
collected 40 items

tests/test_widget.py ..............F....                                 [ 50%]
tests/test_service.py .............F....                                 [100%]

=================================== FAILURES ===================================
__________________________ test_widget_renders_empty ___________________________
assert False
__________________________ test_service_retries_once ___________________________
assert False
=========================== short test summary info ============================
FAILED tests/test_widget.py::test_widget_renders_empty - assert False
FAILED tests/test_service.py::test_service_retries_once - assert False
========================= 2 failed, 38 passed in 1.20s =========================
"""

_PREFIX = (
    "C:/Users/BEDOURTHE/OneDrive - Supira/Documents/Supira/software/"
    "Nexus-Hub/extensions/nexus-context-compressor/src/nexus_context_compressor"
)
_RUFF = "\n".join(
    [
        f"{_PREFIX}/transforms/widget.py:{n}:1: F401 `os` imported but unused; consider removing it or using it in this module"
        for n in range(1, 9)
    ]
    + [
        f"{_PREFIX}/transforms/service.py:{n}:1: E501 line too long (120 > 88 characters); wrap or reflow this statement"
        for n in range(1, 9)
    ]
    + [
        f"{_PREFIX}/transforms/routes.py:{n}:1: B008 do not perform function calls in argument defaults; it is not safe"
        for n in range(1, 9)
    ]
    + [
        f"{_PREFIX}/transforms/models.py:{n}:1: E731 do not assign a lambda expression, use a def instead of this assignment"
        for n in range(1, 9)
    ]
    + ["Found 32 errors.", "[*] 12 fixable with the `--fix` option.", ""]
)


def _ratio(original: str, compressed: str) -> float:
    before = count_tokens(original)
    after = count_tokens(compressed)
    assert before > 0
    return 1.0 - (after / before)


def test_git_status_reformat_beats_sixty_percent() -> None:
    out = try_reformat(_GIT_STATUS)
    assert out is not None
    assert "branch: main" in out
    assert "modified (8):" in out
    assert _ratio(_GIT_STATUS, out) >= 0.60


def test_pytest_failures_only_beats_sixty_percent() -> None:
    out = try_reformat(_PYTEST)
    assert out is not None
    assert "2 failed, 38 passed" in out
    assert "test_widget_renders_empty" in out
    assert "platform linux" not in out
    assert _ratio(_PYTEST, out) >= 0.60


def test_ruff_grouped_by_file_beats_sixty_percent() -> None:
    out = try_reformat(_RUFF)
    assert out is not None
    assert "transforms/widget.py:" in out
    assert out.count("transforms/widget.py") == 1
    assert _ratio(_RUFF, out) >= 0.60


def test_compress_output_uses_the_git_status_reformatter() -> None:
    result = compress_output(_GIT_STATUS, persist=False)
    assert "branch: main" in result.text
    assert result.tokens_after < result.tokens_before


def test_prose_is_not_claimed_by_a_reformatter() -> None:
    assert try_reformat("just a short prose sentence about cats.") is None
