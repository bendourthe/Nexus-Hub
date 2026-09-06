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
                               (a pinned install refuses to move unless --latest
                               or --ref <tag> is given; see Pinned installs below)
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
    nexus-hub org              Connect, synchronize, inspect, or disconnect an
                               organization knowledge bundle from a local directory
                               or user-selected Git remote.
    nexus-hub --help           Usage.

The `upgrade` command calls only the project's own GitHub. The opt-in `org
connect` and `org sync` commands may call the Git remote the user explicitly
selects, using the user's installed Git client and existing credential helper.
No third-party data processor, new credential, or new dependency is introduced.
The upgrade fetch prefers `curl`, falls back to `wget`, and finally to the Python
stdlib `urllib` so it works on a bare machine; a `file://` source (used by the
tests) is read directly without any network tool.

Internal testing affordances (environment variables):

    NEXUS_HUB_HOME            install root to read VERSION from   (default: ~/.nexus-hub)
    NEXUS_HUB_REPO            owner/name slug        (default: bendourthe/Nexus-Hub)
    NEXUS_HUB_REF             git ref to check against            (default: main)
                              The install bootstrap reads the same variable, and
                              `upgrade --ref` / `--latest` set it for the re-run.
    NEXUS_HUB_RAW_BASE        override the raw.githubusercontent base (a URL or a
                              local/`file://` dir holding plugin.json + CHANGELOG.md)
    NEXUS_HUB_INSTALL_BASE    override the install.sh/.ps1 base URL the upgrade re-runs
    NEXUS_HUB_UPGRADE_DRY_RUN=1  print the bootstrap command instead of executing it
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_REPO = "bendourthe/Nexus-Hub"
DEFAULT_REF = "main"

# A semantic-version token. Mirrors the one in check_version_sync.py so the CLI
# reads exactly the surfaces that guard writes.
_SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")
_PLUGIN_VERSION_RE = re.compile(r'"version"\s*:\s*"([^"]+)"')
_GIT_URL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
_GIT_SCP_RE = re.compile(r"^[^@\s]+@[^:\s]+:.+")
ORG_CONNECTION_SCHEMA_VERSION = 1


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


PINNED_REF_FILE = "PINNED_REF"


def pinned_ref() -> str | None:
    """The tag the install bootstrap pinned this install to, or None when unpinned.

    The bootstrap writes `~/.nexus-hub/PINNED_REF` when it installs a release tag
    (v4.7.0) and removes it when it installs a branch, so `upgrade` can tell a
    deliberately pinned install from one that follows tip-of-branch.
    """
    try:
        value = (install_home() / PINNED_REF_FILE).read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def run_bootstrap(ref: str | None = None) -> int:
    """Re-run the install bootstrap to upgrade in place. Honors the dry-run seam.

    `ref` (a tag such as `v4.7.0`, or a branch) is handed to the bootstrap through
    NEXUS_HUB_REF, the same variable a first install accepts, so a pinned upgrade
    and a first pinned install take one code path.
    """
    command = _bootstrap_command()
    env = dict(os.environ)
    if ref:
        env["NEXUS_HUB_REF"] = ref
    if os.environ.get("NEXUS_HUB_UPGRADE_DRY_RUN") == "1":
        # Show the exact command rather than executing it (used by the tests and
        # by anyone who wants to inspect the re-run before trusting it).
        printable = command[-1] if command and command[0] in {"bash", "powershell"} else " ".join(command)
        print(f"[dry-run] would upgrade by running: {printable}")
        print(f"[dry-run] NEXUS_HUB_REF={env.get('NEXUS_HUB_REF', 'main')}")
        return 0
    _eprint("Upgrading by re-running the install bootstrap...")
    return subprocess.run(command, env=env, check=False).returncode


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


def cmd_upgrade(assume_yes: bool, to_ref: str | None = None, to_latest: bool = False) -> int:
    """Compare installed vs latest; show what's new; offer the in-place upgrade.

    Pinned installs (v4.7.0): when the bootstrap pinned this install to a tag,
    `upgrade` REFUSES to move it unless told where. `--latest` re-pins to the
    newest release tag (`v<latest>`, so the download stays verifiable), `--ref`
    moves to the named tag or branch (which is also the rollback path). Moving
    silently to tip-of-branch was rejected: a user who asked to pin and was
    quietly unpinned by `upgrade` is worse off than one who received a refusal.
    """
    installed = read_installed_version()
    installed_label = installed or "unknown"
    pinned = pinned_ref()

    if to_ref:
        print(f"Installed: {installed_label}" + (f" (pinned to {pinned})" if pinned else ""))
        print(f"Target:    {to_ref}")
        if not _confirm_upgrade(assume_yes):
            print("\nUpgrade skipped.")
            return 0
        return run_bootstrap(to_ref)

    try:
        latest = fetch_latest_version()
    except FetchError as exc:
        # Offline / fetch failure: clear message, non-zero exit, NO partial state
        # (nothing has been changed at this point).
        _eprint(f"nexus-hub upgrade: could not reach the project's GitHub -- {exc}")
        _eprint("Check your network connection and try again.")
        return 2

    print(f"Installed: {installed_label}" + (f" (pinned to {pinned})" if pinned else ""))
    print(f"Latest:    {latest}")

    if pinned and not to_latest:
        _eprint(
            f"nexus-hub upgrade: this install is pinned to {pinned}. Nothing was changed.\n"
            f"  To move to the latest release:   nexus-hub upgrade --latest\n"
            f"  To move to another version:      nexus-hub upgrade --ref v{latest}\n"
            f"  To roll back:                    nexus-hub upgrade --ref <older tag>"
        )
        return 3

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

    # A pinned install moves to the newest RELEASE TAG, never to tip-of-branch,
    # so the re-run stays on the verifiable artifact path.
    return run_bootstrap(f"v{latest}" if pinned else None)


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


# --- Organization knowledge connection -------------------------------------


class OrgCliError(Exception):
    """An expected organization CLI failure with a user-actionable message."""


def _org_root() -> Path:
    """Return the Nexus-Hub-owned organization state directory."""

    return install_home() / "org"


def _org_connection_path() -> Path:
    return _org_root() / "connection.json"


def _org_repo_path() -> Path:
    return _org_root() / "repo"


def _utc_now() -> str:
    """Return a stable UTC timestamp for the connection record."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _looks_like_git_url(value: str) -> bool:
    """Distinguish explicit Git remotes from local filesystem paths."""

    return bool(_GIT_URL_RE.match(value) or _GIT_SCP_RE.match(value))


def sanitize_branch_name(raw: str) -> str:
    """Map a branch name to the installer's filesystem-safe cache token."""

    sanitized = re.sub(r"[^A-Za-z0-9._-]", "-", raw)
    sanitized = sanitized.replace("..", "-")
    sanitized = re.sub(r"^[-.]", "", sanitized, count=1)
    return sanitized or "branch"


def _resolve_org_path(value: str) -> Path:
    """Resolve an existing local bundle directory without accepting null bytes."""

    if "\x00" in value:
        raise ValueError(f"Null byte in path: {value!r}")
    try:
        path = Path(value).expanduser().resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f"Organization bundle path does not exist: {value}") from exc
    if not path.is_dir():
        raise ValueError(f"Organization bundle path is not a directory: {path}")
    return path


def _load_org_knowledge():
    """Load the validator from the installed ``scripts/lib`` tree on demand.

    Both launchers execute this file from ``~/.nexus-hub/scripts`` and both
    installers recursively copy ``scripts/lib`` beside it. Adding the exact
    integrations directory to ``sys.path`` loads only the standalone validator,
    avoiding the broad ``lib.integrations`` registry import and any dependency
    on the caller's current working directory.
    """

    integrations_dir = str(Path(__file__).resolve().parent / "lib" / "integrations")
    if integrations_dir not in sys.path:
        sys.path.insert(0, integrations_dir)
    try:
        org_knowledge = importlib.import_module("org_knowledge")
    except ImportError as exc:  # pragma: no cover - missing install artifact
        raise OrgCliError(
            "organization validator not found; re-run the Nexus-Hub installer"
        ) from exc
    return org_knowledge


def _write_org_connection(state: dict[str, Any]) -> None:
    """Atomically replace ``connection.json`` with one complete JSON object."""

    root = _org_root()
    root.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=".connection.",
            suffix=".tmp",
            dir=root,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        destination = _org_connection_path()
        for attempt in range(5):
            try:
                os.replace(temporary, destination)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                # Concurrent Windows replacements can briefly hold the target.
                # Retrying the same atomic operation preserves last-writer-wins.
                time.sleep(0.01 * (attempt + 1))
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _read_org_connection() -> dict[str, Any] | None:
    """Read and minimally validate the connection record."""

    path = _org_connection_path()
    if not path.exists():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OrgCliError(
            f"cannot read organization connection at {path}: {exc}"
        ) from exc
    if not isinstance(state, dict):
        raise OrgCliError(f"organization connection at {path} is not a JSON object")
    required = {
        "schema_version",
        "source_type",
        "source",
        "branch",
        "connected_at",
        "last_sync",
    }
    missing = sorted(required - set(state))
    if missing:
        raise OrgCliError(
            "organization connection is missing required fields: " + ", ".join(missing)
        )
    if state["schema_version"] != ORG_CONNECTION_SCHEMA_VERSION:
        raise OrgCliError(
            f"unsupported organization connection schema: {state['schema_version']!r}"
        )
    if state["source_type"] not in {"dir", "git"}:
        raise OrgCliError(
            f"unsupported organization source type: {state['source_type']!r}"
        )
    return state


def _diagnostic_tail(proc: subprocess.CompletedProcess[str]) -> str:
    """Return one useful line from a failed Git subprocess."""

    lines = [
        line.strip()
        for line in f"{proc.stderr}\n{proc.stdout}".splitlines()
        if line.strip()
    ]
    return lines[-1] if lines else f"git exited with status {proc.returncode}"


def _run_git(arguments: list[str], action: str) -> None:
    """Run Git through an argument list, never a shell-interpolated command."""

    try:
        proc = subprocess.run(
            ["git", *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        raise OrgCliError(f"{action} failed: git is unavailable ({exc})") from exc
    if proc.returncode != 0:
        raise OrgCliError(f"{action} failed: {_diagnostic_tail(proc)}")


def _remove_owned_path(path: Path) -> None:
    """Remove one exact Nexus-Hub-owned cache path."""

    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():

        def make_writable_and_retry(function, blocked_path, _exc_info):
            os.chmod(blocked_path, stat.S_IWRITE)
            function(blocked_path)

        shutil.rmtree(path, onerror=make_writable_and_retry)
    else:
        path.unlink()


def _replace_org_repo(candidate: Path) -> None:
    """Replace the cached clone while restoring the old cache on rename failure."""

    destination = _org_repo_path()
    backup = _org_root() / f".repo-backup-{uuid.uuid4().hex}"
    had_destination = destination.exists() or destination.is_symlink()
    if had_destination:
        os.replace(destination, backup)
    try:
        os.replace(candidate, destination)
    except BaseException:
        if had_destination and backup.exists():
            os.replace(backup, destination)
        raise
    if backup.exists() or backup.is_symlink():
        _remove_owned_path(backup)


def _validate_org_bundle(path: Path):
    validator = _load_org_knowledge()
    return validator.validate_bundle(path)


def _print_org_report(report) -> None:
    for warning in report.warnings:
        _eprint(f"warning: {warning}")
    for error in report.errors:
        _eprint(f"error: {error}")


def _confirm_org_action(prompt: str, override: bool, flag: str) -> bool:
    """Confirm a destructive replacement/removal, failing closed off-terminal."""

    if override:
        return True
    if not sys.stdin.isatty():
        _eprint(f"nexus-hub org: confirmation required; re-run with {flag}")
        return False
    try:
        answer = input(f"{prompt} [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in {"y", "yes"}


def _connect_org(source: str, branch: str | None, force: bool) -> int:
    connection_path = _org_connection_path()
    if connection_path.exists() and not _confirm_org_action(
        "Replace the existing organization connection?", force, "--force"
    ):
        return 2

    source_type = "git" if _looks_like_git_url(source) else "dir"
    bundle_path: Path
    candidate: Path | None = None
    try:
        if source_type == "git":
            root = _org_root()
            root.mkdir(parents=True, exist_ok=True)
            token = sanitize_branch_name(branch or "default")
            candidate = Path(tempfile.mkdtemp(prefix=f".repo-{token}-", dir=root))
            clone_args = ["clone", "--depth", "1"]
            if branch:
                clone_args.extend(["--branch", branch])
            clone_args.extend(["--", source, str(candidate)])
            _run_git(clone_args, "git clone")
            bundle_path = candidate
        else:
            if branch:
                raise OrgCliError("--branch is valid only for Git organization sources")
            try:
                bundle_path = _resolve_org_path(source)
            except ValueError as exc:
                raise OrgCliError(str(exc)) from exc

        report = _validate_org_bundle(bundle_path)
        _print_org_report(report)
        if not report.valid:
            return 2
        if source_type == "git" and candidate is not None:
            _replace_org_repo(candidate)
            candidate = None

        timestamp = _utc_now()
        _write_org_connection(
            {
                "schema_version": ORG_CONNECTION_SCHEMA_VERSION,
                "source_type": source_type,
                "source": source if source_type == "git" else str(bundle_path),
                "branch": branch,
                "connected_at": timestamp,
                "last_sync": timestamp,
            }
        )
    except (OrgCliError, OSError) as exc:
        _eprint(f"nexus-hub org connect: {exc}")
        return 2
    finally:
        if candidate is not None and (candidate.exists() or candidate.is_symlink()):
            _remove_owned_path(candidate)

    print(f"Connected organization bundle: {source}")
    print(report.summary())
    return 0


def _sync_org() -> int:
    try:
        state = _read_org_connection()
        if state is None:
            raise OrgCliError(
                "no organization bundle is connected; run `nexus-hub org connect <path-or-url>`"
            )
        if state["source_type"] == "git":
            bundle_path = _org_repo_path()
            if not bundle_path.is_dir():
                raise OrgCliError(
                    f"cached organization repository is missing: {bundle_path}"
                )
            _run_git(["-C", str(bundle_path), "pull", "--ff-only"], "git pull")
        else:
            try:
                bundle_path = _resolve_org_path(str(state["source"]))
            except ValueError as exc:
                raise OrgCliError(str(exc)) from exc

        report = _validate_org_bundle(bundle_path)
        _print_org_report(report)
        if not report.valid:
            return 2
        state["last_sync"] = _utc_now()
        _write_org_connection(state)
    except (OrgCliError, OSError) as exc:
        _eprint(f"nexus-hub org sync: {exc}")
        return 2

    print("Organization bundle synchronized.")
    print(report.summary())
    return 0


def _status_org() -> int:
    returncode = 0
    try:
        org = _load_org_knowledge()
        state = _read_org_connection()
        if state is None:
            print(
                "Organization knowledge is not connected. Run `nexus-hub org connect <path-or-url>`."
            )
            returncode = 1
            report = None
        else:
            bundle_path = (
                _org_repo_path()
                if state["source_type"] == "git"
                else _resolve_org_path(str(state["source"]))
            )
            report = _validate_org_bundle(bundle_path)
    except (OrgCliError, OSError, ValueError) as exc:
        _eprint(f"nexus-hub org status: {exc}")
        return 2

    if state is not None and report is not None:
        print("Organization knowledge connection")
        print(f"Source type: {state['source_type']}")
        print(f"Source: {state['source']}")
        print(f"Branch: {state['branch'] or '(default)'}")
        print(f"Connected at: {state['connected_at']}")
        print(f"Last sync: {state['last_sync']}")
        print(report.summary())
        _print_org_report(report)
        if not report.valid:
            returncode = 2

    print("Platform posture (all registered platforms; installation not required)")
    print(f"{'Platform':<18} {'Posture':<26} Justification")
    for key, classification, justification in org.platform_posture_rows():
        print(f"{key:<18} {classification:<26} {justification}")
    print(
        "These projections are instructions, not enforcement. Use the "
        "org-standards-authoring escalation guidance for platform-native managed policy."
    )
    return returncode


def _cleanup_installed_org_artifacts() -> int:
    """Remove organization artifacts owned by the installed global manifest."""

    manifest_path = install_home() / "install-manifest.json"
    if not manifest_path.exists():
        return 0
    package_root = str(Path(__file__).resolve().parent.parent)
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    try:
        from scripts.lib.integrations.base import InstallContext
        from scripts.lib.integrations.manifest import InstallManifest
        from scripts.lib.integrations.org_knowledge import remove_org_knowledge
    except ImportError as exc:  # pragma: no cover - incomplete installed tree
        raise OrgCliError(
            "organization lifecycle helpers not found; re-run the Nexus-Hub installer"
        ) from exc

    manifest = InstallManifest.load(manifest_path)
    context = InstallContext(
        repo_root=install_home() / "src",
        target_root=Path.home(),
        scope="global",
        overwrite=True,
        dry_run=False,
        manifest=manifest,
    )
    removed = 0
    for key in manifest.all_org_keys():
        removed += sum(
            action.action == "removed"
            for action in remove_org_knowledge(key, context)
        )
    manifest.save(manifest_path)
    return removed


def _disconnect_org(assume_yes: bool) -> int:
    connection = _org_connection_path()
    repository = _org_repo_path()
    if not connection.exists() and not repository.exists():
        print("Organization knowledge is already disconnected.")
        return 0
    if not _confirm_org_action(
        "Disconnect organization knowledge and remove its cached clone?",
        assume_yes,
        "--yes",
    ):
        return 2
    try:
        removed = _cleanup_installed_org_artifacts()
        if connection.exists() or connection.is_symlink():
            connection.unlink()
        _remove_owned_path(repository)
    except (OSError, OrgCliError, ValueError) as exc:
        _eprint(f"nexus-hub org disconnect: {exc}")
        return 2
    print("Organization knowledge disconnected.")
    if removed:
        print(f"Removed {removed} organization artifact(s) from the global install.")
    print("Workspace organization artifacts are removed on the next install or repair.")
    return 0


def _org_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-hub org",
        description="Manage an organization knowledge bundle connection.",
    )
    actions = parser.add_subparsers(dest="org_command")
    connect = actions.add_parser(
        "connect", help="Connect a local directory or Git remote."
    )
    connect.add_argument("source", help="Bundle directory or Git URL.")
    connect.add_argument("--branch", help="Git branch to clone.")
    connect.add_argument(
        "--force", action="store_true", help="Replace an existing connection."
    )
    actions.add_parser("sync", help="Refresh and revalidate the connected bundle.")
    actions.add_parser("status", help="Show connection and validation status.")
    disconnect = actions.add_parser(
        "disconnect", help="Remove the connection and cached clone."
    )
    disconnect.add_argument(
        "--yes", action="store_true", help="Disconnect without prompting."
    )
    return parser


def cmd_org(argv: list[str]) -> int:
    """Dispatch ``nexus-hub org`` without letting the top-level parser alter args."""

    parser = _org_parser()
    if not argv:
        parser.print_help()
        return 0
    args = parser.parse_args(argv)
    if args.org_command == "connect":
        return _connect_org(args.source, args.branch, args.force)
    if args.org_command == "sync":
        return _sync_org()
    if args.org_command == "status":
        return _status_org()
    if args.org_command == "disconnect":
        return _disconnect_org(args.yes)
    parser.print_help()
    return 0


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
    up.add_argument(
        "--ref",
        help="Install this tag or branch (also the rollback path, e.g. --ref v4.6.0). Required on a pinned install unless --latest is given.",
    )
    up.add_argument(
        "--latest",
        action="store_true",
        help="On a pinned install, move to the newest release tag (verifiable artifact). Unpinned installs already follow the latest.",
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
    # `org` owns a nested parser and accepts paths/URLs that must be forwarded
    # byte-for-byte, so main() intercepts it before the top-level parser.
    sub.add_parser(
        "org",
        add_help=False,
        help="Connect, sync, inspect, or disconnect organization knowledge.",
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

    # `org` accepts a path-or-URL plus its own flags; preserve them verbatim and
    # let the dedicated parser enforce the connection lifecycle contract.
    if raw and raw[0] == "org":
        return cmd_org(raw[1:])

    parser = build_parser()
    args = parser.parse_args(raw)

    if args.version or args.command == "version":
        return cmd_version()
    if args.command == "upgrade":
        return cmd_upgrade(assume_yes=args.yes, to_ref=args.ref, to_latest=args.latest)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
