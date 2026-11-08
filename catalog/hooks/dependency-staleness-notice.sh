#!/usr/bin/env bash
# Dependency-Staleness Notice - advisory PostToolUse Hook for Claude Code
# Emits an advisory reminder when a Write/Edit targets a dependency manifest, so
# a stale / vulnerable-dependency audit is prompted the moment dependencies
# change. Part of Nexus-Hub.
#
# Why this exists:
#   The intent is "audit dependencies when they change." One way to do that is an
#   always-on background worker daemon that re-scans manifests on a timer.
#   Nexus-Hub does NOT ship a daemon; it approximates the same intent on the
#   event surface it already uses - a PostToolUse matcher keyed on the Write/Edit
#   that touched a dependency manifest. This is an advisory, event-driven check,
#   not a background worker. Modeled on workflow-phase-notice.sh.
#
# How it works:
#   Claude Code pipes JSON to stdin after each Write/Edit tool call. This script
#   extracts the file path, decides whether it is a declared-dependency manifest
#   (not a generated lockfile), maps it to the matching ecosystem audit command,
#   and emits an advisory reminder to stderr. Advisory only: it always exits 0
#   and never blocks.
#
# Registration:
#   Registered in the default catalog/hooks/settings.json under PostToolUse with
#   a `Write|Edit` matcher. Disable it per session with
#   `export NEXUS_DISABLED_HOOKS=dependency-staleness-notice` or skip all
#   advisory hooks with `export NEXUS_HOOK_PROFILE=minimal`.

set -euo pipefail

# Never fail loudly on internal errors - this hook is advisory only.
trap 'exit 0' ERR

# --- Runtime Controls ---
# Disable by name:        export NEXUS_DISABLED_HOOKS=dependency-staleness-notice
# Skip all non-essential: export NEXUS_HOOK_PROFILE=minimal
_HOOK_NAME="dependency-staleness-notice"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

# --- ANSI colors ---
COLOR_CYAN='\033[0;36m'
COLOR_RESET='\033[0m'

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: dependency-staleness-notice]"
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

# --- Extract file path (requires jq; silently no-op without it, mirroring
#     large-file-guard.sh / secret-scan.sh / workflow-phase-notice.sh) ---
if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)
else
  exit 0
fi

[ -n "${FILE_PATH:-}" ] || exit 0

# Normalize separators (Windows paths -> POSIX) before pattern matching.
NORM_PATH="${FILE_PATH//\\//}"
BASENAME="${NORM_PATH##*/}"

# --- Skip manifests inside vendor / build directories (not the user's own). ---
case "/$NORM_PATH/" in
  */node_modules/*|*/vendor/*|*/dist/*|*/build/*|*/.venv/*|*/site-packages/*) exit 0 ;;
esac

# --- Recognize declared-dependency manifests (not generated lockfiles) and map
#     each to the matching ecosystem audit command. ---
HINT=""
case "$BASENAME" in
  package.json) HINT="npm audit (or pnpm audit / yarn audit)" ;;
  requirements.txt|requirements-*.txt|pyproject.toml|Pipfile|setup.cfg) HINT="pip-audit (or safety check)" ;;
  go.mod) HINT="govulncheck ./..." ;;
  Cargo.toml) HINT="cargo audit" ;;
  Gemfile) HINT="bundle audit" ;;
  composer.json) HINT="composer audit" ;;
  pom.xml|build.gradle|build.gradle.kts) HINT="the OWASP dependency-check or your build's audit task" ;;
  *.csproj) HINT="dotnet list package --vulnerable" ;;
  *) exit 0 ;;
esac

# --- Emit advisory marker ---
_nexus_msg "$COLOR_CYAN" "Dependency manifest changed: $(_nexus_esc "$NORM_PATH"). Consider auditing for stale / vulnerable deps (run: ${HINT}; see the dependency-security-audit / dependency-manager skills)."
exit 0
