# Skill-Security Detection Classes

This reference defines the 16 vulnerability classes the deterministic detector (`nexus-skill-scanner`, Phase 6) covers and that the `skill-security-scan` skill adjudicates. For each class it gives a definition, what the adjudicator should check when deciding true-positive vs. false-positive, and the primary security-framework identifiers. It is the framework-mapping companion for the parent skill.

**On framework identifiers.** The identifiers below are the *primary* mapping for each class -- the single most representative technique or category. They are not an exhaustive enumeration, and MITRE and NIST revise their matrices over time, so verify the exact (sub-)technique against the linked live source before quoting it in a report. Nexus-Hub does not reproduce framework text; it cites the canonical identifier and links to the public source. Use [[security-framework-mapping]] to assign a more specific identifier to an individual finding.

## Master table

| # | Class (pattern count) | What it is | What the adjudicator checks | Primary framework IDs |
|---|---|---|---|---|
| 1 | Prompt Injection (5) | Instruction overrides, hidden directives, or exfiltration commands embedded in skill text so the agent obeys the skill author instead of the user. | Is the override an actual instruction to the agent, or text inside a fenced example that *teaches* injection? Is it positioned to reach the system prompt? | ATT&CK T1059; ATLAS AML.T0051; NIST CSF DE.AE |
| 2 | Data Exfiltration (4) | Environment-variable harvesting, filesystem enumeration, or context leakage that ships data off the machine. | Is there a real sink (network POST, external URL, write to a shared location) on an execution path, or only an illustrative snippet? | ATT&CK T1041 / T1567; ATLAS AML.T0024; NIST CSF PR.DS |
| 3 | Privilege Escalation (3) | sudo/root execution or credential access from a skill's scripts. | Does an executable script actually invoke elevation or read credential stores, or is it documented as an example of what to avoid? | ATT&CK T1548 / T1552; NIST CSF PR.AA |
| 4 | Supply Chain (6) | Unpinned dependencies, external script fetch, obfuscation, abandoned/typosquatted packages, known CVEs. | Is the dependency real and resolved at install/run time? Is the fetch from an untrusted host? Is obfuscation hiding behavior? | ATT&CK T1195 (T1195.001); NIST CSF ID.SC |
| 5 | Excessive Agency (4) | Unrestricted tool access, scope creep, or unbounded resource use beyond the skill's stated purpose. | Does the granted capability exceed what the skill needs to do its job? Is the breadth justified in a comment? | ATT&CK T1548; ATLAS AML.T0053; NIST CSF PR.AA |
| 6 | Output Handling (3) | Unsafe handling of model output (rendering untrusted output as code, command, or markup downstream). | Does the skill route model output into an execution or render sink without sanitization? | ATT&CK T1059; NIST CSF PR.PS |
| 7 | System Prompt Leakage (3) | Text engineered to extract or expose the agent's system prompt or hidden instructions. | Is the construct designed to elicit the system prompt, or is it discussing prompt-leakage defensively? | ATLAS AML.T0051; NIST CSF DE.AE |
| 8 | Memory Poisoning (3) | Persistent injection or context stuffing that corrupts the agent's memory across sessions (relevant to memory templates). | Does the skill write attacker-controlled content into a persistent memory store the agent later trusts? | ATT&CK T1565; ATLAS AML.T0051; NIST CSF PR.DS |
| 9 | Tool Misuse (3) | Driving a legitimate tool toward a harmful end (a file tool used to overwrite system files, a shell tool used to persist). | Is the tool call benign-but-misdirected, and is it on an execution path? | ATT&CK T1059; ATLAS AML.T0053; NIST CSF DE.CM |
| 10 | Rogue Agent (2) | Self-modification or unauthorized persistence (the skill installs itself, edits its own triggers, or survives beyond its task). | Does the skill modify its own definition or establish persistence without the user's intent? | ATT&CK T1546; NIST CSF DE.CM |
| 11 | Trigger Abuse (3) | Overly broad triggers, shadow commands, or keyword baiting -- the malicious inverse of a legitimate pushy description. | Do the triggers bait the agent into running the skill on unrelated tasks, or shadow another command's name? | ATT&CK T1036; ATLAS AML.T0051; NIST CSF DE.AE |
| 12 | Behavioral AST (8) | exec/eval, dynamic imports, subprocess, getattr manipulation, and reflective code loading in skill scripts. | Is the dangerous call in code the skill executes, or quoted in prose / a fenced example? | ATT&CK T1059 / T1620; D3FEND D3-DA; NIST CSF DE.CM |
| 13 | Taint Tracking (5) | Dangerous data flows: input-to-execution, file-to-network, and credential chains. | Does untrusted input actually reach a dangerous sink along a real path, or is the flow hypothetical? | ATT&CK T1059 / T1041; D3FEND D3-DA; NIST CSF DE.CM |
| 14 | YARA Signatures (4) | Malware, webshell, cryptominer, and exploit signatures (the optional YARA module, Phase 7). | Does the signature match real bundled bytes, or a benign string that happens to match a loose rule? | ATT&CK T1505.003 / T1496; D3FEND D3-FA; NIST CSF DE.CM |
| 15 | MCP Least Privilege (4) | Under- or over-declaration of MCP tool scopes, and wildcard scopes. | Compare declared scope against actual use. Is breadth justified by a comment, or is it silent scope creep? | ATT&CK T1548; ATLAS AML.T0053; NIST CSF PR.AA |
| 16 | MCP Tool Poisoning (4) | Hidden instructions in tool descriptions, parameter injection, and description-vs-behavior mismatch. | Does the server's declared behavior match what its code does? Are there hidden directives in a tool description? | ATT&CK T1195; ATLAS AML.T0051; D3FEND D3-NTA; NIST CSF DE.AE |

## Framework identifier sources

Each identifier referenced above, with its framework, short title, and the public source to verify it against. Look up the most specific applicable (sub-)technique at these URLs when tagging a finding.

### MITRE ATT&CK (Enterprise)

- **T1059 -- Command and Scripting Interpreter**: https://attack.mitre.org/techniques/T1059/
- **T1041 -- Exfiltration Over C2 Channel**: https://attack.mitre.org/techniques/T1041/
- **T1567 -- Exfiltration Over Web Service**: https://attack.mitre.org/techniques/T1567/
- **T1548 -- Abuse Elevation Control Mechanism**: https://attack.mitre.org/techniques/T1548/
- **T1552 -- Unsecured Credentials**: https://attack.mitre.org/techniques/T1552/
- **T1195 -- Supply Chain Compromise** (see T1195.001 for software dependencies): https://attack.mitre.org/techniques/T1195/
- **T1565 -- Data Manipulation**: https://attack.mitre.org/techniques/T1565/
- **T1546 -- Event Triggered Execution**: https://attack.mitre.org/techniques/T1546/
- **T1036 -- Masquerading**: https://attack.mitre.org/techniques/T1036/
- **T1620 -- Reflective Code Loading**: https://attack.mitre.org/techniques/T1620/
- **T1505.003 -- Server Software Component: Web Shell**: https://attack.mitre.org/techniques/T1505/003/
- **T1496 -- Resource Hijacking**: https://attack.mitre.org/techniques/T1496/

### MITRE ATLAS (adversarial ML)

- **AML.T0051 -- LLM Prompt Injection**: https://atlas.mitre.org/techniques/AML.T0051
- **AML.T0024 -- Exfiltration via ML Inference API**: https://atlas.mitre.org/techniques/AML.T0024
- **AML.T0053 -- LLM Plugin Compromise**: https://atlas.mitre.org/techniques/AML.T0053
- ATLAS matrix (verify any AML identifier here, as the matrix is revised over time): https://atlas.mitre.org/

### MITRE D3FEND (defensive countermeasures)

- **D3-DA -- Dynamic Analysis**: https://d3fend.mitre.org/
- **D3-FA -- File Analysis**: https://d3fend.mitre.org/
- **D3-NTA -- Network Traffic Analysis**: https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/
- D3FEND matrix (verify any D3 identifier here): https://d3fend.mitre.org/

### NIST Cybersecurity Framework

- **DE.CM -- Continuous Monitoring**: https://www.nist.gov/cyberframework
- **DE.AE -- Adverse Event Analysis (Anomalies and Events)**: https://www.nist.gov/cyberframework
- **ID.RA -- Risk Assessment**: https://www.nist.gov/cyberframework
- **ID.SC -- Supply Chain Risk Management** (GV.SC in CSF 2.0): https://www.nist.gov/cyberframework
- **PR.AA -- Identity Management, Authentication and Access Control**: https://www.nist.gov/cyberframework
- **PR.DS -- Data Security**: https://www.nist.gov/cyberframework
- **PR.PS -- Platform Security**: https://www.nist.gov/cyberframework

### NIST AI Risk Management Framework

- **MEASURE-2.6 -- AI system safety evaluation**: https://www.nist.gov/itl/ai-risk-management-framework

---

## Attribution

The 16-class taxonomy is a re-authored synthesis of public skill-security knowledge; no external project's text, pattern source, or evaluation metric is reproduced here. Framework short titles are quoted from each framework's public catalog (maintained by MITRE Corporation for ATT&CK, ATLAS, and D3FEND, and by NIST for the CSF and AI RMF); the full prose lives at the linked public sources.
