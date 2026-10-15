# Framework Standards Reference

Framework identifiers mapped to the cloud-security-posture-detection skill. Each entry gives the framework name and tactic or function, the framework's own short title (cited, not paraphrased), the rationale tying this skill to the identifier, and a deep link to the public source.

## ATT&CK T1078 - Valid Accounts

- Framework: MITRE ATT&CK (Enterprise matrix), Defense Evasion / Persistence / Privilege Escalation / Initial Access tactics.
- Short title: "Valid Accounts".
- Rationale: over-permissive IAM and exposed credentials let an adversary operate as a legitimate cloud principal, so detecting wildcard and admin grants reduces the attack surface for T1078.
- Source: https://attack.mitre.org/techniques/T1078/

## ATT&CK T1578 - Modify Cloud Compute Infrastructure

- Framework: MITRE ATT&CK (Enterprise matrix), Defense Evasion tactic.
- Short title: "Modify Cloud Compute Infrastructure".
- Rationale: posture drift such as newly opened management ports or weakened controls is the configuration weakness that enables and conceals adversary modification of cloud compute under T1578.
- Source: https://attack.mitre.org/techniques/T1578/

## ATT&CK T1530 - Data from Cloud Storage

- Framework: MITRE ATT&CK (Enterprise matrix), Collection tactic.
- Short title: "Data from Cloud Storage".
- Rationale: detecting publicly readable buckets and containers directly prevents the anonymous storage access that T1530 describes.
- Source: https://attack.mitre.org/techniques/T1530/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic (Platform Monitoring).
- Short title: "Process Analysis".
- Rationale: the skill performs systematic read-only analysis of cloud resource configuration and identity behavior, the defensive analysis activity D3FEND catalogs under D3-PA.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## NIST CSF ID.RA - Risk Assessment

- Framework: NIST Cybersecurity Framework, Identify function.
- Short title: "Risk Assessment".
- Rationale: ranking misconfigurations by exposure and blast radius is a risk-assessment activity, CSF's ID.RA category.
- Source: https://www.nist.gov/cyberframework

## NIST CSF PR.AC - Identity Management and Access Control

- Framework: NIST Cybersecurity Framework, Protect function.
- Short title: "Identity Management, Authentication and Access Control".
- Rationale: detecting over-permissive IAM and public access aligns to CSF's access-control category, which this skill helps enforce by surfacing violations.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: continuous posture and drift detection is a continuous-monitoring practice, CSF's DE.CM category.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
