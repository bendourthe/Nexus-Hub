### Step 7: Structure Projects and Packaging

**Modern pyproject.toml Configuration**:

```toml
[project]
name = "myapp"
version = "1.2.0"
description = "A production application"
requires-python = ">=3.11"
license = {text = "MIT"}
dependencies = [
    "pydantic>=2.0,<3.0",
    "httpx>=0.25",
    "asyncpg>=0.29",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-asyncio>=0.23",
    "mypy>=1.8",
    "ruff>=0.3",
]

[project.scripts]
myapp = "myapp.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "TCH"]
```

**src Layout (Recommended)**:

```
myapp/
  pyproject.toml
  src/
    myapp/
      __init__.py
      cli.py
      config.py
      models/
        __init__.py
        user.py
      services/
        __init__.py
        auth.py
      utils/
        __init__.py
        logging.py
  tests/
    unit/
      test_models.py
      test_services.py
    integration/
      test_database.py
    conftest.py
```

**Virtual Environment Management with uv**:

```bash
# Create virtual environment
uv venv

# Install project with dev dependencies
uv pip install -e ".[dev]"

# Add a new dependency
uv pip install httpx

# Sync from lock file (reproducible installs)
uv pip sync requirements.lock

# Generate lock file
uv pip compile pyproject.toml -o requirements.lock
```

**Package Entry Points and CLI**:

```python
# src/myapp/cli.py
from __future__ import annotations

import argparse
import sys

def main(argv: list[str] | None = None) -> int:
    """Application entry point."""
    parser = argparse.ArgumentParser(description="My Application")
    parser.add_argument("--config", default="config.toml", help="Config file path")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="Start the server")
    serve_parser.add_argument("--port", type=int, default=8080)

    migrate_parser = subparsers.add_parser("migrate", help="Run database migrations")
    migrate_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "serve":
        return run_server(args.port, args.config)
    elif args.command == "migrate":
        return run_migrations(args.config, dry_run=args.dry_run)

    return 0

if __name__ == "__main__":
    sys.exit(main())
```
