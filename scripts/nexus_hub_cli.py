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
    nexus-hub verify           Recompute SHA-256 of the installed catalog and
                               diff it against the published MANIFEST.sha256,
                               reporting OK / MODIFIED / MISSING / EXTRA and a
                               single PASS / FAIL. Strictly local, no outbound
                               call (see scripts/verify_install.py for the
                               threat-model boundary).
    nexus-hub setup-media      Guided, opt-in bring-your-own-key setup for
                               optional license-free stock-media API keys (Pexels,
                               for stock video). Captures the key via a HIDDEN
                               terminal prompt and stores it under
                               ~/.nexus-hub/config/media.env at mode 0600. Strictly
                               local, no outbound call (see
                               scripts/setup_media_keys.py).
    nexus-hub autonomy         Report or change time-bounded project autonomy
                               through the shared consent and audit core.
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


# A selector id is kebab-case by construction (every id in data/bundles.json is).
# Validating against this instead of quoting is what makes forwarding safe: the
# selectors end up inside a shell command string, and an id that cannot contain a
# quote, space, semicolon, or backtick cannot break out of it. Anything failing
# this check is dropped rather than escaped, because a selector that does not
# match is not a selector we wrote.
_SELECTOR_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def recorded_selection() -> dict | None:
    """The selection recorded by the last global install, or None for full."""
    manifest = install_home() / "install-manifest.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    selection = data.get("selection")
    return selection if isinstance(selection, dict) else None


def recorded_selector_flags(style: str) -> list[str]:
    """Selector flags to re-apply on upgrade, in `style` = "sh" or "ps".

    An upgrade must not silently widen a focused install back to the full
    catalog. That would be the single most annoying way to lose a selection,
    because it happens during an operation the user expects to be a no-op on
    scope.
    """
    selection = recorded_selection()
    if not selection:
        return []
    requested = selection.get("requested") or {}
    profile = requested.get("profile")
    modules = [m for m in (requested.get("modules") or []) if _SELECTOR_ID.match(str(m))]
    bundles = [b for b in (requested.get("bundles") or []) if _SELECTOR_ID.match(str(b))]
    flags: list[str] = []
    prefix = "-" if style == "ps" else "--"
    name = {"profile": "Profile", "modules": "Modules", "bundles": "Bundles"} if style == "ps" \
        else {"profile": "profile", "modules": "modules", "bundles": "bundles"}
    if profile and _SELECTOR_ID.match(str(profile)):
        flags += [f"{prefix}{name['profile']}", str(profile)]
    if modules:
        flags += [f"{prefix}{name['modules']}", ",".join(modules)]
    if bundles:
        flags += [f"{prefix}{name['bundles']}", ",".join(bundles)]
    return flags


def _bootstrap_command() -> list[str]:
    """Build the platform-appropriate bootstrap re-run command (project GitHub).

    Any selection recorded by the previous install is re-applied, so an upgrade
    preserves the user's scope instead of quietly restoring the full catalog.
    """
    base = _install_base()
    if sys.platform == "win32":
        ps_flags = recorded_selector_flags("ps")
        # `irm | iex` cannot take arguments, so a scriptblock is required to pass
        # any. Only used when there is something to pass; the plain pipe stays
        # the default so the common path is unchanged.
        if ps_flags:
            ps_cmd = (
                "&([scriptblock]::Create((irm "
                + f"{base}/install.ps1))) " + " ".join(ps_flags)
            )
        else:
            ps_cmd = f"irm {base}/install.ps1 | iex"
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
    sh_flags = recorded_selector_flags("sh")
    # `bash -s --` is the standard way to hand arguments to a piped script.
    suffix = (" -s -- " + " ".join(sh_flags)) if sh_flags else ""
    sh_cmd = f"curl -fsSL {base}/install.sh | bash{suffix}"
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


def cmd_verify(argv: list[str]) -> int:
    """Dispatch `nexus-hub verify` to the installed verify_install sibling.

    The verifier is a separate stdlib-only module so the integrity logic stays
    out of this network-capable CLI core (the only outbound call in this file is
    `upgrade`'s version check). Imported lazily so importing this module does
    not pull in the verifier; the CLI's own directory is put on sys.path so the
    sibling resolves both at runtime (~/.nexus-hub/scripts/) and in tests.
    """
    cli_dir = str(Path(__file__).resolve().parent)
    if cli_dir not in sys.path:
        sys.path.insert(0, cli_dir)
    try:
        import verify_install
    except ImportError as exc:  # pragma: no cover - missing install artifact
        _eprint(
            "nexus-hub verify: verify_install.py not found "
            f"({exc}). Re-run the installer."
        )
        return 2
    return verify_install.main(argv)


def cmd_setup_media(argv: list[str]) -> int:
    """Dispatch `nexus-hub setup-media` to the installed setup_media_keys sibling.

    The helper captures an optional stock-media API key (Pexels, for stock video)
    via a HIDDEN terminal prompt and stores it under ~/.nexus-hub/config/. It is
    run as a SUBPROCESS (not imported) with this CLI's own interpreter, inheriting
    stdin / stdout / stderr so the hidden getpass prompt reads from the real
    terminal; the key is never passed as an argument. This adds no outbound call
    (the setup helper makes none).
    """
    helper = Path(__file__).resolve().parent / "setup_media_keys.py"
    if not helper.is_file():  # pragma: no cover - missing install artifact
        _eprint(
            "nexus-hub setup-media: setup_media_keys.py not found "
            f"at {helper}. Re-run the installer."
        )
        return 2
    return subprocess.run([sys.executable, str(helper), *argv]).returncode


def cmd_map(argv: list[str]) -> int:
    """Dispatch `nexus-hub map` to the nexus-code-search context-map CLI.

    Late-imports the extension so this network-capable CLI core does not pull in
    the code-search package on every invocation. The heavy logic lives entirely
    in the extension (`nexus_code_search.contextmap.cli`), so no installer change
    is needed to surface this verb -- this dispatcher is already installed. Adds
    no outbound call (context-map generation is strictly local). Mirrors the
    late-import + pip-hint pattern used by scripts/nexus_hub_affected.py.
    """
    try:
        from nexus_code_search.contextmap.cli import main as map_main
    except ImportError as exc:  # pragma: no cover - missing optional extension
        _eprint(
            "nexus-hub map: nexus-code-search package not installed "
            f"({exc}). Install with `pip install nexus-code-search`."
        )
        return 2
    return map_main(argv)


def cmd_autonomy(argv: list[str]) -> int:
    """Dispatch the autonomy subcommand through its recursively installed module."""
    cli_dir = Path(__file__).resolve().parent
    if str(cli_dir) not in sys.path:
        sys.path.insert(0, str(cli_dir))
    try:
        from lib.autonomy_cli import main as autonomy_main
    except ImportError as exc:  # pragma: no cover - missing install artifact
        _eprint(
            "nexus-hub autonomy: scripts/lib/autonomy_cli.py not found "
            f"({exc}). Re-run the installer."
        )
        return 2
    return autonomy_main(argv)


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
    # Registered only so `nexus-hub --help` lists it; `verify` is intercepted in
    # main() before parsing and its args are forwarded verbatim to the verifier
    # (argparse.REMAINDER mishandles a leading `--flag`, so we slice argv instead).
    sub.add_parser(
        "verify",
        add_help=False,
        help="Verify the installed catalog against the published SHA-256 manifest.",
    )
    # Like `verify`, `setup-media` is intercepted in main() before parsing and its
    # args are forwarded verbatim to the helper; registered here only so
    # `nexus-hub --help` lists it.
    sub.add_parser(
        "setup-media",
        add_help=False,
        help="Configure optional license-free stock-media API keys (e.g. Pexels for stock video).",
    )
    # `map` is intercepted in main() before parsing and forwarded verbatim to the
    # nexus-code-search context-map CLI (its own args: [root] --force --json).
    # Registered here only so `nexus-hub --help` lists it.
    sub.add_parser(
        "map",
        add_help=False,
        help="Compile a committed .nexus/CONTEXT-MAP.md from the local code graph.",
    )
    sub.add_parser(
        "autonomy",
        add_help=False,
        help="Manage project-scoped autonomy with mandatory TTL and safety gates.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)

    # `verify` forwards every remaining token to the verifier verbatim, so its
    # own flags (--root/--manifest/--ignore-extra) are never swallowed by this
    # parser. Intercept it before argparse runs (see build_parser for why).
    if raw and raw[0] == "verify":
        return cmd_verify(raw[1:])

    # `setup-media` forwards its remaining tokens to the helper verbatim and runs
    # it as a subprocess (interactive hidden prompt), so intercept before argparse.
    if raw and raw[0] == "setup-media":
        return cmd_setup_media(raw[1:])

    # `map` forwards its remaining tokens ([root] --force --json) to the
    # extension's context-map CLI verbatim, so intercept before argparse.
    if raw and raw[0] == "map":
        return cmd_map(raw[1:])

    # `autonomy` owns a nested verb parser in scripts/lib/autonomy_cli.py, which
    # forwards every operation to the sibling autonomy.py policy engine.
    if raw and raw[0] == "autonomy":
        return cmd_autonomy(raw[1:])

    parser = build_parser()
    args = parser.parse_args(raw)

    if args.version or args.command == "version":
        return cmd_version()
    if args.command == "upgrade":
        return cmd_upgrade(assume_yes=args.yes)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
