#!/usr/bin/env bash
# Lint Autofix - PreToolUse Hook for Claude Code (OPT-IN, file-mutating)
# Part of Nexus-Hub - the deterministic half of the lint-repair-loop skill.
#
# What it does:
#   On a `git commit` Bash tool call, runs available formatters' native --fix on
#   the STAGED files that have NO unstaged changes, then re-stages them, so the
#   commit carries auto-formatted code. The LLM-judgment half (repairing what a
#   formatter cannot) is the lint-repair-loop skill, run by the agent on its own
#   session model - this hook makes no LLM call.
#
# Why opt-in (unlike the advisory hooks):
#   This hook MUTATES files. Shipping it on-by-default would silently reformat
#   every downstream commit, so it is inert unless NEXUS_ENABLE_LINT_AUTOFIX=1
#   (mirroring git-guardrails.sh's NEXUS_PROTECTED_BRANCHES opt-in). It also
#   honors the standard opt-outs.
#
# Safety:
#   - Inert unless NEXUS_ENABLE_LINT_AUTOFIX=1.
#   - Opt-out via NEXUS_DISABLED_HOOKS=lint-autofix or NEXUS_HOOK_PROFILE=minimal.
#   - Never touches a file with unstaged changes (staged-clean files only), so it
#     cannot silently stage work in progress.
#   - Fail-open: always exits 0; never blocks a commit. No LLM call, no network.
#
# Runtime controls:
#   Enable  : export NEXUS_ENABLE_LINT_AUTOFIX=1
#   Disable : export NEXUS_DISABLED_HOOKS=lint-autofix   (or NEXUS_HOOK_PROFILE=minimal)

set -euo pipefail
trap 'exit 0' ERR

_HOOK_NAME="lint-autofix"

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: lint-autofix]"
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
# continuation line printed as is.
_nexus_msg() {
  local line
  printf '%s %s\n' "$_NEXUS_TAG" "$1" >&2
  shift
  for line in "$@"; do printf '%s\n' "$line" >&2; done
}

# --- Opt-in gate (this hook mutates files) ---
[ "${NEXUS_ENABLE_LINT_AUTOFIX:-0}" = "1" ] || exit 0

# --- Opt-out overrides ---
case ",${NEXUS_DISABLED_HOOKS:-}," in *",${_HOOK_NAME},"*) exit 0 ;; esac
[ "${NEXUS_HOOK_PROFILE:-full}" = "minimal" ] && exit 0

# --- Read JSON from stdin; extract the Bash command (jq if present, else grep/sed) ---
INPUT=$(cat)
if command -v jq >/dev/null 2>&1; then
  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
else
  # Fallback (mirrors git-guardrails.sh) so an opt-in user is not silently no-op'd without jq.
  COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//;s/"$//')
fi
[ -n "${COMMAND:-}" ] || exit 0

# --- Only act on a `git commit` invocation ---
echo "$COMMAND" | grep -qE '(^|[;&|]|[[:space:]])git[[:space:]]+commit([[:space:]]|$)' || exit 0

# --- Must be inside a git work tree ---
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# --- Staged files (added/copied/modified) and files with unstaged changes ---
STAGED=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
[ -n "$STAGED" ] || exit 0
UNSTAGED=$(git diff --name-only 2>/dev/null || true)

_has_unstaged() {
  printf '%s\n' "$UNSTAGED" | grep -Fxq -- "$1"
}

FIXED=""
SKIPPED=""

_fix_file() {
  f="$1"
  [ -f "$f" ] || return 0
  case "$f" in
    *.py)
      command -v ruff >/dev/null 2>&1 || return 0
      ruff check --fix -- "$f" >/dev/null 2>&1 || true
      ruff format -- "$f" >/dev/null 2>&1 || true
      ;;
    *.js|*.jsx|*.ts|*.tsx|*.mjs|*.cjs)
      command -v prettier >/dev/null 2>&1 || return 0
      prettier --write -- "$f" >/dev/null 2>&1 || true
      ;;
    *.go)
      command -v gofmt >/dev/null 2>&1 || return 0
      gofmt -w -- "$f" >/dev/null 2>&1 || true
      ;;
    *.sh)
      command -v shfmt >/dev/null 2>&1 || return 0
      shfmt -w -- "$f" >/dev/null 2>&1 || true
      ;;
    *)
      return 0
      ;;
  esac
  git add -- "$f" >/dev/null 2>&1 || true
  FIXED="${FIXED} ${f}"
}

# --- Format staged-clean files only; skip any with unstaged changes ---
while IFS= read -r f; do
  [ -n "$f" ] || continue
  if _has_unstaged "$f"; then
    SKIPPED="${SKIPPED} ${f}"
    continue
  fi
  _fix_file "$f"
done <<EOF
${STAGED}
EOF

# --- Advisory summary to stderr (never stdout; never blocks) ---
[ -n "$FIXED" ] && _nexus_msg "formatted and re-staged:$(_nexus_esc "$FIXED")"
[ -n "$SKIPPED" ] && _nexus_msg "skipped (unstaged changes present):$(_nexus_esc "$SKIPPED")"
exit 0
