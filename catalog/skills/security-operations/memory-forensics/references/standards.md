# Framework Standards Reference

Framework mappings for the `memory-forensics` skill. Each section gives the framework identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source.

## ATT&CK T1003.001 - OS Credential Dumping: LSASS Memory

- Framework: MITRE ATT&CK (Enterprise matrix), Credential Access tactic, sub-technique of T1003.
- Short title: "LSASS Memory".
- Rationale: the credential-artifact step hunts for LSASS access residue and carved secret material in the memory image, which is the forensic footprint of T1003.001.
- Source: https://attack.mitre.org/techniques/T1003/001/

## ATT&CK T1055 - Process Injection

- Framework: MITRE ATT&CK (Enterprise matrix), Defense Evasion and Privilege Escalation tactics.
- Short title: "Process Injection".
- Rationale: the injected-code hunt scans process memory for executable regions not backed by an on-disk image, which is the memory signature of T1055 process injection.
- Source: https://attack.mitre.org/techniques/T1055/

## ATT&CK T1620 - Reflective Code Loading

- Framework: MITRE ATT&CK (Enterprise matrix), Defense Evasion tactic.
- Short title: "Reflective Code Loading".
- Rationale: the skill carves in-memory PE images and unbacked modules with no module-list entry, which is exactly the residue T1620 reflective loading leaves behind.
- Source: https://attack.mitre.org/techniques/T1620/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Analysis".
- Rationale: enumerating and diffing the process tree from a memory image is the process-analysis countermeasure D3FEND defines under D3-PA.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## D3FEND D3-PSA - Process Spawn Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Spawn Analysis".
- Rationale: flagging suspicious parent/child relationships (for example a document viewer spawning a shell) reconstructed from memory is the process-spawn-analysis countermeasure D3-PSA.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessSpawnAnalysis/

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: memory triage is a monitoring-and-detection practice that surfaces malicious activity not visible in routine logs, mapping to the Detect / Continuous Monitoring category.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.AE - Anomalies and Events

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Anomalies and Events".
- Rationale: each hidden process, injected region, or anomalous connection the skill confirms is an analyzed anomaly/event under DE.AE.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
