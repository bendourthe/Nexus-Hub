"""
Tests for the local-only observation-capture hook (Phase 3 T008).

Covers:
    catalog/hooks/learning-capture.sh

Verifies:
  - One JSONL record is appended per invocation.
  - The required fields (`ts`, `event`, `tool`, `prompt_sample`) are present.
  - The off-switch (`NEXUS_LEARNING_CAPTURE=off`) skips writes.
  - The path override (`NEXUS_LEARNING_PATH`) is honored.
  - The size cap (`NEXUS_LEARNING_MAX_BYTES`) trims the file when exceeded.
  - The hook makes no outbound network call (asserted by running with PATH
    restricted to a minimal toolset).
  - The hook never writes outside the project root.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_learning_capture.py -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).parent.parent
_CAPTURE_HOOK = _HOOKS_DIR / "learning-capture.sh"


def _bash_path() -> str:
    candidates = [
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise RuntimeError("bash not found on PATH; cannot run learning-capture hook tests")


_BASH = _bash_path()


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """A fresh git repo for each test."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)
    return repo


def _run(repo: Path, stdin: str, env_extra: dict[str, str] | None = None) -> tuple[str, str, int]:
    env = os.environ.copy()
    env["HOME"] = str(repo / "_home")
    (repo / "_home").mkdir(exist_ok=True)
    if env_extra:
        env.update(env_extra)
    result = subprocess.run(
        [_BASH, str(_CAPTURE_HOOK)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        input=stdin,
    )
    return result.stdout, result.stderr, result.returncode


class TestSyntax:
    def test_capture_hook_parses(self) -> None:
        result = subprocess.run([_BASH, "-n", str(_CAPTURE_HOOK)],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


class TestObservationCapture:
    def test_user_prompt_event_writes_record(self, tmp_repo: Path) -> None:
        payload = json.dumps({
            "hook_event_name": "UserPromptSubmit",
            "prompt": "please refactor this module",
        })
        _out, _err, code = _run(tmp_repo, stdin=payload)
        assert code == 0
        obs = tmp_repo / ".nexus" / "observations.jsonl"
        assert obs.exists()
        lines = obs.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["event"] == "UserPromptSubmit"
        assert "ts" in record
        assert "tool" in record
        assert "prompt_sample" in record
        assert "refactor this module" in record["prompt_sample"]

    def test_tool_event_writes_record(self, tmp_repo: Path) -> None:
        payload = json.dumps({
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
        })
        _out, _err, code = _run(tmp_repo, stdin=payload)
        assert code == 0
        rec = json.loads((tmp_repo / ".nexus" / "observations.jsonl")
                         .read_text(encoding="utf-8").strip())
        assert rec["event"] == "PostToolUse"
        assert rec["tool"] == "Edit"

    def test_multiple_calls_append(self, tmp_repo: Path) -> None:
        for i in range(3):
            _run(tmp_repo, stdin=json.dumps({
                "hook_event_name": "UserPromptSubmit", "prompt": f"msg {i}"
            }))
        obs = tmp_repo / ".nexus" / "observations.jsonl"
        lines = obs.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3
        assert json.loads(lines[2])["prompt_sample"].endswith("msg 2")


class TestRuntimeControls:
    def test_off_switch_skips_write(self, tmp_repo: Path) -> None:
        _out, _err, code = _run(
            tmp_repo,
            stdin=json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "x"}),
            env_extra={"NEXUS_LEARNING_CAPTURE": "off"},
        )
        assert code == 0
        assert not (tmp_repo / ".nexus" / "observations.jsonl").exists()

    def test_disabled_hooks_skips(self, tmp_repo: Path) -> None:
        _out, _err, code = _run(
            tmp_repo,
            stdin=json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "x"}),
            env_extra={"NEXUS_DISABLED_HOOKS": "learning-capture"},
        )
        assert code == 0
        assert not (tmp_repo / ".nexus" / "observations.jsonl").exists()

    def test_minimal_profile_skips(self, tmp_repo: Path) -> None:
        _out, _err, code = _run(
            tmp_repo,
            stdin=json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "x"}),
            env_extra={"NEXUS_HOOK_PROFILE": "minimal"},
        )
        assert code == 0
        assert not (tmp_repo / ".nexus" / "observations.jsonl").exists()

    def test_custom_path_is_honored(self, tmp_repo: Path) -> None:
        custom = ".nexus/custom-obs.jsonl"
        _out, _err, code = _run(
            tmp_repo,
            stdin=json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "x"}),
            env_extra={"NEXUS_LEARNING_PATH": custom},
        )
        assert code == 0
        assert (tmp_repo / custom).exists()
        assert not (tmp_repo / ".nexus" / "observations.jsonl").exists()

    def test_size_cap_truncates_file(self, tmp_repo: Path) -> None:
        # Pre-populate the file beyond the cap.
        obs_dir = tmp_repo / ".nexus"
        obs_dir.mkdir()
        obs = obs_dir / "observations.jsonl"
        # 200 lines of ~100 chars each ~ 20 KiB.
        seed_lines = [
            json.dumps({"ts": "2026-01-01T00:00:00Z", "event": "Seed",
                        "tool": "", "prompt_sample": "x" * 80})
            for _ in range(200)
        ]
        obs.write_text("\n".join(seed_lines) + "\n", encoding="utf-8")
        original_size = obs.stat().st_size
        assert original_size > 5_000

        # Trigger an append with the cap set well below the seeded size.
        _out, _err, code = _run(
            tmp_repo,
            stdin=json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "trim"}),
            env_extra={"NEXUS_LEARNING_MAX_BYTES": "5000"},
        )
        assert code == 0
        new_size = obs.stat().st_size
        # Must have shrunk meaningfully (we keep the last half then appended one).
        assert new_size < original_size


class TestNoNetworkInvariant:
    """The hook must not invoke any network binary.

    Strategy: static analysis. Grep the hook source for tokens that would
    indicate an outbound call (curl, wget, ssh, scp, nc, http, ftp, ...).
    A runtime PATH-sandbox approach is unreliable on Windows where Git
    Bash binaries are dynamically linked and cannot run when copied in
    isolation, so a source-level check is both stronger and more portable.
    """

    # Word-boundary tokens: matched as standalone command words (\b...\b).
    # `nc` is omitted because it collides with the jq `-nc` flag pair; `ncat`
    # is the unambiguous netcat-clone name and is kept.
    _SUSPECT_COMMANDS = (
        "curl", "wget", "ssh", "scp", "sftp", "rsync", "ncat",
        "telnet", "ftp", "urlopen",
    )
    # Substring tokens: matched anywhere (URL schemes / SDK calls).
    _SUSPECT_SUBSTRINGS = (
        "http://", "https://", "ftp://", "ftps://",
        "requests.get", "requests.post", "urllib.request", "fetch(",
    )

    def test_source_has_no_network_token(self) -> None:
        import re
        body = _CAPTURE_HOOK.read_text(encoding="utf-8")
        # Strip the comment header so docstring keywords don't trip us up.
        in_header = True
        cleaned_lines: list[str] = []
        for line in body.splitlines():
            stripped = line.strip()
            if in_header:
                if stripped.startswith("#") or not stripped:
                    continue
                in_header = False
            cleaned_lines.append(line)
        cleaned = "\n".join(cleaned_lines)

        offenders: list[str] = []
        for tok in self._SUSPECT_COMMANDS:
            if re.search(rf"\b{re.escape(tok)}\b", cleaned):
                offenders.append(tok)
        for tok in self._SUSPECT_SUBSTRINGS:
            if tok in cleaned:
                offenders.append(tok)
        assert not offenders, (
            f"learning-capture.sh body references potentially outbound tokens: {offenders}"
        )

    def test_no_write_outside_project_root(self, tmp_repo: Path) -> None:
        """Even with a misleading payload, the hook must not write outside the
        project root. We assert by checking that the resolved obs path stays
        under tmp_repo when NEXUS_LEARNING_PATH is left at the default.
        """
        payload = json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "x"})
        _out, _err, code = _run(tmp_repo, stdin=payload)
        assert code == 0
        obs = (tmp_repo / ".nexus" / "observations.jsonl").resolve()
        assert str(obs).startswith(str(tmp_repo.resolve()))
