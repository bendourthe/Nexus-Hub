"""Security-critical tests for the v3.17.0 project-local autonomy engine."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.lib import autonomy
from scripts.lib.integrations import list_keys as list_integration_keys

NOW = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)


def _git(
    repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=check,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    if shutil.which("git") is None:  # pragma: no cover
        pytest.skip("git not available")
    root = tmp_path / "autonomy-project"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Autonomy Test")
    (root / ".gitignore").write_text(".nexus-hub/\n", encoding="utf-8")
    (root / "README.md").write_text("seed\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    _git(root, "branch", "-M", "feat/autonomy-tests")
    return root


def _commit(repo: Path, message: str = "config") -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


def _audit(repo: Path) -> list[dict]:
    path = repo / autonomy.AUDIT_RELATIVE_PATH
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _enable(
    repo: Path,
    platform: str = "claude",
    tier: str = "edits_only",
    ttl: int | None = 60,
    **kwargs,
) -> autonomy.OperationResult:
    return autonomy.enable(
        platform,
        tier,
        ttl,
        project_dir=repo,
        now=NOW,
        confirmation=repo.name if tier == "full" else None,
        user="test-user",
        process="pytest:1",
        **kwargs,
    )


def test_enable_creates_backup_before_config_write_and_round_trips_state(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = repo / ".claude" / "settings.local.json"
    config.parent.mkdir()
    original = '{\n  "permissions": {"deny": ["Bash(rm *)"]},\n  "theme": "dark"\n}\n'
    config.write_text(original, encoding="utf-8")
    _commit(repo)

    real_atomic_write = autonomy._atomic_write_bytes
    observed_backup: list[Path] = []

    def assert_backup_first(path: Path, content: bytes, *, mode: int = 0o600) -> None:
        if path == config:
            backups = list(config.parent.glob(config.name + ".bak.*"))
            assert len(backups) == 1
            assert backups[0].read_text(encoding="utf-8") == original
            observed_backup.extend(backups)
        real_atomic_write(path, content, mode=mode)

    monkeypatch.setattr(autonomy, "_atomic_write_bytes", assert_backup_first)
    result = _enable(repo)

    assert result.outcome == "enabled"
    assert result.changed is True
    assert observed_backup == [Path(result.backup_path)]
    assert result.diff.startswith("--- ")
    updated = json.loads(config.read_text(encoding="utf-8"))
    assert updated["permissions"]["defaultMode"] == "acceptEdits"
    assert updated["permissions"]["deny"] == ["Bash(rm *)"]
    assert updated["theme"] == "dark"

    state = autonomy.status(project_dir=repo, now=NOW)
    assert state["platforms"][0]["platform"] == "claude"
    assert state["platforms"][0]["tier"] == "edits_only"
    assert state["platforms"][0]["status"] == "active"
    assert state["platforms"][0]["user"] == "test-user"
    assert state["platforms"][0]["process"] == "pytest:1"
    assert state["platforms"][0]["remaining_seconds"] == 3600
    assert {item["platform"] for item in state["platforms"]} == set(
        list_integration_keys()
    )


def test_enable_preview_returns_diff_without_writing_or_auditing(repo: Path) -> None:
    config = repo / ".claude" / "settings.local.json"

    result = autonomy.enable(
        "claude",
        "full",
        30,
        project_dir=repo,
        now=NOW,
        preview_only=True,
    )

    assert result.outcome == "preview"
    assert result.changed is False
    assert result.diff.startswith("--- ")
    assert result.expiry == "2026-08-14T12:30:00Z"
    assert not config.exists()
    assert not Path(result.backup_path).exists()
    assert not (repo / autonomy.STATE_RELATIVE_PATH).exists()
    assert not (repo / autonomy.AUDIT_RELATIVE_PATH).exists()


def test_status_lists_supported_and_descriptorless_platforms_when_off(
    repo: Path,
) -> None:
    state = autonomy.status(project_dir=repo, now=NOW)

    assert [item["platform"] for item in state["platforms"]] == list_integration_keys()
    claude = next(item for item in state["platforms"] if item["platform"] == "claude")
    gemini = next(item for item in state["platforms"] if item["platform"] == "gemini")
    assert claude == {
        "platform": "claude",
        "supported": True,
        "status": "off",
        "tier": "off",
        "expiry": None,
        "remaining_seconds": 0,
        "available_tiers": ["edits_only", "full"],
    }
    assert gemini["supported"] is False
    assert gemini["available_tiers"] == []


def test_disable_restores_original_and_clears_state_and_backup(repo: Path) -> None:
    config = repo / ".claude" / "settings.local.json"
    config.parent.mkdir()
    original = '{"permissions":{"defaultMode":"default"}}\n'
    config.write_text(original, encoding="utf-8")
    _commit(repo)
    enabled = _enable(repo, tier="full")

    result = autonomy.disable(
        "claude", project_dir=repo, now=NOW + timedelta(minutes=1)
    )

    assert result.outcome == "disabled"
    assert config.read_text(encoding="utf-8") == original
    assert not Path(enabled.backup_path).exists()
    assert not (repo / autonomy.STATE_RELATIVE_PATH).exists()
    assert [record["operation"] for record in _audit(repo)] == ["enable", "disable"]


def test_manual_revert_removes_config_that_did_not_exist_before_enable(
    repo: Path,
) -> None:
    config = repo / "opencode.json"
    enabled = _enable(repo, platform="opencode")
    assert config.exists()

    result = autonomy.revert(
        "opencode", project_dir=repo, now=NOW + timedelta(minutes=2)
    )

    assert result.outcome == "reverted"
    assert not config.exists()
    assert not Path(enabled.backup_path).exists()
    assert not (repo / autonomy.STATE_RELATIVE_PATH).exists()


def test_codex_toml_updates_top_level_keys_and_preserves_tables(repo: Path) -> None:
    config = repo / ".codex" / "config.toml"
    config.parent.mkdir()
    config.write_text(
        'approval_policy = "untrusted"\n\n[profiles.safe]\nsandbox_mode = "read-only"\n',
        encoding="utf-8",
    )
    _commit(repo)

    result = _enable(repo, platform="codex", tier="full")

    assert result.outcome == "enabled"
    text = config.read_text(encoding="utf-8")
    assert 'approval_policy = "never"' in text
    assert 'sandbox_mode = "danger-full-access"' in text.split("[profiles.safe]")[0]
    assert '[profiles.safe]\nsandbox_mode = "read-only"' in text


def test_copilot_jsonc_uses_literal_dotted_setting_key(repo: Path) -> None:
    config = repo / ".vscode" / "settings.json"
    config.parent.mkdir()
    config.write_text(
        '{\n  // user preference\n  "editor.wordWrap": "on"\n}\n', encoding="utf-8"
    )
    _commit(repo)

    result = _enable(repo, platform="copilot", tier="full")

    assert result.outcome == "enabled"
    document = json.loads(config.read_text(encoding="utf-8"))
    assert document["chat.permissions.default"] == "autopilot"
    assert "chat" not in document
    assert document["editor.wordWrap"] == "on"


@pytest.mark.parametrize(
    ("ttl", "message_fragment"),
    [
        (None, "TTL is required"),
        (0, "1 to 480"),
        (-1, "1 to 480"),
        (481, "1 to 480"),
    ],
)
def test_invalid_ttl_values_are_rejected_and_audited_once(
    repo: Path, ttl: int | None, message_fragment: str
) -> None:
    result = _enable(repo, ttl=ttl)

    assert result.outcome == "rejected"
    assert result.gate == "ttl"
    assert message_fragment in result.message
    assert len(_audit(repo)) == 1
    assert _audit(repo)[0]["gate"] == "ttl"
    assert not (repo / ".claude" / "settings.local.json").exists()


@pytest.mark.parametrize("confirmation", [None, "yes", "AUTONOMY-PROJECT"])
def test_full_tier_requires_exact_project_name_confirmation(
    repo: Path, confirmation: str | None
) -> None:
    result = autonomy.enable(
        "claude",
        "full",
        60,
        confirmation=confirmation,
        project_dir=repo,
        now=NOW,
    )

    assert result.outcome == "rejected"
    assert result.gate == "typed-confirmation"
    assert repo.name in result.message
    assert len(_audit(repo)) == 1


def test_unsupported_tier_is_rejected(repo: Path) -> None:
    result = _enable(repo, platform="copilot", tier="edits_only")

    assert result.outcome == "rejected"
    assert result.gate == "tier"
    assert len(_audit(repo)) == 1


def test_non_repository_is_rejected_and_audited_locally(tmp_path: Path) -> None:
    work = tmp_path / "plain-directory"
    work.mkdir()

    result = autonomy.enable("claude", "edits_only", 60, project_dir=work, now=NOW)

    assert result.outcome == "rejected"
    assert result.gate == "git-repository"
    assert len(_audit(work)) == 1
    assert not (work / ".claude" / "settings.local.json").exists()


def test_dirty_worktree_is_rejected(repo: Path) -> None:
    (repo / "uncommitted.txt").write_text("dirty\n", encoding="utf-8")

    result = _enable(repo)

    assert result.outcome == "rejected"
    assert result.gate == "clean-worktree"
    assert len(_audit(repo)) == 1


@pytest.mark.parametrize("branch", ["main", "master"])
def test_protected_branches_are_rejected(repo: Path, branch: str) -> None:
    _git(repo, "branch", "-M", branch)

    result = _enable(repo)

    assert result.outcome == "rejected"
    assert result.gate == "protected-branch"
    assert branch in result.message
    assert len(_audit(repo)) == 1


def test_declared_protected_branch_is_rejected(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NEXUS_PROTECTED_BRANCHES", "develop,release")
    _git(repo, "branch", "-M", "release")

    result = _enable(repo)

    assert result.gate == "protected-branch"
    assert len(_audit(repo)) == 1


def test_agents_md_declared_protected_branch_is_rejected(repo: Path) -> None:
    (repo / "AGENTS.md").write_text(
        "Never commit feature work directly to the protected `release` branch.\n",
        encoding="utf-8",
    )
    _commit(repo, "declare protected branch")
    _git(repo, "branch", "-M", "release")

    result = _enable(repo)

    assert result.gate == "protected-branch"
    assert "release" in result.message
    assert len(_audit(repo)) == 1


def test_global_descriptor_is_never_written(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    result = _enable(repo, platform="cursor", tier="full")

    assert result.outcome == "rejected"
    assert result.gate == "project-scope"
    assert "never writes global" in result.message
    assert not (fake_home / ".cursor" / "cli-config.json").exists()
    assert len(_audit(repo)) == 1


def test_unknown_platform_skips_with_note_and_no_config_write(repo: Path) -> None:
    result = _enable(repo, platform="not-a-platform")

    assert result.outcome == "skipped"
    assert result.gate == "unsupported-platform"
    assert "skipped" in result.message
    assert len(_audit(repo)) == 1


def test_atomic_replace_failure_leaves_original_config_intact(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = repo / ".claude" / "settings.local.json"
    config.parent.mkdir()
    original = '{"permissions":{"defaultMode":"default"}}\n'
    config.write_text(original, encoding="utf-8")
    _commit(repo)

    def interrupt(_temp: Path, _target: Path) -> None:
        raise OSError("simulated interrupt")

    monkeypatch.setattr(autonomy, "_atomic_replace", interrupt)
    result = _enable(repo)

    assert result.outcome == "error"
    assert result.gate == "atomic-write"
    assert config.read_text(encoding="utf-8") == original
    assert list(config.parent.glob(config.name + ".bak.*")), (
        "backup must exist before replacement"
    )
    assert not (repo / autonomy.STATE_RELATIVE_PATH).exists()
    assert not list(config.parent.glob(".*.tmp.*"))
    assert len(_audit(repo)) == 1


def test_unexpired_state_is_left_untouched(repo: Path) -> None:
    enabled = _enable(repo)
    config = Path(enabled.config_path)
    enabled_text = config.read_text(encoding="utf-8")

    results = autonomy.expire(project_dir=repo, now=NOW + timedelta(minutes=59))

    assert results == []
    assert config.read_text(encoding="utf-8") == enabled_text
    assert (repo / autonomy.STATE_RELATIVE_PATH).exists()
    assert len(_audit(repo)) == 1


def test_expired_state_reverts_config_and_clears_state(repo: Path) -> None:
    config = repo / ".qwen" / "settings.json"
    config.parent.mkdir()
    original = '{"tools":{"approvalMode":"default"}}\n'
    config.write_text(original, encoding="utf-8")
    _commit(repo)
    enabled = _enable(repo, platform="qwen", ttl=1)

    results = autonomy.expire(project_dir=repo, now=NOW + timedelta(minutes=2))

    assert [result.outcome for result in results] == ["expired-reverted"]
    assert config.read_text(encoding="utf-8") == original
    assert not Path(enabled.backup_path).exists()
    assert not (repo / autonomy.STATE_RELATIVE_PATH).exists()
    assert [record["operation"] for record in _audit(repo)] == ["enable", "expire"]


def test_missing_backup_fails_loudly_and_preserves_config_and_state(repo: Path) -> None:
    enabled = _enable(repo)
    config = Path(enabled.config_path)
    enabled_text = config.read_text(encoding="utf-8")
    state_text = (repo / autonomy.STATE_RELATIVE_PATH).read_text(encoding="utf-8")
    Path(enabled.backup_path).unlink()

    results = autonomy.expire(project_dir=repo, now=NOW + timedelta(minutes=61))

    assert len(results) == 1
    assert results[0].outcome == "error"
    assert results[0].gate == "missing-backup"
    assert "missing" in results[0].message.lower()
    assert config.read_text(encoding="utf-8") == enabled_text
    assert (repo / autonomy.STATE_RELATIVE_PATH).read_text(
        encoding="utf-8"
    ) == state_text
    assert len(_audit(repo)) == 2


def test_no_state_expiry_path_is_a_write_free_no_op(repo: Path) -> None:
    before = list(repo.rglob("*"))

    assert autonomy.expire(project_dir=repo, now=NOW) == []

    assert list(repo.rglob("*")) == before
    assert not (repo / autonomy.AUDIT_RELATIVE_PATH).exists()


def test_audit_is_valid_jsonl_and_excludes_user_process_and_environment_secrets(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "DO-NOT-LOG-super-secret-token"
    monkeypatch.setenv("NEXUS_TEST_SECRET", secret)
    result = autonomy.enable(
        "claude",
        "edits_only",
        60,
        project_dir=repo,
        now=NOW,
        user=secret,
        process=secret,
    )

    assert result.outcome == "enabled"
    raw = (repo / autonomy.AUDIT_RELATIVE_PATH).read_text(encoding="utf-8")
    assert secret not in raw
    records = [json.loads(line) for line in raw.splitlines()]
    assert len(records) == 1
    assert set(records[0]) == {
        "timestamp",
        "operation",
        "platform",
        "tier",
        "config_path",
        "backup_path",
        "expiry",
        "git_branch",
        "git_head",
        "outcome",
        "gate",
    }


@pytest.mark.skipif(
    os.name == "nt" and sys.version_info < (3, 11), reason="requires supported Python"
)
def test_concurrent_process_audit_appends_never_interleave(repo: Path) -> None:
    script = (
        "from pathlib import Path; from scripts.lib import autonomy; "
        "root=Path(r'''{root}'''); "
        "[autonomy._append_audit(root, {{'worker': {worker}, 'line': i}}) for i in range(15)]"
    )
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script.format(root=repo, worker=worker)],
            cwd=str(Path(__file__).resolve().parents[1]),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for worker in range(4)
    ]
    failures = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=30)
        if process.returncode != 0:
            failures.append(stdout + stderr)
    assert failures == []

    lines = (
        (repo / autonomy.AUDIT_RELATIVE_PATH).read_text(encoding="utf-8").splitlines()
    )
    assert len(lines) == 60
    records = [json.loads(line) for line in lines]
    assert {record["worker"] for record in records} == {0, 1, 2, 3}


def _write_guard_state(repo: Path, platforms: dict | None = None) -> None:
    state_path = repo / autonomy.STATE_RELATIVE_PATH
    state_path.parent.mkdir(exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "version": autonomy.STATE_VERSION,
                "platforms": platforms
                if platforms is not None
                else {
                    "claude": {
                        "tier": "edits",
                        "expiry": "2099-01-01T00:00:00Z",
                    }
                },
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("target", "pattern"),
    [
        (".claude/settings.local.json", ".claude/settings*.json"),
        (".claude/hooks/pre.sh", ".claude/hooks/*"),
        (".vscode/tasks.json", ".vscode/tasks.json"),
        (".vscode/launch.json", ".vscode/launch.json"),
        (".git/hooks/post-merge", ".git/hooks/*"),
        (".git/config", ".git/config"),
        (".cursor/rules.md", ".cursor/*"),
        (".venv/bin/python", ".venv/bin/*"),
        (".venv/Scripts/python.exe", ".venv/Scripts/*"),
        ("venv/bin/python", "venv/bin/*"),
        ("venv/Scripts/python.exe", "venv/Scripts/*"),
        ("pyvenv.cfg", "pyvenv.cfg"),
    ],
)
def test_guard_blocks_every_canonical_pattern_directly(
    repo: Path, target: str, pattern: str
) -> None:
    _write_guard_state(repo)

    decision = autonomy.guard_path(target, project_dir=repo)

    assert decision.blocked is True
    assert decision.matched_pattern == pattern
    assert target in decision.message
    assert decision.to_dict()["path"] == target


def test_guard_allows_missing_target_state_and_benign_paths(repo: Path) -> None:
    assert autonomy.guard_path(None, project_dir=repo).blocked is False
    assert (
        autonomy.guard_path(".claude/settings.json", project_dir=repo).blocked is False
    )

    _write_guard_state(repo, {})
    assert (
        autonomy.guard_path(".claude/settings.json", project_dir=repo).blocked is False
    )
    assert autonomy.guard_path("src/feature.py", project_dir=repo).blocked is False
    assert (
        autonomy.guard_path(repo.parent / "outside.py", project_dir=repo).blocked
        is False
    )


def test_guard_normalizes_traversal_and_fails_closed_on_invalid_state(
    repo: Path,
) -> None:
    state_path = repo / autonomy.STATE_RELATIVE_PATH
    state_path.parent.mkdir(exist_ok=True)
    state_path.write_text("not json", encoding="utf-8")

    decision = autonomy.guard_path("src/../.vscode/tasks.json", project_dir=repo)

    assert decision.blocked is True
    assert decision.path == ".vscode/tasks.json"
    assert "state is unreadable" in decision.message
    assert state_path.read_text(encoding="utf-8") == "not json"


def test_guard_cli_supports_explicit_path_and_stdin_payload(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_guard_state(repo)

    assert (
        autonomy.main(["guard", "--project", str(repo), "--path", ".git/config"]) == 2
    )
    assert ".git/config" in capsys.readouterr().err

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(json.dumps({"tool_input": {"path": "src/feature.py"}})),
    )
    assert autonomy.main(["guard", "--project", str(repo)]) == 0

    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert autonomy.main(["guard", "--project", str(repo)]) == 0
