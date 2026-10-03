"""Bounded on-disk size guard for the catalog hooks that write files (v4.13.9 T423).

Every hook below appends to or rewrites a file each time it fires. This module
drives each one through 20 ordinary synthetic events plus one oversized-payload
event and one multi-byte-payload event, measures what lands on disk, prints the
measured table, and asserts a per-class rule:

  - append-only: the file never shrinks and each event adds at most an absolute
    per-event cap.
  - bounded-rotation: the file stays at or under its documented cap once more
    events than the cap have fired (the cap is lowered through its environment
    variable so the rotation path is reached within 20 events).
  - intentional-overwrite: the resulting file stays under an absolute bound, so
    an oversized field must be truncated rather than copied through.

Every cap is an absolute number with the 2026-10-03 measurement and reasoning
next to it, never a multiple of a recorded baseline, so the guard cannot be
re-recorded upward by re-running it on a regressed hook.

Isolation is the other half of this module. Each run gets a temp root that HOME,
USERPROFILE, HOMEDRIVE/HOMEPATH, APPDATA, LOCALAPPDATA, TMP/TEMP/TMPDIR, every
XDG_* and every NEXUS_* path variable point into; it runs from a temp git
repository; provider credentials are removed from the child environment; proxies
point at a closed local port; and in-process sockets refuse to connect. A guard
snapshots the real ~/.nexus-hub, ~/.claude and this repository's git status
before and after, and fails when a change carries the run's unique token. The
token rule (rather than strict equality) is deliberate: the user's own installed
hooks and concurrent agent sessions legitimately write to the real ~/.claude and
~/.nexus-hub while this suite runs, and strict equality would fail on their
writes. Every synthetic event carries the token (in the session id, the temp
repository name, or the payload), so a hook that escaped the temp root writes it.
The meta-tests prove the guard catches a fixture hook that writes to a sentinel
"real home".

Measured classification and the table this prints are recorded in
docs/releases/v4/v4.13/development/v4.13.9-hook-size-bound.md.

Runs in the full CI profile only: the fast profile has no catalog/hooks/tests
step at all (see scripts/ci/profiles.py), so no marker is needed.

Run from the repo root (-s shows the measured table):
    python -m pytest catalog/hooks/tests/test_hook_size_bound.py -q -s
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import socket
import statistics
import subprocess
import sys
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _HOOKS_DIR.parent.parent

# Resolved once, before any child environment is built. The test never mutates
# os.environ, so this is the user's real home for the whole run.
_REAL_HOME = Path.home()

MEASURED_ON = "2026-10-03"
EVENTS = 20
OVERSIZE = 64 * 1024
# 4 code points, 12 UTF-8 bytes (2 + 3 + 3 + 4); 125 repeats = 500 code points,
# enough to cross learning-capture's 400-character prompt truncation.
MULTIBYTE = "\u00e9\u6f22\u5b57\U0001F600" * 125

# Environment names removed from every child: provider credentials and anything
# that looks like a secret, so no hook can authenticate anywhere even by mistake.
_SECRET_ENV_RE = re.compile(
    r"(?i)(API_KEY|APIKEY|_TOKEN$|^TOKEN|_SECRET|PASSWORD|ANTHROPIC|OPENAI|GEMINI|"
    r"GOOGLE_API|OPENROUTER|MISTRAL|DEEPSEEK|COHERE|GROQ|^XAI_|MOONSHOT|DASHSCOPE|"
    r"^AWS_|AZURE_OPENAI|^GH_|^GITHUB_TOKEN)"
)
# Variables that would redirect a hook or git outside the temp repository.
_DROP_ENV = {
    "CLAUDE_PROJECT_DIR",
    "AUTO_DEVLOG",
    "AUTO_DEVLOG_AI",
    "AUTO_DEVLOG_MIN_COMMITS",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_CONFIG",
    "GIT_CONFIG_GLOBAL",
}


# --- In-process network block ----------------------------------------------------


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail any in-process connect; child processes get a dead proxy instead."""

    def _refuse(*_args: object, **_kwargs: object) -> None:
        raise OSError("network access is blocked by test_hook_size_bound")

    monkeypatch.setattr(socket.socket, "connect", _refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", _refuse)
    monkeypatch.setattr(socket, "create_connection", _refuse)


def test_network_block_is_active() -> None:
    with pytest.raises(OSError, match="blocked"):
        socket.create_connection(("127.0.0.1", 9), timeout=1)
    with socket.socket() as sock, pytest.raises(OSError, match="blocked"):
        sock.connect(("127.0.0.1", 9))


# --- Isolated environment --------------------------------------------------------


@dataclass
class Ctx:
    """One isolated run: temp root, temp home, temp git repository, child env."""

    root: Path
    home: Path
    repo: Path
    token: str
    sid: str
    env: dict[str, str]
    clock: int = 0  # minutes added to future commit dates (auto-devlog)


def isolated_env(root: Path, home: Path) -> dict[str, str]:
    """Child environment whose every home, temp, XDG and NEXUS path is under root."""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("NEXUS_", "XDG_"))
        and key not in _DROP_ENV
        and not _SECRET_ENV_RE.search(key)
    }
    tmp = root / "tmp"
    xdg = root / "xdg"
    for directory in (home, tmp, xdg):
        directory.mkdir(parents=True, exist_ok=True)
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "HOMEDRIVE": home.drive,
            "HOMEPATH": str(home)[len(home.drive) :],
            "APPDATA": str(home / "AppData" / "Roaming"),
            "LOCALAPPDATA": str(home / "AppData" / "Local"),
            "TMP": str(tmp),
            "TEMP": str(tmp),
            "TMPDIR": str(tmp),
            "XDG_CONFIG_HOME": str(xdg / "config"),
            "XDG_DATA_HOME": str(xdg / "data"),
            "XDG_CACHE_HOME": str(xdg / "cache"),
            "XDG_STATE_HOME": str(xdg / "state"),
            "XDG_RUNTIME_DIR": str(xdg / "runtime"),
            # Every NEXUS_* path variable an in-scope hook reads. The two
            # project-relative ones resolve inside the temp repository.
            "NEXUS_HOME": str(home / ".nexus-hub"),
            "NEXUS_PROVENANCE_DIR": str(home / ".nexus-hub" / "cache" / "provenance"),
            "NEXUS_SKILL_RULES": str(root / "no-skill-rules.json"),
            "NEXUS_LEARNING_PATH": ".nexus/observations.jsonl",
            "NEXUS_SESSION_DIGEST_PATH": ".nexus/context/last-session.md",
            "NEXUS_SESSION_DIGEST_NOW": "2026-10-03 00:00",
            # git must not read the user's global or system config.
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(root / "gitconfig"),
            "GIT_AUTHOR_NAME": "Size Bound",
            "GIT_AUTHOR_EMAIL": "size-bound@example.invalid",
            "GIT_COMMITTER_NAME": "Size Bound",
            "GIT_COMMITTER_EMAIL": "size-bound@example.invalid",
            # Any child that tries HTTP(S) goes to a closed local port.
            "http_proxy": "http://127.0.0.1:9",
            "https_proxy": "http://127.0.0.1:9",
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "ALL_PROXY": "http://127.0.0.1:9",
            "NO_PROXY": "",
            "no_proxy": "",
        }
    )
    (root / "gitconfig").write_text("", encoding="utf-8")
    return env


def _git(ctx: Ctx, *args: str, date: str | None = None) -> str:
    env = dict(ctx.env)
    if date:
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    proc = subprocess.run(
        ["git", *args], cwd=ctx.repo, env=env, capture_output=True, timeout=60, check=False
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    return proc.stdout.decode("utf-8", "replace")


def make_ctx(base: Path) -> Ctx:
    token = uuid.uuid4().hex
    root = base / "iso"
    home = root / "home"
    env = isolated_env(root, home)
    repo = root / f"hsb-{token}"
    repo.mkdir(parents=True)
    ctx = Ctx(root=root, home=home, repo=repo, token=token, sid=f"hsb-{token}", env=env)
    _git(ctx, "init", "-q")
    return ctx


# --- Isolation guard -------------------------------------------------------------

Snapshot = dict[str, tuple[int, int]]
_GIT_PREFIX = "git::"


@dataclass(frozen=True)
class Watch:
    path: Path
    recursive: bool


def real_watch(real_home: Path) -> list[Watch]:
    """The real-home locations an in-scope hook would write to if it escaped."""
    nexus = real_home / ".nexus-hub"
    return [
        Watch(nexus, recursive=False),
        Watch(nexus / "cache" / "provenance", recursive=True),
        Watch(nexus / "state", recursive=True),
        Watch(real_home / ".claude", recursive=False),
    ]


def snapshot(watches: list[Watch], repo_root: Path) -> Snapshot:
    """Listing with (size, mtime_ns) per watched entry, plus the repo's git status."""
    snap: Snapshot = {}
    for watch in watches:
        if not watch.path.is_dir():
            continue
        entries = watch.path.rglob("*") if watch.recursive else watch.path.iterdir()
        for entry in entries:
            try:
                st = entry.stat()
            except OSError:
                continue
            snap[str(entry)] = (st.st_size, st.st_mtime_ns)
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=all"],
        capture_output=True,
        timeout=60,
        check=False,
    )
    for line in proc.stdout.decode("utf-8", "replace").splitlines():
        if len(line) > 3:
            target = repo_root / line[3:].strip().strip('"')
            try:
                st = target.stat()
                stamp = (st.st_size, st.st_mtime_ns)
            except OSError:
                stamp = (-1, -1)
            snap[_GIT_PREFIX + str(target)] = stamp
    return snap


def _read_text(path: str) -> str:
    try:
        p = Path(path)
        return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""
    except OSError:
        return ""


def find_isolation_breaches(
    before: Snapshot,
    after: Snapshot,
    token: str,
    read_text: Callable[[str], str] = _read_text,
) -> tuple[list[str], list[str]]:
    """Return (breaches, unattributed) between two snapshots.

    A breach is a new or changed entry whose path or content carries the run's
    token. Any other change is unattributed: a concurrent session or the user's
    own installed hooks, reported but not failed.
    """
    breaches: list[str] = []
    unattributed: list[str] = []
    for key, stamp in after.items():
        if before.get(key) == stamp:
            continue
        path = key.removeprefix(_GIT_PREFIX)
        if token in path or token in read_text(path):
            breaches.append(path)
        else:
            unattributed.append(path)
    unattributed.extend(k for k in before if k not in after)
    return breaches, unattributed


@contextmanager
def isolation_guard(
    token: str, watches: list[Watch], repo_root: Path
) -> Iterator[None]:
    before = snapshot(watches, repo_root)
    yield
    after = snapshot(watches, repo_root)
    breaches, unattributed = find_isolation_breaches(before, after, token)
    if unattributed:
        print(f"\n[isolation-guard] {len(unattributed)} unattributed concurrent change(s) ignored")
    assert not breaches, f"hook wrote outside its temp root: {breaches}"


def real_guard(token: str) -> AbstractContextManager[None]:
    return isolation_guard(token, real_watch(_REAL_HOME), _REPO_ROOT)


# --- Meta-tests: the guard catches a hook that escapes ---------------------------

_ESCAPING_HOOK = """
import json, sys, pathlib
payload = json.loads(sys.stdin.read())
target = pathlib.Path(sys.argv[1]) / ".nexus-hub" / "cache" / "provenance"
target.mkdir(parents=True, exist_ok=True)
(target / (payload["session_id"] + ".tsv")).write_text("1\\tNOFILE\\tx\\n", encoding="utf-8")
"""

_WELL_BEHAVED_HOOK = """
import json, os, sys, pathlib
payload = json.loads(sys.stdin.read())
target = pathlib.Path(os.path.expanduser("~")) / ".nexus-hub" / "cache" / "provenance"
target.mkdir(parents=True, exist_ok=True)
(target / (payload["session_id"] + ".tsv")).write_text("1\\tNOFILE\\tx\\n", encoding="utf-8")
"""


def _sentinel_real(tmp_path: Path) -> tuple[Path, Path]:
    """A directory the guard treats as the real home, and a fake 'real' repo."""
    sentinel_home = tmp_path / "sentinel-real-home"
    (sentinel_home / ".nexus-hub" / "cache" / "provenance").mkdir(parents=True)
    (sentinel_home / ".claude").mkdir()
    fake_repo = tmp_path / "sentinel-real-repo"
    fake_repo.mkdir()
    subprocess.run(["git", "init", "-q", str(fake_repo)], check=True, timeout=60)
    return sentinel_home, fake_repo


def _run_fixture_hook(ctx: Ctx, source: str, arg: Path) -> None:
    script = ctx.root / "fixture_hook.py"
    script.write_text(source, encoding="utf-8")
    subprocess.run(
        [sys.executable, str(script), str(arg)],
        input=json.dumps({"session_id": ctx.sid}).encode("utf-8"),
        cwd=ctx.repo,
        env=ctx.env,
        capture_output=True,
        timeout=60,
        check=True,
    )


def test_guard_fails_a_hook_that_writes_to_the_real_home(tmp_path: Path) -> None:
    sentinel_home, fake_repo = _sentinel_real(tmp_path)
    ctx = make_ctx(tmp_path)
    with (
        pytest.raises(AssertionError, match="outside its temp root"),
        isolation_guard(ctx.token, real_watch(sentinel_home), fake_repo),
    ):
        _run_fixture_hook(ctx, _ESCAPING_HOOK, sentinel_home)


def test_guard_fails_a_hook_that_writes_into_the_repository(tmp_path: Path) -> None:
    sentinel_home, fake_repo = _sentinel_real(tmp_path)
    ctx = make_ctx(tmp_path)
    misdirected = _ESCAPING_HOOK.replace(
        '/ ".nexus-hub" / "cache" / "provenance"', '/ ".nexus"'
    )
    with (
        pytest.raises(AssertionError, match="outside its temp root"),
        isolation_guard(ctx.token, real_watch(sentinel_home), fake_repo),
    ):
        # A misdirected project-relative write: the hook's "repo" is the real one.
        _run_fixture_hook(ctx, misdirected, fake_repo)


def test_guard_passes_a_hook_that_stays_in_its_temp_home(tmp_path: Path) -> None:
    sentinel_home, fake_repo = _sentinel_real(tmp_path)
    ctx = make_ctx(tmp_path)
    with isolation_guard(ctx.token, real_watch(sentinel_home), fake_repo):
        _run_fixture_hook(ctx, _WELL_BEHAVED_HOOK, sentinel_home)
    assert (ctx.home / ".nexus-hub" / "cache" / "provenance" / f"{ctx.sid}.tsv").is_file()


def test_guard_ignores_unattributed_concurrent_changes() -> None:
    before = {"/real/.claude/history.jsonl": (10, 1)}
    after = {"/real/.claude/history.jsonl": (20, 2), "/real/.claude/new.json": (5, 3)}
    contents = {"/real/.claude/history.jsonl": "another session", "/real/.claude/new.json": "x"}
    breaches, unattributed = find_isolation_breaches(
        before, after, "tok123", read_text=lambda p: contents.get(p, "")
    )
    assert breaches == []
    assert sorted(unattributed) == sorted(after)


def test_guard_attributes_a_change_by_token_in_path_or_content() -> None:
    before: Snapshot = {}
    after = {"/real/a-tok123.tsv": (1, 1), _GIT_PREFIX + "/repo/.nexus/obs": (1, 1)}
    breaches, _ = find_isolation_breaches(
        before, after, "tok123", read_text=lambda p: "has tok123" if p.endswith("obs") else ""
    )
    assert sorted(breaches) == ["/real/a-tok123.tsv", "/repo/.nexus/obs"]


# --- Hook scenarios --------------------------------------------------------------

APPEND = "append-only"
ROTATION = "bounded-rotation"
OVERWRITE = "intentional-overwrite"


@dataclass(frozen=True)
class Target:
    label: str  # display path for the table
    cls: str
    path: Callable[[Ctx], Path]
    # Absolute caps (bytes). For append-only and rotation: bytes one event may
    # add. For overwrite: the resulting file size. None = not asserted.
    normal_cap: int
    multibyte_cap: int
    oversized_cap: int


@dataclass(frozen=True)
class Scenario:
    name: str
    impls: tuple[str, ...]
    targets: tuple[Target, ...]
    payload: Callable[[Ctx, str, int], str]
    setup: Callable[[Ctx], None] = lambda ctx: None
    before_event: Callable[[Ctx, str, int], None] = lambda ctx, kind, i: None
    extra_env: dict[str, str] = field(default_factory=dict)


# learning-capture ---------------------------------------------------------------


def _lc_payload(ctx: Ctx, kind: str, i: int) -> str:
    event, tool, prompt = "UserPromptSubmit", "", f"{ctx.sid} prompt {i:02d} " + "p" * 60
    if kind == "oversized":
        event, tool, prompt = "E" * OVERSIZE, "T" * OVERSIZE, "P" * OVERSIZE
    elif kind == "multibyte":
        prompt = MULTIBYTE
    return json.dumps(
        {"session_id": ctx.sid, "hook_event_name": event, "tool_name": tool, "prompt": prompt},
        ensure_ascii=False,
    )


LEARNING_CAPTURE = Scenario(
    name="learning-capture",
    impls=("sh", "ps1"),
    payload=_lc_payload,
    targets=(
        Target(
            label="<repo>/.nexus/observations.jsonl",
            cls=ROTATION,
            path=lambda ctx: ctx.repo / ".nexus" / "observations.jsonl",
            # 2026-10-03: ~150 B per ordinary event. The record is four short
            # fields plus a prompt sample truncated to 400 characters, so 1 KiB
            # covers any ordinary event with headroom.
            normal_cap=1024,
            # 2026-10-03: the 400-character sample of a 500-code-point multi-byte
            # prompt; 400 code points x 4 bytes + ~100 B of keys < 2 KiB.
            multibyte_cap=2048,
            # A 64 KiB field must not reach disk; same 2 KiB bound.
            oversized_cap=2048,
        ),
    ),
)

# provenance-ledger --------------------------------------------------------------


def _pl_before(ctx: Ctx, kind: str, i: int) -> None:
    if kind == "normal":
        target = ctx.repo / "src" / f"file_{i:02d}.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"print({i})\n", encoding="utf-8")


def _pl_payload(ctx: Ctx, kind: str, i: int) -> str:
    path = str(ctx.repo / "src" / f"file_{i:02d}.py")
    if kind == "oversized":
        path = str(ctx.repo / ("p" * OVERSIZE))
    elif kind == "multibyte":
        path = str(ctx.repo / "src" / (MULTIBYTE[:40] + ".txt"))
    return json.dumps(
        {"session_id": ctx.sid, "tool_name": "Write", "tool_input": {"file_path": path}},
        ensure_ascii=False,
    )


PROVENANCE_LEDGER = Scenario(
    name="provenance-ledger",
    impls=("sh", "ps1"),
    payload=_pl_payload,
    before_event=_pl_before,
    targets=(
        Target(
            label="~/.nexus-hub/cache/provenance/<session>.tsv",
            cls=ROTATION,
            path=lambda ctx: ctx.home / ".nexus-hub" / "cache" / "provenance" / f"{ctx.sid}.tsv",
            # 2026-10-03: ~200 B per event (epoch + sha256 + a ~120-char temp
            # path). The line is fixed overhead plus the path, and a real path is
            # far below 1 KiB.
            normal_cap=1024,
            # 40 multi-byte code points in the file name: < 1 KiB.
            multibyte_cap=1024,
            # A 64 KiB path field must not reach disk whole.
            oversized_cap=8192,
        ),
    ),
)

# session-summary ----------------------------------------------------------------


def _ss_setup(ctx: Ctx) -> None:
    for name in ("alpha.txt", "beta.txt"):
        (ctx.repo / name).write_text("v1\n", encoding="utf-8")
    _git(ctx, "add", "-A")
    _git(ctx, "commit", "-q", "-m", "seed")
    for name in ("alpha.txt", "beta.txt"):
        (ctx.repo / name).write_text("v2\n", encoding="utf-8")


def _ss_payload(ctx: Ctx, kind: str, i: int) -> str:
    duration = f"{i}m"
    if kind == "oversized":
        duration = "D" * OVERSIZE
    elif kind == "multibyte":
        duration = MULTIBYTE
    return json.dumps({"session_id": ctx.sid, "session_duration": duration}, ensure_ascii=False)


SESSION_SUMMARY = Scenario(
    name="session-summary",
    impls=("sh", "ps1"),
    payload=_ss_payload,
    setup=_ss_setup,
    targets=(
        Target(
            label="~/.claude/session-log.md",
            cls=APPEND,
            path=lambda ctx: ctx.home / ".claude" / "session-log.md",
            # 2026-10-03: ~60 B per row (date, temp repo name, duration, count).
            # A row is four short cells; 512 B is generous for any real one.
            normal_cap=512,
            multibyte_cap=512,
            oversized_cap=512,
        ),
        Target(
            label="<repo>/.nexus/context/last-session.md",
            cls=OVERWRITE,
            path=lambda ctx: ctx.repo / ".nexus" / "context" / "last-session.md",
            # 2026-10-03: ~200 B with two changed files. The digest is a fixed
            # header plus at most 30 changed-file paths; 30 x ~200-char paths +
            # header fits in 8 KiB, which is the absolute bound.
            normal_cap=8192,
            multibyte_cap=8192,
            oversized_cap=8192,
        ),
    ),
)

# auto-devlog --------------------------------------------------------------------


def _ad_setup(ctx: Ctx) -> None:
    docs = ctx.repo / "docs"
    docs.mkdir()
    (docs / "DEVLOG.md").write_text(
        "# Dev Log\n\n## [2019-12-30] - seed\n\nSeed entry.\n", encoding="utf-8"
    )
    _git(ctx, "add", "-A")
    _git(ctx, "commit", "-q", "-m", "seed", date="2019-12-31T00:00:00")


def _ad_before(ctx: Ctx, kind: str, i: int) -> None:
    # Two commits dated tomorrow, so `--after=<today>` (the newest entry's date
    # once the hook has prepended one) always counts them.
    # The hook stamps entries with the LOCAL date, so commit dates follow it.
    tomorrow = _dt.date.today() + _dt.timedelta(days=1)  # noqa: DTZ011
    subjects = [f"{ctx.sid} change {i:02d} a", f"change {i:02d} b"]
    if kind == "oversized":
        subjects[1] = "S" * OVERSIZE
    elif kind == "multibyte":
        subjects[1] = MULTIBYTE
    for n, subject in enumerate(subjects):
        ctx.clock += 1
        (ctx.repo / "src").mkdir(exist_ok=True)
        (ctx.repo / "src" / f"{kind}_{i:02d}_{n}.txt").write_text(subject[:20], encoding="utf-8")
        msg = ctx.root / "commit-msg.txt"
        msg.write_text(subject + "\n", encoding="utf-8")
        _git(ctx, "add", "-A")
        stamp = f"{tomorrow.isoformat()}T{ctx.clock // 60:02d}:{ctx.clock % 60:02d}:00"
        _git(ctx, "commit", "-q", "-F", str(msg), date=stamp)
    # Defeat the five-minute double-run guard deterministically.
    devlog = ctx.repo / "docs" / "DEVLOG.md"
    old = time.time() - 3600
    os.utime(devlog, (old, old))


def _ad_payload(ctx: Ctx, kind: str, i: int) -> str:
    return json.dumps({"session_id": ctx.sid, "hook_event_name": "Stop"})


AUTO_DEVLOG = Scenario(
    name="auto-devlog",
    impls=("sh", "ps1"),
    payload=_ad_payload,
    setup=_ad_setup,
    before_event=_ad_before,
    extra_env={"AUTO_DEVLOG": "1"},
    targets=(
        Target(
            label="<repo>/docs/DEVLOG.md",
            cls=APPEND,
            path=lambda ctx: ctx.repo / "docs" / "DEVLOG.md",
            # 2026-10-03: ~1.3 KB per entry once 10 commits and 20 files are
            # listed. An entry is capped at 10 commit lines and 20 file lines;
            # with ordinary subjects and paths that is well under 4 KiB.
            normal_cap=4096,
            # 2026-10-03: 4574 B on ps1. One 500-code-point subject is 1500 B of
            # UTF-8; Windows PowerShell 5.1 decodes git output through the OEM
            # codepage, which roughly doubles it, on top of a ~1.1 KB entry.
            # 8 KiB bounds that without admitting an untruncated 64 KiB field.
            multibyte_cap=8192,
            oversized_cap=4096,
        ),
    ),
)

# skill-tracker ------------------------------------------------------------------


def _st_payload(ctx: Ctx, kind: str, i: int) -> str:
    skill = f"skill-{i:02d}"
    if kind == "oversized":
        skill = "K" * OVERSIZE
    elif kind == "multibyte":
        skill = MULTIBYTE
    return json.dumps(
        {"session_id": ctx.sid, "tool_name": "Skill", "tool_input": {"skill": skill}},
        ensure_ascii=False,
    )


SKILL_TRACKER = Scenario(
    name="skill-tracker",
    impls=("py",),
    payload=_st_payload,
    targets=(
        Target(
            label="~/.nexus-hub/state/skill-usage-<session>.json",
            cls=OVERWRITE,
            path=lambda ctx: ctx.home / ".nexus-hub" / "state" / f"skill-usage-{ctx.sid}.json",
            # 2026-10-03: ~250 B after 20 distinct skills. The file is the
            # de-duplicated list of skill names used in one session; the whole
            # catalog (339 skills, names <= 64 chars) fits in 32 KiB.
            normal_cap=32768,
            multibyte_cap=32768,
            oversized_cap=32768,
        ),
    ),
)

SCENARIOS = (LEARNING_CAPTURE, PROVENANCE_LEDGER, SESSION_SUMMARY, AUTO_DEVLOG, SKILL_TRACKER)

# Known breaches, measured on 2026-10-03. Each entry is reported, never fixed by
# this plan (v4.13.9 Phase 5). The test asserts the breach is STILL present and
# then xfails, so fixing a hook makes the test fail until its entry is removed.
# Key: (scenario, impl, target label, event kind). Value: reason.
# A reason starting with "[bash+jq]" applies to the .sh leg only when the bash
# that runs it has jq on PATH (the .sh copies the field only through jq).
_LC = "<repo>/.nexus/observations.jsonl"
_PL = "~/.nexus-hub/cache/provenance/<session>.tsv"
_SL = "~/.claude/session-log.md"
_SD = "<repo>/.nexus/context/last-session.md"
_DL = "<repo>/docs/DEVLOG.md"
_ST = "~/.nexus-hub/state/skill-usage-<session>.json"
KNOWN_BREACHES: dict[tuple[str, str, str, str], str] = {
    # prompt_sample is cut to 400 chars, but hook_event_name and tool_name are
    # copied whole: 2 x 64 KiB fields -> ~131.5 KB line (sh 131549, ps1 131543).
    ("learning-capture", "sh", _LC, "oversized"): "event/tool fields untruncated",
    ("learning-capture", "ps1", _LC, "oversized"): "event/tool fields untruncated",
    # The path is recorded whole (65699 B line); rotation bounds LINES, not bytes,
    # so the ledger's byte size is NEXUS_PROVENANCE_MAX x the longest path.
    ("provenance-ledger", "sh", _PL, "oversized"): "file_path untruncated",
    ("provenance-ledger", "ps1", _PL, "oversized"): "file_path untruncated",
    # session_duration is copied whole into the log row and the digest (ps1
    # always; sh only through jq, absent on the 2026-10-03 Windows host).
    ("session-summary", "ps1", _SL, "oversized"): "duration untruncated",
    ("session-summary", "ps1", _SL, "multibyte"): "duration untruncated",
    ("session-summary", "ps1", _SD, "oversized"): "duration untruncated",
    ("session-summary", "sh", _SL, "oversized"): "[bash+jq] duration untruncated",
    ("session-summary", "sh", _SL, "multibyte"): "[bash+jq] duration untruncated",
    ("session-summary", "sh", _SD, "oversized"): "[bash+jq] duration untruncated",
    # Commit subjects are listed whole (up to 10 per entry, re-listed while
    # they stay newer than the newest entry date).
    ("auto-devlog", "ps1", _DL, "oversized"): "commit subject untruncated",
    # Not a size breach but found by the liveness check: once a `## [` heading
    # reaches line 1, INSERT_LINE = 0, awk's NR == 0 never matches, and every
    # later entry is silently dropped while the hook reports "entry prepended".
    # The .ps1 sibling splices correctly (parity divergence).
    ("auto-devlog", "sh", _DL, "liveness"): "entries silently dropped after line-1 heading",
    # The skill name is stored whole in the de-duplicated JSON list.
    ("skill-tracker", "py", _ST, "oversized"): "skill name untruncated",
}

# --- Runner ----------------------------------------------------------------------


def _prefix(request: pytest.FixtureRequest, scenario: Scenario, impl: str) -> list[str]:
    if impl == "sh":
        return [request.getfixturevalue("bash_bin"), str(_HOOKS_DIR / f"{scenario.name}.sh")]
    if impl == "ps1":
        return [
            request.getfixturevalue("powershell_bin"),
            "-NoProfile",
            "-File",
            str(_HOOKS_DIR / f"{scenario.name}.ps1"),
        ]
    return [sys.executable, str(_HOOKS_DIR / f"{scenario.name}.py")]


def _fire(ctx: Ctx, prefix: list[str], scenario: Scenario, kind: str, i: int) -> None:
    scenario.before_event(ctx, kind, i)
    env = {**ctx.env, **scenario.extra_env}
    proc = subprocess.run(
        prefix,
        input=scenario.payload(ctx, kind, i).encode("utf-8"),
        cwd=ctx.repo,
        env=env,
        capture_output=True,
        timeout=180,
        check=False,
    )
    assert proc.returncode == 0, (
        f"UNMEASURED: {scenario.name} exited {proc.returncode}: "
        f"{proc.stderr.decode('utf-8', 'replace')[:500]}"
    )


def _size(path: Path) -> int:
    return path.stat().st_size if path.is_file() else -1


@dataclass
class Measure:
    sizes: list[int] = field(default_factory=list)  # size after each event

    def delta(self, idx: int, start: int) -> int:
        prev = self.sizes[idx - 1] if idx > 0 else start
        return self.sizes[idx] - max(prev, 0)


_TABLE: list[dict[str, str]] = []


def _cases() -> list[pytest.param]:
    return [
        pytest.param(scenario, impl, id=f"{scenario.name}-{impl}")
        for scenario in SCENARIOS
        for impl in scenario.impls
    ]


def _bash_has_jq(bash: str) -> bool:
    proc = subprocess.run([bash, "-c", "command -v jq"], capture_output=True, timeout=60, check=False)
    return proc.returncode == 0


@pytest.mark.parametrize(("scenario", "impl"), _cases())
def test_hook_size_bound(
    request: pytest.FixtureRequest, tmp_path: Path, scenario: Scenario, impl: str
) -> None:
    prefix = _prefix(request, scenario, impl)
    ctx = make_ctx(tmp_path)
    # Multi-byte before oversized, so an overwrite file (or an entry that
    # re-lists earlier commits) does not carry the 64 KiB field into the
    # multi-byte reading.
    kinds = ["normal"] * EVENTS + ["multibyte", "oversized"]
    measures = {t.label: Measure() for t in scenario.targets}
    starts = {}

    with real_guard(ctx.token):
        scenario.setup(ctx)
        starts = {t.label: max(_size(t.path(ctx)), 0) for t in scenario.targets}
        for i, kind in enumerate(kinds):
            _fire(ctx, prefix, scenario, kind, i)
            for target in scenario.targets:
                measures[target.label].sizes.append(_size(target.path(ctx)))

    violations: dict[tuple[str, str, str, str], str] = {}
    for target in scenario.targets:
        m = measures[target.label]
        start = starts[target.label]
        assert m.sizes[0] >= 0, (
            f"UNMEASURED: {scenario.name}-{impl} never created {target.label}"
        )
        overwrite = target.cls == OVERWRITE
        per_event = [m.sizes[i] if overwrite else m.delta(i, start) for i in range(len(kinds))]
        normal = per_event[:EVENTS]
        multibyte, oversized = per_event[EVENTS], per_event[EVENTS + 1]
        _TABLE.append(
            {
                "hook": scenario.name,
                "impl": impl,
                "class": target.cls,
                "file": target.label,
                "typical": str(int(statistics.median(normal))),
                "oversized": str(oversized),
                "multibyte": str(multibyte),
                "after20": str(m.sizes[EVENTS - 1]),
            }
        )
        print(
            f"\n[size-bound] {scenario.name}-{impl} {target.cls} {target.label}: "
            f"typical={int(statistics.median(normal))} oversized={oversized} "
            f"multibyte={multibyte} after20={m.sizes[EVENTS - 1]} final={m.sizes[-1]}"
        )

        if target.cls == APPEND:
            sizes = [start, *m.sizes]
            assert all(b >= a for a, b in pairwise(sizes)), (
                f"append-only {target.label} shrank: {sizes}"
            )
        if not overwrite and min(normal) <= 0:
            # Liveness: under the default caps no rotation is reached within 20
            # events, so every ordinary event must add bytes. A hook that runs,
            # exits 0 and writes nothing would otherwise pass every size check.
            key = (scenario.name, impl, target.label, "liveness")
            violations[key] = f"ordinary event added no bytes: deltas {normal}"
        checks = (("normal", max(normal), target.normal_cap),
                  ("multibyte", multibyte, target.multibyte_cap),
                  ("oversized", oversized, target.oversized_cap))
        for kind, value, cap in checks:
            if value > cap:
                key = (scenario.name, impl, target.label, kind)
                violations[key] = f"{kind} event: {value} B > cap {cap} B"

    _settle(request, scenario, impl, violations)


def _settle(
    request: pytest.FixtureRequest,
    scenario: Scenario,
    impl: str,
    violations: dict[tuple[str, str, str, str], str],
) -> None:
    """Fail on any unknown breach; xfail when only known breaches remain."""
    expected = {
        key: reason
        for key, reason in KNOWN_BREACHES.items()
        if key[0] == scenario.name and key[1] == impl
        and not (reason.startswith("[bash+jq]") and not _bash_has_jq(
            request.getfixturevalue("bash_bin")))
    }
    unknown = {k: v for k, v in violations.items() if k not in expected}
    assert not unknown, f"size bound breached: {unknown}"
    fixed = [k for k in expected if k not in violations]
    assert not fixed, (
        f"known breach no longer reproduces (remove it from KNOWN_BREACHES): {fixed}"
    )
    if expected:
        pytest.xfail("known breach(es): " + "; ".join(
            f"{k[2]} {k[3]}: {violations[k]} ({expected[k]})" for k in expected
        ))


# --- Bounded rotation: drive past the lowered cap --------------------------------

ROTATION_CASES = [
    pytest.param(LEARNING_CAPTURE, impl, "NEXUS_LEARNING_MAX_BYTES", 2048, "bytes",
                 id=f"learning-capture-{impl}")
    for impl in LEARNING_CAPTURE.impls
] + [
    pytest.param(PROVENANCE_LEDGER, impl, "NEXUS_PROVENANCE_MAX", 5, "lines",
                 id=f"provenance-ledger-{impl}")
    for impl in PROVENANCE_LEDGER.impls
]


@pytest.mark.parametrize(("scenario", "impl", "env_var", "cap", "unit"), ROTATION_CASES)
def test_rotation_holds_lowered_cap(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    scenario: Scenario,
    impl: str,
    env_var: str,
    cap: int,
    unit: str,
) -> None:
    prefix = _prefix(request, scenario, impl)
    ctx = make_ctx(tmp_path)
    ctx.env[env_var] = str(cap)
    target = scenario.targets[0]
    observed: list[int] = []
    with real_guard(ctx.token):
        for i in range(EVENTS):
            _fire(ctx, prefix, scenario, "normal", i)
            data = target.path(ctx).read_bytes()
            observed.append(len(data) if unit == "bytes" else data.count(b"\n"))
    print(f"\n[size-bound] rotation {scenario.name}-{impl} {unit} cap={cap}: {observed}")
    assert all(v <= cap for v in observed), f"{target.label} exceeded {cap} {unit}: {observed}"
    if unit == "bytes":
        # The rotation path was actually reached: the file shrank at least once.
        assert any(b < a for a, b in pairwise(observed)), (
            f"rotation path not reached within {EVENTS} events: {observed}"
        )
    else:
        assert observed[-1] == cap, f"expected exactly {cap} retained lines: {observed}"


def test_print_measured_table() -> None:
    """Print the table gathered by the parametrized cases (visible with -s)."""
    if not _TABLE:
        pytest.skip("run together with test_hook_size_bound to print the table")
    cols = ("hook", "impl", "class", "file", "typical", "oversized", "multibyte", "after20")
    print(f"\n\nMeasured on {MEASURED_ON} (bytes; overwrite rows show resulting size)")
    print(" | ".join(cols))
    for row in _TABLE:
        print(" | ".join(row[c] for c in cols))
