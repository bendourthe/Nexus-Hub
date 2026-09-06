# Framework Standards Reference

Framework mappings for the `skill-security-scan` skill. Each section gives the framework identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source.

## ATT&CK T1059 - Command and Scripting Interpreter

- Framework: MITRE ATT&CK (Enterprise matrix), Execution tactic.
- Short title: "Command and Scripting Interpreter".
- Rationale: the scanner and this adjudication look for skill text and bundled scripts that would cause an agent to execute interpreter or shell constructs (eval, exec, subprocess, dynamic imports). That is the execution residue of T1059, whether the payload is Python, a shell one-liner, or an MCP tool that shells out.
- Source: https://attack.mitre.org/techniques/T1059/

## ATT&CK T1041 - Exfiltration Over C2 Channel

- Framework: MITRE ATT&CK (Enterprise matrix), Exfiltration tactic.
- Short title: "Exfiltration Over C2 Channel".
- Rationale: several detection classes (data exfiltration, taint tracking) exist to catch skill code that harvests environment, files, or conversation context and ships it to an external host. Adjudicating those findings is a T1041 judgment: is there a real outbound sink on an execution path, or only an illustrative snippet?
- Source: https://attack.mitre.org/techniques/T1041/

## ATT&CK T1552 - Unsecured Credentials

- Framework: MITRE ATT&CK (Enterprise matrix), Credential Access tactic.
- Short title: "Unsecured Credentials".
- Rationale: the scanner flags credential-store reads, hardcoded secrets, and environment-variable harvesting inside skill scripts. This skill decides whether those matches are documentation or a real attempt to collect unsecured credentials at install or run time, which is T1552.
- Source: https://attack.mitre.org/techniques/T1552/

## ATT&CK T1195 - Supply Chain Compromise

- Framework: MITRE ATT&CK (Enterprise matrix), Initial Access tactic.
- Short title: "Supply Chain Compromise".
- Rationale: a third-party skill is a supply-chain artifact. Unpinned fetches, obfuscated payloads, and MCP servers whose declared tools do not match their code are T1195-class compromise delivered through the skill catalog rather than a traditional package mirror. This skill is the install-time gate for that path.
- Source: https://attack.mitre.org/techniques/T1195/

## ATT&CK T1548 - Abuse Elevation Control Mechanism

- Framework: MITRE ATT&CK (Enterprise matrix), Privilege Escalation tactic.
- Short title: "Abuse Elevation Control Mechanism".
- Rationale: privilege-escalation and MCP least-privilege classes catch sudo/root execution and over-broad tool scopes. Adjudicating those findings asks whether the skill actually abuses an elevation control (or silently widens agency) versus documenting the anti-pattern, which is T1548.
- Source: https://attack.mitre.org/techniques/T1548/

## ATLAS AML.T0051 - LLM Prompt Injection

- Framework: MITRE ATLAS (adversarial ML), initial-access / persistence against an LLM agent.
- Short title: "LLM Prompt Injection".
- Rationale: prompt injection, system-prompt leakage, memory poisoning, trigger abuse, and MCP tool-description poisoning are all prompt-injection families against an LLM agent. This skill's job is to tell a teaching example of injection from a skill that actually injects. That is AML.T0051.
- Source: https://atlas.mitre.org/techniques/AML.T0051

## D3FEND D3-FA - File Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "File Analysis".
- Rationale: the deterministic detector inspects SKILL.md files, bundled scripts, and MCP configs as files, then this skill analyzes those artifacts for malicious versus illustrative content. That file-analysis countermeasure is D3-FA.
- Source: https://d3fend.mitre.org/technique/d3f:FileAnalysis/

## D3FEND D3-NTA - Network Traffic Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Network Traffic Analysis".
- Rationale: exfiltration and MCP-poisoning adjudication both ask whether the skill opens a real network sink (POST, webhook, wildcard egress) or only mentions one. Inspecting declared versus actual network behavior is the network-traffic-analysis countermeasure D3-NTA.
- Source: https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/

## NIST CSF DE.CM - Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Continuous Monitoring".
- Rationale: the skill is meant to run on every candidate install and as a CI catalog gate, continuously monitoring inbound skills for malicious patterns rather than as a one-off audit. That is DE.CM.
- Source: https://www.nist.gov/cyberframework

## NIST CSF ID.RA - Risk Assessment

- Framework: NIST Cybersecurity Framework, Identify function.
- Short title: "Risk Assessment".
- Rationale: the output of this skill is an install verdict with residual-risk reasoning (safe / caution / do not install). That is a risk assessment of a specific artifact against the user's threat model, which maps to ID.RA.
- Source: https://www.nist.gov/cyberframework

## NIST AI RMF MEASURE-2.6 - AI system safety evaluation

- Framework: NIST AI Risk Management Framework, MEASURE function.
- Short title: "AI system safety evaluation".
- Rationale: scanning and adjudicating skills before an AI agent loads them is a measurement of whether the agent runtime would ingest unsafe instructions or tools. MEASURE-2.6 is the evaluation of those safety properties; this skill is that evaluation's human/agent adjudication stage.
- Source: https://www.nist.gov/itl/ai-risk-management-framework

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, ATLAS, D3FEND) and the National Institute of Standards and Technology (NIST CSF and AI RMF).
