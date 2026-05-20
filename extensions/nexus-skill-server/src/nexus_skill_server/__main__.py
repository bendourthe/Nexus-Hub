from __future__ import annotations

import asyncio

from nexus_skill_server.server import run_server


def main() -> None:
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
