"""Module entry point: ``python -m nexus_context_compressor [SUBCOMMAND]``.

Delegates to :mod:`nexus_context_compressor.cli`. With no subcommand it prints
package identity and the active token-counting mode (preserving the Phase 1
behavior). The runtime subcommands are:

* ``compress``  -- compress raw tool output read from stdin (the PreToolUse hook
  pipes a command's output through this).
* ``retrieve``  -- resolve a ``<<ccr:HASH N_rows>>`` marker back to its originals.
* ``serve``     -- launch the internal MCP server (needs the optional ``mcp`` extra).

Per-strategy entry points (e.g. ``python -m nexus_context_compressor.smart_crusher``)
remain available on their own modules.
"""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
