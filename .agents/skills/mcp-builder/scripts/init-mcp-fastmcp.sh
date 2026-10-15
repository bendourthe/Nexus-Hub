#!/usr/bin/env bash
# init-mcp-fastmcp.sh - scaffold a FastMCP (Python) MCP server with one example tool.
# Cross-platform sibling: init-mcp-fastmcp.ps1 (PowerShell, same output).
# Bundled with the mcp-builder skill; invoked from SKILL.md instructions.

set -euo pipefail

log_info()  { printf '[INFO]  %s\n' "$*" >&2; }
log_warn()  { printf '[WARN]  %s\n' "$*" >&2; }
log_error() { printf '[ERROR] %s\n' "$*" >&2; }

usage() {
    cat <<'EOF'
Usage: init-mcp-fastmcp.sh <server-name>

Scaffolds a FastMCP (Python) MCP server with:
  - pyproject.toml (mcp[cli] dependency)
  - server.py with one example @mcp.tool() decorated function
  - stdio transport configured by default
  - .gitignore for venv / build artifacts

Requires: python (>= 3.10), pip.
EOF
}

require_command() {
    local cmd="$1"
    local hint="$2"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        log_error "$cmd not detected on PATH."
        log_error "Install via $hint and re-run this script."
        exit 1
    fi
}

check_python_version() {
    local py_version
    py_version=$("$1" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "")
    if [ -z "$py_version" ]; then
        log_error "Could not determine Python version."
        exit 1
    fi
    local major minor
    major=$(echo "$py_version" | cut -d. -f1)
    minor=$(echo "$py_version" | cut -d. -f2)
    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 10 ]; }; then
        log_error "Python 3.10+ required (found $py_version)."
        log_error "FastMCP needs Python 3.10 or newer."
        exit 1
    fi
}

main() {
    if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
        usage
        exit 0
    fi

    local server_name="${1:-}"
    if [ -z "$server_name" ]; then
        log_error "Server name is required."
        usage
        exit 1
    fi

    if [ -e "$server_name" ]; then
        log_error "'$server_name' already exists in the current directory."
        log_error "Pick a different name or remove the existing path."
        exit 1
    fi

    local python_cmd
    if command -v python3 >/dev/null 2>&1; then
        python_cmd="python3"
    elif command -v python >/dev/null 2>&1; then
        python_cmd="python"
    else
        log_error "python / python3 not detected on PATH."
        log_error "Install Python 3.10+ via https://python.org or your platform package manager."
        exit 1
    fi
    check_python_version "$python_cmd"

    log_info "Scaffolding FastMCP server: $server_name"
    mkdir -p "$server_name"
    cd "$server_name"

    log_info "Writing pyproject.toml"
    cat > pyproject.toml <<EOF
[project]
name = "$server_name"
version = "0.1.0"
description = "MCP server scaffolded by mcp-builder"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.0.0",
    "pydantic>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project.scripts]
$server_name = "server:main"
EOF

    log_info "Writing server.py with one example tool"
    cat > server.py <<'PY'
"""MCP server scaffolded by mcp-builder.

Replace the example tool with your own. Apply the pushy-description rule
in each tool's docstring (trigger phrases + SKIP clause).
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("__SERVER_NAME__")


class EchoResult(BaseModel):
    message: str = Field(description="The echoed input message")
    length: int = Field(description="Length of the echoed message in characters")


@mcp.tool()
def echo(message: str) -> EchoResult:
    """Echo a message back to the agent with its character length.

    Use this whenever the user wants to verify the MCP server is reachable
    or wants to test tool invocation end-to-end. Returns the message and its
    length so downstream tools can reason over the structured output.

    SKIP: any production use case - this is a placeholder tool. Replace it
    with the actual capability before registering the MCP server with users.
    """
    return EchoResult(message=message, length=len(message))


def main() -> None:
    """Run the MCP server over stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
PY
    sed -i.bak "s/__SERVER_NAME__/$server_name/" server.py && rm -f server.py.bak

    log_info "Writing .gitignore"
    cat > .gitignore <<'EOF'
__pycache__/
*.pyc
.venv/
venv/
build/
dist/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
EOF

    log_info "Creating virtual environment at .venv/"
    "$python_cmd" -m venv .venv

    log_info "Installing mcp[cli] into the venv"
    if [ -f .venv/bin/pip ]; then
        .venv/bin/pip install --quiet --upgrade pip
        .venv/bin/pip install --quiet "mcp[cli]>=1.0.0" "pydantic>=2.0.0"
    else
        log_warn "Could not locate .venv/bin/pip; skipping install. Run 'pip install -e .' manually."
    fi

    log_info "Scaffold complete."
    cat <<EOF

Next steps:
  cd $server_name
  source .venv/bin/activate
  python server.py            # runs the server over stdio
  mcp dev server.py           # opens the MCP Inspector at http://localhost:5173

Replace the echo tool with your real capability, then register the server
in each AI CLI's settings.json (see mcp-builder/SKILL.md Step 6).
EOF
}

main "$@"
