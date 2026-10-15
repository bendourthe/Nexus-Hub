# init-artifact.ps1 - scaffold a Vite + React + TypeScript + Tailwind v4 + shadcn/ui web artifact.
# Cross-platform sibling: init-artifact.sh (Bash, same output).
# Bundled with the web-artifacts-builder skill; invoked from SKILL.md instructions.

[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$ProjectName,

    [switch]$Help
)

$ErrorActionPreference = 'Stop'

function Write-LogInfo  { param($Message) Write-Host "[INFO]  $Message" }
function Write-LogWarn  { param($Message) Write-Warning $Message }
function Write-LogError { param($Message) Write-Error $Message -ErrorAction Continue }

function Show-Usage {
    @"
Usage: init-artifact.ps1 -ProjectName <name>

Scaffolds a multi-component HTML artifact using:
  - Vite (build tool)
  - React 18+ with TypeScript (strict)
  - Tailwind CSS v4 (via @tailwindcss/vite plugin)
  - shadcn/ui (initialized with the New York style + Slate base)

Requires: node (>= 20), npm (>= 10).
"@ | Write-Host
}

function Test-Command {
    param([string]$Command, [string]$Hint)
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        Write-LogError "$Command not detected on PATH."
        Write-LogError "Install via $Hint and re-run this script."
        exit 1
    }
}

if ($Help) {
    Show-Usage
    exit 0
}

if ([string]::IsNullOrWhiteSpace($ProjectName)) {
    Write-LogError "Project name is required."
    Show-Usage
    exit 1
}

if (Test-Path -Path $ProjectName) {
    Write-LogError "'$ProjectName' already exists in the current directory."
    Write-LogError "Pick a different name or remove the existing path."
    exit 1
}

Test-Command -Command 'node' -Hint 'https://nodejs.org or your platform package manager'
Test-Command -Command 'npm'  -Hint 'https://nodejs.org or your platform package manager'

Write-LogInfo "Scaffolding Vite + React + TypeScript project: $ProjectName"
& npm create vite@latest $ProjectName -- --template react-ts
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-LogInfo "Entering project directory: $ProjectName"
Set-Location -Path $ProjectName

Write-LogInfo "Installing base dependencies"
& npm install
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-LogInfo "Installing Tailwind CSS v4 via @tailwindcss/vite plugin"
& npm install -D tailwindcss @tailwindcss/vite
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-LogInfo "Wiring Tailwind into vite.config.ts"
$viteConfig = @'
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
});
'@
Set-Content -Path 'vite.config.ts' -Value $viteConfig -Encoding utf8

Write-LogInfo "Replacing src/App.css with Tailwind import"
$appCss = @'
@import "tailwindcss";

@theme {
  /* Wire theme-tokens here:
   * --color-primary, --color-secondary, --color-accent,
   * --color-background, --color-foreground, --color-muted,
   * --font-heading, --font-body, --font-mono,
   * --radius, --shadow.
   */
}
'@
Set-Content -Path 'src/App.css' -Value $appCss -Encoding utf8

Write-LogInfo "Initializing shadcn/ui (New York style, Slate base)"
try {
    & npx --yes shadcn@latest init --defaults --silent 2>$null
} catch {
    Write-LogWarn "shadcn init produced output or prompts; review the project root and re-run interactively if needed."
}

Write-LogInfo "Trimming default Vite demo content"
$appTsx = @'
function App() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <h1 className="text-3xl font-semibold">Hello, web artifact.</h1>
    </main>
  );
}

export default App;
'@
Set-Content -Path 'src/App.tsx' -Value $appTsx -Encoding utf8

Write-LogInfo "Scaffold complete."
@"

Next steps:
  Set-Location $ProjectName
  npm run dev

Add shadcn components on demand:
  npx shadcn@latest add button card dialog input

Tailwind theme tokens go in: src/App.css inside the @theme { ... } block.
"@ | Write-Host
