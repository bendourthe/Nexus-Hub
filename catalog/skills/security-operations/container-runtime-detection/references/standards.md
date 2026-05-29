# Framework Standards Reference

Framework identifiers mapped to the container-runtime-detection skill. Each entry gives the framework name and tactic or function, the framework's own short title (cited, not paraphrased), the rationale tying this skill to the identifier, and a deep link to the public source.

## ATT&CK T1610 - Deploy Container

- Framework: MITRE ATT&CK (Enterprise matrix), Defense Evasion / Execution tactics.
- Short title: "Deploy Container".
- Rationale: detecting unexpected or malicious workloads (including mining containers) deployed into the cluster catches the adversary container-deployment behavior T1610 describes.
- Source: https://attack.mitre.org/techniques/T1610/

## ATT&CK T1611 - Escape to Host

- Framework: MITRE ATT&CK (Enterprise matrix), Privilege Escalation tactic.
- Short title: "Escape to Host".
- Rationale: the skill's container-escape detections (privileged mounts, host namespaces, capability abuse) target exactly the breakout behavior T1611 covers.
- Source: https://attack.mitre.org/techniques/T1611/

## ATT&CK T1613 - Container and Resource Discovery

- Framework: MITRE ATT&CK (Enterprise matrix), Discovery tactic.
- Short title: "Container and Resource Discovery".
- Rationale: suspicious exec-into-pod sessions and orchestrator API activity often perform the in-cluster discovery T1613 describes, which the skill detects and attributes via the audit trail.
- Source: https://attack.mitre.org/techniques/T1613/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic (Platform Monitoring).
- Short title: "Process Analysis".
- Rationale: the skill analyzes per-container process and syscall behavior against a baseline, the defensive analysis activity D3FEND catalogs under D3-PA.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: standing runtime detections over container and orchestrator telemetry are continuous monitoring, CSF's DE.CM category.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.AE - Anomalies and Events

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Anomalies and Events".
- Rationale: baselining workload behavior and correlating deviations into triaged alerts is the anomaly-and-event analysis CSF's DE.AE category defines.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
