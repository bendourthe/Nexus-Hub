"""Integration tests for consented Legacy Instruction Block removal (v4.13.3 Phase 4).

Every case runs on a throwaway HOME. A candidate span is removed only when the
install context carries that span's consent token from the file's current
bytes; otherwise the install reports, backs up, and leaves every byte outside
the managed block alone. Each integration case asserts the cleanup owner
actually ran for its file (the path is recorded in the run's `touched` map).
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.installer import instruction_merge as im  # noqa: E402
from scripts.lib.integrations import get, list_keys  # noqa: E402
from scripts.lib.integrations import runner  # noqa: E402
from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402
from scripts.lib.integrations.result import FileAction  # noqa: E402

START, END = im.DEFAULT_START_MARKER, im.DEFAULT_END_MARKER
INDEX = (REPO_ROOT / "data" / "SKILL_INDEX.md").read_text(encoding="utf-8").splitlines()
LEGACY = ["## Tech Stack", *INDEX]
DETECTION_ROOTS = (".codeium", ".copilot", ".qwen", ".kimi", ".openclaw", ".hermes", ".pi", ".gemini", ".cursor")


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "home"
    root.mkdir()
    monkeypatch.setenv("HOME", str(root))
    monkeypatch.setenv("USERPROFILE", str(root))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: root))
    return root


def _ctx(home: Path, consents: frozenset = frozenset(), *, dry_run: bool = False, scope: str = "global",
         target: Path | None = None, overwrite: bool = False, instruction_only: bool = True) -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=target or home,
        scope=scope,
        explicit_target=True,
        overwrite=overwrite,
        dry_run=dry_run,
        manifest=InstallManifest(),
        instruction_only=instruction_only,
        legacy_removal_hashes=consents,
    )


def _fixture(path: Path, *, user_above: str = "# My rules\n- keep answers short\n", managed: str = "old body",
             newline: str = "\n", bom: bool = False) -> bytes:
    text = user_above + "\n" + "\n".join(LEGACY) + "\n\n" + f"{START}\n{managed}\n{END}\n"
    data = text.replace("\n", newline).encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def _merge(path: Path, ctx, body: str = "new body") -> FileAction:
    return im.merge_instruction(path, body, ctx=ctx, legacy_header="## Nexus-Hub")


def _tokens(ctx) -> list[str]:
    return [c.consent_sha256 for c in im.collect_legacy_report(ctx)[0]]


def _backups(home: Path) -> list[Path]:
    root = home / ".nexus-hub" / "state" / "backups"
    return sorted(root.iterdir()) if root.is_dir() else []


# --- report only, backups ---------------------------------------------------


def test_report_only_keeps_legacy_bytes_and_backs_up(home: Path) -> None:
    path = home / "CLAUDE.md"
    original = _fixture(path)
    ctx = _ctx(home)
    assert _merge(path, ctx).action == "updated"
    after = path.read_bytes()
    assert after.startswith(original[: original.index(START.encode())])
    assert b"new body" in after
    candidates, refused = im.collect_legacy_report(ctx)
    assert len(candidates) == 1 and refused == []
    assert candidates[0].tokens > 0
    assert Path(candidates[0].diff_path).read_text(encoding="utf-8").count("\n-") == candidates[0].line_count
    [backup] = _backups(home)
    assert backup.read_bytes() == original
    assert backup.name == f"{hashlib.sha256(original).hexdigest()}.CLAUDE.md"


def test_backup_is_content_addressed_and_never_pruned(home: Path) -> None:
    path = home / "CLAUDE.md"
    _fixture(path)
    for body in ("one", "one", "two"):
        _merge(path, _ctx(home), body)
    names = [p.name for p in _backups(home)]
    assert len(names) == 2  # original, and the "one" state; the repeat added nothing
    first = _backups(home)
    _merge(path, _ctx(home), "three")
    assert set(first) <= set(_backups(home))


@pytest.mark.skipif(sys.platform != "win32", reason="Windows ACL check")
def test_windows_backup_acl_is_owner_only(home: Path) -> None:
    path = home / "CLAUDE.md"
    content = _fixture(path)
    backup = im.backup_bytes(home / ".nexus-hub" / "state" / "backups", path, content)
    assert backup is not None
    for item in (backup.parent, backup):
        quoted = "'" + str(item).replace("'", "''") + "'"
        script = (
            f"$acl = Get-Acl -LiteralPath {quoted}; "
            "$sid = $acl.Access[0].IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value; "
            "Write-Output ($acl.AreAccessRulesProtected.ToString() + '|' + $acl.Access.Count + '|' + $sid)"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "True|1|S-1-3-4"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX mode check")
def test_posix_backup_modes_are_owner_only(home: Path) -> None:
    path = home / "CLAUDE.md"
    content = _fixture(path)
    backup = im.backup_bytes(home / ".nexus-hub" / "state" / "backups", path, content)
    assert backup is not None
    assert backup.parent.stat().st_mode & 0o777 == 0o700
    assert backup.stat().st_mode & 0o777 == 0o600


def test_yes_style_overwrite_never_implies_consent(home: Path) -> None:
    path = home / "CLAUDE.md"
    _fixture(path)
    ctx = _ctx(home, overwrite=True)
    _merge(path, ctx)
    assert len(_tokens(ctx)) == 1


# --- consent ----------------------------------------------------------------


def test_token_from_one_install_removes_on_the_next(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = home / "CLAUDE.md"
    _fixture(path)
    first = _ctx(home)
    _merge(path, first)  # also refreshes the managed block
    [token] = _tokens(first)
    before = path.read_bytes()
    writes: list[bytes] = []
    real_replace = im._atomic_replace_bytes
    monkeypatch.setattr(im, "_atomic_replace_bytes", lambda p, c: (writes.append(c), real_replace(p, c)))
    second = _ctx(home, frozenset({token}))
    assert _merge(path, second).action == "updated"
    assert len(writes) == 1
    candidates, refused = im.collect_legacy_report(second)
    assert candidates == [] and refused == []
    after = path.read_bytes()
    lines = before.splitlines(keepends=True)
    assert after == b"".join(lines[:3] + lines[3 + len(LEGACY) :])
    assert after.count(b"**Total:") == 0
    assert f"{START}\nnew body\n{END}\n".encode() in after


def test_stale_token_is_refused_and_file_unchanged(home: Path) -> None:
    path = home / "CLAUDE.md"
    _fixture(path)
    first = _ctx(home)
    _merge(path, first)
    [token] = _tokens(first)
    path.write_bytes(b"# edited by hand\n" + path.read_bytes())
    snapshot = path.read_bytes()
    stale = _ctx(home, frozenset({token}))
    assert _merge(path, stale).action == "unchanged"
    assert path.read_bytes() == snapshot
    assert im.collect_legacy_report(stale)[1] == [token]


def test_identical_candidate_in_another_file_needs_its_own_token(home: Path) -> None:
    a, b = home / "a" / "AGENTS.md", home / "b" / "AGENTS.md"
    _fixture(a)
    _fixture(b)
    ctx = _ctx(home)
    _merge(a, ctx)
    _merge(b, ctx)
    token_a, token_b = _tokens(ctx)
    assert token_a != token_b
    b_before = b.read_bytes()
    only_a = _ctx(home, frozenset({token_a}))
    _merge(b, only_a)
    assert b.read_bytes() == b_before
    _merge(a, only_a)
    assert b"**Total:" not in a.read_bytes()


def test_dry_run_token_is_usable_on_a_later_real_install(home: Path) -> None:
    path = home / "CLAUDE.md"
    _fixture(path, managed="new body")
    dry = _ctx(home, dry_run=True)
    _merge(path, dry)
    [token] = _tokens(dry)
    assert _backups(home) == []
    _merge(path, _ctx(home, frozenset({token})))
    assert b"**Total:" not in path.read_bytes()


@pytest.mark.parametrize(("newline", "bom"), [("\r\n", False), ("\r\n", True), ("\n", True)])
def test_crlf_and_bom_are_byte_preserved(home: Path, newline: str, bom: bool) -> None:
    path = home / "CLAUDE.md"
    _fixture(path, managed="new body", newline=newline, bom=bom)
    first = _ctx(home)
    assert _merge(path, first).action == "unchanged"
    [token] = _tokens(first)
    before = path.read_bytes()
    _merge(path, _ctx(home, frozenset({token})))
    after = path.read_bytes()
    assert after.startswith(b"\xef\xbb\xbf") == bom
    body = after[3:] if bom else after
    if newline == "\r\n":
        assert body.count(b"\n") == body.count(b"\r\n")
    head = before[: before.index(b"## Tech Stack")]
    assert after.startswith(head)
    assert after.endswith(before[before.index(START.encode()) - len(newline) :])


# --- failure modes ----------------------------------------------------------


def test_unwritable_backup_directory_skips_removal(home: Path) -> None:
    path = home / "CLAUDE.md"
    _fixture(path)
    first = _ctx(home)
    _merge(path, first)
    [token] = _tokens(first)
    backups = home / ".nexus-hub" / "state" / "backups"
    for existing in backups.iterdir():
        existing.unlink()
    backups.rmdir()
    backups.write_text("not a directory", encoding="utf-8")
    ctx = _ctx(home, frozenset({token}))
    _merge(path, ctx, "newer body")
    assert b"**Total:" in path.read_bytes()
    assert b"newer body" in path.read_bytes()
    assert any("no verified backup" in note for _, note in ctx.legacy_run.notes)
    assert im.collect_legacy_report(ctx)[1] == [token]


def test_backup_permission_failure_skips_consented_removal(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = home / "CLAUDE.md"
    _fixture(path)
    first = _ctx(home)
    _merge(path, first)
    [token] = _tokens(first)
    backups = home / ".nexus-hub" / "state" / "backups"
    real_chmod = im.os.chmod

    def deny_backup_permissions(candidate: str | Path, mode: int) -> None:
        if Path(candidate) == backups:
            raise PermissionError("cannot restrict backup directory")
        real_chmod(candidate, mode)

    monkeypatch.setattr(im.os, "chmod", deny_backup_permissions)
    ctx = _ctx(home, frozenset({token}))
    _merge(path, ctx, "newer body")
    assert b"**Total:" in path.read_bytes()
    assert any("no verified backup" in note for _, note in ctx.legacy_run.notes)
    assert im.collect_legacy_report(ctx)[1] == [token]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows ACL failure check")
def test_windows_acl_failure_rejects_backup(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = home / "CLAUDE.md"
    content = _fixture(path)

    def fail_acl(_path: Path, *, directory: bool) -> None:
        raise PermissionError("cannot set backup ACL")

    monkeypatch.setattr(im, "_windows_owner_only", fail_acl)
    assert im.backup_bytes(home / ".nexus-hub" / "state" / "backups", path, content) is None


@pytest.mark.skipif(sys.platform != "win32", reason="Windows ACL failure check")
def test_windows_file_acl_failure_rejects_backup(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = home / "CLAUDE.md"
    content = _fixture(path)
    real_acl = im._windows_owner_only

    def fail_file_acl(candidate: Path, *, directory: bool) -> None:
        if not directory:
            raise PermissionError("cannot restrict backup file")
        real_acl(candidate, directory=directory)

    monkeypatch.setattr(im, "_windows_owner_only", fail_file_acl)
    assert im.backup_bytes(home / ".nexus-hub" / "state" / "backups", path, content) is None


@pytest.mark.skipif(sys.platform != "win32", reason="Windows owner check")
def test_windows_other_owner_rejects_backup(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = home / "CLAUDE.md"
    content = _fixture(path)
    monkeypatch.setattr(im, "_windows_current_user_owns", lambda _path: False, raising=False)
    assert im.backup_bytes(home / ".nexus-hub" / "state" / "backups", path, content) is None


def test_unusable_state_directory_skips_removal(home: Path) -> None:
    path = home / "CLAUDE.md"
    _fixture(path)
    first = _ctx(home)
    _merge(path, first)
    [token] = _tokens(first)
    state = home / ".nexus-hub" / "state"
    import shutil

    shutil.rmtree(state)
    state.write_text("not a directory", encoding="utf-8")
    ctx = _ctx(home, frozenset({token}))
    _merge(path, ctx)
    assert b"**Total:" in path.read_bytes()
    assert any("no usable lock" in note for _, note in ctx.legacy_run.notes)


def test_external_change_before_final_hash_fails_closed(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = home / "CLAUDE.md"
    _fixture(path)
    first = _ctx(home)
    _merge(path, first)
    [token] = _tokens(first)
    real_render = im.render_marker_merge

    def render_then_race(*args, **kwargs):
        rendered = real_render(*args, **kwargs)
        path.write_bytes(b"# someone else wrote this\n")
        return rendered

    monkeypatch.setattr(im, "render_marker_merge", render_then_race)
    ctx = _ctx(home, frozenset({token}))
    action = _merge(path, ctx, "newer body")
    assert (action.action, action.reason) == ("kept", "refuse-concurrent-change")
    assert path.read_bytes() == b"# someone else wrote this\n"
    assert im.collect_legacy_report(ctx)[1] == [token]


def test_malformed_markers_offer_no_candidates(home: Path) -> None:
    path = home / "CLAUDE.md"
    from scripts.lib.installer.legacy_instruction_block import detect

    path.write_text("\n".join(LEGACY) + f"\n{START}\norphan start\n", encoding="utf-8")
    assert (detect(path).status, detect(path).spans) == ("markers-malformed", [])
    ctx = _ctx(home, frozenset({"0" * 64}))
    _merge(path, ctx)
    # The merge appends a complete block, so the NEXT install may offer the
    # leftover; this one had nothing to consent to and removed nothing.
    assert im.collect_legacy_report(ctx)[1] == ["0" * 64]
    assert path.read_text(encoding="utf-8").startswith("\n".join(LEGACY))


def test_two_cooperating_installers_do_not_lose_updates(home: Path, tmp_path: Path) -> None:
    path = home / "SHARED.md"
    path.write_text("# shared\n", encoding="utf-8")
    worker = textwrap.dedent(
        """
        import sys
        from pathlib import Path
        from types import SimpleNamespace
        sys.path.insert(0, sys.argv[1])
        from scripts.lib.installer import instruction_merge as im
        home, target, tag, start, end = Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
        ctx = SimpleNamespace(scope="global", global_root=home, dry_run=False, legacy_removal_hashes=frozenset())
        for i in range(25):
            im.merge_instruction(target, f"{tag} {i}", ctx=ctx, start_marker=start, end_marker=end)
        """
    )
    script = tmp_path / "worker.py"
    script.write_text(worker, encoding="utf-8")
    procs = [
        subprocess.Popen([sys.executable, str(script), str(REPO_ROOT), str(home), str(path), tag, s, e])
        for tag, s, e in (("alpha", START, END), ("beta", "<!-- ORG_START -->", "<!-- ORG_END -->"))
    ]
    assert [p.wait(timeout=120) for p in procs] == [0, 0]
    text = path.read_text(encoding="utf-8")
    assert "alpha 24" in text and "beta 24" in text
    assert text.startswith("# shared\n")


# --- every marker-merged integration ---------------------------------------


def _touched_after_install(key: str, home: Path, scope: str, full: bool = False) -> tuple[InstallContext, list[str]]:
    target = home if scope == "global" else home / "project"
    target.mkdir(exist_ok=True)
    ctx = _ctx(home, scope=scope, target=target, instruction_only=not full)
    im.legacy_run(ctx).owner = key
    get(key).install(ctx)
    return ctx, list(ctx.legacy_run.touched)


def _exercise(key: str, home: Path, scope: str, full: bool = False) -> list[str]:
    """Seed a leftover above each file `key` merges, then report and remove it."""
    _, touched = _touched_after_install(key, home, scope, full)
    for path_str in touched:
        path = Path(path_str)
        path.write_bytes(("\n".join(LEGACY) + "\n\n").encode("utf-8") + path.read_bytes())
        report_ctx, again = _touched_after_install(key, home, scope, full)
        assert path_str in again, f"{key} did not route {path} through merge_instruction"
        mine = [c for c in im.collect_legacy_report(report_ctx)[0] if c.path == path_str]
        assert len(mine) == 1, (key, path_str)
        consent = _ctx(home, frozenset({mine[0].consent_sha256}), scope=scope,
                       target=home if scope == "global" else home / "project", instruction_only=not full)
        im.legacy_run(consent).owner = key
        get(key).install(consent)
        assert b"**Total:" not in path.read_bytes().split(START.encode())[0], (key, path_str)
    return touched


@pytest.mark.parametrize("scope", ["global", "workspace"])
def test_every_marker_merged_integration_runs_cleanup(home: Path, scope: str) -> None:
    for root in DETECTION_ROOTS:
        (home / root).mkdir(exist_ok=True)
    exercised = {key for key in list_keys() if _exercise(key, home, scope)}
    base_owned = {"claude", "codex", "gemini", "opencode", "qwen", "openclaw", "antigravity"}
    direct = {"antigravity2", "windsurf"} | ({"cursor", "copilot"} if scope == "workspace" else set())
    assert base_owned | direct <= exercised


def test_copilot_personal_instructions_run_cleanup(home: Path) -> None:
    (home / ".copilot").mkdir()
    assert _exercise("copilot", home, "global", full=True)


def test_org_knowledge_merge_routes_through_the_owner(home: Path) -> None:
    from scripts.lib.integrations import org_knowledge

    path = home / "AGENTS.md"
    _fixture(path)
    ctx = SimpleNamespace(scope="global", global_root=home, dry_run=False, legacy_removal_hashes=frozenset())
    org_knowledge._merge_org_after_nexus(path, "org rules", ctx)
    assert str(path) in ctx.legacy_run.touched
    assert len(im.collect_legacy_report(ctx)[0]) == 1


def test_no_integration_calls_the_primitive_directly() -> None:
    offenders = []
    for module in sorted((REPO_ROOT / "scripts" / "lib" / "integrations").glob("*.py")):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if name == "merge_marker_section":
                    offenders.append(f"{module.name}:{node.lineno}")
                if name == "merge_instruction" and not any(k.arg == "ctx" for k in node.keywords):
                    offenders.append(f"{module.name}:{node.lineno} (no ctx)")
    assert offenders == []


# --- runner, manifest, teardown ---------------------------------------------


def _run(home: Path, *extra: str) -> tuple[int, dict]:
    summary = home / "summary.json"
    code = runner.main(["install", "--scope", "global", "--target", str(home), "--integrations", "claude",
                        "--instruction-only", "--quiet", "--summary-json", str(summary), *extra])
    return code, json.loads(summary.read_text(encoding="utf-8"))


def test_runner_reports_candidates_and_refuses_stale_tokens(home: Path) -> None:
    path = home / ".claude" / "CLAUDE.md"
    _fixture(path)
    code, summary = _run(home)
    assert code == 0
    [candidate] = summary["legacy"]["candidates"]
    assert candidate["command"] == f"--remove-legacy-instructions={candidate['consent_sha256']}"
    assert candidate["platform"] == "claude" and candidate["estimated_tokens"] > 0
    assert summary["legacy"]["backups"]
    token = candidate["consent_sha256"]
    code, summary = _run(home, f"--remove-legacy-instructions={token}")
    legacy = summary["legacy"]
    assert (code, legacy["candidates"], legacy["refused"], legacy["consumed"]) == (0, [], [], [token])
    before = path.read_bytes()
    code, summary = _run(home, f"--remove-legacy-instructions={token}")
    assert (code, summary["legacy"]["refused"], summary["legacy"]["consumed"]) == (0, [token], [])
    assert path.read_bytes() == before


def test_runner_rejects_a_malformed_token_before_writing(home: Path) -> None:
    path = home / ".claude" / "CLAUDE.md"
    original = _fixture(path)
    code = runner.main(["install", "--scope", "global", "--target", str(home), "--integrations", "claude",
                        "--instruction-only", "--quiet", "--remove-legacy-instructions=nothex"])
    assert code == 2
    assert path.read_bytes() == original


def test_report_actions_are_not_recorded_in_the_manifest(home: Path) -> None:
    manifest = InstallManifest()
    manifest.record_actions("claude", [FileAction(path=str(home / "x.md"), action="updated"),
                                       FileAction(path=str(home / "b.bak"), action="backed-up"),
                                       FileAction(path=str(home / "x.md"), action="detected")])
    assert [entry["action"] for entry in manifest.actions_for("claude")] == ["updated"]


def test_teardown_preserves_backups(home: Path) -> None:
    path = home / ".claude" / "CLAUDE.md"
    _fixture(path)
    ctx = _ctx(home)
    get("claude").install(ctx)
    before = {p.name: p.read_bytes() for p in _backups(home)}
    assert before
    get("claude").teardown(ctx)
    assert {p.name: p.read_bytes() for p in _backups(home)} == before


# --- installer plumbing -----------------------------------------------------


def _candidate(path: str, token: str, start: int = 1) -> dict:
    return {"file": path, "start_line": start, "end_line": start + 9, "estimated_tokens": 120,
            "consent_sha256": token, "diff": f"/state/{token}.diff"}


def test_aggregate_keeps_the_last_writer_per_file_and_unused_tokens_only() -> None:
    first = {"legacy": {"files": ["/a", "/b"], "candidates": [_candidate("/a", "1" * 64), _candidate("/b", "2" * 64)],
                        "backups": [{"file": "/a"}], "consumed": []}}
    second = {"legacy": {"files": ["/a"], "candidates": [_candidate("/a", "3" * 64)], "backups": [],
                         "consumed": ["4" * 64]}}
    report = runner.aggregate_legacy_summaries([first, second], ["4" * 64, "5" * 64])
    assert sorted(c["consent_sha256"] for c in report["candidates"]) == ["2" * 64, "3" * 64]
    assert report["refused"] == ["5" * 64]
    assert len(report["backups"]) == 1


@pytest.mark.parametrize(("form", "flag"), [("sh", "--remove-legacy-instructions="),
                                             ("ps1", "-RemoveLegacyInstructions ")])
def test_legacy_report_prints_the_installer_spelling(tmp_path: Path, form: str, flag: str,
                                                      capsys: pytest.CaptureFixture[str]) -> None:
    summary = {"legacy": {"files": ["/a"], "candidates": [_candidate("/a", "1" * 64)], "backups": [], "consumed": []}}
    (tmp_path / "0000.json").write_text(json.dumps(summary), encoding="utf-8")
    assert runner.main(["legacy-report", "--summaries", str(tmp_path), "--form", form, "--token", "9" * 64]) == 0
    out = capsys.readouterr().out
    assert f"re-run the installer with: {flag}{'1' * 64}" in out
    assert f"refused: {flag}{'9' * 64}" in out
    assert "review first: /state/" in out


def test_legacy_report_is_silent_when_nothing_to_say(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "0000.json").write_text(json.dumps({"legacy": {"files": ["/a"], "candidates": []}}), encoding="utf-8")
    assert runner.main(["legacy-report", "--summaries", str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def _shell(kind: str) -> list[str] | None:
    import shutil

    if kind == "sh":
        exe = shutil.which("bash")
        return [exe, str(REPO_ROOT / "scripts" / "installer.sh"), "--remove-legacy-instructions=nothex"] if exe else None
    exe = shutil.which("pwsh") or shutil.which("powershell")
    return ([exe, "-NoProfile", "-File", str(REPO_ROOT / "scripts" / "installer.ps1"),
             "-RemoveLegacyInstructions", "nothex"] if exe else None)


@pytest.mark.parametrize("kind", ["sh", "ps1"])
def test_installers_reject_a_malformed_token_before_installing(kind: str, home: Path) -> None:
    argv = _shell(kind)
    if argv is None:
        pytest.skip(f"{kind} interpreter unavailable")
    result = subprocess.run(argv, capture_output=True, text=True, timeout=180, check=False, cwd=home,
                            env={**__import__("os").environ, "HOME": str(home), "USERPROFILE": str(home)})
    assert result.returncode == 2, result.stdout[-400:] + result.stderr[-400:]
    assert "64-hex consent token" in result.stdout + result.stderr
    assert not (home / ".nexus-hub").exists()


@pytest.mark.parametrize("installer", ["installer.sh", "installer.ps1"])
def test_installers_forward_tokens_and_print_the_combined_report(installer: str) -> None:
    text = (REPO_ROOT / "scripts" / installer).read_text(encoding="utf-8-sig")
    assert "--remove-legacy-instructions=$legacy" in text.replace("$legacyToken", "$legacy_token")
    assert '"legacy-report"' in text
    assert text.count("LegacyReport" if installer.endswith(".ps1") else "write_legacy_report") >= 3


def test_bash_token_check_rejects_an_embedded_newline(home: Path) -> None:
    """A line-based grep would accept `<64 hex>\n<anything>`; the installer must not."""
    import os
    import shutil

    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash unavailable")
    token = "a" * 64 + "\nextra"
    result = subprocess.run([bash, str(REPO_ROOT / "scripts" / "installer.sh"), f"--remove-legacy-instructions={token}"],
                            capture_output=True, text=True, timeout=180, check=False, cwd=home,
                            env={**os.environ, "HOME": str(home), "USERPROFILE": str(home)})
    assert result.returncode == 2, result.stdout[-300:] + result.stderr[-300:]
    assert not (home / ".nexus-hub").exists()


def test_legacy_report_never_echoes_a_malformed_token(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "0000.json").write_text(json.dumps({"legacy": {"files": [], "candidates": []}}), encoding="utf-8")
    hostile = "a" * 64 + "\n\x1b[2J"
    assert runner.main(["legacy-report", "--summaries", str(tmp_path), "--token", hostile]) == 0
    assert "\x1b" not in capsys.readouterr().out
