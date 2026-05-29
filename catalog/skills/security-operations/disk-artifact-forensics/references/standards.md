# Framework Standards Reference

Framework mappings for the `disk-artifact-forensics` skill. Each section gives the framework identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source.

## ATT&CK T1070 - Indicator Removal

- Framework: MITRE ATT&CK (Enterprise matrix), Defense Evasion tactic.
- Short title: "Indicator Removal".
- Rationale: the skill detects the residue of indicator removal - timestomping ($SI vs $FN mismatch) and event-log clearing/gaps - which is the forensic footprint of T1070.
- Source: https://attack.mitre.org/techniques/T1070/

## ATT&CK T1547 - Boot or Logon Autostart Execution

- Framework: MITRE ATT&CK (Enterprise matrix), Persistence and Privilege Escalation tactics.
- Short title: "Boot or Logon Autostart Execution".
- Rationale: the registry-hive step recovers Run/RunOnce keys, services, and autostart locations, which are the persistence mechanisms catalogued under T1547.
- Source: https://attack.mitre.org/techniques/T1547/

## ATT&CK T1059 - Command and Scripting Interpreter

- Framework: MITRE ATT&CK (Enterprise matrix), Execution tactic.
- Short title: "Command and Scripting Interpreter".
- Rationale: the program-execution evidence from prefetch, amcache, and shimcache reconstructs what interpreters and tools ran, which is the execution activity T1059 describes.
- Source: https://attack.mitre.org/techniques/T1059/

## D3FEND D3-FA - File Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "File Analysis".
- Rationale: parsing the MFT, $UsnJrnl, prefetch, and amcache/shimcache files to characterize on-disk activity is the file-analysis countermeasure D3-FA.
- Source: https://d3fend.mitre.org/technique/d3f:FileAnalysis/

## D3FEND D3-SFA - System File Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "System File Analysis".
- Rationale: analyzing OS system artifacts - registry hives, event logs, and execution caches - to reconstruct host state is the system-file-analysis countermeasure D3-SFA.
- Source: https://d3fend.mitre.org/technique/d3f:SystemFileAnalysis/

## NIST CSF DE.AE - Anomalies and Events

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Anomalies and Events".
- Rationale: each reconstructed event (execution, persistence, anti-forensic action) is an analyzed anomaly/event placed on the timeline under DE.AE.
- Source: https://www.nist.gov/cyberframework

## NIST CSF RS.AN - Analysis

- Framework: NIST Cybersecurity Framework, Respond function.
- Short title: "Analysis".
- Rationale: building a defensible host timeline to understand the scope and impact of an incident is the response-analysis activity under RS.AN.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
