"""A failed optional usage-monitor build must not abort the Bash installer."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("failure", ["out_cleanup", "cleanup", "package", "no_vsix"])
def test_optional_extension_build_failure_continues_install(tmp_path: Path, failure: str) -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is unavailable")

    source = (REPO_ROOT / "scripts" / "installer.sh").read_text(encoding="utf-8")
    function = source.split("build_and_install_one_extension() {", 1)[1].split(
        "# --- Template & Script Installation ---", 1
    )[0]
    extension = tmp_path / "extension"
    (extension / "out").mkdir(parents=True)
    (extension / "node_modules").mkdir(parents=True)
    shell = (
        """set -euo pipefail
        DARK_YELLOW='' RESET='' RED='' GREEN='' GRAY='' YELLOW=''
        write_item() { printf '%s\\n' "$1"; }
        rm() {
            if [[ "$FAIL_STEP" == out_cleanup && "$*" == */out* ]]; then return 12; fi
            if [[ "$FAIL_STEP" == cleanup && "$*" == *node_modules* ]]; then return 13; fi
            command rm "$@"
        }
        npm() { return 0; }
        npx() { if [[ "$FAIL_STEP" == package ]]; then return 23; fi; return 0; }
        build_and_install_one_extension() {
        """
        + function
        + """
        build_and_install_one_extension "$PWD/extension" test.optional Optional '--%' '' Editor
        build_and_install_one_extension missing test.next Next '--%' '' Editor
        printf 'CONTINUED\\n'
        """
    )
    env = os.environ.copy()
    env["FAIL_STEP"] = failure
    result = subprocess.run(
        [bash, "-c", shell], cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Extension source not found at: missing" in result.stdout
    assert "CONTINUED" in result.stdout
    assert "failed" in result.stdout.lower()
