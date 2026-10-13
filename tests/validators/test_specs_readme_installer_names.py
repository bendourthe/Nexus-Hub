"""docs/specs/README.md cites each installer's real dispatch function.

The install-mechanism note named `invoke_registry_platform` for both installers,
while the PowerShell installer defines `Invoke-RegistryPlatform` (v4.13.11 cycle 2
A7). This checks the cited names against the installers rather than the wording.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "docs" / "specs" / "README.md"


def _defined(installer: str) -> set[str]:
    text = (REPO_ROOT / "scripts" / installer).read_text(encoding="utf-8")
    if installer.endswith(".sh"):
        return set(re.findall(r"(?m)^([A-Za-z_]\w*)\(\)\s*\{", text))
    return set(re.findall(r"(?mi)^function\s+([A-Za-z][\w-]*)", text))


def test_install_mechanism_cites_each_installers_own_dispatch_function():
    line = next(
        row
        for row in README.read_text(encoding="utf-8").splitlines()
        if row.startswith("- **Install mechanism**")
    )
    cited = re.findall(r"`([A-Za-z_][\w-]*)` in `scripts/(installer\.(?:sh|ps1))`", line)

    assert {installer for _, installer in cited} == {"installer.sh", "installer.ps1"}, line
    for name, installer in cited:
        assert name in _defined(installer), f"{name} is not defined in scripts/{installer}"
