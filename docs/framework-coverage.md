<!-- GENERATED FILE. Do not edit by hand.
     Regenerate with: python scripts/build_framework_coverage.py --out docs/framework-coverage.md --navigator-layer docs/attack-navigator-layer.json
-->

# Security Framework Coverage Matrix

GENERATED from optional framework-mapping frontmatter. Never hand-edit this file; run `python scripts/build_framework_coverage.py --out docs/framework-coverage.md --navigator-layer docs/attack-navigator-layer.json` instead.

Scanned `catalog/skills`. Each row links a public framework control ID to the Nexus-Hub skills tagged with it. See `catalog/skills/security/security-framework-mapping/SKILL.md` for the tagging convention.

## Summary

| Framework | Distinct controls covered | Skill tags |
|---|---|---|
| MITRE ATT&CK | 64 | 103 |
| MITRE ATLAS | 4 | 6 |
| MITRE F3 | 1 | 1 |
| MITRE D3FEND | 20 | 53 |
| NIST CSF | 19 | 127 |
| NIST AI RMF | 2 | 4 |

## MITRE ATT&CK

| Control ID | Skills |
|---|---|
| `T0807` | ics-protocol-anomaly-detection |
| `T0813` | ot-incident-response |
| `T0829` | ot-incident-response |
| `T0842` | bluetooth-and-wireless-assessment |
| `T0855` | ics-protocol-anomaly-detection |
| `T0878` | scada-historian-threat-detection |
| `T0883` | ot-network-segmentation-and-zones |
| `T0891` | scada-historian-threat-detection |
| `T1003` | hunting-credential-dumping, purple-team-exercise-design |
| `T1003.001` | hunting-credential-dumping, memory-forensics, security-framework-mapping |
| `T1003.002` | hunting-credential-dumping |
| `T1003.003` | hunting-credential-dumping |
| `T1011` | bluetooth-and-wireless-assessment |
| `T1021` | lateral-movement-detection, threat-actor-ttp-profiling |
| `T1021.001` | lateral-movement-detection |
| `T1021.002` | lateral-movement-detection |
| `T1027` | malware-triage-analysis |
| `T1041` | ioc-enrichment-and-reputation-triage, skill-security-scan |
| `T1053` | persistence-mechanism-hunting |
| `T1055` | endpoint-edr-detection, malware-triage-analysis, memory-forensics |
| `T1059` | agentic-endpoint-hardening, disk-artifact-forensics, endpoint-edr-detection, log-threat-hunting, malware-triage-analysis, purple-team-exercise-design, siem-detection-engineering, skill-security-scan, threat-actor-ttp-profiling |
| `T1070` | disk-artifact-forensics |
| `T1071` | agent-execution-isolation, ioc-enrichment-and-reputation-triage, log-threat-hunting, security-framework-mapping, siem-detection-engineering, threat-intel-feed-operations |
| `T1078` | api-object-level-authorization-flaws, cloud-audit-log-detection, cloud-security-posture-detection, honeytoken-placement, identity-threat-detection, jwt-header-and-key-confusion-attacks |
| `T1080` | agent-execution-isolation |
| `T1090` | agent-execution-isolation |
| `T1098` | cloud-audit-log-detection |
| `T1110` | api-rate-limit-and-abuse-detection, identity-threat-detection |
| `T1190` | api-inventory-and-undocumented-endpoints, api-object-level-authorization-flaws, api-schema-and-gateway-enforcement |
| `T1195` | skill-security-scan |
| `T1200` | adversary-engagement-deception |
| `T1218` | endpoint-edr-detection |
| `T1417` | mobile-malware-family-triage |
| `T1476` | mobile-malware-family-triage |
| `T1486` | ransomware-incident-response, ransomware-leak-site-monitoring |
| `T1489` | ransomware-incident-response |
| `T1490` | ransomware-incident-response |
| `T1499` | api-rate-limit-and-abuse-detection |
| `T1526` | api-inventory-and-undocumented-endpoints |
| `T1530` | cloud-audit-log-detection, cloud-security-posture-detection |
| `T1542.001` | firmware-extraction-and-analysis, uefi-secure-boot-integrity |
| `T1543` | persistence-mechanism-hunting |
| `T1546` | agentic-endpoint-hardening, persistence-mechanism-hunting |
| `T1547` | disk-artifact-forensics, persistence-mechanism-hunting |
| `T1548` | skill-security-scan |
| `T1550` | lateral-movement-detection |
| `T1550.001` | jwt-header-and-key-confusion-attacks |
| `T1552` | agent-execution-isolation, honeytoken-placement, skill-security-scan |
| `T1553.006` | uefi-secure-boot-integrity |
| `T1556` | identity-threat-detection |
| `T1566` | cert-transparency-and-typosquat-monitoring, phishing-analysis-and-defense |
| `T1566.001` | phishing-analysis-and-defense |
| `T1566.002` | phishing-analysis-and-defense |
| `T1573` | infrastructure-pivoting-and-attribution |
| `T1578` | cloud-security-posture-detection |
| `T1583` | threat-actor-ttp-profiling |
| `T1583.001` | cert-transparency-and-typosquat-monitoring, infrastructure-pivoting-and-attribution |
| `T1584` | adversary-engagement-deception |
| `T1601` | firmware-extraction-and-analysis |
| `T1610` | container-runtime-detection |
| `T1611` | agent-execution-isolation, agentic-endpoint-hardening, container-runtime-detection |
| `T1613` | container-runtime-detection |
| `T1620` | memory-forensics |
| `T1657` | ransomware-leak-site-monitoring |

## MITRE ATLAS

| Control ID | Skills |
|---|---|
| `AML.T0020` | ai-attack-patterns |
| `AML.T0047` | security-framework-mapping |
| `AML.T0051` | ai-attack-patterns, prompt-injection-defense, skill-security-scan |
| `AML.T0054` | ai-attack-patterns |

## MITRE F3

| Control ID | Skills |
|---|---|
| `F1005` | ransomware-leak-site-monitoring |

## MITRE D3FEND

| Control ID | Skills |
|---|---|
| `D3-CH` | cryptographic-control-audit, digital-signatures-and-jwt-signing |
| `D3-CR` | agentic-endpoint-hardening |
| `D3-DE` | honeytoken-placement |
| `D3-DNRA` | cert-transparency-and-typosquat-monitoring |
| `D3-FA` | agent-execution-isolation, agentic-endpoint-hardening, disk-artifact-forensics, malware-triage-analysis, phishing-analysis-and-defense, ransomware-incident-response, skill-security-scan |
| `D3-FE` | encryption-at-rest-design |
| `D3-FH` | agentic-endpoint-hardening, malware-triage-analysis, ransomware-incident-response |
| `D3-IAA` | ioc-enrichment-and-reputation-triage |
| `D3-ITA` | api-schema-and-gateway-enforcement |
| `D3-KBPI` | key-management-and-hsm-integration |
| `D3-NI` | agent-execution-isolation, network-microsegmentation-design, ot-network-segmentation-and-zones |
| `D3-NTA` | agent-execution-isolation, ioc-enrichment-and-reputation-triage, lateral-movement-detection, log-threat-hunting, security-framework-mapping, siem-detection-engineering, skill-security-scan, zero-trust-architecture-design |
| `D3-PA` | agent-execution-isolation, agentic-endpoint-hardening, cloud-audit-log-detection, cloud-security-posture-detection, container-runtime-detection, endpoint-edr-detection, hunting-credential-dumping, identity-threat-detection, lateral-movement-detection, log-threat-hunting, memory-forensics, persistence-mechanism-hunting, siem-detection-engineering |
| `D3-PH` | agent-execution-isolation |
| `D3-PSA` | endpoint-edr-detection, hunting-credential-dumping, memory-forensics |
| `D3-PT` | agentic-endpoint-hardening |
| `D3-SCI` | slsa-provenance-and-sigstore-verification |
| `D3-SFA` | disk-artifact-forensics, persistence-mechanism-hunting |
| `D3-TBPA` | tpm-measured-boot-attestation |
| `D3-TLSC` | tls-certificate-lifecycle |

## NIST CSF

| Control ID | Skills |
|---|---|
| `DE.AE` | cloud-audit-log-detection, container-runtime-detection, disk-artifact-forensics, endpoint-edr-detection, honeytoken-placement, hunting-credential-dumping, ics-protocol-anomaly-detection, identity-threat-detection, infrastructure-pivoting-and-attribution, lateral-movement-detection, log-threat-hunting, memory-forensics, mobile-malware-family-triage, persistence-mechanism-hunting, purple-team-exercise-design, siem-detection-engineering, threat-actor-ttp-profiling |
| `DE.CM` | adversary-engagement-deception, agent-execution-isolation, agentic-endpoint-hardening, android-dynamic-app-analysis, api-inventory-and-undocumented-endpoints, api-object-level-authorization-flaws, api-rate-limit-and-abuse-detection, api-schema-and-gateway-enforcement, bluetooth-and-wireless-assessment, cert-transparency-and-typosquat-monitoring, cloud-audit-log-detection, cloud-security-posture-detection, container-runtime-detection, endpoint-edr-detection, honeytoken-placement, hunting-credential-dumping, ics-protocol-anomaly-detection, identity-threat-detection, ioc-enrichment-and-reputation-triage, jwt-header-and-key-confusion-attacks, lateral-movement-detection, log-threat-hunting, malware-triage-analysis, memory-forensics, mobile-tls-pinning-bypass-assessment, network-microsegmentation-design, persistence-mechanism-hunting, phishing-analysis-and-defense, ransomware-incident-response, ransomware-leak-site-monitoring, scada-historian-threat-detection, security-framework-mapping, siem-detection-engineering, skill-security-scan, threat-intel-feed-operations, tls-certificate-lifecycle, uefi-secure-boot-integrity |
| `DE.DP` | siem-detection-engineering |
| `ID.AM` | api-inventory-and-undocumented-endpoints, ot-nerc-cip-compliance |
| `ID.IM` | ot-nerc-cip-compliance, threat-intel-feed-operations |
| `ID.RA` | adversary-engagement-deception, android-static-app-analysis, cloud-security-posture-detection, cryptographic-control-audit, firmware-extraction-and-analysis, infrastructure-pivoting-and-attribution, ioc-enrichment-and-reputation-triage, ios-app-security-review, post-quantum-cryptography-migration, security-framework-mapping, skill-security-scan, smart-contract-security-review, threat-actor-ttp-profiling, vulnerability-prioritization-with-ssvc |
| `ID.SC` | slsa-provenance-and-sigstore-verification |
| `PR.AA` | api-object-level-authorization-flaws, bluetooth-and-wireless-assessment, digital-signatures-and-jwt-signing, encryption-at-rest-design, jwt-header-and-key-confusion-attacks, key-management-and-hsm-integration, tpm-measured-boot-attestation, zero-trust-architecture-design, ztna-broker-deployment |
| `PR.AC` | agent-execution-isolation, cloud-security-posture-detection, identity-threat-detection, ot-network-segmentation-and-zones, smart-contract-security-review |
| `PR.AT` | cert-transparency-and-typosquat-monitoring, phishing-analysis-and-defense |
| `PR.DS` | agent-execution-isolation, android-dynamic-app-analysis, android-static-app-analysis, api-rate-limit-and-abuse-detection, api-schema-and-gateway-enforcement, cryptographic-control-audit, digital-signatures-and-jwt-signing, encryption-at-rest-design, firmware-extraction-and-analysis, ios-app-security-review, key-management-and-hsm-integration, mobile-tls-pinning-bypass-assessment, post-quantum-cryptography-migration, scada-historian-threat-detection, slsa-provenance-and-sigstore-verification, tls-certificate-lifecycle, tpm-measured-boot-attestation, uefi-secure-boot-integrity |
| `PR.IR` | network-microsegmentation-design, ot-network-segmentation-and-zones, zero-trust-architecture-design, ztna-broker-deployment |
| `PR.PS` | agentic-endpoint-hardening |
| `PR.PT` | agent-execution-isolation |
| `RC.RP` | ransomware-incident-response |
| `RS.AN` | cloud-audit-log-detection, disk-artifact-forensics, malware-triage-analysis, mobile-malware-family-triage, phishing-analysis-and-defense, purple-team-exercise-design |
| `RS.CO` | ot-incident-response, ransomware-leak-site-monitoring |
| `RS.MI` | ot-incident-response, ransomware-incident-response, vulnerability-prioritization-with-ssvc |
| `RS.RP` | ransomware-incident-response |

## NIST AI RMF

| Control ID | Skills |
|---|---|
| `MEASURE-2.6` | ai-attack-patterns, security-framework-mapping, skill-security-scan |
| `MEASURE-2.7` | ai-attack-patterns |
