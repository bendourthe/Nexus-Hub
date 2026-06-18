#!/usr/bin/env python3
"""`nexus-hub` command-line interface (v3.7.0 Phase 3).

This is the logic core behind the small `nexus-hub` launcher the installer drops
on PATH (`~/.nexus-hub/bin/nexus-hub` on POSIX, `nexus-hub.cmd` on Windows). The
native launcher is a thin shim that locates a Python interpreter and execs this
module; all of the real work lives here so a single cross-platform `.py` file
covers every platform (the NI-v24-1 convention -- a stdlib-only Python tool needs
no `.ps1` sibling).

Subcommands:

    nexus-hub --version        Print the installed Nexus-Hub version.
    nexus-hub upgrade          Compare the installed version against the latest
                               on the project's own GitHub, show what's new, and
                               offer to upgrade in place by re-running the
                               install bootstrap.
    nexus-hub --help           Usage.

THE ONLY OUTBOUND CALL this CLI makes is `upgrade`'s version check, and it goes
to the project's OWN GitHub (raw.githubusercontent.com / github.com) -- the same
posture the installer already has. No third-party data processor, credential, or
new dependency is introduced. The fetch prefers `curl`, falls back to `wget`,
and finally to the Python stdlib `urllib` so it works on a bare machine; a
`file://` source (used by the tests) is read directly without any network tool.

Internal testing affordances (environment variables):

    NEXUS_HUB_HOME            install root to read VERSION from   (default: ~/.nexus-hub)
    NEXUS_HUB_REPO            owner/name slug        (default: bendourthe/Nexus-Hub)
    NEXUS_HUB_REF             git ref to check against            (default: main)
    NEXUS_HUB_RAW_BASE        override the raw.githubusercontent base (a URL or a
                              local/`file://` dir holding plugin.json + CHANGELOG.md)
    NEXUS_HUB_INSTALL_BASE    override the install.sh/.ps1 base URL the upgrade re-runs
    NEXUS_HUB_UPGRADE_DRY_RUN=1  print the bootstrap command instead of executing it
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

DEFAULT_REPO = "bendourthe/Nexus-Hub"
DEFAULT_REF = "main"

# A semantic-version token. Mirrors the one in check_version_sync.py so the CLI
# reads exactly the surfaces that guard writes.
_SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")
_PLUGIN_VERSION_RE = re.compile(r'"version"\s*:\s*"([^"]+)"')


def _eprint(message: str) -> None:
    """Write a line to stderr (informational/error output)."""
    print(message, file=sys.stderr)


# --- Environment-derived configuration --------------------------------------


def install_home() -> Path:
    """The install root (`~/.nexus-hub`), overridable via NEXUS_HUB_HOME."""
    override = os.environ.get("NEXUS_HUB_HOME")
    if override:
        return Path(override)
    return Path.home() / ".nexus-hub"


def _repo() -> str:
    return os.environ.get("NEXUS_HUB_REPO") or DEFAULT_REPO


def _ref() -> str:
    return os.environ.get("NEXUS_HUB_REF") or DEFAULT_REF


def _raw_base() -> str:
    """Base for raw file reads (plugin.json, CHANGELOG.md) on the chosen ref."""
    override = os.environ.get("NEXUS_HUB_RAW_BASE")
    if override:
        return override.rstrip("/")
    return f"https://raw.githubusercontent.com/{_repo()}/{_ref()}"


def _install_base() -> str:
    """Base the `upgrade` re-run fetches install.sh / install.ps1 from."""
    override = os.environ.get("NEXUS_HUB_INSTALL_BASE")
    if override:
        return override.rstrip("/")
    return f"https://raw.githubusercontent.com/{_repo()}/{_ref()}"


# --- Version reading --------------------------------------------------------


def read_installed_version() -> str | None:
    """Return the installed version, or None if it cannot be determined.

    Reads the `VERSION` file the installer writes (install-mode independent),
    falling back to the extracted catalog's plugin.json for a standalone install.
    """
    home = install_home()
    version_file = home / "VERSION"
    if version_file.is_file():
        # utf-8-sig so a BOM (a PowerShell-written file can carry one) is dropped.
        text = version_file.read_text(encoding="utf-8-sig", errors="replace").strip()
        if text:
            return text.splitlines()[0].strip()

    plugin = home / "src" / ".claude-plugin" / "plugin.json"
    if plugin.is_file():
        match = _PLUGIN_VERSION_RE.search(
            plugin.read_text(encoding="utf-8", errors="replace")
        )
        if match:
            return match.group(1)
    return None


def parse_semver(version: str) -> tuple[int, int, int] | None:
    """Parse `X.Y.Z` (ignoring any pre-release/build suffix) into a tuple."""
    match = _SEMVER_RE.search(version)
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def compare_semver(installed: str, latest: str) -> int:
    """Return -1 if installed < latest, 0 if equal, 1 if installed > latest.

    Unparseable versions sort as oldest (0.0.0), so a missing/garbled installed
    version is always treated as "behind" -- the safe default that still offers
    the upgrade rather than silently refusing it.
    """
    a = parse_semver(installed) or (0, 0, 0)
    b = parse_semver(latest) or (0, 0, 0)
    return (a > b) - (a < b)


# --- Network: fetch text from the project's own GitHub ----------------------


class FetchError(Exception):
    """A version-check fetch failed (offline, 404, or no usable downloader)."""


def fetch_text(url: str) -> str:
    """Fetch the text at `url`, preferring curl, then wget, then urllib.

    A `file://` URL or a bare local path is read directly (no network tool) so
    the tests can point NEXUS_HUB_RAW_BASE at a local fixture. For real https
    URLs the tool order honors the Phase 1 precheck (curl preferred, wget
    fallback); urllib is the last resort so a machine with neither still works.
    Raises FetchError with a clear message on any failure.
    """
    # Local fixture / offline-friendly path: read straight off disk.
    if url.startswith("file://"):
        local = Path(urllib.request.url2pathname(url[len("file://"):]))
        return _read_local(local)
    if "://" not in url:
        return _read_local(Path(url))

    import shutil

    if shutil.which("curl"):
        proc = subprocess.run(
            ["curl", "-fsSL", "--connect-timeout", "15", "--max-time", "60", url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode == 0:
            return proc.stdout
        raise FetchError(f"download failed (curl, exit {proc.returncode}): {url}")

    if shutil.which("wget"):
        proc = subprocess.run(
            ["wget", "-q", "--timeout=60", "-O", "-", url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode == 0:
            return proc.stdout
        raise FetchError(f"download failed (wget, exit {proc.returncode}): {url}")

    try:
        with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 - project's own GitHub
            return response.read().decode("utf-8", errors="replace")
    except OSError as exc:
        raise FetchError(f"download failed (urllib): {url} -- {exc}") from exc


def _read_local(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise FetchError(f"cannot read {path}: {exc}") from exc


def fetch_latest_version() -> str:
    """Read the latest version from the project's own GitHub plugin.json."""
    text = fetch_text(f"{_raw_base()}/.claude-plugin/plugin.json")
    match = _PLUGIN_VERSION_RE.search(text)
    if not match:
        raise FetchError("could not parse 'version' from the remote plugin.json")
    return match.group(1)


def extract_changelog_section(changelog: str, version: str) -> str:
    """Return the CHANGELOG block for `version` (`## [X.Y.Z]` to the next `## [`).

    Falls back to the first versioned section (skipping `## [Unreleased]`) when
    the exact heading is absent, then to an empty string. The result is trimmed
    to a short summary so `upgrade` stays scannable.
    """
    lines = changelog.splitlines()
    target = f"## [{version}]"

    def _slice_from(start_idx: int) -> list[str]:
        out: list[str] = []
        for line in lines[start_idx + 1:]:
            if line.startswith("## ["):
                break
            out.append(line)
        return out

    start = next((i for i, ln in enumerate(lines) if ln.startswith(target)), None)
    if start is None:
        start = next(
            (
                i
                for i, ln in enumerate(lines)
                if ln.startswith("## [") and "[Unreleased]" not in ln
            ),
            None,
        )
    if start is None:
        return ""

    body = _slice_from(start)
    # Trim leading/trailing blank lines and cap the length for a short summary.
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    max_lines = 40
    if len(body) > max_lines:
        body = body[:max_lines] + ["...", "(truncated -- see the full CHANGELOG on GitHub)"]
    return "\n".join(body)


# --- Bootstrap re-run -------------------------------------------------------


def _bootstrap_command() -> list[str]:
    """Build the platform-appropriate bootstrap re-run command (project GitHub)."""
    base = _install_base()
    if sys.platform == "win32":
        ps_cmd = f"irm {base}/install.ps1 | iex"
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
    sh_cmd = f"curl -fsSL {base}/install.sh | bash"
    return ["bash", "-c", sh_cmd]


def run_bootstrap() -> int:
    """Re-run the install bootstrap to upgrade in place. Honors the dry-run seam."""
    command = _bootstrap_command()
    if os.environ.get("NEXUS_HUB_UPGRADE_DRY_RUN") == "1":
        # Show the exact command rather than executing it (used by the tests and
        # by anyone who wants to inspect the re-run before trusting it).
        printable = command[-1] if command and command[0] in {"bash", "powershell"} else " ".join(command)
        print(f"[dry-run] would upgrade by running: {printable}")
        return 0
    _eprint("Upgrading by re-running the install bootstrap...")
    return subprocess.run(command).returncode


# --- Subcommands ------------------------------------------------------------


def cmd_version() -> int:
    """Print the installed version (or a clear 'unknown' note)."""
    version = read_installed_version()
    if version:
        print(f"nexus-hub {version}")
        return 0
    _eprint(
        "nexus-hub: installed version unknown "
        f"(no VERSION file under {install_home()}). Re-run the installer."
    )
    return 1


def _confirm_upgrade(assume_yes: bool) -> bool:
    """Ask whether to upgrade. Auto-yes with --yes; safe 'no' without a TTY."""
    if assume_yes:
        return True
    if not sys.stdin or not sys.stdin.isatty():
        base = _install_base()
        hint = (
            f"irm {base}/install.ps1 | iex"
            if sys.platform == "win32"
            else f"curl -fsSL {base}/install.sh | bash"
        )
        _eprint(f"Run `nexus-hub upgrade --yes`, or upgrade directly with:\n    {hint}")
        return False
    try:
        answer = input("Upgrade now? [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def cmd_upgrade(assume_yes: bool) -> int:
    """Compare installed vs latest; show what's new; offer the in-place upgrade."""
    installed = read_installed_version()
    installed_label = installed or "unknown"

    try:
        latest = fetch_latest_version()
    except FetchError as exc:
        # Offline / fetch failure: clear message, non-zero exit, NO partial state
        # (nothing has been changed at this point).
        _eprint(f"nexus-hub upgrade: could not reach the project's GitHub -- {exc}")
        _eprint("Check your network connection and try again.")
        return 2

    print(f"Installed: {installed_label}")
    print(f"Latest:    {latest}")

    if installed and compare_semver(installed, latest) >= 0:
        print("\nYou are already on the latest version. Nothing to do.")
        return 0

    # Behind (or unknown installed version): show a short what's-new summary.
    try:
        changelog = fetch_text(f"{_raw_base()}/CHANGELOG.md")
        whats_new = extract_changelog_section(changelog, latest)
    except FetchError:
        whats_new = ""  # The version comparison is enough; notes are best-effort.

    print(f"\nA newer version is available ({installed_label} -> {latest}).")
    if whats_new:
        print("\nWhat's new:\n")
        print(whats_new)

    if not _confirm_upgrade(assume_yes):
        print("\nUpgrade skipped.")
        return 0

    return run_bootstrap()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-hub",
        description="Nexus-Hub command-line interface.",
    )
    parser.add_argument(
        "-v", "--version", action="store_true", help="Print the installed version."
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("version", help="Print the installed version.")
    up = sub.add_parser("upgrade", help="Check for and install the latest version.")
    up.add_argument(
        "-y", "--yes", action="store_true", help="Upgrade without prompting."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version or args.command == "version":
        return cmd_version()
    if args.command == "upgrade":
        return cmd_upgrade(assume_yes=args.yes)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
