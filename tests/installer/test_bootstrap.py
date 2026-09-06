"""Tests for the dual-mode self-fetching bootstrap (v3.7.0 Phase 1).

The repo-root `install.sh` / `install.ps1` are dual-mode entry points:

  * In-repo    - run from a checkout; delegate to `scripts/installer.{sh,ps1}`.
  * Standalone - piped from the network (`curl|bash` / `irm|iex`); precheck the
                 required tools, download the catalog tarball from the project's
                 own GitHub, extract it to ~/.nexus-hub/src, and run the
                 extracted core installer.

These tests cover:
  * the static surface (both entry points declare the precheck, the dual-mode
    detection, the GitHub fetch URL, and the documented testing env vars);
  * the precheck-only success path;
  * the missing-tool failure path (empty PATH -> non-zero exit + clear message);
  * the standalone extract + hand-off against a local tarball (with arg
    passthrough), asserting the extracted source is populated and the core
    installer is invoked;
  * in-repo detection (a sibling `scripts/installer.*` is delegated to).

The bash functional tests skip cleanly when bash is absent, and on Windows (see
the `bash_functional` marker below for the specific reason); CI (ubuntu) is
authoritative for the bash path. The PowerShell functional tests skip where no
PowerShell is present.

Note on WN-v36-1, which this file used to cite as "bash cannot always be fully run
on the Windows dev host": that framing was DISPROVEN in v3.15.6 Phase 4. The cause
was PATH shadowing (the WSL launcher stub preceding Git Bash), not host
incapability, and the hook and repo test suites now pass on Windows with no PATH
assistance. The Windows skip HERE is retained for a narrower and still-valid
reason, spelled out at the marker: this file drives the full bootstrap, not a hook
script, and that path is unverified on Windows.
"""

from __future__ import annotations

import hashlib
import io
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
WINDOWS = sys.platform == "win32"

# On Windows, `bash` commonly resolves to the WSL launcher stub, which translates
# the CWD and does not forward Windows env vars across the boundary, so the env-var
# seams the bootstrap relies on are not honored. (Git Bash, being a native Windows
# process, does forward them, and v3.15.6 Phase 4 added a conftest PATH repair that
# prefers it. But that only makes bash RESOLVABLE: whether the full download,
# extract, and install bootstrap behaves correctly on Windows is a separate
# question this suite has never verified.) So the skip is retained deliberately,
# on the narrow ground that the path is unverified rather than the disproven
# claim that Windows cannot run bash. The bash path is verified on CI (ubuntu)
# and a manual Mac smoke test.
bash_functional = pytest.mark.skipif(
    not BASH or WINDOWS,
    reason="full bash bootstrap verified on CI/macOS; unverified on Windows",
)

# Capture subprocess output as UTF-8 with replacement so ANSI/banner bytes never
# trip the Windows cp1252 default decoder.
_RUN_KW = {
    "capture_output": True,
    "text": True,
    "encoding": "utf-8",
    "errors": "replace",
}


def _run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=False, **_RUN_KW, **kwargs)  # type: ignore[arg-type]

# Env-var names the bootstrap documents as internal testing seams.
BOOTSTRAP_ENV_VARS = [
    "NEXUS_HUB_REF",
    "NEXUS_HUB_REPO",
    "NEXUS_HUB_TARBALL",
    "NEXUS_HUB_SRC",
    "NEXUS_HUB_FORCE_STANDALONE",
    "NEXUS_HUB_PRECHECK_ONLY",
    "NEXUS_HUB_EXPECTED_SHA256",
    "NEXUS_HUB_CHECKSUMS",
    "NEXUS_HUB_SKIP_CHECKSUM",
]


def _make_stub_tarball(dest_dir: Path, installer_name: str, installer_body: str) -> Path:
    """Build a GitHub-shaped tarball: a single top dir `Nexus-Hub-main/` holding
    `scripts/<installer_name>` with the given body. Returns the tarball path."""
    stub = dest_dir / "stub"
    (stub / "Nexus-Hub-main" / "scripts").mkdir(parents=True)
    (stub / "Nexus-Hub-main" / "scripts" / installer_name).write_text(
        installer_body, encoding="utf-8"
    )
    tarball = dest_dir / "catalog.tar.gz"
    with tarfile.open(tarball, "w:gz") as tf:
        tf.add(stub / "Nexus-Hub-main", arcname="Nexus-Hub-main")
    return tarball


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_traversal_tarball(dest_dir: Path) -> Path:
    """Archive whose member is ``../evil`` (CWE-22). Must be refused."""
    tarball = dest_dir / "evil.tar.gz"
    payload = b"pwned"
    info = tarfile.TarInfo(name="../evil")
    info.size = len(payload)
    with tarfile.open(tarball, "w:gz") as tf:
        tf.addfile(info, io.BytesIO(payload))
    return tarball


# --- Static surface ---------------------------------------------------------

def test_install_sh_is_dual_mode() -> None:
    body = INSTALL_SH.read_text(encoding="utf-8")
    assert "precheck_dependencies" in body, "install.sh must precheck tools"
    assert "run_standalone" in body and "run_in_repo" in body, "install.sh must be dual-mode"
    assert "archive/refs/heads/" in body, "install.sh must fetch the GitHub tarball"
    assert "scripts/installer.sh" in body, "install.sh must hand off to the core installer"
    assert "curl" in body and "wget" in body, "install.sh must prefer curl, fall back to wget"
    for var in BOOTSTRAP_ENV_VARS:
        assert var in body, f"install.sh must document the {var} seam"


def test_install_ps1_is_dual_mode() -> None:
    assert INSTALL_PS1.exists(), "install.ps1 (the irm|iex bootstrap) must exist"
    body = INSTALL_PS1.read_text(encoding="utf-8")
    assert "Invoke-DependencyPrecheck" in body, "install.ps1 must precheck tools"
    assert "Invoke-Standalone" in body and "Invoke-InRepo" in body, "install.ps1 must be dual-mode"
    assert "archive/refs/heads/" in body, "install.ps1 must fetch the GitHub archive"
    assert "scripts\\installer.ps1" in body, "install.ps1 must hand off to the core installer"
    assert "Invoke-WebRequest" in body, "install.ps1 downloads via Invoke-WebRequest"
    for var in BOOTSTRAP_ENV_VARS:
        assert var in body, f"install.ps1 must document the {var} seam"


def test_no_new_outbound_host() -> None:
    """The only outbound host the bootstrap may name is the project's own GitHub."""
    for entry in (INSTALL_SH, INSTALL_PS1):
        body = entry.read_text(encoding="utf-8")
        for line in body.splitlines():
            if "https://" in line and "://" in line:
                # Allow comments/URLs only to github.com or raw.githubusercontent.com.
                lowered = line.lower()
                if "github.com" in lowered or "githubusercontent.com" in lowered:
                    continue
                # python.org / aka.ms / powershell appear only as user-facing
                # "install Python/PowerShell from ..." hints, never as a fetch.
                if "python.org" in lowered or "aka.ms" in lowered:
                    continue
                pytest.fail(f"unexpected outbound URL in {entry.name}: {line.strip()}")


# --- bash functional --------------------------------------------------------

@bash_functional
def test_bash_precheck_only_succeeds() -> None:
    env = {**os.environ, "NEXUS_HUB_FORCE_STANDALONE": "1", "NEXUS_HUB_PRECHECK_ONLY": "1"}
    proc = _run([BASH, "install.sh"], cwd=str(REPO_ROOT), env=env)
    assert proc.returncode == 0, proc.stderr
    assert "precheck" in (proc.stdout + proc.stderr).lower()


@bash_functional
def test_bash_missing_downloader_fails_clearly() -> None:
    # Empty PATH -> the builtins-only precheck finds no curl/wget and bails.
    env = {**os.environ, "PATH": "", "NEXUS_HUB_FORCE_STANDALONE": "1"}
    proc = _run([BASH, "install.sh"], cwd=str(REPO_ROOT), env=env)
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    combined = (proc.stdout + proc.stderr).lower()
    assert "curl" in combined and "wget" in combined


@bash_functional
def test_bash_standalone_extracts_and_hands_off(tmp_path: Path) -> None:
    tarball = _make_stub_tarball(
        tmp_path, "installer.sh",
        '#!/usr/bin/env bash\necho "STUB BASH INSTALLER args=$*"\n',
    )
    src = tmp_path / "out" / "src"
    env = {
        **os.environ,
        "NEXUS_HUB_FORCE_STANDALONE": "1",
        "NEXUS_HUB_TARBALL": str(tarball),
        "NEXUS_HUB_SRC": str(src),
    }
    proc = _run(
        [BASH, "install.sh", "alpha", "beta"], cwd=str(REPO_ROOT), env=env,
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "STUB BASH INSTALLER args=alpha beta" in proc.stdout
    assert (src / "scripts" / "installer.sh").is_file(), "extracted source must be populated"


@bash_functional
def test_bash_in_repo_delegates(tmp_path: Path) -> None:
    # Copy install.sh next to a stub scripts/installer.sh -> in-repo detection
    # must delegate to the sibling without any standalone fetch.
    shutil.copy(INSTALL_SH, tmp_path / "install.sh")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "installer.sh").write_text(
        '#!/usr/bin/env bash\necho "IN-REPO STUB args=$*"\n', encoding="utf-8"
    )
    proc = _run([BASH, "install.sh", "foo"], cwd=str(tmp_path))
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "IN-REPO STUB args=foo" in proc.stdout


# --- PowerShell functional --------------------------------------------------

@pytest.mark.skipif(not PWSH, reason="PowerShell not available")
def test_ps_precheck_only_succeeds() -> None:
    env = {**os.environ, "NEXUS_HUB_FORCE_STANDALONE": "1", "NEXUS_HUB_PRECHECK_ONLY": "1"}
    proc = _run(
        [PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(INSTALL_PS1)],
        cwd=str(REPO_ROOT), env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert "precheck" in (proc.stdout + proc.stderr).lower()


@pytest.mark.skipif(not PWSH, reason="PowerShell not available")
def test_ps_standalone_extracts_and_hands_off(tmp_path: Path) -> None:
    tarball = _make_stub_tarball(
        tmp_path, "installer.ps1",
        'param([Parameter(ValueFromRemainingArguments=$true)]$a)\n'
        'Write-Host "STUB PS INSTALLER args=$a"\n',
    )
    src = tmp_path / "out" / "src"
    env = {
        **os.environ,
        "NEXUS_HUB_FORCE_STANDALONE": "1",
        "NEXUS_HUB_TARBALL": str(tarball),
        "NEXUS_HUB_SRC": str(src),
    }
    proc = _run(
        [PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(INSTALL_PS1), "alpha"],
        cwd=str(REPO_ROOT), env=env,
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "STUB PS INSTALLER args=alpha" in proc.stdout
    assert (src / "scripts" / "installer.ps1").is_file(), "extracted source must be populated"


def test_install_scripts_declare_integrity_helpers() -> None:
    sh = INSTALL_SH.read_text(encoding="utf-8")
    ps = INSTALL_PS1.read_text(encoding="utf-8")
    for body in (sh, ps):
        assert "NEXUS_HUB_EXPECTED_SHA256" in body
        assert "NEXUS_HUB_SKIP_CHECKSUM" in body
        assert "CWE-22" in body
    assert "assert_archive_safe" in sh
    assert "verify_archive_checksum" in sh
    assert "Assert-ArchiveSafe" in ps
    assert "Assert-ArchiveChecksum" in ps


@bash_functional
def test_bash_checksum_match_extracts(tmp_path: Path) -> None:
    tarball = _make_stub_tarball(
        tmp_path, "installer.sh",
        '#!/usr/bin/env bash\necho "OK HASH"\n',
    )
    src = tmp_path / "out" / "src"
    env = {
        **os.environ,
        "NEXUS_HUB_FORCE_STANDALONE": "1",
        "NEXUS_HUB_TARBALL": str(tarball),
        "NEXUS_HUB_SRC": str(src),
        "NEXUS_HUB_EXPECTED_SHA256": _sha256(tarball),
    }
    proc = _run([BASH, "install.sh"], cwd=str(REPO_ROOT), env=env)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    combined = proc.stdout + proc.stderr
    assert "checksum OK" in combined
    assert "OK HASH" in proc.stdout


@bash_functional
def test_bash_checksum_mismatch_aborts(tmp_path: Path) -> None:
    tarball = _make_stub_tarball(
        tmp_path, "installer.sh",
        '#!/usr/bin/env bash\necho "SHOULD NOT RUN"\n',
    )
    src = tmp_path / "out" / "src"
    env = {
        **os.environ,
        "NEXUS_HUB_FORCE_STANDALONE": "1",
        "NEXUS_HUB_TARBALL": str(tarball),
        "NEXUS_HUB_SRC": str(src),
        "NEXUS_HUB_EXPECTED_SHA256": "0" * 64,
    }
    proc = _run([BASH, "install.sh"], cwd=str(REPO_ROOT), env=env)
    assert proc.returncode != 0
    combined = (proc.stdout + proc.stderr).lower()
    assert "checksum" in combined
    assert "SHOULD NOT RUN" not in proc.stdout


@bash_functional
def test_bash_path_traversal_is_refused(tmp_path: Path) -> None:
    tarball = _make_traversal_tarball(tmp_path)
    src = tmp_path / "out" / "src"
    env = {
        **os.environ,
        "NEXUS_HUB_FORCE_STANDALONE": "1",
        "NEXUS_HUB_TARBALL": str(tarball),
        "NEXUS_HUB_SRC": str(src),
        "NEXUS_HUB_SKIP_CHECKSUM": "1",
    }
    proc = _run([BASH, "install.sh"], cwd=str(REPO_ROOT), env=env)
    assert proc.returncode != 0
    combined = (proc.stdout + proc.stderr).lower()
    assert ".." in combined or "unsafe" in combined
    assert not src.exists() or not any(src.rglob("*"))


@pytest.mark.skipif(not PWSH, reason="PowerShell not available")
def test_ps_checksum_match_extracts(tmp_path: Path) -> None:
    tarball = _make_stub_tarball(
        tmp_path, "installer.ps1",
        'Write-Host "OK HASH"\n',
    )
    src = tmp_path / "out" / "src"
    env = {
        **os.environ,
        "NEXUS_HUB_FORCE_STANDALONE": "1",
        "NEXUS_HUB_TARBALL": str(tarball),
        "NEXUS_HUB_SRC": str(src),
        "NEXUS_HUB_EXPECTED_SHA256": _sha256(tarball),
    }
    proc = _run(
        [PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(INSTALL_PS1)],
        cwd=str(REPO_ROOT), env=env,
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    combined = proc.stdout + proc.stderr
    assert "checksum OK" in combined
    assert "OK HASH" in proc.stdout


@pytest.mark.skipif(not PWSH, reason="PowerShell not available")
def test_ps_checksum_mismatch_aborts(tmp_path: Path) -> None:
    tarball = _make_stub_tarball(
        tmp_path, "installer.ps1",
        'Write-Host "SHOULD NOT RUN"\n',
    )
    src = tmp_path / "out" / "src"
    env = {
        **os.environ,
        "NEXUS_HUB_FORCE_STANDALONE": "1",
        "NEXUS_HUB_TARBALL": str(tarball),
        "NEXUS_HUB_SRC": str(src),
        "NEXUS_HUB_EXPECTED_SHA256": "0" * 64,
    }
    proc = _run(
        [PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(INSTALL_PS1)],
        cwd=str(REPO_ROOT), env=env,
    )
    assert proc.returncode != 0
    combined = (proc.stdout + proc.stderr).lower()
    assert "checksum" in combined
    assert "SHOULD NOT RUN" not in proc.stdout


@pytest.mark.skipif(not PWSH, reason="PowerShell not available")
def test_ps_path_traversal_is_refused(tmp_path: Path) -> None:
    tarball = _make_traversal_tarball(tmp_path)
    src = tmp_path / "out" / "src"
    env = {
        **os.environ,
        "NEXUS_HUB_FORCE_STANDALONE": "1",
        "NEXUS_HUB_TARBALL": str(tarball),
        "NEXUS_HUB_SRC": str(src),
        "NEXUS_HUB_SKIP_CHECKSUM": "1",
    }
    proc = _run(
        [PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(INSTALL_PS1)],
        cwd=str(REPO_ROOT), env=env,
    )
    assert proc.returncode != 0
    combined = (proc.stdout + proc.stderr).lower()
    assert ".." in combined or "unsafe" in combined
