"""Workload-owned deterministic floor for an instruction-file case set.

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
elif not result.read_bytes()[:4096].strip():
    print(json.dumps({"success": False, "fingerprint": "empty-output"}))
else:
    print(json.dumps({"success": True, "fingerprint": ""}))
