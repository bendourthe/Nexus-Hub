# Standards Mapping -- label-gated-agent-pipelines

Framework identifiers this skill is tagged with in its `SKILL.md` frontmatter, with the control the skill body actually teaches for each. Short titles are quoted from the framework's public catalog; full prose belongs at the source URL.

---

## OWASP Top 10 for Agentic Applications (2026)

Identifiers verified 2026-09-07 against the OWASP source. The full ten-entry set with official titles lives in `catalog/skills/security/security-framework-mapping/references/standards.md`; only the identifiers this skill is tagged with are explained below.

### ASI07 -- Insecure Inter-Agent Communication

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: Each stage declares a safe-outputs contract up front, so what one stage hands the next is a declared, bounded artifact rather than free text a later stage interprets as instruction. That is the inter-stage communication boundary.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

### ASI09 -- Human-Agent Trust Exploitation

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: A stage runs only when a maintainer deliberately applies that stage's label, so the agent never self-advances. The pattern exists because an agent that advances itself is trading on trust the human never granted for that step.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
