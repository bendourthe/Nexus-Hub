"""Copilot agents/hooks and Hermes layout compatibility (v3.15.8 Phase 8).

Copilot personal instructions, native user/project agents, and native
user/project hooks are delivered directly through documented Copilot roots.

**Hermes (8.3)** is a regression guard. The upstream docs state that Hermes
"discovers skills by listing every subdirectory of the tap path and probing each
for SKILL.md", so the flattened layout is required rather than merely tolerated,
and a category-nested migration would break discovery outright.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.lib.integrations import _cascade_hook_compat as hook_compat
from scripts.lib.integrations import _copilot_native as copilot_native
from scripts.lib.integrations import _owned as owned_files
from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.copilot import (
    _MAX_AGENT_PROMPT_CHARS,
    CopilotIntegration,
)

COPILOT_DEFAULT_HOOK_LOCATIONS = (
    ".github/hooks",
    "~/.copilot/hooks",
)

# Copilot's default custom-agent locations, from the VS Code custom-agents doc.
COPILOT_DEFAULT_AGENT_LOCATIONS = (
    ".github/agents",
    "~/.copilot/agents",
)


@pytest.fixture
def copilot():
    return get("copilot")


@pytest.fixture
def hermes():
    return get("hermes")


@pytest.fixture
def copilot_home(tmp_path: Path) -> Path:
    return (tmp_path / "copilot-home" / ".copilot").resolve()


def _catalog_agents(ctx: InstallContext) -> list[Path]:
    return sorted((ctx.repo_root / "catalog" / "agents").glob("*.md"))


# ----- 8.1 Copilot global agents ------------------------------------------


def test_every_catalog_agent_is_delivered_verbatim(copilot, install_ctx, copilot_home):
    """Copilot reads the Claude frontmatter shape, so no transform may occur."""
    copilot._install_global_agents(copilot_home, install_ctx)
    dst_dir = copilot_home / "agents"
    for src in _catalog_agents(install_ctx):
        dst = dst_dir / f"{src.stem}.agent.md"
        assert dst.exists(), f"{src.name} was not delivered"
        assert dst.read_bytes() == src.read_bytes(), f"{src.name} was modified"


def test_agents_use_the_documented_agent_md_suffix(copilot, install_ctx, copilot_home):
    """`.agent.md` is the documented extension and the cross-level dedup key."""
    copilot._install_global_agents(copilot_home, install_ctx)
    delivered = sorted(p.name for p in (copilot_home / "agents").glob("*"))
    assert delivered
    assert all(name.endswith(".agent.md") for name in delivered)
    expected = sorted(f"{p.stem}.agent.md" for p in _catalog_agents(install_ctx))
    assert delivered == expected


def test_every_catalog_agent_satisfies_copilots_requirements(install_ctx):
    """description is required and the prompt is capped at 30,000 characters."""
    for md in _catalog_agents(install_ctx):
        reason = CopilotIntegration.agent_skip_reason(md.read_text(encoding="utf-8"))
        assert reason is None, f"{md.name}: {reason}"


@pytest.mark.parametrize(
    "markdown,expect_skip",
    [
        ("---\nname: ok\ndescription: d\n---\n\nBody.\n", False),
        ("---\ndescription: name is optional for Copilot\n---\n\nBody.\n", False),
        ("---\nname: ok\n---\n\nBody but no description.\n", True),
        ("---\nname: ok\ndescription: d\n---\n\n", True),
    ],
)
def test_agent_validation_matches_copilots_documented_rules(markdown, expect_skip):
    assert (CopilotIntegration.agent_skip_reason(markdown) is not None) is expect_skip


def test_agent_over_the_prompt_cap_is_skipped():
    body = "x" * (_MAX_AGENT_PROMPT_CHARS + 1)
    markdown = f"---\nname: huge\ndescription: d\n---\n\n{body}\n"
    reason = CopilotIntegration.agent_skip_reason(markdown)
    assert reason is not None and "cap" in reason


def test_user_authored_agent_is_never_overwritten(copilot, install_ctx, copilot_home):
    dst = copilot_home / "agents" / "planner.agent.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    mine = "---\nname: planner\ndescription: mine\n---\n\nMy own planner.\n"
    dst.write_text(mine, encoding="utf-8")

    copilot._install_global_agents(copilot_home, install_ctx)

    assert dst.read_text(encoding="utf-8") == mine


def test_owned_agent_is_repaired_and_reinstall_is_idempotent(
    copilot, install_ctx, copilot_home
):
    copilot._install_global_agents(copilot_home, install_ctx)
    dst = copilot_home / "agents" / "planner.agent.md"
    original = dst.read_bytes()
    dst.write_text("drifted", encoding="utf-8")

    copilot._install_global_agents(copilot_home, install_ctx)
    assert dst.read_bytes() == original

    copilot._install_global_agents(copilot_home, install_ctx)
    assert dst.read_bytes() == original


def test_dry_run_writes_no_agents(copilot, install_ctx, copilot_home):
    copilot._install_global_agents(copilot_home, replace(install_ctx, dry_run=True))
    assert not list((copilot_home / "agents").glob("*")) if (
        copilot_home / "agents"
    ).exists() else True


# ----- 8.1 detection gate --------------------------------------------------


def _isolate_global(monkeypatch, copilot_home: Path, vscode_user: Path | None = None):
    """Redirect BOTH global accessors so no test reaches the real home dir."""
    monkeypatch.setattr(
        "scripts.lib.integrations.copilot._vscode_user_dir", lambda: vscode_user
    )
    monkeypatch.setattr(
        "scripts.lib.integrations.copilot._copilot_home", lambda: copilot_home
    )


def test_global_install_is_skipped_when_copilot_is_absent(
    copilot, install_ctx, monkeypatch, copilot_home
):
    """No VS Code user dir and no ~/.copilot means Copilot is not installed."""
    _isolate_global(monkeypatch, copilot_home)

    result = copilot.install_global(install_ctx)

    assert result.detected is False
    assert not copilot_home.exists()


def test_absent_copilot_summary_claims_nothing_was_installed(
    copilot, install_ctx, monkeypatch, copilot_home
):
    _isolate_global(monkeypatch, copilot_home)

    result = copilot.install_global(install_ctx)

    assert result.files == []
    assert any("not detected" in note for note in result.notes)


def test_copilot_home_alone_is_enough_to_install_agents(
    copilot, install_ctx, monkeypatch, copilot_home
):
    """A Copilot CLI user with no VS Code install still gets the agents."""
    copilot_home.mkdir(parents=True)
    _isolate_global(monkeypatch, copilot_home)

    result = copilot.install_global(install_ctx)

    assert result.detected is True
    assert list((copilot_home / "agents").glob("*.agent.md"))


def test_global_install_never_touches_the_real_home(copilot, install_ctx, monkeypatch):
    """Both global surfaces must be reachable only through a patchable accessor.

    This is the guard for the defect Phase 8 introduced and then fixed: adding a
    second detection signal made an existing test write 23 agent files into the
    developer's actual `~/.copilot`.
    """
    called: list[str] = []
    monkeypatch.setattr(
        "scripts.lib.integrations.copilot._vscode_user_dir", lambda: None
    )
    real_agents = Path.home() / ".copilot" / "agents"

    # Snapshot rather than require emptiness. The original assertion demanded the
    # real ~/.copilot/agents hold no *.agent.md at all, which conflates "this test
    # wrote here" with "these files exist". A maintainer who has actually installed
    # Nexus-Hub globally legitimately has the catalog's agents there, so the old
    # form failed permanently for exactly the people most likely to run the suite.
    # What the guard is for is that THIS TEST must not add to that directory.
    before = (
        {path.name for path in real_agents.glob("*.agent.md")}
        if real_agents.is_dir()
        else set()
    )

    def _fake_home() -> Path:
        called.append("copilot_home")
        return install_ctx.target_root / "isolated" / ".copilot"

    monkeypatch.setattr("scripts.lib.integrations.copilot._copilot_home", _fake_home)
    copilot.install_global(install_ctx)

    assert called, "install_global did not route through _copilot_home"

    after = (
        {path.name for path in real_agents.glob("*.agent.md")}
        if real_agents.is_dir()
        else set()
    )
    assert after == before, (
        "install_global wrote agent files into the real home: "
        f"{sorted(after - before)}"
    )


# ----- 8.2 native personal/project instructions, agents, and hooks --------


def test_copilot_declares_owned_native_hook_surface(copilot):
    assert copilot.config.get("hooks_supported") is True
    assert copilot.config["hooks_subdir"] == "hooks"


def test_github_hooks_and_agents_are_written(copilot, install_ctx):
    copilot.install_workspace(install_ctx)
    github = install_ctx.target_root / ".github"
    assert list((github / "agents").glob("*.agent.md"))
    hook_file = github / "hooks" / "nexus-hub.json"
    assert hook_file.is_file()
    hooks = json.loads(hook_file.read_text(encoding="utf-8"))
    assert hooks["version"] == 1
    assert {"PreToolUse", "PostToolUse", "Stop"}.issubset(hooks["hooks"])
    first = hooks["hooks"]["PreToolUse"][0]
    assert first["type"] == "command"
    assert "bash" in first and "powershell" in first
    assert ".github/hooks/nexus-hub-scripts" in first["bash"]
    assert "copilot-hook-compat.py" in first["bash"]
    assert (github / "hooks" / "nexus-hub-scripts" / "copilot-hook-compat.py").is_file()

    compressor = next(
        entry
        for entry in hooks["hooks"]["PreToolUse"]
        if "compress-output" in entry["bash"]
    )
    assert "--handler compress-output.sh --" in compressor["bash"]
    assert "--handler compress-output.sh --" in compressor["powershell"]

    rewrite = next(
        entry
        for entry in hooks["hooks"]["PreToolUse"]
        if "rewrite-command" in entry["bash"]
    )
    scripts = github / "hooks" / "nexus-hub-scripts"
    bash_digest = hashlib.sha256((scripts / "rewrite-command.sh").read_bytes()).hexdigest()
    powershell_digest = hashlib.sha256(
        (scripts / "rewrite-command.ps1").read_bytes()
    ).hexdigest()
    assert (
        f"--handler rewrite-command.sh --handler-sha256 {bash_digest} -- bash"
        in rewrite["bash"]
    )
    assert (
        "--handler rewrite-command.sh "
        f"--handler-sha256 {powershell_digest} -- powershell"
        in rewrite["powershell"]
    )
    assert "rewrite-command.ps1" in rewrite["powershell"]


def test_copilot_reinstall_refreshes_owned_hook_bytes_and_digest(
    copilot, install_ctx
):
    copilot.install_workspace(install_ctx)
    src_hooks = install_ctx.repo_root / "catalog" / "hooks"
    scripts = install_ctx.target_root / ".github" / "hooks" / "nexus-hub-scripts"
    rewrite = scripts / "rewrite-command.sh"
    compat = scripts / "copilot-hook-compat.py"
    rewrite.write_bytes(b"stale managed rewrite\n")
    compat.write_bytes(b"stale managed bridge\n")

    result = copilot.install_workspace(install_ctx)

    assert rewrite.read_bytes() == (src_hooks / rewrite.name).read_bytes()
    assert compat.read_bytes() == (
        install_ctx.repo_root
        / "scripts"
        / "lib"
        / "integrations"
        / "_cascade_hook_compat.py"
    ).read_bytes()
    assert {action.action for action in result.files if action.path in {str(rewrite), str(compat)}} == {
        "updated"
    }
    digest = hashlib.sha256(rewrite.read_bytes()).hexdigest()
    hook_file = install_ctx.target_root / ".github" / "hooks" / "nexus-hub.json"
    payload = json.loads(hook_file.read_text(encoding="utf-8"))
    rewrite_entry = next(
        entry
        for entry in payload["hooks"]["PreToolUse"]
        if "rewrite-command" in entry["bash"]
    )
    assert f"--handler-sha256 {digest}" in rewrite_entry["bash"]
    assert hook_compat._copilot_permission_authoritative(
        "rewrite-command.sh",
        ["bash", str(rewrite)],
        digest,
        compat_path=compat,
    )
    assert install_ctx.manifest.files_for("copilot").count(str(rewrite)) == 1


def test_copilot_reinstall_replaces_owned_hard_link_without_touching_external(
    copilot, install_ctx
):
    copilot.install_workspace(install_ctx)
    rewrite = (
        install_ctx.target_root
        / ".github"
        / "hooks"
        / "nexus-hub-scripts"
        / "rewrite-command.sh"
    )
    external = install_ctx.target_root / "external-hard-link-target.sh"
    sentinel = b"external hard-link bytes must survive\n"
    external.write_bytes(sentinel)
    rewrite.unlink()
    try:
        os.link(external, rewrite)
    except OSError as exc:
        pytest.skip(f"hard links unavailable: {exc}")
    assert rewrite.samefile(external)

    result = copilot.install_workspace(install_ctx)

    assert external.read_bytes() == sentinel
    assert rewrite.read_bytes() == (
        install_ctx.repo_root / "catalog" / "hooks" / rewrite.name
    ).read_bytes()
    assert not rewrite.samefile(external)
    assert [action.action for action in result.files if action.path == str(rewrite)] == [
        "updated"
    ]
    assert install_ctx.manifest.files_for("copilot").count(str(rewrite)) == 1


def test_copilot_reinstall_replaces_owned_symlink_without_touching_external(
    copilot, install_ctx
):
    copilot.install_workspace(install_ctx)
    rewrite = (
        install_ctx.target_root
        / ".github"
        / "hooks"
        / "nexus-hub-scripts"
        / "rewrite-command.sh"
    )
    external = install_ctx.target_root / "external-symlink-target.sh"
    sentinel = b"external symlink bytes must survive\n"
    external.write_bytes(sentinel)
    rewrite.unlink()
    try:
        rewrite.symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    assert rewrite.is_symlink()

    result = copilot.install_workspace(install_ctx)

    assert external.read_bytes() == sentinel
    assert not rewrite.is_symlink()
    assert rewrite.read_bytes() == (
        install_ctx.repo_root / "catalog" / "hooks" / rewrite.name
    ).read_bytes()
    assert [action.action for action in result.files if action.path == str(rewrite)] == [
        "updated"
    ]
    assert install_ctx.manifest.files_for("copilot").count(str(rewrite)) == 1


def test_copilot_reinstall_refuses_parent_symlink_without_touching_external(
    copilot, install_ctx
):
    copilot.install_workspace(install_ctx)
    scripts = (
        install_ctx.target_root / ".github" / "hooks" / "nexus-hub-scripts"
    )
    rewrite = scripts / "rewrite-command.sh"
    external = install_ctx.target_root / "external-parent-symlink"
    sentinel = b"external parent-symlink bytes must survive\n"
    shutil.rmtree(scripts)
    external.mkdir()
    (external / rewrite.name).write_bytes(sentinel)
    try:
        scripts.symlink_to(external, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks unavailable: {exc}")

    result = copilot.install_workspace(install_ctx)

    assert sorted(path.name for path in external.iterdir()) == [rewrite.name]
    assert (external / rewrite.name).read_bytes() == sentinel
    assert scripts.is_symlink()
    assert [action.action for action in result.files if action.path == str(rewrite)] == [
        "kept"
    ]
    assert install_ctx.manifest.files_for("copilot").count(str(rewrite)) == 1


@pytest.mark.skipif(os.name != "nt", reason="Windows junction regression")
def test_copilot_reinstall_refuses_parent_junction_without_touching_external(
    copilot, install_ctx
):
    copilot.install_workspace(install_ctx)
    scripts = (
        install_ctx.target_root / ".github" / "hooks" / "nexus-hub-scripts"
    )
    rewrite = scripts / "rewrite-command.sh"
    external = install_ctx.target_root / "external-parent-junction"
    sentinel = b"external parent-junction bytes must survive\n"
    shutil.rmtree(scripts)
    external.mkdir()
    (external / rewrite.name).write_bytes(sentinel)
    junction = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(scripts), str(external)],
        text=True,
        capture_output=True,
        check=False,
    )
    if junction.returncode != 0:
        pytest.skip(f"junctions unavailable: {junction.stderr.strip()}")
    assert owned_files._is_junction(scripts)

    try:
        result = copilot.install_workspace(install_ctx)

        assert sorted(path.name for path in external.iterdir()) == [rewrite.name]
        assert (external / rewrite.name).read_bytes() == sentinel
        assert owned_files._is_junction(scripts)
        assert [
            action.action for action in result.files if action.path == str(rewrite)
        ] == ["kept"]
        assert install_ctx.manifest.files_for("copilot").count(str(rewrite)) == 1
    finally:
        if owned_files._is_junction(scripts):
            scripts.rmdir()


def test_copilot_reinstall_owned_leaf_symlink_branch_is_deterministic(
    copilot, install_ctx, monkeypatch
):
    copilot.install_workspace(install_ctx)
    rewrite = (
        install_ctx.target_root
        / ".github"
        / "hooks"
        / "nexus-hub-scripts"
        / "rewrite-command.sh"
    )
    rewrite.write_bytes(b"mocked leaf symlink drift\n")
    original = Path.is_symlink

    def pretend_rewrite_is_symlink(path):
        return path == rewrite or original(path)

    monkeypatch.setattr(Path, "is_symlink", pretend_rewrite_is_symlink)

    result = copilot.install_workspace(install_ctx)

    assert rewrite.read_bytes() == (
        install_ctx.repo_root / "catalog" / "hooks" / rewrite.name
    ).read_bytes()
    assert [action.action for action in result.files if action.path == str(rewrite)] == [
        "updated"
    ]
    assert install_ctx.manifest.files_for("copilot").count(str(rewrite)) == 1


def test_copilot_reinstall_refuses_owned_junction_without_touching_contents(
    copilot, install_ctx, monkeypatch
):
    copilot.install_workspace(install_ctx)
    rewrite = (
        install_ctx.target_root
        / ".github"
        / "hooks"
        / "nexus-hub-scripts"
        / "rewrite-command.sh"
    )
    rewrite.unlink()
    rewrite.mkdir()
    sentinel = rewrite / "external-junction-content.txt"
    sentinel.write_bytes(b"external junction bytes must survive\n")
    original = getattr(Path, "is_junction", None)

    def pretend_rewrite_is_junction(path):
        if path == rewrite:
            return True
        return original(path) if original is not None else False

    monkeypatch.setattr(Path, "is_junction", pretend_rewrite_is_junction, raising=False)

    result = copilot.install_workspace(install_ctx)

    assert sentinel.read_bytes() == b"external junction bytes must survive\n"
    assert [action.action for action in result.files if action.path == str(rewrite)] == [
        "kept"
    ]
    assert install_ctx.manifest.files_for("copilot").count(str(rewrite)) == 1


def test_owned_junction_detection_supports_python_without_path_is_junction(monkeypatch):
    """The reparse-tag fallback is exercised on every host, not only on Windows.

    `stat.IO_REPARSE_TAG_MOUNT_POINT` does not exist on POSIX, so reading it at
    class-definition time made this test an unconditional Linux error rather than
    a check of the fallback branch. Pinning the documented tag value keeps the
    assertion host-independent.
    """
    mount_point_tag = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
    monkeypatch.setattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", mount_point_tag, raising=False)

    class LegacyWindowsStat:
        st_reparse_tag = mount_point_tag

    class LegacyWindowsPath:
        def lstat(self):
            return LegacyWindowsStat()

    assert owned_files._is_junction(LegacyWindowsPath())


def test_copilot_reinstall_preserves_untracked_user_hook(copilot, install_ctx):
    rewrite = (
        install_ctx.target_root
        / ".github"
        / "hooks"
        / "nexus-hub-scripts"
        / "rewrite-command.sh"
    )
    rewrite.parent.mkdir(parents=True)
    _write_hook_file(rewrite, "# user-authored hook\n")

    result = copilot.install_workspace(install_ctx)

    assert rewrite.read_text(encoding="utf-8") == "# user-authored hook\n"
    assert [action.action for action in result.files if action.path == str(rewrite)] == [
        "kept"
    ]
    assert str(rewrite) not in install_ctx.manifest.files_for("copilot")


def test_copilot_install_does_not_claim_untracked_catalog_identical_hook(
    copilot, install_ctx
):
    rewrite = (
        install_ctx.target_root
        / ".github"
        / "hooks"
        / "nexus-hub-scripts"
        / "rewrite-command.sh"
    )
    rewrite.parent.mkdir(parents=True)
    catalog_bytes = (
        install_ctx.repo_root / "catalog" / "hooks" / rewrite.name
    ).read_bytes()
    rewrite.write_bytes(catalog_bytes)

    result = copilot.install_workspace(install_ctx)

    assert rewrite.read_bytes() == catalog_bytes
    assert [action.action for action in result.files if action.path == str(rewrite)] == [
        "kept"
    ]
    assert str(rewrite) not in install_ctx.manifest.files_for("copilot")


def test_copilot_shell_quoters_preserve_interpolation_characters():
    value = "copilot-$hook path's"
    bash = shutil.which("bash")
    if bash is not None:
        result = subprocess.run(
            [bash, "-c", f"printf '%s' {copilot_native._bash_quote(value)}"],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "hook": "EXPANDED"},
        )
        assert result.returncode == 0
        assert result.stdout == value

    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is not None:
        result = subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-Command",
                f"Write-Output {copilot_native._powershell_quote(value)}",
            ],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "hook": "EXPANDED"},
        )
        assert result.returncode == 0
        assert result.stdout.strip() == value

    assert bash is not None or powershell is not None


def test_copilot_generated_commands_literal_quote_paths_with_dollar_and_spaces(
    install_ctx, tmp_path
):
    base = (tmp_path / "copilot-$hook path").as_posix()
    bash, powershell = copilot_native._command_pair(
        "rewrite-command.sh",
        base,
        "PreToolUse",
        install_ctx.repo_root / "catalog" / "hooks",
    )

    assert f"'{base}/copilot-hook-compat.py'" in bash
    assert f"'{base}/rewrite-command.sh'" in bash
    assert f"'{base}/copilot-hook-compat.py'" in powershell
    assert f"'{base}/rewrite-command.ps1'" in powershell


def test_copilot_hook_bridge_translates_native_input_to_guard_contract():
    translated = hook_compat.translate_copilot_payload(
        {
            "sessionId": "session-123",
            "cwd": "/repo",
            "toolName": "bash",
            "toolArgs": '{"command":"git reset --hard","description":"reset"}',
        },
        "PreToolUse",
    )

    assert translated["hook_event_name"] == "PreToolUse"
    assert translated["session_id"] == "session-123"
    assert translated["tool_name"] == "bash"
    assert translated["tool_input"] == {
        "command": "git reset --hard",
        "description": "reset",
    }


def _write_hook_file(path: Path, body: str = "# test hook\n") -> None:
    path.write_text(body, encoding="utf-8")


def test_copilot_permission_authority_accepts_only_generated_child_shapes(tmp_path):
    hooks = tmp_path / "nexus-hub-scripts"
    hooks.mkdir()
    compat = hooks / "copilot-hook-compat.py"
    _write_hook_file(compat)
    for name in ("rewrite-command.sh", "rewrite-command.ps1"):
        _write_hook_file(hooks / name)

    bash_digest = hashlib.sha256((hooks / "rewrite-command.sh").read_bytes()).hexdigest()
    powershell_digest = hashlib.sha256(
        (hooks / "rewrite-command.ps1").read_bytes()
    ).hexdigest()
    accepted = (
        (
            "rewrite-command.sh",
            ["bash", str(hooks / "rewrite-command.sh")],
            bash_digest,
        ),
        (
            "rewrite-command.sh",
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(hooks / "rewrite-command.ps1"),
            ],
            powershell_digest,
        ),
    )

    for handler_name, command, digest in accepted:
        assert hook_compat._copilot_permission_authoritative(
            handler_name, command, digest, compat_path=compat
        )


@pytest.mark.parametrize(
    "handler_name,interpreter",
    [
        ("format-bash-description.py", "python3"),
        ("format-powershell-description.py", "python"),
    ],
)
def test_copilot_formatters_are_not_permission_authoritative(
    tmp_path, handler_name, interpreter
):
    hooks = tmp_path / "nexus-hub-scripts"
    hooks.mkdir()
    compat = hooks / "copilot-hook-compat.py"
    child = hooks / handler_name
    _write_hook_file(compat)
    _write_hook_file(child)
    digest = hashlib.sha256(child.read_bytes()).hexdigest()

    assert not hook_compat._copilot_permission_authoritative(
        handler_name,
        [interpreter, str(child)],
        digest,
        compat_path=compat,
    )


def test_copilot_permission_authority_rejects_ambiguous_child_shapes(tmp_path):
    hooks = tmp_path / "nexus-hub-scripts"
    hooks.mkdir()
    compat = hooks / "copilot-hook-compat.py"
    canonical = hooks / "rewrite-command.sh"
    rewrite_ps1 = hooks / "rewrite-command.ps1"
    outside = tmp_path / "rewrite-command.sh"
    sibling_dir = hooks / "nested"
    sibling_dir.mkdir()
    sibling = sibling_dir / "rewrite-command.sh"
    for path in (compat, canonical, rewrite_ps1, outside, sibling):
        _write_hook_file(path)
    digest = hashlib.sha256(canonical.read_bytes()).hexdigest()
    powershell_digest = hashlib.sha256(rewrite_ps1.read_bytes()).hexdigest()

    rejected = (
        ("format-bash-description.py", ["bash", str(canonical)], digest),
        ("rewrite-command.sh", ["bash", str(outside)], digest),
        ("rewrite-command.sh", ["bash", str(sibling)], digest),
        ("rewrite-command.sh", ["bash", str(canonical), "extra"], digest),
        ("rewrite-command.sh", ["python", "-c", str(canonical)], digest),
        ("rewrite-command.sh", [sys.executable, str(canonical)], digest),
        ("rewrite-command.sh", ['"bash"', str(canonical)], digest),
        ("rewrite-command.sh", ["bash", f'"{canonical}"'], digest),
        (
            "rewrite-command.sh",
            ["bash", str(canonical.with_name("REWRITE-COMMAND.SH"))],
            digest,
        ),
        (
            "rewrite-command.sh",
            ["bash", str(canonical.with_suffix(".bash"))],
            digest,
        ),
        (
            "rewrite-command.sh",
            ["bash", str(sibling_dir / ".." / canonical.name)],
            digest,
        ),
        (
            "rewrite-command.ps1",
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(rewrite_ps1),
            ],
            powershell_digest,
        ),
        (
            "rewrite-command.sh",
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(rewrite_ps1),
                "extra",
            ],
            powershell_digest,
        ),
        (
            "rewrite-command.sh",
            [
                "powershell",
                "-noprofile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(rewrite_ps1),
            ],
            powershell_digest,
        ),
        ("rewrite-command.sh", ["bash", str(canonical)], "0" * 64),
        ("rewrite-command.sh", ["bash", str(canonical)], digest.upper()),
    )

    for handler_name, command, expected_digest in rejected:
        assert not hook_compat._copilot_permission_authoritative(
            handler_name, command, expected_digest, compat_path=compat
        )


def test_copilot_permission_authority_rejects_symlinked_child(
    tmp_path, monkeypatch
):
    hooks = tmp_path / "nexus-hub-scripts"
    hooks.mkdir()
    compat = hooks / "copilot-hook-compat.py"
    child = hooks / "rewrite-command.sh"
    _write_hook_file(compat)
    _write_hook_file(child)
    original = Path.is_symlink

    def pretend_child_is_symlink(path):
        return path == child or original(path)

    monkeypatch.setattr(Path, "is_symlink", pretend_child_is_symlink)
    digest = hashlib.sha256(child.read_bytes()).hexdigest()
    assert not hook_compat._copilot_permission_authoritative(
        "rewrite-command.sh",
        ["bash", str(child)],
        digest,
        compat_path=compat,
    )


def test_copilot_permission_authority_rejects_hard_linked_child(tmp_path):
    hooks = tmp_path / "nexus-hub-scripts"
    hooks.mkdir()
    compat = hooks / "copilot-hook-compat.py"
    child = hooks / "rewrite-command.sh"
    external = tmp_path / "external-command.sh"
    _write_hook_file(compat)
    _write_hook_file(external)
    try:
        os.link(external, child)
    except OSError as exc:
        pytest.skip(f"hard links unavailable: {exc}")
    digest = hashlib.sha256(child.read_bytes()).hexdigest()

    assert not hook_compat._copilot_permission_authoritative(
        "rewrite-command.sh",
        ["bash", str(child)],
        digest,
        compat_path=compat,
    )


def test_copilot_canonical_authoritative_child_may_allow(
    tmp_path, monkeypatch, capsys
):
    hooks = tmp_path / "nexus-hub-scripts"
    hooks.mkdir()
    compat = hooks / "copilot-hook-compat.py"
    child = hooks / "rewrite-command.sh"
    _write_hook_file(compat)
    _write_hook_file(
        child,
        "#!/usr/bin/env bash\n"
        "cat >/dev/null\n"
        "printf '%s' '{\"hookSpecificOutput\":{\"permissionDecision\":\"allow\","
        "\"permissionDecisionReason\":\"validated child\","
        "\"updatedInput\":{\"command\":\"git status\"}}}'\n",
    )
    digest = hashlib.sha256(child.read_bytes()).hexdigest()
    monkeypatch.setattr(hook_compat, "__file__", str(compat))
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {"toolName": "bash", "toolArgs": '{"command":"git status"}'}
            )
        ),
    )

    wrapper_exit = hook_compat.main(
        [
            "copilot",
            "PreToolUse",
            "--handler",
            "rewrite-command.sh",
            "--handler-sha256",
            digest,
            "--",
            "bash",
            str(child),
        ]
    )
    captured = capsys.readouterr()

    assert wrapper_exit == 0
    assert json.loads(captured.out) == {
        "permissionDecision": "allow",
        "permissionDecisionReason": "validated child",
        "modifiedArgs": {"command": "git status"},
    }


def test_copilot_transformation_only_compressor_cannot_authorize_arbitrary_command():
    rewritten = {
        "command": "{ arbitrary-command --dangerous ; } | python -m nexus_context_compressor compress",
        "description": "arbitrary command",
    }
    output, wrapper_exit = hook_compat.translate_child_result(
        "copilot",
        "PreToolUse",
        stdout=json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "updatedInput": rewritten,
                }
            }
        ),
        stderr="",
        returncode=0,
    )

    assert wrapper_exit == 0
    assert output == {"modifiedArgs": rewritten}


def test_copilot_hook_bridge_end_to_end_returns_modified_args_without_allow(
    monkeypatch, capsys
):
    payload = {
        "sessionId": "session-123",
        "cwd": "/repo",
        "toolName": "bash",
        "toolArgs": '{"command":"git reset --hard"}',
    }
    child = (
        "import json,sys; "
        "payload=json.load(sys.stdin); "
        "assert payload['tool_input']['command']=='git reset --hard'; "
        "print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse',"
        "'permissionDecision':'allow','permissionDecisionReason':'rewritten safely',"
        "'updatedInput':{'command':'git status'}}}))"
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    wrapper_exit = hook_compat.main(
        [
            "copilot",
            "PreToolUse",
            "--handler",
            "compress-output.sh",
            "--",
            sys.executable,
            "-c",
            child,
        ]
    )
    captured = capsys.readouterr()

    assert wrapper_exit == 0
    assert json.loads(captured.out) == {
        "modifiedArgs": {"command": "git status"},
    }


def test_copilot_authoritative_label_cannot_bless_an_arbitrary_python_child(
    monkeypatch, capsys
):
    payload = {
        "toolName": "bash",
        "toolArgs": '{"command":"arbitrary-command --dangerous"}',
    }
    child = (
        "import json,sys; "
        "json.load(sys.stdin); "
        "print(json.dumps({'hookSpecificOutput':{'permissionDecision':'allow',"
        "'permissionDecisionReason':'label spoofed authority',"
        "'updatedInput':{'command':'arbitrary-command --dangerous'}}}))"
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    wrapper_exit = hook_compat.main(
        [
            "copilot",
            "PreToolUse",
            "--handler",
            "rewrite-command.sh",
            "--",
            sys.executable,
            "-c",
            child,
        ]
    )
    captured = capsys.readouterr()

    assert wrapper_exit == 0
    assert json.loads(captured.out) == {
        "modifiedArgs": {"command": "arbitrary-command --dangerous"},
    }


def test_copilot_hook_bridge_cannot_be_tricked_into_allowing_exit_two():
    output, wrapper_exit = hook_compat.translate_child_result(
        "copilot",
        "PreToolUse",
        stdout=json.dumps(
            {"hookSpecificOutput": {"permissionDecision": "allow"}}
        ),
        stderr="catalog guard blocked the operation",
        returncode=2,
    )

    assert wrapper_exit == 0
    assert output["permissionDecision"] == "deny"
    assert output["permissionDecisionReason"] == "catalog guard blocked the operation"


def test_copilot_hook_bridge_reasonless_structured_deny_gets_safe_reason():
    output, wrapper_exit = hook_compat.translate_child_result(
        "copilot",
        "PreToolUse",
        stdout=json.dumps(
            {"hookSpecificOutput": {"permissionDecision": "deny"}}
        ),
        stderr="",
        returncode=0,
    )

    assert wrapper_exit == 0
    assert output == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "Nexus-Hub guard denied the tool call.",
    }


def test_copilot_hook_bridge_preserves_ask_and_reason_without_authority():
    output, wrapper_exit = hook_compat.translate_child_result(
        "copilot",
        "PreToolUse",
        stdout=json.dumps(
            {
                "hookSpecificOutput": {
                    "permissionDecision": "ask",
                    "permissionDecisionReason": "human review required",
                }
            }
        ),
        stderr="",
        returncode=0,
    )

    assert wrapper_exit == 0
    assert output == {
        "permissionDecision": "ask",
        "permissionDecisionReason": "human review required",
    }


def test_copilot_hook_bridge_end_to_end_cannot_be_tricked_by_exit_two(
    monkeypatch, capsys
):
    payload = {
        "toolName": "bash",
        "toolArgs": '{"command":"git reset --hard"}',
    }
    child = (
        "import json,sys; "
        "json.load(sys.stdin); "
        "print(json.dumps({'hookSpecificOutput':{'permissionDecision':'allow'}})); "
        "print('catalog guard blocked the operation',file=sys.stderr); "
        "sys.exit(2)"
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    wrapper_exit = hook_compat.main(
        ["copilot", "PreToolUse", "--", sys.executable, "-c", child]
    )
    captured = capsys.readouterr()

    assert wrapper_exit == 0
    assert json.loads(captured.out) == {
        "permissionDecision": "deny",
        "permissionDecisionReason": "catalog guard blocked the operation",
    }


def test_copilot_hook_bridge_fails_closed_when_child_cannot_start(
    monkeypatch, capsys
):
    payload = {
        "toolName": "bash",
        "toolArgs": '{"command":"git reset --hard"}',
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    wrapper_exit = hook_compat.main(
        ["copilot", "PreToolUse", "--", "nexus-hook-command-that-does-not-exist"]
    )
    captured = capsys.readouterr()

    assert wrapper_exit == 0
    output = json.loads(captured.out)
    assert output["permissionDecision"] == "deny"
    assert "hook-compat:" in output["permissionDecisionReason"]


def test_user_authored_copilot_hook_file_is_preserved(copilot, install_ctx):
    hook_file = install_ctx.target_root / ".github" / "hooks" / "nexus-hub.json"
    hook_file.parent.mkdir(parents=True)
    hook_file.write_text('{"version":1,"hooks":{"preToolUse":[]}}', encoding="utf-8")
    copilot.install_workspace(install_ctx)
    assert json.loads(hook_file.read_text(encoding="utf-8"))["hooks"] == {"preToolUse": []}


def test_global_install_writes_personal_instruction_and_hooks(
    copilot, install_ctx, monkeypatch, copilot_home
):
    copilot_home.mkdir(parents=True)
    _isolate_global(monkeypatch, copilot_home)
    copilot.install_global(install_ctx)
    assert (copilot_home / "copilot-instructions.md").is_file()
    assert (copilot_home / "hooks" / "nexus-hub.json").is_file()


def test_recorded_copilot_defaults_stay_in_step_with_the_contract():
    """The quoted default locations must appear in the read contract prose."""
    doc = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "policy"
        / "platform-read-contracts.md"
    ).read_text(encoding="utf-8")
    for location in (
        "~/.copilot/copilot-instructions.md",
        "~/.copilot/hooks",
        ".github/hooks",
        ".github/agents",
        "~/.copilot/agents",
    ):
        assert location in doc, location


# ----- 8.2 the skills selector must not regress ---------------------------


def test_skills_selector_still_defaults_to_off(copilot, install_ctx, monkeypatch):
    monkeypatch.delenv("NEXUS_HUB_COPILOT_SKILLS", raising=False)
    result = copilot.wire_project_surfaces(install_ctx)
    assert not (install_ctx.target_root / ".github" / "skills").exists()
    assert any("opt-in" in note for note in result.notes)


@pytest.mark.parametrize("value", ["1", "core-developer", "all"])
def test_skills_selector_still_seeds_when_opted_in(
    copilot, install_ctx, monkeypatch, value
):
    monkeypatch.setenv("NEXUS_HUB_COPILOT_SKILLS", value)
    copilot.wire_project_surfaces(install_ctx)
    seeded = list((install_ctx.target_root / ".github" / "skills").glob("*/SKILL.md"))
    assert seeded, value


def test_skills_selector_never_overwrites_a_committed_file(
    copilot, install_ctx, monkeypatch
):
    monkeypatch.setenv("NEXUS_HUB_COPILOT_SKILLS", "1")
    dst = install_ctx.target_root / ".github" / "skills" / "commit" / "SKILL.md"
    dst.parent.mkdir(parents=True)
    dst.write_text("mine", encoding="utf-8")

    copilot.wire_project_surfaces(install_ctx)

    assert dst.read_text(encoding="utf-8") == "mine"


# ----- 8.3 Hermes layout compatibility ------------------------------------


def test_hermes_skills_are_exactly_one_level_deep(hermes, install_ctx):
    """Hermes probes each direct subdirectory of the tap path for SKILL.md.

    Category nesting would put SKILL.md two levels down, where Hermes would not
    find it, so the flattened layout is required rather than merely accepted.
    """
    hermes.install_workspace(install_ctx)
    skills_root = install_ctx.target_root / ".hermes" / "skills"
    assert skills_root.is_dir()

    direct = [p for p in skills_root.iterdir() if p.is_dir()]
    assert direct, "no skills were delivered"
    for child in direct:
        assert (child / "SKILL.md").is_file(), f"{child.name} has no SKILL.md at depth 1"


def test_no_hermes_skill_md_sits_two_levels_deep(hermes, install_ctx):
    """The failure mode a category-nested migration would introduce."""
    hermes.install_workspace(install_ctx)
    skills_root = install_ctx.target_root / ".hermes" / "skills"
    nested = [
        p
        for p in skills_root.glob("*/*/SKILL.md")
        # A skill's own bundled subdirs (references/, scripts/, assets/) never
        # contain a SKILL.md, so any match here is a category layer.
    ]
    assert nested == [], f"SKILL.md found below depth 1: {nested[:3]}"


def test_hermes_skill_dirs_are_discoverable_names(hermes, install_ctx):
    """Hermes ignores directories starting with `.` or `_`."""
    hermes.install_workspace(install_ctx)
    skills_root = install_ctx.target_root / ".hermes" / "skills"
    for child in skills_root.iterdir():
        if child.is_dir():
            assert not child.name.startswith(("._", ".", "_")), child.name


def test_hermes_commands_also_surface_as_skills(hermes, install_ctx):
    """Skills are Hermes's only action surface, so commands must appear there."""
    hermes.install_workspace(install_ctx)
    names = {
        p.name for p in (install_ctx.target_root / ".hermes" / "skills").iterdir()
    }
    assert "implement" in names or "plan" in names


def test_hermes_does_not_write_the_shared_agents_alias(hermes, install_ctx):
    """Shared roots require an explicit Hermes skills.external_dirs setting."""
    hermes.install_workspace(install_ctx)
    assert not (install_ctx.target_root / ".agents").exists()


def test_hermes_global_is_detection_gated(hermes, install_ctx, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: install_ctx.target_root))
    result = hermes.install_global(install_ctx)
    assert result.detected is False
    assert not (install_ctx.target_root / ".hermes" / "skills").exists()


def _alias_spelling(path: Path) -> Path | None:
    """A different spelling of `path` that denotes the same directory, or None.

    Windows exposes 8.3 short names (the BEDOUR~1 form of a long user name);
    POSIX hosts commonly reach the same directory through a symlinked parent.
    """
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        get_short = ctypes.windll.kernel32.GetShortPathNameW
        get_short.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        get_short.restype = wintypes.DWORD
        buffer = ctypes.create_unicode_buffer(1024)
        if get_short(str(path), buffer, len(buffer)) == 0:
            return None
        short = Path(buffer.value)
        return short if str(short) != str(path) else None
    alias = path.parent / f"{path.name}-alias"
    try:
        alias.symlink_to(path, target_is_directory=True)
    except OSError:
        return None
    return alias


def test_owned_write_survives_an_aliased_target_root_spelling(install_ctx):
    """A managed write must not be silently refused because `target_root` and the
    destination are spelled differently while denoting the same directory.

    Regression (v4.3.0 Phase 5): the link-like ancestor guard compared only
    `os.path.abspath` spellings, which does not normalize Windows 8.3 short names
    or POSIX parent symlinks. Every such write returned `kept` with nothing on
    disk and no error, so an installer reported success and delivered nothing.
    """
    from scripts.lib.integrations._owned import write_owned_file

    alias_root = _alias_spelling(install_ctx.target_root)
    if alias_root is None:
        pytest.skip("no alternate path spelling available on this host")
    aliased_ctx = replace(install_ctx, target_root=alias_root)

    destination = (install_ctx.target_root / "aliased" / "managed.md").resolve()
    action = write_owned_file(aliased_ctx, "copilot", destination, b"managed bytes\n")

    assert action.action == "created", f"expected a real write, got {action.action!r}"
    assert destination.exists(), "write_owned_file reported success but wrote nothing"
    assert destination.read_bytes() == b"managed bytes\n"


def test_owned_write_outside_target_root_is_not_silently_refused(install_ctx, tmp_path):
    """A global-scope managed write lands even though it sits outside target_root.

    Regression (v4.3.0 Phase 5): the link-like ancestor guard refused every
    destination it could not express relative to `target_root` and reported
    `kept`. Global installs legitimately write to `~/.copilot`, `~/.claude`, and
    the VS Code user directory while `target_root` is the workspace, so the
    installer reported success and delivered nothing. Outside the managed root
    there is no managed ancestor to police; the leaf is still protected below.
    """
    from scripts.lib.integrations._owned import write_owned_file

    workspace = tmp_path / "ws"
    workspace.mkdir()
    scoped_ctx = replace(install_ctx, target_root=workspace)
    outside = tmp_path / ".copilot" / "agents" / "architect.agent.md"

    action = write_owned_file(scoped_ctx, "copilot", outside, b"agent bytes\n")

    assert action.action == "created", f"expected a real write, got {action.action!r}"
    assert outside.read_bytes() == b"agent bytes\n"


def test_owned_write_outside_target_root_still_refuses_a_junction_leaf(
    install_ctx, tmp_path
):
    """Allowing out-of-root writes must not disable leaf-level link protection."""
    from scripts.lib.integrations._owned import write_owned_file

    workspace = tmp_path / "ws"
    workspace.mkdir()
    scoped_ctx = replace(install_ctx, target_root=workspace)
    external = tmp_path / "external.txt"
    sentinel = b"external bytes must survive\n"
    external.write_bytes(sentinel)

    outside = tmp_path / "outside-link.txt"
    try:
        os.link(external, outside)
    except OSError as exc:
        pytest.skip(f"hard links unavailable: {exc}")
    scoped_ctx.manifest.track("copilot", str(outside))

    write_owned_file(scoped_ctx, "copilot", outside, b"replacement bytes\n")

    assert external.read_bytes() == sentinel, "external hard-link target was clobbered"
    assert outside.read_bytes() == b"replacement bytes\n"
    assert not outside.samefile(external)


def test_bare_bash_resolves_to_a_real_interpreter_on_windows(tmp_path, monkeypatch):
    """A bare `bash` is rewritten to a verified Git Bash on Windows.

    Regression (v4.3.0 Phase 5): on a Windows host whose PATH `bash` is the WSL
    launcher stub, the guard child exits non-zero and prints its notice to stdout,
    so the bridge denied every tool call with an empty stderr and no diagnostic.
    """
    real_bash = tmp_path / "bash.exe"
    real_bash.write_text("", encoding="utf-8")
    monkeypatch.setattr(hook_compat, "_windows_host", lambda: True)
    monkeypatch.setattr(hook_compat, "_WINDOWS_BASH_CANDIDATES", (str(real_bash),))

    assert hook_compat._resolve_bash_command(["bash", "child.sh"]) == [
        str(real_bash),
        "child.sh",
    ]


def test_absolute_interpreter_is_never_second_guessed(tmp_path, monkeypatch):
    """Only a BARE `bash` is rewritten; a chosen absolute path is left alone."""
    real_bash = tmp_path / "bash.exe"
    real_bash.write_text("", encoding="utf-8")
    monkeypatch.setattr(hook_compat, "_windows_host", lambda: True)
    monkeypatch.setattr(hook_compat, "_WINDOWS_BASH_CANDIDATES", (str(real_bash),))

    chosen = [str(tmp_path / "custom-bash.exe"), "child.sh"]
    assert hook_compat._resolve_bash_command(chosen) == chosen
    powershell = ["powershell", "-NoProfile", "-File", "child.ps1"]
    assert hook_compat._resolve_bash_command(powershell) == powershell


def test_bash_command_is_unchanged_when_no_git_bash_is_present(monkeypatch):
    """With no Git Bash on disk the original command survives for PATH lookup."""
    monkeypatch.setattr(hook_compat, "_windows_host", lambda: True)
    monkeypatch.setattr(hook_compat, "_WINDOWS_BASH_CANDIDATES", ())

    assert hook_compat._resolve_bash_command(["bash", "child.sh"]) == ["bash", "child.sh"]


def test_posix_bash_command_is_left_to_path(monkeypatch):
    """POSIX has no WSL stub problem, so PATH resolution is correct there."""
    monkeypatch.setattr(hook_compat, "_windows_host", lambda: False)

    assert hook_compat._resolve_bash_command(["bash", "child.sh"]) == ["bash", "child.sh"]


def test_guard_survives_a_wsl_stub_first_on_path(tmp_path, monkeypatch, capsys):
    """End-to-end: a stub `bash` first on PATH must not silently deny every call.

    This is the regression for the defect the v4.3.0 integration run surfaced. A
    Windows host whose PATH `bash` is the WSL launcher stub gets a child that
    prints its notice to STDOUT and exits non-zero, so the bridge saw a non-zero
    child with an empty stderr and denied. The unit tests around
    `_resolve_bash_command` check its return value; this one checks that the
    guard still WORKS with a hostile PATH, which is the property users depend on.
    """
    real_bash = shutil.which("bash")
    if real_bash is None:
        pytest.skip("no usable bash on this host")

    # A stand-in for the WSL stub: writes to stdout, never stderr, exits non-zero.
    stub_dir = tmp_path / "stub"
    stub_dir.mkdir()
    stub = stub_dir / ("bash.exe" if os.name == "nt" else "bash")
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "print('Windows Subsystem for Linux has no installed distributions.')\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", str(stub_dir) + os.pathsep + os.environ.get("PATH", ""))

    hooks = tmp_path / "nexus-hub-scripts"
    hooks.mkdir()
    compat = hooks / "copilot-hook-compat.py"
    child = hooks / "rewrite-command.sh"
    _write_hook_file(compat)
    _write_hook_file(
        child,
        "#!/usr/bin/env bash\n"
        "cat >/dev/null\n"
        "printf '%s' '{\"hookSpecificOutput\":{\"permissionDecision\":\"allow\","
        "\"permissionDecisionReason\":\"validated child\","
        "\"updatedInput\":{\"command\":\"git status\"}}}'\n",
    )
    digest = hashlib.sha256(child.read_bytes()).hexdigest()

    # Take the Windows branch on any host, pointing it at this host's real bash.
    monkeypatch.setattr(hook_compat, "_windows_host", lambda: True)
    monkeypatch.setattr(hook_compat, "_WINDOWS_BASH_CANDIDATES", (real_bash,))
    monkeypatch.setattr(hook_compat, "__file__", str(compat))
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(json.dumps({"toolName": "bash", "toolArgs": '{"command":"git status"}'})),
    )

    wrapper_exit = hook_compat.main(
        [
            "copilot",
            "PreToolUse",
            "--handler",
            "rewrite-command.sh",
            "--handler-sha256",
            digest,
            "--",
            "bash",
            str(child),
        ]
    )

    assert wrapper_exit == 0
    decision = json.loads(capsys.readouterr().out)
    assert decision.get("permissionDecision") != "deny", (
        "a stub bash first on PATH silently denied the tool call; "
        "the interpreter resolver did not rescue the child"
    )
    assert decision["permissionDecision"] == "allow"
    assert decision["modifiedArgs"] == {"command": "git status"}
