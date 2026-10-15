# Framework Standards Reference

Framework mappings for the endpoint-edr-detection skill. Each entry gives the identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source.

## ATT&CK T1055 - Process Injection

- Framework: MITRE ATT&CK (Enterprise matrix), Defense Evasion and Privilege Escalation tactics.
- Short title: "Process Injection".
- Rationale: the skill detects remote-thread and memory-permission injection indicators, the technique ATT&CK catalogs as T1055.
- Source: https://attack.mitre.org/techniques/T1055/

## ATT&CK T1059 - Command and Scripting Interpreter

- Framework: MITRE ATT&CK (Enterprise matrix), Execution tactic.
- Short title: "Command and Scripting Interpreter".
- Rationale: detecting suspicious script-interpreter command lines targets the execution technique ATT&CK defines as T1059.
- Source: https://attack.mitre.org/techniques/T1059/

## ATT&CK T1218 - System Binary Proxy Execution

- Framework: MITRE ATT&CK (Enterprise matrix), Defense Evasion tactic.
- Short title: "System Binary Proxy Execution".
- Rationale: LOLBin-abuse detection targets the use of trusted signed binaries to proxy attacker execution, the technique ATT&CK defines as T1218.
- Source: https://attack.mitre.org/techniques/T1218/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Analysis".
- Rationale: analyzing process behavior, command lines, and injection indicators is the process-analysis defender action D3FEND defines as D3-PA.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## D3FEND D3-PSA - Process Spawn Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Spawn Analysis".
- Rationale: keying detections on parent-child process lineage is the process-spawn-analysis defender action D3FEND defines as D3-PSA.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessSpawnAnalysis/

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: behavioral EDR detection over host telemetry is a continuous-monitoring practice, the CSF Detect category DE.CM.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.AE - Anomalies and Events

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Anomalies and Events".
- Rationale: detecting deviations from modeled normal process behavior is anomaly analysis, the CSF Detect category DE.AE.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
