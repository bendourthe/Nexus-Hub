# Framework Standards Reference

Framework mappings for the `hunting-credential-dumping` skill. Each section gives the framework identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source.

## ATT&CK T1003 - OS Credential Dumping

- Framework: MITRE ATT&CK (Enterprise matrix), Credential Access tactic.
- Short title: "OS Credential Dumping".
- Rationale: the skill is a hunt for the parent technique itself - detecting attempts to obtain account credentials from the operating system across all of its sub-paths.
- Source: https://attack.mitre.org/techniques/T1003/

## ATT&CK T1003.001 - OS Credential Dumping: LSASS Memory

- Framework: MITRE ATT&CK (Enterprise matrix), sub-technique of T1003.
- Short title: "LSASS Memory".
- Rationale: the LSASS-access detection in the skill targets handle opens and memory reads against LSASS, which is the residue of T1003.001.
- Source: https://attack.mitre.org/techniques/T1003/001/

## ATT&CK T1003.002 - OS Credential Dumping: Security Account Manager

- Framework: MITRE ATT&CK (Enterprise matrix), sub-technique of T1003.
- Short title: "Security Account Manager".
- Rationale: the hive-theft detection covers SAM/SECURITY/SYSTEM export, raw reads, and shadow-copy extraction, which is exactly T1003.002.
- Source: https://attack.mitre.org/techniques/T1003/002/

## ATT&CK T1003.003 - OS Credential Dumping: NTDS

- Framework: MITRE ATT&CK (Enterprise matrix), sub-technique of T1003.
- Short title: "NTDS".
- Rationale: the domain-controller detection correlates shadow-copy creation to ntds.dit/ESE access, which is the footprint of T1003.003 NTDS extraction.
- Source: https://attack.mitre.org/techniques/T1003/003/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Analysis".
- Rationale: analyzing which process opened a handle to LSASS and its access rights is the process-analysis countermeasure D3-PA.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## D3FEND D3-PSA - Process Spawn Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Spawn Analysis".
- Rationale: correlating the requesting process to its parent chain to separate benign accessors from malicious ones is the process-spawn-analysis countermeasure D3-PSA.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessSpawnAnalysis/

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: the hunt deploys continuous detections across the fleet for credential-access activity, mapping to the Detect / Continuous Monitoring category.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.AE - Anomalies and Events

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Anomalies and Events".
- Rationale: each confirmed credential-dumping pattern is an analyzed anomaly/event routed into the SIEM under DE.AE.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
