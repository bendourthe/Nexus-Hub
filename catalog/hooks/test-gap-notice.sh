#!/usr/bin/env bash
# Test-Gap Notice - advisory PostToolUse Hook for Claude Code
# Emits an advisory reminder when a Write/Edit targets a (non-test) source file
# that has no discoverable companion test, so a coverage gap is visible at the
# moment the code changes. Part of Nexus-Hub.
#
# Why this exists:
#   The intent is "flag source changes that lack a matching test." One way to do
#   that is an always-on background worker daemon that scans the tree on a timer.
#   Nexus-Hub does NOT ship a daemon; it approximates the same intent on the
#   event surface it already uses - a PostToolUse matcher keyed on the Write/Edit
#   that touched a source file - and the hook inspects the tool input to decide
#   whether the edited file looks untested. This is an advisory, event-driven
#   check, not a background worker. Modeled on workflow-phase-notice.sh.
#
# How it works:
#   Claude Code pipes JSON to stdin after each Write/Edit tool call. This script
#   extracts the file path, decides whether it is a (non-test) source file in a
#   language with a strong file-based test convention, looks for a conventional
#   companion test next to it (and in adjacent test directories), and emits an
#   advisory reminder to stderr only when none is found. Advisory only: it always
#   exits 0 and never blocks.
#
# Registration:
#   Registered in the default catalog/hooks/settings.json under PostToolUse with
#   a `Write|Edit` matcher. Disable it per session with
#   `export NEXUS_DISABLED_HOOKS=test-gap-notice` or skip all advisory hooks with
#   `export NEXUS_HOOK_PROFILE=minimal`.

set -euo pipefail

# Never fail loudly on internal errors - this hook is advisory only.
trap 'exit 0' ERR

# --- Runtime Controls ---
# Disable by name:        export NEXUS_DISABLED_HOOKS=test-gap-notice
# Skip all non-essential: export NEXUS_HOOK_PROFILE=minimal
_HOOK_NAME="test-gap-notice"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

# --- ANSI colors ---
COLOR_CYAN='\033[0;36m'
COLOR_RESET='\033[0m'

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
DIRNAME="${NORM_PATH%/*}"
[ "$DIRNAME" = "$NORM_PATH" ] && DIRNAME="."

EXT="${BASENAME##*.}"
STEM="${BASENAME%.*}"

# --- Only consider source extensions with a strong file-based test convention.
#     Languages that favor inline tests (Rust #[cfg(test)], C/C++) are excluded
#     to keep the advisory low-noise. ---
case "$EXT" in
  py|js|jsx|ts|tsx|go|rb|java|cs|php) ;;
  *) exit 0 ;;
esac

# --- Skip files that are themselves tests. ---
case "$BASENAME" in
  test_*.py|*_test.py|*_test.go|*.test.js|*.test.jsx|*.test.ts|*.test.tsx) exit 0 ;;
  *.spec.js|*.spec.jsx|*.spec.ts|*.spec.tsx|*Test.java|*Tests.cs|*_spec.rb|*Test.php) exit 0 ;;
esac

# --- Skip common entrypoint / aggregator files that rarely carry a dedicated
#     unit test, to avoid false positives. ---
case "$BASENAME" in
  __init__.py|conftest.py|setup.py|index.js|index.ts|index.jsx|index.tsx) exit 0 ;;
esac

# --- Skip files inside test / build / vendor directories. ---
case "/$NORM_PATH/" in
  */test/*|*/tests/*|*/__tests__/*|*/spec/*|*/node_modules/*|*/vendor/*|*/dist/*|*/build/*|*/.venv/*|*/site-packages/*) exit 0 ;;
esac

# --- Look for a conventional companion test in a bounded set of nearby
#     directories (no full-repo walk). A match is any nearby file whose name
#     contains the source stem AND matches a test-name convention. ---
has_companion_test() {
  local dir="$1" stem="$2"
  local d f bn
  local -a cand_dirs=(
    "$dir"
    "$dir/tests" "$dir/test" "$dir/__tests__" "$dir/spec"
    "$dir/../tests" "$dir/../test" "$dir/../__tests__" "$dir/../spec"
  )
  for d in "${cand_dirs[@]}"; do
    [ -d "$d" ] || continue
    for f in "$d"/*"$stem"*; do
      [ -e "$f" ] || continue
      bn="${f##*/}"
      case "$bn" in
        test_*|*_test.*|*.test.*|*.spec.*|*_spec.*|*Test.*|*Tests.*) return 0 ;;
      esac
    done
  done
  return 1
}

if has_companion_test "$DIRNAME" "$STEM"; then
  exit 0
fi

# --- Emit advisory marker ---
MSG="[test-gap-notice] No companion test found near ${NORM_PATH}. Consider adding one (see the unit-tests / test-driven-development skills, or run /test)."
echo -e "${COLOR_CYAN}${MSG}${COLOR_RESET}" >&2
exit 0
