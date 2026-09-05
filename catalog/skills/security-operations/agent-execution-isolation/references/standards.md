# Framework Standards Reference

Source provenance and framework mappings for the `agent-execution-isolation` skill. Each section gives the identifier, the framework's own short title (cited, not paraphrased), the rationale tying this skill to the ID, and a deep link to the public source.

This file is the single place external names belong. The skill body describes the durable pattern without naming research vendors or commercial sandbox products.

## Source Provenance

The four-layer model (hardened host environment, OS sandbox, minimal in-loop runtime and sandbox configuration, out-of-process egress boundary with transitive-reachability checking), per-session ephemeral containers, placeholder-credential brokering, and static-rule plus LLM-judge plus human-escalation egress control are generalized from public articles and open-source agent-sandbox and egress-proxy designs. They are ingested as engineering patterns, not as product endorsements. Incident anecdotes in those sources are treated as unverified claims and are not reproduced in the skill. The v4.5.0 additions (transitive reachability, shared writable services as inter-agent channels, the host layer under assumed sandbox compromise, boundary-interface minimization) generalize publicly reported 2026 incidents and a published virtual-machine escape result; they are described in the body as patterns, with no researcher, company, product, or hypervisor named.

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

## ATT&CK T1090 - Proxy

- Framework: MITRE ATT&CK (Enterprise matrix), Command and Control tactic.
- Short title: "Proxy".
- Rationale: an allowlisted internal service with its own internet egress functions as a proxy for a sandboxed agent. The transitive-reachability control in step 5 exists to find that route before the allowlist approves it.
- Source: https://attack.mitre.org/techniques/T1090/

## ATT&CK T1080 - Taint Shared Content

- Framework: MITRE ATT&CK (Enterprise matrix), Lateral Movement tactic.
- Short title: "Taint Shared Content".
- Rationale: a writable service reachable from more than one agent session is shared content one session can taint for another. The shared-writable-service enumeration and remediation ladder in step 3 are the preventive mapping.
- Source: https://attack.mitre.org/techniques/T1080/

## D3FEND D3-NI - Network Isolation

- Framework: MITRE D3FEND, Isolate tactic.
- Short title: "Network Isolation".
- Rationale: enforcing egress at the workload, subnet, and perimeter tiers rather than at a single proxy, and restricting sandbox hosts from management networks and control planes, are network isolation applied at more than one layer.
- Source: https://d3fend.mitre.org/technique/d3f:NetworkIsolation/

## D3FEND D3-PH - Platform Hardening

- Framework: MITRE D3FEND, Harden tactic.
- Short title: "Platform Hardening".
- Rationale: host-level mandatory access control, secrets kept off sandbox hosts, dedicated infrastructure for high-risk workloads, and a minimal sandbox configuration with unused devices, mounts, and management interfaces removed are platform hardening of the environment the sandbox stands on.
- Source: https://d3fend.mitre.org/technique/d3f:PlatformHardening/

## NIST CSF PR.PT - Protective Technology

- Framework: NIST Cybersecurity Framework, Protect function.
- Short title: "Protective Technology".
- Rationale: mandatory access control on sandbox hosts, minimal machine configuration, and multi-layer egress enforcement are protective technology managed to secure the systems the agent runs on.
- Source: https://www.nist.gov/cyberframework

---

## Attribution

Framework short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF).
