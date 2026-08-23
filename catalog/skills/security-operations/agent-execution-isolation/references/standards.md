# Framework Standards Reference

Source provenance and framework mappings for the `agent-execution-isolation` skill. Each section gives the identifier, the framework's own short title (cited, not paraphrased), the rationale tying this skill to the ID, and a deep link to the public source.

This file is the single place external names belong. The skill body describes the durable pattern without naming research vendors or commercial sandbox products.

## Source Provenance

The three-layer model (OS sandbox, minimal in-loop runtime, out-of-process egress boundary), per-session ephemeral containers, placeholder-credential brokering, and static-rule plus LLM-judge plus human-escalation egress control are generalized from public articles and open-source agent-sandbox and egress-proxy designs. They are ingested as engineering patterns, not as product endorsements. Incident anecdotes in those sources are treated as unverified claims and are not reproduced in the skill.

- Source type: public design articles and self-hosted open-source repositories (sandbox runtimes and HTTP egress proxies).
- Not adopted: any vendor-operated hardened-image rebuild service, and any TLS-intercept proxy implementation as code in this catalog.

## ATT&CK T1611 - Escape to Host

- Framework: MITRE ATT&CK (Enterprise matrix), Privilege Escalation tactic.
- Short title: "Escape to Host".
- Rationale: the skill's objective is keeping agent execution inside a container plus kernel filters so a captured agent does not become host-privileged. Landlock, seccomp, dropped capabilities, and no runtime socket are the preventive mapping.
- Source: https://attack.mitre.org/techniques/T1611/

## ATT&CK T1552 - Unsecured Credentials

- Framework: MITRE ATT&CK (Enterprise matrix), Credential Access tactic.
- Short title: "Unsecured Credentials".
- Rationale: real API keys inside the agent environment are credentials an adversary who captures the agent can read. Placeholder credentials with injection at the egress broker remove that store.
- Source: https://attack.mitre.org/techniques/T1552/

## ATT&CK T1071 - Application Layer Protocol

- Framework: MITRE ATT&CK (Enterprise matrix), Command and Control tactic.
- Short title: "Application Layer Protocol".
- Rationale: agent exfiltration and tool calls travel over HTTP/HTTPS. The out-of-process egress proxy, static URL rules, and SSRF blocks are the network-layer response to application-layer egress.
- Source: https://attack.mitre.org/techniques/T1071/

## D3FEND D3-NTA - Network Traffic Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Network Traffic Analysis".
- Rationale: the proxy's audit log and deny/escalate decisions are traffic analysis at the only path the agent can use.
- Source: https://d3fend.mitre.org/technique/d3f:NetworkTrafficAnalysis/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Analysis".
- Rationale: inventorying in-loop binaries and applying seccomp to the agent process is process analysis and process restriction.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## D3FEND D3-FA - File Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "File Analysis".
- Rationale: Landlock rulesets and explicit mount allowlists classify which paths the agent may open; probes that attempt denied paths are file-access analysis.
- Source: https://d3fend.mitre.org/technique/d3f:FileAnalysis/

## NIST CSF PR.AC - Access Control

- Framework: NIST Cybersecurity Framework, Protect function. CSF 2.0 uses PR.AA for identity; PR.AC remains the widely cited access-control category label in this catalog's existing skills.
- Short title: "Access Control".
- Rationale: mount allowlists, dropped capabilities, and placeholder credentials are access control on what the agent may read and where it may authenticate.
- Source: https://www.nist.gov/cyberframework

## NIST CSF PR.DS - Data Security

- Framework: NIST Cybersecurity Framework, Protect function.
- Short title: "Data Security".
- Rationale: keeping production secrets out of the agent container and blocking private-range egress protect data in use and in transit from a captured agent.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.CM - Security Continuous Monitoring

- Framework: NIST Cybersecurity Framework, Detect function.
- Short title: "Security Continuous Monitoring".
- Rationale: the egress audit log and human escalation path are continuous monitoring of what leaves the agent boundary.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

Framework short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
