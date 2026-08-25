"""Tests for scripts/check_memory_provenance.py (v3.19.2 Phase 3)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# v4.0.0: `ci.yml` calls scripts/ci/run.py rather than naming each guard in its
# own `run:` step, so CI reachability is resolved through the profile
# definitions. See tests/validators/_ci_reachability.py for why greping the
# YAML would be both wrong and dangerous to "fix".
from tests.validators._ci_reachability import assert_wired_into_ci

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_memory_provenance.py"
MAKEFILE = REPO_ROOT / "Makefile"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def run(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *extra],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_repo_templates_pass() -> None:
    proc = run("--root", str(REPO_ROOT))
    assert proc.returncode == 0, proc.stderr


def test_fixture_without_source_fails_as_expected(tmp_path: Path) -> None:
    path = tmp_path / "bad.md"
    path.write_text("just a note\n", encoding="utf-8")
    proc = run("--fixture", str(path), "--expect", "fail")
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_fixture_with_source_passes(tmp_path: Path) -> None:
    path = tmp_path / "good.md"
    path.write_text(
        "source: conversation:x\ntier: working\n---\nbody\n",
        encoding="utf-8",
    )
    proc = run("--fixture", str(path), "--expect", "pass")
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_makefile_and_ci_invoke_the_guard() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    assert "check_memory_provenance.py" in makefile
    assert_wired_into_ci("check_memory_provenance.py")
