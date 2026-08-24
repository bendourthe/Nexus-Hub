<!-- GENERATED FILE. Do not edit by hand.
     Regenerate with: python scripts/build_framework_coverage.py --out docs/framework-coverage.md --navigator-layer docs/attack-navigator-layer.json
-->

# Security Framework Coverage Matrix

GENERATED from optional framework-mapping frontmatter. Never hand-edit this file; run `python scripts/build_framework_coverage.py --out docs/framework-coverage.md --navigator-layer docs/attack-navigator-layer.json` instead.

Scanned `catalog/skills`. Each row links a public framework control ID to the Nexus-Hub skills tagged with it. See `catalog/skills/security/security-framework-mapping/SKILL.md` for the tagging convention.

## Summary

| Framework | Distinct controls covered | Skill tags |
|---|---|---|
| MITRE ATT&CK | 38 | 59 |
| MITRE ATLAS | 4 | 6 |
| MITRE F3 | 0 | 0 |
| MITRE D3FEND | 6 | 34 |
| NIST CSF | 12 | 46 |
| NIST AI RMF | 2 | 4 |

## MITRE ATT&CK

| Control ID | Skills |
|---|---|
| `T1003` | hunting-credential-dumping |
| `T1003.001` | hunting-credential-dumping, memory-forensics, security-framework-mapping |
| `T1003.002` | hunting-credential-dumping |
| `T1003.003` | hunting-credential-dumping |
| `T1021` | lateral-movement-detection |
| `T1021.001` | lateral-movement-detection |
| `T1021.002` | lateral-movement-detection |
| `T1027` | malware-triage-analysis |
| `T1041` | skill-security-scan |
| `T1053` | persistence-mechanism-hunting |
| `T1055` | endpoint-edr-detection, malware-triage-analysis, memory-forensics |
| `T1059` | agentic-endpoint-hardening, disk-artifact-forensics, endpoint-edr-detection, log-threat-hunting, malware-triage-analysis, siem-detection-engineering, skill-security-scan |
| `T1070` | disk-artifact-forensics |
| `T1071` | agent-execution-isolation, log-threat-hunting, security-framework-mapping, siem-detection-engineering |
| `T1078` | cloud-audit-log-detection, cloud-security-posture-detection, identity-threat-detection |
| `T1098` | cloud-audit-log-detection |
| `T1110` | identity-threat-detection |
| `T1195` | skill-security-scan |
| `T1218` | endpoint-edr-detection |
| `T1486` | ransomware-incident-response |
| `T1489` | ransomware-incident-response |
| `T1490` | ransomware-incident-response |
| `T1530` | cloud-audit-log-detection, cloud-security-posture-detection |
| `T1543` | persistence-mechanism-hunting |
| `T1546` | agentic-endpoint-hardening, persistence-mechanism-hunting |
| `T1547` | disk-artifact-forensics, persistence-mechanism-hunting |
| `T1548` | skill-security-scan |
| `T1550` | lateral-movement-detection |
| `T1552` | agent-execution-isolation, skill-security-scan |
| `T1556` | identity-threat-detection |
| `T1566` | phishing-analysis-and-defense |
| `T1566.001` | phishing-analysis-and-defense |
| `T1566.002` | phishing-analysis-and-defense |
| `T1578` | cloud-security-posture-detection |
| `T1610` | container-runtime-detection |
| `T1611` | agent-execution-isolation, agentic-endpoint-hardening, container-runtime-detection |
| `T1613` | container-runtime-detection |
| `T1620` | memory-forensics |

## MITRE ATLAS

| Control ID | Skills |
|---|---|
| `AML.T0020` | ai-attack-patterns |
| `AML.T0047` | security-framework-mapping |
| `AML.T0051` | ai-attack-patterns, prompt-injection-defense, skill-security-scan |
| `AML.T0054` | ai-attack-patterns |

## MITRE F3

_No skills currently tagged with this framework._

## MITRE D3FEND

| Control ID | Skills |
|---|---|
| `D3-FA` | agent-execution-isolation, agentic-endpoint-hardening, disk-artifact-forensics, malware-triage-analysis, phishing-analysis-and-defense, ransomware-incident-response, skill-security-scan |
| `D3-FH` | agentic-endpoint-hardening, malware-triage-analysis, ransomware-incident-response |
| `D3-NTA` | agent-execution-isolation, lateral-movement-detection, log-threat-hunting, security-framework-mapping, siem-detection-engineering, skill-security-scan |
| `D3-PA` | agent-execution-isolation, agentic-endpoint-hardening, cloud-audit-log-detection, cloud-security-posture-detection, container-runtime-detection, endpoint-edr-detection, hunting-credential-dumping, identity-threat-detection, lateral-movement-detection, log-threat-hunting, memory-forensics, persistence-mechanism-hunting, siem-detection-engineering |
| `D3-PSA` | endpoint-edr-detection, hunting-credential-dumping, memory-forensics |
| `D3-SFA` | disk-artifact-forensics, persistence-mechanism-hunting |

## NIST CSF

| Control ID | Skills |
|---|---|
| `DE.AE` | cloud-audit-log-detection, container-runtime-detection, disk-artifact-forensics, endpoint-edr-detection, hunting-credential-dumping, identity-threat-detection, lateral-movement-detection, log-threat-hunting, memory-forensics, persistence-mechanism-hunting, siem-detection-engineering |
| `DE.CM` | agent-execution-isolation, agentic-endpoint-hardening, cloud-audit-log-detection, cloud-security-posture-detection, container-runtime-detection, endpoint-edr-detection, hunting-credential-dumping, identity-threat-detection, lateral-movement-detection, log-threat-hunting, malware-triage-analysis, memory-forensics, persistence-mechanism-hunting, phishing-analysis-and-defense, ransomware-incident-response, security-framework-mapping, siem-detection-engineering, skill-security-scan |
| `DE.DP` | siem-detection-engineering |
| `ID.RA` | cloud-security-posture-detection, security-framework-mapping, skill-security-scan |
| `PR.AC` | agent-execution-isolation, cloud-security-posture-detection, identity-threat-detection |
| `PR.AT` | phishing-analysis-and-defense |
| `PR.DS` | agent-execution-isolation |
| `PR.PS` | agentic-endpoint-hardening |
| `RC.RP` | ransomware-incident-response |
| `RS.AN` | cloud-audit-log-detection, disk-artifact-forensics, malware-triage-analysis, phishing-analysis-and-defense |
| `RS.MI` | ransomware-incident-response |
| `RS.RP` | ransomware-incident-response |

## NIST AI RMF

| Control ID | Skills |
|---|---|
| `MEASURE-2.6` | ai-attack-patterns, security-framework-mapping, skill-security-scan |
| `MEASURE-2.7` | ai-attack-patterns |
