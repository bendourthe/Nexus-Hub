#!/usr/bin/env python3
"""Thin CLI entry for the nexus-skill-scanner static skill-security engine.

Usage:
    python scripts/scan_skill_security.py <target> [<target> ...] [options]
    python scripts/scan_skill_security.py catalog/skills catalog/mcp-configs --fail-on high

This is a thin launcher: all logic lives in the ``nexus_skill_scanner`` package
under ``extensions/nexus-skill-scanner/``. The launcher imports the package if
it is pip-installed; otherwise it locates the bundled ``src/`` layout (repo
checkout or ``~/.nexus-hub`` install) and runs from there, so the scanner works
without a separate install step.

Local-only and deterministic: zero outbound calls, no LLM client, no API key.
The semantic-adjudication stage is the ``skill-security-scan`` skill, run by the
user's own agent.

Exit codes: 0 = clean / below threshold, 1 = findings at/above --fail-on,
2 = usage or IO error.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_importable() -> None:
    """Make ``nexus_skill_scanner`` importable from a pip install or the bundle."""
    try:
        import nexus_skill_scanner  # noqa: F401
        return
    except ImportError:
        pass
    here = Path(__file__).resolve()
    candidates = [
        # Repo checkout (scripts/ -> ../extensions) AND the ~/.nexus-hub install
        # (both put extensions/ one level up from scripts/).
        here.parent.parent / "extensions" / "nexus-skill-scanner" / "src",
        Path.home() / ".nexus-hub" / "extensions" / "nexus-skill-scanner" / "src",
    ]
    for candidate in candidates:
        if (candidate / "nexus_skill_scanner" / "__init__.py").is_file():
            sys.path.insert(0, str(candidate))
            return
    print(
        "ERROR: the nexus-skill-scanner package could not be located. "
        "Install it with: pip install -e extensions/nexus-skill-scanner",
        file=sys.stderr,
    )
    sys.exit(2)


def main() -> int:
    _ensure_importable()
    from nexus_skill_scanner.cli import main as cli_main

    return cli_main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
