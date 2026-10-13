"""Multi-byte payloads survive every stdin-reading hook byte-identically (WN-37).

Windows PowerShell 5.1 decodes ``[Console]::In`` and native-command output with
the console code page (IBM437 or cp1252 on a stock host), and encodes
``[Console]::Out`` / ``[Console]::Error`` the same way. A UTF-8 hook payload
therefore grew on the way in (44 bytes became 92 in the 2026-10-10 probe) and
non-ASCII text left the hook as ``?``. The fix reads stdin as raw UTF-8 bytes and
writes stdout/stderr through UTF-8 writers, without calling SetConsoleCP or
SetConsoleOutputCP, which would change the code page of a console shared with
the parent process.

Each case below drives one hook with a payload carrying ``MULTIBYTE`` in a
field the hook echoes (a message, a JSON reply, or a file it writes) or decides
on (a deny rule). The ``.sh`` sibling is driven with the same bytes as the
parity reference. Every assertion is on exact UTF-8 bytes, so a grown,
re-encoded, or ``?``-substituted payload fails, and a leading UTF-8 BOM on
stdout or on a written file fails.

Hooks that read stdin but have no channel through which payload text can be
observed are not listed: auto-format-on-write and lint-on-write (output depends
on an installed formatter or linter), code-search-routing (fixed hint text),
lint-autofix (paths come from git, not the payload), and the drain-only hooks
(auto-devlog's stdin, usage-display, notify-*). auto-devlog is covered here for
its git-output decoding instead. The static test at the end asserts that every
content-reading ``.ps1`` hook uses the UTF-8 read, so the unobservable ones
cannot regress silently.

Run (Windows PowerShell 5.1 is the edition this guards):
    NEXUS_TEST_POWERSHELL=powershell python -m pytest catalog/hooks/tests/test_hook_stdin_utf8.py -q
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _HOOKS_DIR.parent.parent
_ENGINE_SRC = _REPO_ROOT / "extensions" / "nexus-context-compressor" / "src"

# 4 code points, 12 UTF-8 bytes: 2-, 3-, 3- and 4-byte sequences.
MULTIBYTE = "é漢字\U0001f600"
MB_BYTES = MULTIBYTE.encode("utf-8")
BOM = b"\xef\xbb\xbf"
# Split so the repository's own secret-scan hook does not flag this test file.
_FAKE_KEY = "AKIA" + "1234567890ABCDEF"


@dataclass
class Case:
    stem: str
    payload: dict
    env: dict[str, str] = field(default_factory=dict)
    setup: Callable[[Path, str], None] | None = None
    # None: observe stdout + stderr. Otherwise a path relative to the work dir.
    observe_file: str | None = None
    # None: the token's UTF-8 bytes. Otherwise a regex over the observed bytes.
    expect: bytes | None = None
    needs_engine: bool = False


def _git(work: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=work, check=True, capture_output=True)


def _git_repo(work: Path, token: str = "") -> None:
    _git(work, "init", "-q", "-b", "main")
    _git(work, "config", "user.email", "t@example.invalid")
    _git(work, "config", "user.name", "t")
    _git(work, "config", "commit.gpgsign", "false")


def _old_docs_setup(work: Path, token: str) -> None:
    (work / "docs/releases/v0/v0.8").mkdir(parents=True)
    (work / "docs/releases/v1/v1.0").mkdir(parents=True)


def _memory_store_setup(work: Path, token: str) -> None:
    _git_repo(work)
    store = work / token / "store"
    store.mkdir(parents=True)
    (store / ".nexus-memory-store").write_text("", encoding="utf-8")


def _rewrite_deny_setup(work: Path, token: str) -> None:
    cfg = work / "cfgdir"
    cfg.mkdir()
    (cfg / "settings.json").write_text(
        json.dumps({"permissions": {"deny": [f"echo {token}"]}}, ensure_ascii=False),
        encoding="utf-8",
    )


def _devlog_setup(work: Path, token: str) -> None:
    _git_repo(work)
    devlog = work / "docs" / "DEVLOG.md"
    devlog.parent.mkdir(parents=True)
    devlog.write_text("# Devlog\n\n## [2000-01-01] - seed\n\nseed\n", encoding="utf-8")
    for n in (1, 2):
        (work / f"f{n}.txt").write_text(str(n), encoding="utf-8")
        _git(work, "add", f"f{n}.txt")
        _git(work, "commit", "-q", "-m", f"commit {n} {token}")
    old = time.time() - 3600
    os.utime(devlog, (old, old))


CASES: list[Case] = [
    Case(
        "git-guardrails",
        {
            "tool_name": "Bash",
            "tool_input": {"command": f"git push --force origin {MULTIBYTE}"},
        },
    ),
    Case(
        "escalation-trigger",
        {
            "tool_name": "Write",
            "tool_input": {"file_path": f"{MULTIBYTE}/.env", "content": "x"},
        },
        env={"ESCALATION_MODE": "warn"},
    ),
    Case(
        "secret-scan",
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": f"{MULTIBYTE}.py",
                "content": f"AWS_KEY = '{_FAKE_KEY}'\n",
            },
        },
    ),
    Case(
        "large-file-guard",
        {
            "tool_name": "Write",
            "tool_input": {"file_path": f"{MULTIBYTE}.py", "content": "x = 1\n" * 20},
        },
        env={"LARGE_FILE_MAX_LINES": "5"},
    ),
    Case(
        "html-responsive-guard",
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": f"{MULTIBYTE}.html",
                "content": "<style>.copy { max-width: 60ch; }</style>",
            },
        },
    ),
    Case(
        "dependency-staleness-notice",
        {
            "tool_name": "Edit",
            "tool_input": {"file_path": f"{MULTIBYTE}/package.json", "content": "{}"},
        },
    ),
    Case(
        "test-gap-notice",
        {
            "tool_name": "Write",
            "tool_input": {"file_path": f"src/{MULTIBYTE}.py", "content": "x = 1\n"},
        },
    ),
    Case(
        "workflow-phase-notice",
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": f"docs/releases/v1/v1.0/plans/{MULTIBYTE}.md",
                "content": "x",
            },
        },
    ),
    Case(
        "old-version-docs-guard",
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": f"docs/releases/v0/v0.8/plans/{MULTIBYTE}.md",
                "content": "x",
            },
        },
        setup=_old_docs_setup,
    ),
    Case(
        "memory-store-guard",
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": f"{MULTIBYTE}/store/entries.log",
                "content": "x",
            },
        },
        setup=_memory_store_setup,
    ),
    Case(
        "compress-output",
        {
            "tool_name": "Bash",
            "tool_input": {"command": f"echo {MULTIBYTE}", "description": "d"},
        },
        env={"NEXUS_CONTEXT_COMPRESS": "1"},
        needs_engine=True,
    ),
    # rewrite-command never echoes payload text; the observable is the decision:
    # the deny rule only matches when the command decoded intact.
    Case(
        "rewrite-command",
        {"tool_name": "Bash", "tool_input": {"command": f"echo {MULTIBYTE}"}},
        setup=_rewrite_deny_setup,
        expect=rb'"permissionDecision":\s*"deny"',
        needs_engine=True,
    ),
    Case(
        "learning-capture",
        {"hook_event_name": "UserPromptSubmit", "prompt": f"say {MULTIBYTE}"},
        observe_file=".nexus/observations.jsonl",
    ),
    Case(
        "session-summary",
        {"session_duration": f"9m {MULTIBYTE}"},
        setup=_git_repo,
        observe_file=".nexus/context/last-session.md",
    ),
    Case(
        "auto-devlog",
        {"hook_event_name": "Stop"},
        env={"AUTO_DEVLOG": "1"},
        setup=_devlog_setup,
        observe_file="docs/DEVLOG.md",
    ),
]


def _env(tmp_path: Path, case: Case) -> dict[str, str]:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {**os.environ}
    for key in (
        "NEXUS_DISABLED_HOOKS",
        "NEXUS_HOOK_PROFILE",
        "CLAUDE_FILE_PATH",
        "ESCALATION_MODE",
        "NEXUS_CONTEXT_COMPRESS",
        "AUTO_DEVLOG",
        "AUTO_DEVLOG_AI",
        "NEXUS_LEARNING_CAPTURE",
        "NEXUS_LEARNING_PATH",
        "NEXUS_SESSION_DIGEST",
        "NEXUS_SESSION_DIGEST_PATH",
        "NEXUS_OLD_DOCS_GUARD",
        "NEXUS_MEMORY_ALLOW_IN_REPO",
        "CLAUDE_CONFIG_DIR",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
    ):
        env.pop(key, None)
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "NEXUS_PROVENANCE_DIR": str(tmp_path / "ledger"),
            "NEXUS_NOTIFY_DRY_RUN": "1",
        }
    )
    if case.needs_engine:
        env["PYTHONPATH"] = str(_ENGINE_SRC) + os.pathsep + env.get("PYTHONPATH", "")
    env.update(case.env)
    return env


def _drive(
    argv: list[str], case: Case, tmp_path: Path, token: str
) -> tuple[bytes, bytes]:
    """Run one hook with `token` in place of MULTIBYTE; return (head, observed) bytes."""
    work = tmp_path / f"work-{len(token.encode('utf-8'))}"
    work.mkdir()
    if case.setup:
        case.setup(work, token)
    env = _env(tmp_path, case)
    if case.stem == "rewrite-command":
        env["CLAUDE_CONFIG_DIR"] = str(work / "cfgdir")
    text = json.dumps(case.payload, ensure_ascii=False).replace(MULTIBYTE, token)
    proc = subprocess.run(
        argv,
        input=text.encode("utf-8"),
        capture_output=True,
        cwd=str(work),
        env=env,
        timeout=180,
        check=False,
    )
    if case.observe_file is None:
        return proc.stdout, proc.stdout + proc.stderr
    target = work / case.observe_file
    data = target.read_bytes() if target.is_file() else b""
    return data, data


def _intact(case: Case, observed: bytes, token: str) -> bool:
    if case.stem == "learning-capture":
        # The record is JSON and a sibling may \u-escape, so compare decoded values.
        try:
            samples = [
                json.loads(line).get("prompt_sample", "")
                for line in observed.decode("utf-8").splitlines()
                if line.strip()
            ]
        except ValueError:
            return False
        return any(token in s for s in samples)
    if case.expect is not None:
        return re.search(case.expect, observed) is not None
    return token.encode("utf-8") in observed


def _assert_intact(label: str, case: Case, head: bytes, observed: bytes) -> None:
    assert not head.startswith(BOM), f"{label}: output starts with a UTF-8 BOM"
    assert _intact(case, observed, MULTIBYTE), (
        f"{label}: multi-byte text did not survive byte-identically "
        f"(expected {case.expect or MB_BYTES!r}); got {observed[-600:]!r}"
    )


def _skip_if_engine_missing(case: Case) -> None:
    if case.needs_engine and not _ENGINE_SRC.is_dir():
        pytest.skip("nexus-context-compressor source tree not present")


@pytest.mark.parametrize("case", CASES, ids=[c.stem for c in CASES])
def test_ps1_hook_round_trips_multibyte(
    case: Case, powershell_bin: str, tmp_path: Path
) -> None:
    _skip_if_engine_missing(case)
    argv = [
        powershell_bin,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(_HOOKS_DIR / f"{case.stem}.ps1"),
    ]
    head, observed = _drive(argv, case, tmp_path, MULTIBYTE)
    _assert_intact(f"{case.stem}.ps1", case, head, observed)


@pytest.mark.parametrize("case", CASES, ids=[c.stem for c in CASES])
def test_sh_sibling_round_trips_multibyte(
    case: Case, bash_bin: str, tmp_path: Path
) -> None:
    """Parity reference. Several .sh hooks parse with jq only and stay silent
    without it, so an ASCII control run decides whether this host can observe
    the sibling at all; an inert sibling skips rather than passing vacuously."""
    _skip_if_engine_missing(case)
    argv = [bash_bin, str(_HOOKS_DIR / f"{case.stem}.sh")]
    _, control = _drive(argv, case, tmp_path, "abc")
    if not _intact(case, control, "abc"):
        pytest.skip(
            f"{case.stem}.sh is inert on this host even for ASCII (jq={shutil.which('jq')})"
        )
    head, observed = _drive(argv, case, tmp_path, MULTIBYTE)
    _assert_intact(f"{case.stem}.sh", case, head, observed)


_CONSOLE_READ = re.compile(
    r"^\s*(?:try\s*\{\s*)?\$\w+\s*=\s*\[Console\]::In\.ReadToEnd\(\)"
)
# Either a raw-handle read (decoded as UTF-8 or forwarded as bytes) or a UTF-8
# InputEncoding set (provenance-ledger, v4.13.11 Phase 3) makes a following
# [Console]::In read a fallback rather than the primary decode.
_UTF8_PRIMARY = re.compile(
    r"\[Console\]::OpenStandardInput\(\)"
    r"|\[Console\]::InputEncoding\s*=\s*New-Object System\.Text\.UTF8Encoding"
)
_FALLBACK_WINDOW = 6


def test_every_content_reading_ps1_hook_decodes_stdin_as_utf8() -> None:
    """No .ps1 hook may decode its payload through the console code page.

    A `$x = [Console]::In.ReadToEnd()` is the defect unless one of the previous
    few lines already read the raw handle or set a UTF-8 InputEncoding; there it
    is the Windows PowerShell 5.1 no-console fallback. Drain-only reads
    (`$null = ...` inside an `if`) do not match the pattern.
    """
    offenders = []
    for ps1 in sorted(_HOOKS_DIR.glob("*.ps1")):
        lines = ps1.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            window = lines[max(0, i - _FALLBACK_WINDOW) : i]
            if _CONSOLE_READ.match(line) and not any(
                _UTF8_PRIMARY.search(prev) for prev in window
            ):
                offenders.append(f"{ps1.name}:{i + 1}")
    assert not offenders, "console-code-page stdin read: " + ", ".join(offenders)
