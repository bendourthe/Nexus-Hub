"""The end-to-end harness itself is sound: with a scripted stand-in agent, a
fixture run reaches PLAN COMPLETE through the real checker, the real runner, and
the stateful gh stand-in. This proves the fixture is completable and the chain
(upfront record, resume cycles, verdict) holds; it does not measure a model."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent / "run_e2e.py"


def test_stub_agent_reaches_plan_complete(tmp_path: Path) -> None:
    empty = tmp_path / "empty.gitconfig"
    empty.write_text("", encoding="utf-8")
    env = dict(os.environ, GIT_CONFIG_GLOBAL=str(empty), GIT_CONFIG_NOSYSTEM="1")
    proc = subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "--agent",
            "stub",
            "--out",
            str(tmp_path / "out"),
            "--ledger",
            str(tmp_path / "ledger.jsonl"),
        ],
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    result = json.loads(proc.stdout)
    assert result["complete"] is True
    assert result["verdict"].startswith(
        "PLAN COMPLETE docs/releases/v0/v0.2/plans/v0.2.0-demo.md "
    )
    assert result["runner_exit"] == 0
