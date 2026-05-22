"""Tests for the `print-config` runner subcommand and `print_config` hook.

Each registered integration must produce a Markdown readout that:

* names the integration's display_name and key in a top-level H1;
* lists the destination scope and target root;
* contains a File actions section;
* never touches disk during the call.
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

from scripts.lib.integrations import INTEGRATION_REGISTRY, list_keys  # noqa: E402
from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402
from scripts.lib.integrations.runner import main as runner_main  # noqa: E402


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


@pytest.mark.parametrize("key", sorted(INTEGRATION_REGISTRY.keys()))
def test_print_config_runs_without_touching_disk(
    key: str, fake_home: Path, tmp_path: Path
) -> None:
    project = tmp_path / "p"
    project.mkdir()
    snapshot_before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = runner_main([
            "print-config",
            key,
            "--scope",
            "workspace",
            "--target",
            str(project),
        ])
    output = buf.getvalue()
    assert exit_code == 0
    snapshot_after = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    assert snapshot_before == snapshot_after, (
        f"print-config for {key!r} mutated disk; "
        f"new entries: {set(snapshot_after) - set(snapshot_before)}"
    )
    assert output, f"print-config for {key!r} produced no output"
    assert "# " in output  # Has at least one H1.
    assert "File actions" in output
    assert key in output


def test_print_config_unknown_key_exits_non_zero(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    exit_code = runner_main(["print-config", "not-a-real-key", "--target", str(project)])
    assert exit_code == 1


def test_print_config_includes_rendered_instruction_body(
    fake_home: Path, tmp_path: Path
) -> None:
    """For MarkdownIntegration subclasses the output must include a rendered
    instruction body block so the user can paste it manually.
    """
    project = tmp_path / "p"
    project.mkdir()
    buf = io.StringIO()
    with redirect_stdout(buf):
        runner_main([
            "print-config",
            "claude",
            "--scope",
            "workspace",
            "--target",
            str(project),
        ])
    output = buf.getvalue()
    assert "Rendered instruction body" in output
    assert "```markdown" in output


def test_print_config_direct_hook_returns_string(fake_home: Path, tmp_path: Path) -> None:
    """The Python-side hook returns the readout string directly (no stdout)."""
    from scripts.lib.integrations import get

    integ = get("claude")
    project = tmp_path / "p"
    project.mkdir()
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=project,
        scope="workspace",
        overwrite=False,
        dry_run=True,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "test"},
    )
    body = integ.print_config(ctx)
    assert isinstance(body, str)
    assert body.startswith("# ")
    assert "claude" in body
    assert "File actions" in body
