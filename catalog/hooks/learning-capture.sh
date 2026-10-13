#!/usr/bin/env bash
# learning-capture.sh - Local-only observation capture for the continuous-learning skill.
#
# Reads a Claude Code hook payload from stdin (UserPromptSubmit, PreToolUse,
# PostToolUse, Stop) and appends a single JSON line to
# `.nexus/observations.jsonl` under the project root. The continuous-learning
# skill (catalog/skills/workflow/continuous-learning/SKILL.md) reads that file
# in-session to mint instinct YAML files and, eventually, draft skills.
#
# Hard constraints (see plan T008, comparison-ECC.md Section 13):
#   - No network calls of any kind.
#   - No external observer model -- the only consumer is the agent itself,
#     in-session, reading the JSONL.
#   - Project-scoped storage; nothing crosses project boundaries.
#
# Runtime controls:
#   NEXUS_DISABLED_HOOKS=learning-capture   skip this hook entirely
#   NEXUS_HOOK_PROFILE=minimal              skip this hook entirely
#   NEXUS_LEARNING_CAPTURE=off              skip writes (default 'on')
#   NEXUS_LEARNING_PATH=<path>              override observations file (project-relative)
#   NEXUS_LEARNING_MAX_BYTES=<int>          truncate observations file when it
#                                           exceeds this size (default 1048576 = 1 MiB)

trap 'exit 0' ERR

_HOOK_NAME="learning-capture"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi
if [[ "${NEXUS_LEARNING_CAPTURE:-on}" == "off" ]]; then exit 0; fi

# --- Read payload ---
INPUT=$(cat 2>/dev/null || true)
if [ -z "$INPUT" ]; then exit 0; fi

# --- Locate project root ---
PROJECT_ROOT="$(pwd)"
if command -v git >/dev/null 2>&1; then
  GIT_TOPLEVEL=$(git rev-parse --show-toplevel 2>/dev/null || true)
  if [ -n "$GIT_TOPLEVEL" ]; then
    PROJECT_ROOT="$GIT_TOPLEVEL"
  fi
fi

OBS_REL="${NEXUS_LEARNING_PATH:-.nexus/observations.jsonl}"
OBS_PATH="$PROJECT_ROOT/$OBS_REL"
OBS_DIR="$(dirname "$OBS_PATH")"
mkdir -p "$OBS_DIR" 2>/dev/null || exit 0

# --- Pick a JSON helper (python is the most portable; jq is faster when available) ---
PY=""
if command -v python3 >/dev/null 2>&1; then
  PY="python3"
elif command -v python >/dev/null 2>&1; then
  PY="python"
fi

# --- Compose and append the record ---
TIMESTAMP=$(date -u "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "unknown")
MAX_BYTES="${NEXUS_LEARNING_MAX_BYTES:-1048576}"
if ! [[ "$MAX_BYTES" =~ ^[0-9]+$ ]] || [ "$MAX_BYTES" -le 0 ]; then
  MAX_BYTES=1048576
fi

if [ -n "$PY" ]; then
  # Payload travels over stdin, avoiding the environment's per-string size cap.
  printf '%s' "$INPUT" | \
  NEXUS_LC_OBS_PATH="$OBS_PATH" \
  NEXUS_LC_TS="$TIMESTAMP" \
  NEXUS_LC_MAX_BYTES="$MAX_BYTES" \
  PYTHONIOENCODING=utf-8 \
  "$PY" -c '
import json
import os
import sys

try:
    raw = sys.stdin.read()
    obs_path = os.environ["NEXUS_LC_OBS_PATH"]
    ts = os.environ.get("NEXUS_LC_TS", "")
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    def first(d, *keys, default=""):
        for k in keys:
            v = d.get(k)
            if v:
                return v
        return default

    event = str(first(payload, "hook_event_name", "event", "type", default="unknown"))[:128]
    tool = str(first(payload, "tool_name", "tool", default=""))[:128]
    prompt_raw = str(first(payload, "prompt", "user_prompt", default=""))
    if len(prompt_raw) > 400:
        prompt_sample = prompt_raw[:400]
    else:
        prompt_sample = prompt_raw

    record = {
        "ts": ts,
        "event": event,
        "tool": tool,
        "prompt_sample": prompt_sample,
    }
    with open(obs_path, "a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    max_bytes = int(os.environ["NEXUS_LC_MAX_BYTES"])
    if os.path.getsize(obs_path) > max_bytes:
        with open(obs_path, "rb") as fh:
            lines = fh.readlines()
        kept = []
        total = 0
        for line in reversed(lines):
            if total + len(line) > max_bytes:
                break
            kept.append(line)
            total += len(line)
        tmp = obs_path + ".trim." + str(os.getpid())
        with open(tmp, "wb") as fh:
            fh.writelines(reversed(kept))
        os.replace(tmp, obs_path)
except Exception:
    pass
' 2>/dev/null || true
elif command -v jq >/dev/null 2>&1; then
  # jq fallback when no Python is available.
  EVENT=$(printf '%s' "$INPUT" | jq -r '(.hook_event_name // .event // .type // "unknown") | tostring | .[0:128]' 2>/dev/null || echo "unknown")
  TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '(.tool_name // .tool // "") | tostring | .[0:128]' 2>/dev/null || true)
  PROMPT_SAMPLE=$(echo "$INPUT" | jq -r '(.prompt // .user_prompt // "") | tostring | .[0:400]' 2>/dev/null || true)
  RECORD=$(jq -nc \
    --arg ts "$TIMESTAMP" \
    --arg event "$EVENT" \
    --arg tool "$TOOL_NAME" \
    --arg prompt "$PROMPT_SAMPLE" \
    '{ts:$ts, event:$event, tool:$tool, prompt_sample:$prompt}' 2>/dev/null)
  if [ -n "$RECORD" ]; then
    echo "$RECORD" >> "$OBS_PATH" 2>/dev/null || true
  fi
else
  # No JSON helper available: write a minimal record without parsing.
  echo "{\"ts\":\"$TIMESTAMP\",\"event\":\"unknown\",\"tool\":\"\",\"prompt_sample\":\"\"}" >> "$OBS_PATH" 2>/dev/null || true
fi

# --- Truncate the observations file if it has grown too large ---
SIZE=$(wc -c < "$OBS_PATH" 2>/dev/null | tr -d ' ' || echo 0)
while [ -n "$SIZE" ] && [ "$SIZE" -gt "$MAX_BYTES" ]; do
  # Whole-line fallback rotation preserves UTF-8 and repeats until byte-bounded.
  TOTAL_LINES=$(wc -l < "$OBS_PATH" 2>/dev/null | tr -d ' ' || echo 0)
  if [ -n "$TOTAL_LINES" ] && [ "$TOTAL_LINES" -gt 1 ]; then
    KEEP=$(( TOTAL_LINES / 2 ))
    [ "$KEEP" -lt 1 ] && KEEP=1
    TMP="$OBS_PATH.trim.$$"
    if tail -n "$KEEP" "$OBS_PATH" > "$TMP" 2>/dev/null; then
      if ! mv -f "$TMP" "$OBS_PATH" 2>/dev/null; then
        rm -f "$TMP" 2>/dev/null
        printf '%s\n' 'learning-capture: degraded-rotation; observations retained above the byte cap' >&2
        break
      fi
    else
      rm -f "$TMP" 2>/dev/null
      break
    fi
  else
    # An individual record cannot fit this configured cap; never cut its bytes.
    : > "$OBS_PATH"
  fi
  SIZE=$(wc -c < "$OBS_PATH" 2>/dev/null | tr -d ' ' || echo 0)
done

exit 0
