"""Cross-implementation parity for every catalog hook (v3.15.6 follow-on).

Every `catalog/hooks/*.sh` now ships a `*.ps1` sibling. This suite is the guard that
keeps the two honest, and it is deliberately GENERIC rather than 25 bespoke files:

  * a structural invariant (every .sh has a .ps1 and vice versa), so a future hook
    added in one language only fails immediately rather than silently shipping
    half-platform support;
  * a syntax floor for every .ps1 (AST parse);
  * behavioural parity: each pair is run with the SAME payloads and must agree on
    exit code.

Why generic matters here. v3.15.6 found four real defects in `.sh`/`.ps1` pairs
(an inert env-var contract, an undecoded JSON escape, a UTF-8 BOM, and
`sha256sum` filename escaping), and every one surfaced only because assertions ran
against both implementations. It also found `session-summary.ps1` had never parsed
since v3.11.0. A generic harness extends that protection to hooks nobody has
written yet.

SAFETY: these tests must not touch the developer's real environment. Every hook is
run with HOME / USERPROFILE pointed at a temp directory and with the CWD set to a
temp directory, so side-effecting hooks (auto-devlog writing DEVLOG.md,
usage-display reading credentials or reaching the network, provenance-ledger writing
a ledger) all hit their "precondition absent" path and exit without doing anything.
The payloads used are also the quiet ones: empty, malformed, and a benign path.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_hook_sibling_parity.py -v
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent

SH_HOOKS = sorted(p for p in _HOOKS_DIR.glob("*.sh") if p.is_file())
PS1_HOOKS = sorted(p for p in _HOOKS_DIR.glob("*.ps1") if p.is_file())

SH_STEMS = {p.stem for p in SH_HOOKS}
PS1_STEMS = {p.stem for p in PS1_HOOKS}

# Payloads that are safe for EVERY hook: each one either fails a precondition or
# describes a benign, non-matching path. None of them causes a side effect.
QUIET_PAYLOADS = {
    "empty": "",
    "malformed": "not json at all",
    "empty-object": "{}",
    "no-tool-input": '{"session_id":"parity"}',
    "benign-path": json.dumps(
        {"session_id": "parity", "tool_name": "Write",
         "tool_input": {"file_path": "src/benign_module.rs"}}
    ),
    "benign-command": json.dumps(
        {"session_id": "parity", "tool_name": "Bash",
         "tool_input": {"command": "git status", "description": "Show status"}}
    ),
}


# --- Structural invariants ---------------------------------------------------


def test_hooks_exist_at_all() -> None:
    """Guards against a glob that silently matches nothing."""
    assert len(SH_HOOKS) >= 20, f"expected the full hook set, found {len(SH_HOOKS)}"


def test_every_sh_hook_has_a_ps1_sibling() -> None:
    missing = sorted(SH_STEMS - PS1_STEMS)
    assert not missing, (
        "every catalog hook must ship a PowerShell sibling so Windows users get the "
        f"same guardrails; missing: {missing}"
    )


def test_every_ps1_hook_has_a_sh_sibling() -> None:
    """The reverse direction, so a PowerShell-only hook cannot appear either."""
    orphans = sorted(PS1_STEMS - SH_STEMS)
    assert not orphans, f".ps1 hooks with no .sh sibling: {orphans}"


@pytest.mark.parametrize("ps1", PS1_HOOKS, ids=lambda p: p.name)
def test_ps1_hook_parses(ps1: Path, powershell_bin: str) -> None:
    """Syntax floor. This is the check that caught session-summary.ps1 having been
    unparseable, and therefore dead on Windows, since v3.11.0."""
    probe = (
        "$e=$null;"
        f"$null=[System.Management.Automation.Language.Parser]::ParseFile('{ps1}',[ref]$null,[ref]$e);"
        "if($e -and $e.Count -gt 0){$e|ForEach-Object{Write-Host $_.Message};exit 1}"
    )
    proc = subprocess.run(
        [powershell_bin, "-NoProfile", "-Command", probe],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, f"{ps1.name} does not parse:\n{proc.stdout}{proc.stderr}"


@pytest.mark.parametrize("sh", SH_HOOKS, ids=lambda p: p.name)
def test_sh_hook_parses(sh: Path, bash_bin: str) -> None:
    proc = subprocess.run(
        [bash_bin, "-n", str(sh)], capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, f"{sh.name} does not parse:\n{proc.stderr}"


# --- Behavioural parity -----------------------------------------------------


@pytest.fixture()
def isolated_env(tmp_path: Path) -> dict[str, str]:
    """An environment that cannot reach the developer's real state.

    HOME / USERPROFILE are redirected so credential reads, cache writes, and ledger
    writes all land in (or miss in) a temp directory instead of the real one.

    The notification hooks are held in dry-run mode for the same reason. Raising a
    real desktop toast IS touching the developer's environment, and the Windows
    path deliberately keeps a tray icon alive for seconds per notification so the
    balloon renders, which would also add minutes to this suite. Dry run prints
    the notification to stdout instead; the parity assertion is on exit codes, so
    the comparison is unaffected.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    env = {**os.environ}
    env["HOME"] = str(fake_home)
    env["USERPROFILE"] = str(fake_home)
    env["NEXUS_PROVENANCE_DIR"] = str(tmp_path / "ledger")
    env["NEXUS_NOTIFY_DRY_RUN"] = "1"
    # Never let an ambient control leak into a parity expectation.
    for key in ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE", "CLAUDE_FILE_PATH",
                "ESCALATION_MODE", "NEXUS_HUB_INIT", "NEXUS_CONTEXT_COMPRESS",
                "AUTO_DEVLOG_AI", "NEXUS_PROTECTED_BRANCHES",
                "NEXUS_NOTIFY_DISABLED_FILE"):
        env.pop(key, None)
    return env


def _run(argv: list[str], payload: str, cwd: Path, env: dict[str, str]) -> int:
    proc = subprocess.run(
        argv, input=payload, text=True, capture_output=True,
        cwd=str(cwd), env=env, timeout=180,
    )
    return proc.returncode


@pytest.mark.parametrize("stem", sorted(SH_STEMS & PS1_STEMS))
@pytest.mark.parametrize("payload_name", sorted(QUIET_PAYLOADS))
def test_pair_agrees_on_exit_code(
    stem: str,
    payload_name: str,
    bash_bin: str,
    powershell_bin: str,
    tmp_path: Path,
    isolated_env: dict[str, str],
) -> None:
    """The two implementations must agree on the exit code for the same input.

    Exit code is the contract the harness acts on: 0 allows, 2 blocks. A pair that
    disagrees here means Windows and POSIX users get different enforcement from the
    same hook, which is the whole failure mode this suite exists to prevent.
    """
    payload = QUIET_PAYLOADS[payload_name]
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)

    sh_rc = _run([bash_bin, str(_HOOKS_DIR / f"{stem}.sh")], payload, work, isolated_env)
    ps_rc = _run(
        [powershell_bin, "-NoProfile", "-File", str(_HOOKS_DIR / f"{stem}.ps1")],
        payload, work, isolated_env,
    )

    assert sh_rc == ps_rc, (
        f"{stem}: exit-code parity broken on the {payload_name!r} payload "
        f"(.sh={sh_rc}, .ps1={ps_rc})"
    )


# --- Targeted parity for the BLOCKING hooks ---------------------------------
# These are the hooks whose disagreement would matter most: they refuse an
# operation, so a divergence means an action blocked on one platform and allowed
# on the other.

_BLOCKING_CASES = [
    # (stem, payload, expected exit code)
    (
        "secret-scan",
        json.dumps({"tool_input": {"file_path": "ok.py", "content": "x = 1\n"}}),
        0,
    ),
    (
        "html-responsive-guard",
        json.dumps({"tool_input": {"file_path": "report.html",
                                   "content": "<style>.copy { max-width: 60ch; }</style>"}}),
        2,
    ),
    (
        "html-responsive-guard",
        json.dumps({"tool_input": {"file_path": "report.html",
                                   "content": "<style>.container { max-width: 1200px; }</style>"}}),
        0,
    ),
    (
        "require-description",
        json.dumps({"tool_input": {"command": "rm -rf build"}}),
        2,
    ),
    (
        "require-description",
        json.dumps({"tool_input": {"command": "rm -rf build",
                                   "description": "Remove the build directory"}}),
        0,
    ),
    (
        "require-powershell-description",
        json.dumps({"tool_input": {"command": "Remove-Item build -Recurse"}}),
        2,
    ),
    (
        "require-powershell-description",
        json.dumps({"tool_input": {"command": "Remove-Item build -Recurse",
                                   "description": "Remove the build directory"}}),
        0,
    ),
]


@pytest.mark.parametrize("stem,payload,expected", _BLOCKING_CASES)
def test_blocking_hooks_agree_and_are_correct(
    stem: str,
    payload: str,
    expected: int,
    bash_bin: str,
    powershell_bin: str,
    tmp_path: Path,
    isolated_env: dict[str, str],
) -> None:
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)

    sh_rc = _run([bash_bin, str(_HOOKS_DIR / f"{stem}.sh")], payload, work, isolated_env)
    ps_rc = _run(
        [powershell_bin, "-NoProfile", "-File", str(_HOOKS_DIR / f"{stem}.ps1")],
        payload, work, isolated_env,
    )

    assert sh_rc == expected, f"{stem}.sh returned {sh_rc}, expected {expected}"
    assert ps_rc == expected, f"{stem}.ps1 returned {ps_rc}, expected {expected}"


def test_secret_scan_blocks_a_real_secret(
    bash_bin: str,
    powershell_bin: str,
    tmp_path: Path,
    isolated_env: dict[str, str],
) -> None:
    """Both implementations must block a planted credential WHERE THEY CAN SCAN.

    Asymmetry is expected and documented here, so this is not an exit-code parity
    case: secret-scan.sh requires `jq` to extract multi-line content and exits 0
    when it is absent, meaning it cannot scan at all on a jq-less host. The .ps1
    parses JSON natively and always scans. That difference is in the safe direction
    (it blocks strictly more, never less), so the assertion is conditional on jq for
    bash and unconditional for PowerShell.
    """
    import shutil as _shutil

    payload = json.dumps({"tool_input": {"file_path": "cfg.py",
                                         "content": "AWS_KEY = 'AKIA1234567890ABCDEF'\n"}})
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)

    ps_rc = _run(
        [powershell_bin, "-NoProfile", "-File", str(_HOOKS_DIR / "secret-scan.ps1")],
        payload, work, isolated_env,
    )
    assert ps_rc == 2, "secret-scan.ps1 must block a planted AWS key"

    sh_rc = _run([bash_bin, str(_HOOKS_DIR / "secret-scan.sh")], payload, work, isolated_env)
    if _shutil.which("jq"):
        assert sh_rc == 2, "secret-scan.sh must block a planted AWS key when jq is present"
    else:
        assert sh_rc == 0, (
            "without jq secret-scan.sh cannot scan and documents that it allows; "
            f"got {sh_rc}"
        )


def test_secret_scan_ps1_does_not_echo_the_secret(
    powershell_bin: str, tmp_path: Path, isolated_env: dict[str, str]
) -> None:
    """A scanner that prints what it found becomes the leak. It must report the
    CATEGORY only, never the matched value."""
    secret = "AKIA1234567890ABCDEF"
    payload = json.dumps({"tool_input": {"file_path": "cfg.py",
                                         "content": f"AWS_KEY = '{secret}'\n"}})
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    proc = subprocess.run(
        [powershell_bin, "-NoProfile", "-File", str(_HOOKS_DIR / "secret-scan.ps1")],
        input=payload, text=True, capture_output=True,
        cwd=str(work), env=isolated_env, timeout=180,
    )
    assert proc.returncode == 2
    assert secret not in proc.stdout, "secret-scan echoed the secret on stdout"
    assert secret not in proc.stderr, "secret-scan echoed the secret on stderr"
    assert "AWS Access Key ID" in proc.stderr, "expected the finding CATEGORY"


# --- Runtime-control parity -------------------------------------------------

# Hooks that document the shared disable controls. The essential security blockers
# (secret-scan, require-*) and compress-output deliberately do NOT honor them. The
# responsive-layout guard does honor them as its documented per-session escape.
_CONTROLLED = sorted(
    (SH_STEMS & PS1_STEMS)
    - {"secret-scan", "memory-store-guard", "require-description",
       "require-powershell-description",
       "compress-output", "claude-diff-review", "gemini-diff-review",
       "codex-diff-review", "opencode-diff-review", "antigravity-cli-diff-review"}
)


@pytest.mark.parametrize("stem", _CONTROLLED)
@pytest.mark.parametrize("control", ["NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE"])
def test_runtime_controls_are_honored_by_both(
    stem: str,
    control: str,
    bash_bin: str,
    powershell_bin: str,
    tmp_path: Path,
    isolated_env: dict[str, str],
) -> None:
    """Both implementations must exit 0 quietly when disabled.

    This also happens to be the only safe way to exercise the side-effecting hooks
    (notify-on-complete, usage-display, auto-devlog) end to end.
    """
    env = {**isolated_env}
    env[control] = stem if control == "NEXUS_DISABLED_HOOKS" else "minimal"
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    payload = QUIET_PAYLOADS["benign-path"]

    sh_rc = _run([bash_bin, str(_HOOKS_DIR / f"{stem}.sh")], payload, work, env)
    ps_rc = _run(
        [powershell_bin, "-NoProfile", "-File", str(_HOOKS_DIR / f"{stem}.ps1")],
        payload, work, env,
    )

    assert sh_rc == 0, f"{stem}.sh did not exit 0 when disabled via {control}"
    assert ps_rc == 0, f"{stem}.ps1 did not exit 0 when disabled via {control}"
