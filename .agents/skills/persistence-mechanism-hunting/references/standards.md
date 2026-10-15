# Framework Standards Reference

Framework mappings for the persistence-mechanism-hunting skill. Each entry gives the identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source.

## ATT&CK T1547 - Boot or Logon Autostart Execution

- Framework: MITRE ATT&CK (Enterprise matrix), Persistence tactic.
- Short title: "Boot or Logon Autostart Execution".
- Rationale: the skill hunts registry run keys and startup-folder entries that auto-execute at boot or logon, the persistence class ATT&CK catalogs as T1547.
- Source: https://attack.mitre.org/techniques/T1547/

## ATT&CK T1053 - Scheduled Task/Job

- Framework: MITRE ATT&CK (Enterprise matrix), Persistence tactic.
- Short title: "Scheduled Task/Job".
- Rationale: scheduled-task enumeration and triage in this skill target the persistence technique ATT&CK defines as T1053.
- Source: https://attack.mitre.org/techniques/T1053/

## ATT&CK T1543 - Create or Modify System Process

- Framework: MITRE ATT&CK (Enterprise matrix), Persistence tactic.
- Short title: "Create or Modify System Process".
- Rationale: the service-hunting steps look for malicious or modified auto-start services, the system-process persistence ATT&CK catalogs as T1543.
- Source: https://attack.mitre.org/techniques/T1543/

## ATT&CK T1546 - Event Triggered Execution

- Framework: MITRE ATT&CK (Enterprise matrix), Persistence tactic.
- Short title: "Event Triggered Execution".
- Rationale: WMI permanent event subscription hunting targets event-triggered persistence, which ATT&CK defines as T1546.
- Source: https://attack.mitre.org/techniques/T1546/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Analysis".
- Rationale: enriching each candidate by parent and creating process is the process-analysis defender action D3FEND defines as D3-PA.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## D3FEND D3-SFA - System File Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "System File Analysis".
- Rationale: checking signature, path, and masquerading on autostart binaries is the system-file-analysis defender action D3FEND defines as D3-SFA.
- Source: https://d3fend.mitre.org/technique/d3f:SystemFileAnalysis/

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: fleet-wide persistence hunting is a continuous-monitoring practice, the CSF Detect category DE.CM.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.AE - Anomalies and Events

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Anomalies and Events".
- Rationale: low-prevalence and baseline-deviating autostart entries are anomalies analyzed for impact, the CSF Detect category DE.AE.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
