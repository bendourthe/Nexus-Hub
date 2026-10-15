# init-mcp-ts.ps1 - scaffold a Node / TypeScript MCP server (official @modelcontextprotocol/sdk).
# Cross-platform sibling: init-mcp-ts.sh (Bash, same output).
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
Usage: init-mcp-ts.ps1 -ServerName <name>

Scaffolds a Node / TypeScript MCP server with:
  - package.json (@modelcontextprotocol/sdk + zod dependencies)
  - tsconfig.json (ESM, ES2022)
  - src/server.ts with one example server.tool() registration
  - stdio transport configured by default

Requires: node (>= 20), npm (>= 10).
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

function Test-NodeVersion {
    $version = (node -v 2>$null)
    if (-not $version) {
        Write-LogError "Could not determine Node version."
        exit 1
    }
    $version = $version.TrimStart('v')
    $parts = $version -split '\.'
    $major = [int]$parts[0]
    if ($major -lt 20) {
        Write-LogError "Node 20+ required (found $version)."
        Write-LogError "The MCP TypeScript SDK requires Node 20 or newer."
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

Test-CommandAvailable -Command 'node' -Hint 'https://nodejs.org or your platform package manager'
Test-CommandAvailable -Command 'npm'  -Hint 'https://nodejs.org or your platform package manager'
Test-NodeVersion

Write-LogInfo "Scaffolding TS MCP server: $ServerName"
New-Item -ItemType Directory -Path $ServerName | Out-Null
New-Item -ItemType Directory -Path (Join-Path $ServerName 'src') | Out-Null
Set-Location -Path $ServerName

Write-LogInfo "Writing package.json"
@"
{
  "name": "$ServerName",
  "version": "0.1.0",
  "description": "MCP server scaffolded by mcp-builder",
  "type": "module",
  "main": "build/server.js",
  "bin": {
    "$ServerName": "build/server.js"
  },
  "scripts": {
    "build": "tsc",
    "dev": "tsx src/server.ts",
    "start": "node build/server.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "tsx": "^4.7.0",
    "typescript": "^5.4.0",
    "@types/node": "^20.0.0"
  },
  "engines": {
    "node": ">=20"
  }
}
"@ | Set-Content -Path 'package.json' -Encoding utf8

Write-LogInfo "Writing tsconfig.json"
@'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "outDir": "./build",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": false,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "build"]
}
'@ | Set-Content -Path 'tsconfig.json' -Encoding utf8

Write-LogInfo "Writing src/server.ts with one example tool"
$serverTs = @'
/**
 * MCP server scaffolded by mcp-builder.
 *
 * Replace the example tool with your own. Apply the pushy-description rule
 * in each tool's .describe() calls (trigger phrases + SKIP clause).
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
    name: "__SERVER_NAME__",
    version: "0.1.0",
});

server.tool(
    "echo",
    {
        message: z.string().describe("Message to echo back"),
    },
    async ({ message }) => {
        const result = { message, length: message.length };
        return {
            content: [
                { type: "text", text: JSON.stringify(result) },
            ],
            structuredContent: result,
        };
    },
);

const transport = new StdioServerTransport();
await server.connect(transport);
'@
$serverTs = $serverTs -replace '__SERVER_NAME__', $ServerName
$serverTs | Set-Content -Path (Join-Path 'src' 'server.ts') -Encoding utf8

Write-LogInfo "Writing .gitignore"
@'
node_modules/
build/
*.log
.DS_Store
'@ | Set-Content -Path '.gitignore' -Encoding utf8

Write-LogInfo "Installing dependencies"
npm install --silent

Write-LogInfo "Scaffold complete."
@"

Next steps:
  cd $ServerName
  npm run dev                                         # runs the server over stdio (tsx)
  npx @modelcontextprotocol/inspector npm run dev     # launches the MCP Inspector

To build for production:
  npm run build && npm start

Replace the echo tool with your real capability, then register the server
in each AI CLI's settings.json (see mcp-builder/SKILL.md Step 6).
"@ | Write-Host
