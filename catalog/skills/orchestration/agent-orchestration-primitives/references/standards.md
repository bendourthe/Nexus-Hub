# Standards Mapping -- agent-orchestration-primitives

Framework identifiers this skill is tagged with in its `SKILL.md` frontmatter, with the control the skill body actually teaches for each. Short titles are quoted from the framework's public catalog; full prose belongs at the source URL.

---

## OWASP Top 10 for Agentic Applications (2026)

Identifiers verified 2026-09-07 against the OWASP source. The full ten-entry set with official titles lives in `catalog/skills/security/security-framework-mapping/references/standards.md`; only the identifiers this skill is tagged with are explained below.

### ASI07 -- Insecure Inter-Agent Communication

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: The graph readiness checklist requires inputs and outputs between nodes to use explicit contracts or schemas, so a handoff can be validated instead of assumed, and the agent-teams envelope is explicit about peers holding shared state.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

### ASI08 -- Cascading Failures

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: Step 5 names cascading error as a failure mode in its own right: every downstream agent inherits an unverified premise and multiplies the error. The response is to verify the upstream result BEFORE fanning out on it and to version shared state so a corrupted revision can be identified and rolled back.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
