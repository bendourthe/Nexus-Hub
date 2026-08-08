"""Tests for the `nexus-hub init` runner subcommand.

Covers the wire_project_surfaces() hook introduced in v2.2.0 Phase 3 sub-task
3.2: a global install user can run `nexus-hub init` against any project root
and get the project-local surfaces (Cursor rules, Claude settings.json stub)
bootstrapped without rerunning the full workspace install.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations.runner import main as runner_main  # noqa: E402


def _run_init(target: Path, *extra: str) -> int:
    return runner_main(["init", "--target", str(target), "--quiet", *extra])


def test_init_creates_cursor_rule_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    exit_code = _run_init(project)
    assert exit_code == 0
    rule = project / ".cursor" / "rules" / "nexus-hub.mdc"
    assert rule.is_file()
    body = rule.read_text(encoding="utf-8")
    assert "name: nexus-hub" in body
    assert "Nexus-Hub project rules" in body


def test_init_is_idempotent_for_cursor(tmp_path: Path) -> None:
    """A second `nexus-hub init` reports the rule file as `unchanged`."""
    project = tmp_path / "project"
    project.mkdir()
    _run_init(project)
    # Snapshot the bytes; re-running must not mutate them.
    rule = project / ".cursor" / "rules" / "nexus-hub.mdc"
    snapshot = rule.read_bytes()
    _run_init(project)
    assert rule.read_bytes() == snapshot


def test_init_creates_claude_settings_stub(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    _run_init(project)
    settings = project / ".claude" / "settings.json"
    assert settings.is_file()
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert "permissions" in data
    assert "allow" in data["permissions"]
    # The stub seeds its effort/model/env defaults from the DECLARED source
    # (configs/platform-defaults.json) rather than a hardcoded literal, so this
    # asserts consistency with that source instead of restating the value. That
    # makes it a real consistency test rather than a second place to edit when
    # the default moves (v3.16.0 Phase 1).
    declared = json.loads(
        (REPO_ROOT / "configs" / "platform-defaults.json").read_text(encoding="utf-8")
    )["platforms"]["claude"]["settings"]
    assert data["effortLevel"] == declared["effortLevel"]
    assert data["model"] == declared["model"]
    assert (
        data["env"]["CLAUDE_CODE_EFFORT_LEVEL"]
        == declared["env"]["CLAUDE_CODE_EFFORT_LEVEL"]
    )


def test_init_never_overwrites_existing_claude_settings(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".claude").mkdir(parents=True)
    settings = project / ".claude" / "settings.json"
    custom = '{"permissions": {"allow": ["Read"]}, "_user_managed": true}\n'
    settings.write_text(custom, encoding="utf-8")
    _run_init(project)
    # The user's file must be preserved byte-identically.
    assert settings.read_text(encoding="utf-8") == custom


def test_init_dry_run_does_not_write(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    _run_init(project, "--dry-run")
    rule = project / ".cursor" / "rules" / "nexus-hub.mdc"
    settings = project / ".claude" / "settings.json"
    assert not rule.exists()
    assert not settings.exists()


def test_default_wire_project_surfaces_returns_none(tmp_path: Path) -> None:
    """Every integration without an override returns None from the base hook.

    Uses dry_run=True so the cursor / claude overrides also do not touch
    disk - the only signal we need is the return value (None vs. WriteResult).
    """
    from scripts.lib.integrations import INTEGRATION_REGISTRY
    from scripts.lib.integrations.base import InstallContext
    from scripts.lib.integrations.manifest import InstallManifest

    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=tmp_path,
        scope="workspace",
        dry_run=True,
        manifest=InstallManifest(),
    )

    # antigravity2 overrides the hook (v3.3.4): the Antigravity 2.0 IDE reads
    # slash commands only from the open project's .agents/, so `nexus-hub init`
    # seeds that tree per-repo (there is no global command surface to mirror).
    # copilot overrides it too (since v3.11.0): it returns a WriteResult (a note
    # when the opt-in is unset, or seeded .github/skills wrappers when set), never None.
    overrides = {"cursor", "claude", "antigravity2", "copilot"}
    for key, integ in INTEGRATION_REGISTRY.items():
        out = integ.wire_project_surfaces(ctx)
        if key in overrides:
            assert out is not None, f"{key} must override wire_project_surfaces"
        else:
            assert out is None, f"{key} unexpectedly overrode wire_project_surfaces"
