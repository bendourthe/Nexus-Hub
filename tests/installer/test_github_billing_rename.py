"""Tests for the GitHub monitor rename to "GitHub Billing Usage" (v3.15.12 Phase 3).

The rename exists because "GitHub Usage Monitor" invited two wrong readings: that
the extension monitored Copilot, or that it monitored Actions only. It reports
Actions minutes and storage PLUS Copilot billing, for one configured billing owner.

The load-bearing decision this file guards is that the extension **id did not
change**. A VS Code id is `publisher.name`, so renaming `name` mints a new
extension rather than updating the installed one, and anyone who had already
installed the old id would end up with two extensions both writing a status-bar
item. Renaming only the display surfaces is non-breaking: an existing install
updates in place and keeps its stored token and cached snapshot.

Coverage:
  * Manifest: new display name, a description naming both covered surfaces, every
    command title and category on the new prefix, and the unchanged id inputs
    (`name`, `publisher`) plus unchanged command ids and configuration prefix.
  * Installers: both pass the new DisplayName and StatusHint, both still pass the
    unchanged extension id, and they agree with each other and with the manifest.
  * Idempotence: exactly one GitHub billing extension is installed by a run, and
    the install is keyed on a single unchanged id, so a re-run cannot leave two.
  * No stale copy: the old prefix survives only where it legitimately must (the
    directory path, the id, command ids, the config prefix, storage/view ids).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXTENSION_DIR = ROOT / "extensions" / "github-usage-monitor"
MANIFEST = EXTENSION_DIR / "package.json"
README = EXTENSION_DIR / "README.md"
INSTALLER_SH = ROOT / "scripts" / "installer.sh"
INSTALLER_PS1 = ROOT / "scripts" / "installer.ps1"

EXTENSION_ID = "nexus-hub.github-usage-monitor"
DISPLAY_NAME = "GitHub Billing Usage"
STATUS_HINT = "GitHub Billing: --"
TITLE_PREFIX = "GitHub Billing: "


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _manifest() -> dict:
    return json.loads(_read(MANIFEST))


def test_manifest_carries_the_new_display_name() -> None:
    assert _manifest()["displayName"] == DISPLAY_NAME


def test_description_names_both_covered_surfaces() -> None:
    """An Actions-only or Copilot-only description would be inaccurate."""
    description = _manifest()["description"].lower()
    assert "actions" in description
    assert "storage" in description
    assert "copilot" in description
    # The single-owner scope is the other thing users get wrong.
    assert "owner" in description


def test_every_command_title_and_category_uses_the_new_prefix() -> None:
    commands = _manifest()["contributes"]["commands"]
    # 9 at the v3.15.12 Phase 3 rename, plus logIn / logOut / diagnoseAuth / openBillingPage from
    # Phase 4's per-target auth work. The count is asserted so a dropped command is
    # caught, and it is updated deliberately rather than relaxed to a range.
    assert len(commands) == 13
    for command in commands:
        assert command["title"].startswith(TITLE_PREFIX), command["title"]
        # A single space after the colon, not zero and not two.
        assert not command["title"].startswith(f"{TITLE_PREFIX} ")
        assert command["category"] == "GitHub Billing"


def test_configuration_and_view_titles_are_renamed() -> None:
    contributes = _manifest()["contributes"]
    assert contributes["configuration"]["title"] == DISPLAY_NAME
    container = contributes["viewsContainers"]["activitybar"][0]
    assert container["title"] == "GitHub Billing Warning"


def test_extension_id_inputs_are_unchanged() -> None:
    """The id is publisher.name; changing either would orphan the install."""
    manifest = _manifest()
    assert manifest["name"] == "github-usage-monitor"
    assert manifest["publisher"] == "nexus-hub"
    assert f"{manifest['publisher']}.{manifest['name']}" == EXTENSION_ID


def test_command_ids_and_configuration_prefix_are_unchanged() -> None:
    """Renaming these would break keybindings and discard stored settings."""
    manifest = _manifest()
    for command in manifest["contributes"]["commands"]:
        assert command["command"].startswith("github-usage.")
    for key in manifest["contributes"]["configuration"]["properties"]:
        assert key.startswith("githubUsage.")


@pytest.mark.parametrize("installer", (INSTALLER_SH, INSTALLER_PS1))
def test_installers_pass_the_new_display_name_and_status_hint(installer: Path) -> None:
    text = _read(installer)
    # Match the invocation, not any line that merely names the path: the rename
    # added an explanatory comment that also mentions the extension directory.
    github_lines = [
        line
        for line in text.splitlines()
        # bash uses underscores, PowerShell hyphens, so normalize before matching.
        if ("build_and_install_one_extension" in line.lower().replace("-", "_"))
        and (
            "extensions/github-usage-monitor" in line
            or "extensions\\github-usage-monitor" in line
        )
    ]
    assert len(github_lines) == 1, "expected exactly one GitHub install invocation"
    line = github_lines[0]
    assert DISPLAY_NAME in line
    assert STATUS_HINT in line
    assert EXTENSION_ID in line
    # The old display strings must not survive on the invocation line.
    assert "GitHub Usage Monitor" not in line
    assert "GitHub Usage: --" not in line


def test_both_installers_agree_on_the_github_invocation() -> None:
    """Cross-platform parity: a rename applied to one installer only would leave
    Windows and POSIX users seeing different names for the same extension."""
    for token in (DISPLAY_NAME, STATUS_HINT, EXTENSION_ID):
        assert token in _read(INSTALLER_SH)
        assert token in _read(INSTALLER_PS1)


@pytest.mark.parametrize("installer", (INSTALLER_SH, INSTALLER_PS1))
def test_install_is_keyed_on_one_unchanged_id_so_a_rerun_cannot_duplicate(
    installer: Path,
) -> None:
    """Exactly one GitHub billing extension after a run AND after a re-run.

    Because the id is unchanged and appears exactly once, a re-run reinstalls the
    same id in place rather than adding a second extension. Equally important:
    there is no uninstall of a superseded id, because none was created.
    """
    text = _read(installer)
    assert text.count(EXTENSION_ID) == 1
    # No stale second id was introduced by the rename.
    assert "nexus-hub.github-billing" not in text
    assert "github-billing-usage" not in text
    # No teardown step is needed, and none should have been added.
    assert not re.search(r"uninstall-extension.*github", text, re.IGNORECASE)


def test_old_prefix_survives_only_where_it_legitimately_must() -> None:
    """The manifest keeps `github-usage` in ids and paths, never in visible copy."""
    manifest = _manifest()
    visible = [
        manifest["displayName"],
        manifest["description"],
        manifest["contributes"]["configuration"]["title"],
        manifest["contributes"]["viewsContainers"]["activitybar"][0]["title"],
        *(command["title"] for command in manifest["contributes"]["commands"]),
        *(command["category"] for command in manifest["contributes"]["commands"]),
    ]
    for value in visible:
        assert "GitHub Usage" not in value, value


def test_readme_records_the_id_decision_and_its_consequence() -> None:
    text = _read(README)
    assert text.startswith(f"# {DISPLAY_NAME}")
    assert EXTENSION_ID in text
    # The reasoning must be recorded, not just the outcome, so it is not undone.
    assert "did NOT change" in text or "deliberately did NOT change" in text
    assert "publisher.name" in text
    # The one user-visible cost of the rename is stated.
    assert "Command Palette" in text


def test_readme_command_table_uses_the_new_titles() -> None:
    text = _read(README)
    assert "`GitHub Billing: Dashboard`" in text
    assert "GitHub Usage: " not in text
