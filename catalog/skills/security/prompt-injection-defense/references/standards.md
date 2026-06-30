# Framework Standards Reference

Framework mapping for the `prompt-injection-defense` skill. The section below gives the framework identifier, the framework's own short title (cited, not paraphrased), the rationale that ties this skill to the ID, and a deep link to the public source. MITRE ATLAS is the primary taxonomy because it catalogs the adversarial machine-learning technique this skill defends against, which ATT&CK Enterprise does not cover. D3FEND is intentionally not mapped: at the time of writing it has no countermeasure technique that precisely names defense against LLM prompt injection, and asserting a loose match would overclaim the coverage this skill provides.

## ATLAS AML.T0051 - LLM Prompt Injection

- Framework: MITRE ATLAS, Initial Access / Execution tactics for ML-enabled systems.
- Short title: "LLM Prompt Injection".
- Rationale: this skill is the defender's posture against direct and indirect LLM prompt injection (AML.T0051, including its direct and indirect sub-paths). Instruction-origin discipline and untrusted-content fencing directly counter the technique by denying externally-sourced text the ability to override the model's intended instructions; tool-output skepticism and the indirect-injection recognition cues counter the indirect sub-path where the directive is planted in content the model later reads.
- Source: https://atlas.mitre.org/techniques/AML.T0051

---

## Attribution

The short title above is quoted from the framework's public catalog; full prose belongs at the public source URL. Nexus-Hub does not redistribute framework text. The ATLAS taxonomy is maintained by MITRE Corporation.
