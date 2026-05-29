# Framework Standards Reference

Framework identifiers carried by this skill. Each section gives the framework, the framework's own short title (cited, not paraphrased), the rationale tying this detection-engineering skill to the ID, and a deep link to the public source.

## ATT&CK T1059 - Command and Scripting Interpreter

- Framework: MITRE ATT&CK (Enterprise matrix), Execution tactic.
- Short title: "Command and Scripting Interpreter".
- Rationale: the worked detection in this skill watches for scripting-interpreter execution, the canonical behavior ATT&CK catalogs as T1059, so authored rules map here directly.
- Source: https://attack.mitre.org/techniques/T1059/

## ATT&CK T1071 - Application Layer Protocol

- Framework: MITRE ATT&CK (Enterprise matrix), Command and Control tactic.
- Short title: "Application Layer Protocol".
- Rationale: correlation rules built with this skill frequently key on command-and-control traffic over application protocols, which ATT&CK defines as T1071.
- Source: https://attack.mitre.org/techniques/T1071/

## D3FEND D3-NTA - Network Traffic Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Network Traffic Analysis".
- Rationale: detections in this skill that inspect proxy, firewall, and flow telemetry for malicious patterns are the defender action D3FEND defines as Network Traffic Analysis.
- Source: https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Analysis".
- Rationale: process-creation rules authored here (parent/child lineage, command-line inspection) are exactly the defender action D3FEND defines as Process Analysis.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: standing SIEM detection content is a continuous-monitoring capability, the governance-level home CSF assigns under DE.CM.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.AE - Anomalies and Events

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Anomalies and Events".
- Rationale: correlation logic that ties multiple events into a single alert is the detection-and-analysis-of-anomalies capability CSF defines under DE.AE.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.DP - Detection Processes

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Detection Processes".
- Rationale: the seeded-test and false-positive tuning loop is a maintained, tested detection process, which CSF tracks under DE.DP.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
