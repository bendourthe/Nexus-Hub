#!/usr/bin/env bash
# escalation-trigger.sh - Warn when Write/Edit targets match sensitive path patterns.
#
# Hook type: PreToolUse (Write, Edit)
# Behavior: Advisory (exit 0 with warning message). Change ESCALATION_MODE to
#           "block" to exit 2 and block the operation instead.
#
# Sensitive path patterns (customize per project):
#   - Auth/security modules
#   - Database migrations and schemas
#   - Dependency manifests
#   - Infrastructure and CI/CD config
#   - Environment and secrets files

set -euo pipefail

ESCALATION_MODE="${ESCALATION_MODE:-warn}"  # "warn" or "block"

# The file path being written/edited is passed via $CLAUDE_FILE_PATH
FILE_PATH="${CLAUDE_FILE_PATH:-}"

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Normalize to forward slashes for consistent matching
FILE_PATH="${FILE_PATH//\\//}"

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
