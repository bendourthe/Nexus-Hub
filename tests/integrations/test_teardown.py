"""Tests for the teardown / uninstall path."""

from __future__ import annotations

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext


def test_teardown_removes_tracked_files(install_ctx: InstallContext):
    integ = get("opencode")
    integ.install(install_ctx)
    files_before = sum(1 for _ in install_ctx.target_root.rglob("*") if _.is_file())
    assert files_before > 0

    integ.teardown(install_ctx)
    assert install_ctx.manifest.files_for("opencode") == []


def test_path_traversal_rejected_in_safe_resolve():
    from scripts.lib.integrations.base import _safe_resolve
    import pytest
    from pathlib import Path

    root = Path("/tmp/safe-resolve-root").resolve()
    root.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError):
        _safe_resolve(root, "../etc/passwd")
    with pytest.raises(ValueError):
        _safe_resolve(root, "/etc/passwd")
    with pytest.raises(ValueError):
        _safe_resolve(root, "foo\x00bar")
    with pytest.raises(ValueError):
        _safe_resolve(root, "\\\\server\\share\\evil")

    resolved = _safe_resolve(root, "subdir/file.md")
    assert resolved == (root / "subdir" / "file.md").resolve()
