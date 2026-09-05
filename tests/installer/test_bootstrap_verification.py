"""v4.7.0 Phase 6: fail-closed release verification and the --ref pin, both bootstraps.

Every behavioral case runs against BOTH implementations through one parametrized
fixture, so each assertion doubles as a parity assertion (the AGENTS.md sibling
rule). The bash leg skips on hosts where the full bash bootstrap is unverified
(see test_bootstrap.py); CI's ubuntu runner is authoritative for it.

The published artifact set is simulated with the NEXUS_HUB_RELEASE_BASE seam
pointing at a local directory holding `Nexus-Hub-<version>.tar.gz` and
`SHA256SUMS`, which is the same shape the release workflow attaches to a Release.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_SH = REPO_ROOT / "install.sh"
INSTALL_PS1 = REPO_ROOT / "install.ps1"
BASH = shutil.which("bash")
PWSH = shutil.which("pwsh") or shutil.which("powershell")
_RUN_KW = {
    "capture_output": True,
    "text": True,
    "encoding": "utf-8",
    "errors": "replace",
}

TAG = "v9.9.9"
ASSET = "Nexus-Hub-9.9.9.tar.gz"


def _skip_reason(impl: str) -> str | None:
    if impl == "sh":
        if not BASH:
            return "bash not available"
        if sys.platform == "win32":
            return "full bash bootstrap verified on CI/macOS; unverified on Windows"
    if impl == "ps" and not PWSH:
        return "PowerShell not available"
    return None


@pytest.fixture(params=["sh", "ps"])
def impl(request) -> str:
    reason = _skip_reason(request.param)
    if reason:
        pytest.skip(reason)
    return request.param


def _installer_stub(impl: str, marker: str) -> tuple[str, str]:
    if impl == "sh":
        return "installer.sh", f'#!/usr/bin/env bash\necho "{marker} args=$*"\n'
    return "installer.ps1", f'Write-Host "{marker} args=$args"\n'


def _make_tarball(dest: Path, impl: str, marker: str) -> Path:
    stub = dest.parent / (dest.stem + "-stub")
    (stub / "Nexus-Hub-9.9.9" / "scripts").mkdir(parents=True)
    name, body = _installer_stub(impl, marker)
    (stub / "Nexus-Hub-9.9.9" / "scripts" / name).write_text(body, encoding="utf-8")
    with tarfile.open(dest, "w:gz") as tf:
        tf.add(stub / "Nexus-Hub-9.9.9", arcname="Nexus-Hub-9.9.9")
    return dest


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _release_dir(
    root: Path,
    impl: str,
    marker: str = "RELEASE OK",
    *,
    sums: bool = True,
    corrupt: bool = False,
    tarball: bool = True,
) -> Path:
    release = root / "release"
    release.mkdir(parents=True, exist_ok=True)
    if tarball:
        archive = _make_tarball(release / ASSET, impl, marker)
        digest = "0" * 64 if corrupt else _sha256(archive)
        if sums:
            (release / "SHA256SUMS").write_text(
                f"{digest}  {ASSET}\n", encoding="utf-8"
            )
    return release


def _run(
    impl: str, env_extra: dict[str, str], *args: str
) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("NEXUS_HUB_")}
    env.update({"NEXUS_HUB_FORCE_STANDALONE": "1"})
    env.update(env_extra)
    if impl == "sh":
        cmd = [BASH, str(INSTALL_SH), *args]
    else:
        cmd = [
            PWSH,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(INSTALL_PS1),
            *args,
        ]
    return subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, check=False, **_RUN_KW)  # type: ignore[arg-type]


def test_genuine_release_artifact_installs_and_pins(impl: str, tmp_path: Path) -> None:
    release = _release_dir(tmp_path, impl)
    src = tmp_path / "home" / ".nexus-hub" / "src"
    proc = _run(
        impl,
        {"NEXUS_HUB_RELEASE_BASE": str(release), "NEXUS_HUB_SRC": str(src)},
        "--ref",
        TAG,
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out
    assert "checksum OK" in out
    assert "RELEASE OK" in proc.stdout
    assert "--ref" not in proc.stdout and TAG not in proc.stdout.split("args=")[-1], (
        "the ref flag must not reach the core installer"
    )
    assert (src.parent / "PINNED_REF").read_text(encoding="utf-8").strip() == TAG


def test_corrupted_release_artifact_aborts(impl: str, tmp_path: Path) -> None:
    release = _release_dir(tmp_path, impl, marker="SHOULD NOT RUN", corrupt=True)
    src = tmp_path / "home" / ".nexus-hub" / "src"
    proc = _run(
        impl,
        {
            "NEXUS_HUB_RELEASE_BASE": str(release),
            "NEXUS_HUB_SRC": str(src),
            "NEXUS_HUB_REF": TAG,
        },
    )
    out = (proc.stdout + proc.stderr).lower()
    assert proc.returncode != 0
    assert "checksum mismatch" in out and "expected" in out and "got" in out
    assert "SHOULD NOT RUN" not in proc.stdout
    assert not (src.parent / "PINNED_REF").exists()


def test_missing_checksum_file_aborts_and_names_it(impl: str, tmp_path: Path) -> None:
    release = _release_dir(tmp_path, impl, marker="SHOULD NOT RUN", sums=False)
    src = tmp_path / "home" / ".nexus-hub" / "src"
    proc = _run(
        impl,
        {
            "NEXUS_HUB_RELEASE_BASE": str(release),
            "NEXUS_HUB_SRC": str(src),
            "NEXUS_HUB_REF": TAG,
        },
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "SHA256SUMS" in out and "unverified" in out.lower()
    assert "SHOULD NOT RUN" not in proc.stdout


def test_unresolvable_release_ref_aborts_naming_the_ref(
    impl: str, tmp_path: Path
) -> None:
    release = _release_dir(tmp_path, impl, tarball=False)
    src = tmp_path / "home" / ".nexus-hub" / "src"
    proc = _run(
        impl,
        {
            "NEXUS_HUB_RELEASE_BASE": str(release),
            "NEXUS_HUB_SRC": str(src),
            "NEXUS_HUB_REF": TAG,
        },
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert TAG in out and "releases" in out.lower()
    assert not src.exists()


def test_release_dir_path_with_space_and_backslash(impl: str, tmp_path: Path) -> None:
    # The space applies everywhere. A LITERAL backslash in a directory name is a
    # bash-on-POSIX case only: Windows treats it as a separator, and PowerShell 7
    # on Linux normalizes it to one too (the ubuntu `ps` leg of PR #167 proved
    # that by looking up `back/slash`), so neither of those hosts can hold the
    # directory this fixture would create.
    literal_backslash = impl == "sh" and sys.platform != "win32"
    odd = tmp_path / "odd dir" / ("back\\slash" if literal_backslash else "backslash")
    release = _release_dir(odd, impl)
    src = tmp_path / "home" / ".nexus-hub" / "src"
    proc = _run(
        impl,
        {
            "NEXUS_HUB_RELEASE_BASE": str(release),
            "NEXUS_HUB_SRC": str(src),
            "NEXUS_HUB_REF": TAG,
        },
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out
    assert "checksum OK" in out


def test_branch_install_keeps_the_warning_path_and_clears_the_pin(
    impl: str, tmp_path: Path
) -> None:
    tarball = _make_tarball(tmp_path / "branch.tar.gz", impl, "BRANCH OK")
    src = tmp_path / "home" / ".nexus-hub" / "src"
    (src.parent).mkdir(parents=True)
    (src.parent / "PINNED_REF").write_text(TAG, encoding="utf-8")
    proc = _run(
        impl,
        {
            "NEXUS_HUB_TARBALL": str(tarball),
            "NEXUS_HUB_SRC": str(src),
            "NEXUS_HUB_REF": "main",
        },
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out
    assert "unverified" in out.lower() and "BRANCH OK" in proc.stdout
    assert not (src.parent / "PINNED_REF").exists()


def test_ref_flag_without_a_value_fails_clearly(impl: str, tmp_path: Path) -> None:
    proc = _run(impl, {"NEXUS_HUB_SRC": str(tmp_path / "src")}, "--ref")
    assert proc.returncode != 0
    assert "needs a value" in (proc.stdout + proc.stderr)
