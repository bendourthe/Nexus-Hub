# Standards Mapping -- loop-engineering

Framework identifiers this skill is tagged with in its `SKILL.md` frontmatter, with the control the skill body actually teaches for each. Short titles are quoted from the framework's public catalog; full prose belongs at the source URL.

---

## OWASP Top 10 for Agentic Applications (2026)

Identifiers verified 2026-09-07 against the OWASP source. The full ten-entry set with official titles lives in `catalog/skills/security/security-framework-mapping/references/standards.md`; only the identifiers this skill is tagged with are explained below.

### ASI10 -- Rogue Agents

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: The Reward Hacking section and the loopmaxxing anti-patterns address an agent optimizing a proxy for its objective and continuing under its own direction; the mandatory iteration cap, the command-derived exit condition, and the requirement that the maker never self-certifies the exit are the containment. Note the deliberate boundary: cascading failures (ASI08) are owned by agent-orchestration-primitives per references/failure-mode-ownership.md, so this skill is not tagged ASI08.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
