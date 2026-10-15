# Framework Standards Reference

Framework mapping for the `prompt-injection-defense` skill. The section below gives the framework identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source. MITRE ATLAS is the primary taxonomy because it catalogs the adversarial machine-learning technique this skill defends against, which ATT&CK Enterprise does not cover. D3FEND is intentionally not mapped: at the time of writing it has no countermeasure technique that precisely names defense against LLM prompt injection, and asserting a loose match would overclaim the coverage this skill provides.

## ATLAS AML.T0051 - LLM Prompt Injection

- Framework: MITRE ATLAS, Initial Access / Execution tactics for ML-enabled systems.
- Short title: "LLM Prompt Injection".
- Rationale: this skill is the defender's posture against direct and indirect LLM prompt injection (AML.T0051, including its direct and indirect sub-paths). Instruction-origin discipline and untrusted-content fencing directly counter the technique by denying externally-sourced text the ability to override the model's intended instructions; tool-output skepticism and the indirect-injection recognition cues counter the indirect sub-path where the directive is planted in content the model later reads.
- Source: https://atlas.mitre.org/techniques/AML.T0051

---

---

## OWASP Top 10 for Agentic Applications (2026)

Identifiers verified 2026-09-07 against the OWASP source. The full ten-entry set with official titles lives in `catalog/skills/security/security-framework-mapping/references/standards.md`; only the identifiers this skill is tagged with are explained below.

### ASI01 -- Agent Goal Hijack

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: The skill's whole posture is instruction-origin discipline: instructions come only from the user and the system, and everything read while working (a fetched page, a file, a tool result, another agent's handoff) is untrusted data rather than a principal that can issue commands. A goal hijack is precisely an injected instruction being obeyed as if it came from a principal, so this discipline is the direct control.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

---

## Attribution

The short title above is quoted from the framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. The ATLAS taxonomy is maintained by MITRE Corporation.
