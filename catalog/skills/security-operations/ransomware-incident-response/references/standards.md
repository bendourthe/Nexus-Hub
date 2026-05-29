# Framework Standards Reference

Framework mappings for the ransomware-incident-response skill. Each entry gives the identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source.

## ATT&CK T1486 - Data Encrypted for Impact

- Framework: MITRE ATT&CK (Enterprise matrix), Impact tactic.
- Short title: "Data Encrypted for Impact".
- Rationale: this skill responds to active mass file encryption, which is exactly the impact behavior ATT&CK catalogs as T1486.
- Source: https://attack.mitre.org/techniques/T1486/

## ATT&CK T1490 - Inhibit System Recovery

- Framework: MITRE ATT&CK (Enterprise matrix), Impact tactic.
- Short title: "Inhibit System Recovery".
- Rationale: the runbook's backup-protection and shadow-copy-deletion detection steps directly counter the recovery-inhibition behavior ATT&CK defines as T1490.
- Source: https://attack.mitre.org/techniques/T1490/

## ATT&CK T1489 - Service Stop

- Framework: MITRE ATT&CK (Enterprise matrix), Impact tactic.
- Short title: "Service Stop".
- Rationale: eradication includes detecting and reversing the service-stop actions ransomware uses to disable defenses and unlock files for encryption, which ATT&CK catalogs as T1489.
- Source: https://attack.mitre.org/techniques/T1489/

## D3FEND D3-FA - File Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "File Analysis".
- Rationale: the evidence-preservation phase analyzes the ransom note, encrypted samples, and dropped files, the defender action D3FEND defines as D3-FA.
- Source: https://d3fend.mitre.org/technique/d3f:FileAnalysis/

## D3FEND D3-FH - File Hashing

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "File Hashing".
- Rationale: chain-of-custody for collected artifacts depends on recording cryptographic hashes, the file-hashing defender action D3FEND defines as D3-FH.
- Source: https://d3fend.mitre.org/technique/d3f:FileHashing/

## NIST CSF RS.RP - Response Planning

- Framework: NIST Cybersecurity Framework, Respond function.
- Short title: "Response Planning".
- Rationale: the runbook itself is an executed response plan, the governance-level practice CSF places under RS.RP.
- Source: https://www.nist.gov/cyberframework

## NIST CSF RS.MI - Mitigation

- Framework: NIST Cybersecurity Framework, Respond function.
- Short title: "Mitigation".
- Rationale: the containment and eradication phases mitigate and contain the incident, the CSF Respond category RS.MI.
- Source: https://www.nist.gov/cyberframework

## NIST CSF RC.RP - Recovery Planning

- Framework: NIST Cybersecurity Framework, Recover function.
- Short title: "Recovery Planning".
- Rationale: the staged restore-from-clean-backup phase is the recovery-planning execution CSF defines as RC.RP.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: detection, triage, and the heightened monitoring during recovery rely on continuous monitoring, the CSF Detect category DE.CM.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
