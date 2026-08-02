#!/usr/bin/env bash
# Secret Scan - PreToolUse Hook for Claude Code
# Scans file content for potential secrets before writing.
# Part of Nexus-Hub
#
# How it works:
#   Claude Code pipes JSON to stdin before each Write/Edit tool call.
#   This script scans the content for patterns that look like secrets
#   (API keys, tokens, private keys, passwords in config).
#   If secrets are found: exits 2 (blocks the write).
#   If clean: exits 0.
#
# Detected patterns:
#   AWS access keys     (AKIA...)
#   OpenAI/Stripe keys  (sk-...)
#   GitHub tokens       (ghp_..., gho_..., ghs_..., ghr_...)
#   Slack tokens        (xoxb-..., xoxp-..., xoxa-...)
#   Private keys        (BEGIN RSA/EC/PRIVATE KEY)
#   Generic secrets     (password/secret/token assignments with values)

set -euo pipefail

# --- ANSI colors ---
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

# --- Read JSON from stdin ---
INPUT=$(cat)

# --- Extract content ---
if command -v jq >/dev/null 2>&1; then
  if ! FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null); then
    exit 0
  fi
  if ! CONTENT=$(printf '%s' "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // empty' 2>/dev/null); then
    exit 0
  fi
else
  # Without jq we cannot reliably extract content; allow the write
  exit 0
fi

# If no content to scan, allow
[ -n "${CONTENT:-}" ] || exit 0

FILE_PATH="${FILE_PATH:-unknown}"
FILENAME=$(basename "$FILE_PATH" 2>/dev/null || echo "$FILE_PATH")

# --- Secret patterns ---
# Each entry: "regex:::description"
SECRET_PATTERNS=(
  'AKIA[0-9A-Z]{16}:::AWS Access Key ID'
  'sk-[a-zA-Z0-9]{20,}:::API key (OpenAI/Stripe-style sk- prefix)'
  'ghp_[a-zA-Z0-9]{36,}:::GitHub Personal Access Token'
  'gho_[a-zA-Z0-9]{36,}:::GitHub OAuth Token'
  'ghs_[a-zA-Z0-9]{36,}:::GitHub Server Token'
  'ghr_[a-zA-Z0-9]{36,}:::GitHub Refresh Token'
  'xoxb-[0-9a-zA-Z-]{20,}:::Slack Bot Token'
  'xoxp-[0-9a-zA-Z-]{20,}:::Slack User Token'
  'xoxa-[0-9a-zA-Z-]{20,}:::Slack App Token'
  '-----BEGIN RSA PRIVATE KEY-----:::RSA Private Key'
  '-----BEGIN EC PRIVATE KEY-----:::EC Private Key'
  '-----BEGIN PRIVATE KEY-----:::Private Key (PKCS#8)'
  '-----BEGIN OPENSSH PRIVATE KEY-----:::OpenSSH Private Key'
)

FOUND_SECRETS=()

for entry in "${SECRET_PATTERNS[@]}"; do
  PATTERN="${entry%%:::*}"
  DESC="${entry##*:::}"

  if echo "$CONTENT" | grep -qE "$PATTERN" 2>/dev/null; then
    FOUND_SECRETS+=("$DESC")
  fi
done

# --- Check for password/secret assignments in config-like files ---
# Match: password = "value", secret: 'value', TOKEN="value" (8+ char values)
if echo "$CONTENT" | grep -qiE "(password|secret|token|api_key|apikey|auth_token|access_token)[[:space:]]*[:=][[:space:]]*[\"'][^\"']{8,}" 2>/dev/null; then
  MATCH_LINE=$(echo "$CONTENT" | grep -iE "(password|secret|token|api_key|apikey|auth_token|access_token)[[:space:]]*[:=][[:space:]]*[\"'][^\"']{8,}" 2>/dev/null | head -1)
  # Exclude common false positives (placeholder values, env var references)
  if ! echo "$MATCH_LINE" | grep -qiE '(your[-_]|example|placeholder|changeme|xxx|process\.env|os\.environ|\$\{|\$\()' 2>/dev/null; then
    FOUND_SECRETS+=("Hardcoded password/secret/token assignment")
  fi
fi

# --- Report findings ---
if [ ${#FOUND_SECRETS[@]} -gt 0 ]; then
  echo -e "${COLOR_RED}[secret-scan] BLOCKED${COLOR_RESET}: Potential secrets detected in $FILENAME:" >&2
  for secret in "${FOUND_SECRETS[@]}"; do
    echo "  - $secret" >&2
  done
  echo "Remove secrets and use environment variables or a secrets manager instead." >&2
  exit 2
fi

# Content is clean
exit 0
