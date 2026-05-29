# Framework Standards Reference

Framework identifiers carried by this skill. Each section gives the framework, the framework's own short title (cited, not paraphrased), the rationale tying this threat-hunting skill to the ID, and a deep link to the public source.

## ATT&CK T1059 - Command and Scripting Interpreter

- Framework: MITRE ATT&CK (Enterprise matrix), Execution tactic.
- Short title: "Command and Scripting Interpreter".
- Rationale: the worked hunt hypothesis searches host telemetry for scripting-interpreter abuse, the behavior ATT&CK catalogs as T1059.
- Source: https://attack.mitre.org/techniques/T1059/

## ATT&CK T1071 - Application Layer Protocol

- Framework: MITRE ATT&CK (Enterprise matrix), Command and Control tactic.
- Short title: "Application Layer Protocol".
- Rationale: network and proxy hunts in this skill pivot on command-and-control over application protocols, which ATT&CK defines as T1071.
- Source: https://attack.mitre.org/techniques/T1071/

## D3FEND D3-NTA - Network Traffic Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Network Traffic Analysis".
- Rationale: hunting through DNS, proxy, and flow logs for malicious patterns is the defender action D3FEND defines as Network Traffic Analysis.
- Source: https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Analysis".
- Rationale: pivoting on process lineage and command lines during a host hunt is exactly the defender action D3FEND defines as Process Analysis.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: proactive hunting across retained telemetry is a continuous-monitoring practice CSF assigns under DE.CM.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.AE - Anomalies and Events

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Anomalies and Events".
- Rationale: separating anomalous findings from the known-good baseline is the detection-and-analysis-of-anomalies capability CSF defines under DE.AE.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
