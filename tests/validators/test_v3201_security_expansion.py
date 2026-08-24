"""v3.20.1 Phase 4: forty new security skills, two categories, dual-use gates."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / "catalog" / "skills"

PHASE4 = {
    "security-operations": [
        "ioc-enrichment-and-reputation-triage",
        "threat-actor-ttp-profiling",
        "threat-intel-feed-operations",
        "infrastructure-pivoting-and-attribution",
        "ransomware-leak-site-monitoring",
        "cert-transparency-and-typosquat-monitoring",
        "honeytoken-placement",
        "adversary-engagement-deception",
        "firmware-extraction-and-analysis",
        "uefi-secure-boot-integrity",
        "tpm-measured-boot-attestation",
        "purple-team-exercise-design",
    ],
    "ot-security": [
        "ics-protocol-anomaly-detection",
        "scada-historian-threat-detection",
        "ot-network-segmentation-and-zones",
        "ot-incident-response",
        "ot-nerc-cip-compliance",
    ],
    "security": [
        "api-object-level-authorization-flaws",
        "api-inventory-and-undocumented-endpoints",
        "api-rate-limit-and-abuse-detection",
        "api-schema-and-gateway-enforcement",
        "jwt-header-and-key-confusion-attacks",
        "encryption-at-rest-design",
        "tls-certificate-lifecycle",
        "key-management-and-hsm-integration",
        "digital-signatures-and-jwt-signing",
        "post-quantum-cryptography-migration",
        "cryptographic-control-audit",
        "zero-trust-architecture-design",
        "ztna-broker-deployment",
        "network-microsegmentation-design",
        "smart-contract-security-review",
        "bluetooth-and-wireless-assessment",
        "vulnerability-prioritization-with-ssvc",
        "slsa-provenance-and-sigstore-verification",
    ],
    "mobile-security": [
        "android-static-app-analysis",
        "android-dynamic-app-analysis",
        "ios-app-security-review",
        "mobile-tls-pinning-bypass-assessment",
        "mobile-malware-family-triage",
    ],
}

DUAL_USE = (
    "infrastructure-pivoting-and-attribution",
    "api-object-level-authorization-flaws",
    "api-inventory-and-undocumented-endpoints",
    "api-rate-limit-and-abuse-detection",
    "jwt-header-and-key-confusion-attacks",
    "android-dynamic-app-analysis",
    "mobile-tls-pinning-bypass-assessment",
    "firmware-extraction-and-analysis",
    "smart-contract-security-review",
    "bluetooth-and-wireless-assessment",
    "purple-team-exercise-design",
)


def test_phase4_skill_count_is_forty() -> None:
    assert sum(len(v) for v in PHASE4.values()) == 40


def test_phase4_skill_files_exist() -> None:
    missing = []
    for cat, names in PHASE4.items():
        for name in names:
            path = SKILLS / cat / name / "SKILL.md"
            if not path.is_file():
                missing.append(str(path))
    assert not missing, missing


def test_dual_use_skills_open_with_an_authorization_gate() -> None:
    for name in DUAL_USE:
        matches = list(SKILLS.rglob(f"{name}/SKILL.md"))
        assert matches, name
        text = matches[0].read_text(encoding="utf-8")
        assert "Authorization precondition" in text, name


def test_phase4_skills_ship_trigger_evals() -> None:
    missing = []
    for cat, names in PHASE4.items():
        for name in names:
            path = SKILLS / cat / name / "evals" / "trigger-cases.json"
            if not path.is_file():
                missing.append(name)
    assert not missing, missing
