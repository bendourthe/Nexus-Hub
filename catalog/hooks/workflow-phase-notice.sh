#!/usr/bin/env bash
# Workflow-Phase Notice - example PreToolUse/PostToolUse Hook for Claude Code
# Emits an advisory phase-boundary marker when a Write/Edit targets a
# Nexus-Hub workflow-phase artifact (a /plan, /spec, /tasks, or release file).
# Part of Nexus-Hub - candidate N1a (workflow-phase hook recipe).
#
# Why this exists:
#   Spec Kit registers per-command lifecycle hooks (before_/after_specify,
#   after_tasks, ...) in a `.specify/extensions.yml` registry that presupposes
#   its third-party extension runtime. Nexus-Hub does NOT add new harness event
#   types and does NOT import that registry. Instead it approximates the same
#   "run automation at a workflow-phase boundary" intent on the Claude-style
#   event surface it already uses: a PreToolUse / PostToolUse matcher keyed on
#   the tool call that marks the boundary (here, Write/Edit), with the hook
#   script inspecting the tool input to decide whether it is really at a
#   boundary. This is the runnable example referenced by the "Workflow-phase
#   automation recipe" in guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md.
#
# How it works:
#   Claude Code pipes JSON to stdin around each Write/Edit tool call. This
#   script extracts the file path, classifies it as a plan / spec / tasks /
#   release artifact, and emits an advisory reminder to stderr if it matches.
#   It is advisory only - it always exits 0 and never blocks a phase.
#
# Registration:
#   Registered in the default catalog/hooks/settings.json under PostToolUse
#   with a `Write|Edit` matcher, so it runs on every install. It is advisory
#   only (exit 0, stderr marker on workflow artifacts; silent otherwise).
#   Disable it per-session with `export NEXUS_DISABLED_HOOKS=workflow-phase-notice`
#   or skip all advisory hooks with `export NEXUS_HOOK_PROFILE=minimal`.

set -euo pipefail

# Never fail loudly on internal errors - this hook is advisory only.
trap 'exit 0' ERR

# --- Runtime Controls ---
# Disable by name:        export NEXUS_DISABLED_HOOKS=workflow-phase-notice
# Skip all non-essential: export NEXUS_HOOK_PROFILE=minimal
_HOOK_NAME="workflow-phase-notice"
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
readonly _NEXUS_TAG="[Nexus-Hub: workflow-phase-notice]"
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
#     large-file-guard.sh / secret-scan.sh / old-version-docs-guard.sh) ---
if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)
else
  exit 0
fi

[ -n "${FILE_PATH:-}" ] || exit 0

# Normalize separators (Windows paths -> POSIX) before pattern matching.
NORM_PATH="${FILE_PATH//\\//}"
BASENAME="${NORM_PATH##*/}"

# --- Classify the workflow phase by path/basename ---
# Order matters: plan-dir match wins over a bare plan.md basename.
PHASE=""
if [[ "$NORM_PATH" =~ (^|/)docs/.*/plans/[^/]+\.md$ ]]; then
  PHASE="plan"
elif [[ "$BASENAME" == "spec.md" ]]; then
  PHASE="spec"
elif [[ "$BASENAME" == "tasks.md" ]]; then
  PHASE="tasks"
elif [[ "$BASENAME" == "CHANGELOG.md" ]]; then
  PHASE="release"
fi

# Silent for any non-workflow artifact.
[ -n "$PHASE" ] || exit 0

# --- Emit advisory marker ---
_nexus_msg "$COLOR_CYAN" "${PHASE}-phase artifact written: $(_nexus_esc "$NORM_PATH"). Remember the post-phase docs + commit sequence."
exit 0
