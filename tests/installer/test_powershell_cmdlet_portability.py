"""The PowerShell installer must not depend on Get-FileHash (v3.16.1).

`Get-FileHash` raised CommandNotFoundException inside `installer.ps1` on GitHub's
windows-latest image under Windows PowerShell 5.1, while the rest of
Microsoft.PowerShell.Utility worked in the same session and pwsh 7 on the same
image was fine. It is the second sighting of the class in this repo: v3.15.6 hit
it in `catalog/hooks/provenance-ledger.ps1` and reached for the same .NET stream.

What makes it worth a regression test rather than just a fix is how long it hid.
`Safe-Copy` hashes ONLY when the destination already exists, so on a fresh
install every call short-circuits and the cmdlet is never reached. The
install-smoke job installs into a clean HOME, so it passed for release after
release with that line unreachable. The failure needs a job that installs twice
into one HOME, which the v3.16.1 parity suite was the first to do.

So the guard here is deliberately static. Re-running the end-to-end install
would not catch a reintroduction on any developer machine where the cmdlet
works, which is all of them - the defect is only observable on an image we do
not control. A source assertion is the only check that fails in the right place.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_INSTALLER = _ROOT / "scripts" / "installer.ps1"
_LEDGER = _ROOT / "catalog" / "hooks" / "provenance-ledger.ps1"


@pytest.fixture(scope="module")
def installer() -> str:
    return _INSTALLER.read_text(encoding="utf-8")


def _code_lines(src: str) -> list[tuple[int, str]]:
    """Lines that are not pure comments.

    The fix's own rationale names the cmdlet several times, and a naive substring
    search would flag the comment explaining why the cmdlet is banned.
    """
    out = []
    for n, line in enumerate(src.split("\n"), 1):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            out.append((n, line))
    return out


def test_installer_does_not_call_get_filehash(installer: str) -> None:
    hits = [n for n, line in _code_lines(installer) if "Get-FileHash" in line]
    assert not hits, (
        f"installer.ps1 calls Get-FileHash at line(s) {hits}. That cmdlet has "
        "twice failed to resolve on Windows PowerShell 5.1 CI images. Use the "
        "Get-FileSha256 helper, which goes through .NET and needs no module "
        "resolution."
    )


def test_installer_defines_the_dotnet_hash_helper(installer: str) -> None:
    assert re.search(r"^function Get-FileSha256\b", installer, re.M), (
        "installer.ps1 must define Get-FileSha256; Safe-Copy's identical-file "
        "short-circuit depends on it."
    )


def test_helper_uses_the_dotnet_stream_not_a_cmdlet(installer: str) -> None:
    start = installer.index("function Get-FileSha256")
    body = installer[start:start + 800]
    assert "System.Security.Cryptography.SHA256" in body, (
        "Get-FileSha256 must hash via .NET. Routing it back through any cmdlet "
        "reintroduces the module-resolution dependency it exists to remove."
    )
    assert "Dispose()" in body, (
        "The stream and the hash provider must be disposed; the installer opens "
        "this for every file whose destination already exists, and a leaked "
        "handle on Windows blocks the very file the installer is about to write."
    )


def test_safe_copy_still_short_circuits_on_identical_files(installer: str) -> None:
    """The behavior the hash exists for, pinned.

    Without this, a future edit could satisfy every assertion above and still
    drop the comparison, turning every re-install into a full rewrite and
    resurfacing conflict prompts for files the user never touched.
    """
    start = installer.index("function Safe-Copy")
    body = installer[start:start + 1500]
    assert "Get-FileSha256" in body and "$srcHash -eq $dstHash" in body, (
        "Safe-Copy must compare source and destination hashes and return early "
        "when they match."
    )


def test_precedent_in_the_hook_is_still_dotnet() -> None:
    """The v3.15.6 sibling fix must not regress to the cmdlet either.

    The installer comment cites this file as the corroborating sighting. If the
    hook quietly went back to Get-FileHash, that citation would be misleading and
    the ledger would start emitting NOHASH on the same images.
    """
    src = _LEDGER.read_text(encoding="utf-8")
    hits = [n for n, line in _code_lines(src) if "Get-FileHash" in line]
    assert not hits, f"provenance-ledger.ps1 calls Get-FileHash at line(s) {hits}."
    assert "System.Security.Cryptography.SHA256" in src
