# Standards Mapping -- agent-memory

Framework identifiers this skill is tagged with in its `SKILL.md` frontmatter, with the control the skill body actually teaches for each. Short titles are quoted from the framework's public catalog; full prose belongs at the source URL.

---

## OWASP Top 10 for Agentic Applications (2026)

Identifiers verified 2026-09-07 against the OWASP source. The full ten-entry set with official titles lives in `catalog/skills/security/security-framework-mapping/references/standards.md`; only the identifiers this skill is tagged with are explained below.

### ASI06 -- Memory & Context Poisoning

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: The store's append-only discipline is the control: every write names a source, mutations append to a changelog, and a superseded row is marked rather than deleted, so a poisoned fact can be located by provenance and the affected facts rolled back to the last good changelog index.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
