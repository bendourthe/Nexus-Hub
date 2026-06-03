"""Detection-class taxonomy and security-framework identifier mapping.

The 16 vulnerability classes and their primary MITRE ATT&CK / ATLAS / D3FEND
and NIST CSF identifiers mirror
``catalog/skills/security/skill-security-scan/references/detection-classes.md``
(the framework-mapping companion for the ``skill-security-scan`` skill). The
identifiers here are the *primary* mapping per class; an individual finding can
be tagged more specifically by the semantic-adjudication skill.

The taxonomy is a re-authored synthesis of public skill-security knowledge; no
external project's pattern source, text, or evaluation metric is reproduced
(Reverse-Engineering Attribution Rule).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectionClass:
    number: int
    name: str
    framework_ids: tuple[str, ...]


# Class number -> (name, primary framework IDs). Class 14 (YARA signatures) is
# defined here for completeness but is implemented by the optional Phase 7
# module, not the core static engine.
DETECTION_CLASSES: dict[int, DetectionClass] = {
    1: DetectionClass(1, "Prompt Injection", ("ATTACK:T1059", "ATLAS:AML.T0051", "NIST-CSF:DE.AE")),
    2: DetectionClass(2, "Data Exfiltration", ("ATTACK:T1041", "ATTACK:T1567", "ATLAS:AML.T0024", "NIST-CSF:PR.DS")),
    3: DetectionClass(3, "Privilege Escalation", ("ATTACK:T1548", "ATTACK:T1552", "NIST-CSF:PR.AA")),
    4: DetectionClass(4, "Supply Chain", ("ATTACK:T1195", "ATTACK:T1195.001", "NIST-CSF:ID.SC")),
    5: DetectionClass(5, "Excessive Agency", ("ATTACK:T1548", "ATLAS:AML.T0053", "NIST-CSF:PR.AA")),
    6: DetectionClass(6, "Output Handling", ("ATTACK:T1059", "NIST-CSF:PR.PS")),
    7: DetectionClass(7, "System Prompt Leakage", ("ATLAS:AML.T0051", "NIST-CSF:DE.AE")),
    8: DetectionClass(8, "Memory Poisoning", ("ATTACK:T1565", "ATLAS:AML.T0051", "NIST-CSF:PR.DS")),
    9: DetectionClass(9, "Tool Misuse", ("ATTACK:T1059", "ATLAS:AML.T0053", "NIST-CSF:DE.CM")),
    10: DetectionClass(10, "Rogue Agent", ("ATTACK:T1546", "NIST-CSF:DE.CM")),
    11: DetectionClass(11, "Trigger Abuse", ("ATTACK:T1036", "ATLAS:AML.T0051", "NIST-CSF:DE.AE")),
    12: DetectionClass(12, "Behavioral AST", ("ATTACK:T1059", "ATTACK:T1620", "D3FEND:D3-DA", "NIST-CSF:DE.CM")),
    13: DetectionClass(13, "Taint Tracking", ("ATTACK:T1059", "ATTACK:T1041", "D3FEND:D3-DA", "NIST-CSF:DE.CM")),
    14: DetectionClass(14, "YARA Signatures", ("ATTACK:T1505.003", "ATTACK:T1496", "D3FEND:D3-FA", "NIST-CSF:DE.CM")),
    15: DetectionClass(15, "MCP Least Privilege", ("ATTACK:T1548", "ATLAS:AML.T0053", "NIST-CSF:PR.AA")),
    16: DetectionClass(16, "MCP Tool Poisoning", ("ATTACK:T1195", "ATLAS:AML.T0051", "D3FEND:D3-NTA", "NIST-CSF:DE.AE")),
}


def framework_ids_for(detection_class: int) -> tuple[str, ...]:
    cls = DETECTION_CLASSES.get(detection_class)
    return cls.framework_ids if cls else ()


def class_name(detection_class: int) -> str:
    cls = DETECTION_CLASSES.get(detection_class)
    return cls.name if cls else f"Class {detection_class}"
