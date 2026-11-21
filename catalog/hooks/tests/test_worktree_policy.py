"""Tests for the worktree-policy guard pair and its _worktree_policy.py helper.

Each behavioral case runs the real .sh and the real .ps1 as separate processes, so
every assertion is also an exit-code parity assertion. The delivery cases copy the
payload to an isolated directory with no path back to the source tree.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = HOOKS_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations._hooks_common import sourced_modules  # noqa: E402

PAYLOAD_FILES = ("worktree-policy.sh", "worktree-policy.ps1", "_worktree_policy.py")


def _load_helper():
    spec = importlib.util.spec_from_file_location(
        "_worktree_policy", HOOKS_DIR / "_worktree_policy.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["_worktree_policy"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    home = tmp_path / "home"
    home.mkdir()
    environment = {**os.environ}
    environment.update(
        HOME=str(home), USERPROFILE=str(home), NEXUS_HUB_HOME=str(home / ".nexus-hub")
    )
    environment["NEXUS_WORKTREE_ROOT"] = str(tmp_path / "central")
    for key in ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE"):
        environment.pop(key, None)
    return environment


def payload(command: str, cwd: Path, **extra: object) -> str:
    return json.dumps(
        {
            "tool_name": "Bash",
            "cwd": str(cwd),
            "tool_input": {"command": command},
            **extra,
        }
    )


def run_pair(
    bash_bin: str,
    powershell_bin: str,
    body: str,
    env: dict[str, str],
    cwd: Path,
    hooks: Path = HOOKS_DIR,
) -> tuple[int, int, str, str]:
    sh = subprocess.run(
        [bash_bin, str(hooks / "worktree-policy.sh")],
        input=body,
        text=True,
        capture_output=True,
        cwd=cwd,
        env=env,
        timeout=180,
        encoding="utf-8",
    )
    ps = subprocess.run(
        [powershell_bin, "-NoProfile", "-File", str(hooks / "worktree-policy.ps1")],
        input=body,
        text=True,
        capture_output=True,
        cwd=cwd,
        env=env,
        timeout=180,
        encoding="utf-8",
    )
    return sh.returncode, ps.returncode, sh.stderr, ps.stderr


def cases(central: Path) -> list[tuple[str, int]]:
    good = central / "app-0123abcd" / "feat"
    return [
        ("git status", 0),
        ("git worktree list", 0),
        ("git worktree prune", 0),
        (f'git worktree add -b feat "{good}" main', 0),
        (f"git -C repo worktree add {good} -b other", 0),
        (f"cd repo && git worktree add {good}2 HEAD", 0),
        (f"git commit -m 'document git worktree add ../x here'", 0),
        ("git worktree add ../sibling-wt", 2),
        ("git worktree add -b x .claude/worktrees/x", 2),
        ("git worktree add $HOME/x", 2),
        (f"git worktree add {central}/direct", 2),
        (f"git worktree add {central}/app-0123abcd/a/b", 2),
        (f"git -C repo worktree move old ../new", 2),
        (f"git worktree move old {good}3", 0),
        ('bash -c "git worktree add ../x"', 2),
        ('eval "git worktree add ../x"', 2),
        ("echo $(git worktree add ../x)", 2),
        ("git worktree add", 2),
    ]


def test_policy_table_through_both_wrappers(
    bash_bin: str, powershell_bin: str, env: dict[str, str], tmp_path: Path
) -> None:
    work = tmp_path / "work"
    work.mkdir()
    for command, expected in cases(tmp_path / "central"):
        sh_rc, ps_rc, sh_err, ps_err = run_pair(
            bash_bin, powershell_bin, payload(command, work), env, work
        )
        assert (sh_rc, ps_rc) == (expected, expected), (command, sh_err, ps_err)
        if expected == 2:
            assert (
                sh_err.startswith("[Nexus-Hub: worktree-policy] BLOCKED")
                and "nexus-hub worktree create" in sh_err
            )
            assert ps_err.startswith("[Nexus-Hub: worktree-policy] BLOCKED")


def test_windows_style_paths_and_quoting_are_understood(
    env: dict[str, str], tmp_path: Path
) -> None:
    helper = _load_helper()
    os.environ.update(env)
    central = tmp_path / "central"
    ok = str(central / "app-0123abcd" / "my tree")
    assert helper.evaluate(f'git worktree add "{ok}" -b "x y"', str(tmp_path)) == 0
    assert helper.evaluate(f"git worktree add '{ok}2' -b z", str(tmp_path)) == 0
    assert (
        helper.evaluate(
            f"powershell -NoProfile -Command \"git worktree add '{ok}3'\"",
            str(tmp_path),
        )
        == 2
    )
    assert helper.evaluate("git worktree add ..\\sibling", str(tmp_path)) == 2


def test_invalid_root_denies_a_worktree_mutation_but_not_other_commands(
    bash_bin: str, powershell_bin: str, env: dict[str, str], tmp_path: Path
) -> None:
    env = {**env, "NEXUS_WORKTREE_ROOT": "relative/place"}
    work = tmp_path / "work"
    work.mkdir()
    assert run_pair(
        bash_bin, powershell_bin, payload("git worktree add x", work), env, work
    )[:2] == (2, 2)
    assert run_pair(bash_bin, powershell_bin, payload("git status", work), env, work)[
        :2
    ] == (0, 0)


@pytest.mark.parametrize(
    "control",
    [
        {"NEXUS_HOOK_PROFILE": "minimal"},
        {"NEXUS_DISABLED_HOOKS": "worktree-policy"},
        {"NEXUS_HOOK_PROFILE": "minimal", "NEXUS_DISABLED_HOOKS": "worktree-policy"},
    ],
)
def test_guard_is_mandatory_under_the_minimal_profile_and_disable_list(
    bash_bin: str,
    powershell_bin: str,
    env: dict[str, str],
    tmp_path: Path,
    control: dict[str, str],
) -> None:
    work = tmp_path / "work"
    work.mkdir()
    sh_rc, ps_rc, _, _ = run_pair(
        bash_bin,
        powershell_bin,
        payload("git worktree add ../out-of-policy", work),
        {**env, **control},
        work,
    )
    assert (sh_rc, ps_rc) == (2, 2)


@pytest.mark.parametrize("mode", ["default", "auto", "dontAsk", "bypassPermissions"])
def test_guard_applies_in_every_host_permission_mode(
    bash_bin: str, powershell_bin: str, env: dict[str, str], tmp_path: Path, mode: str
) -> None:
    work = tmp_path / "work"
    work.mkdir()
    body = payload("git worktree add ../out-of-policy", work, permission_mode=mode)
    assert run_pair(bash_bin, powershell_bin, body, env, work)[:2] == (2, 2)


def test_explicit_root_override_is_the_only_override(
    bash_bin: str, powershell_bin: str, env: dict[str, str], tmp_path: Path
) -> None:
    work = tmp_path / "work"
    work.mkdir()
    other = tmp_path / "elsewhere"
    target = other / "app-0123abcd" / "wt"
    body = payload(f"git worktree add {target}", work)
    assert run_pair(bash_bin, powershell_bin, body, env, work)[:2] == (2, 2)
    assert run_pair(
        bash_bin, powershell_bin, body, {**env, "NEXUS_WORKTREE_ROOT": str(other)}, work
    )[:2] == (0, 0)
    config = Path(env["NEXUS_HUB_HOME"]) / "config"
    config.mkdir(parents=True)
    (config / "worktrees.json").write_text(
        json.dumps({"root": str(other)}), encoding="utf-8"
    )
    no_env = {k: v for k, v in env.items() if k != "NEXUS_WORKTREE_ROOT"}
    assert run_pair(bash_bin, powershell_bin, body, no_env, work)[:2] == (0, 0)


def test_repository_file_cannot_set_policy(
    bash_bin: str, powershell_bin: str, env: dict[str, str], tmp_path: Path
) -> None:
    work = tmp_path / "work"
    work.mkdir()
    (work / ".nexus-worktrees.json").write_text(
        json.dumps({"root": str(work)}), encoding="utf-8"
    )
    (work / "worktrees.json").write_text(
        json.dumps({"root": str(work)}), encoding="utf-8"
    )
    assert run_pair(
        bash_bin,
        powershell_bin,
        payload(f"git worktree add {work}/a/b", work),
        env,
        work,
    )[:2] == (2, 2)


def test_malformed_and_absent_payloads(
    bash_bin: str, powershell_bin: str, env: dict[str, str], tmp_path: Path
) -> None:
    work = tmp_path / "work"
    work.mkdir()
    for body, expected in (
        ("", 0),
        ("not json", 0),
        ("{}", 0),
        ('{"tool_input": {"command": 5}}', 0),
        ("garbage git worktree add ../x", 2),
    ):
        assert run_pair(bash_bin, powershell_bin, body, env, work)[:2] == (
            expected,
            expected,
        ), body


def test_missing_interpreter_cannot_certify_a_worktree_mutation(
    bash_bin: str, powershell_bin: str, env: dict[str, str], tmp_path: Path
) -> None:
    empty = tmp_path / "empty-path"
    empty.mkdir()
    bare_env = {**env, "PATH": str(empty)}
    work = tmp_path / "work"
    work.mkdir()
    bad, good = payload("git worktree add ../x", work), payload("git status", work)
    for runner in (
        lambda b: subprocess.run(
            [bash_bin, str(HOOKS_DIR / "worktree-policy.sh")],
            input=b,
            text=True,
            capture_output=True,
            cwd=work,
            env=bare_env,
            timeout=120,
        ),
        lambda b: subprocess.run(
            [
                powershell_bin,
                "-NoProfile",
                "-File",
                str(HOOKS_DIR / "worktree-policy.ps1"),
            ],
            input=b,
            text=True,
            capture_output=True,
            cwd=work,
            env=bare_env,
            timeout=120,
        ),
    ):
        denied, allowed = runner(bad), runner(good)
        assert denied.returncode == 2 and "no Python interpreter" in denied.stderr
        assert allowed.returncode == 0


def test_slow_inputs_do_not_hang_unrelated_commands(
    env: dict[str, str], tmp_path: Path
) -> None:
    helper = _load_helper()
    os.environ.update(env)
    long_unrelated = "echo " + "x" * 200000 + "; git status"
    assert helper.evaluate(long_unrelated, str(tmp_path)) == 0


def test_helper_creates_no_files_and_runs_no_process(
    env: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    helper = _load_helper()
    os.environ.update(env)

    def boom(*_a: object, **_k: object) -> None:
        raise AssertionError("the helper started a process")

    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(subprocess, "Popen", boom)
    before = sorted(p.name for p in tmp_path.iterdir())
    assert (
        helper.evaluate(
            f"git worktree add {tmp_path}/central/app-0123abcd/x", str(tmp_path)
        )
        == 0
    )
    assert helper.evaluate("git worktree add ../x", str(tmp_path)) == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == before


# --------------------------------------------------------------------------- delivery


def test_helper_is_collected_from_the_sh_wrapper_alone(tmp_path: Path) -> None:
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    for name in ("_worktree_policy.py", "worktree-policy.sh"):
        shutil.copy2(HOOKS_DIR / name, hooks / name)
    assert sourced_modules({"worktree-policy.sh"}, hooks) == {"_worktree_policy.py"}


def test_helper_is_collected_from_the_ps1_wrapper_alone(tmp_path: Path) -> None:
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    for name in ("_worktree_policy.py", "worktree-policy.ps1"):
        shutil.copy2(HOOKS_DIR / name, hooks / name)
    assert sourced_modules({"worktree-policy.ps1"}, hooks) == {"_worktree_policy.py"}


@pytest.mark.parametrize("wrapper", ["worktree-policy.sh", "worktree-policy.ps1"])
def test_comment_only_helper_reference_is_not_collected(
    tmp_path: Path, wrapper: str
) -> None:
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    shutil.copy2(HOOKS_DIR / "_worktree_policy.py", hooks / "_worktree_policy.py")
    (hooks / wrapper).write_text(
        "# calls _worktree_policy.py\nexit 0\n", encoding="utf-8"
    )
    assert sourced_modules({wrapper}, hooks) == set()


@pytest.mark.parametrize("wrapper", ["worktree-policy.sh", "worktree-policy.ps1"])
def test_wrapper_names_the_helper_in_executable_text(wrapper: str) -> None:
    code = [
        line
        for line in (HOOKS_DIR / wrapper).read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("#")
    ]
    assert any("_worktree_policy.py" in line for line in code)


def test_isolated_copied_payload_runs_with_no_source_back_reference(
    bash_bin: str, powershell_bin: str, env: dict[str, str], tmp_path: Path
) -> None:
    delivered = tmp_path / "delivered" / ".claude" / "hooks"
    delivered.mkdir(parents=True)
    for name in sorted(
        sourced_modules({"worktree-policy.sh", "worktree-policy.ps1"}, HOOKS_DIR)
        | {"worktree-policy.sh", "worktree-policy.ps1"}
    ):
        shutil.copy2(HOOKS_DIR / name, delivered / name)
    assert {p.name for p in delivered.iterdir()} == set(PAYLOAD_FILES)
    text = "".join((delivered / n).read_text(encoding="utf-8") for n in PAYLOAD_FILES)
    assert str(REPO_ROOT) not in text and "catalog/hooks" not in text.replace(
        "docs/runbooks", ""
    )
    work = tmp_path / "somewhere-else"
    work.mkdir()
    clean = {k: v for k, v in env.items() if k != "PYTHONPATH"}
    denied = run_pair(
        bash_bin,
        powershell_bin,
        payload("git worktree add ../x", work),
        clean,
        work,
        hooks=delivered,
    )
    allowed = run_pair(
        bash_bin,
        powershell_bin,
        payload(f"git worktree add {tmp_path}/central/app-0123abcd/ok", work),
        clean,
        work,
        hooks=delivered,
    )
    assert denied[:2] == (2, 2) and allowed[:2] == (0, 0)


def test_helper_and_cli_agree_on_root_validation(
    env: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The delivered helper duplicates the root rules; a drift here means two policies."""
    from scripts import nexus_worktrees as nw

    helper = _load_helper()
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    bad_root = tmp_path / "repo-root"
    (bad_root / ".git").mkdir(parents=True)
    candidates = [
        str(tmp_path / "ok"),
        "relative/path",
        "//server/share",
        str(tmp_path / ".claude" / "x"),
        str(bad_root / "wt"),
        str(tmp_path / "OneDrive - X" / "wt"),
        str(tmp_path / "a" / ".." / "b"),
        str(Path(env["NEXUS_HUB_HOME"]) / "wt"),
    ]
    for value in candidates:
        try:
            nw.validate_root(value, "test")
            cli_ok = True
        except nw.PolicyError:
            cli_ok = False
        try:
            helper.validate_root(value, "test")
            hook_ok = True
        except helper.Denied:
            hook_ok = False
        assert cli_ok == hook_ok, value
# --------------------------------------------------------------------------- hardening after review

APPROVE_BODY = "migrate --approve --manifest m.json --expect-sha256 abc --item a --item b --approver me"


def hardening_cases(central: Path) -> list[tuple[str, int]]:
    good = central / "app-0123abcd" / "feat"
    return [
        # quoted text and heredoc bodies are text, not commands
        ('git commit -m "docs: explain git worktree move behavior"', 0),
        (
            "git commit -m 'uses `git worktree add ../x` and $(git worktree move a b) in text'",
            0,
        ),
        (
            "git commit -F - <<'EOF'\nfix: notes mention `git worktree move a b` and $(git worktree add ../y)\ngit worktree add ../z\nEOF",
            0,
        ),
        ("bash <<'EOF'\ngit worktree add ../x\nEOF", 2),
        ("echo $(git worktree add ../x)", 2),
        # a relative destination after a directory change cannot be certified
        (f"cd repo && git worktree add {good}", 0),
        ("cd repo && git worktree add wt", 2),
        ("pushd repo; git worktree add wt", 2),
        ("Set-Location repo; git worktree add wt", 2),
        ("sl repo; git worktree add wt", 2),
        ("chdir repo && git worktree add wt", 2),
        ("(cd repo; git worktree add wt)", 2),
        # approval is a human step
        (f"nexus-hub worktree {APPROVE_BODY}", 2),
        (f"nexus-hub.cmd worktree {APPROVE_BODY}", 2),
        (f"python -B scripts/nexus_worktrees.py {APPROVE_BODY}", 2),
        (f'bash -c "nexus-hub worktree {APPROVE_BODY}"', 2),
        (
            "nexus-hub worktree migrate --dry-run --inventory a.json --manifest b.json",
            0,
        ),
        ("nexus-hub worktree migrate --apply --manifest m.json --expect-sha256 abc", 0),
        (
            'git commit -m "docs: nexus-hub worktree migrate --approve is a human step"',
            0,
        ),
    ]


def test_hardening_cases_through_both_wrappers(
    bash_bin: str, powershell_bin: str, env: dict[str, str], tmp_path: Path
) -> None:
    work = tmp_path / "work"
    work.mkdir()
    for command, expected in hardening_cases(tmp_path / "central"):
        sh_rc, ps_rc, sh_err, ps_err = run_pair(
            bash_bin, powershell_bin, payload(command, work), env, work
        )
        assert (sh_rc, ps_rc) == (expected, expected), (command, sh_err, ps_err)
        if expected == 2 and "--approve" in command:
            assert "human step" in sh_err and "human step" in ps_err


def test_relative_destination_without_a_directory_change_still_resolves(
    bash_bin: str, powershell_bin: str, env: dict[str, str], tmp_path: Path
) -> None:
    inside = tmp_path / "central" / "app-0123abcd"
    inside.mkdir(parents=True)
    assert run_pair(
        bash_bin,
        powershell_bin,
        payload("git worktree add newwt -b n", inside),
        env,
        inside,
    )[:2] == (0, 0)
    for change in ("cd .", "pushd .", "Set-Location .", "sl .", "chdir ."):
        sh_rc, ps_rc, _, _ = run_pair(
            bash_bin,
            powershell_bin,
            payload(f"{change}; git worktree add newwt", inside),
            env,
            inside,
        )
        assert (sh_rc, ps_rc) == (2, 2), change


def test_powershell_tool_payloads_use_powershell_quoting_rules(
    bash_bin: str, powershell_bin: str, env: dict[str, str], tmp_path: Path
) -> None:
    work = tmp_path / "work"
    work.mkdir()
    here_string = "git commit -m @'\nnotes: git worktree move a b with a `backtick` and git worktree add ../x\n'@"
    backtick_text = 'git commit -m "mentions `git worktree move` in markdown"'
    for command, expected in (
        (here_string, 0),
        (backtick_text, 0),
        ("Set-Location repo; git worktree add wt", 2),
        (f"nexus-hub worktree {APPROVE_BODY}", 2),
    ):
        body = payload(command, work, tool_name="PowerShell")
        sh_rc, ps_rc, sh_err, ps_err = run_pair(
            bash_bin, powershell_bin, body, env, work
        )
        assert (sh_rc, ps_rc) == (expected, expected), (command, sh_err, ps_err)
