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

## Attribution

These short titles are quoted from each framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. Framework taxonomies are maintained by MITRE Corporation (ATLAS) and the National Institute of Standards and Technology (NIST AI RMF).
