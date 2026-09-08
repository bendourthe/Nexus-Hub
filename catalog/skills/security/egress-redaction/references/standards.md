# Standards Mapping -- egress-redaction

Framework identifiers this skill is tagged with in its `SKILL.md` frontmatter, with the control the skill body actually teaches for each. Short titles are quoted from the framework's public catalog; full prose belongs at the source URL.

---

## OWASP Top 10 for Agentic Applications (2026)

Identifiers verified 2026-09-07 against the OWASP source. The full ten-entry set with official titles lives in `catalog/skills/security/security-framework-mapping/references/standards.md`; only the identifiers this skill is tagged with are explained below.

### ASI03 -- Identity & Privilege Abuse

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: The identifier's own framing is that leaked credentials let agents operate far beyond their intended scope. This skill detects sensitive data (credentials among the named categories) and applies a typed block, redact, hash, or pass action before any artifact crosses a trust boundary, which is the control on the leak that enables the abuse.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
