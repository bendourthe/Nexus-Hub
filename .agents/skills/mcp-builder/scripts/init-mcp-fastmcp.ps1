# init-mcp-fastmcp.ps1 - scaffold a FastMCP (Python) MCP server with one example tool.
# Cross-platform sibling: init-mcp-fastmcp.sh (Bash, same output).
# Bundled with the mcp-builder skill; invoked from SKILL.md instructions.

[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$ServerName,

    [switch]$Help
)

$ErrorActionPreference = 'Stop'

function Write-LogInfo  { param($Message) Write-Host "[INFO]  $Message" }
function Write-LogWarn  { param($Message) Write-Warning $Message }
function Write-LogError { param($Message) Write-Error $Message -ErrorAction Continue }

function Show-Usage {
    @"
Usage: init-mcp-fastmcp.ps1 -ServerName <name>

Scaffolds a FastMCP (Python) MCP server with:
  - pyproject.toml (mcp[cli] dependency)
  - server.py with one example @mcp.tool() decorated function
  - stdio transport configured by default
  - .gitignore for venv / build artifacts

Requires: python (>= 3.10), pip.
"@ | Write-Host
}

function Test-CommandAvailable {
    param([string]$Command, [string]$Hint)
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        Write-LogError "$Command not detected on PATH."
        Write-LogError "Install via $Hint and re-run this script."
        exit 1
    }
}

function Test-PythonVersion {
    param([string]$PythonCmd)
    $version = & $PythonCmd -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>$null
    if (-not $version) {
        Write-LogError "Could not determine Python version."
        exit 1
    }
    $parts = $version -split '\.'
    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    if (($major -lt 3) -or (($major -eq 3) -and ($minor -lt 10))) {
        Write-LogError "Python 3.10+ required (found $version)."
        Write-LogError "FastMCP needs Python 3.10 or newer."
        exit 1
    }
}

if ($Help) {
    Show-Usage
    exit 0
}

if ([string]::IsNullOrWhiteSpace($ServerName)) {
    Write-LogError "Server name is required."
    Show-Usage
    exit 1
}

if (Test-Path -LiteralPath $ServerName) {
    Write-LogError "'$ServerName' already exists in the current directory."
    Write-LogError "Pick a different name or remove the existing path."
    exit 1
}

$pythonCmd = $null
if (Get-Command 'python' -ErrorAction SilentlyContinue) {
    $pythonCmd = 'python'
} elseif (Get-Command 'python3' -ErrorAction SilentlyContinue) {
    $pythonCmd = 'python3'
} else {
    Write-LogError "python / python3 not detected on PATH."
    Write-LogError "Install Python 3.10+ via https://python.org or your platform package manager."
    exit 1
}
Test-PythonVersion -PythonCmd $pythonCmd

Write-LogInfo "Scaffolding FastMCP server: $ServerName"
New-Item -ItemType Directory -Path $ServerName | Out-Null
Set-Location -Path $ServerName

Write-LogInfo "Writing pyproject.toml"
@"
[project]
name = "$ServerName"
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
$ServerName = "server:main"
"@ | Set-Content -Path 'pyproject.toml' -Encoding utf8

Write-LogInfo "Writing server.py with one example tool"
$serverPy = @'
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
'@
$serverPy = $serverPy -replace '__SERVER_NAME__', $ServerName
$serverPy | Set-Content -Path 'server.py' -Encoding utf8

Write-LogInfo "Writing .gitignore"
@'
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
'@ | Set-Content -Path '.gitignore' -Encoding utf8

Write-LogInfo "Creating virtual environment at .venv/"
& $pythonCmd -m venv .venv

Write-LogInfo "Installing mcp[cli] into the venv"
$venvPip = Join-Path '.venv' (Join-Path 'Scripts' 'pip.exe')
if (Test-Path -LiteralPath $venvPip) {
    & $venvPip install --quiet --upgrade pip
    & $venvPip install --quiet 'mcp[cli]>=1.0.0' 'pydantic>=2.0.0'
} else {
    Write-LogWarn "Could not locate .venv\Scripts\pip.exe; skipping install. Run 'pip install -e .' manually."
}

Write-LogInfo "Scaffold complete."
@"

Next steps:
  cd $ServerName
  .\.venv\Scripts\Activate.ps1
  python server.py            # runs the server over stdio
  mcp dev server.py           # opens the MCP Inspector at http://localhost:5173

Replace the echo tool with your real capability, then register the server
in each AI CLI's settings.json (see mcp-builder/SKILL.md Step 6).
"@ | Write-Host
