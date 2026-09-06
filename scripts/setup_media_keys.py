#!/usr/bin/env python3
"""setup_media_keys.py - guided, opt-in bring-your-own-key setup for optional
license-free stock-media API keys (currently Pexels, for stock VIDEO).

Run via `nexus-hub setup-media`. It explains that stock IMAGES need no setup
(the default source, Openverse, is keyless) while stock VIDEO needs a free Pexels
key, then captures the key with a HIDDEN terminal prompt (getpass - never echoed,
never recorded in shell history) and persists it once to
~/.nexus-hub/config/media.env at mode 0600, outside any repository.
fetch_stock_media.py reads that file (via _resolve_pexels_key) as a fallback to
the PEXELS_API_KEY environment variable.

Security (see catalog/rules/bash/security.md):
  - The key is NEVER accepted as a command-line argument (that would land in
    shell history); the hidden prompt is the only input path.
  - The key value is NEVER echoed or logged; only a masked form (...<last4>) is
    ever printed.
  - The file is written with restrictive permissions (0600 on POSIX; best-effort
    on Windows, which has no exact chmod equivalent) and lives under the user's
    home, never in a repo.
  - stdlib-only; no third-party import; no network validation of the key.

Exit codes:
    0  the key was captured and stored.
    1  cancelled (EOF / interrupt) or the entered value failed the local sanity
       check (empty, whitespace, or implausibly short). Nothing is stored.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

PEXELS_SIGNUP_URL = "https://www.pexels.com/api/"
KEY_NAME = "PEXELS_API_KEY"
MIN_KEY_LEN = 16


def config_dir() -> Path:
    """`~/.nexus-hub/config`, overridable via NEXUS_HUB_HOME (matches the CLI)."""
    override = os.environ.get("NEXUS_HUB_HOME")
    base = Path(override) if override else Path.home() / ".nexus-hub"
    return base / "config"


def mask_key(key: str) -> str:
    """A safe, non-reversible display form: the last 4 characters only."""
    tail = key[-4:] if len(key) >= 4 else ""
    return f"...{tail}" if tail else "(set)"


def sanity_check(key: str) -> str | None:
    """Return an error message if the key is implausible, else None.

    Local only - no network validation. Catches the obvious paste mistakes
    (empty, embedded whitespace, far too short) without rejecting a real key.
    """
    if not key:
        return "no key entered (empty input)"
    if any(c.isspace() for c in key):
        return "the key contains whitespace; paste the raw key with no spaces"
    if len(key) < MIN_KEY_LEN:
        return f"the key looks too short ({len(key)} chars); a Pexels key is ~56 chars"
    return None


def upsert_env_line(existing: str, name: str, value: str) -> str:
    """Return media.env text with `name=value` set, preserving all other lines.

    Replaces the first existing top-level `name=` line; appends when absent.
    Blank lines and `#` comments are carried through untouched.
    """
    out: list[str] = []
    replaced = False
    for line in existing.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            if stripped.split("=", 1)[0].strip() == name:
                out.append(f"{name}={value}")
                replaced = True
                continue
        out.append(line)
    if not replaced:
        out.append(f"{name}={value}")
    return "\n".join(out).strip() + "\n"


def write_key(value: str) -> Path:
    """Upsert `PEXELS_API_KEY` into ~/.nexus-hub/config/media.env at mode 0600."""
    cfg = config_dir()
    cfg.mkdir(parents=True, exist_ok=True)
    path = cfg / "media.env"
    existing = ""
    if path.exists():
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError:
            existing = ""
    path.write_text(upsert_env_line(existing, KEY_NAME, value), encoding="utf-8")
    # Restrictive perms: 0600 on POSIX. Windows has no exact chmod equivalent, so
    # this is best-effort there; the file already lives under the user profile.
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def main(argv: list[str] | None = None) -> int:
    # Deliberately NO key argument: a key on the command line would be recorded
    # in shell history. The hidden prompt below is the ONLY input path.
    argparse.ArgumentParser(
        prog="nexus-hub setup-media",
        description=(
            "Configure optional license-free stock-media API keys (e.g. Pexels "
            "for stock video). The key is entered via a hidden prompt and is "
            "never passed as an argument."
        ),
    ).parse_args(argv)

    print("Nexus-Hub media-key setup")
    print("-------------------------")
    print("Stock IMAGES need no setup - the default source (Openverse) is keyless.")
    print("Stock VIDEO needs a free Pexels API key (Pexels is the only license-clean")
    print("free video source). Creating one takes ~30 seconds at:")
    print(f"    {PEXELS_SIGNUP_URL}")
    print()
    print("The key is stored locally at ~/.nexus-hub/config/media.env (mode 0600)")
    print("and read by the stock-media fetch as a fallback to the PEXELS_API_KEY")
    print("environment variable. This tool never sends the key anywhere.")
    print()

    try:
        key = getpass.getpass("Paste your Pexels API key (input hidden): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled; no key stored.", file=sys.stderr)
        return 1

    error = sanity_check(key)
    if error:
        print(f"Not stored: {error}.", file=sys.stderr)
        return 1

    path = write_key(key)
    print(f"\nStored {KEY_NAME} ({mask_key(key)}) at {path}")
    print("Stock video will now work when you choose the stock / mix imagery tier")
    print("AND consent to the build-time fetch (the key does not bypass consent).")
    print("To remove it, delete that line from the file (or delete the file).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
