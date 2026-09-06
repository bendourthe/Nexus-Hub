"""Tests for scripts/check_no_outbound.py (v3.19.2 Phase 1)."""

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
SCRIPT = REPO_ROOT / "scripts" / "check_no_outbound.py"
MAKEFILE = REPO_ROOT / "Makefile"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def run(*extra: str, root: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPT)]
    if root is not None:
        cmd.extend(["--root", str(root)])
    cmd.extend(extra)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)


def test_real_compressor_tree_is_clean() -> None:
    proc = run()
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_injected_requests_import_is_flagged(tmp_path: Path) -> None:
    pkg = tmp_path / "src" / "nexus_context_compressor"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "leaky.py").write_text("import requests\n", encoding="utf-8")

    proc = run(root=tmp_path)
    assert proc.returncode == 1
    assert "leaky.py" in proc.stderr
    assert "requests" in proc.stderr


def test_urllib_request_import_from_is_flagged(tmp_path: Path) -> None:
    (tmp_path / "client.py").write_text(
        "from urllib.request import urlopen\n", encoding="utf-8"
    )
    proc = run(root=tmp_path)
    assert proc.returncode == 1
    assert "urllib.request" in proc.stderr


def test_urllib_parse_is_allowed(tmp_path: Path) -> None:
    (tmp_path / "ok.py").write_text("from urllib.parse import urlparse\n", encoding="utf-8")
    proc = run(root=tmp_path)
    assert proc.returncode == 0, proc.stderr


def test_subprocess_curl_is_flagged(tmp_path: Path) -> None:
    (tmp_path / "fetch.py").write_text(
        "import subprocess\nsubprocess.run(['curl', 'https://example.invalid'])\n",
        encoding="utf-8",
    )
    proc = run(root=tmp_path)
    assert proc.returncode == 1
    assert "curl" in proc.stderr


def test_commented_import_is_ignored(tmp_path: Path) -> None:
    (tmp_path / "ok.py").write_text("# import requests\nvalue = 1\n", encoding="utf-8")
    proc = run(root=tmp_path)
    assert proc.returncode == 0, proc.stderr


def test_tests_directory_is_not_scanned(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_net.py").write_text("import socket\n", encoding="utf-8")
    (tmp_path / "pkg.py").write_text("x = 1\n", encoding="utf-8")
    proc = run(root=tmp_path)
    assert proc.returncode == 0, proc.stderr


def test_missing_root_fails(tmp_path: Path) -> None:
    proc = run(root=tmp_path / "no-such")
    assert proc.returncode == 1
    assert "MISS" in proc.stderr


def test_makefile_and_ci_invoke_the_guard() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    assert "scripts/check_no_outbound.py" in makefile
    assert_wired_into_ci("check_no_outbound.py")
