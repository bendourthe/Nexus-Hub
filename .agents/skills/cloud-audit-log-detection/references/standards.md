# Framework Standards Reference

Framework identifiers mapped to the cloud-audit-log-detection skill. Each entry gives the framework name and tactic or function, the framework's own short title (cited, not paraphrased), the rationale tying this skill to the identifier, and a deep link to the public source.

## ATT&CK T1078 - Valid Accounts

- Framework: MITRE ATT&CK (Enterprise matrix), Defense Evasion / Persistence / Privilege Escalation / Initial Access tactics.
- Short title: "Valid Accounts".
- Rationale: detecting privilege escalation and unexpected actions by a legitimate cloud principal in audit logs is the core detection for adversary use of valid accounts under T1078.
- Source: https://attack.mitre.org/techniques/T1078/

## ATT&CK T1098 - Account Manipulation

- Framework: MITRE ATT&CK (Enterprise matrix), Persistence tactic.
- Short title: "Account Manipulation".
- Rationale: the skill's IAM-persistence detections (new users, access keys, trust-relationship changes) target exactly the account-manipulation behavior T1098 describes.
- Source: https://attack.mitre.org/techniques/T1098/

## ATT&CK T1530 - Data from Cloud Storage

- Framework: MITRE ATT&CK (Enterprise matrix), Collection tactic.
- Short title: "Data from Cloud Storage".
- Rationale: detecting unexpected data-store reads and exports in audit logs catches the collection activity T1530 covers.
- Source: https://attack.mitre.org/techniques/T1530/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic (Platform Monitoring).
- Short title: "Process Analysis".
- Rationale: the skill analyzes control-plane event sequences to find malicious behavior, the defensive analysis activity D3FEND catalogs under D3-PA.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: standing detections over collected audit logs are continuous monitoring, CSF's DE.CM category.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.AE - Anomalies and Events

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Anomalies and Events".
- Rationale: correlating and triaging suspicious event sequences is the anomaly-and-event analysis CSF's DE.AE category defines.
- Source: https://www.nist.gov/cyberframework

## NIST CSF RS.AN - Analysis

- Framework: NIST Cybersecurity Framework, Respond function.
- Short title: "Analysis".
- Rationale: producing triage verdicts and evidence event IDs for likely-malicious activity feeds the response analysis CSF's RS.AN category describes.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
