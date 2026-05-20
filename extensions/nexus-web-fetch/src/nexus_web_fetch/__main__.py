"""Entrypoint for `python -m nexus_web_fetch`."""
from __future__ import annotations

import asyncio

from nexus_web_fetch.server import run_server


def main() -> None:
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
