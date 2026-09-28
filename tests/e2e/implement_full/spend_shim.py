"""Forward to a real agent CLI with a spend guard and a spend log.

Placed on PATH under the agent's own name by the harness for paid runs. It asks the
CLI for machine-readable output (none of these flags bypasses an approval), prints
the model's reply text, and appends the call's cost to E2E_SPEND_LOG and to the
plan-wide ledger E2E_LEDGER so the evaluation stops at its budget. E2E_SHIM_AGENT
names the CLI and E2E_REAL_BIN is the real binary.

- claude: `--output-format json --max-budget-usd <cap>`; the CLI reports `total_cost_usd`
  and enforces the per-call cap itself.
- codex: `--json`; the CLI reports token usage only, priced at the published rates
  below. It has no per-call budget flag, so a call is bounded by E2E_CALL_TIMEOUT and
  the ledger guard assumes each call may cost up to the per-call cap.
- opencode: `--format json`; each `step_finish` event reports its `cost` in USD. It has
  no per-call budget flag either, with the same bounds as codex.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# gpt-5.5, Standard tier, <272K context, USD per token, from
# https://developers.openai.com/api/docs/pricing (fetched 2026-09-27). Reasoning tokens
# are added to output tokens, which overstates cost if they are already included.
CODEX_RATES = {"input": 5.00e-6, "cached": 0.50e-6, "output": 30.00e-6}


def _ledger_total(path: str) -> float:
    try:
        with open(path, encoding="utf-8") as record:
            return sum(json.loads(line).get("cost_usd", 0.0) for line in record if line.strip())
    except OSError:
        return 0.0


def _events(stdout: str) -> list[dict]:
    events = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _claude(stdout: str) -> tuple[float, str]:
    payload = json.loads(stdout)
    return float(payload.get("total_cost_usd") or 0.0), str(payload.get("result", ""))


def _codex(stdout: str) -> tuple[float, str]:
    cost, text = 0.0, ""
    for event in _events(stdout):
        if event.get("type") == "turn.completed":
            usage = event.get("usage") or {}
            cached = int(usage.get("cached_input_tokens") or 0)
            fresh = max(int(usage.get("input_tokens") or 0) - cached, 0)
            out = int(usage.get("output_tokens") or 0) + int(usage.get("reasoning_output_tokens") or 0)
            cost += fresh * CODEX_RATES["input"] + cached * CODEX_RATES["cached"] + out * CODEX_RATES["output"]
        item = event.get("item") or {}
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            text = str(item.get("text", ""))
        if event.get("type") == "error":
            # A provider refusal (quota, auth) arrives only as an event; without this the
            # call looked like a silent exit 1 at zero cost.
            sys.stderr.write(f"codex error: {event.get('message', '')}\n")
    return cost, text


def _opencode(stdout: str) -> tuple[float, str]:
    cost, texts = 0.0, []
    for event in _events(stdout):
        part = event.get("part") or {}
        if event.get("type") == "step_finish":
            cost += float(part.get("cost") or 0.0)
        elif event.get("type") == "text" and part.get("text"):
            texts.append(str(part["text"]))
    return cost, "\n".join(texts)


def _argv(agent: str, argv: list[str], cap: str) -> list[str]:
    if agent == "claude":
        return [*argv, "--output-format", "json", "--max-budget-usd", cap]
    flags = ["--json"] if agent == "codex" else ["--format", "json"]
    if agent == "codex" and os.environ.get("E2E_CODEX_TRUST_HOOKS") == "1":
        # Stands in for the one-time `/hooks` trust a user gives; see run_e2e.isolated.
        flags.append("--dangerously-bypass-hook-trust")
    # Before the trailing prompt: `exec`, `exec resume --last`, `run`, and `run -c` all accept it there.
    return [*argv[:-1], *flags, argv[-1]] if argv else flags


def main(argv: list[str]) -> int:
    agent = os.environ["E2E_SHIM_AGENT"]
    real = os.environ["E2E_REAL_BIN"]
    cap = os.environ.get("E2E_CALL_CAP_USD", "3")
    ledger = os.environ.get("E2E_LEDGER")
    ledger_cap = float(os.environ.get("E2E_LEDGER_CAP", "50"))
    if ledger:
        # The plan-wide spend guard: refuse a call that could take the ledger past its cap.
        spent = _ledger_total(ledger)
        if spent + float(cap) > ledger_cap:
            sys.stderr.write(f"spend guard: USD {spent:.4f} spent; a USD {cap} call could pass the USD "
                             f"{ledger_cap:.2f} cap\n")
            return 3
    try:
        proc = subprocess.run(
            [real, *_argv(agent, argv, cap)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=float(os.environ.get("E2E_CALL_TIMEOUT", "1800")),
        )
        stdout, stderr, rc = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as expired:
        out = expired.stdout or ""
        stdout = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
        stderr, rc = "spend shim: call timed out\n", 124
    parse = {"claude": _claude, "codex": _codex, "opencode": _opencode}[agent]
    try:
        cost, text = parse(stdout)
        sys.stdout.write(text + "\n")
    except ValueError:
        cost = 0.0
        sys.stdout.write(stdout)
    if ledger:
        with open(ledger, "a", encoding="utf-8") as record:
            record.write(json.dumps({"run": os.environ.get("E2E_RUN_LABEL", ""), "cost_usd": cost}) + "\n")
    with open(os.environ["E2E_SPEND_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps({"argv": argv[:1], "cost_usd": cost, "exit": rc}) + "\n")
    sys.stderr.write(stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
