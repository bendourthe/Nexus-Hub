"""Entrypoint for `python -m devai_code_search`."""
from __future__ import annotations

import asyncio

from devai_code_search.server import run_server


def main() -> None:
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
