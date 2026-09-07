# Framework Standards Reference

Framework mappings for the `ai-attack-patterns` skill. Each section gives the framework identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source. MITRE ATLAS is the primary taxonomy because it catalogs adversarial machine-learning techniques that ATT&CK Enterprise does not cover.

## ATLAS AML.T0051 - LLM Prompt Injection

- Framework: MITRE ATLAS, Initial Access / Execution tactics for ML-enabled systems.
- Short title: "LLM Prompt Injection".
- Rationale: Phases 2 and 3 of the skill are direct and indirect prompt injection -- supplying or planting text that overrides the model's intended instructions -- which is exactly the parent technique AML.T0051 (direct and indirect sub-paths).
- Source: https://atlas.mitre.org/techniques/AML.T0051

## ATLAS AML.T0054 - LLM Jailbreak

- Framework: MITRE ATLAS, Defense Evasion tactic for ML-enabled systems.
- Short title: "LLM Jailbreak".
- Rationale: Phase 4 measures the durability of safety and policy constraints by relocating the model outside its policy via roleplay, encoding, and constraint-stacking, which is the jailbreak technique AML.T0054.
- Source: https://atlas.mitre.org/techniques/AML.T0054

## ATLAS AML.T0020 - Poison Training Data

- Framework: MITRE ATLAS, Resource Development / Persistence tactic for ML-enabled systems.
- Short title: "Poison Training Data".
- Rationale: Phase 5 (RAG / knowledge-base poisoning) plants attacker-controlled content into the corpus a model retrieves from so that retrieval steers the answer; this is the data-poisoning class captured by AML.T0020 applied to the retrieval/knowledge layer rather than pretraining.
- Source: https://atlas.mitre.org/techniques/AML.T0020

## NIST AI RMF MEASURE-2.6 - AI System Trustworthy Characteristics Evaluation

- Framework: NIST AI Risk Management Framework, Measure function.
- Short title: "MEASURE 2.6".
- Rationale: the skill evaluates a deployed AI system for safety and security failure modes under adversarial input, which is the trustworthy-characteristics measurement activity MEASURE-2.6.
- Source: https://www.nist.gov/itl/ai-risk-management-framework

## NIST AI RMF MEASURE-2.7 - AI System Security and Resilience

- Framework: NIST AI Risk Management Framework, Measure function.
- Short title: "MEASURE 2.7".
- Rationale: red-teaming prompt injection, jailbreak, poisoning, and tool-abuse paths measures the security and resilience of the AI system against attack, which is the activity MEASURE-2.7 calls for.
- Source: https://www.nist.gov/itl/ai-risk-management-framework

---

---

## OWASP Top 10 for Agentic Applications (2026)

Identifiers verified 2026-09-07 against the OWASP source. The full ten-entry set with official titles lives in `catalog/skills/security/security-framework-mapping/references/standards.md`; only the identifiers this skill is tagged with are explained below.

### ASI01 -- Agent Goal Hijack

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: Covers direct and indirect prompt injection from the attacker's side under authorization, which is the offensive form of the same risk, and requires every finding to be translated into a concrete defense.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

### ASI02 -- Tool Misuse

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: Covers tool and function-call abuse in agentic systems as a named attack surface: bending a legitimate tool the agent already holds into an unintended effect.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

### ASI06 -- Memory & Context Poisoning

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: Covers RAG and knowledge-base poisoning, which is context poisoning through the retrieval path rather than through the prompt.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

---

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATLAS) and the National Institute of Standards and Technology (NIST AI RMF).
