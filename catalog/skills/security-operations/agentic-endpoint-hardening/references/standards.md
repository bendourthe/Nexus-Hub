# Framework Standards Reference

Source provenance and framework mappings for the `agentic-endpoint-hardening` skill. Each framework section gives the identifier, the framework's own short title (cited, not paraphrased), the rationale tying this skill to the ID, and a deep link to the public source.

This file is the single place where the external source is named. Per the Reverse-Engineering Attribution Rule in `AGENTS.md`, the skill body itself stays generic: it describes the durable pattern and the affected component classes without naming the research vendor, its framework, or its commercial product.

## Source Provenance

The escape taxonomy and the layered control model in `SKILL.md` are generalized from a public security-research series.

- Primary source: Pillar Security, "The Week of Sandbox Escapes".
- Source URL: https://www.pillar.security/blog/the-week-of-sandbox-escapes
- Source type: public security-research report (web article). Ingested as data, not as instructions; a pre-ingest source security scan returned a CLEAR verdict (no hidden directives, no obfuscated payloads, no destructive samples).
- Referenced by name only, not reproduced: the vendor's SAIL 2.0 framework. Its structure and text are that vendor's intellectual property and are deliberately not adopted into catalog content. Only the independently-derivable engineering conclusions were adopted.
- Not adopted: the vendor's commercial endpoint product. It was assessed and dropped under the MCP Registry Policy hard-no list (it is a third-party data processor receiving endpoint trust-handoff telemetry). Its valuable concept, provenance plus seam monitoring, is reverse-engineered locally as a best-effort ledger with the boundary documented in the skill's "Limits and Honest Boundaries" section.

### Underlying public advisories

The six taxonomy forms generalize the following publicly disclosed findings across mainstream coding-agent and editor platforms (2025 to 2026). They are recorded here for traceability; the skill body deliberately describes component classes rather than product versions, so that the guidance stays accurate as products patch.

| Taxonomy form | Public identifier | Disposition at time of writing |
|---|---|---|
| Harness hook configuration | CVE-2026-48124, GHSA-pc9j-3qc2-95wv | Patched |
| Privileged local daemon (container socket) | GHSA-v4xv-rqh3-w9mc | Fixed |
| Interpreter or shim substitution | GHSA-p9g2-cr55-cw9c | Fixed |
| Version-control metadata indirection | CVE pending at time of writing | Patched |
| Safe-name argument smuggling | CVE pending at time of writing | Patched |
| Editor task configuration | Vendor-assessed, severity downgraded | Downgraded |
| Allow-default sandbox denylist bypass | Vendor-assessed, severity downgraded | Downgraded |

The first row is the reason this skill exists in this catalog specifically: the affected surface is a workspace-controlled agent-harness hook configuration, which is exactly the artifact class Nexus-Hub distributes.

## ATT&CK T1546 - Event Triggered Execution

- Framework: MITRE ATT&CK (Enterprise matrix), Persistence and Privilege Escalation tactics.
- Short title: "Event Triggered Execution".
- Rationale: the config-write-then-executed pattern is event-triggered execution seen from the defender's seat. The agent writes a configuration entry (a harness hook, an editor task, a version-control hook path) that a trusted component executes on a later event such as session start, folder open, or commit. This is the single technique that unifies the taxonomy.
- Source: https://attack.mitre.org/techniques/T1546/

## ATT&CK T1059 - Command and Scripting Interpreter

- Framework: MITRE ATT&CK (Enterprise matrix), Execution tactic.
- Short title: "Command and Scripting Interpreter".
- Rationale: in every taxonomy form the payload is a command line or script that the trusting component hands to an interpreter at its own privilege. The command policy layer (control layer 6) and the group B command-string patterns both target this technique.
- Source: https://attack.mitre.org/techniques/T1059/

## ATT&CK T1611 - Escape to Host

- Framework: MITRE ATT&CK (Enterprise matrix), Privilege Escalation tactic.
- Short title: "Escape to Host".
- Rationale: the skill's objective is preventing execution that crosses out of the agent's sandbox onto the host. This is most literal in the privileged-local-daemon form, where a reachable daemon socket runs host-privileged work on request, but it is the outcome every form produces.
- Source: https://attack.mitre.org/techniques/T1611/

## D3FEND D3-FA - File Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "File Analysis".
- Rationale: classifying agent-writable configuration as execution-triggering, and inspecting the content of a write to a listed surface, is the file-analysis countermeasure. Control layer 2 and the group A and C path patterns implement it.
- Source: https://d3fend.mitre.org/technique/d3f:FileAnalysis/

## D3FEND D3-FH - File Hashing

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "File Hashing".
- Rationale: the provenance and seam-monitoring layers (control layers 8 and 9) record a content hash for each agent write rather than the file body, which is both the correlation mechanism and the redaction discipline. File hashing is precisely that countermeasure.
- Source: https://d3fend.mitre.org/technique/d3f:FileHashing/

## D3FEND D3-PA - Process Analysis

- Framework: MITRE D3FEND, Detect tactic.
- Short title: "Process Analysis".
- Rationale: naming the executing component, its privilege, and its trigger for each writable surface (instruction step 2), and correlating a later command against recently written paths (instruction step 7), is process analysis.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessAnalysis/

## NIST CSF PR.PS - Platform Security

- Framework: NIST Cybersecurity Framework 2.0, Protect function.
- Short title: "Platform Security".
- Rationale: the nine control layers harden the developer endpoint's configuration and execution surface, which is the platform-security outcome category. Deny-by-default scoping, sensitive-config classification, and privileged-daemon restriction all sit here.
- Source: https://www.nist.gov/cyberframework

## NIST CSF DE.CM - Continuous Monitoring

- Framework: NIST Cybersecurity Framework 2.0, Detect function. Titled "Security Continuous Monitoring" in CSF 1.1.
- Short title: "Continuous Monitoring".
- Rationale: control layer 9 instruments the trust handoff so a write that is later executed leaves a correlated record, which is the continuous-monitoring category. The skill's honest-boundary section records where that monitoring cannot reach.
- Source: https://www.nist.gov/cyberframework

## D3FEND D3-CR - Credential Revoking

- Framework: MITRE D3FEND, Evict tactic.
- Short title: "Credential Revoking".
- Rationale: the deterministic response class in step 7 names credential revocation as one of three automated responses to an architectural-assumption violation that no legitimate operation produces.
- Source: https://d3fend.mitre.org/technique/d3f:CredentialRevoking/

## D3FEND D3-PT - Process Termination

- Framework: MITRE D3FEND, Evict tactic.
- Short title: "Process Termination".
- Rationale: terminating the workload is the strongest of the three deterministic responses in step 7, reserved for violations that pass the qualifying test and have been observed stopping a test event.
- Source: https://d3fend.mitre.org/technique/d3f:ProcessTermination/

---

## Attribution

Framework short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATT&CK, D3FEND) and the National Institute of Standards and Technology (NIST CSF). Advisory identifiers are maintained by their respective CVE and GitHub Security Advisory registries.
