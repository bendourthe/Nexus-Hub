"""Path-traversal defense tests for the installer's registrar logic.

The installer scripts (`scripts/installer.sh` on POSIX, `scripts/installer.ps1`
on Windows) both rely on the host's path-resolution primitives to collapse `..`
segments before any write. This test suite exercises that invariant via a
Python helper (`_path_safety.resolve_under`) that mirrors the same semantics
without spinning up a full installer run.

The catalog skill / command / template directory tree is controlled by the
repo, so the realistic threat is a malicious *contributor* adding a folder
named, e.g., `../etc/passwd` to `catalog/skills/`. The installer must refuse
such a name, regardless of which platform it runs on. These tests pin that
behavior in CI.

Related plan reference: docs/archive/v2/v2.1.0/plans/adoption-spec-kit.md (Phase 9
sub-task 9.4). The plan adapts the Spec-Kit `tests/test_registrar_path_traversal.py`
pattern -- per the Reverse-Engineering Attribution Rule in AGENTS.md, the
upstream name is documented in the comparison report at
docs/archive/v2/v2.0.0/comparison-spec-kit.md, not in the artifact itself.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Make the helper importable without requiring tests/ to be on sys.path globally.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _path_safety import PathTraversalError, is_safe_candidate, resolve_under  # noqa: E402


@pytest.fixture
def install_root(tmp_path: Path) -> Path:
    """Throwaway install root for each test case."""
    root = tmp_path / "nexus-hub-install"
    root.mkdir()
    return root


class TestRejectMaliciousNames:
    """Cases 1-4 from docs/archive/v2/v2.1.0/plans/adoption-spec-kit.md sub-task 9.4."""

    def test_rejects_dotdot_traversal(self, install_root: Path) -> None:
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, "../etc/passwd")

    def test_rejects_deeper_dotdot_traversal(self, install_root: Path) -> None:
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, "skills/../../../etc/passwd")

    def test_rejects_posix_absolute_path(self, install_root: Path) -> None:
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, "/etc/passwd")

    def test_rejects_null_byte(self, install_root: Path) -> None:
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, "foo\x00bar")

    def test_rejects_unc_path(self, install_root: Path) -> None:
        # UNC prefix is rejected on every platform because Nexus-Hub never
        # writes to remote shares from the installer.
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, "\\\\server\\share\\evil")

    def test_rejects_unc_forward_slashes(self, install_root: Path) -> None:
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, "//server/share/evil")


class TestRejectWindowsSpecificAbsolutePaths:
    """Windows drive-letter and backslash forms are rejected on every platform.

    The helper is intentionally OS-agnostic -- we do not want a malicious
    catalog committed on Linux to suddenly become exploitable when the
    installer runs on Windows.
    """

    def test_rejects_drive_letter(self, install_root: Path) -> None:
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, "C:\\Windows\\System32\\evil")

    def test_rejects_backslash_root(self, install_root: Path) -> None:
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, "\\Windows\\System32\\evil")


class TestRejectMalformedInputs:
    def test_rejects_empty_string(self, install_root: Path) -> None:
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, "")

    def test_rejects_whitespace_only(self, install_root: Path) -> None:
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, "   ")

    def test_rejects_none(self, install_root: Path) -> None:
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, None)  # type: ignore[arg-type]

    def test_rejects_non_string(self, install_root: Path) -> None:
        with pytest.raises(PathTraversalError):
            resolve_under(install_root, 123)  # type: ignore[arg-type]


class TestAcceptLegitimateNames:
    """Sanity checks: well-formed catalog names must still resolve successfully."""

    def test_accepts_simple_skill_name(self, install_root: Path) -> None:
        resolved = resolve_under(install_root, "spec-driven-development")
        assert resolved.parent == install_root.resolve()
        assert resolved.name == "spec-driven-development"

    def test_accepts_nested_category_and_skill(self, install_root: Path) -> None:
        resolved = resolve_under(install_root, "developer-experience/spec-driven-development")
        assert resolved.is_relative_to(install_root.resolve())

    def test_accepts_skill_md_target(self, install_root: Path) -> None:
        resolved = resolve_under(
            install_root, "workflow/project-constitution/SKILL.md"
        )
        assert resolved.is_relative_to(install_root.resolve())

    def test_accepts_dot_inside_filename(self, install_root: Path) -> None:
        # Files named with dots (markdownlint-cli2.jsonc, etc.) must still resolve.
        resolved = resolve_under(install_root, "style-guides/markdownlint-cli2.jsonc")
        assert resolved.is_relative_to(install_root.resolve())


class TestIsSafeCandidate:
    """The boolean wrapper exposes the same invariant for non-raising call sites."""

    def test_returns_true_for_legitimate_name(self, install_root: Path) -> None:
        assert is_safe_candidate(install_root, "spec-driven-development") is True

    def test_returns_false_for_dotdot(self, install_root: Path) -> None:
        assert is_safe_candidate(install_root, "../etc/passwd") is False

    def test_returns_false_for_null_byte(self, install_root: Path) -> None:
        assert is_safe_candidate(install_root, "foo\x00bar") is False
