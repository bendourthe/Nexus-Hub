#!/usr/bin/env bash
# escalation-trigger.sh - Warn when Write/Edit targets match sensitive path patterns.
#
# Hook type: PreToolUse (Write, Edit)
# Behavior: Advisory (exit 0 with warning message). Change ESCALATION_MODE to
#           "block" to exit 2 and block the operation instead.
#
# Input contract:
#   Reads the PreToolUse JSON payload from stdin and takes the path from
#   .tool_input.file_path (falling back to .tool_input.path). This is the same
#   contract every other Write/Edit hook in this catalog uses (secret-scan,
#   large-file-guard, old-version-docs-guard, auto-format-on-write, lint-on-write).
#   The legacy $CLAUDE_FILE_PATH environment variable is still honored as a
#   fallback when stdin carries no usable path, so an existing setup that exports
#   it keeps working.
#
# Sensitive path patterns (customize per project):
#   - Auth/security modules
#   - Database migrations and schemas
#   - Dependency manifests
#   - Infrastructure and CI/CD config
#   - Environment and secrets files
#   - Execution-trigger config: groups A and C of the canonical surface list in
#     catalog/skills/security-operations/agentic-endpoint-hardening/SKILL.md
#
# Scope note: this hook matches FILE PATHS only. Group B of that canonical list
# (the `core.hooksPath` / `core.fsmonitor` command-string patterns) can never be
# seen here, because a PreToolUse Write/Edit payload carries no shell command;
# those are owned by git-guardrails.sh. Keep the split intact.
#
# Limitation: a fixed glob list is defense-in-depth, not a boundary. It matches
# only the surfaces someone already enumerated, so a novel execution-trigger path
# will pass silently. Treat a clean run as "no known-bad path matched", never as
# "this write is safe".

set -euo pipefail

ESCALATION_MODE="${ESCALATION_MODE:-warn}"  # "warn" or "block"

# --- Resolve the target path ---
# Primary: the PreToolUse JSON payload on stdin. Fallback: $CLAUDE_FILE_PATH.
FILE_PATH=""
if [ ! -t 0 ]; then
  INPUT=$(cat 2>/dev/null || true)
  if [ -n "${INPUT:-}" ]; then
    if command -v jq >/dev/null 2>&1; then
      FILE_PATH=$(printf '%s' "$INPUT" \
        | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null || true)
    else
      # Fallback: basic JSON extraction via grep/sed (no jq dependency).
      FILE_PATH=$(printf '%s' "$INPUT" \
        | grep -oE '"(file_path|path)"[[:space:]]*:[[:space:]]*"[^"]*"' \
        | head -1 \
        | sed -E 's/.*"(file_path|path)"[[:space:]]*:[[:space:]]*"//; s/"$//' || true)
      # This text fallback reads the RAW JSON string, so it does not decode JSON
      # escapes the way jq does. A Windows path therefore arrives with doubled
      # backslashes ("C:\\repo\\.git\\hooks\\x"). Decode that escape HERE, before
      # the separator normalization below, or each "\\" would normalize to "//"
      # and defeat every glob (a real defect: it silently stopped Windows paths
      # from matching). The jq branch above needs no such step.
      FILE_PATH="${FILE_PATH//\\\\/\\}"
    fi
  fi
fi

# jq prints the literal string "null" for a JSON null; treat that as absent.
if [ "${FILE_PATH:-}" = "null" ]; then
  FILE_PATH=""
fi

FILE_PATH="${FILE_PATH:-${CLAUDE_FILE_PATH:-}}"

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Normalize to forward slashes for consistent matching
FILE_PATH="${FILE_PATH//\\//}"

# --- Nexus-Hub self-write carve-out ---
# `nexus-hub init` legitimately writes several of the execution-trigger surfaces
# below (.claude/settings.json, .cursor/rules, .agents/, .github/skills). A
# legitimate installer write and a hostile one produce an IDENTICAL file, so path
# matching cannot separate them and writer identity is the only discriminator
# available to a shell hook. When the installer announces itself by exporting
# NEXUS_HUB_INIT=1, suppress the advisory for the surfaces it owns. Every other
# path still warns, and the default action stays "warn" regardless, so the
# catalog's own wiring is never self-blocked even when this carve-out is absent.
if [ "${NEXUS_HUB_INIT:-0}" = "1" ]; then
  case "$FILE_PATH" in
    .claude/settings*.json|*/.claude/settings*.json) exit 0 ;;
    .claude/hooks/*|*/.claude/hooks/*)               exit 0 ;;
    .cursor/*|*/.cursor/*)                           exit 0 ;;
    .agents/*|*/.agents/*)                           exit 0 ;;
    .github/skills/*|*/.github/skills/*)             exit 0 ;;
  esac
fi

# --- Sensitive path patterns ---
# Each pattern is a bash glob matched against the full file path.
# Add or remove patterns to match your project's layout.

SENSITIVE_PATTERNS=(
  # Authentication and authorization
  "*/auth/*"
  "*/authentication/*"
  "*/authorization/*"
  "**/oauth*"
  "**/jwt*"
  "**/rbac*"
  "**/permissions*"

  # Database migrations and schemas
  "*/migrations/*"
  "*/migrate/*"
  "**/schema*"
  "**/alembic/*"
  "**/flyway/*"
  "**/liquibase/*"

  # Dependency manifests
  "*/package.json"
  "*/package-lock.json"
  "*/yarn.lock"
  "*/pnpm-lock.yaml"
  "*/requirements.txt"
  "*/requirements*.txt"
  "*/Pipfile"
  "*/Pipfile.lock"
  "*/pyproject.toml"
  "*/poetry.lock"
  "*/go.mod"
  "*/go.sum"
  "*/Cargo.toml"
  "*/Cargo.lock"
  "*/Gemfile"
  "*/Gemfile.lock"
  "*/*.csproj"
  "*/*.sln"

  # Infrastructure and CI/CD
  "*/Dockerfile*"
  "*/docker-compose*"
  "*/.github/workflows/*"
  "*/.gitlab-ci*"
  "*/Jenkinsfile*"
  "*/*.tf"
  "*/*.tfvars"
  "*/terraform/*"
  "*/pulumi/*"
  "*/k8s/*"
  "*/kubernetes/*"
  "*/helm/*"

  # Environment and secrets
  "*/.env*"
  "*/secrets*"
  "*/*.pem"
  "*/*.key"
  "*/*.cert"
  "*/credentials*"

  # --- Execution-trigger config (canonical surface list, group A) ---
  # Agent-harness settings and hooks: loaded by the harness itself, outside the
  # agent sandbox, on session start or a registered tool event.
  ".claude/settings*.json"
  "*/.claude/settings*.json"
  ".claude/hooks/*"
  "*/.claude/hooks/*"

  # Editor task and launch config: executed by the editor on a task run, a debug
  # action, or a configured folder-open task.
  ".vscode/tasks.json"
  "*/.vscode/tasks.json"
  ".vscode/launch.json"
  "*/.vscode/launch.json"

  # Version-control metadata: .git/hooks/* runs on hooked operations, and
  # .git/config is where a redirected core.hooksPath / core.fsmonitor persists.
  ".git/hooks/*"
  "*/.git/hooks/*"
  ".git/config"
  "*/.git/config"

  # Editor agent surface: read on editor or agent startup and rule evaluation.
  ".cursor/*"
  "*/.cursor/*"

  # --- Execution-trigger config (canonical surface list, group C) ---
  # Interpreter and environment paths: executed by an editor language extension
  # during environment discovery, commonly without any user action.
  ".venv/bin/*"
  "*/.venv/bin/*"
  ".venv/Scripts/*"
  "*/.venv/Scripts/*"
  "venv/bin/*"
  "*/venv/bin/*"
  "venv/Scripts/*"
  "*/venv/Scripts/*"
  "pyvenv.cfg"
  "*/pyvenv.cfg"
)

# --- Match check ---

matched_pattern=""
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
  # shellcheck disable=SC2254
  case "$FILE_PATH" in
    $pattern)
      matched_pattern="$pattern"
      break
      ;;
  esac
done

if [[ -n "$matched_pattern" ]]; then
  if [[ "$ESCALATION_MODE" == "block" ]]; then
    echo "ESCALATION BLOCKED: Modifying '$FILE_PATH' matches sensitive pattern '$matched_pattern'."
    echo "This file requires explicit approval. Set ESCALATION_MODE=warn to downgrade to advisory."
    exit 2
  else
    echo "ESCALATION WARNING: Modifying '$FILE_PATH' matches sensitive pattern '$matched_pattern'."
    echo "This is a sensitive file. Please verify this change is intentional and authorized."
    exit 0
  fi
fi

exit 0
