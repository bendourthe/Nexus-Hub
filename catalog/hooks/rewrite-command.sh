#!/usr/bin/env bash
# rewrite-command.sh -- PreToolUse delegate for the shared rewrite decision.
# Asks python -m nexus_context_compressor rewrite and maps 0/1/2/3 onto a
# PreToolUse permissionDecision. Fail-open to passthrough (never auto-allow).

set -euo pipefail

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  exit 0
fi
PYBIN="$(command -v python3 || command -v python)"

INPUT="$(cat || true)"
if [ -z "${INPUT}" ]; then
  exit 0
fi

COMMAND="$("$PYBIN" -c "import json,sys
try:
    payload=json.load(sys.stdin)
except Exception:
    payload={}
inp=payload.get('tool_input') or payload.get('toolInput') or {}
print(inp.get('command') or '')" <<<"$INPUT" 2>/dev/null || true)"

if [ -z "${COMMAND}" ]; then
  exit 0
fi

HOST_SETTINGS=""
if [ -n "${CLAUDE_CONFIG_DIR:-}" ] && [ -f "${CLAUDE_CONFIG_DIR}/settings.json" ]; then
  HOST_SETTINGS="${CLAUDE_CONFIG_DIR}/settings.json"
elif [ -f "${HOME}/.claude/settings.json" ]; then
  HOST_SETTINGS="${HOME}/.claude/settings.json"
elif [ -f ".claude/settings.json" ]; then
  HOST_SETTINGS=".claude/settings.json"
fi

set +e
if [ -n "${HOST_SETTINGS}" ]; then
  REWRITE="$("$PYBIN" -m nexus_context_compressor rewrite --cmd "$COMMAND" --host-settings "$HOST_SETTINGS" 2>/dev/null)"
else
  REWRITE="$("$PYBIN" -m nexus_context_compressor rewrite --cmd "$COMMAND" 2>/dev/null)"
fi
CODE=$?
set -e

case "$CODE" in
  0)
    DECISION="allow"
    ;;
  2)
    DECISION="deny"
    ;;
  3)
    DECISION="ask"
    ;;
  *)
    exit 0
    ;;
esac

"$PYBIN" -c "import json,sys
decision=sys.argv[1]
rewrite=sys.argv[2]
payload={}
try:
    payload=json.loads(sys.stdin.read() or '{}')
except Exception:
    payload={}
tool=dict(payload.get('tool_input') or {})
if rewrite:
    tool['command']=rewrite
out={'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':decision}}
if rewrite:
    out['hookSpecificOutput']['updatedInput']=tool
print(json.dumps(out))
" "$DECISION" "$REWRITE" <<<"$INPUT"

exit 0
