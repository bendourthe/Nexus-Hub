"""Tests for catalog/hooks/git-guardrails.{sh,ps1}.

Covers:

  * the existing dangerous-pattern blocking (regression),
  * the opt-in protected-branch guard added for the develop+main workflow,
  * the v3.15.6 Phase 2 execution-indirection patterns (AC4): core.hooksPath and
    core.fsmonitor in both the inline `git -c key=value` form and the persistent
    `git config` form, which is group B of the canonical execution-trigger
    surface list in
    catalog/skills/security-operations/agentic-endpoint-hardening/SKILL.md,
  * the false-positive guards that matter for group B: a READ of the same key
    (`git config --get core.hooksPath`) and a benign `-c` option must both be
    allowed, or the guardrail becomes an obstacle to ordinary work,
  * the v4.14.4 opt-in bypass-flag mode, generated from the decision table in
    docs/decisions/*/tooling/2026-10-14-opt-in-git-bypass-flag-guard.md: every
    blocked form with the mode on and off, every allowed form, the switch file read
    on every run, the environment override, a malformed file, and the PowerShell
    tool payload for each existing block family.

Every test runs against BOTH the bash hook and its PowerShell sibling via the
`run` fixture, so the suite is also the .sh/.ps1 parity check. A missing
interpreter skips only that parameter.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_git_guardrails.py -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_HOOK_SH = _HOOKS_DIR / "git-guardrails.sh"
_HOOK_PS1 = _HOOKS_DIR / "git-guardrails.ps1"

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None, reason="git-guardrails requires git on PATH"
)

_ALLOW = 0
_BLOCK = 2


@pytest.fixture()
def home(tmp_path: Path) -> Path:
    """A throwaway home, so no test reads the real ~/.nexus-hub/guardrails.json."""
    h = tmp_path / "home"
    h.mkdir()
    return h


@pytest.fixture()
def workdir(tmp_path: Path) -> Path:
    """A plain directory to run from: the bypass-flag mode never calls git, so it needs no repo."""
    w = tmp_path / "work"
    w.mkdir()
    return w


@pytest.fixture(params=["sh", "ps1"])
def run(request, home: Path):
    """Invoke either hook implementation with a PreToolUse payload (Bash by default)."""
    if request.param == "sh":
        prefix = [request.getfixturevalue("bash_bin"), str(_HOOK_SH)]
    else:
        prefix = [
            request.getfixturevalue("powershell_bin"),
            "-NoProfile",
            "-File",
            str(_HOOK_PS1),
        ]

    def _run(
        command: str,
        cwd: Path,
        env_extra: dict[str, str] | None = None,
        tool_name: str = "Bash",
        permission_mode: str | None = None,
    ) -> subprocess.CompletedProcess:
        body: dict[str, object] = {"tool_name": tool_name, "tool_input": {"command": command}}
        if permission_mode is not None:
            body["permission_mode"] = permission_mode
        payload = json.dumps(body)
        env = {**os.environ}
        for key in (
            "NEXUS_PROTECTED_BRANCHES",
            "NEXUS_PROTECTED_BRANCH_ALLOW",
            "NEXUS_GUARD_GIT_BYPASS",
        ):
            env.pop(key, None)
        # The switch file is read from the home directory, so point both variables at it.
        env["HOME"] = env["USERPROFILE"] = str(home)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            prefix,
            input=payload,
            text=True,
            capture_output=True,
            cwd=str(cwd),
            env=env,
            timeout=120,
        )

    return _run


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=str(repo), check=True, capture_output=True, text=True
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A throwaway git repo with main, develop, and feat-x branches."""
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init")
    _git(r, "config", "user.email", "t@example.com")
    _git(r, "config", "user.name", "tester")
    (r / "f.txt").write_text("x\n", encoding="utf-8")
    _git(r, "add", "f.txt")
    _git(r, "commit", "-m", "init")
    _git(r, "branch", "-M", "main")
    _git(r, "branch", "develop")
    _git(r, "branch", "feat-x")
    return r


# --- existing dangerous-pattern behavior (regression) ---


def test_force_push_blocked(run, repo: Path) -> None:
    res = run("git push --force origin main", repo)
    assert res.returncode == _BLOCK
    assert "BLOCKED" in res.stderr


def test_safe_command_allowed(run, repo: Path) -> None:
    assert run("git status", repo).returncode == _ALLOW


@pytest.mark.parametrize(
    "command",
    [
        "git reset --hard HEAD~1",
        "git clean -fd",
        "git branch -D feat-x",
        "git stash drop",
        "git stash clear",
        "rm -rf .git",
    ],
)
def test_destructive_patterns_still_blocked(run, repo: Path, command: str) -> None:
    assert run(command, repo).returncode == _BLOCK, f"regressed: {command}"


# --- v3.15.6 AC4: execution indirection via git metadata (group B) ---


@pytest.mark.parametrize(
    "command",
    [
        "git -c core.hooksPath=/tmp/evil status",
        "git -c core.fsmonitor=evil.sh status",
        # Interleaving another -c option must not be an evasion.
        "git -c protocol.version=2 -c core.hooksPath=/tmp/x status",
        "git -c http.sslVerify=false -c core.fsmonitor=x.sh diff",
        # Spacing around the assignment must not be an evasion.
        "git -c core.hooksPath = /tmp/x status",
    ],
)
def test_inline_execution_indirection_blocked(run, repo: Path, command: str) -> None:
    """`git -c core.hooksPath=` / `core.fsmonitor=` name something git EXECUTES."""
    res = run(command, repo)
    assert res.returncode == _BLOCK, f"not blocked: {command}"
    assert "BLOCKED" in res.stderr


@pytest.mark.parametrize(
    "command",
    [
        "git config core.hooksPath .githooks",
        "git config --local core.fsmonitor evil.sh",
        "git config --global core.hooksPath /tmp/x",
        "git config --add core.hooksPath .githooks",
    ],
)
def test_persistent_execution_indirection_blocked(
    run, repo: Path, command: str
) -> None:
    """The `git config` form persists into .git/config and applies to every later
    operation, so it needs its own check beyond the inline `-c` patterns."""
    res = run(command, repo)
    assert res.returncode == _BLOCK, f"not blocked: {command}"
    assert "execution-indirection" in res.stderr


# --- AC4 false-positive guards (a denylist that blocks real work is a liability) ---


@pytest.mark.parametrize(
    "command",
    [
        # Reads of the same key are harmless and must stay allowed.
        "git config --get core.hooksPath",
        "git config --get-all core.fsmonitor",
        "git config --get-regexp core.*",
        "git config --list",
        "git config --unset core.hooksPath",
        # Benign -c options must stay allowed.
        "git -c user.name=Bob commit -m x",
        "git -c core.pager=cat log",
        "git -c core.autocrlf=false checkout feat-x",
        # Ordinary config writes to unrelated keys.
        "git config user.email a@b.c",
        "git config core.autocrlf false",
    ],
)
def test_benign_git_commands_allowed(run, repo: Path, command: str) -> None:
    res = run(command, repo)
    assert res.returncode == _ALLOW, (
        f"false positive on a benign command: {command} (stderr={res.stderr!r})"
    )


# --- opt-in protected-branch guard ---


def test_guard_inert_without_env(run, repo: Path) -> None:
    """With no NEXUS_PROTECTED_BRANCHES, committing on main is allowed."""
    _git(repo, "checkout", "main")
    assert run('git commit -m "x"', repo).returncode == _ALLOW


def test_guard_blocks_commit_on_protected(run, repo: Path) -> None:
    _git(repo, "checkout", "main")
    res = run('git commit -m "x"', repo, {"NEXUS_PROTECTED_BRANCHES": "main"})
    assert res.returncode == _BLOCK
    assert "protected branch 'main'" in res.stderr


def test_guard_allows_commit_on_feature_branch(run, repo: Path) -> None:
    _git(repo, "checkout", "feat-x")
    res = run('git commit -m "x"', repo, {"NEXUS_PROTECTED_BRANCHES": "main"})
    assert res.returncode == _ALLOW


def test_guard_override_allows_one_commit(run, repo: Path) -> None:
    _git(repo, "checkout", "main")
    res = run(
        'git commit -m "x"',
        repo,
        {"NEXUS_PROTECTED_BRANCHES": "main", "NEXUS_PROTECTED_BRANCH_ALLOW": "1"},
    )
    assert res.returncode == _ALLOW


def test_guard_does_not_block_merge(run, repo: Path) -> None:
    """Release merges onto the protected branch are intentionally allowed."""
    _git(repo, "checkout", "main")
    res = run("git merge --no-ff develop", repo, {"NEXUS_PROTECTED_BRANCHES": "main"})
    assert res.returncode == _ALLOW


def test_guard_accepts_comma_separated_list(run, repo: Path) -> None:
    _git(repo, "checkout", "develop")
    res = run('git commit -m "x"', repo, {"NEXUS_PROTECTED_BRANCHES": "main,develop"})
    assert res.returncode == _BLOCK


# --- quiet paths ---


@pytest.mark.parametrize("payload_cmd", ["", "   "])
def test_no_command_is_allowed(run, repo: Path, payload_cmd: str) -> None:
    """A payload without a usable command must not block non-Bash tools."""
    assert run(payload_cmd, repo).returncode == _ALLOW


# ---------------------------------------------------------------------------
# Written-content precision (heredoc bodies)
#
# A command that WRITES a file carries the file's text in the same raw string the
# patterns match against, so documentation that merely NAMES a destructive
# command used to read as an attempt to RUN one. That is not hypothetical: it
# blocked an ordinary docs write, and a guard that blocks documentation is a
# guard that gets switched off.
#
# The dangerous strings below are ASSEMBLED at runtime so this test file does not
# itself trip a scanner that reads it as text.
# ---------------------------------------------------------------------------

_RESET = "git " + "reset " + "--hard"
_CFG_WRITE = "git " + "config core." + "hooksPath=/tmp/x"
_NL = chr(10)
_CRNL = chr(13) + chr(10)
_TAB = chr(9)


def test_destructive_command_still_blocks(run, repo):
    """Regression floor: the real invocation must keep blocking."""
    assert run(_RESET + " HEAD~1", repo).returncode == _BLOCK


def test_pattern_inside_heredoc_body_is_allowed(run, repo):
    """Prose naming a destructive command is a write, not an invocation."""
    cmd = "cat > doc.md <<'EOF'" + _NL + "Never run " + _RESET + " here." + _NL + "EOF"
    assert run(cmd, repo).returncode == _ALLOW


def test_pattern_inside_heredoc_body_still_warns(run, repo):
    """Allowing the write must not make the signal disappear.

    This is what keeps the change in the safe direction: the blocking scan
    matches less, but nothing is silently dropped.
    """
    cmd = "cat > doc.md <<'EOF'" + _NL + "Never run " + _RESET + " here." + _NL + "EOF"
    proc = run(cmd, repo)
    assert proc.returncode == _ALLOW
    assert "written file content" in proc.stderr


def test_crlf_heredoc_still_blocks_the_command_after_it(run, repo):
    """A CRLF payload must not swallow the rest of the script.

    Regression: the guard FAILED OPEN here. With CRLF the closing delimiter arrives
    as "EOF" plus a carriage return, never equals "EOF", so the body never ends and
    every later line goes unscanned - including a destructive command placed after
    the heredoc. It reached CI's Windows leg only: that runner has jq and returns
    real carriage returns, while a host without jq took the fallback, which decoded
    \n but not \r. Both paths now drop them.
    """
    cmd = "cat > d.md <<'EOF'" + _CRNL + "notes" + _CRNL + "EOF" + _CRNL + _RESET
    assert run(cmd, repo).returncode == _BLOCK


def test_real_command_after_a_heredoc_still_blocks(run, repo):
    """Closing a heredoc must resume scanning, or the body becomes an evasion."""
    cmd = "cat > d.md <<'EOF'" + _NL + "notes" + _NL + "EOF" + _NL + _RESET
    assert run(cmd, repo).returncode == _BLOCK


@pytest.mark.parametrize(
    "opener,closer,indent",
    [
        ("<<'EOF'", "EOF", ""),
        ('<<"END"', "END", ""),
        ("<<-EOF", _TAB + "EOF", _TAB),
        ("<<EOF", "EOF", ""),
    ],
    ids=["single-quoted", "double-quoted", "dash-indented", "bare"],
)
def test_heredoc_delimiter_forms(run, repo, opener, closer, indent):
    """All four documented opener forms must strip their body."""
    cmd = "cat > c.md " + opener + _NL + indent + _RESET + _NL + closer
    assert run(cmd, repo).returncode == _ALLOW


def test_config_write_inside_heredoc_is_allowed(run, repo):
    """The execution-indirection guard reads the same stripped scan."""
    cmd = "cat > n.md <<'EOF'" + _NL + _CFG_WRITE + _NL + "EOF"
    assert run(cmd, repo).returncode == _ALLOW


def test_config_write_as_a_command_still_blocks(run, repo):
    assert run(_CFG_WRITE, repo).returncode == _BLOCK


def test_multiline_payload_is_decoded_faithfully(run, repo):
    """Guards the jq-absent fallback path in the .sh hook.

    Without JSON un-escaping, a multi-line command arrives as ONE line carrying a
    literal backslash-n, so every line-oriented check sees a single long line
    rather than a script. The .ps1 sibling never had this bug because
    ConvertFrom-Json decodes escapes, which is exactly why this assertion is
    parametrized over both implementations: it must hold with and without jq.
    """
    cmd = "echo one" + _NL + "echo two" + _NL + _RESET
    assert run(cmd, repo).returncode == _BLOCK


# ---------------------------------------------------------------------------
# v4.14.4: opt-in bypass-flag mode
#
# The two tables below ARE the decision table of
# docs/decisions/*/tooling/2026-10-14-opt-in-git-bypass-flag-guard.md. Every case runs
# through both implementations, so each row is also an exit-code parity assertion.
# ---------------------------------------------------------------------------

_NEWLINE_HEREDOC_BASH = "bash <<'EOF'" + _NL + "git commit --no-verify -m x" + _NL + "EOF"
_NEWLINE_HEREDOC_SH = "sh <<EOF" + _NL + "git commit -n -m x" + _NL + "EOF"

BLOCKED_FORMS = [
    # --no-verify on commit, push, merge, rebase, am, and unique abbreviations
    "git commit --no-verify",
    "git commit -m x --no-verify",
    'git commit -m "msg" --no-verify',
    "git push --no-verify origin main",
    "git merge --no-verify topic",
    "git rebase --no-verify main",
    "git am --no-verify x.patch",
    "git commit --no-verif -m x",
    "git commit --no-v -m x",
    # -n as a commit option, alone and in a cluster
    "git commit -n -m x",
    "git commit -an -m x",
    "git commit -nm x",
    "git commit -sn",
    'git commit -am "x" -n',
    # --no-gpg-sign
    "git commit --no-gpg-sign -m x",
    "git merge --no-gpg-sign topic",
    "git rebase --no-gpg-sign main",
    "git cherry-pick --no-gpg-sign abc123",
    "git revert --no-gpg-sign abc123",
    # inline and persistent gpgsign=false, key in any letter case
    "git -c commit.gpgsign=false commit -m x",
    "git -c COMMIT.GPGSIGN=FALSE commit -m x",
    "git -c commit.gpgsign=0 commit -m x",
    "git config commit.gpgsign false",
    "git config --global tag.gpgsign no",
    "git config --global --replace-all Commit.GpgSign 0",
    "git config commit.gpgsign off",
    # git global options, a path prefix, or .exe before the subcommand
    "git -C repo commit -n",
    'git -C "my repo" commit -n',
    "git --no-pager commit --no-verify",
    "git -c core.pager=cat -C repo commit -n",
    "git --git-dir=.git push --no-verify",
    "/usr/bin/git commit -n",
    "git.exe commit -n",
    # after a separator, on a later line, and across a line continuation
    "git add . && git commit -n -m x",
    "echo ok; git commit --no-verify",
    "git add ." + _NL + "git commit -n -m x",
    "git commit \\" + _NL + "-n",
    # inside a heredoc fed to an interpreter
    _NEWLINE_HEREDOC_BASH,
    _NEWLINE_HEREDOC_SH,
]

ALLOWED_FORMS = [
    "git push -n origin main",
    "git log -n 5",
    "git tag -n",
    "git commit --no-edit",
    "git commit --amend --no-edit",
    'git commit -m "explain --no-verify and -n"',
    "git commit -m 'it names -n and --no-verify'",
    'git commit --message="mentions --no-verify"',
    'git commit -am "explain -n"',
    "git commit -mn",
    "git commit -uno -m x",
    "git commit -S -m x",
    "git commit -am x",
    "git commit -m x",
    "git commit -F msg.txt",
    "git config commit.gpgsign true",
    "git config --get commit.gpgsign",
    "git -c commit.gpgsign=true commit -m x",
    "git merge --no-ff develop",
    "git rebase --no-autosquash main",
    "git status",
    "cat > notes.md <<'EOF'" + _NL + "Never pass --no-verify or -n." + _NL + "EOF",
]


def _switch(home: Path, content: str | bytes | None) -> Path:
    """Write (or remove, with None) ~/.nexus-hub/guardrails.json under the test home."""
    cfg = home / ".nexus-hub" / "guardrails.json"
    if content is None:
        cfg.unlink(missing_ok=True)
        return cfg
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    return cfg


_ON = '{"block_git_bypass_flags": true}'
_OFF = '{"block_git_bypass_flags": false}'


@pytest.mark.parametrize("command", BLOCKED_FORMS)
def test_bypass_forms_blocked_when_the_mode_is_on(run, workdir: Path, home: Path, command: str) -> None:
    _switch(home, _ON)
    res = run(command, workdir)
    assert res.returncode == _BLOCK, f"not blocked with the mode on: {command!r} (stderr={res.stderr!r})"
    assert "guardrails.json" in res.stderr and "NEXUS_GUARD_GIT_BYPASS" in res.stderr


@pytest.mark.parametrize("command", BLOCKED_FORMS)
def test_bypass_forms_allowed_when_the_mode_is_off(run, workdir: Path, home: Path, command: str) -> None:
    """No file at all (the default) leaves every form allowed: the mode is opt-in."""
    assert run(command, workdir).returncode == _ALLOW, f"blocked with the mode off: {command!r}"
    _switch(home, _OFF)
    assert run(command, workdir).returncode == _ALLOW, f"blocked with the file set false: {command!r}"


@pytest.mark.parametrize("command", ALLOWED_FORMS)
def test_allowed_forms_stay_allowed_when_the_mode_is_on(run, workdir: Path, home: Path, command: str) -> None:
    _switch(home, _ON)
    res = run(command, workdir)
    assert res.returncode == _ALLOW, f"false positive with the mode on: {command!r} (stderr={res.stderr!r})"


def test_the_switch_file_is_read_on_every_run(run, workdir: Path, home: Path) -> None:
    """Editing guardrails.json changes the very next command, with no restart."""
    command = "git commit -m x --no-verify"
    assert run(command, workdir).returncode == _ALLOW
    _switch(home, _ON)
    assert run(command, workdir).returncode == _BLOCK
    _switch(home, _OFF)
    assert run(command, workdir).returncode == _ALLOW
    _switch(home, _ON)
    assert run(command, workdir).returncode == _BLOCK
    _switch(home, None)
    assert run(command, workdir).returncode == _ALLOW


@pytest.mark.parametrize(
    "content",
    ['{"block_git_bypass_flags": "true"}', "{}", '{"other": true}', '{"block_git_bypass_flags": 1}'],
    ids=["string-true", "empty-object", "other-key", "number"],
)
def test_only_the_json_boolean_true_turns_the_mode_on(run, workdir: Path, home: Path, content: str) -> None:
    _switch(home, content)
    res = run("git commit -m x --no-verify", workdir)
    assert res.returncode == _ALLOW
    assert "guardrails.json" not in res.stderr, "a valid file must not warn"


def test_a_utf8_byte_order_mark_does_not_hide_the_switch(run, workdir: Path, home: Path) -> None:
    """Notepad and Windows PowerShell 5.1 write a BOM; the switch must still work."""
    _switch(home, b"\xef\xbb\xbf" + _ON.encode("utf-8"))
    assert run("git commit -m x --no-verify", workdir).returncode == _BLOCK


@pytest.mark.parametrize(
    "content",
    ["{not json", "not json at all", "[]", "", "true"],
    ids=["unclosed", "prose", "array", "empty", "scalar"],
)
def test_a_malformed_switch_file_means_off_with_one_warning(run, workdir: Path, home: Path, content: str) -> None:
    """A crash would block every command, so a bad file degrades to off and says so once."""
    _switch(home, content)
    res = run("git commit -m x --no-verify", workdir)
    assert res.returncode == _ALLOW
    assert res.stderr.count("guardrails.json") == 1, f"expected one warning naming the file: {res.stderr!r}"
    assert "BLOCKED" not in res.stderr


def test_a_malformed_file_is_not_read_for_a_command_that_never_mentions_git(run, workdir: Path, home: Path) -> None:
    _switch(home, "{not json")
    res = run("echo hello", workdir)
    assert res.returncode == _ALLOW
    assert res.stderr == ""


@pytest.mark.parametrize(
    "file_content,env_value,expected",
    [
        (_ON, "0", _ALLOW),
        (None, "1", _BLOCK),
        (_OFF, "1", _BLOCK),
        (_ON, "yes", _BLOCK),
        (_ON, "", _BLOCK),
        (_OFF, "yes", _ALLOW),
        ("{not json", "1", _BLOCK),
        ("{not json", "0", _ALLOW),
    ],
    ids=["env0-beats-file-on", "env1-no-file", "env1-beats-file-off", "env-other-defers-to-on",
         "env-empty-defers-to-on", "env-other-defers-to-off", "env1-skips-bad-file", "env0-skips-bad-file"],
)
def test_the_environment_override_wins_over_the_file(
    run, workdir: Path, home: Path, file_content: str | None, env_value: str, expected: int
) -> None:
    _switch(home, file_content)
    res = run("git commit -m x --no-verify", workdir, {"NEXUS_GUARD_GIT_BYPASS": env_value})
    assert res.returncode == expected
    if env_value in ("0", "1"):
        assert "WARNING" not in res.stderr, "an override must not read (or warn about) the file"


def test_the_variable_is_read_from_the_environment_never_from_the_command_text(run, workdir: Path, home: Path) -> None:
    """Typing the override into the command must not switch the mode either way."""
    _switch(home, _ON)
    assert run("NEXUS_GUARD_GIT_BYPASS=0 git commit --no-verify", workdir).returncode == _BLOCK
    assert run("export NEXUS_GUARD_GIT_BYPASS=0; git commit --no-verify", workdir).returncode == _BLOCK
    _switch(home, None)
    assert run("NEXUS_GUARD_GIT_BYPASS=1 git commit --no-verify", workdir).returncode == _ALLOW


def test_the_mode_never_weakens_an_existing_block(run, workdir: Path, home: Path) -> None:
    for content, env in ((_ON, None), (_OFF, None), (_ON, {"NEXUS_GUARD_GIT_BYPASS": "0"})):
        _switch(home, content)
        assert run(_RESET + " HEAD~1", workdir, env).returncode == _BLOCK
        assert run("git push --force origin main", workdir, env).returncode == _BLOCK


@pytest.mark.parametrize(
    "command",
    [
        'echo "hi" && ' + _RESET,
        'git commit -m "x" && ' + _RESET,
        "echo 'it' && git push --force origin main",
    ],
    ids=["double-quote", "message-then-reset", "single-quote"],
)
def test_a_quote_never_truncates_the_command_before_a_later_block(run, workdir: Path, command: str) -> None:
    """Regression: without jq the .sh cut the command at the first escaped double quote.

    Everything after it went unscanned, so a destructive command placed after any quoted
    text passed. This is mode-independent, so it also covers the existing blocks.
    """
    assert run(command, workdir).returncode == _BLOCK, f"not blocked: {command}"


def test_full_access_mode_steps_aside_even_with_the_mode_on(run, workdir: Path, home: Path) -> None:
    """Documented limit: bypassPermissions means the user chose to run without approval gates."""
    _switch(home, _ON)
    assert run("git commit --no-verify", workdir, permission_mode="bypassPermissions").returncode == _ALLOW


# --- nice to have: core.* keys match in any letter case (git reads keys case-insensitively) ---


@pytest.mark.parametrize(
    "command",
    [
        "git -c CORE.HOOKSPATH=/tmp/evil status",
        "git -c Core.FsMonitor=evil.sh status",
        "git config Core.HooksPath .githooks",
        "git config --global CORE.FSMONITOR evil.sh",
    ],
)
def test_core_keys_match_in_any_letter_case(run, workdir: Path, command: str) -> None:
    assert run(command, workdir).returncode == _BLOCK, f"not blocked: {command}"


@pytest.mark.parametrize(
    "command", ["git config --get CORE.hooksPath", "git config --list", "git -c Core.Pager=cat log"]
)
def test_core_key_reads_and_unrelated_keys_stay_allowed_in_any_case(run, workdir: Path, command: str) -> None:
    assert run(command, workdir).returncode == _ALLOW, f"false positive: {command}"


# --- the PowerShell tool: every existing block family applies, and so does the new mode ---


@pytest.mark.parametrize(
    "command",
    [
        "git push --force origin main",
        _RESET + " HEAD~1",
        "git clean -fd",
        "git -c core.hooksPath=/tmp/evil status",
        "git config core.hooksPath .githooks",
        _CFG_WRITE,
    ],
    ids=["force-push", "hard-reset", "clean", "inline-indirection", "persistent-indirection", "config-write"],
)
def test_powershell_tool_payload_hits_every_existing_block_family(run, workdir: Path, command: str) -> None:
    res = run(command, workdir, tool_name="PowerShell")
    assert res.returncode == _BLOCK, f"PowerShell-tool payload not blocked: {command}"
    assert "BLOCKED" in res.stderr


def test_powershell_tool_payload_hits_the_protected_branch_guard(run, repo: Path) -> None:
    _git(repo, "checkout", "main")
    res = run('git commit -m "x"', repo, {"NEXUS_PROTECTED_BRANCHES": "main"}, tool_name="PowerShell")
    assert res.returncode == _BLOCK


def test_powershell_tool_payload_keeps_the_quiet_paths(run, workdir: Path) -> None:
    assert run("git status", workdir, tool_name="PowerShell").returncode == _ALLOW
    assert run("", workdir, tool_name="PowerShell").returncode == _ALLOW
    cmd = "cat > doc.md <<'EOF'" + _NL + "Never run " + _RESET + " here." + _NL + "EOF"
    assert run(cmd, workdir, tool_name="PowerShell").returncode == _ALLOW


def test_powershell_tool_payload_with_no_command_field_is_allowed(workdir: Path, bash_bin: str, powershell_bin: str) -> None:
    payload = json.dumps({"tool_name": "PowerShell", "tool_input": {}})
    for prefix in ([bash_bin, str(_HOOK_SH)], [powershell_bin, "-NoProfile", "-File", str(_HOOK_PS1)]):
        res = subprocess.run(prefix, input=payload, text=True, capture_output=True, cwd=str(workdir), timeout=120)
        assert res.returncode == _ALLOW, f"{prefix[0]}: {res.stderr!r}"


@pytest.mark.parametrize("command", ["git commit -n -m x", "git commit -m x --no-verify", "git config commit.gpgsign false"])
def test_bypass_mode_applies_to_the_powershell_tool(run, workdir: Path, home: Path, command: str) -> None:
    _switch(home, _ON)
    assert run(command, workdir, tool_name="PowerShell").returncode == _BLOCK
    assert run("git commit -m x", workdir, tool_name="PowerShell").returncode == _ALLOW


# --- registration in catalog/hooks/settings.json ---


def _git_guardrails_entries() -> list[dict]:
    settings = json.loads((_HOOKS_DIR / "settings.json").read_text(encoding="utf-8"))
    return [
        entry
        for entry in settings["hooks"]["PreToolUse"]
        if any("git-guardrails" in h.get("command", "") for h in entry["hooks"])
    ]


def _entries_matching(tool: str) -> list[dict]:
    return [e for e in _git_guardrails_entries() if tool in e.get("matcher", "").split("|")]


def test_git_guardrails_is_registered_exactly_once_for_bash() -> None:
    """One registration per tool: two entries would run the hook twice for one call."""
    assert len(_entries_matching("Bash")) == 1


# Needs the catalog/hooks/settings.json registration change (protected path, delivered as a
# separate reviewed patch). Non-strict: it reports XPASS once the registration lands.
@pytest.mark.xfail(
    strict=False,
    reason="needs the git-guardrails PowerShell-tool registration in catalog/hooks/settings.json",
)
def test_git_guardrails_is_registered_exactly_once_for_the_powershell_tool() -> None:
    assert len(_entries_matching("PowerShell")) == 1
    entry = _entries_matching("PowerShell")[0]
    assert entry in _entries_matching("Bash"), "one entry must cover both tools, so a call runs the hook once"
    assert [h["command"] for h in entry["hooks"]] == ["bash .claude/hooks/git-guardrails.sh"]
