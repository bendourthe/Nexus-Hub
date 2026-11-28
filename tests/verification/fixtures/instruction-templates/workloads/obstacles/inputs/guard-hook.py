import json, sys

event = json.load(sys.stdin)
command = str(event.get("tool_input", {}).get("command", ""))
if "rm " in command or "Remove-Item" in command:
    print("blocked by workspace guard: destructive command", file=sys.stderr)
    sys.exit(2)
