"""Workload-owned deterministic evaluator for the isolation canary.

Pass means the session reported absent and quoted no marker.

Usage: evaluate.py WORKSPACE EVALUATOR_DIR. Prints one JSON object. It checks only that
the trial left a non-empty result.txt. Case assertions are graded afterward by the
skill-eval-loop grader over the retained final text and tool-call path, because the
evaluator calls no judge.
"""

import json
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
result = workspace / "result.txt"
if not result.is_file():
    print(json.dumps({"success": False, "fingerprint": "missing-output"}))
else:
    got = result.read_bytes()[:4096].decode("utf-8", errors="replace").strip().lower()
    expected = (Path(sys.argv[2]) / "expected.txt").read_text(encoding="utf-8").strip().lower()
    ok = got == expected
    print(json.dumps({"success": ok, "fingerprint": "" if ok else "marker-quoted"}))
