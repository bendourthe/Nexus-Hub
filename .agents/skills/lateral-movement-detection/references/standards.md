# Framework Standards Reference

Framework identifiers carried by this skill. Each section gives the framework, the framework's own short title (cited, not paraphrased), the rationale tying this lateral-movement-detection skill to the ID, and a deep link to the public source.

## ATT&CK T1021 - Remote Services

- Framework: MITRE ATT&CK (Enterprise matrix), Lateral Movement tactic.
- Short title: "Remote Services".
- Rationale: this skill detects abuse of remote-service protocols to move between hosts, the parent technique ATT&CK catalogs as T1021.
- Source: https://attack.mitre.org/techniques/T1021/

## ATT&CK T1021.001 - Remote Services: Remote Desktop Protocol

- Framework: MITRE ATT&CK, sub-technique of T1021.
- Short title: "Remote Desktop Protocol".
- Rationale: the RDP correlation logic (remote-interactive logon type plus port-3389 session) maps directly to the RDP sub-technique T1021.001.
- Source: https://attack.mitre.org/techniques/T1021/001/

## ATT&CK T1021.002 - Remote Services: SMB/Windows Admin Shares

- Framework: MITRE ATT&CK, sub-technique of T1021.
- Short title: "SMB/Windows Admin Shares".
- Rationale: the SMB and admin-share detection (network logon to ADMIN$/C$/IPC$ then service creation) maps to the SMB sub-technique T1021.002.
- Source: https://attack.mitre.org/techniques/T1021/002/

## ATT&CK T1550 - Use Alternate Authentication Material

- Framework: MITRE ATT&CK (Enterprise matrix), Defense Evasion and Lateral Movement tactics.
- Short title: "Use Alternate Authentication Material".
- Rationale: the pass-the-hash and pass-the-ticket detection keys on authentication using reused material rather than an interactive credential, which ATT&CK defines as T1550.
- Source: https://attack.mitre.org/techniques/T1550/

## D3FEND D3-NTA - Network Traffic Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Network Traffic Analysis".
- Rationale: inspecting SMB (445) and RDP (3389) session telemetry to confirm a movement edge is the defender action D3FEND defines as Network Traffic Analysis.
- Source: https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Analysis".
- Rationale: analyzing the service or process spawned on a destination host after a remote logon is the defender action D3FEND defines as Process Analysis.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: continuously correlating authentication telemetry across hosts for movement is a continuous-monitoring capability CSF assigns under DE.CM.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.AE - Anomalies and Events

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Anomalies and Events".
- Rationale: flagging anomalous fan-out and abnormal service-account logons against a baseline is the anomaly-detection capability CSF defines under DE.AE.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
