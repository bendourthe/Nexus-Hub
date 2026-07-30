<#
.SYNOPSIS
    PowerShell parity for escalation-trigger.sh.

.DESCRIPTION
    PreToolUse hook (Write, Edit) that warns when the target file path matches a
    sensitive path pattern, including the execution-trigger config surfaces that
    a trusted component outside the agent sandbox later loads and executes.

    Advisory by default (exit 0 with a warning on stdout). Set
    $env:ESCALATION_MODE = 'block' to exit 2 and block the operation instead.

    Input contract: reads the PreToolUse JSON payload from stdin and takes the
    path from tool_input.file_path (falling back to tool_input.path), matching
    every other Write/Edit hook in this catalog. The legacy
    $env:CLAUDE_FILE_PATH is still honored as a fallback when stdin carries no
    usable path.

    This script mirrors the .sh implementation so Windows users who run hooks
    through PowerShell get the same guardrail.

.NOTES
    Scope: this hook matches FILE PATHS only. Group B of the canonical
    execution-trigger surface list (the core.hooksPath / core.fsmonitor
    command-string patterns) can never appear in a Write/Edit payload and is
    owned by git-guardrails.ps1. Keep the split intact.

    Parity note: PowerShell's -like operator is case-insensitive, while the bash
    `case` glob is case-sensitive. That difference is deliberate and safe here.
    Windows filesystems are case-insensitive, so `.Claude/settings.json` and
    `.claude/settings.json` are the same file; matching case-insensitively is a
    strict superset of the bash behavior and can only warn more, never less.

    Limitation: a fixed glob list is defense-in-depth, not a boundary. It matches
    only the surfaces someone already enumerated, so a novel execution-trigger
    path passes silently. See the "Limits and Honest Boundaries" section of
    catalog/skills/security-operations/agentic-endpoint-hardening/SKILL.md.
#>

# Never fail loudly on internal errors.
$ErrorActionPreference = "Continue"

$escalationMode = if ($env:ESCALATION_MODE) { $env:ESCALATION_MODE } else { "warn" }

# --- Resolve the target path ---
# Primary: the PreToolUse JSON payload on stdin. Fallback: $env:CLAUDE_FILE_PATH.
$filePath = $null
if ([Console]::IsInputRedirected) {
    $raw = [Console]::In.ReadToEnd()
    if ($raw) {
        try {
            $payload = $raw | ConvertFrom-Json
            if ($payload.tool_input) {
                $names = $payload.tool_input.PSObject.Properties.Name
                if ($names -contains 'file_path') {
                    $filePath = $payload.tool_input.file_path
                } elseif ($names -contains 'path') {
                    $filePath = $payload.tool_input.path
                }
            }
        } catch {
            # Malformed JSON: fall through to the environment fallback.
            $filePath = $null
        }
    }
}

if (-not $filePath) { $filePath = $env:CLAUDE_FILE_PATH }
if (-not $filePath) { exit 0 }

# Normalize to forward slashes for consistent matching.
$filePath = $filePath -replace '\\', '/'

# --- Nexus-Hub self-write carve-out ---
# `nexus-hub init` legitimately writes several of the execution-trigger surfaces
# below. A legitimate installer write and a hostile one produce an IDENTICAL
# file, so path matching cannot separate them and writer identity is the only
# discriminator available. When the installer announces itself by setting
# NEXUS_HUB_INIT=1, suppress the advisory for the surfaces it owns; everything
# else still warns, and the default action stays "warn" regardless.
if ($env:NEXUS_HUB_INIT -eq '1') {
    $initOwned = @(
        '.claude/settings*.json', '*/.claude/settings*.json',
        '.claude/hooks/*',        '*/.claude/hooks/*',
        '.cursor/*',              '*/.cursor/*',
        '.agents/*',              '*/.agents/*',
        '.github/skills/*',       '*/.github/skills/*'
    )
    foreach ($owned in $initOwned) {
        if ($filePath -like $owned) { exit 0 }
    }
}

# --- Sensitive path patterns ---
# Kept in the same order as escalation-trigger.sh so the two stay comparable.
$sensitivePatterns = @(
    # Authentication and authorization
    '*/auth/*'
    '*/authentication/*'
    '*/authorization/*'
    '**/oauth*'
    '**/jwt*'
    '**/rbac*'
    '**/permissions*'

    # Database migrations and schemas
    '*/migrations/*'
    '*/migrate/*'
    '**/schema*'
    '**/alembic/*'
    '**/flyway/*'
    '**/liquibase/*'

    # Dependency manifests
    '*/package.json'
    '*/package-lock.json'
    '*/yarn.lock'
    '*/pnpm-lock.yaml'
    '*/requirements.txt'
    '*/requirements*.txt'
    '*/Pipfile'
    '*/Pipfile.lock'
    '*/pyproject.toml'
    '*/poetry.lock'
    '*/go.mod'
    '*/go.sum'
    '*/Cargo.toml'
    '*/Cargo.lock'
    '*/Gemfile'
    '*/Gemfile.lock'
    '*/*.csproj'
    '*/*.sln'

    # Infrastructure and CI/CD
    '*/Dockerfile*'
    '*/docker-compose*'
    '*/.github/workflows/*'
    '*/.gitlab-ci*'
    '*/Jenkinsfile*'
    '*/*.tf'
    '*/*.tfvars'
    '*/terraform/*'
    '*/pulumi/*'
    '*/k8s/*'
    '*/kubernetes/*'
    '*/helm/*'

    # Environment and secrets
    '*/.env*'
    '*/secrets*'
    '*/*.pem'
    '*/*.key'
    '*/*.cert'
    '*/credentials*'

    # --- Execution-trigger config (canonical surface list, group A) ---
    # Agent-harness settings and hooks: loaded by the harness itself, outside the
    # agent sandbox, on session start or a registered tool event.
    '.claude/settings*.json'
    '*/.claude/settings*.json'
    '.claude/hooks/*'
    '*/.claude/hooks/*'

    # Editor task and launch config: executed by the editor on a task run, a
    # debug action, or a configured folder-open task.
    '.vscode/tasks.json'
    '*/.vscode/tasks.json'
    '.vscode/launch.json'
    '*/.vscode/launch.json'

    # Version-control metadata: .git/hooks/* runs on hooked operations, and
    # .git/config is where a redirected core.hooksPath / core.fsmonitor persists.
    '.git/hooks/*'
    '*/.git/hooks/*'
    '.git/config'
    '*/.git/config'

    # Editor agent surface: read on editor or agent startup and rule evaluation.
    '.cursor/*'
    '*/.cursor/*'

    # --- Execution-trigger config (canonical surface list, group C) ---
    # Interpreter and environment paths: executed by an editor language extension
    # during environment discovery, commonly without any user action.
    '.venv/bin/*'
    '*/.venv/bin/*'
    '.venv/Scripts/*'
    '*/.venv/Scripts/*'
    'venv/bin/*'
    '*/venv/bin/*'
    'venv/Scripts/*'
    '*/venv/Scripts/*'
    'pyvenv.cfg'
    '*/pyvenv.cfg'
)

# --- Match check ---
$matchedPattern = $null
foreach ($pattern in $sensitivePatterns) {
    if ($filePath -like $pattern) {
        $matchedPattern = $pattern
        break
    }
}

if ($matchedPattern) {
    if ($escalationMode -eq 'block') {
        Write-Output "ESCALATION BLOCKED: Modifying '$filePath' matches sensitive pattern '$matchedPattern'."
        Write-Output "This file requires explicit approval. Set ESCALATION_MODE=warn to downgrade to advisory."
        exit 2
    }
    Write-Output "ESCALATION WARNING: Modifying '$filePath' matches sensitive pattern '$matchedPattern'."
    Write-Output "This is a sensitive file. Please verify this change is intentional and authorized."
    exit 0
}

exit 0
