---
name: security-framework-mapping
description: Map a security skill, finding, detection, or control to identifiers across MITRE ATT&CK, ATLAS, D3FEND, F3 (Fight Fraud Framework), NIST CSF, and NIST AI RMF, then tag optional frontmatter so a coverage matrix can be generated. Use whenever the user asks "what ATT&CK technique is this", "tag this skill with the framework", "which NIST control covers X", "map this finding to ATT&CK / D3FEND / ATLAS / F3", "build a framework coverage matrix", "what AI RMF measure applies here", "Fight Fraud Framework", "cyber-enabled financial fraud TTPs", or wants to align a security artifact with a published taxonomy even if the framework name is implied. SKIP, do NOT use for, end-to-end threat modeling (use architecture-design), running a security audit (use run-security-audit), or regulation-specific compliance evidence (use gdpr-compliance, soc2-compliance, iso27001-compliance).
summary_l0: "Map security artifacts across ATT&CK, ATLAS, D3FEND, F3, CSF, and AI RMF"
overview_l1: "Cross-maps a security artifact to identifiers from six public taxonomies: MITRE ATT&CK, ATLAS, D3FEND, F3 (Fight Fraud Framework v1.1, 2026-04-09, cyber-enabled financial fraud TTPs after initial compromise), NIST CSF, and NIST AI RMF. Covers which framework fits, how to find the identifier, how to record it in optional frontmatter (mitre_attack, atlas_techniques, d3fend_techniques, mitre_f3, nist_csf, nist_ai_rmf) plus references/standards.md, and how those tags feed the coverage-matrix generator. Trigger phrases: ATT&CK technique, D3FEND countermeasure, NIST CSF mapping, AI RMF measure, ATLAS technique, Fight Fraud Framework, F3, framework coverage matrix."
mitre_attack: [T1003.001, T1071]
atlas_techniques: [AML.T0047]
d3fend_techniques: [D3-NTA]
nist_csf: [DE.CM, ID.RA]
nist_ai_rmf: [MEASURE-2.6]
---

# Security Framework Mapping

Cross-map a security artifact to its identifiers across six public taxonomies so downstream consumers (auditors, coverage matrices, traceability tools) can locate the artifact by control ID instead of by free-text search.

The frameworks this skill covers are all public domain or freely re-distributable from their authoring institutions (MITRE, NIST). This skill never copies framework text into the artifact -- it cites the framework's canonical identifier and links to the public source.

## When to Use This Skill

Use when:

- Authoring or revising a security or compliance skill and you want to add the optional `mitre_attack` / `atlas_techniques` / `d3fend_techniques` / `mitre_f3` / `nist_csf` / `nist_ai_rmf` frontmatter fields (see `AGENTS.md`, "Optional Security and Compliance Framework Mapping").
- A finding from a security review, pen test, or threat model needs to be assigned a control identifier so the user can route it (ticket category, dashboard, compliance report).
- A user asks "what's the ATT&CK technique for this?" or "which NIST CSF category does this belong to?"
- Building a coverage matrix that shows which Nexus-Hub skills cover which controls (the matrix consumes these tags).

**When NOT to use:**

- End-to-end threat modeling of a new system -- use [[architecture-design]] plus a dedicated threat model.
- Actually running a security audit -- use `/review security` or `/review pentest`.
- Generating evidence for a specific regulation (GDPR, SOC 2, ISO 27001) -- those have dedicated skills: [[gdpr-compliance]], [[soc2-compliance]], [[iso27001-compliance]].
- Picking between security skills for a task -- that is skill routing, not mapping.

## The Six Frameworks

| Framework | Scope | When it fits | Public source |
|---|---|---|---|
| MITRE ATT&CK | Adversarial techniques against enterprise IT (post-exploitation tactics + techniques). | The artifact concerns how an attacker behaves on a host or network. | https://attack.mitre.org/ |
| MITRE ATLAS | Adversarial techniques against AI/ML systems. | The artifact concerns adversarial behavior targeted at an ML model, training pipeline, or inference service. | https://atlas.mitre.org/ |
| MITRE F3 | Cyber-enabled financial fraud TTPs after initial compromise (Fight Fraud Framework v1.1, released 2026-04-09 by MITRE's Center for Threat-Informed Defense). ATT&CK stops at the foothold; F3 covers the fraud that follows. | The artifact concerns account takeover, mule networks, authorized-push-payment fraud, or other fraud TTPs that sit past initial access. | https://ctid.mitre.org/ |
| MITRE D3FEND | Defensive countermeasures, organized as a knowledge graph of "Detect / Isolate / Deceive / Evict / Restore / Harden / Model" actions. | The artifact concerns what defenders do (detection logic, hardening, response). | https://d3fend.mitre.org/ |
| NIST CSF | Five high-level functions (ID / PR / DE / RS / RC) decomposed into categories and subcategories. | The artifact is a control or capability framed in defender language, especially in a US-federal-regulated context. | https://www.nist.gov/cyberframework |
| NIST AI RMF | AI-specific Govern / Map / Measure / Manage functions and subcategories. | The artifact concerns an AI system's risk posture or governance. | https://www.nist.gov/itl/ai-risk-management-framework |

ATT&CK and D3FEND are paired: every defensive countermeasure in D3FEND maps to one or more ATT&CK techniques it counters. ATLAS is ATT&CK's sister catalog for ML systems. F3 is ATT&CK's sister catalog for cyber-enabled fraud. AI RMF is the governance lens NIST CSF lacks for AI-specific risk.

## Instructions

### 1. Identify which framework(s) fit the artifact

Ask three questions in order:

1. **Is this artifact about an attacker action, a defender action, governance, or cyber-enabled fraud?**
    - Attacker action (IT) -> ATT&CK.
    - Attacker action (ML) -> ATLAS.
    - Cyber-enabled financial fraud TTPs after initial compromise -> F3 (`mitre_f3`). ATT&CK stops at the foothold; F3 covers the fraud that follows.
    - Defender action -> D3FEND.
    - Governance / risk posture -> NIST CSF, or NIST AI RMF if the system is AI.
2. **Is the target an AI/ML system?**
    - Yes -> add ATLAS (for attacks) or AI RMF (for governance).
    - No -> stick with ATT&CK / D3FEND / CSF.
3. **Does the artifact span attack + defense?**
    - Yes -> map both. A "hunting credential dumping" skill maps to ATT&CK T1003 (attack) AND D3FEND D3-PA (defense).

Most security skills will carry 2-3 mappings, not 1. Compliance skills lean toward CSF + (for AI) AI RMF. Detection skills lean toward ATT&CK + D3FEND.

### 2. Find the right identifier in each framework

For each framework, the ID is the row-level identifier in the public catalog:

- **ATT&CK**: `T<NNNN>` for techniques (e.g., `T1071` for "Application Layer Protocol") or `T<NNNN>.<NN>` for sub-techniques (e.g., `T1003.001` for "LSASS Memory"). Find via https://attack.mitre.org/techniques/.
- **ATLAS**: `AML.T<NNNN>` (e.g., `AML.T0047` for "ML-Enabled Product or Service Reconnaissance"). Find via https://atlas.mitre.org/matrices/ATLAS.
- **F3**: `F<NNNN>` or `F<NNNN>.<NNN>` (e.g., `F1005.006`, `F1010`). Find via MITRE CTID's Fight Fraud Framework; v1.1 was released 2026-04-09.
- **D3FEND**: `D3-<CC>` two-to-four-letter codes (e.g., `D3-NTA` for "Network Traffic Analysis", `D3-PA` for "Process Analysis"). Find via https://d3fend.mitre.org/.
- **NIST CSF**: `<FN>.<CC>` where `FN` is one of `ID / PR / DE / RS / RC` and `CC` is the category (e.g., `DE.CM` for "Security Continuous Monitoring"). Find via the CSF reference at the NIST site.
- **NIST AI RMF**: `<FUNCTION>-<N.N>` (e.g., `MEASURE-2.6` for "AI system is evaluated regularly for safety risks"). Find via the AI RMF playbook.

When unsure between a parent technique and a sub-technique, prefer the most specific one that still describes the artifact accurately. For ATT&CK, `T1003.001` is preferred over `T1003` if the artifact is specifically about LSASS.

### 3. Record the mapping in the skill

For a Nexus-Hub skill, add the optional frontmatter fields per `AGENTS.md` ("Optional Security and Compliance Framework Mapping"):

```yaml
---
name: hunting-credential-dumping
description: <pushy description>
summary_l0: "<one-line>"
overview_l1: "<paragraph>"
mitre_attack: [T1003.001]
d3fend_techniques: [D3-PA, D3-PSA]
nist_csf: [DE.CM, DE.AE]
---
```

Use bracketed list syntax even for a single ID (`[T1071]`), not bare string, so the schema is consistent.

Then ship a `references/standards.md` documenting each mapping. The reference file's job is to be readable on its own: for each ID, give the framework name, the short title from the framework, why this skill maps to it, and a link to the public source. See the worked example below.

### 4. Worked example

Skill: `analyzing-network-traffic-of-malware`

| Field | Value | Why |
|---|---|---|
| `mitre_attack` | `[T1071]` | The skill analyzes network traffic that malware uses as a command-and-control channel -- ATT&CK calls this "Application Layer Protocol". |
| `atlas_techniques` | `[AML.T0047]` | When applied to ML-enabled detection products, the same traffic-analysis lens covers ATLAS "ML-Enabled Product or Service Reconnaissance". |
| `d3fend_techniques` | `[D3-NTA]` | The defender activity the skill teaches is D3FEND "Network Traffic Analysis". |
| `nist_csf` | `[DE.CM]` | The skill enables continuous monitoring for malicious activity -- NIST CSF "Detect / Continuous Monitoring" category. |
| `nist_ai_rmf` | `[MEASURE-2.6]` | If the analysis is part of an AI system's safety evaluation, AI RMF measure 2.6 (regular safety evaluation) applies. |

The `references/standards.md` companion would list each ID, the framework's own short title for it, the rationale ("this skill teaches X, which the framework defines as Y"), and a deep link.

### 5. Verify the mapping

Before finalizing, check three things:

1. **Each ID resolves on the public site.** Open the linked URL; the ID must exist in the current version of the framework.
2. **The mapping is defensible in one sentence.** If you cannot say "this skill teaches X, which ATT&CK calls T1003.001 because LSASS dumping is the operation involved", drop the mapping.
3. **The reference file does not copy framework prose.** Quote IDs and short titles only; long descriptions belong on the public site (Reverse-Engineering Attribution Rule).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Tagging is busywork -- the body of the skill already explains what it does" | Free-text descriptions cannot be queried by control ID. An auditor asking "which Nexus-Hub skills cover ATT&CK T1003?" cannot grep the body. The optional tags give that auditor a one-line answer and feed the coverage matrix generator. |
| "I'll map it to one framework and skip the others to keep frontmatter small" | The Tier-1 cost of these optional fields is negligible (a few tokens per skill), and the frameworks cover different lenses. A skill that only carries an ATT&CK tag is invisible to a defender doing a D3FEND coverage review. Map the lenses that apply, not just the easiest one. |
| "I'll pick a parent technique because the sub-technique might be wrong" | Picking the parent when the sub-technique is correct hides specificity. If the skill is specifically about LSASS dumping, `T1003.001` is right and `T1003` is too broad. If you genuinely cannot tell, ask the user; do not silently round up. |
| "I'll copy the framework's description into the skill body so the user does not need to click out" | The frameworks are revised over time; copies go stale. Quote the ID, the short title, and the public URL -- let the public source remain authoritative. (Reverse-Engineering Attribution Rule.) |
| "ATLAS and AI RMF only apply to LLM apps -- skip them for traditional ML" | ATLAS covers all ML systems including classical models. AI RMF covers any AI system including pre-LLM. The "AI" gate is broader than the agent's first instinct. |

## Verification

- [ ] Every ID added to the skill's frontmatter exists on the framework's current public site (open the URL, see the ID).
- [ ] The skill's `references/standards.md` exists and lists every ID with framework name, short title, rationale, and a deep URL.
- [ ] No long passages of framework text are copied into the skill or its references -- only IDs, short titles, and rationale in the agent's own words.
- [ ] The skill body still teaches the agent what to do; the mapping fields do not replace `Common Rationalizations` or `Verification` sections.
- [ ] When the skill is rerun through `scripts/validate_skills.py`, the optional fields produce no errors and no orphan-bundle warnings (`references/standards.md` is referenced from `SKILL.md`).

## Related Skills

- [[nist-ai-rmf]] -- implements the AI RMF directly; this skill is the cross-cutting mapper, not the implementer.
- [[traceability-matrix-generator]] -- requirement-to-code traceability; the framework tags extend that idea to security-control-to-skill traceability.
- [[security-review]] -- produces findings that can be tagged with this skill's framework IDs.
- [[ai-agent-governance]] -- uses AI RMF identifiers; mapping fields here feed its coverage view.
- [[soc2-compliance]] / [[iso27001-compliance]] / [[gdpr-compliance]] / [[pci-dss-compliance]] -- regulation-specific implementations; this skill helps them carry the right CSF / AI RMF tags.
