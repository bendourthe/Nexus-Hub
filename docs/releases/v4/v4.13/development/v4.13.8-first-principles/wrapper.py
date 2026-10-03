"""Throwaway v4.13.8 first-principles pilot wrapper (T321-T322). Scaffolding, never shipped.

Applies the T319 dispatch contract from docs/releases/v4/v4.13/development/v4.13.8-admission.md:
one `claude -p --bare` run per (prompt, arm) cell, effort fixed with --effort high, no tools,
the skill body appended as a system prompt, the API key passed only through the child
environment, a fail-closed ledger checked before every dispatch, and one inert .json file per run.
Run one wrapper process at a time: the ledger is not locked, so two concurrent processes could
together exceed the cap.

Usage:
    python wrapper.py smoke    # the single smoke cell (baseline, p1)
    python wrapper.py run      # every remaining cell in the recorded order
"""
from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
EVALS = HERE / "evals" / "bug-localization.json"
SKILL = REPO / "catalog" / "skills" / "bug-fixing" / "bug-localization" / "SKILL.md"
RUNS = HERE / "runs"
ORDER = HERE / "order.json"
LEDGER = HERE / "ledger.json"
LOG = HERE / "run-log.jsonl"

MODEL = "claude-sonnet-5-5"
EFFORT = "high"
CAP_USD = 20.00
PER_RUN_CEILING_USD = 1.00
TIMEOUT_S = 900
KEY_SOURCE = "NEXUS_PILOT_ANTHROPIC_API_KEY"

ARMS = {
    "baseline": "",
    "first-principles": "Reason from first principles: restate the problem in your own terms "
    "and identify what must be true before choosing an approach.",
    "control": "Think the problem through before you answer.",
}
SMOKE_CELL = ("p1-invoice-keyerror", "baseline")


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_checked(path: Path, obj: object) -> None:
    """Write JSON, then read it back; a failed read-back is a failed write."""
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    if json.loads(path.read_text(encoding="utf-8")) != obj:
        raise SystemExit(f"read-back mismatch for {path}")


def append_log(entry: dict) -> None:
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def load_order(prompts: list[dict]) -> list[list[str]]:
    """The 15 cells shuffled once with seed 42; recorded before the first dispatch."""
    if ORDER.exists():
        return json.loads(ORDER.read_text(encoding="utf-8"))["order"]
    cells = [[p["id"], arm] for p in prompts for arm in ARMS]
    random.Random(42).shuffle(cells)
    write_checked(ORDER, {"seed": 42, "recorded_at": now(), "order": cells})
    return cells


def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    if RUNS.exists() and any(RUNS.glob("*.json")):
        # A missing ledger beside recorded runs would restart the cap from zero.
        raise SystemExit("ledger.json is missing but runs/ holds records; refusing to start")
    return {"cap_usd": CAP_USD, "per_run_ceiling_usd": PER_RUN_CEILING_USD, "spent_usd": 0.0, "runs": []}


def as_text(value: object) -> str:
    """TimeoutExpired carries bytes on POSIX even with text=True."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def build_prompt(entry: dict, instruction: str, arm: str) -> str:
    text = entry["prompt"] + "\n\n" + instruction
    return text + (" " + ARMS[arm] if ARMS[arm] else "")


def scrub(text: str, secret: str) -> str:
    return text.replace(secret, "[REDACTED]") if secret else text


def dispatch(entry: dict, instruction: str, arm: str, ledger: dict) -> dict:
    """Run one cell. Never retries; an error or empty reply is recorded as-is."""
    secret = os.environ.get(KEY_SOURCE, "")
    if not secret:
        raise SystemExit(f"{KEY_SOURCE} is not set; refusing to dispatch")
    if ledger["spent_usd"] + PER_RUN_CEILING_USD > CAP_USD:
        raise SystemExit(
            f"ledger refuses dispatch: spent {ledger['spent_usd']:.4f} + ceiling "
            f"{PER_RUN_CEILING_USD:.2f} would exceed cap {CAP_USD:.2f}"
        )
    exe = shutil.which("claude")
    if exe is None:
        raise SystemExit("claude CLI not found")
    args = [
        "-p", "--bare", "--setting-sources", "", "--model", MODEL, "--effort", EFFORT,
        "--tools", "", "--no-session-persistence", "--output-format", "json",
        "--max-budget-usd", f"{PER_RUN_CEILING_USD:.2f}",
        "--append-system-prompt-file", str(SKILL),
    ]
    env = dict(os.environ)
    env["ANTHROPIC_API_KEY"] = secret
    prompt = build_prompt(entry, instruction, arm)
    cell = f"{entry['id']}__{arm}"
    # Pre-charge the ceiling before dispatch, so a crash after a paid call can
    # only over-count; the measured cost replaces it once the run is recorded.
    spent_before = ledger["spent_usd"]
    ledger["spent_usd"] = round(spent_before + PER_RUN_CEILING_USD, 6)
    write_checked(LEDGER, ledger)
    append_log({"cell": cell, "status": "started", "at": now()})
    with tempfile.TemporaryDirectory(prefix="fp-pilot-") as scratch:
        try:
            proc = subprocess.run(
                [exe, *args], input=prompt, capture_output=True, text=True,
                encoding="utf-8", cwd=scratch, env=env, timeout=TIMEOUT_S, check=False,
            )
            exit_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            exit_code, stdout, stderr = None, exc.stdout, f"timeout after {TIMEOUT_S}s"
    stdout, stderr = scrub(as_text(stdout), secret), scrub(as_text(stderr), secret)
    try:
        cli_output = json.loads(stdout) if stdout.strip() else None
    except json.JSONDecodeError:
        cli_output = None
    cost = (cli_output or {}).get("total_cost_usd")
    # An unknown cost is charged at the ceiling so the ledger can only over-count.
    charged = float(cost) if isinstance(cost, (int, float)) else PER_RUN_CEILING_USD
    # Record the skill path repo-relative so no machine path or username lands in the record.
    recorded_args = [SKILL.relative_to(REPO).as_posix() if a == str(SKILL) else a for a in args]
    record = {
        "cell": cell, "prompt_id": entry["id"], "arm": arm, "model": MODEL, "effort": EFFORT,
        "cli_args": recorded_args, "prompt_length": len(prompt), "exit_code": exit_code,
        "errored": exit_code != 0 or cli_output is None,
        "cli_output": cli_output, "stdout_raw": None if cli_output else stdout[:20000],
        "stderr": stderr[:20000], "measured_cost_usd": cost, "charged_usd": charged,
        "finished_at": now(),
    }
    RUNS.mkdir(exist_ok=True)
    write_checked(RUNS / f"{cell}.json", record)
    ledger["spent_usd"] = round(spent_before + charged, 6)
    ledger["runs"].append({"cell": cell, "charged_usd": charged, "measured_cost_usd": cost})
    write_checked(LEDGER, ledger)
    append_log({"cell": cell, "status": "done", "at": now(), "errored": record["errored"],
                "charged_usd": charged, "spent_usd": ledger["spent_usd"]})
    return record


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("smoke", "run"):
        print(__doc__)
        return 2
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in data["prompts"]}
    order = load_order(data["prompts"])
    ledger = load_ledger()
    cells = [list(SMOKE_CELL)] if mode == "smoke" else order
    for prompt_id, arm in cells:
        if (RUNS / f"{prompt_id}__{arm}.json").exists():
            continue  # completed results are authoritative; never recomputed
        rec = dispatch(by_id[prompt_id], data["answer_format_instruction"], arm, ledger)
        print(f"{rec['cell']}: exit={rec['exit_code']} errored={rec['errored']} "
              f"cost={rec['measured_cost_usd']} spent={ledger['spent_usd']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
