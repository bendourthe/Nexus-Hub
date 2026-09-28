"""Redirected native config roots must stop a whole platform install."""

from __future__ import annotations

import os
import subprocess
from dataclasses import replace

import pytest

from scripts.lib.integrations import get
from scripts.lib.integrations._owned import _is_junction


@pytest.mark.parametrize(
    ("platform", "root_name", "scope"),
    [
        ("codex", ".codex", "global"),
        ("codex", ".codex", "workspace"),
        ("kimi", ".kimi-code", "global"),
        ("kimi", ".kimi-code", "workspace"),
    ],
)
def test_install_refuses_redirected_native_root(
    platform, root_name, scope, install_ctx, tmp_path
):
    profile = tmp_path / "profile"
    profile.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    native_root = profile / root_name
    try:
        native_root.symlink_to(external, target_is_directory=True)
    except OSError as exc:
        if os.name != "nt":
            pytest.skip(f"directory links unavailable: {exc}")
        junction = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(native_root), str(external)],
            text=True,
            capture_output=True,
            check=False,
        )
        if junction.returncode != 0:
            pytest.skip(f"junctions unavailable: {junction.stderr.strip()}")

    try:
        ctx = replace(
            install_ctx, target_root=profile, scope=scope,
            explicit_target=True, dry_run=True,
        )
        result = get(platform).install(ctx)

        assert result.files
        assert any(action.action == "kept" and action.reason for action in result.files)
        assert not list(external.iterdir())
    finally:
        if _is_junction(native_root):
            native_root.rmdir()
