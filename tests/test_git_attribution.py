"""Observe attribution enforcement through real Git operations in isolated homes."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts/nexus_git_attribution.py"


@pytest.fixture
def sandbox(tmp_path):
    home = tmp_path / "user home"
    home.mkdir()
    repo = tmp_path / "project"
    repo.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        HOME=str(home),
        USERPROFILE=str(home),
        GIT_CONFIG_GLOBAL=str(home / ".gitconfig"),
        GIT_CONFIG_NOSYSTEM="1",
        NEXUS_HUB_HOME=str(home / ".nexus-hub"),
    )
    if os.name == "nt":
        env["PATH"] = r"C:\Program Files\Git\bin" + os.pathsep + env["PATH"]

    def run(*args, code=0, extra=None, input=None):
        result = subprocess.run(
            args,
            cwd=repo,
            env=env | (extra or {}),
            input=input,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=300,
        )
        if code is not None:
            assert result.returncode == code, result.stdout + result.stderr
        return result

    run("git", "init", "-q")
    run("git", "config", "--global", "user.name", "Alex Human")
    run("git", "config", "--global", "user.email", "alex@example.test")
    return run, repo, home


def guard(run, *args, **kwargs):
    return run(sys.executable, str(GUARD), *args, **kwargs)


def test_installed_user_commit_and_checked_tag(sandbox):
    run, _repo, home = sandbox
    guard(run, "install")
    guard(run, "check")
    run("git", "commit", "--allow-empty", "-m", "Discuss Claude integration")
    assert (
        run("git", "log", "-1", "--format=%an <%ae>|%cn <%ce>").stdout.strip()
        == "Alex Human <alex@example.test>|Alex Human <alex@example.test>"
    )
    guard(run, "tag", "v1.0.0", "-m", "Release")
    run("git", "init", "--bare", "-q", str(home / "remote.git"))
    run(
        "git",
        "push",
        str(home / "remote.git"),
        "HEAD:refs/heads/main",
        "refs/tags/v1.0.0",
    )
    run("git", "config", "user.name", "Robin Human")
    run("git", "config", "user.email", "robin@example.test")
    run("git", "commit", "--allow-empty", "-m", "Another user")
    assert "Robin Human" in run("git", "log", "-1", "--format=%an").stdout
    run("git", "push", str(home / "remote.git"), "HEAD:refs/heads/main")


def test_interpreter_removal_and_reinstall_preserve_special_hook_absence(sandbox):
    run, repo, home = sandbox
    runtime = home / "temporary Python"
    run(sys.executable, "-m", "venv", "--without-pip", str(runtime))
    python = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    previous = repo / ".git/hooks/push-to-checkout"
    previous.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8", newline="\n")
    previous.chmod(0o755)
    run(str(python), str(GUARD), "install")
    guard(run, "check")
    wrapper = home / ".nexus-hub/git-hooks/push-to-checkout"
    assert wrapper.is_file()
    previous.unlink()
    python.rename(python.with_name("retired-python"))
    result = guard(run, "check", code=None)
    assert result.returncode != 0 and "Reinstall the guard" in result.stderr
    guard(run, "install")
    assert not wrapper.exists()
    guard(run, "check")
    run("git", "commit", "--allow-empty", "-m", "Reinstalled guard")


@pytest.mark.parametrize(
    "extra",
    [
        {"GIT_AUTHOR_NAME": "Claude", "GIT_AUTHOR_EMAIL": "noreply@anthropic.com"},
        {"GIT_COMMITTER_NAME": "Codex", "GIT_COMMITTER_EMAIL": "codex@openai.com"},
        {"GIT_AUTHOR_NAME": "Other Human", "GIT_AUTHOR_EMAIL": "other@example.test"},
    ],
)
def test_identity_overrides_blocked_even_no_verify(sandbox, extra):
    run, _, _ = sandbox
    guard(run, "install")
    result = run(
        "git",
        "commit",
        "--no-verify",
        "--allow-empty",
        "-m",
        "Work",
        extra=extra,
        code=None,
    )
    assert result.returncode != 0 and "Attribution BLOCKED" in result.stderr


@pytest.mark.parametrize(
    "trailer",
    [
        "Co-Authored-By: Claude <c@anthropic.com>",
        "mAdE-wItH: Cursor",
        "Co-Authored-By:\n Claude <c@anthropic.com>",
    ],
)
def test_trailers_blocked(sandbox, trailer):
    run, _, _ = sandbox
    guard(run, "install")
    result = run(
        "git", "commit", "--allow-empty", "-m", "Work\n\n" + trailer, code=None
    )
    assert result.returncode != 0 and "attribution trailers" in result.stderr


def test_pre_push_rejects_bypassed_trailer_and_wrong_tagger(sandbox):
    run, _, home = sandbox
    guard(run, "install")
    run("git", "init", "--bare", "-q", str(home / "remote.git"))
    run(
        "git",
        "commit",
        "--no-verify",
        "--allow-empty",
        "-m",
        "Work\n\nCo-Authored-By: Claude <c@anthropic.com>",
    )
    result = run(
        "git", "push", str(home / "remote.git"), "HEAD:refs/heads/main", code=None
    )
    assert result.returncode != 0 and "attribution trailers" in result.stderr
    run("git", "commit", "--amend", "--allow-empty", "-m", "Clean")
    run(
        "git",
        "tag",
        "-a",
        "v1",
        "-m",
        "Release",
        extra={
            "GIT_COMMITTER_NAME": "Cursor",
            "GIT_COMMITTER_EMAIL": "cursor@cursor.com",
        },
    )
    result = run("git", "push", str(home / "remote.git"), "refs/tags/v1", code=None)
    assert result.returncode != 0 and "Outgoing tag" in result.stderr


def test_existing_hook_and_rollback(sandbox):
    run, repo, _ = sandbox
    hook = repo / ".git/hooks/pre-commit"
    hook.write_text(
        "#!/bin/sh\nprintf preserved > hook-result\nexit 17\n", encoding="utf-8"
    )
    hook.chmod(0o755)
    guard(run, "install")
    guard(run, "install")
    result = run("git", "commit", "--allow-empty", "-m", "Work", code=None)
    assert result.returncode != 0
    assert (repo / "hook-result").read_text() == "preserved"
    guard(run, "uninstall")
    assert (
        run("git", "config", "--global", "--get", "core.hooksPath", code=1).stdout == ""
    )
    assert hook.exists()
    guard(run, "install")
    guard(run, "check")


def test_workspace_wraps_override_and_passes_push_stdin(sandbox):
    run, repo, home = sandbox
    custom = repo / "custom hooks"
    custom.mkdir()
    hook = custom / "pre-push"
    hook.write_text(
        "#!/bin/sh\ncat > push-input\nprintf '%s' \"$1\" > push-arg\n", encoding="utf-8"
    )
    hook.chmod(0o755)
    run("git", "config", "core.hooksPath", str(custom))
    guard(run, "install")
    guard(run, "check", code=1)
    guard(run, "install", "--workspace")
    guard(run, "check")
    run("git", "commit", "--allow-empty", "-m", "Work")
    run("git", "init", "--bare", "-q", str(home / "remote.git"))
    run("git", "push", str(home / "remote.git"), "HEAD:refs/heads/main")
    assert "refs/heads/main" in (repo / "push-input").read_text()
    assert (repo / "push-arg").read_text() == str(home / "remote.git")
    guard(run, "uninstall", "--workspace")
    assert run(
        "git", "config", "--local", "--get", "core.hooksPath"
    ).stdout.strip() == str(custom)


def test_missing_identity_installs_blocking_guard(sandbox):
    run, _, _ = sandbox
    run("git", "config", "--global", "--unset", "user.email")
    assert "NEEDS SETUP" in guard(run, "install").stdout
    guard(run, "check", code=1)
    run("git", "config", "--global", "user.email", "agent@anthropic.com")
    guard(run, "check", code=1)


@pytest.mark.parametrize("runtime", ["bash", "powershell"])
@pytest.mark.parametrize("scope", ["workspace", "global"])
def test_real_workspace_installer_delivers_working_guard(sandbox, runtime, scope):
    run, repo, home = sandbox
    if os.name == "nt" and runtime == "bash" and scope == "global":
        pytest.skip(
            "POSIX global venv layout is covered on Linux; Windows uses the PowerShell installer."
        )
    if runtime == "powershell":
        if os.name != "nt":
            pytest.skip("The PowerShell installer targets Windows; POSIX hosts use Bash.")
        executable = shutil.which("powershell") or shutil.which("pwsh")
        if not executable:
            pytest.skip("PowerShell unavailable")
        command = [
            executable,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts/installer.ps1"),
            "-Workspace",
            str(repo),
            "-Platforms",
            "claude,codex,cursor,antigravity2,aider",
            "-Yes",
        ]
    else:
        executable = (
            r"C:\Program Files\Git\bin\bash.exe"
            if os.name == "nt"
            else shutil.which("bash")
        )
        if not executable:
            pytest.skip("Bash unavailable")
        command = [
            executable,
            str(ROOT / "scripts/installer.sh"),
            "--workspace",
            str(repo),
            "--platforms",
            "claude,codex,cursor,antigravity2,aider",
            "--yes",
        ]
    if scope == "global":
        for platform in (".claude", ".codex", ".cursor", ".gemini"):
            (home / platform).mkdir(exist_ok=True)
        flag = "-Workspace" if runtime == "powershell" else "--workspace"
        index = command.index(flag)
        del command[index : index + 2]
    extra = {"NEXUS_HUB_NO_AUTOSEED": "1"}
    if os.name == "nt" and scope == "global":
        # Exercise the real installer without discovering the host's editor
        # CLIs or optional uv/npm installations outside the disposable home.
        extra["PATH"] = os.pathsep.join(
            [
                str(Path(sys.executable).parent),
                r"C:\Program Files\Git\bin",
                r"C:\Program Files\Git\usr\bin",
                r"C:\Windows\System32",
                str(Path(executable).parent),
            ]
        )
    result = run(*command, code=None, extra=extra)
    (home / "installer.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    assert result.returncode == 0, result.stderr[-4000:]
    installed_cli = home / ".nexus-hub/scripts/nexus_hub_cli.py"
    run(sys.executable, str(installed_cli), "attribution", "check")
    cursor_root = home / ".cursor" if scope == "global" else repo / ".cursor"
    context_command = json.loads((cursor_root / "hooks.json").read_text())["hooks"][
        "sessionStart"
    ][0]["command"]
    if os.name == "nt":
        # A batch file preserves the actual shell command; subprocess list
        # quoting is for executable argv, not cmd.exe's /c expression grammar.
        context_script = repo / "cursor-context.cmd"
        context_script.write_text("@echo off\n" + context_command + "\n")
        shell = ["cmd", "/d", "/c", str(context_script)]
    else:
        shell = ["sh", "-c", context_command]
    context = json.loads(run(*shell, input="{}").stdout)[
        "additional_context"
    ]
    assert "user.name" in context and "user.email" in context and "Co-Authored-By" in context
    import yaml

    aider_root = home if scope == "global" else repo
    aider = yaml.safe_load((aider_root / ".aider.conf.yml").read_text())
    assert aider["attribute-author"] is False
    assert aider["attribute-committer"] is False
    assert aider["attribute-co-authored-by"] is False
    assert aider["git-commit-verify"] is True
    assert (
        str(home / ".nexus-hub/style-guides/git-attribution.md").replace("\\", "/")
        in aider["read"]
    )
    run("git", "commit", "--allow-empty", "-m", "Installed guard works")
    rejected = run(
        "git",
        "commit",
        "--allow-empty",
        "-m",
        "Agent work",
        extra={"GIT_AUTHOR_NAME": "Claude", "GIT_AUTHOR_EMAIL": "claude@anthropic.com"},
        code=None,
    )
    assert rejected.returncode != 0 and "Attribution BLOCKED" in rejected.stderr
    if scope == "workspace":
        assert "## User Attribution" in (repo / "AGENTS.md").read_text(
            encoding="utf-8-sig"
        )
        assert "## User Attribution" in (repo / "CLAUDE.md").read_text(
            encoding="utf-8-sig"
        )


def test_existing_message_hook_cannot_append_agent_trailer(sandbox):
    run, repo, _ = sandbox
    hook = repo / ".git/hooks/commit-msg"
    hook.write_text(
        '#!/bin/sh\nprintf "\\nCo-Authored-By: Claude <c@anthropic.com>\\n" >> "$1"\n',
        encoding="utf-8",
    )
    hook.chmod(0o755)
    guard(run, "install")
    result = run("git", "commit", "--allow-empty", "-m", "Work", code=None)
    assert result.returncode != 0 and "attribution trailers" in result.stderr


@pytest.mark.parametrize("field", ["AUTHOR", "COMMITTER"])
def test_push_rejects_preexisting_agent_commit(sandbox, field):
    run, _, home = sandbox
    run(
        "git",
        "commit",
        "--allow-empty",
        "-m",
        "Bad identity",
        extra={f"GIT_{field}_NAME": "Codex", f"GIT_{field}_EMAIL": "codex@openai.com"},
    )
    guard(run, "install")
    run("git", "init", "--bare", "-q", str(home / "remote.git"))
    result = run(
        "git", "push", str(home / "remote.git"), "HEAD:refs/heads/main", code=None
    )
    assert result.returncode != 0 and "Agent/bot identities" in result.stderr
    assert run("git", "ls-remote", str(home / "remote.git")).stdout == ""


def test_workspace_install_respects_worktree_config(sandbox):
    run, repo, _ = sandbox
    custom = repo / "custom-hooks"
    custom.mkdir()
    run("git", "config", "extensions.worktreeConfig", "true")
    run("git", "config", "--worktree", "core.hooksPath", str(custom))
    guard(run, "install", "--workspace")
    guard(run, "check")
    run("git", "commit", "--allow-empty", "-m", "Worktree scope")
    guard(run, "uninstall", "--workspace")
    assert run(
        "git", "config", "--worktree", "--get", "core.hooksPath"
    ).stdout.strip() == str(custom)


def test_replayed_human_author_is_preserved(sandbox):
    run, repo, _ = sandbox
    run("git", "commit", "--allow-empty", "-m", "Base")
    run("git", "branch", "base")
    (repo / "work.txt").write_text("Human work")
    run("git", "add", "work.txt")
    run(
        "git",
        "commit",
        "-m",
        "Original work",
        extra={
            "GIT_AUTHOR_NAME": "Robin Human",
            "GIT_AUTHOR_EMAIL": "robin@example.test",
        },
    )
    original = run("git", "rev-parse", "HEAD").stdout.strip()
    run("git", "checkout", "-q", "base")
    guard(run, "install")
    run("git", "cherry-pick", original)
    assert (
        run("git", "log", "-1", "--format=%an|%cn").stdout.strip()
        == "Robin Human|Alex Human"
    )


def test_update_instead_retains_git_checkout_behavior(sandbox):
    run, repo, home = sandbox
    (repo / "work.txt").write_text("before")
    run("git", "add", "work.txt")
    run("git", "commit", "-m", "Before")
    remote = home / "remote"
    run("git", "clone", "-q", str(repo), str(remote))
    run(
        "git", "-C", str(remote), "config", "receive.denyCurrentBranch", "updateInstead"
    )
    guard(run, "install")
    (repo / "work.txt").write_text("after")
    run("git", "add", "work.txt")
    run("git", "commit", "-m", "After")
    run("git", "push", str(remote), "HEAD")
    assert (remote / "work.txt").read_text() == "after"
    assert run("git", "-C", str(remote), "status", "--porcelain").stdout == ""


def test_special_hook_added_after_global_install_needs_workspace(sandbox):
    run, repo, _ = sandbox
    guard(run, "install")
    hook = repo / ".git/hooks/push-to-checkout"
    hook.write_text("#!/bin/sh\nexit 0\n")
    hook.chmod(0o755)
    guard(run, "check", code=1)
    guard(run, "install", "--workspace")
    guard(run, "check")


@pytest.mark.parametrize(
    "footer", ["Generated with [Claude Code]", "Made with Cursor", "Written by AI"]
)
def test_plain_agent_footers_are_rejected(sandbox, footer):
    run, _, _ = sandbox
    guard(run, "install")
    result = run("git", "commit", "--allow-empty", "-m", "Work\n\n" + footer, code=None)
    assert result.returncode != 0 and "attribution footer" in result.stderr


@pytest.mark.parametrize(
    "name",
    [
        "Claude",
        "Claude Code",
        "Codex",
        "Codex CLI",
        "Cursor",
        "Cursor Agent",
        "Antigravity",
        "Copilot",
        "Gemini",
        "Qwen",
        "Kimi",
        "GitHub Actions[bot]",
    ],
)
def test_configured_agent_identity_requires_user_setup(sandbox, name):
    run, _, _ = sandbox
    run("git", "config", "--global", "user.name", name)
    assert "NEEDS SETUP" in guard(run, "install").stdout
    guard(run, "check", code=1)


def test_human_name_containing_platform_word_is_preserved(sandbox):
    run, _, _ = sandbox
    run("git", "config", "user.name", "Claude Martin")
    run("git", "config", "user.email", "claude.martin@example.test")
    guard(run, "install")
    guard(run, "check")
    run("git", "commit", "--allow-empty", "-m", "Human contribution")
    assert run("git", "log", "-1", "--format=%an <%ae>").stdout.strip() == (
        "Claude Martin <claude.martin@example.test>"
    )


def test_human_history_with_github_service_committer_can_be_pushed(sandbox):
    run, _, home = sandbox
    run(
        "git",
        "commit",
        "--allow-empty",
        "-m",
        "Human web contribution",
        extra={
            "GIT_COMMITTER_NAME": "GitHub",
            "GIT_COMMITTER_EMAIL": "noreply@github.com",
        },
    )
    guard(run, "install")
    run("git", "init", "--bare", "-q", str(home / "remote.git"))
    run("git", "push", str(home / "remote.git"), "HEAD:refs/heads/main")
    # The service exception is for the committer only, never the author.
    run(
        "git",
        "-c",
        "core.hooksPath=missing-hooks",
        "commit",
        "--allow-empty",
        "-m",
        "Invalid service author",
        extra={"GIT_AUTHOR_NAME": "GitHub", "GIT_AUTHOR_EMAIL": "noreply@github.com"},
    )
    result = run(
        "git", "push", str(home / "remote.git"), "HEAD:refs/heads/main", code=None
    )
    assert result.returncode != 0 and "Agent/bot identities" in result.stderr


def test_uninstall_does_not_overwrite_later_user_config(sandbox):
    run, _, _ = sandbox
    guard(run, "install")
    run("git", "config", "--global", "core.hooksPath", "different")
    guard(run, "uninstall", code=1)
    assert (
        run("git", "config", "--global", "--get", "core.hooksPath").stdout.strip()
        == "different"
    )
