"""Tests for the end-of-task notification triggers (v3.15.10 Phase 1).

Covers catalog/hooks/notify-on-complete.{sh,ps1} (trigger B, Stop) and
catalog/hooks/notify-attention-required.{sh,ps1} (trigger A, Notification),
plus the shared _notify_common.{sh,ps1} helpers.

Contract: docs/releases/v3/v3.15/development/end-of-task-notification-contract.md

The load-bearing assertions are the ones that pin the three field defects this
release exists to fix:

  1. The label must name the REPOSITORY, not the directory the hook ran in. A
     field toast read "Task complete in work" because the old implementation
     used `basename "$(pwd)"`.
  2. The kill switch must work WITHOUT the process environment. An environment
     variable cannot silence a hook inside a running editor, because a child
     process inherits its parent's environment block rather than the registry.
  3. SubagentStop must never be registered. Wiring it reintroduces the per-turn
     notification storm this release removed.

Every behavioral test runs against BOTH implementations via the `run` fixture,
so the suite is also the .sh/.ps1 parity check.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_notify_triggers.py -v
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _HOOKS_DIR.parent.parent
_SETTINGS = _HOOKS_DIR / "settings.json"

_COMPLETE = "notify-on-complete"
_ATTENTION = "notify-attention-required"
_BOTH_HOOKS = [_COMPLETE, _ATTENTION]


def _current_branch() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except OSError:  # pragma: no cover - git absent
        return None
    branch = out.stdout.strip()
    return branch if out.returncode == 0 and branch and branch != "HEAD" else None


@pytest.fixture(params=["sh", "ps1"])
def run(request, tmp_path: Path):
    """Invoke either implementation of either hook, in notification dry-run mode."""
    impl = request.param

    def _run(
        hook: str,
        payload: str = "{}",
        env_extra: dict[str, str] | None = None,
        cwd: Path | None = None,
        clear_switch_override: bool = False,
    ) -> subprocess.CompletedProcess:
        if impl == "sh":
            prefix = [request.getfixturevalue("bash_bin"), str(_HOOKS_DIR / f"{hook}.sh")]
        else:
            prefix = [
                request.getfixturevalue("powershell_bin"),
                "-NoProfile",
                "-File",
                str(_HOOKS_DIR / f"{hook}.ps1"),
            ]

        env = {**os.environ}
        # Dry run so a test never raises a real desktop toast, and the label
        # becomes an assertable observable on stdout.
        env["NEXUS_NOTIFY_DRY_RUN"] = "1"
        # Point the switch file at a path that does not exist, so a developer's
        # real ~/.nexus-hub/notifications-disabled cannot silence the suite.
        env["NEXUS_NOTIFY_DISABLED_FILE"] = str(tmp_path / "absent-switch")
        for key in ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE"):
            env.pop(key, None)
        if env_extra:
            env.update(env_extra)
        # Exercise the DEFAULT switch path (~/.nexus-hub/notifications-disabled)
        # rather than the explicit override. Callers that do this must redirect
        # HOME and USERPROFILE, or the hook would read the developer's real one.
        if clear_switch_override:
            env.pop("NEXUS_NOTIFY_DISABLED_FILE", None)

        return subprocess.run(
            prefix,
            input=payload,
            text=True,
            capture_output=True,
            env=env,
            cwd=str(cwd) if cwd else str(_REPO_ROOT),
            timeout=120,
        )

    return _run


# ---------------------------------------------------------------------------
# Defect 1: the label names the repository, not the working directory
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("hook", _BOTH_HOOKS)
def test_label_names_repo_when_run_from_a_subdirectory(run, hook):
    """The regression that produced "Task complete in work".

    Invoked from catalog/hooks/, the old `basename "$(pwd)"` label would have
    said "hooks". The label must say the repository name instead.
    """
    result = run(hook, cwd=_HOOKS_DIR)

    assert result.returncode == 0, result.stderr
    assert _REPO_ROOT.name in result.stdout, (
        f"label should name the repo {_REPO_ROOT.name!r}; got {result.stdout!r}"
    )
    # The subdirectory name must not be what identifies the workspace.
    label = result.stdout.split("\t", 1)[-1]
    assert not label.strip().startswith("hooks"), (
        f"label started with the subdirectory name: {label!r}"
    )


@pytest.mark.parametrize("hook", _BOTH_HOOKS)
def test_label_includes_the_branch(run, hook):
    """Worktrees of one repo are routinely open at once, so the branch matters."""
    branch = _current_branch()
    if branch is None:  # pragma: no cover - detached HEAD or no git
        pytest.skip("no named branch available to assert against")

    result = run(hook)

    assert result.returncode == 0, result.stderr
    assert f"({branch})" in result.stdout, (
        f"label should carry the branch {branch!r}; got {result.stdout!r}"
    )


@pytest.mark.parametrize("hook", _BOTH_HOOKS)
def test_label_falls_back_to_claude_project_dir_outside_a_repo(run, hook, tmp_path):
    """Outside a git tree the label falls back rather than emitting nothing."""
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    project = tmp_path / "my-project"
    project.mkdir()

    result = run(hook, env_extra={"CLAUDE_PROJECT_DIR": str(project)}, cwd=outside)

    assert result.returncode == 0, result.stderr
    assert "my-project" in result.stdout, (
        f"expected the CLAUDE_PROJECT_DIR fallback; got {result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Defect 2: the kill switch works without the process environment
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("hook", _BOTH_HOOKS)
def test_switch_file_silences_without_any_env_var(run, hook, tmp_path):
    """The whole point of the file switch.

    An already-running editor keeps the environment block it launched with, so an
    env-var opt-out never reaches it. The hook stats this file on every
    invocation instead. Note that NEXUS_DISABLED_HOOKS and NEXUS_HOOK_PROFILE are
    deliberately absent from the environment here.
    """
    switch = tmp_path / "notifications-disabled"
    switch.write_text("", encoding="utf-8")

    result = run(hook, env_extra={"NEXUS_NOTIFY_DISABLED_FILE": str(switch)})

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", (
        f"switch file present but the hook still notified: {result.stdout!r}"
    )


@pytest.mark.parametrize("hook", _BOTH_HOOKS)
def test_default_switch_path_is_honored_under_a_redirected_home(run, hook, tmp_path):
    """The DEFAULT ~/.nexus-hub/notifications-disabled path, not the override.

    Every other suppression test sets NEXUS_NOTIFY_DISABLED_FILE explicitly,
    which meant the default-path branch was never executed. That branch is where
    the PowerShell implementation resolved the home directory, and it had a real
    defect: it assigned to `$home`, a readonly automatic variable.
    """
    fake_home = tmp_path / "home"
    (fake_home / ".nexus-hub").mkdir(parents=True)
    (fake_home / ".nexus-hub" / "notifications-disabled").write_text("", encoding="utf-8")

    result = run(
        hook,
        env_extra={"HOME": str(fake_home), "USERPROFILE": str(fake_home)},
        clear_switch_override=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", (
        f"default switch path not honored; hook still notified: {result.stdout!r}"
    )


@pytest.mark.parametrize("hook", _BOTH_HOOKS)
def test_default_switch_path_absent_still_notifies(run, hook, tmp_path):
    """The inverse, so the test above cannot pass by accidentally silencing everything."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    result = run(
        hook,
        env_extra={"HOME": str(fake_home), "USERPROFILE": str(fake_home)},
        clear_switch_override=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() != "", "no switch file present, so the hook should notify"


@pytest.mark.parametrize("hook", _BOTH_HOOKS)
def test_disabled_hooks_env_still_honored(run, hook):
    """Backward compatibility: the pre-v3.15.10 opt-out keeps working."""
    result = run(hook, env_extra={"NEXUS_DISABLED_HOOKS": hook})

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ""


@pytest.mark.parametrize("hook", _BOTH_HOOKS)
def test_minimal_profile_silences(run, hook):
    result = run(hook, env_extra={"NEXUS_HOOK_PROFILE": "minimal"})

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ""


@pytest.mark.parametrize("hook", _BOTH_HOOKS)
def test_unrelated_disabled_hook_name_does_not_silence(run, hook):
    """A substring or a neighbouring hook name must not suppress this one."""
    result = run(hook, env_extra={"NEXUS_DISABLED_HOOKS": "some-other-hook"})

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() != ""


# ---------------------------------------------------------------------------
# Trigger identity and the always-exit-0 invariant
# ---------------------------------------------------------------------------


def test_the_two_triggers_say_different_things(run):
    """Trigger A means "blocked on you"; trigger B means "finished"."""
    complete = run(_COMPLETE).stdout
    attention = run(_ATTENTION).stdout

    assert "Task complete" in complete, complete
    assert "Needs your input" in attention, attention
    assert complete != attention


@pytest.mark.parametrize("hook", _BOTH_HOOKS)
@pytest.mark.parametrize(
    "payload",
    ["", "{}", "not json at all", '{"session_duration":"5m"}', '{"unclosed":'],
)
def test_always_exits_zero_on_any_payload(run, hook, payload):
    """A notification must never fail a turn, whatever arrives on stdin."""
    result = run(hook, payload=payload)

    assert result.returncode == 0, (
        f"{hook} exited {result.returncode} on payload {payload!r}: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Defect 3: registration -- what must and must not be wired
# ---------------------------------------------------------------------------


def _registered_commands() -> dict[str, list[str]]:
    data = json.loads(_SETTINGS.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for event, matchers in data.get("hooks", {}).items():
        cmds: list[str] = []
        for matcher in matchers:
            for hook in matcher.get("hooks", []):
                cmds.append(hook.get("command", ""))
        out[event] = cmds
    return out


def test_notification_chain_registers_the_attention_hook():
    events = _registered_commands()

    assert "Notification" in events, "the Notification event is not registered"
    assert any(f"{_ATTENTION}.sh" in c for c in events["Notification"]), (
        f"Notification chain does not run {_ATTENTION}.sh: {events['Notification']}"
    )


def test_stop_chain_registers_the_completion_hook():
    events = _registered_commands()

    assert any(f"{_COMPLETE}.sh" in c for c in events.get("Stop", [])), (
        f"Stop chain does not run {_COMPLETE}.sh: {events.get('Stop')}"
    )


def test_subagentstop_is_not_registered_at_all():
    """The single change most likely to reintroduce the notification storm.

    A sub-agent finishing is a sub-task milestone, not a reason to interrupt a
    human. This is asserted rather than merely documented.
    """
    events = _registered_commands()

    assert "SubagentStop" not in events, (
        "SubagentStop is registered; a sub-task completion must never notify"
    )


def test_no_notification_hook_rides_a_per_tool_event():
    """Neither notifier may be wired to a per-tool-call event."""
    events = _registered_commands()

    for event in ("PreToolUse", "PostToolUse"):
        for cmd in events.get(event, []):
            assert _COMPLETE not in cmd and _ATTENTION not in cmd, (
                f"{event} runs a notification hook ({cmd}); that notifies per tool call"
            )


def test_shared_helper_is_not_registered_as_a_hook():
    """_notify_common is a module, not a hook. Registering it would be a no-op run."""
    events = _registered_commands()

    for cmds in events.values():
        for cmd in cmds:
            assert "_notify_common" not in cmd, f"shared helper registered as a hook: {cmd}"
