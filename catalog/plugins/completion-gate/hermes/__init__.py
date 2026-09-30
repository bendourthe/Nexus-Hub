"""Nexus-Hub completion gate for Hermes (v4.13.2).

On ``pre_verify``, asks the installed Nexus-Hub gate core whether this session's
full /implement run is complete, and returns ``continue`` with the core's reason
when it is not. Hermes fires ``pre_verify`` only on turns that edited code, so
the ``nexus-hub run-plan`` runner is Hermes' primary continuation layer and this
plugin is best-effort. Hermes plugins load only when listed in ``plugins.enabled``
(``hermes plugins enable nexus-completion-gate``).

A schema-2 (minor) record needs nothing here: the core judges it through
``check-minor`` and ``score-minor`` inside this plugin's budget (v4.13.6).

Policy: catalog/skills/workflow/implement-phase/references/completion-contract.md
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CORE = Path.home() / ".nexus-hub" / "scripts" / "completion_gate.py"


def _run_gate(session_id: str) -> dict | None:
    """Run the installed core with an argument list and no shell; None on any failure."""
    if not CORE.is_file():
        return None
    payload = json.dumps({"hook_event_name": "Stop", "session_id": session_id, "platform": "hermes"})
    env = dict(os.environ, NEXUS_GATE_FORMAT="plugin", NEXUS_GATE_BUDGET_SECONDS="25")
    try:
        proc = subprocess.run(
            [sys.executable, str(CORE), "stop"], input=payload, capture_output=True, text=True,
            timeout=30, env=env, check=False,
        )
        return json.loads(proc.stdout) if proc.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


def _pre_verify(**kwargs: object) -> dict | None:
    session_id = kwargs.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return None
    verdict = _run_gate(session_id)
    if not verdict or verdict.get("decision") != "continue" or not verdict.get("reason"):
        return None
    return {"action": "continue", "message": verdict["reason"]}


def register(ctx) -> None:
    ctx.register_hook("pre_verify", _pre_verify)
