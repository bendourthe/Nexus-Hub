"""Workload-owned deterministic evaluator for the synthetic echo workload.

Usage: evaluate.py WORKSPACE EVALUATOR_DIR. Prints one JSON object. The harness's
own claim is never an input; only the file the trial left behind is.
"""

import json
import sys
from pathlib import Path

workspace, evaluator_dir = Path(sys.argv[1]), Path(sys.argv[2])
expected = (evaluator_dir / "expected.txt").read_text(encoding="utf-8").strip().lower()
result = workspace / "result.txt"
if not result.is_file():
    print(json.dumps({"success": False, "fingerprint": "missing-output"}))
else:
    got = result.read_bytes()[:4096].decode("utf-8", errors="replace").strip().lower()
    ok = got == expected
    print(json.dumps({"success": ok, "fingerprint": "" if ok else "output-mismatch"}))
