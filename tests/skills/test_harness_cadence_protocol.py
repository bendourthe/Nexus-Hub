"""Drive the v4.15.2 pairing evaluator with the credential-free feedback-cadence matrix.

The evaluator is the only engine. It runs one adapter per trial and one final,
workload-owned evaluator, so it cannot record feedback timing itself. The fake
adapter below therefore performs a real check against its workspace at the steps
its schedule permits and records a sidecar history; the tests read that sidecar.
Everything is synthetic: no model, credential, network or paid runner is used.
"""

from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CADENCE = ROOT / "tests/fixtures/harness_pairings/v4.15.3-cadence"
WORKLOAD = ROOT / "tests/fixtures/harness_pairings/workloads/echo"
INSTRUCTIONS = ROOT / "tests/fixtures/harness_pairings/instructions"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import evaluate_harness_pairings as runner  # noqa: E402

MANIFEST = json.loads((CADENCE / "manifest.json").read_text(encoding="utf-8"))
ADAPTER_DATA = json.loads((CADENCE / "fake-adapter.json").read_text(encoding="utf-8"))

ADAPTER_CODE = '''
import json, os, sys, time
from pathlib import Path

name = sys.argv[1]
cfg = json.loads(Path(os.environ["CADENCE_CONFIG"]).read_text(encoding="utf-8"))
schedule = cfg["schedules"][name]
request = json.loads(sys.stdin.read())
ws, idx, task = Path(request["workspace"]), request["trial_index"], cfg["task"]
target, wrong, started = task["target"], task["wrong"], time.time()
history, last_passed = [], None


def put(correct):
    (ws / task["file"]).write_text(target if correct else wrong, encoding="utf-8")


for step, event in enumerate(schedule["events"]):
    row = {"step": step, "event": event}
    if event == "draft":
        put(task["draft_correct"][idx])
    elif event == "draft_final":
        put(True)
    elif event == "draft_wrong":
        put(False)
    elif event == "check":
        last_passed = (ws / task["file"]).read_text(encoding="utf-8") == target
        row["passed"] = last_passed
    elif event == "repair":
        if last_passed is not False:
            continue
        put(task["repair_correct"][idx])
    elif event == "sleep":
        time.sleep(float(schedule["sleep_s"]))
    history.append(row)

out = Path(os.environ["CADENCE_HISTORY_DIR"]) / f"{name}-{idx}.json"
out.write_text(
    json.dumps({"schedule": name, "trial_index": idx, "events": history,
                "elapsed_s": round(time.time() - started, 3)}),
    encoding="utf-8",
)
print(json.dumps({"claimed_success": True}))
'''


class Rig:
    """One throwaway evaluation root: workload copy, adapter profiles, output dirs."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.workload = tmp / "workload"
        shutil.copytree(WORKLOAD, self.workload)
        for path in self.workload.rglob("*"):  # LF so the frozen hashes hold on every host
            if path.is_file():
                path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
        self.adapters = tmp / "adapters"
        self.adapters.mkdir()
        self.histories = tmp / "histories"
        self.histories.mkdir()
        self.out, self.work = tmp / "out", tmp / "work"
        (tmp / "adapter.py").write_text(ADAPTER_CODE, encoding="utf-8")
        for schedule in ADAPTER_DATA["schedules"]:
            self.profile(f"cadence-{schedule}", schedule)

    def profile(self, name: str, schedule: str, timeout_s: int = 30) -> None:
        body = {
            "schema": "harness-adapter/1",
            "name": name,
            "kind": "fake",
            "timeout_s": timeout_s,
            "argv": ["{python}", str(self.tmp / "adapter.py"), schedule],
            "env_set": {
                "CADENCE_CONFIG": str(CADENCE / "fake-adapter.json"),
                "CADENCE_HISTORY_DIR": str(self.histories),
            },
        }
        (self.adapters / f"{name}.json").write_text(json.dumps(body), encoding="utf-8")

    def run(self, manifest: dict | None = None, workload: Path | None = None) -> dict:
        return runner.run_matrix(
            manifest or copy.deepcopy(MANIFEST),
            workload or self.workload,
            self.adapters,
            INSTRUCTIONS,
            self.out,
            self.work,
        )


@pytest.fixture
def rig(tmp_path):
    return Rig(tmp_path)


def trials_of(rig, outcome):
    run_dir = Path(outcome["run_dir"])
    return [json.loads(p.read_text()) for p in sorted(run_dir.glob("trial-*.json"))]


def history_of(rig, schedule, index):
    path = rig.histories / f"{schedule}-{index}.json"
    return json.loads(path.read_text()) if path.is_file() else None


def summarize(history):
    events = history["events"]
    feedback = [e for e in events if e["event"] == "check"]
    finish = next(e["step"] for e in events if e["event"] == "finish")
    return {
        "first_feedback_step": feedback[0]["step"] if feedback else None,
        "finish_step": finish,
        "feedback_count": len(feedback),
        "repair_count": sum(e["event"] == "repair" for e in events),
        "initial_accepted": feedback[0]["passed"] if feedback else None,
        "post_repair_accepted": feedback[-1]["passed"] if feedback else None,
    }


def spend_per_accepted(trials):
    accepted = sum(t["evaluator_success"] is True for t in trials)
    costs = [t["cost_usd"] for t in trials]
    if accepted == 0:
        return {"unavailable": "no accepted artifact"}
    if any(isinstance(c, dict) for c in costs):
        return {"unavailable": "spend unavailable for at least one trial"}
    return sum(costs) / accepted


def check_protocol(rig, trials, ran=None):
    """Return error codes for a run that does not satisfy the frozen protocol.

    `ran` maps a pairing to the schedule its adapter actually executed; it
    defaults to the declared schedule.
    """
    errors = []
    schedules = MANIFEST["cadence_protocol"]["schedules"]
    for trial in trials:
        schedule = schedules[trial["pairing_id"]]
        executed = (ran or {}).get(trial["pairing_id"], schedule)
        history = history_of(rig, executed, trial["trial_index"])
        if history is None:
            errors.append(f"missing-history:{trial['pairing_id']}:{trial['trial_index']}")
            continue
        facts = summarize(history)
        if facts["feedback_count"] == 0:
            errors.append(f"no-feedback-delivered:{trial['pairing_id']}")
        elif schedule == "construction" and not facts["first_feedback_step"] < facts["finish_step"]:
            errors.append("construction-feedback-late")
        elif schedule == "final-gate" and not facts["first_feedback_step"] > facts["finish_step"]:
            errors.append("final-gate-feedback-early")
    if len({t["workload_hash"] for t in trials}) != 1:
        errors.append("grader-not-identical")
    return errors


def test_manifest_freezes_the_protocol_and_claims_nothing_live():
    protocol = MANIFEST["cadence_protocol"]
    assert protocol["claims"] == {
        "live_reliability": False,
        "savings": False,
        "ranking": False,
        "default_change": False,
    }
    assert protocol["frozen"]["repeat_minimum"] == runner.MIN_REPEATS <= MANIFEST["repeats"]
    assert {p["isolation_mode"] for p in MANIFEST["pairings"]} == {"synthetic"}
    assert runner.validate_manifest(MANIFEST) == []


def test_valid_schedules_differ_in_feedback_history_not_in_acceptance(rig):
    outcome = rig.run()
    assert outcome["state"] == "complete"
    trials = trials_of(rig, outcome)
    assert len(trials) == 6 and check_protocol(rig, trials) == []
    by_pairing = {}
    for t in trials:
        by_pairing.setdefault(t["pairing_id"], []).append(t["evaluator_success"])
    assert by_pairing["pair-construction"] == [True, True, False]
    assert by_pairing["pair-final-gate"] == [True, False, False]
    construction = [summarize(history_of(rig, "construction", i)) for i in range(3)]
    final_gate = [summarize(history_of(rig, "final-gate", i)) for i in range(3)]
    assert [c["initial_accepted"] for c in construction] == [True, False, False]
    assert [c["post_repair_accepted"] for c in construction] == [True, True, False]
    assert [c["repair_count"] for c in construction] == [0, 1, 1]
    assert all(c["first_feedback_step"] < c["finish_step"] for c in construction)
    assert [f["initial_accepted"] for f in final_gate] == [True, False, False]
    assert all(f["repair_count"] == 0 and f["first_feedback_step"] > f["finish_step"] for f in final_gate)
    agg = outcome["aggregate"]
    assert agg["comparison_groups"] == 1
    assert agg["recommendation"]["state"] == "no-recommendation"
    assert {t["workload_hash"] for t in trials} == {MANIFEST["workload"]["hash"]}


def test_failures_are_retained_not_dropped(rig):
    trials = trials_of(rig, rig.run())
    failed = [t for t in trials if t["evaluator_success"] is False]
    assert len(failed) == 3 and all(t["failure_fingerprint"] for t in failed)
    for t in failed:
        schedule = MANIFEST["cadence_protocol"]["schedules"][t["pairing_id"]]
        assert history_of(rig, schedule, t["trial_index"]) is not None


def test_prewritten_output_without_feedback_is_not_a_cadence(rig):
    manifest = copy.deepcopy(MANIFEST)
    manifest["pairings"][0]["harness"]["adapter"] = "cadence-prewritten-control"
    outcome = rig.run(manifest)
    trials = trials_of(rig, outcome)
    assert all(t["evaluator_success"] is True for t in trials if t["pairing_id"] == "pair-construction")
    mine = [t for t in trials if t["pairing_id"] == "pair-construction"]
    errors = check_protocol(rig, mine, ran={"pair-construction": "prewritten-control"})
    assert "no-feedback-delivered:pair-construction" in errors


def test_missing_failure_history_is_flagged(rig):
    trials = trials_of(rig, rig.run())
    (rig.histories / "construction-2.json").unlink()
    assert "missing-history:pair-construction:2" in check_protocol(rig, trials)


def test_weakened_grader_is_refused_before_any_trial(rig):
    (rig.workload / "evaluator" / "expected.txt").write_text("anything\n", encoding="utf-8")
    with pytest.raises(runner.PreflightError) as caught:
        rig.run()
    assert caught.value.code == "evaluator-hash"
    assert not (rig.out / MANIFEST["run_id"]).exists()


def test_wrong_workload_binding_is_refused(rig):
    manifest = copy.deepcopy(MANIFEST)
    manifest["workload"]["hash"] = "sha256:" + "0" * 64
    with pytest.raises(runner.PreflightError) as caught:
        rig.run(manifest)
    assert caught.value.code == "workload-hash"


def test_differing_settings_make_the_pairs_incomparable(rig):
    manifest = copy.deepcopy(MANIFEST)
    manifest["pairings"][1]["environment_override"] = {"retry_policy": "retry-3"}
    agg = rig.run(manifest)["aggregate"]
    assert agg["comparison_groups"] == 2
    assert agg["recommendation"] == {
        "state": "no-recommendation",
        "reason": "incomparable comparison groups",
    }


def test_zero_accepted_artifacts_leave_spend_per_artifact_undefined(rig):
    manifest = copy.deepcopy(MANIFEST)
    manifest["pairings"][0]["harness"]["adapter"] = "cadence-never-accepted"
    outcome = rig.run(manifest)
    trials = [t for t in trials_of(rig, outcome) if t["pairing_id"] == "pair-construction"]
    assert [t["evaluator_success"] for t in trials] == [False, False, False]
    assert spend_per_accepted(trials) == {"unavailable": "no accepted artifact"}
    mine = next(p for p in outcome["aggregate"]["pairings"] if p["pairing_id"] == "pair-construction")
    assert mine["successes"] == 0 and "unavailable" in mine["cost_per_success_usd"]


def test_unknown_spend_is_unavailable_never_zero(rig):
    trials = trials_of(rig, rig.run())
    assert all(t["cost_usd"] == {"unavailable": "not-applicable-synthetic"} for t in trials)
    accepted = [t for t in trials if t["evaluator_success"] is True]
    assert accepted and spend_per_accepted(accepted) == {
        "unavailable": "spend unavailable for at least one trial"
    }


def test_timeout_is_a_rankable_failure_with_no_history(rig):
    rig.profile("cadence-timeout", "timeout", timeout_s=1)
    manifest = copy.deepcopy(MANIFEST)
    manifest["repeats"] = 1
    manifest["pairings"] = manifest["pairings"][:1]
    manifest["pairings"][0]["harness"]["adapter"] = "cadence-timeout"
    manifest["pairings"][0]["budgets"]["time_s"] = 1
    trials = trials_of(rig, rig.run(manifest))
    assert [t["outcome"] for t in trials] == ["timeout"]
    assert trials[0]["evaluator_success"] is False
    assert history_of(rig, "timeout", 0) is None


def test_rerunning_a_run_id_cannot_overwrite_receipts(rig):
    first = rig.run()
    before = {p.name: p.read_bytes() for p in Path(first["run_dir"]).iterdir()}
    with pytest.raises(runner.PreflightError) as caught:
        rig.run()
    assert caught.value.code == "output-collision"
    assert before == {p.name: p.read_bytes() for p in Path(first["run_dir"]).iterdir()}
