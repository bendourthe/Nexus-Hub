"""End-to-end tests for the serial local pairing runner (v4.15.2, Phase 3).

Everything here uses trusted fake adapters and a synthetic workload. No test needs
a provider credential, network access, or a real harness. Child processes are
started without a console window, and every test works in its own temporary root.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "harness_pairings"
SCRIPT = ROOT / "scripts" / "evaluate_harness_pairings.py"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import evaluate_harness_pairings as runner  # noqa: E402

_spec = importlib.util.spec_from_file_location("harness_pairing_oracle", FIXTURES / "oracle.py")
oracle = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(oracle)

BEHAVIORS = (
    "benign", "wrong-but-claims-success", "failing", "hang", "malformed", "binary", "big",
    "extra-fields", "hostile", "escape", "tamper",
)


class Env:
    """A throwaway evaluation environment rooted in one temporary directory."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.workload = tmp / "workload"
        import shutil

        shutil.copytree(FIXTURES / "workloads" / "echo", self.workload)
        self.adapters = tmp / "adapters"
        self.adapters.mkdir()
        self.out = tmp / "out"
        self.work = tmp / "work"
        self.extra_env: dict[str, dict[str, str]] = {}
        self.write_profiles()

    def write_profiles(self) -> None:
        for name in BEHAVIORS:
            profile = {
                "schema": "harness-adapter/1", "name": name, "kind": "fake", "timeout_s": 30,
                "argv": ["{python}", str(FIXTURES / "adapters" / "fake_adapter.py"), name],
                "env_set": self.extra_env.get(name, {}),
            }
            (self.adapters / f"{name}.json").write_text(json.dumps(profile), encoding="utf-8")

    def manifest(self, adapters: list[tuple[str, str, str]], repeats: int = 3, time_s: int = 20,
                 run_id: str = "e2e-run", mode: str = "synthetic") -> dict:
        pairings = []
        for pid, adapter, variant in adapters:
            path = f"{variant}.md"
            size, digest, tokens = runner.instruction_figures(FIXTURES / "instructions" / path)
            pairings.append({
                "id": pid,
                "harness": {"name": "fake-harness", "version": "1.0.0", "adapter": adapter, "adapter_version": "1"},
                "model": {"id": "fixture-model", "identity": "fixture-model-2026-11"},
                "instruction": {"variant": variant, "skill_index_mode": variant, "hash": digest, "bytes": size,
                                "tokens_estimated": tokens, "path": path},
                "tool_schema_hash": "sha256:" + "a" * 64,
                "isolation_mode": mode,
                "budgets": {"time_s": time_s, "turns": 5, "spend_usd": 5.0 if mode == "metered-live" else None,
                            "spend_enforcement": "provider" if mode == "metered-live" else "none"},
            })
        return {
            "schema": "harness-pairing-manifest/1", "run_id": run_id,
            "workload": {
                "id": "wl-synthetic-echo", "revision": "r1",
                "hash": runner.tree_hash(self.workload, ("evaluator",)),
                "evaluator_revision": "e1", "evaluator_hash": runner.tree_hash(self.workload / "evaluator"),
                "budget_class": "synthetic-small",
                "policy": {"min_success_rate": 0.6, "max_latency_s": 20, "max_cost_usd": None,
                           "tie_break": "lowest-instruction-tokens"},
            },
            "environment": {
                "os": "test", "arch": "test", "repo_revision": "0" * 40, "harness_configuration": "defaults",
                "model_parameters": {"temperature": 0}, "cache_policy": "cold", "concurrency": 1,
                "retry_policy": "none", "pricing": {"basis": "fixture", "date": "2026-11-01"},
            },
            "pairings": pairings, "repeats": repeats, "seed": 7, "order_policy": "alternating",
        }

    def run(self, manifest: dict, **kwargs):
        return runner.run_matrix(manifest, self.workload, self.adapters, FIXTURES / "instructions", self.out,
                                 self.work, **kwargs)


@pytest.fixture()
def env(tmp_path: Path) -> Env:
    return Env(tmp_path)


def _receipts(result: dict) -> list[dict]:
    run_dir = Path(result["run_dir"])
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(run_dir.glob("trial-*.json"))]


def _one(env: Env, behavior: str, **kwargs) -> dict:
    manifest = env.manifest([("p", behavior, "full")], repeats=1, **kwargs)
    return _receipts(env.run(manifest))[0]


# ----------------------------------------------------------------- preflight


def test_dry_run_plans_without_creating_workspaces_or_receipts(env: Env) -> None:
    manifest = env.manifest([("a", "benign", "full"), ("b", "failing", "pointer")])
    result = env.run(manifest, dry_run=True)
    assert result["dry_run"] is True
    assert result["plan"]["trials"] == 6
    assert result["plan"]["order"] == ["a", "b", "b", "a", "a", "b"]
    assert not env.out.exists() and not env.work.exists()


@pytest.mark.parametrize("breaker,code", [
    (lambda m: m.pop("environment"), "manifest-invalid"),
    (lambda m: m["pairings"][0]["harness"].update(adapter="no-such-adapter"), "adapter-missing"),
    (lambda m: m["pairings"][0]["harness"].update(adapter="../escape"), "adapter-name"),
    (lambda m: m["workload"].update(hash="sha256:" + "0" * 64), "workload-hash"),
    (lambda m: m["workload"].update(evaluator_hash="sha256:" + "0" * 64), "evaluator-hash"),
    (lambda m: m["pairings"][0]["instruction"].update(tokens_estimated=1), "instruction-figures"),
    (lambda m: m["pairings"][0]["instruction"].update(path="../../outside.md"), "instruction-path"),
    (lambda m: m["pairings"].append(copy.deepcopy(m["pairings"][0])), "manifest-invalid"),
])
def test_unsafe_or_inconsistent_input_fails_before_any_workspace_exists(env: Env, breaker, code: str) -> None:
    manifest = env.manifest([("a", "benign", "full")])
    breaker(manifest)
    with pytest.raises(runner.PreflightError) as caught:
        env.run(manifest)
    assert caught.value.code == code
    assert not env.work.exists() and not env.out.exists()


def test_missing_binary_and_credential_environment_are_typed_preflight_failures(env: Env) -> None:
    manifest = env.manifest([("a", "benign", "full")])
    profile = env.adapters / "benign.json"
    data = json.loads(profile.read_text(encoding="utf-8"))
    data["argv"] = ["definitely-not-an-installed-binary-xyz"]
    profile.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(runner.PreflightError) as caught:
        env.run(manifest)
    assert caught.value.code == "binary-absent"
    data["argv"] = ["{python}", "x.py"]
    data["env_set"] = {"SERVICE_API_KEY": "placeholder"}
    profile.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(runner.PreflightError) as caught:
        env.run(manifest)
    assert caught.value.code == "adapter-credential-env"


def test_string_command_profiles_are_rejected_not_passed_to_a_shell(env: Env) -> None:
    profile = env.adapters / "benign.json"
    data = json.loads(profile.read_text(encoding="utf-8"))
    data["argv"] = "python fake_adapter.py benign"
    profile.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(runner.PreflightError) as caught:
        env.run(env.manifest([("a", "benign", "full")]))
    assert caught.value.code == "adapter-argv"


@pytest.mark.parametrize("mode", ["metered-live", "observational-live"])
def test_live_modes_are_rejected_without_a_proven_isolation_backend(env: Env, mode: str) -> None:
    manifest = env.manifest([("a", "benign", "full")], mode=mode)
    with pytest.raises(runner.PreflightError) as caught:
        env.run(manifest)
    assert caught.value.code == "isolation-backend-unavailable"
    assert "needs-live-validation" in caught.value.detail
    assert not env.work.exists()


def test_metered_live_with_post_hoc_spend_control_is_a_manifest_error(env: Env) -> None:
    manifest = env.manifest([("a", "benign", "full")], mode="metered-live")
    manifest["pairings"][0]["budgets"]["spend_enforcement"] = "none"
    with pytest.raises(runner.PreflightError) as caught:
        env.run(manifest)
    assert caught.value.code == "manifest-invalid"
    assert "post-hoc" in caught.value.detail


def test_a_second_run_with_the_same_id_collides_and_never_resumes(env: Env) -> None:
    manifest = env.manifest([("a", "benign", "full")], repeats=1)
    env.run(manifest)
    with pytest.raises(runner.PreflightError) as caught:
        env.run(manifest)
    assert caught.value.code == "output-collision"


# ------------------------------------------------------------ synthetic matrix


def test_synthetic_matrix_matches_the_independent_oracle_end_to_end(env: Env) -> None:
    manifest = env.manifest([("pair-full", "benign", "full"), ("pair-pointer", "failing", "pointer")])
    assert oracle.validate_manifest(manifest) == []
    result = env.run(manifest)
    trials = _receipts(result)
    assert len(trials) == 6 and result["state"] == "complete"
    for trial in trials:
        assert oracle.validate_trial(trial, manifest) == [], oracle.validate_trial(trial, manifest)
    produced = json.loads((Path(result["run_dir"]) / "aggregate.json").read_text(encoding="utf-8"))
    assert produced.pop("run_state") == "complete"
    expected = oracle.aggregate(manifest, trials)
    assert produced == expected
    by_id = {p["pairing_id"]: p for p in produced["pairings"]}
    assert by_id["pair-full"]["successes"] == 3 and by_id["pair-pointer"]["successes"] == 0
    assert produced["recommendation"]["state"] == "no-recommendation"
    assert (Path(result["run_dir"]) / "report.md").read_text(encoding="utf-8").startswith("# Harness Pairing Report")
    assert not any(env.work.iterdir()), "workspaces must be cleaned after a normal run"


def test_full_against_pointer_pair_records_distinct_hashes_and_measurer_tokens(env: Env) -> None:
    manifest = env.manifest([("pair-full", "benign", "full"), ("pair-pointer", "benign", "pointer")])
    result = env.run(manifest)
    aggregate = {p["pairing_id"]: p for p in result["aggregate"]["pairings"]}
    full_inst, pointer_inst = (p["instruction"] for p in manifest["pairings"])
    assert full_inst["hash"] != pointer_inst["hash"]
    for variant, pid in (("full", "pair-full"), ("pointer", "pair-pointer")):
        text = (FIXTURES / "instructions" / f"{variant}.md").read_text(encoding="utf-8")
        assert aggregate[pid]["instruction_tokens_estimated"] == oracle.measurer_tokens(text)
    assert aggregate["pair-full"]["instruction_tokens_estimated"] > aggregate["pair-pointer"]["instruction_tokens_estimated"]
    for pairing in aggregate.values():
        assert pairing["organic_skills"] == {"unavailable": "needs-live-validation"}
    frozen = json.loads((FIXTURES / "variant-pair.expected.json").read_text(encoding="utf-8"))
    assert frozen["organic_skills"] == "needs-live-validation"
    assert frozen["pair"] == ["full", "pointer"]
    assert frozen["tokens"]["full"] > frozen["tokens"]["pointer"]


def test_the_workload_evaluator_not_the_adapter_decides_success(env: Env) -> None:
    trial = _one(env, "wrong-but-claims-success")
    assert trial["harness_claim_success"] is True
    assert trial["evaluator_success"] is False and trial["outcome"] == "failure"
    assert trial["failure_fingerprint"].startswith("fp-")


def test_a_hanging_adapter_is_terminated_with_its_whole_process_tree(env: Env) -> None:
    pid_file = env.tmp / "child.pid"
    env.extra_env["hang"] = {"CHILD_PID_FILE": str(pid_file)}
    env.write_profiles()
    started = time.monotonic()
    trial = _one(env, "hang", time_s=2)
    assert trial["outcome"] == "timeout" and trial["evaluator_success"] is False
    assert time.monotonic() - started < 25
    child = int(pid_file.read_text(encoding="utf-8"))
    for _ in range(40):
        if not _pid_alive(child):
            break
        time.sleep(0.25)
    assert not _pid_alive(child), "the adapter's child process survived the timeout"


def _pid_alive(pid: int) -> bool:
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                             creationflags=NO_WINDOW, check=False).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


@pytest.mark.parametrize("behavior", ["malformed", "binary", "big", "extra-fields"])
def test_malformed_or_hostile_protocol_output_is_a_typed_error_that_cannot_assert_success(
    env: Env, behavior: str
) -> None:
    trial = _one(env, behavior)
    assert trial["outcome"] == "adapter-protocol-error"
    assert trial["evaluator_success"] is False
    assert oracle.validate_trial(trial, env.manifest([("p", behavior, "full")], repeats=1)) == []


def test_hostile_text_is_redacted_and_escaped_before_it_reaches_any_artifact(env: Env) -> None:
    canary = "s" + "k-" + "abcdefghijklmnopqrstuvwxyz"
    os.environ["CANARY_PARENT_API_TOKEN"] = "parent-secret-canary-value"
    try:
        manifest = env.manifest([("p", "hostile", "full")], repeats=1)
        result = env.run(manifest)
    finally:
        del os.environ["CANARY_PARENT_API_TOKEN"]
    blob = ""
    for path in Path(result["run_dir"]).glob("*"):
        blob += path.read_text(encoding="utf-8")
    for needle in (canary, "\x1b", "parent-secret-canary-value", "<b>"):
        assert needle not in blob
    trial = _receipts(result)[0]
    assert "[REDACTED:secret]" in trial["organic_skills"]
    assert any(s.startswith("\\## Recommendation") for s in trial["organic_skills"])
    assert oracle.validate_trial(trial, manifest) == []
    assert trial["guard_skills"] == ["security-review"]


def test_child_environment_is_an_explicit_minimal_set_not_inherited(monkeypatch) -> None:
    monkeypatch.setenv("CANARY_API_KEY", "x")
    monkeypatch.setenv("HOME_SECRET", "y")
    assert "CANARY_API_KEY" not in runner.base_env() and "HOME_SECRET" not in runner.base_env()


def test_evaluator_tampering_is_a_containment_failure_and_never_a_success(env: Env) -> None:
    target = env.workload / "evaluator" / "expected.txt"
    env.extra_env["tamper"] = {"TAMPER_TARGET": str(target)}
    env.write_profiles()
    manifest = env.manifest([("p", "tamper", "full")], repeats=1)
    trial = _receipts(env.run(manifest))[0]
    assert trial["outcome"] == "containment-failure"
    assert trial["evaluator_success"] is False
    assert trial["harness_claim_success"] is True


def test_synthetic_mode_is_workspace_separated_not_isolated_and_live_stays_closed(env: Env) -> None:
    sentinel = env.tmp / "external-sentinel.txt"
    env.extra_env["escape"] = {"EXTERNAL_SENTINEL": str(sentinel)}
    env.write_profiles()
    trial = _one(env, "escape")
    # Synthetic mode does not contain the adapter, so the write happens. This is why
    # the label is workspace-separated and why live execution has no synthetic path.
    assert sentinel.is_file()
    assert trial["isolation_mode"] == "synthetic"
    assert runner.isolation_backend_proven() is False


def test_cleanup_removes_only_sentinel_owned_roots_inside_the_work_root(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    owned = work / "owned"
    owned.mkdir()
    (owned / runner.SENTINEL).write_text("tok", encoding="utf-8")
    foreign = work / "foreign"
    foreign.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / runner.SENTINEL).write_text("tok", encoding="utf-8")
    assert runner.cleanup_workspace(owned, work, "tok") == "removed" and not owned.exists()
    assert runner.cleanup_workspace(owned.parent / "foreign", work, "tok") == "manual-cleanup-needed"
    assert foreign.exists()
    assert runner.cleanup_workspace(outside, work, "tok") == "manual-cleanup-needed"
    assert outside.exists()
    wrong = work / "wrong-token"
    wrong.mkdir()
    (wrong / runner.SENTINEL).write_text("other", encoding="utf-8")
    assert runner.cleanup_workspace(wrong, work, "tok") == "manual-cleanup-needed"


def test_an_interrupted_run_still_leaves_schema_valid_receipts(env: Env) -> None:
    manifest = env.manifest([("a", "benign", "full"), ("b", "benign", "pointer")])
    result = env.run(manifest, stop_after=3)
    assert result["state"] == "interrupted"
    trials = _receipts(result)
    assert len(trials) == 3
    for trial in trials:
        assert oracle.validate_trial(trial, manifest) == []
    aggregate = json.loads((Path(result["run_dir"]) / "aggregate.json").read_text(encoding="utf-8"))
    assert aggregate["run_state"] == "interrupted" and sum(p["trials"] for p in aggregate["pairings"]) == 3
    with pytest.raises(runner.PreflightError):
        env.run(manifest)


def test_duplicate_receipt_paths_fail_closed(tmp_path: Path) -> None:
    target = tmp_path / "receipt.json"
    runner.write_new(target, "{}")
    with pytest.raises(FileExistsError):
        runner.write_new(target, "{}")


def test_zero_eligible_trials_is_nonzero_unless_run_as_a_probe(env: Env) -> None:
    # An evaluator that cannot score leaves every trial non-rankable: a no-data run.
    (env.workload / "evaluator" / "evaluate.py").write_text("raise SystemExit(5)\n", encoding="utf-8")
    manifest = env.manifest([("a", "benign", "full")], repeats=1, run_id="no-data")
    path = _write(env, manifest)
    base = [sys.executable, str(SCRIPT), "run", "--manifest", str(path), "--workload-root", str(env.workload),
            "--adapters-dir", str(env.adapters), "--instruction-root", str(FIXTURES / "instructions"),
            "--work-root", str(env.work)]
    strict = subprocess.run(base + ["--out-dir", str(env.out)], capture_output=True, text=True,
                            creationflags=NO_WINDOW, check=False)
    assert strict.returncode == 1, strict.stdout + strict.stderr
    assert json.loads(strict.stdout)["rankable_trials"] == 0
    trial = json.loads(next((env.out / "no-data").glob("trial-*.json")).read_text(encoding="utf-8"))
    assert trial["outcome"] == "evaluator-error" and trial["evaluator_success"] is None
    manifest["run_id"] = "no-data-probe"
    probe_args = base[:4] + [str(_write(env, manifest))] + base[5:] + ["--out-dir", str(env.out), "--probe"]
    probe = subprocess.run(probe_args, capture_output=True, text=True, creationflags=NO_WINDOW, check=False)
    assert probe.returncode == 0, probe.stdout + probe.stderr


def _write(env: Env, manifest: dict) -> Path:
    path = env.tmp / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


# ------------------------------------------------------------------------ CLI


def test_command_line_run_and_preflight_failure_exit_codes(env: Env) -> None:
    manifest = env.manifest([("a", "benign", "full")], repeats=1, run_id="cli-run")
    path = _write(env, manifest)
    base = [sys.executable, str(SCRIPT), "run", "--manifest", str(path), "--workload-root", str(env.workload),
            "--adapters-dir", str(env.adapters), "--instruction-root", str(FIXTURES / "instructions"),
            "--out-dir", str(env.out), "--work-root", str(env.work)]
    ok = subprocess.run(base, capture_output=True, text=True, creationflags=NO_WINDOW, check=False)
    assert ok.returncode == 0, ok.stderr + ok.stdout
    assert json.loads(ok.stdout)["rankable_trials"] == 1
    again = subprocess.run(base, capture_output=True, text=True, creationflags=NO_WINDOW, check=False)
    assert again.returncode == 2
    assert json.loads(again.stdout)["code"] == "output-collision"


# --------------------------------------------------- Claude Code and Codex profiles


def test_builtin_profiles_are_argv_arrays_without_credentials_or_shell_strings() -> None:
    profiles = sorted((ROOT / "configs" / "harness-adapters").glob("*.json"))
    assert [p.stem for p in profiles] == ["claude-code", "codex"]
    for path in profiles:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["schema"] == "harness-adapter/1" and data["kind"] == "cli"
        for key in ("argv", "version_argv"):
            assert isinstance(data[key], list) and all(isinstance(a, str) for a in data[key])
        assert "env_allow" not in data and "env_set" not in data
        assert "unverified" in data["live_argv_status"]
        runner.load_adapter(path.parent, path.stem)


def test_credential_free_conformance_never_raises_and_reports_typed_status() -> None:
    rows = runner.conformance(ROOT / "configs" / "harness-adapters")
    assert {r["adapter"] for r in rows} == {"claude-code", "codex"}
    for row in rows:
        assert row["status"] in ("ok", "binary-absent", "version-probe-failed"), row
    result = subprocess.run([sys.executable, str(SCRIPT), "conformance"], capture_output=True, text=True,
                            creationflags=NO_WINDOW, check=False)
    assert result.returncode in (0, 1)
    assert json.loads(result.stdout)


def test_guide_and_command_line_agree_on_flags_codes_and_defaults() -> None:
    guide = (ROOT / "guides" / "reference" / "HARNESS_PAIRING_EVALUATION.md").read_text(encoding="utf-8")
    helped = subprocess.run([sys.executable, str(SCRIPT), "run", "--help"], capture_output=True, text=True,
                            creationflags=NO_WINDOW, check=False).stdout
    for flag in ("--dry-run", "--probe", "--out-dir", "--workload-root", "--adapters-dir"):
        assert flag in helped and flag in guide, flag
    for needle in ("isolation-backend-unavailable", "130", "needs-live-validation",
                   "containment-failure", str(runner.Z95), "2000"):
        assert needle in guide, needle
    assert runner.MIN_REPEATS == 3 and runner.BOOTSTRAP_RESAMPLES == 2000
    assert runner.MAX_FIELD_CHARS == oracle.MAX_FIELD_CHARS
    assert set(runner.TIE_BREAKS) == set(oracle.TIE_BREAKS)
    assert set(runner.ISOLATION_MODES) == set(oracle.ISOLATION_MODES)


def test_script_documents_its_contract_and_is_listed_as_repo_internal() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "HARNESS_PAIRING_EVALUATION.md" in text and "shell=False" in text
    smoke = (ROOT / "catalog" / "hooks" / "tests" / "test_installer_smoke.py").read_text(encoding="utf-8")
    assert '"evaluate_harness_pairings.py"' in smoke
