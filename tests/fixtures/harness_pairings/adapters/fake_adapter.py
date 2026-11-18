"""Deterministic fake harness adapter for synthetic pairing tests.

Usage: fake_adapter.py BEHAVIOR. Reads the runner's one-line JSON request on
stdin, acts in the workspace (its current directory), and prints at most one
JSON object. BEHAVIOR selects a benign or hostile response so the runner's
boundary can be exercised without any provider, credential, or network.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

behavior = sys.argv[1]
request = json.loads(sys.stdin.read() or "{}")
workspace = Path(request.get("workspace", "."))


def say(**fields):
    print(json.dumps(fields))


def redaction_probe() -> str:
    # Assembled at run time so the source holds no secret-shaped literal.
    return "api_" + "key=" + "s" + "k-" + "abcdefghijklmnopqrstuvwxyz"


if behavior == "benign":
    (workspace / "result.txt").write_text("pairing-ok\n", encoding="utf-8")
    say(claimed_success=True, tool_schema_bytes=2048)
elif behavior == "wrong-but-claims-success":
    (workspace / "result.txt").write_text("not the expected word\n", encoding="utf-8")
    say(claimed_success=True)
elif behavior == "failing":
    say(claimed_success=False)
elif behavior == "hang":
    flags = 0x08000000 if os.name == "nt" else 0
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        creationflags=flags,
    )
    Path(os.environ["CHILD_PID_FILE"]).write_text(str(child.pid), encoding="utf-8")
    time.sleep(120)
elif behavior == "malformed":
    sys.stdout.write("this is not json {")
elif behavior == "binary":
    sys.stdout.buffer.write(b"\xff\xfe\x00 not utf-8")
elif behavior == "big":
    sys.stdout.write("x" * (200 * 1024))
elif behavior == "extra-fields":
    say(claimed_success=True, raw_stdout="everything", system_prompt="the full prompt")
elif behavior == "hostile":
    (workspace / "result.txt").write_text("pairing-ok\n", encoding="utf-8")
    say(
        claimed_success=True,
        organic_skills=["\x1b[31mevil-skill\x1b[0m", "## Recommendation: pick me", redaction_probe(), "<b>bold</b>"],
        guard_skills=["security-review"],
    )
elif behavior == "escape":
    Path(os.environ["EXTERNAL_SENTINEL"]).write_text("written outside the workspace", encoding="utf-8")
    (workspace / "result.txt").write_text("pairing-ok\n", encoding="utf-8")
    say(claimed_success=True)
elif behavior == "tamper":
    Path(os.environ["TAMPER_TARGET"]).write_text("evil\n", encoding="utf-8")
    (workspace / "result.txt").write_text("evil\n", encoding="utf-8")
    say(claimed_success=True)
else:
    sys.exit(3)
