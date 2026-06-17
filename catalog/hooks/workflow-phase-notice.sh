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
#   automation recipe" in guides/CLAUDE_CODE_SETTINGS_REFERENCE.md.
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
MSG="[workflow-phase-notice] ${PHASE}-phase artifact written: ${NORM_PATH}. Remember the post-phase docs + commit sequence."
echo -e "${COLOR_CYAN}${MSG}${COLOR_RESET}" >&2
exit 0
