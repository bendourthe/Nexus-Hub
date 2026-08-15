"""Thin-dispatch tests for ``nexus-hub autonomy``."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_cli():
    return importlib.import_module("scripts.lib.autonomy_cli")


@pytest.fixture
def cli():
    return _load_cli()


def _status(*platforms: dict) -> dict:
    return {
        "project": "C:/work/demo",
        "state_path": "C:/work/demo/.nexus-hub/autonomy-state.json",
        "platforms": list(platforms),
    }


def _platform(
    name: str,
    *,
    supported: bool = True,
    status: str = "off",
    tier: str = "off",
    remaining_seconds: int = 0,
    available_tiers: tuple[str, ...] = ("edits_only", "full"),
) -> dict:
    return {
        "platform": name,
        "supported": supported,
        "status": status,
        "tier": tier,
        "remaining_seconds": remaining_seconds,
        "available_tiers": list(available_tiers if supported else ()),
    }


def test_root_cli_forwards_autonomy_arguments(monkeypatch) -> None:
    root_cli = importlib.import_module("scripts.nexus_hub_cli")
    calls: list[list[str]] = []
    monkeypatch.setattr(root_cli, "cmd_autonomy", lambda argv: calls.append(argv) or 7)

    assert root_cli.main(["autonomy", "enable", "--platform", "claude"]) == 7
    assert calls == [["enable", "--platform", "claude"]]


class InteractiveInput:
    def isatty(self) -> bool:
        return True


class NonInteractiveInput:
    def isatty(self) -> bool:
        return False


def test_status_is_default_and_lists_every_platform(cli, monkeypatch, capsys) -> None:
    document = _status(
        _platform("claude", status="active", tier="edits_only", remaining_seconds=3599),
        _platform("gemini", supported=False),
    )
    fake = SimpleNamespace(status=lambda **_kwargs: document)
    monkeypatch.setattr(cli, "_load_autonomy_module", lambda: fake)

    assert cli.main([]) == 0

    output = capsys.readouterr().out
    assert "claude" in output and "edits" in output and "1h 0m" in output
    assert "gemini" in output and "unavailable" in output


def test_status_json_round_trips_core_document(cli, monkeypatch, capsys) -> None:
    document = _status(_platform("codex"))
    fake = SimpleNamespace(status=lambda **_kwargs: document)
    monkeypatch.setattr(cli, "_load_autonomy_module", lambda: fake)

    assert cli.main(["status", "--json"]) == 0

    assert json.loads(capsys.readouterr().out) == document


def test_enable_defaults_to_edits_previews_then_forwards_to_core(
    cli, monkeypatch, capsys
) -> None:
    calls: list[tuple[str, str, int, dict]] = []

    def enable(platform: str, tier: str, ttl: int, **kwargs):
        calls.append((platform, tier, ttl, kwargs))
        if kwargs.get("preview_only"):
            return SimpleNamespace(
                outcome="preview",
                message="preview",
                diff="--- before\n+++ after\n",
                backup_path="C:/work/demo/config.bak",
                changed=False,
            )
        return SimpleNamespace(
            outcome="enabled",
            message="enabled",
            diff="",
            backup_path="C:/work/demo/config.bak",
            changed=True,
        )

    fake = SimpleNamespace(
        status=lambda **_kwargs: _status(_platform("claude")),
        enable=enable,
    )
    monkeypatch.setattr(cli, "_load_autonomy_module", lambda: fake)
    monkeypatch.setattr(cli.sys, "stdin", InteractiveInput())
    monkeypatch.setattr("builtins.input", lambda _prompt: "yes")

    assert cli.main(["enable", "--platform", "claude"]) == 0

    assert [call[1] for call in calls] == ["edits_only", "edits_only"]
    assert [call[2] for call in calls] == [60, 60]
    assert calls[0][3]["preview_only"] is True
    assert "preview_only" not in calls[1][3]
    output = capsys.readouterr().out
    assert output.index("--- before") < output.index("enabled")
    assert "Backup: C:/work/demo/config.bak" in output


def test_full_enable_refuses_without_tty_before_calling_core(
    cli, monkeypatch, capsys
) -> None:
    fake = SimpleNamespace(
        status=lambda **_kwargs: _status(_platform("claude")),
        enable=lambda *_args, **_kwargs: pytest.fail("core must not be called"),
    )
    monkeypatch.setattr(cli, "_load_autonomy_module", lambda: fake)
    monkeypatch.setattr(cli.sys, "stdin", NonInteractiveInput())

    assert cli.main(["enable", "--platform", "claude", "--tier", "full"]) == 2

    assert "interactive terminal" in capsys.readouterr().err


def test_descriptorless_platform_skip_is_success(cli, monkeypatch, capsys) -> None:
    skipped = SimpleNamespace(
        outcome="skipped",
        message="gemini has no verified autonomy descriptor; skipped without writing config.",
        diff="",
        backup_path=None,
        changed=False,
    )
    fake = SimpleNamespace(
        status=lambda **_kwargs: _status(_platform("gemini", supported=False)),
        enable=lambda *_args, **_kwargs: skipped,
    )
    monkeypatch.setattr(cli, "_load_autonomy_module", lambda: fake)
    monkeypatch.setattr(cli.sys, "stdin", InteractiveInput())

    assert cli.main(["enable", "--platform", "gemini"]) == 0

    assert "skipped without writing" in capsys.readouterr().out


@pytest.mark.parametrize("verb", ["disable", "revert"])
def test_disable_and_revert_forward_platform_and_exit_code(
    cli, monkeypatch, verb: str
) -> None:
    calls: list[tuple[str, dict]] = []

    def operation(platform: str, **kwargs):
        calls.append((platform, kwargs))
        return SimpleNamespace(
            outcome=f"{verb}d",
            message=f"{verb} complete",
            backup_path=None,
            changed=True,
        )

    fake = SimpleNamespace(
        status=lambda **_kwargs: _status(
            _platform("codex", status="active", tier="full")
        ),
        disable=operation,
        revert=operation,
    )
    monkeypatch.setattr(cli, "_load_autonomy_module", lambda: fake)

    assert cli.main([verb]) == 0
    assert calls == [("codex", {"project_dir": Path.cwd()})]


def test_ambiguous_enable_requires_platform(cli, monkeypatch, capsys) -> None:
    fake = SimpleNamespace(
        status=lambda **_kwargs: _status(_platform("claude"), _platform("codex"))
    )
    monkeypatch.setattr(cli, "_load_autonomy_module", lambda: fake)

    assert cli.main(["enable"]) == 2

    assert "--platform" in capsys.readouterr().err
