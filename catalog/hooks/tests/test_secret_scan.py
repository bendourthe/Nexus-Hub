"""secret-scan.sh / secret-scan.ps1 parity, including the jq-absent path (AR-02).

Until v4.13.6 the bash hook exited 0 whenever `jq` was missing, so on such a
host it allowed every write unscanned. It now falls back to Python 3 and fails
closed when it has neither parser. These tests force each parser situation by
running the .sh with a PATH that holds only wrappers for the tools it needs,
so a host that has jq still exercises the no-jq path. Every behavioral case is
parametrized over the .sh (with and without jq) and the .ps1, so each one is
also an exit-code parity assertion.

The fixture secrets are assembled from parts so this file does not itself trip
the secret scan that guards writes in this repository.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[1]
_SH = _HOOKS_DIR / "secret-scan.sh"
_PS1 = _HOOKS_DIR / "secret-scan.ps1"

_ALLOW, _BLOCK = 0, 2
_BASE_TOOLS = ("cat", "grep", "basename", "head")
_PYTHONS = ("python3", "python")

_AWS = "AK" + "IA" + "1234567890ABCDEF"
_KEY_HEADER = "-----BEGIN " + "OPENSSH PRIVATE" + " KEY-----"
_GH_TOKEN = "gh" + "p_" + "a" * 36
_PW = "pass" + "word"

# Build one wrapper per tool the hook calls, resolved by the bash under test,
# so the wrapper directory can stand in for PATH on POSIX and on Git Bash.
_MAKE_WRAPPERS = r"""
dir="$1"; shift
mkdir -p "$dir"
for tool in "$@"; do
  real=$(command -v "$tool") || continue
  printf '#!/bin/sh\nexec "%s" "$@"\n' "$real" > "$dir/$tool"
  chmod +x "$dir/$tool"
done
"""


def _payload(content: str, *, key: str = "content", path: str = "cfg.py") -> str:
    return json.dumps({"tool_input": {"file_path": path, key: content}})


def _wrapper_path(bash_bin: str, directory: Path, tools: tuple[str, ...]) -> str:
    subprocess.run(
        [bash_bin, "-c", _MAKE_WRAPPERS, "_", directory.as_posix(), *tools],
        check=True, capture_output=True, timeout=60,
    )
    return str(directory)


def _has_python(bash_bin: str) -> bool:
    probe = "for p in python3 python; do command -v $p >/dev/null && $p -c 'import json' && exit 0; done; exit 1"
    return subprocess.run([bash_bin, "-c", probe], capture_output=True, timeout=60).returncode == 0


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    return {**os.environ, "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}


@pytest.fixture(params=["sh-jq", "sh-python", "ps1"])
def run(request, tmp_path: Path, env: dict[str, str]):
    """Run one implementation on a payload and return its CompletedProcess."""
    variant = request.param
    if variant == "ps1":
        argv = [request.getfixturevalue("powershell_bin"), "-NoProfile", "-File", str(_PS1)]
        run_env = env
    else:
        bash_bin = request.getfixturevalue("bash_bin")
        argv = [bash_bin, str(_SH)]
        if variant == "sh-jq":
            if shutil.which("jq") is None:
                pytest.skip("jq is not installed; the sh-python variant covers this host")
            run_env = env
        else:
            if not _has_python(bash_bin):
                pytest.skip("no Python 3 reachable from bash")
            wrappers = _wrapper_path(bash_bin, tmp_path / "bin", _BASE_TOOLS + _PYTHONS)
            run_env = {**env, "PATH": wrappers}

    def _run(payload: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            argv, input=payload, text=True, encoding="utf-8", capture_output=True,
            env=run_env, timeout=180,
        )

    return _run


@pytest.mark.parametrize(
    "content",
    [
        f"AWS_KEY = '{_AWS}'\n",
        f"line one\n{_KEY_HEADER}\nabc\n",
        f'value = "{_GH_TOKEN}"\n',
        f'{_PW} = "correcthorsebattery"\n',
    ],
    ids=["aws-key", "private-key-on-a-later-line", "github-token", "password-assignment"],
)
def test_a_secret_is_blocked(run, content: str) -> None:
    proc = run(_payload(content))
    assert proc.returncode == _BLOCK, proc.stderr


def test_a_secret_in_an_edit_new_string_is_blocked(run) -> None:
    proc = run(_payload(f"x = '{_AWS}'", key="new_string"))
    assert proc.returncode == _BLOCK, proc.stderr


@pytest.mark.parametrize(
    "content",
    [
        "print('hello')\n",
        f'{_PW} = "your-{_PW}-here"\n',
        "api_key = os.environ['API_KEY']\n",
        "café = 'naïve text with no secret'\n",
    ],
    ids=["plain-code", "placeholder", "env-reference", "non-ascii"],
)
def test_clean_content_is_allowed(run, content: str) -> None:
    proc = run(_payload(content))
    assert proc.returncode == _ALLOW, proc.stderr


@pytest.mark.parametrize("payload", ["not json", "{}", '{"tool_input": "text"}'],
                         ids=["malformed", "no-tool-input", "non-object-tool-input"])
def test_a_payload_without_content_is_allowed(run, payload: str) -> None:
    assert run(payload).returncode == _ALLOW


def test_the_report_names_the_category_not_the_secret(run) -> None:
    proc = run(_payload(f"AWS_KEY = '{_AWS}'\n"))
    assert proc.returncode == _BLOCK
    assert "AWS Access Key ID" in proc.stderr
    assert _AWS not in proc.stdout + proc.stderr


def test_the_sh_fails_closed_with_neither_jq_nor_python(
    bash_bin: str, tmp_path: Path, env: dict[str, str]
) -> None:
    """With no parser at all the bash hook cannot scan, so it must block."""
    wrappers = _wrapper_path(bash_bin, tmp_path / "bin", _BASE_TOOLS)
    proc = subprocess.run(
        [bash_bin, str(_SH)], input=_payload("print('hello')\n"), text=True,
        capture_output=True, env={**env, "PATH": wrappers}, timeout=180,
    )
    assert proc.returncode == _BLOCK
    assert "cannot be scanned" in proc.stderr


def test_a_secret_at_the_start_of_a_large_write_is_blocked(run) -> None:
    """ADV-1: under pipefail, `echo | grep -q` turned an early match into "no match"."""
    filler = "".join(f"line {i} of harmless filler text\n" for i in range(20000))
    proc = run(_payload(f"AWS_KEY = '{_AWS}'\n" + filler))
    assert proc.returncode == _BLOCK, proc.stderr


def test_a_python2_named_python3_is_not_a_parser(
    bash_bin: str, tmp_path: Path, env: dict[str, str]
) -> None:
    """ADV-8: an interpreter that imports json but is not Python 3 must not be trusted.

    The stand-in accepts `import json` (as Python 2 does) and fails anything that
    asks for Python 3, then emits nothing, which the old probe mistook for a clean
    payload and allowed.
    """
    wrappers = Path(_wrapper_path(bash_bin, tmp_path / "bin", _BASE_TOOLS))
    fake = wrappers / "python3"
    fake.write_text(
        '#!/bin/sh\ncase "$2" in *version_info*) exit 1 ;; esac\nexit 0\n', encoding="utf-8"
    )
    subprocess.run([bash_bin, "-c", f'chmod +x "{fake.as_posix()}"'], check=True, timeout=60)
    proc = subprocess.run(
        [bash_bin, str(_SH)], input=_payload(f"AWS_KEY = '{_AWS}'\n"), text=True,
        capture_output=True, env={**env, "PATH": str(wrappers)}, timeout=180,
    )
    assert proc.returncode == _BLOCK
    assert "cannot be scanned" in proc.stderr
