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

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: secret-scan]"
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
# Print the tag and the message to stderr; every further argument is a
# continuation line printed as is. $1 is an optional color code for the tag.
_nexus_msg() {
  local color=$1 message=$2 line
  shift 2
  printf '%b%s%b %s\n' "$color" "$_NEXUS_TAG" "${color:+$COLOR_RESET}" "$message" >&2
  for line in "$@"; do printf '%s\n' "$line" >&2; done
}

# --- Read JSON from stdin ---
INPUT=$(cat)
# Full access (Claude Code or Codex permission_mode "bypassPermissions"): the
# user chose to run without approval gates, so this Nexus-Hub guard steps aside.
# Contract: docs/policy/permission-mode-contract.md
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
if [ "$_HOST_MODE" = "bypassPermissions" ]; then exit 0; fi

# --- Extract content ---
# jq is preferred. A host without it must not lose the scan: this hook blocks,
# so a silent allow is indistinguishable from a clean pass. Python 3 is the
# fallback (every supported platform already requires it). With neither, the
# hook fails CLOSED, because it cannot tell a clean write from a leaking one.
# A malformed payload is allowed when a parser ran, as in the .ps1 sibling; with no
# parser the hook cannot tell, so it blocks. A Python 2 interpreter does not count.
_find_python() {
  local candidate
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 \
      && "$candidate" -c 'import json, sys; sys.exit(sys.version_info[0] < 3)' >/dev/null 2>&1; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

# Print one tool_input field (first non-empty of the given keys) as UTF-8.
# Exits 0 with no output on a malformed payload; exits 3 only on an internal
# failure, which the caller treats as "cannot scan".
_py_field() {
  printf '%s' "$INPUT" | "$PY" -c 'import json, sys
try:
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
except Exception:
    sys.exit(0)
for key in sys.argv[1:]:
    value = tool_input.get(key)
    if value:
        sys.stdout.buffer.write(str(value).encode("utf-8"))
        break' "$@"
}

if command -v jq >/dev/null 2>&1; then
  if ! FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null); then
    exit 0
  fi
  if ! CONTENT=$(printf '%s' "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // empty' 2>/dev/null); then
    exit 0
  fi
elif PY=$(_find_python); then
  if ! FILE_PATH=$(_py_field file_path path) || ! CONTENT=$(_py_field content new_string); then
    _nexus_msg "" "BLOCKED: the payload could not be parsed, so the write was not scanned."
    exit 2
  fi
else
  _nexus_msg "" "BLOCKED: neither jq nor Python 3 is available, so the write cannot be scanned." \
    "Install jq or Python 3 so the scan can run."
  exit 2
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

  # -e: the private-key patterns start with "-----" and would otherwise parse as options.
  # A here-string, not a pipe: under pipefail, `grep -q` exiting on an early match
  # would SIGPIPE the writer and turn a real match into "no match" on a large write.
  if grep -qE -e "$PATTERN" <<<"$CONTENT" 2>/dev/null; then
    FOUND_SECRETS+=("$DESC")
  fi
done

# --- Check for password/secret assignments in config-like files ---
# Match: password = "value", secret: 'value', TOKEN="value" (8+ char values)
if grep -qiE "(password|secret|token|api_key|apikey|auth_token|access_token)[[:space:]]*[:=][[:space:]]*[\"'][^\"']{8,}" <<<"$CONTENT" 2>/dev/null; then
  MATCH_LINE=$(grep -m1 -iE "(password|secret|token|api_key|apikey|auth_token|access_token)[[:space:]]*[:=][[:space:]]*[\"'][^\"']{8,}" <<<"$CONTENT" 2>/dev/null || true)
  # Exclude common false positives (placeholder values, env var references)
  if ! grep -qiE '(your[-_]|example|placeholder|changeme|xxx|process\.env|os\.environ|\$\{|\$\()' <<<"$MATCH_LINE" 2>/dev/null; then
    FOUND_SECRETS+=("Hardcoded password/secret/token assignment")
  fi
fi

# --- Report findings ---
if [ ${#FOUND_SECRETS[@]} -gt 0 ]; then
  _lines=()
  for secret in "${FOUND_SECRETS[@]}"; do
    _lines+=("  - $secret")
  done
  _nexus_msg "$COLOR_RED" "BLOCKED: Potential secrets detected in $(_nexus_esc "$FILENAME"):" \
    "${_lines[@]}" "Remove secrets and use environment variables or a secrets manager instead."
  exit 2
fi

# Content is clean
exit 0
