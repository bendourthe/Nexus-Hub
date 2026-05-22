"""Tests for the `check` runner subcommand and `dry_run()` hook.

The `check` subcommand is CI-friendly install-drift detection:

* On a fresh install state, every integration reports `created` -> exit 1.
* After a real install, a re-run with `check` reports only `unchanged` /
  `kept` -> exit 0.
* `check` never touches disk during the call.
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations.runner import main as runner_main  # noqa: E402


def _snapshot(root: Path) -> set[Path]:
    return {p.relative_to(root) for p in root.rglob("*")}


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    p = tmp_path / "workspace"
    p.mkdir()
    return p


def _install_workspace_for(key: str, workspace: Path, quiet: bool = True) -> int:
    args = [
        "install",
        "--scope",
        "workspace",
        "--integrations",
        key,
        "--target",
        str(workspace),
    ]
    if quiet:
        args.append("--quiet")
    return runner_main(args)


def _check_workspace_for(key: str, workspace: Path, quiet: bool = True) -> tuple[int, str]:
    args = [
        "check",
        "--scope",
        "workspace",
        "--target",
        str(workspace),
        "--integrations",
        key,
    ]
    if quiet:
        args.append("--quiet")
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = runner_main(args)
    return exit_code, buf.getvalue()


def test_check_returns_non_zero_on_fresh_state(workspace: Path) -> None:
    """Fresh state -> every file would be created -> exit 1."""
    exit_code, _ = _check_workspace_for("cursor", workspace)
    assert exit_code == 1


def test_check_returns_zero_after_install(workspace: Path) -> None:
    """Post-install -> re-check sees all `unchanged` / `kept` -> exit 0."""
    install_rc = _install_workspace_for("cursor", workspace)
    assert install_rc == 0
    exit_code, _ = _check_workspace_for("cursor", workspace)
    assert exit_code == 0


def test_check_does_not_write_anything(workspace: Path, tmp_path: Path) -> None:
    """--check on a fresh project must not mutate the filesystem."""
    before = _snapshot(tmp_path)
    _check_workspace_for("cursor", workspace)
    after = _snapshot(tmp_path)
    assert before == after, (
        f"check mutated disk; new entries: {sorted(after - before)}"
    )


def test_check_runs_for_all_integrations(workspace: Path) -> None:
    """Default invocation walks every registered integration."""
    exit_code, output = _check_workspace_for("", workspace, quiet=False)  # type: ignore[arg-type]
    # `--integrations ""` is rejected by the resolver; use the default by
    # passing through main() with no --integrations.
    args = ["check", "--scope", "workspace", "--target", str(workspace)]
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = runner_main(args)
    output = buf.getvalue()
    # Should mention every registered integration's display_name.
    assert "Cursor" in output
    assert "Claude" in output
    assert exit_code in (0, 1)


def test_dry_run_method_returns_writeresult() -> None:
    """The Python-side dry_run() hook returns a WriteResult, not None."""
    from scripts.lib.integrations import get
    from scripts.lib.integrations.base import InstallContext
    from scripts.lib.integrations.manifest import InstallManifest
    from scripts.lib.integrations.result import WriteResult

    integ = get("cursor")
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=REPO_ROOT,
        scope="workspace",
        overwrite=False,
        dry_run=False,  # dry_run() forces this to True internally
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "test"},
    )
    out = integ.dry_run(ctx)
    assert isinstance(out, WriteResult)


def test_dry_run_matches_install_actions(workspace: Path) -> None:
    """The action histogram from dry_run on a fresh state matches the
    histogram from install() on a separately-cloned fresh state.
    """
    from scripts.lib.integrations import get
    from scripts.lib.integrations.base import InstallContext
    from scripts.lib.integrations.manifest import InstallManifest

    integ = get("cursor")

    def _new_ctx(target: Path, dry: bool) -> InstallContext:
        return InstallContext(
            repo_root=REPO_ROOT,
            target_root=target,
            scope="workspace",
            overwrite=False,
            dry_run=dry,
            manifest=InstallManifest(),
            template_vars={"PROJECT_NAME": "test"},
        )

    dry_target = workspace
    install_target = workspace.parent / "install-clone"
    install_target.mkdir()

    dry_result = integ.dry_run(_new_ctx(dry_target, dry=False))
    install_result = integ.install(_new_ctx(install_target, dry=False))

    # Compare the action histogram. The path strings differ because the two
    # contexts have different target_roots, so we compare counts only.
    assert dry_result.actions_by_kind() == install_result.actions_by_kind()
