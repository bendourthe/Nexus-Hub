# Standards Mapping -- agent-access-policy

Framework identifiers this skill is tagged with in its `SKILL.md` frontmatter, with the control the skill body actually teaches for each. Short titles are quoted from the framework's public catalog; full prose belongs at the source URL.

---

## OWASP Top 10 for Agentic Applications (2026)

Identifiers verified 2026-09-07 against the OWASP source. The full ten-entry set with official titles lives in `catalog/skills/security/security-framework-mapping/references/standards.md`; only the identifiers this skill is tagged with are explained below.

### ASI02 -- Tool Misuse

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: Default-deny host command execution and typed dangerous-action approval gates constrain which tool calls an agent may make at all, which is the preventive control against a legitimate tool being turned to an unintended effect.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

### ASI03 -- Identity & Privilege Abuse

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: Least-privilege file access controls and the typed capability-grant broker scope what identity and authority an agent operates under, and the blast-radius section bounds what a commandeered agent can reach with the authority it has.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
