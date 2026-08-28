"""Ownership and safety-language tests for local security-audit scanner recipes."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SECURITY_REVIEW = (
    _ROOT / "catalog" / "skills" / "code-review" / "security-review" / "SKILL.md"
)
_RECIPES = (
    _ROOT
    / "catalog"
    / "skills"
    / "code-review"
    / "security-review"
    / "references"
    / "local-scanner-recipes.md"
)
_DEPENDENCY = (
    _ROOT / "catalog" / "skills" / "security" / "dependency-security-audit" / "SKILL.md"
)
_REACHABILITY = (
    _ROOT / "catalog" / "skills" / "security" / "cve-reachability-analyzer" / "SKILL.md"
)
_CLOUD = (
    _ROOT
    / "catalog"
    / "skills"
    / "security-operations"
    / "cloud-security-posture-detection"
    / "SKILL.md"
)
_PRECOMMIT = (
    _ROOT / "catalog" / "skills" / "security" / "pre-commit-checklist" / "SKILL.md"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing {path}"
    return path.read_text(encoding="utf-8")


def test_each_named_scanner_has_one_primary_owner() -> None:
    recipes = _read(_RECIPES)
    dependency = _read(_DEPENDENCY)
    cloud = _read(_CLOUD)

    assert "Semgrep owns local static analysis" in recipes
    assert "gitleaks owns secrets scanning" in recipes
    assert "Semgrep owns" not in dependency
    assert "gitleaks owns" not in dependency
    assert "Semgrep owns" not in cloud
    assert "gitleaks owns" not in cloud

    assert "This skill owns dependency scanners" in dependency
    assert "OSV-Scanner" in dependency
    assert "npm audit" in dependency
    assert "pip-audit" in dependency
    assert "`trivy-vuln`" in dependency

    assert "This skill owns Trivy config and Checkov" in cloud
    assert "trivy-vuln" not in cloud
    assert "OSV-Scanner" not in cloud


def test_owners_forbid_auto_install_and_hosted_fallback() -> None:
    bodies = (
        _read(_RECIPES),
        _read(_DEPENDENCY),
        _read(_CLOUD),
        _read(_PRECOMMIT),
    )
    for body in bodies:
        assert "Never auto-install" in body or "never auto-install" in body
        assert "hosted" in body.lower()


def test_gitleaks_output_is_redacted() -> None:
    recipes = _read(_RECIPES)
    skill = _read(_SECURITY_REVIEW)

    assert "must not include matched secret values" in recipes
    assert "[REDACTED]" in recipes
    assert "local-scanner-recipes.md" in skill
    assert (
        "Redact gitleaks matches" in skill
        or "gitleaks output contains no matched secret values" in skill
    )


def test_cloud_posture_never_applies_changes() -> None:
    cloud = _read(_CLOUD)

    assert "never run `apply`" in cloud or "Never run `apply`" in cloud
    assert "mutate cloud resources" in cloud
    assert "`NOT_APPLICABLE`" in cloud


def test_reachability_accepts_scanner_receipt_without_restating_audit() -> None:
    reachability = _read(_REACHABILITY)
    dependency = _read(_DEPENDENCY)

    assert "scanner receipt id plus a finding id" in reachability
    assert "Preserve the original severity" in reachability
    assert "do not restate that skill's applicability matrix" in reachability
    assert "cve-reachability-analyzer" in dependency
    assert "Select tools from observed manifests" not in reachability


def test_precommit_defers_full_gitleaks_ownership() -> None:
    precommit = _read(_PRECOMMIT)

    assert (
        "security-review` owns full repository" in precommit
        or "security-review` owns full-repository" in precommit
    )
    assert "Do not copy that recipe" in precommit or "do not copy the full" in precommit
    assert "do not auto-install" in precommit or "never auto-install" in precommit
    assert "Semgrep owns local static analysis" not in precommit
