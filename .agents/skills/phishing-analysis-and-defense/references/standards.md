# Framework Standards Reference

Framework mappings for the `phishing-analysis-and-defense` skill. Each section gives the framework identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source.

## ATT&CK T1566 - Phishing

- Framework: MITRE ATT&CK (Enterprise matrix), Initial Access tactic.
- Short title: "Phishing".
- Rationale: the skill triages a suspected phishing message end to end (sender, routing, links, attachments), which is the defensive analysis of the T1566 initial-access technique.
- Source: https://attack.mitre.org/techniques/T1566/

## ATT&CK T1566.001 - Phishing: Spearphishing Attachment

- Framework: MITRE ATT&CK (Enterprise matrix), Initial Access tactic, sub-technique of T1566.
- Short title: "Spearphishing Attachment".
- Rationale: the attachment-characterization step identifies macro documents, script files, and disguised executables delivered as attachments, which is the defensive view of T1566.001.
- Source: https://attack.mitre.org/techniques/T1566/001/

## ATT&CK T1566.002 - Phishing: Spearphishing Link

- Framework: MITRE ATT&CK (Enterprise matrix), Initial Access tactic, sub-technique of T1566.
- Short title: "Spearphishing Link".
- Rationale: the defanged-URL inspection step detects credential-harvest and redirect links embedded in the message, which is the defensive view of T1566.002.
- Source: https://attack.mitre.org/techniques/T1566/002/

## D3FEND D3-FA - File Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "File Analysis".
- Rationale: identifying attachment true type, hashing, and checking indicators without execution is the file-analysis countermeasure D3FEND defines under D3-FA.
- Source: https://d3fend.mitre.org/technique/d3f:FileAnalysis/

## NIST CSF PR.AT - Awareness and Training

- Framework: NIST Cybersecurity Framework, Protect function.
- Short title: "Awareness and Training".
- Rationale: acknowledging the reporter and feeding awareness gaps back as training inputs reinforces the user-reporting behavior covered by PR.AT.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: hunting the mail logs for other recipients and clickers of the same campaign is a continuous-monitoring detection practice under DE.CM.
- Source: https://www.nist.gov/cyberframework

## NIST CSF RS.AN - Analysis

- Framework: NIST Cybersecurity Framework, Respond function.
- Short title: "Analysis".
- Rationale: reaching a graded verdict from the collected indicators and recording it for the incident is the response-analysis activity defined under RS.AN.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
