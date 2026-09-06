"""Tests for scope-aware target-root resolution and manifest-write hardening.

Covers the v3.14.1 installer-hotfix contract in scripts/lib/integrations/runner.py:

* ``_resolve_target_root`` precedence: an explicit ``--target`` wins; otherwise a
  ``--scope global`` invocation resolves to the user home; otherwise the CWD.
* The manifest path derived from a global-scope resolution lands under the user
  home, NOT under the process CWD (the pre-fix WinError-5 behavior).
* ``cmd_install`` for global scope with no ``--target`` writes the manifest under
  the user home even when the process CWD is a foreign directory, exiting 0 with
  no traceback.
* A manifest-write ``OSError`` (e.g. ``PermissionError``) degrades to a single
  stderr warning while ``cmd_install`` still returns 0.

Follows the import + monkeypatch conventions in test_legacy_cleanups.py: import
from ``scripts.lib.integrations...`` and monkeypatch ``Path.home`` via
``staticmethod`` so the tests never touch the real user home.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from scripts.lib.integrations import runner
from scripts.lib.integrations.manifest import InstallManifest
from scripts.lib.integrations.result import WriteResult


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


def _install_args(**overrides) -> argparse.Namespace:
    """Build a fully-populated Namespace for cmd_install (all attrs it reads)."""
    base = dict(
        integrations="claude",
        target=None,
        scope="global",
        overwrite=False,
        dry_run=False,
        quiet=True,
        project_name=None,
        var=None,
        languages=None,
        instruction_only=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


class _StubIntegration:
    """A no-op integration so cmd_install exercises only path/manifest logic."""

    display_name = "Stub"

    def install(self, ctx) -> WriteResult:
        return WriteResult()


@pytest.fixture
def stub_integration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace runner.get so cmd_install never runs a real per-platform install."""
    monkeypatch.setattr(runner, "get", lambda key: _StubIntegration())


# ---------------------------------------------------------------------------
# _resolve_target_root precedence
# ---------------------------------------------------------------------------


def test_global_scope_resolves_to_home(
    fake_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """global scope + no target -> user home, regardless of the process CWD."""
    foreign = tmp_path / "foreign_cwd"
    foreign.mkdir()
    monkeypatch.chdir(foreign)
    args = argparse.Namespace(target=None, scope="global")

    root = runner._resolve_target_root(args)

    assert root == fake_home.resolve()
    manifest_path = runner._manifest_path(root)
    assert (
        manifest_path
        == fake_home.resolve() / ".nexus-hub" / "install-manifest.json"
    )
    # Decisively NOT under the process CWD (the pre-fix, WinError-5 behavior).
    assert foreign.resolve() not in manifest_path.parents


def test_workspace_scope_resolves_to_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """workspace scope + no target -> the process CWD (unchanged behavior)."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)
    args = argparse.Namespace(target=None, scope="workspace")

    assert runner._resolve_target_root(args) == workspace.resolve()


@pytest.mark.parametrize("scope", ["global", "workspace"])
def test_explicit_target_always_wins(
    tmp_path: Path, fake_home: Path, scope: str
) -> None:
    """An explicit --target overrides both scopes."""
    explicit = tmp_path / "explicit"
    explicit.mkdir()
    args = argparse.Namespace(target=str(explicit), scope=scope)

    assert runner._resolve_target_root(args) == explicit.resolve()


def test_missing_scope_attr_defaults_to_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Subcommands with no --scope flag (init/doctor/repair/list-installed) keep
    their CWD default -- getattr(args, "scope", None) is None, not "global".
    """
    workspace = tmp_path / "ws_no_scope"
    workspace.mkdir()
    monkeypatch.chdir(workspace)
    args = argparse.Namespace(target=None)  # no `scope` attribute at all

    assert runner._resolve_target_root(args) == workspace.resolve()


# ---------------------------------------------------------------------------
# cmd_install: manifest path (global) + graceful degradation
# ---------------------------------------------------------------------------


def test_global_install_writes_manifest_under_home(
    fake_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stub_integration: None,
) -> None:
    """A global install from a foreign CWD writes the manifest under home, exit 0."""
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    monkeypatch.chdir(foreign)

    rc = runner.cmd_install(_install_args(scope="global", target=None))

    assert rc == 0
    assert (fake_home / ".nexus-hub" / "install-manifest.json").exists()
    assert not (foreign / ".nexus-hub" / "install-manifest.json").exists()


def test_manifest_write_failure_degrades_to_warning(
    fake_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stub_integration: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A manifest-write OSError warns to stderr; cmd_install still returns 0."""

    def _boom(self, path):  # noqa: ANN001 - test double
        raise PermissionError("[WinError 5] Access is denied")

    monkeypatch.setattr(InstallManifest, "save", _boom)
    monkeypatch.chdir(tmp_path)

    rc = runner.cmd_install(_install_args(scope="global", target=None))

    assert rc == 0
    err = capsys.readouterr().err
    assert "could not write install manifest" in err
    assert "install content is unaffected" in err
