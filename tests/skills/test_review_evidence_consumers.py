"""Drive review-fanout-workflow.js with the real projector and a stubbed runtime.

The workflow runtime (Dynamic Workflows) is not available here, so these tests
execute the template's own merge, filter and render path under Node with
deterministic stand-ins for agent(), parallel(), phase() and log(). That is
stubbed-runtime proof, not a native workflow run.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "catalog/skills/code-review/security-review/scripts"
WORKFLOW = (
    ROOT
    / "catalog/skills/code-review/multi-agent-code-review/scripts/review-fanout-workflow.js"
)
ENVELOPES = ROOT / "tests/fixtures/security-audit/envelopes"
CASES = json.loads(
    (ROOT / "tests/fixtures/review-evidence/v4.15.3/consumer-cases.json").read_text()
)
HIDDEN = {"creationflags": 0x08000000} if sys.platform == "win32" else {}
NODE = shutil.which("node")
FOREIGN = "f" * 64

sys.path.insert(0, str(SCRIPTS))
import _audit_envelope as contract

_spec = importlib.util.spec_from_file_location(
    "project_review_findings", SCRIPTS / "project-review-findings.py"
)
projector = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(projector)

pytestmark = pytest.mark.skipif(
    NODE is None,
    reason="optional workflow runtime check needs node; the documented sequential review path applies",
)

HARNESS = """
const fs = require('fs');
const [, , scriptPath, inputPath] = process.argv;
const input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const src = fs.readFileSync(scriptPath, 'utf8').replace('export const meta', 'const meta');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const labels = [];
const agent = async (prompt, opts) => {
  const label = (opts && opts.label) || 'synthesize';
  labels.push(label);
  if (label.startsWith('review:')) return { findings: (input.reviews || {})[label.slice(7)] || [] };
  if (label.startsWith('verify:')) {
    return (input.verdicts || {})[label] || { verdict: 'refuted', rationale: 'stub', adjusted_confidence: 0 };
  }
  return 'REPORT:' + prompt.length;
};
const parallel = (fns) => Promise.all(fns.map((f) => f()));
const run = new AsyncFunction('agent', 'parallel', 'phase', 'log', 'args', src);
run(agent, parallel, () => {}, () => {}, input.args || {}).then((result) => {
  process.stdout.write(JSON.stringify({ result, labels }));
});
"""


def run_workflow(tmp_path, args, reviews=None, verdicts=None, source=None):
    harness = tmp_path / "harness.js"
    harness.write_text(HARNESS)
    script = WORKFLOW
    if source is not None:
        script = tmp_path / "mutated.js"
        script.write_text(source)
    payload = tmp_path / "input.json"
    payload.write_text(
        json.dumps({"args": args, "reviews": reviews or {}, "verdicts": verdicts or {}})
    )
    done = subprocess.run(
        [NODE, str(harness), str(script), str(payload)],
        capture_output=True,
        check=False,
        **HIDDEN,
    )
    assert done.returncode == 0, done.stderr.decode()[:400]
    return json.loads(done.stdout)


def seal(value):
    value["run_fingerprint"] = contract.digest(
        {k: v for k, v in value.items() if k != "run_fingerprint"}
    )
    return value


def envelope(name="degraded.expected.json"):
    return json.loads((ENVELOPES / name).read_text())


def context_for(env):
    target = env["target"]
    return {
        "revision": target["revision"],
        "root_fingerprint": target["root_fingerprint"],
        "scope_fingerprint": target["scope_fingerprint"],
        "input_run_fingerprint": env["input_run_fingerprint"],
    }


def projected(env, context=None):
    return projector.project(env, context_for(env) if context is None else context, secrets=[])


def titles(items):
    return [f["title"] for f in items]


def assert_preserved(proj, found):
    """Oracle: each projected finding sits in the right tier with source values."""
    tier = {"confirmed": "headline", "pending": "pending", "rejected": "appendix", "corrected": "appendix"}
    for source in proj["findings"]:
        matches = [f for f in found[tier[source["review_state"]]] if f["id"] == source["id"]]
        assert len(matches) == 1, source["id"]
        got = matches[0]
        assert got["review_state"] == source["review_state"]
        assert got["source_confidence"] == source["source_confidence"]
        assert got["confidence"] == source["confidence_band"]
        assert got["source_disposition"] == source["source_disposition"]
        assert got["release_blocking"] == source["release_blocking"]
        assert got["security"]["evidence_receipt_ids"] == source["security"]["evidence_receipt_ids"]
        if tier[source["review_state"]] == "appendix":
            assert got["suppressed_reason"] == "security-" + source["review_state"]


def test_legacy_control_matches_baseline(tmp_path):
    case = CASES["legacy"]
    out = run_workflow(tmp_path, {}, case["reviews"], case["verdicts"])["result"]
    expected = case["expected"]
    assert titles(out["findings"]["headline"]) == expected["headline"]
    assert titles(out["findings"]["appendix"]) == expected["appendix"]
    assert out["pending"] == expected["pending"]
    assert out["securityCoverage"] is expected["securityCoverage"]
    assert out["caveats"] == expected["caveats"]


def test_bound_projection_preserves_tiers_and_evidence(tmp_path):
    env = envelope()
    proj = projected(env)
    run = run_workflow(
        tmp_path, {"security_projection": proj, "expected_context": context_for(env)}
    )
    out = run["result"]
    assert_preserved(proj, out["findings"])
    assert out["pending"] == 1 and out["headline"] == 1 and out["appendix"] == 2
    assert out["securityCoverage"]["associated"] is True
    assert out["securityCoverage"]["complete_review"] is False
    assert out["securityCoverage"]["computed_health"] == env["computed_health"]
    assert not any(label.startswith("verify:") for label in run["labels"])


def test_reviewer_agreement_cannot_merge_or_upgrade_security_item(tmp_path):
    env = envelope()
    proj = projected(env)
    pending = next(f for f in proj["findings"] if f["review_state"] == "pending")
    persona = {
        "title": pending["title"],
        "severity": "P3",
        "file": pending["file"],
        "line": pending["line"],
        "confidence": CASES["agreement_control"]["persona_confidence"],
        "persona": "correctness",
    }
    out = run_workflow(
        tmp_path,
        {"security_projection": proj, "expected_context": context_for(env)},
        reviews={"correctness": [persona]},
    )["result"]
    assert_preserved(proj, out["findings"])
    kept = next(f for f in out["findings"]["pending"] if f["id"] == pending["id"])
    assert kept["confidence"] == pending["confidence_band"]
    assert kept["persona"] == "security"


@pytest.mark.parametrize("kind", ["foreign-context", "unbound", "missing-expected"])
def test_unbound_or_foreign_projection_is_refused(kind, tmp_path):
    env = envelope()
    proj = projected(env)
    expected = context_for(env)
    if kind == "foreign-context":
        expected = {**expected, "root_fingerprint": FOREIGN}
    elif kind == "unbound":
        proj = projector.project(env, None, secrets=[])
    else:
        expected = None
    args = {"security_projection": proj}
    if expected is not None:
        args["expected_context"] = expected
    out = run_workflow(tmp_path, args)["result"]
    assert out["findings"] == {"headline": [], "pending": [], "appendix": []}
    assert out["securityCoverage"]["associated"] is False
    assert out["securityCoverage"]["complete_review"] is False
    assert out["caveats"] and out["caveats"][0].startswith("security_projection_refused")


def test_forged_empty_complete_projection_cannot_claim_completeness(tmp_path):
    foreign = envelope("complete-local.expected.json")
    foreign["target"]["root_fingerprint"] = FOREIGN
    seal(foreign)
    forged = projected(foreign, context_for(foreign))
    assert forged["claims"]["complete_review"] is True
    out = run_workflow(
        tmp_path,
        {"security_projection": forged, "expected_context": context_for(envelope())},
    )["result"]
    assert out["securityCoverage"]["complete_review"] is False
    assert out["securityCoverage"]["associated"] is False


def test_duplicates_merge_when_identical_and_stay_separate_when_conflicting(tmp_path):
    env = envelope()
    proj = projected(env)
    base = proj["findings"][0]
    same = copy.deepcopy(base)
    other = copy.deepcopy(proj["findings"][1])
    other["fingerprint_key"] = base["fingerprint_key"]
    other["id"] = "sha256:" + FOREIGN
    proj["findings"] = [base, same, other]
    out = run_workflow(
        tmp_path, {"security_projection": proj, "expected_context": context_for(env)}
    )["result"]
    items = [f for tier in out["findings"].values() for f in tier]
    assert len(items) == 2
    merged = next(f for f in items if f["id"] == base["id"])
    assert merged["duplicate_count"] == 2
    assert merged["security"]["evidence_receipt_ids"] == base["security"]["evidence_receipt_ids"]
    assert out["caveats"] == ["conflicting_security_duplicate: " + base["fingerprint_key"]]


@pytest.mark.parametrize(
    "anchor, replacement",
    [
        ("    security: f.security,\n", ""),
        ("f.review_state === 'pending')\n", "f.review_state === 'none')\n"),
        ("    release_blocking: f.release_blocking,\n", ""),
    ],
    ids=["drop-evidence", "drop-pending", "drop-blocking"],
)
def test_consumer_mutation_is_detected(anchor, replacement, tmp_path):
    text = WORKFLOW.read_text().replace("\r\n", "\n")
    env = envelope()
    proj = projected(env)
    args = {"security_projection": proj, "expected_context": context_for(env)}
    assert_preserved(proj, run_workflow(tmp_path, args)["result"]["findings"])
    assert text.count(anchor) >= 1, anchor
    mutated = text.replace(anchor, replacement, 1)
    broken = run_workflow(tmp_path, args, source=mutated)["result"]["findings"]
    with pytest.raises((AssertionError, KeyError)):
        assert_preserved(proj, broken)
