"""Tests for v2.3.0 / Phase 4 / T012 harness_audit scoring.

Extended in v3.10.0 Phase 5 with the 1-100 agent-setup grade and the
cross-snapshot regression diff.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import harness_audit  # noqa: E402
from scripts.lib.integrations import INTEGRATION_REGISTRY  # noqa: E402
from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


@pytest.fixture
def fresh_target_with_install(
    tmp_path: Path, fake_home: Path
) -> tuple[Path, Path]:
    """Install `claude` against a fresh workspace and persist the manifest."""
    target = tmp_path / "workspace"
    target.mkdir()
    manifest = InstallManifest()
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=manifest,
        template_vars={"PROJECT_NAME": "test-project"},
    )
    integ = INTEGRATION_REGISTRY["claude"]
    result = integ.install(ctx)
    manifest.record_actions("claude", result.files)
    manifest_path = target / ".nexus-hub" / "install-manifest.json"
    manifest.save(manifest_path)
    return target, manifest_path


def test_audit_returns_empty_report_when_no_manifest(tmp_path: Path) -> None:
    report = harness_audit.audit(tmp_path / "empty")
    assert report.integrations == []
    assert report.aggregate() == 0.0


def test_audit_scores_clean_install_at_high_score(
    fresh_target_with_install: tuple[Path, Path]
) -> None:
    target, _ = fresh_target_with_install
    report = harness_audit.audit(target)
    assert report.integrations, "claude install should produce an audit entry"
    claude = report.integrations[0]
    # A clean install should score very high on every axis.
    assert claude.score >= 80.0, f"expected score >= 80, got {claude.score}"
    assert claude.axes["presence"] == pytest.approx(1.0)
    assert claude.axes["integrity"] == pytest.approx(1.0)
    assert claude.missing == 0
    assert claude.drifted == 0


def test_audit_penalizes_drifted_files(
    fresh_target_with_install: tuple[Path, Path]
) -> None:
    target, manifest_path = fresh_target_with_install
    manifest = InstallManifest.load(manifest_path)
    # Drift exactly one file.
    for entry in manifest.actions_for("claude"):
        sha = entry.get("sha256")
        path = Path(str(entry.get("path", "")))
        if sha is not None and path.is_file():
            path.write_text("DRIFTED", encoding="utf-8")
            break
    report = harness_audit.audit(target)
    claude = report.integrations[0]
    assert claude.drifted >= 1
    assert claude.axes["integrity"] < 1.0


def test_audit_penalizes_missing_files(
    fresh_target_with_install: tuple[Path, Path]
) -> None:
    target, manifest_path = fresh_target_with_install
    manifest = InstallManifest.load(manifest_path)
    for entry in manifest.actions_for("claude"):
        sha = entry.get("sha256")
        path = Path(str(entry.get("path", "")))
        if sha is not None and path.is_file():
            path.unlink()
            break
    report = harness_audit.audit(target)
    claude = report.integrations[0]
    assert claude.missing >= 1
    # Both presence and integrity drop when a file disappears.
    assert claude.axes["presence"] < 1.0
    assert claude.axes["integrity"] < 1.0


def test_audit_score_is_deterministic(
    fresh_target_with_install: tuple[Path, Path]
) -> None:
    target, _ = fresh_target_with_install
    first = harness_audit.audit(target).aggregate()
    second = harness_audit.audit(target).aggregate()
    assert first == second


def test_main_json_output_is_parseable(
    fresh_target_with_install: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    import json

    target, _ = fresh_target_with_install
    code = harness_audit.main(["--target", str(target), "--json"])
    captured = capsys.readouterr().out
    assert code == 0
    parsed = json.loads(captured)
    assert "aggregate_score" in parsed
    assert parsed["integrations"]


def test_main_min_score_threshold(
    fresh_target_with_install: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    target, _ = fresh_target_with_install
    # 200 is unreachable (max is 100) so this should always exit 1.
    code = harness_audit.main(
        ["--target", str(target), "--min-score", "200", "--json"]
    )
    assert code == 1


def test_audit_handles_unknown_integration_gracefully(tmp_path: Path) -> None:
    # Hand-build a manifest with a key that is NOT in the registry.
    target = tmp_path / "workspace"
    target.mkdir()
    manifest = InstallManifest()
    manifest._actions["does-not-exist"] = [
        {"path": "fake.txt", "action": "created", "sha256": None, "mtime": None}
    ]
    manifest_path = target / ".nexus-hub" / "install-manifest.json"
    manifest.save(manifest_path)
    report = harness_audit.audit(target, requested=["does-not-exist"])
    # _audit_one returns None for unknown keys; the audit just skips them.
    assert report.integrations == []


# --------------------------------------------------------------------------- #
# v3.10.0 Phase 5: agent-setup grade + regression diff
# --------------------------------------------------------------------------- #


_SKILL_FRONTMATTER = (
    "---\n"
    "name: {name}\n"
    "description: A test skill for the grade fixture.\n"
    'summary_l0: "A test skill summary."\n'
    'overview_l1: "A test skill overview."\n'
    "---\n\n# {name}\n\nbody\n"
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def synthetic_root(tmp_path: Path) -> Path:
    """A minimal, fully-consistent agent setup that grades 100/100.

    Individual tests mutate one signal to drive a single dimension down.
    """
    root = tmp_path / "repo"
    for rel in harness_audit.EXPECTED_INSTRUCTION_FILES:
        _write(root / rel, "instruction\n")
    _write(
        root / "catalog/skills/cat/skill-a/SKILL.md",
        _SKILL_FRONTMATTER.format(name="skill-a"),
    )
    _write(
        root / "catalog/skills/cat/skill-b/SKILL.md",
        _SKILL_FRONTMATTER.format(name="skill-b"),
    )
    for hook in harness_audit.SECURITY_HOOKS:
        _write(root / "catalog/hooks" / hook, "#!/usr/bin/env bash\n")
    settings = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write",
                    "hooks": [
                        {"type": "command", "command": "bash .claude/hooks/secret-scan.sh"},
                        {"type": "command", "command": "bash .claude/hooks/large-file-guard.sh"},
                    ],
                },
                {
                    "matcher": "Bash",
                    "hooks": [
                        {"type": "command", "command": "bash .claude/hooks/git-guardrails.sh"},
                    ],
                },
            ]
        }
    }
    _write(root / "catalog/hooks/settings.json", json.dumps(settings))
    _write(
        root / "data/skills.json",
        json.dumps(
            {
                "statistics": {"total_skills": 2, "categories": {"cat": 2}},
                "skills": [{"name": "skill-a"}, {"name": "skill-b"}],
            }
        ),
    )
    _write(
        root / "data/marketplace.json",
        json.dumps({"categories": [{"id": "cat", "skill_count": 2}]}),
    )
    _write(root / "data/bundles.json", json.dumps({"bundles": []}))
    _write(
        root / "data/SKILL_INDEX.md",
        "| Skill | Category | Summary | File |\n"
        "|---|---|---|---|\n"
        '| skill-a | Cat | "x" | catalog/skills/cat/skill-a/SKILL.md |\n'
        '| skill-b | Cat | "y" | catalog/skills/cat/skill-b/SKILL.md |\n',
    )
    return root


# ----- rubric shape ------------------------------------------------------- #


def test_rubric_weights_sum_to_one() -> None:
    assert abs(sum(harness_audit.GRADE_WEIGHTS.values()) - 1.0) < 1e-9


def test_grade_dimensions_match_rubric(synthetic_root: Path) -> None:
    setup = harness_audit.grade(synthetic_root)
    names = [d.name for d in setup.dimensions]
    assert set(names) == set(harness_audit.GRADE_WEIGHTS)
    assert len(names) == len(harness_audit.GRADE_WEIGHTS)  # no duplicates


# ----- grade math --------------------------------------------------------- #


def test_synthetic_root_grades_100(synthetic_root: Path) -> None:
    setup = harness_audit.grade(synthetic_root)
    assert setup.grade == 100
    assert all(d.applicable for d in setup.dimensions)
    assert all(d.sub_score == pytest.approx(1.0) for d in setup.dimensions)


def test_repo_grades_high() -> None:
    setup = harness_audit.grade(harness_audit.REPO_ROOT)
    assert setup.grade >= 90
    assert all(d.applicable for d in setup.dimensions)


def test_empty_root_grades_one(tmp_path: Path) -> None:
    setup = harness_audit.grade(tmp_path / "nothing-here")
    # Nothing is measurable, so the grade floors at 1 and no dimension counts.
    assert setup.grade == 1
    assert all(not d.applicable for d in setup.dimensions)


def test_grade_detects_registry_drift(synthetic_root: Path) -> None:
    sk = synthetic_root / "data/skills.json"
    data = json.loads(sk.read_text(encoding="utf-8"))
    data["statistics"]["total_skills"] = 3  # claim 3, only 2 on disk
    sk.write_text(json.dumps(data), encoding="utf-8")
    setup = harness_audit.grade(synthetic_root)
    rc = next(d for d in setup.dimensions if d.name == "registry_consistency")
    assert rc.applicable
    assert rc.sub_score < 1.0
    assert setup.grade < 100


def test_grade_half_credit_for_unregistered_security_hook(
    synthetic_root: Path,
) -> None:
    settings = synthetic_root / "catalog/hooks/settings.json"
    data = json.loads(settings.read_text(encoding="utf-8"))
    for chain in data["hooks"].values():
        for entry in chain:
            entry["hooks"] = [
                h for h in entry["hooks"] if "git-guardrails" not in h["command"]
            ]
    settings.write_text(json.dumps(data), encoding="utf-8")
    setup = harness_audit.grade(synthetic_root)
    sh = next(d for d in setup.dimensions if d.name == "security_hooks")
    # On disk but unregistered -> half credit: (1 + 1 + 0.5) / 3.
    assert sh.sub_score == pytest.approx((1 + 1 + 0.5) / 3)


def test_grade_detects_orphan_hook_reference(synthetic_root: Path) -> None:
    settings = synthetic_root / "catalog/hooks/settings.json"
    data = json.loads(settings.read_text(encoding="utf-8"))
    data["hooks"]["PreToolUse"][0]["hooks"].append(
        {"type": "command", "command": "bash .claude/hooks/does-not-exist.sh"}
    )
    settings.write_text(json.dumps(data), encoding="utf-8")
    setup = harness_audit.grade(synthetic_root)
    hr = next(d for d in setup.dimensions if d.name == "hook_registration")
    assert hr.applicable
    assert hr.sub_score < 1.0


# ----- determinism + snapshot --------------------------------------------- #


def test_grade_snapshot_payload_deterministic(synthetic_root: Path) -> None:
    first = harness_audit.grade(synthetic_root).snapshot_payload()
    second = harness_audit.grade(synthetic_root).snapshot_payload()
    assert first == second
    # The payload must not leak the absolute root (machine-specific).
    assert "root" not in first


def test_write_snapshot_is_byte_identical(
    synthetic_root: Path, tmp_path: Path
) -> None:
    snap_dir = tmp_path / "snaps"
    p1 = harness_audit.write_snapshot(
        harness_audit.grade(synthetic_root), synthetic_root, str(snap_dir)
    )
    first = p1.read_bytes()
    p2 = harness_audit.write_snapshot(
        harness_audit.grade(synthetic_root), synthetic_root, str(snap_dir)
    )
    assert p1 == p2
    assert p2.read_bytes() == first


# ----- diff classification ------------------------------------------------ #


def test_snapshot_then_diff_all_unchanged(
    synthetic_root: Path, tmp_path: Path
) -> None:
    snap_dir = tmp_path / "snaps"
    harness_audit.write_snapshot(
        harness_audit.grade(synthetic_root), synthetic_root, str(snap_dir)
    )
    stored = json.loads(
        (snap_dir / harness_audit.SNAPSHOT_FILENAME).read_text(encoding="utf-8")
    )
    diff = harness_audit.diff_against_snapshot(
        harness_audit.grade(synthetic_root), stored
    )
    assert diff.grade_delta == 0
    assert diff.regressed is False
    assert all(d.status == "unchanged" for d in diff.deltas)


def test_diff_classifies_regression() -> None:
    snapshot = {
        "schema": 1,
        "grade": 100,
        "dimensions": [
            {"name": n, "sub_score": 1.0} for n in harness_audit.GRADE_WEIGHTS
        ],
    }
    setup = harness_audit.grade(Path("/__does_not_exist__"))  # grades 1
    diff = harness_audit.diff_against_snapshot(setup, snapshot)
    assert diff.before_grade == 100
    assert diff.after_grade == 1
    assert diff.regressed is True
    assert all(d.status == "regressed" for d in diff.deltas)


def test_diff_classifies_improvement() -> None:
    snapshot = {
        "schema": 1,
        "grade": 50,
        "dimensions": [
            {"name": n, "sub_score": 0.0} for n in harness_audit.GRADE_WEIGHTS
        ],
    }
    setup = harness_audit.grade(harness_audit.REPO_ROOT)  # grades high
    diff = harness_audit.diff_against_snapshot(setup, snapshot)
    assert diff.regressed is False
    assert (diff.grade_delta or 0) > 0
    assert all(d.status == "improved" for d in diff.deltas)


# ----- CLI exit codes ----------------------------------------------------- #


def test_main_grade_is_advisory_exit_zero(
    synthetic_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = harness_audit.main(["grade", "--target", str(synthetic_root), "--json"])
    out = capsys.readouterr().out
    assert code == 0
    parsed = json.loads(out)
    assert parsed["grade"] == 100
    assert parsed["dimensions"]


def test_main_snapshot_flag_alias_writes(
    synthetic_root: Path, tmp_path: Path
) -> None:
    snap_dir = tmp_path / "snaps"
    code = harness_audit.main(
        ["--target", str(synthetic_root), "--snapshot", "--snapshot-dir", str(snap_dir)]
    )
    assert code == 0
    assert (snap_dir / harness_audit.SNAPSHOT_FILENAME).is_file()


def test_main_diff_fail_on_regression_gates(tmp_path: Path) -> None:
    target = tmp_path / "degraded"  # empty -> grades 1
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    snapshot = {
        "schema": 1,
        "grade": 100,
        "dimensions": [
            {"name": n, "sub_score": 1.0} for n in harness_audit.GRADE_WEIGHTS
        ],
    }
    (snap_dir / harness_audit.SNAPSHOT_FILENAME).write_text(
        json.dumps(snapshot), encoding="utf-8"
    )
    # Default diff is advisory: regressed but still exit 0.
    assert (
        harness_audit.main(
            ["diff", "--target", str(target), "--snapshot-dir", str(snap_dir)]
        )
        == 0
    )
    # Opt-in gate: exit non-zero on regression.
    assert (
        harness_audit.main(
            [
                "diff",
                "--target",
                str(target),
                "--snapshot-dir",
                str(snap_dir),
                "--fail-on-regression",
            ]
        )
        == 1
    )


def test_main_diff_no_snapshot_is_advisory(tmp_path: Path) -> None:
    target = tmp_path / "x"
    snap_dir = tmp_path / "empty-snaps"
    # No baseline yet: even with the gate flag, a first run never fails.
    assert (
        harness_audit.main(
            [
                "diff",
                "--target",
                str(target),
                "--snapshot-dir",
                str(snap_dir),
                "--fail-on-regression",
            ]
        )
        == 0
    )
