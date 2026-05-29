# Framework Standards Reference

Framework mappings for the `identity-threat-detection` skill. Each section gives the framework identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source.

## ATT&CK T1078 - Valid Accounts

- Framework: MITRE ATT&CK (Enterprise matrix), Defense Evasion, Persistence, Privilege Escalation, and Initial Access tactics.
- Short title: "Valid Accounts".
- Rationale: impossible travel, session theft, and post-spray success detections all surface abuse of legitimate credentials, which is the defensive view of T1078 valid-accounts.
- Source: https://attack.mitre.org/techniques/T1078/

## ATT&CK T1556 - Modify Authentication Process

- Framework: MITRE ATT&CK (Enterprise matrix), Credential Access, Defense Evasion, and Persistence tactics.
- Short title: "Modify Authentication Process".
- Rationale: the authentication-tampering step hunts new MFA methods, conditional-access and federation changes, and added app credentials, which are the artifacts of T1556.
- Source: https://attack.mitre.org/techniques/T1556/

## ATT&CK T1110 - Brute Force

- Framework: MITRE ATT&CK (Enterprise matrix), Credential Access tactic.
- Short title: "Brute Force".
- Rationale: the password-spray and brute-force detections fire on the failure-pattern signatures that T1110 (including password spraying and credential stuffing) leaves in sign-in logs.
- Source: https://attack.mitre.org/techniques/T1110/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Analysis".
- Rationale: analyzing the authentication-process behavior of each identity (sign-in events, session use, auth-config changes) to flag anomalies is the process-analysis countermeasure D3FEND defines under D3-PA.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## NIST CSF PR.AC - Identity Management, Authentication and Access Control

- Framework: NIST Cybersecurity Framework, Protect function.
- Short title: "Identity Management, Authentication and Access Control".
- Rationale: detecting takeover and authentication tampering directly protects the identity, authentication, and access-control posture covered by PR.AC.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: continuously querying sign-in and audit logs for attack signatures is the continuous-monitoring detection practice under DE.CM.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.AE - Anomalies and Events

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Anomalies and Events".
- Rationale: each baseline-delta detection (impossible travel, MFA-fatigue burst, spray, token reuse) is an analyzed anomaly/event under DE.AE.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
