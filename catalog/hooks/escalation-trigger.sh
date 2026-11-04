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

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: escalation-trigger]"
# Make CR, LF, ESC and the other C0 control characters in an echoed value
# visible, so a file name or command cannot start a forged tagged line.
_nexus_esc() {
  local s=$1 ctrl i c r
  ctrl=$'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x7f'
  for ((i = 0; i < ${#ctrl}; i++)); do
    c=${ctrl:i:1}
    case $c in
      $'\t') r='\t' ;; $'\n') r='\n' ;; $'\r') r='\r' ;; $'\x1b') r='\x1b' ;; $'\x7f') r='\x7f' ;;
      *) printf -v r '%s%02x' '\x' $((i + 1)) ;;
    esac
    s=${s//"$c"/"$r"}
  done
  printf '%s' "$s"
}
# Print the tag and the message to stdout (SessionStart context the agent
# reads); every further argument is a continuation line printed as is.
_nexus_msg() {
  local line
  printf '%s %s\n' "$_NEXUS_TAG" "$1"
  shift
  for line in "$@"; do printf '%s\n' "$line"; done
}

ESCALATION_MODE="${ESCALATION_MODE:-warn}"  # "warn" or "block"

# --- Resolve the target path ---
# Primary: the PreToolUse JSON payload on stdin. Fallback: $CLAUDE_FILE_PATH.
FILE_PATH=""
if [ ! -t 0 ]; then
  INPUT=$(cat 2>/dev/null || true)
  # Full access (permission_mode "bypassPermissions"): an opted-in block
  # downgrades to the default warning. Contract: docs/policy/permission-mode-contract.md
  _HOST_MODE=""
  if command -v jq >/dev/null 2>&1; then
    _HOST_MODE=$(printf '%s' "$INPUT" | jq -r 'if type == "object" and (.permission_mode | type) == "string" then .permission_mode else empty end' 2>/dev/null || true)
  elif command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
    _MODE_PYTHON=$(command -v python3 || command -v python)
    _HOST_MODE=$(printf '%s' "$INPUT" | "$_MODE_PYTHON" -c '
import json, sys
try:
    payload = json.load(sys.stdin)
    mode = payload.get("permission_mode") if isinstance(payload, dict) else None
    if isinstance(mode, str):
        print(mode)
except (ValueError, TypeError):
    pass' 2>/dev/null || true)
  fi
  if [ "$_HOST_MODE" = "bypassPermissions" ]; then ESCALATION_MODE="warn"; fi
  if [ -n "${INPUT:-}" ]; then
    if command -v jq >/dev/null 2>&1; then
      FILE_PATH=$(printf '%s' "$INPUT" \
        | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null || true)
    else
      # Fallback: basic JSON extraction via grep/sed (no jq dependency).
      FILE_PATH=$(printf '%s' "$INPUT" \
        | LC_ALL=C grep -oE '"(file_path|path)"[[:space:]]*:[[:space:]]*"[^"]*"' \
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
    _nexus_msg "ESCALATION BLOCKED: Modifying '$(_nexus_esc "$FILE_PATH")' matches sensitive pattern '$matched_pattern'." \
      "This file requires explicit approval. Set ESCALATION_MODE=warn to downgrade to advisory."
    exit 2
  else
    _nexus_msg "ESCALATION WARNING: Modifying '$(_nexus_esc "$FILE_PATH")' matches sensitive pattern '$matched_pattern'." \
      "This is a sensitive file. Please verify this change is intentional and authorized."
    exit 0
  fi
fi

exit 0
