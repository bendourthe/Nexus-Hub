"""Tests for the v1.1.5 skill-eval-loop dispatchers (Phase 5 / A6 + A7).

Covers three things:

1. CLI-adapter parity invariant: `scripts/optimize_skill_description.py`
   dispatches to claude / gemini / codex / opencode via per-CLI branches; no
   branch may invoke any other CLI (mirrors the v1.1.3 four-hook precedent
   in test_diff_review_hooks.py::TestPlatformIndependence).

2. Optimizer dry-run schema: `--dry-run` produces a JSON report with the
   declared shape (split, n_train, n_test, baseline_description, etc.) and
   does NOT call any CLI.

3. Aggregator + viewer smoke: `scripts/aggregate_benchmark.py` correctly
   produces benchmark.json from a fixture iteration directory; the static
   viewer renders without errors.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_eval_loop.py -v
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_OPTIMIZER = _REPO_ROOT / "scripts" / "optimize_skill_description.py"
_AGGREGATOR = _REPO_ROOT / "scripts" / "aggregate_benchmark.py"
_VIEWER = _REPO_ROOT / "scripts" / "skill_eval_viewer.py"

_SUPPORTED_CLIS = ("claude", "gemini", "codex", "opencode")
_DISPATCHER_SCRIPTS = (_OPTIMIZER,)


# ── Module loading helper ─────────────────────────────────────────────────────


def _load_module(file_path: Path):
    spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[file_path.stem] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ── 1. CLI-adapter parity ────────────────────────────────────────────────────


class TestEvalLoopCLIAdapter:
    """Each `if cli == "X":` branch in any dispatcher script must invoke ONLY
    its matching CLI binary. This is the same invariant the v1.1.3 four-hook
    suite enforces, applied to the option-B dispatcher pattern (single file,
    `--cli` flag) used by the eval-loop scripts."""

    @pytest.mark.parametrize("script_path", _DISPATCHER_SCRIPTS, ids=[p.name for p in _DISPATCHER_SCRIPTS])
    @pytest.mark.parametrize("cli", _SUPPORTED_CLIS)
    def test_branch_does_not_invoke_other_clis(self, script_path: Path, cli: str) -> None:
        source = script_path.read_text(encoding="utf-8")
        # Anchor on the branch header. The branch body is everything indented
        # MORE than the `if cli == "X":` line, up to the next sibling line
        # (the next `if cli ==` or the function's `raise`).
        lines = source.splitlines()
        header_idx = None
        header_indent = 0
        for i, line in enumerate(lines):
            if line.lstrip().startswith(f'if cli == "{cli}":'):
                header_idx = i
                header_indent = len(line) - len(line.lstrip())
                break
        assert header_idx is not None, (
            f"{script_path.name}: no `if cli == \"{cli}\":` branch found"
        )
        body_lines: list[str] = []
        for line in lines[header_idx + 1:]:
            if line.strip() == "":
                body_lines.append(line)
                continue
            indent = len(line) - len(line.lstrip())
            if indent <= header_indent:
                break
            body_lines.append(line)
        body = "\n".join(body_lines)

        other_clis = set(_SUPPORTED_CLIS) - {cli}
        for other in other_clis:
            # The branch must not invoke any other CLI as the first argv
            # element of a subprocess call (and our dispatcher uses argv-list
            # form exclusively, so checking the literal `["<other>"` is enough).
            assert f'["{other}"' not in body and f"['{other}'" not in body, (
                f"{script_path.name} `if cli == \"{cli}\":` branch must not invoke {other} CLI"
            )

    @pytest.mark.parametrize("script_path", _DISPATCHER_SCRIPTS, ids=[p.name for p in _DISPATCHER_SCRIPTS])
    def test_dispatcher_has_assertion_against_unsupported_cli(self, script_path: Path) -> None:
        source = script_path.read_text(encoding="utf-8")
        # The dispatcher must enforce the supported-cli set with a hard assert.
        assert "assert cli in" in source, (
            f"{script_path.name}: missing `assert cli in {{...}}` guard at the top of the dispatcher"
        )

    @pytest.mark.parametrize("cli", _SUPPORTED_CLIS)
    def test_dispatcher_has_branch_for_each_cli(self, cli: str) -> None:
        source = _OPTIMIZER.read_text(encoding="utf-8")
        assert f'if cli == "{cli}":' in source, (
            f"optimize_skill_description.py: missing `if cli == \"{cli}\":` branch"
        )


# ── 2. Optimizer dry-run schema ──────────────────────────────────────────────


@pytest.fixture
def fixture_skill_and_evals(tmp_path: Path) -> tuple[Path, Path]:
    """Build a temporary SKILL.md + evals.json for dry-run testing."""
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(
        "---\n"
        "name: fixture-skill\n"
        "description: Run a structured task. Use when the user wants to run, evaluate, or score a task.\n"
        "summary_l0: \"fixture\"\n"
        "overview_l1: \"fixture\"\n"
        "---\n\n"
        "# Fixture\n",
        encoding="utf-8",
    )
    evals = tmp_path / "evals.json"
    evals.write_text(
        json.dumps(
            [
                {"id": "eval-001", "query": "run my task", "should_trigger": True, "assertions": []},
                {"id": "eval-002", "query": "evaluate this", "should_trigger": True, "assertions": []},
                {"id": "eval-003", "query": "score the output", "should_trigger": True, "assertions": []},
                {"id": "eval-004", "query": "unrelated", "should_trigger": False, "assertions": []},
                {"id": "eval-005", "query": "tangential ask", "should_trigger": False, "assertions": []},
            ]
        ),
        encoding="utf-8",
    )
    return skill_md, evals


class TestOptimizerDryRun:
    def test_dry_run_returns_zero_and_emits_schema(self, fixture_skill_and_evals: tuple[Path, Path]) -> None:
        skill_md, evals = fixture_skill_and_evals
        result = subprocess.run(
            [
                sys.executable,
                str(_OPTIMIZER),
                "--skill", str(skill_md),
                "--evals", str(evals),
                "--cli", "claude",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"dry-run failed: {result.stderr}"
        report = json.loads(result.stdout)
        assert report["mode"] == "dry-run"
        assert report["cli"] == "claude"
        assert report["selection_metric"] == "test_trigger_rate"
        assert report["n_train"] + report["n_test"] == 5
        assert report["n_train"] >= 1 and report["n_test"] >= 1
        assert isinstance(report["split"]["train_ids"], list)
        assert isinstance(report["split"]["test_ids"], list)
        assert set(report["split"]["train_ids"]) | set(report["split"]["test_ids"]) == {
            "eval-001", "eval-002", "eval-003", "eval-004", "eval-005"
        }
        assert "candidate_generation_prompt_template_preview" in report
        assert "Run a structured task" in report["baseline_description"]

    def test_dry_run_split_is_deterministic_under_fixed_seed(
        self, fixture_skill_and_evals: tuple[Path, Path]
    ) -> None:
        skill_md, evals = fixture_skill_and_evals
        runs = []
        for _ in range(2):
            result = subprocess.run(
                [
                    sys.executable, str(_OPTIMIZER),
                    "--skill", str(skill_md),
                    "--evals", str(evals),
                    "--cli", "gemini",
                    "--dry-run",
                    "--seed", "7",
                ],
                capture_output=True, text=True, timeout=30,
            )
            assert result.returncode == 0
            runs.append(json.loads(result.stdout)["split"])
        assert runs[0] == runs[1], "split must be deterministic for the same --seed"

    def test_dry_run_does_not_invoke_cli(self, fixture_skill_and_evals: tuple[Path, Path], tmp_path: Path) -> None:
        """Stub PATH so that if the optimizer tried to run any CLI, it would
        fail. With --dry-run the optimizer must NOT try."""
        skill_md, evals = fixture_skill_and_evals
        empty_path_dir = tmp_path / "no_clis"
        empty_path_dir.mkdir()
        result = subprocess.run(
            [
                sys.executable, str(_OPTIMIZER),
                "--skill", str(skill_md),
                "--evals", str(evals),
                "--cli", "codex",
                "--dry-run",
            ],
            capture_output=True, text=True, timeout=30,
            env={"PATH": str(empty_path_dir)},
        )
        assert result.returncode == 0, (
            f"dry-run must not invoke any CLI; stderr was: {result.stderr}"
        )


# ── 3. Aggregator + viewer smoke ─────────────────────────────────────────────


def _build_fixture_iteration(tmp_path: Path) -> Path:
    """Create a minimal iteration directory with one eval and paired runs."""
    iter_dir = tmp_path / "iteration-1"
    for cond, pass_rate, duration, tokens in [("with_skill", 1.0, 18000, 4100), ("without_skill", 0.0, 9500, 2200)]:
        run = iter_dir / "eval-001" / cond
        (run / "outputs").mkdir(parents=True)
        (run / "outputs" / "response.txt").write_text(
            f"Response from {cond} run\n", encoding="utf-8"
        )
        (run / "outputs" / "run_metadata.json").write_text(
            json.dumps(
                {
                    "cli": "claude",
                    "skill_loaded": cond == "with_skill",
                    "duration_ms": duration,
                    "total_tokens": tokens,
                    "exit_code": 0,
                }
            ),
            encoding="utf-8",
        )
        (run / "grading.json").write_text(
            json.dumps(
                {
                    "eval_id": "eval-001",
                    "skill_loaded": cond == "with_skill",
                    "assertions": [
                        {"text": "fixture assertion", "passed": pass_rate == 1.0, "evidence": "fixture"}
                    ],
                    "pass_rate": pass_rate,
                }
            ),
            encoding="utf-8",
        )
    return iter_dir


def _add_raw_memory_run(iter_dir: Path) -> Path:
    """Add the optional third arm to the fixture iteration."""
    run = iter_dir / "eval-001" / "raw_memory"
    (run / "outputs").mkdir(parents=True)
    (run / "outputs" / "response.txt").write_text(
        "Response from raw memory run\n", encoding="utf-8"
    )
    (run / "outputs" / "run_metadata.json").write_text(
        json.dumps(
            {
                "cli": "claude",
                "skill_loaded": False,
                "memory_injected": True,
                "duration_ms": 14000,
                "total_tokens": 3300,
                "exit_code": 0,
            }
        ),
        encoding="utf-8",
    )
    (run / "grading.json").write_text(
        json.dumps(
            {
                "eval_id": "eval-001",
                "skill_loaded": False,
                "assertions": [
                    {"text": "fixture assertion", "passed": True, "evidence": "fixture"}
                ],
                "pass_rate": 1.0,
            }
        ),
        encoding="utf-8",
    )
    return run


def _read_run_metadata(run_dir: Path) -> dict:
    return json.loads((run_dir / "outputs" / "run_metadata.json").read_text(encoding="utf-8"))


def _write_run_metadata(run_dir: Path, metadata: dict) -> None:
    (run_dir / "outputs" / "run_metadata.json").write_text(
        json.dumps(metadata), encoding="utf-8"
    )


class TestRawMemoryDispatch:
    def test_declared_source_runs_through_existing_dispatcher(
        self, optimizer_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        evals_dir = tmp_path / "evals"
        notes_dir = evals_dir / "notes"
        notes_dir.mkdir(parents=True)
        raw_text = "attempt one failed\nattempt two succeeded\n"
        (notes_dir / "raw-memory.md").write_text(raw_text, encoding="utf-8")
        evals_path = evals_dir / "evals.json"
        entry = {
            "id": "eval-raw",
            "query": "Solve the boundary problem.",
            "raw_memory": "notes/raw-memory.md",
            "model": "fixture-model",
        }
        evals_path.write_text(json.dumps([entry]), encoding="utf-8")
        captured: dict = {}

        def fake_invoke(cli: str, prompt: str, skill_path: Path | None, model: str | None):
            captured.update(cli=cli, prompt=prompt, skill_path=skill_path, model=model)
            return {
                "stdout": "fixture response",
                "stderr": "",
                "exit_code": 0,
                "duration_ms": 123,
                "started_at": "2026-08-28T00:00:00Z",
                "finished_at": "2026-08-28T00:00:01Z",
            }

        monkeypatch.setattr(optimizer_module, "invoke_cli", fake_invoke)
        run_dir = optimizer_module.run_raw_memory_condition(
            "claude", evals_path, entry, tmp_path / "iteration-1"
        )

        assert run_dir == tmp_path / "iteration-1" / "eval-raw" / "raw_memory"
        assert captured["cli"] == "claude"
        assert captured["skill_path"] is None
        assert captured["model"] == "fixture-model"
        assert captured["prompt"].startswith(entry["query"])
        assert captured["prompt"].endswith(raw_text)
        metadata = _read_run_metadata(run_dir)
        assert metadata["skill_loaded"] is False
        assert metadata["memory_injected"] is True
        assert metadata["exit_code"] == 0
        assert (run_dir / "outputs" / "response.txt").read_text(encoding="utf-8") == "fixture response"

    def test_missing_source_is_not_run_and_does_not_dispatch(
        self, optimizer_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        evals_path = tmp_path / "evals.json"
        entry = {"id": "eval-raw", "query": "test", "raw_memory": "missing.md"}
        evals_path.write_text(json.dumps([entry]), encoding="utf-8")

        def unexpected_dispatch(*args, **kwargs):
            raise AssertionError("missing raw memory must not invoke a CLI")

        monkeypatch.setattr(optimizer_module, "invoke_cli", unexpected_dispatch)
        report = optimizer_module.run_declared_raw_memory_evals(
            "codex", evals_path, [entry], tmp_path / "iteration-1"
        )
        assert report == {"mode": "raw-memory", "run": [], "not_run": ["eval-raw"]}
        assert not (tmp_path / "iteration-1" / "eval-raw" / "raw_memory").exists()

    def test_undecodable_source_is_not_run_and_does_not_dispatch(
        self, optimizer_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        evals_path = tmp_path / "evals.json"
        source = tmp_path / "raw-memory.bin"
        source.write_bytes(b"\xff\xfe\x00")
        entry = {"id": "eval-raw", "query": "test", "raw_memory": source.name}
        evals_path.write_text(json.dumps([entry]), encoding="utf-8")

        def unexpected_dispatch(*args, **kwargs):
            raise AssertionError("undecodable raw memory must not invoke a CLI")

        monkeypatch.setattr(optimizer_module, "invoke_cli", unexpected_dispatch)
        report = optimizer_module.run_declared_raw_memory_evals(
            "claude", evals_path, [entry], tmp_path / "iteration-1"
        )
        assert report == {"mode": "raw-memory", "run": [], "not_run": ["eval-raw"]}
        assert not (tmp_path / "iteration-1" / "eval-raw" / "raw_memory").exists()


class TestAggregator:
    def test_aggregator_emits_benchmark_json_and_md(self, tmp_path: Path) -> None:
        iter_dir = _build_fixture_iteration(tmp_path)
        result = subprocess.run(
            [sys.executable, str(_AGGREGATOR), str(iter_dir)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"aggregator failed: {result.stderr}"
        bj = iter_dir / "benchmark.json"
        bm = iter_dir / "benchmark.md"
        assert bj.exists() and bm.exists()
        data = json.loads(bj.read_text(encoding="utf-8"))
        assert data["n_evals"] == 1
        assert data["overall"]["with_skill_pass_rate"] == 1.0
        assert data["overall"]["without_skill_pass_rate"] == 0.0
        assert data["overall"]["pass_rate_delta"] == 1.0
        assert data["by_eval"]["eval-001"]["raw_memory"] == "not_run"
        assert data["overall"]["raw_memory"] == "not_run"

    def test_aggregator_includes_present_raw_memory_arm(self, tmp_path: Path) -> None:
        iter_dir = _build_fixture_iteration(tmp_path)
        raw_memory_dir = _add_raw_memory_run(iter_dir)
        assert raw_memory_dir.is_dir()

        result = subprocess.run(
            [sys.executable, str(_AGGREGATOR), str(iter_dir)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"aggregator failed: {result.stderr}"
        data = json.loads((iter_dir / "benchmark.json").read_text(encoding="utf-8"))
        assert data["by_eval"]["eval-001"]["raw_memory"]["status"] == "run"
        assert data["by_eval"]["eval-001"]["raw_memory"]["pass_rate"] == 1.0
        assert data["overall"]["raw_memory"] == {
            "status": "run",
            "n_evals": 1,
            "pass_rate": 1.0,
            "duration_ms_mean": 14000.0,
            "tokens_mean": 3300.0,
        }

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("memory_injected", False, "memory_injected must be true"),
            ("skill_loaded", True, "skill_loaded must be false"),
            ("exit_code", 9, "exit_code must be 0"),
            ("cli", "gemini", "cli must match both paired runs"),
        ],
    )
    def test_aggregator_rejects_invalid_raw_memory_metadata(
        self, tmp_path: Path, field: str, value: object, message: str
    ) -> None:
        iter_dir = _build_fixture_iteration(tmp_path)
        run_dir = _add_raw_memory_run(iter_dir)
        metadata = _read_run_metadata(run_dir)
        metadata[field] = value
        _write_run_metadata(run_dir, metadata)

        result = subprocess.run(
            [sys.executable, str(_AGGREGATOR), str(iter_dir)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"aggregator failed: {result.stderr}"
        data = json.loads((iter_dir / "benchmark.json").read_text(encoding="utf-8"))
        raw = data["by_eval"]["eval-001"]["raw_memory"]
        assert raw["status"] == "invalid"
        assert message in raw["errors"]
        assert data["overall"]["raw_memory"] == {
            "status": "invalid", "n_evals": 0, "invalid_evals": ["eval-001"]
        }

    def test_aggregator_rejects_missing_raw_memory_metadata(self, tmp_path: Path) -> None:
        iter_dir = _build_fixture_iteration(tmp_path)
        run_dir = _add_raw_memory_run(iter_dir)
        (run_dir / "outputs" / "run_metadata.json").unlink()

        subprocess.run(
            [sys.executable, str(_AGGREGATOR), str(iter_dir)],
            capture_output=True, text=True, timeout=30, check=True,
        )
        data = json.loads((iter_dir / "benchmark.json").read_text(encoding="utf-8"))
        raw = data["by_eval"]["eval-001"]["raw_memory"]
        assert raw["status"] == "invalid"
        assert "missing or invalid outputs/run_metadata.json" in raw["errors"]


class TestViewerStaticMode:
    def test_static_html_renders_without_errors(self, tmp_path: Path) -> None:
        iter_dir = _build_fixture_iteration(tmp_path)
        # Run the aggregator first so benchmark.json exists.
        subprocess.run(
            [sys.executable, str(_AGGREGATOR), str(iter_dir)],
            capture_output=True, text=True, timeout=30, check=True,
        )
        out_html = tmp_path / "review.html"
        result = subprocess.run(
            [
                sys.executable, str(_VIEWER), str(iter_dir),
                "--static", str(out_html),
            ],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"viewer failed: {result.stderr}"
        assert out_html.exists()
        body = out_html.read_text(encoding="utf-8")
        assert "skill-eval-loop viewer" in body
        assert "eval-001" in body
        assert "with_skill" in body and "without_skill" in body
        assert "submitFeedback" in body  # the JS handler is wired in
        assert "<wbr>" in body

    def test_static_html_renders_raw_memory_when_present(self, tmp_path: Path) -> None:
        iter_dir = _build_fixture_iteration(tmp_path)
        _add_raw_memory_run(iter_dir)
        subprocess.run(
            [sys.executable, str(_AGGREGATOR), str(iter_dir)],
            capture_output=True, text=True, timeout=30, check=True,
        )
        out_html = tmp_path / "review.html"
        subprocess.run(
            [sys.executable, str(_VIEWER), str(iter_dir), "--static", str(out_html)],
            capture_output=True, text=True, timeout=30, check=True,
        )
        body = out_html.read_text(encoding="utf-8")
        assert "raw_memory (prior notes)" in body
        assert "Response from raw memory run" in body


# ── 4. Trigger-testing techniques (v2.3.0 Phase 4 / T014-T015) ───────────────


@pytest.fixture
def optimizer_module():
    """Import optimize_skill_description.py as a module to call its pure helpers."""
    return _load_module(_OPTIMIZER)


def _stream_line(*tool_names: str) -> str:
    """One stream-json assistant event whose content holds the given tool_use blocks."""
    return json.dumps(
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "name": name, "input": {}} for name in tool_names
                ]
            },
        }
    )


class TestPrematureActionDetection:
    """T014: flag a with_skill run that acted before loading the skill."""

    def test_tool_use_before_skill_flags_true(self, optimizer_module) -> None:
        stream = "\n".join([_stream_line("Bash"), _stream_line("Skill")])
        assert optimizer_module.detect_premature_action(stream) is True

    def test_skill_first_flags_false(self, optimizer_module) -> None:
        stream = "\n".join([_stream_line("Skill"), _stream_line("Bash")])
        assert optimizer_module.detect_premature_action(stream) is False

    def test_todowrite_before_skill_is_allowed(self, optimizer_module) -> None:
        assert optimizer_module.detect_premature_action(["TodoWrite", "Skill", "Bash"]) is False

    def test_skill_never_loads_with_real_tool_flags_true(self, optimizer_module) -> None:
        assert optimizer_module.detect_premature_action(["Bash", "Edit"]) is True

    def test_clean_planning_only_stream_flags_false(self, optimizer_module) -> None:
        assert optimizer_module.detect_premature_action(["TodoWrite", "Skill"]) is False

    def test_empty_stream_flags_false(self, optimizer_module) -> None:
        assert optimizer_module.detect_premature_action("") is False

    def test_extract_tool_invocations_preserves_order(self, optimizer_module) -> None:
        stream = "\n".join(
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {"type": "text", "text": "thinking out loud"},
                                {"type": "tool_use", "name": "TodoWrite", "input": {}},
                            ]
                        },
                    }
                ),
                _stream_line("Skill"),
            ]
        )
        assert optimizer_module.extract_tool_invocations(stream) == ["TodoWrite", "Skill"]

    def test_extract_tool_invocations_handles_single_json_array(self, optimizer_module) -> None:
        events = [
            {"type": "tool_use", "name": "Grep"},
            {"type": "tool_use", "name": "Skill"},
        ]
        assert optimizer_module.extract_tool_invocations(json.dumps(events)) == ["Grep", "Skill"]


class TestMultiTurnTriggering:
    """T015: replay an ordered turns list and assert the skill triggers on time."""

    def test_is_multi_turn_detects_turns(self, optimizer_module) -> None:
        assert optimizer_module.is_multi_turn({"id": "e", "turns": ["a", "b"]}) is True
        assert optimizer_module.is_multi_turn({"id": "e", "query": "a"}) is False
        assert optimizer_module.is_multi_turn({"id": "e", "turns": []}) is False

    def test_first_trigger_turn(self, optimizer_module) -> None:
        assert optimizer_module.first_trigger_turn([False, False, True]) == 3
        assert optimizer_module.first_trigger_turn([True, False]) == 1
        assert optimizer_module.first_trigger_turn([False, False]) is None

    def test_multi_turn_passes_on_designated_turn(self, optimizer_module) -> None:
        assert optimizer_module.multi_turn_passes([False, False, True], 3) is True

    def test_multi_turn_fails_when_triggering_too_early(self, optimizer_module) -> None:
        assert optimizer_module.multi_turn_passes([True, False, False], 3) is False

    def test_multi_turn_fails_when_never_triggering(self, optimizer_module) -> None:
        assert optimizer_module.multi_turn_passes([False, False, False], 3) is False


class TestCheapModelThreading:
    """T015: the --model flag threads through the dispatcher into every CLI branch."""

    @pytest.mark.parametrize("cli", _SUPPORTED_CLIS)
    def test_build_cli_command_threads_model(self, optimizer_module, cli: str) -> None:
        cmd = optimizer_module.build_cli_command(cli, "do a thing", Path("SKILL.md"), model="haiku")
        assert cmd[0] == cli
        assert "--model" in cmd
        assert "haiku" in cmd

    @pytest.mark.parametrize("cli", _SUPPORTED_CLIS)
    def test_build_cli_command_omits_model_by_default(self, optimizer_module, cli: str) -> None:
        cmd = optimizer_module.build_cli_command(cli, "do a thing", Path("SKILL.md"))
        assert cmd[0] == cli
        assert "--model" not in cmd

    def test_model_flag_surfaces_in_dry_run(self, fixture_skill_and_evals: tuple[Path, Path]) -> None:
        skill_md, evals = fixture_skill_and_evals
        result = subprocess.run(
            [
                sys.executable, str(_OPTIMIZER),
                "--skill", str(skill_md),
                "--evals", str(evals),
                "--cli", "claude",
                "--model", "haiku",
                "--dry-run",
            ],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"dry-run with --model failed: {result.stderr}"
        report = json.loads(result.stdout)
        assert report["model"] == "haiku"


class TestPrematureActionInBenchmark:
    """T014: the aggregator surfaces premature_action per-eval in benchmark.json."""

    def test_aggregator_surfaces_premature_action(self, tmp_path: Path) -> None:
        iter_dir = _build_fixture_iteration(tmp_path)
        grading_path = iter_dir / "eval-001" / "with_skill" / "grading.json"
        data = json.loads(grading_path.read_text(encoding="utf-8"))
        data["premature_action"] = True
        grading_path.write_text(json.dumps(data), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(_AGGREGATOR), str(iter_dir)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"aggregator failed: {result.stderr}"
        bench = json.loads((iter_dir / "benchmark.json").read_text(encoding="utf-8"))
        assert bench["by_eval"]["eval-001"]["premature_action"] is True
        assert bench["by_eval"]["eval-001"]["with_skill"]["premature_action"] is True
        # The baseline run has no skill to load, so it defaults to False.
        assert bench["by_eval"]["eval-001"]["without_skill"]["premature_action"] is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
