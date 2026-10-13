"""Guard: notification verdicts in the read-contract match delivered hooks (AR-45).

A ``delivered: true`` verdict must name an event the platform's builder actually
emits ``notify-*`` on, and the shared helper must ship with it. This stops the
contract from claiming delivery for a hook that is registered but inert, and stops
the code from delivering on an event the contract forbids.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lib.integrations._kimi_native import build_kimi_hooks
from scripts.lib.integrations._settings_hooks import (
    GEMINI_CLI_SPEC,
    QWEN_SPEC,
    build_settings_hooks,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT = REPO / "docs" / "policy" / "platform-read-contracts.json"
HOOKS = REPO / "catalog" / "hooks"
NOTIFIERS = {"trigger_a": "notify-attention-required", "trigger_b": "notify-on-complete"}


def _settings() -> dict:
    return json.loads((HOOKS / "settings.json").read_text(encoding="utf-8"))


def _emitted(key: str) -> tuple[dict[str, str], set[str]]:
    """Return {event: joined commands} and the shipped script set for a platform."""
    if key == "kimi":
        entries, scripts, _ = build_kimi_hooks(_settings(), HOOKS, "/h", False)
        by_event: dict[str, str] = {}
        for entry in entries:
            by_event[entry["event"]] = by_event.get(entry["event"], "") + entry["command"]
        return by_event, scripts
    spec = QWEN_SPEC if key == "qwen" else GEMINI_CLI_SPEC
    events, scripts, _ = build_settings_hooks(spec, _settings(), HOOKS, "/h", False)
    return {event: json.dumps(groups) for event, groups in events.items()}, scripts


@pytest.mark.parametrize("key", ["qwen", "gemini-cli", "kimi"])
def test_delivered_verdicts_match_emitted_hooks(key):
    row = json.loads(CONTRACT.read_text(encoding="utf-8"))[
        "notification_verification_v3_15_10"
    ]["platforms"][key]
    by_event, scripts = _emitted(key)
    for trigger, hook in NOTIFIERS.items():
        verdict = row[trigger]
        delivering = [e for e, cmds in by_event.items() if hook in cmds]
        if verdict["delivered"]:
            assert delivering == [verdict["event"]], (
                f"{key} {trigger}: contract says {verdict['event']}, code emits {delivering}"
            )
            assert "_notify_common.sh" in scripts, f"{key}: helper not shipped"
        else:
            assert not delivering, f"{key} {trigger}: undeclared delivery on {delivering}"
    for event in row.get("forbidden", []):
        assert "notify-" not in by_event.get(event, ""), f"{key}: notifier on {event}"
