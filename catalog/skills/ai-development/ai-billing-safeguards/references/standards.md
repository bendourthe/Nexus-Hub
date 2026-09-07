# Standards Mapping -- ai-billing-safeguards

Framework identifiers this skill is tagged with in its `SKILL.md` frontmatter, with the control the skill body actually teaches for each. Short titles are quoted from the framework's public catalog; full prose belongs at the source URL.

---

## OWASP Top 10 for Agentic Applications (2026)

Identifiers verified 2026-09-07 against the OWASP source. The full ten-entry set with official titles lives in `catalog/skills/security/security-framework-mapping/references/standards.md`; only the identifiers this skill is tagged with are explained below.

### ASI10 -- Rogue Agents

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: The skill's own framing is preventing runaway agents: hard session caps with automatic termination on breach, per-task limits to contain individual runaway subtasks, and clean rather than silent termination, for agents deployed without continuous human oversight. That is containment of self-directed action, measured in the dimension this skill owns.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
