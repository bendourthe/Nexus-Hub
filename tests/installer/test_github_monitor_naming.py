"""Naming and identity contract for the GitHub monitor VS Code extension.

The display name has moved twice: v3.15.12 Phase 3 renamed "GitHub Usage Monitor"
to "GitHub Billing Usage", and v3.16.3 Phase 1 reverted it for consistency with the
Claude, Codex, and Cursor monitors, which a user reads as one family. The concern
behind the v3.15.12 rename (that "usage monitor" under-describes the coverage) is
now carried by the description and the panel subtitle, which name Actions minutes
and storage AND Copilot billing explicitly - which is what
``test_description_names_both_covered_surfaces`` pins.

This file was renamed from ``test_github_billing_rename.py`` at the same time. It
now guards the *contract*, not one dated decision: whatever the display name is,
every surface must agree on it, and the extension id must never move.

The load-bearing invariant is that the extension **id has never changed**, through
either rename. A VS Code id is ``publisher.name``, so renaming ``name`` mints a new
extension rather than updating the installed one, and anyone who had already
installed the old id would end up with two extensions both writing a status-bar
item. Renaming only the display surfaces is non-breaking: an existing install
updates in place.

The configuration and command namespace DID move in v3.16.3, which is why
``src/migration.ts`` exists. That migration is covered by the extension's own
Vitest suite (``extensions/github-usage-monitor/test/migration.test.ts``); this
file covers only the manifest and installer surfaces.

Coverage:
  * Manifest: the display name, a description naming both covered surfaces, every
    command title and category derived from that display name, the current command
    and configuration prefix, and the unchanged id inputs (`name`, `publisher`).
  * Installers: both pass the same DisplayName and StatusHint, both still pass the
    unchanged extension id, and they agree with each other and with the manifest.
  * Idempotence: exactly one GitHub extension is installed by a run, keyed on a
    single unchanged id, so a re-run cannot leave two.
  * No stale copy: the superseded display name survives only in the deliberate
    naming-history record, never in live user-visible manifest copy.
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
DISPLAY_NAME = "GitHub Usage Monitor"
STATUS_HINT = "GitHub Usage: --"
TITLE_PREFIX = f"{DISPLAY_NAME}: "
COMMAND_PREFIX = "githubUsageMonitor."
SUPERSEDED_DISPLAY_NAME = "GitHub Billing Usage"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _manifest() -> dict:
    return json.loads(_read(MANIFEST))


def test_manifest_carries_the_current_display_name() -> None:
    assert _manifest()["displayName"] == DISPLAY_NAME


def test_description_names_both_covered_surfaces() -> None:
    """An Actions-only or Copilot-only description would be inaccurate.

    This is the assertion that lets the display name be the short family name: the
    coverage is stated here rather than crammed into the title.
    """
    description = _manifest()["description"].lower()
    assert "actions" in description
    assert "storage" in description
    assert "copilot" in description
    # The single-owner scope is the other thing users get wrong.
    assert "owner" in description


def test_every_command_title_and_category_matches_the_display_name() -> None:
    commands = _manifest()["contributes"]["commands"]
    # 13 through v3.15.12, plus `openNativeSettings` in v3.16.3, which was
    # registered but never contributed and so was unreachable from the Command
    # Palette. The count is asserted so a dropped command is caught, and it is
    # updated deliberately rather than relaxed to a range.
    assert len(commands) == 14
    for command in commands:
        assert command["title"].startswith(TITLE_PREFIX), command["title"]
        # A single space after the colon, not zero and not two.
        assert not command["title"].startswith(f"{TITLE_PREFIX} ")
        assert command["category"] == DISPLAY_NAME


def test_configuration_and_view_titles_match_the_display_name() -> None:
    contributes = _manifest()["contributes"]
    assert contributes["configuration"]["title"] == DISPLAY_NAME
    container = contributes["viewsContainers"]["activitybar"][0]
    assert container["title"] == f"{DISPLAY_NAME} Warning"


def test_extension_id_inputs_are_unchanged() -> None:
    """The id is publisher.name; changing either would orphan the install.

    Unchanged through BOTH renames. This is the one assertion in this file that
    must never be updated to follow a decision.
    """
    manifest = _manifest()
    assert manifest["name"] == "github-usage-monitor"
    assert manifest["publisher"] == "nexus-hub"
    assert f"{manifest['publisher']}.{manifest['name']}" == EXTENSION_ID


def test_command_ids_and_configuration_keys_share_one_namespace() -> None:
    """v3.16.3 moved both to `githubUsageMonitor.*`, with a one-time migration.

    A split namespace is the failure this catches: renaming the commands but not
    the settings (or vice versa) type-checks and runs, and simply reads defaults.
    """
    manifest = _manifest()
    for command in manifest["contributes"]["commands"]:
        assert command["command"].startswith(COMMAND_PREFIX), command["command"]
    for key in manifest["contributes"]["configuration"]["properties"]:
        assert key.startswith(COMMAND_PREFIX), key


@pytest.mark.parametrize("installer", (INSTALLER_SH, INSTALLER_PS1))
def test_installers_pass_the_current_display_name_and_status_hint(installer: Path) -> None:
    text = _read(installer)
    # Match the invocation, not any line that merely names the path: the rename
    # commentary also mentions the extension directory.
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
    # The superseded display strings must not survive on the invocation line.
    assert SUPERSEDED_DISPLAY_NAME not in line
    assert "GitHub Billing: --" not in line


def test_both_installers_agree_on_the_github_invocation() -> None:
    """Cross-platform parity: a rename applied to one installer only would leave
    Windows and POSIX users seeing different names for the same extension."""
    for token in (DISPLAY_NAME, STATUS_HINT, EXTENSION_ID):
        assert token in _read(INSTALLER_SH)
        assert token in _read(INSTALLER_PS1)


def test_installer_status_hint_matches_the_extension_status_bar_label() -> None:
    """The hint the installer prints must be the text the extension really shows.

    `buildStatusText()` composes `<glyph><gap><label><value>`, so a hint that names
    a different label advertises a status bar the user will not recognize.
    """
    status_bar = _read(EXTENSION_DIR / "src" / "statusBarManager.ts")
    label = STATUS_HINT.removesuffix("--")
    assert f'"{label}"' in status_bar, f"statusBarManager must render the {label!r} label"


@pytest.mark.parametrize("installer", (INSTALLER_SH, INSTALLER_PS1))
def test_install_is_keyed_on_one_unchanged_id_so_a_rerun_cannot_duplicate(
    installer: Path,
) -> None:
    """Exactly one GitHub extension after a run AND after a re-run.

    Because the id is unchanged and appears exactly once, a re-run reinstalls the
    same id in place rather than adding a second extension. Equally important:
    there is no uninstall of a superseded id, because none was ever created.
    """
    text = _read(installer)
    assert text.count(EXTENSION_ID) == 1
    # No stale second id was introduced by either rename.
    assert "nexus-hub.github-billing" not in text
    assert "github-billing-usage" not in text
    assert "nexus-hub.github-usage-monitor-monitor" not in text
    # No teardown step is needed, and none should have been added.
    assert not re.search(r"uninstall-extension.*github", text, re.IGNORECASE)


def test_superseded_display_name_survives_nowhere_in_live_manifest_copy() -> None:
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
        assert SUPERSEDED_DISPLAY_NAME not in value, value
        assert "GitHub Billing" not in value, value


def test_readme_records_the_id_decision_and_both_renames() -> None:
    text = _read(README)
    assert text.startswith(f"# {DISPLAY_NAME}")
    assert EXTENSION_ID in text
    # The reasoning must be recorded, not just the outcome, so it is not undone.
    assert "did NOT change" in text or "deliberately did NOT change" in text
    assert "publisher.name" in text
    # Both decisions stay visible; a silently-overwritten history is the thing to
    # avoid, since a reader of the v3.15.12 plan must be able to see what happened.
    assert SUPERSEDED_DISPLAY_NAME in text
    # The user-visible cost of a rename is stated.
    assert "Command Palette" in text


def test_readme_command_table_uses_the_current_titles() -> None:
    text = _read(README)
    assert f"`{TITLE_PREFIX}Dashboard`" in text
    # No stale command title survives outside the naming-history section.
    assert "`GitHub Billing: " not in text
