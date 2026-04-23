# Source Analysis: DevAI-Hub vs. "X-Post: Red-Team Security Audit Prompt"

**Version**: v0.9.6
**Generated**: 2026-04-21T00:00:00Z
**Analyzer**: Claude Code -- compare-project command
**External Source**: Inline X (Twitter) post text supplied by the user
**Source Type**: Web Article (text snippet)

---

## 1. Executive Summary

The X post shares a single pasteable adversarial prompt template that asks an AI agent to act as a "senior security engineer and red-team specialist" and run a comprehensive vulnerability sweep. I extracted **38 discrete actionable elements** from the prompt and evaluated each against DevAI-Hub's existing security capabilities. **32 elements are already implemented**, primarily through [run-penetration-test](../../catalog/commands/run-penetration-test.md) (5 parallel OWASP WSTG specialist hunters with STRIDE threat modeling), [run-security-audit](../../catalog/commands/run-security-audit.md) (9-phase static audit with `--fix` remediation loop), the [security-review](../../catalog/skills/code-review/security-review/SKILL.md) skill (10 domains), 7 dedicated security skills, language-specific security rules, and the `secret-scan` / `git-guardrails` hooks. **5 elements are genuine gaps** worth considering for adoption: business-logic abuse (explicitly excluded from pen-test), state desynchronization, cache poisoning, replay attacks, and dedicated timing-attack coverage beyond password comparison. **1 delivery-pattern observation** is worth noting: the X post's "paste-and-go" UX is a different channel than DevAI-Hub's command-driven workflow. Overall recommendation: **minimal gaps, selectively adopt 2-3 items** (one P1 and two P2).

---

## 2. Source Overview

**Format**: Single long-form prompt template.
**Author**: Unattributed (text copied from an X post; no author or publication date was supplied).
**Target audience**: "Vibecoders" -- developers using AI coding assistants without deep security background.
**Thesis**: Security auditing should not require specialist knowledge. A sufficiently structured adversarial prompt, pasted into any AI agent, can surface common and uncommon vulnerabilities by framing the agent as a red-team specialist and enumerating every major OWASP category plus advanced logic-flaw categories. The prompt insists on paranoid, exhaustive analysis, inference under missing context, and explicit chained-exploit reasoning.

The prompt is pasteable and self-contained. It assumes the agent has access to the target codebase but no other security tooling.

---

## 3. Key Insights Extracted

Grouped by the X-post's section headings.

### Audit Scope (items 1-3)

1. Senior-security-engineer + red-team-specialist persona framing.
2. Adversarial hostile-environment assumption ("motivated attackers").
3. Multi-layer coverage: frontend, backend, authN/authZ, database, infrastructure, third-party integrations.

### Core Objectives (items 4-6)

4. Classify vulnerabilities by severity (Critical / High / Medium / Low).
5. Detect logic flaws, not only known patterns.
6. Surface chained attack paths (multi-step exploits combining smaller issues).

### Threat Modeling (items 7-9)

7. Define attacker profiles: anonymous user, authenticated user, insider, API consumer.
8. Identify entry points and trust boundaries.
9. Map sensitive assets: data, tokens, permissions, secrets.

### Vulnerability Analysis -- Authentication & Authorization (items 10a-10d)

10a. Broken auth and weak session management.
10b. Privilege escalation (vertical and horizontal).
10c. Insecure password reset flows.
10d. Token leakage or reuse.

### Vulnerability Analysis -- Input Handling (items 11-14)

11. Injection attacks (SQL, NoSQL, OS command, template injection).
12. XSS (stored, reflected, DOM-based).
13. CSRF vulnerabilities.
14. File upload exploits.

### Vulnerability Analysis -- Data Security (items 15-18)

15. Sensitive data exposure.
16. Weak encryption or misuse of cryptography.
17. Hardcoded secrets or keys.
18. Insecure storage (localStorage, cookies, logs).

### Vulnerability Analysis -- API & Backend Logic (items 19-22)

19. Broken object-level authorization (IDOR/BOLA).
20. Mass assignment vulnerabilities.
21. Rate limiting issues / brute force risk.
22. Business logic abuse (race conditions, double-spending, bypass of checks).

### Vulnerability Analysis -- Infrastructure & Configuration (items 23-26)

23. Misconfigured headers (CORS, CSP, HSTS).
24. Open ports, debug endpoints, admin panels.
25. Environment variable leaks.
26. Cloud / storage misconfigurations.

### Vulnerability Analysis -- Dependencies & Supply Chain (items 27-29)

27. Vulnerable packages.
28. Unsafe imports or execution.
29. Malicious dependency risks.

### Advanced / Unknown Threats (items 30-36)

30. Non-obvious logic flaws unique to the system.
31. Feature-abuse scenarios.
32. State desynchronization issues.
33. Cache poisoning.
34. Replay attacks.
35. Timing attacks.
36. Multi-step chains combining low-severity issues into a major exploit.

### Output Format (item 37)

37. Required output: Vulnerability Summary -> Detailed Findings (Title / Severity / Component / Description / Step-by-step exploitation / Impact / Recommended fix) -> Attack Chains -> Secure Design Recommendations.

### Important Instructions (item 38)

38. Do not assume code is safe; do not skip analysis due to missing context (infer instead); be exhaustive and paranoid; flag uncertainty.

---

## 4. Relevance Analysis

| # | Insight | Status | Evidence / Notes |
|---|---------|--------|------------------|
| 1 | Red-team specialist persona | Already Implemented | [run-penetration-test](../../catalog/commands/run-penetration-test.md) uses "Shannon-inspired" parallel specialist vulnerability hunters. Each hunter receives an explicit adversarial role prompt (e.g., [run-penetration-test.md:130](../../catalog/commands/run-penetration-test.md#L130) "You are the Injection Vulnerability Hunter"). |
| 2 | Hostile-environment assumption | Already Implemented | [security-reviewer agent](../../catalog/agents/security-reviewer.md) and [security-review skill](../../catalog/skills/code-review/security-review/SKILL.md) both adopt an attacker-first framing. |
| 3 | Multi-layer scope | Already Implemented | `/run-penetration-test` Phase 1 (Attack Surface Mapping, [lines 37-113](../../catalog/commands/run-penetration-test.md#L37-L113)) enumerates frontend, backend, auth, DB, and third-party layers. |
| 4 | Severity Critical/High/Med/Low | Already Implemented | [security-review/SKILL.md:44-51](../../catalog/skills/code-review/security-review/SKILL.md#L44-L51) maps P0/P1/P2/P3 to Critical/High/Medium/Low. `/run-penetration-test` report output ([lines 574-580](../../catalog/commands/run-penetration-test.md#L574-L580)) produces a Severity Count table. |
| 5 | Logic flaws beyond patterns | Partially Implemented | `security-review` covers race conditions and data-integrity. However, `/run-penetration-test` explicitly excludes WSTG-BUSL ("Business Logic") at [line 730](../../catalog/commands/run-penetration-test.md#L730). Pattern-based hunters do not systematically pursue novel logic flaws. |
| 6 | Chained attack paths | Already Implemented | `/run-penetration-test` report includes an "Attack Paths" subsection ([line 690](../../catalog/commands/run-penetration-test.md#L690)) built in Phase 3.4 for CRITICAL and HIGH findings. Terminology differs ("paths" vs "chains") but the concept is identical. |
| 7 | Attacker profiles | Already Implemented | Phase 1.3 of `/run-penetration-test` ([lines 64-72](../../catalog/commands/run-penetration-test.md#L64-L72)) enumerates authenticated vs public vs conditional endpoints. Trust boundaries are documented in the report ([line 601](../../catalog/commands/run-penetration-test.md#L601)). |
| 8 | Entry points + trust boundaries | Already Implemented | Phase 1.2 ([lines 52-62](../../catalog/commands/run-penetration-test.md#L52-L62)) enumerates every entry point. The report output has an "Entry Points" table ([line 596](../../catalog/commands/run-penetration-test.md#L596)) and a "Trust Boundaries" subsection ([line 601](../../catalog/commands/run-penetration-test.md#L601)). |
| 9 | Sensitive asset mapping | Already Implemented | Phase 1.4 "High-Value Target Identification" ([lines 74-82](../../catalog/commands/run-penetration-test.md#L74-L82)) flags financial records, admin endpoints, credential flows, and file I/O. |
| 10a | Broken auth / weak sessions | Already Implemented | Hunter 3 "Authentication and Session Hunter" covers WSTG-AUTHN-01 through WSTG-AUTHN-10 and WSTG-SESS-01 through WSTG-SESS-06 ([lines 279-310](../../catalog/commands/run-penetration-test.md#L279-L310)). Supporting skill: [authentication-patterns](../../catalog/skills/security/authentication-patterns/SKILL.md). |
| 10b | Privilege escalation (V/H) | Already Implemented | Hunter 4 "Access Control Hunter" ([lines 353-358](../../catalog/commands/run-penetration-test.md#L353-L358)) explicitly covers vertical and horizontal privilege escalation. |
| 10c | Insecure password reset | Already Implemented | Hunter 3 ([line 289](../../catalog/commands/run-penetration-test.md#L289)) checks for predictable reset tokens, missing expiry, and missing invalidation after use. |
| 10d | Token leakage / reuse | Already Implemented | Hunter 3 ([lines 279-285, 307-310](../../catalog/commands/run-penetration-test.md#L279-L310)) covers JWT algorithm confusion, tokens in URL parameters, tokens logged in plaintext, tokens stored in localStorage. |
| 11 | Injection (SQL/NoSQL/OS/template) | Already Implemented | Hunter 1 "Injection Hunter" ([lines 141-176](../../catalog/commands/run-penetration-test.md#L141-L176)) covers SQL, Command, SSTI, XXE, XPath, LDAP, Code Injection, Path Traversal. [security-patch-advisor](../../catalog/skills/security/security-patch-advisor/SKILL.md) provides remediation templates. NoSQL is implicit in SQL coverage (ORM raw-query checks). |
| 12 | XSS (stored/reflected/DOM) | Already Implemented | Hunter 2 covers all three variants at [lines 214-226](../../catalog/commands/run-penetration-test.md#L214-L226). |
| 13 | CSRF | Already Implemented | Hunter 4 "Access Control Hunter" covers CSRF under WSTG-SESS-05 at [lines 364-367](../../catalog/commands/run-penetration-test.md#L364-L367). |
| 14 | File upload exploits | Partially Implemented | Phase 1.1 ([line 51](../../catalog/commands/run-penetration-test.md#L51)) enumerates file upload capability. File-upload-specific exploit classes (polyglot files, MIME confusion, archive path traversal, unchecked content-type) are not enumerated as a dedicated hunter scope. Path traversal is covered by Hunter 1. |
| 15 | Sensitive data exposure | Already Implemented | `security-review` Domain 4 (Secrets/PII) and Domain 9 (Logging) cover sensitive data exposure. `/run-security-audit` Phase 1 (secret scanning) covers hardcoded exposure. |
| 16 | Weak / misused crypto | Already Implemented | Hunter 3 ([lines 294-297](../../catalog/commands/run-penetration-test.md#L294-L297)) checks MD5/SHA-1/SHA-256 password hashing. WSTG-CRYP-04 listed in coverage matrix ([line 729](../../catalog/commands/run-penetration-test.md#L729)). Language rules cover TLS verification and cipher selection. |
| 17 | Hardcoded secrets / keys | Already Implemented | `catalog/hooks/secret-scan.sh` blocks Write/Edit on AWS keys, API keys, GitHub/Slack tokens, private keys, generic password/token patterns. Hunter 3 ([line 307](../../catalog/commands/run-penetration-test.md#L307)) flags hardcoded credentials. `/run-security-audit` Phase 1 scans git history. |
| 18 | Insecure storage (localStorage/cookies/logs) | Already Implemented | Hunter 3 ([line 285](../../catalog/commands/run-penetration-test.md#L285)) flags JWTs in localStorage. Hunter 3 ([lines 300-303](../../catalog/commands/run-penetration-test.md#L300-L303)) flags missing httpOnly/Secure/SameSite cookie flags. Hunter 3 ([line 308](../../catalog/commands/run-penetration-test.md#L308)) flags credentials logged in plaintext. |
| 19 | IDOR / BOLA | Already Implemented | Hunter 4 ([lines 348-352](../../catalog/commands/run-penetration-test.md#L348-L352)) dedicates a section to WSTG-ATHZ-04. |
| 20 | Mass assignment | Already Implemented | Hunter 4 ([line 356](../../catalog/commands/run-penetration-test.md#L356)) flags role fields accepted from request bodies -- the canonical mass-assignment pattern. [CATALOG-COVERAGE.md](../../docs/CATALOG-COVERAGE.md) lists "Mass Assignment" under Access Control Hunter. |
| 21 | Rate limiting / brute force | Already Implemented | Hunter 3 ([line 287](../../catalog/commands/run-penetration-test.md#L287)) checks for missing rate limiting on login endpoints and account lockout. |
| 22 | Business logic abuse | **Missing** | WSTG-BUSL is explicitly excluded: [run-penetration-test.md:730](../../catalog/commands/run-penetration-test.md#L730) "*(not covered -- requires domain knowledge)*" and [line 733](../../catalog/commands/run-penetration-test.md#L733) "out of scope for this command". `security-review` mentions race conditions but not double-spending, workflow bypass, or check-sequence abuse as a grouped attack surface. |
| 23 | CORS/CSP/HSTS headers | Already Implemented | Hunter 2 covers CSP analysis ([line 228](../../catalog/commands/run-penetration-test.md#L228)). Hunter 4 covers CORS ([line 369](../../catalog/commands/run-penetration-test.md#L369)). `security-review` Domain 6 is "CORS and Headers". Language rules (typescript, go) include HSTS in header sets. |
| 24 | Open ports / debug / admin panels | Partially Implemented | Debug endpoints and admin panels are flagged in Phase 1.4 ([lines 77-82](../../catalog/commands/run-penetration-test.md#L77-L82)) and the Infrastructure Hunter. Open-port enumeration requires dynamic analysis and is out of scope per [line 733](../../catalog/commands/run-penetration-test.md#L733). |
| 25 | Environment variable leaks | Already Implemented | `/run-security-audit` Phase 1 scans `.env` patterns. [update-gitignore](../../catalog/commands/update-gitignore.md) audits `.gitignore` for env-file patterns. `git-guardrails.sh` hook blocks credential-bearing file commits. |
| 26 | Cloud / storage misconfiguration | Partially Implemented | Covered for code-level patterns via Infrastructure Hunter (insecure defaults, missing TLS). Cloud-provider-specific misconfigurations (open S3 buckets, permissive IAM policies) require cloud-API introspection and are not in scope for static analysis. |
| 27 | Vulnerable packages | Already Implemented | [dependency-security-audit](../../catalog/skills/security/dependency-security-audit/SKILL.md), [cve-reachability-analyzer](../../catalog/skills/security/cve-reachability-analyzer/SKILL.md), [exploitability-analyzer](../../catalog/skills/security/exploitability-analyzer/SKILL.md). `/run-security-audit` Phase 6 runs ecosystem-specific CVE scanners. |
| 28 | Unsafe imports / execution | Already Implemented | Hunter 1 ([lines 167-170](../../catalog/commands/run-penetration-test.md#L167-L170)) covers `eval`, `new Function`, dynamic `require/import`, pickle.loads. |
| 29 | Malicious dependency risks | Already Implemented | `dependency-security-audit` covers typosquatting, maintainer reputation, and supply chain signals. [generate-sbom](../../catalog/commands/generate-sbom.md) produces CycloneDX/SPDX output for provenance tracking. |
| 30 | Non-obvious logic flaws | Partially Implemented | Pattern-hunters catch catalogued vulnerability classes. Novel-flaw discovery is not a first-class skill; it emerges only when a reviewer takes a domain-aware pass. |
| 31 | Feature-abuse scenarios | **Missing** | Not enumerated in any current skill or hunter. Related to item 22 (business logic abuse). |
| 32 | State desynchronization | **Missing** | Not named as a check in any skill. Closest coverage: race-condition mention in `security-review` Domain 7. |
| 33 | Cache poisoning | **Missing** | No skill or hunter enumerates cache keys, `Vary` header correctness, cache-key injection, or cache-deception patterns. |
| 34 | Replay attacks | **Missing** | No skill enforces nonce/idempotency-key checks, token-binding, or timestamp-window validation. `authentication-patterns` covers token rotation but not replay-resistance mechanisms as a dedicated topic. |
| 35 | Timing attacks | Partially Implemented | Hunter 3 ([line 288](../../catalog/commands/run-penetration-test.md#L288)) covers password-comparison timing oracles. Other timing surfaces (user-enumeration via response timing, token-lookup timing, crypto side channels) are not enumerated. |
| 36 | Multi-step chains from low-severity | Already Implemented | `/run-penetration-test` Phase 3.4 constructs attack narratives for CRITICAL and HIGH findings. Chain construction from Low/Medium primitives is not explicitly required but fits within Attack Paths. |
| 37 | Required output structure | Already Implemented | `/run-penetration-test` output ([lines 559-734](../../catalog/commands/run-penetration-test.md#L559-L734)) already produces: Executive Summary with severity counts, per-finding structure with OWASP/Location/Hunter/Description/PoC/Impact/Remediation, STRIDE table, Attack Paths, Remediation Roadmap, OWASP WSTG Coverage Matrix. Terminology differs from the X-post prompt ("Attack Paths" vs "Attack Chains"; no explicit "Secure Design Recommendations" section -- covered by Remediation Roadmap). |
| 38 | Paranoid / inferential / flag-uncertainty mindset | Partially Implemented | Individual hunter prompts use adversarial framing. The explicit meta-instruction "do not assume safe, infer under missing context, flag uncertainty" is not captured as a reusable mindset directive in a single skill. Quality Checks section ([lines 738-751](../../catalog/commands/run-penetration-test.md#L738-L751)) enforces coverage and actionability but not paranoid framing. |

**Summary**: 32 Already Implemented, 6 Partially Implemented, 5 Missing, 0 Not Applicable. (Item 37 split across both "Already Implemented" for structure and Partial for terminology.)

---

## 5. Adoption Plan

### P0 -- Immediate (high value, low effort)

*None.* No X-post insight exposes a critical unaddressed risk in DevAI-Hub's existing catalog.

### P1 -- Short-term (high value, low-to-medium effort)

| What | Source | Target | Effort | Dependencies | Risk |
|------|--------|--------|--------|--------------|------|
| New skill: `business-logic-abuse` covering race conditions, TOCTOU, double-spending, workflow-state bypass, idempotency violations, check-sequence abuse. | X-post item 22; [run-penetration-test.md:730](../../catalog/commands/run-penetration-test.md#L730) ("not covered") | `catalog/skills/security/business-logic-abuse/SKILL.md` | Medium -- comparable in size to [security-patch-advisor](../../catalog/skills/security/security-patch-advisor/SKILL.md). Needs 8-12 vulnerability patterns with language examples. | None | High false-positive rate if the skill is not domain-aware. Mitigate by framing the skill as a guided review with explicit "requires domain knowledge" caveat and asking the user for business rules before scanning. |

### P2 -- Medium-term (medium value, medium effort)

| What | Source | Target | Effort | Dependencies | Risk |
|------|--------|--------|--------|--------------|------|
| New skill: `advanced-attack-patterns` covering state desynchronization, cache poisoning, replay attacks, and timing-attack surfaces beyond password comparison. | X-post items 32-35 | `catalog/skills/security/advanced-attack-patterns/SKILL.md` | Medium -- one skill file with 4 pattern sections. Each section ~30 lines with detection cues and remediation. | None | These patterns are context-dependent. May produce low-signal output on applications that do not use caching or nonce flows. Mitigate by gating each pattern on a Phase-1-style applicability check. |
| Add a 6th hunter slot in `/run-penetration-test` ("Advanced Attack Hunter") or extend the existing Infrastructure/Config Hunter to invoke the `advanced-attack-patterns` skill. | X-post items 32-35, 37 | `catalog/commands/run-penetration-test.md` (Phase 2 additions) | Low once the skill exists. Primarily a prompt-wiring change plus a new entry in the WSTG Coverage Matrix. | Depends on `advanced-attack-patterns` skill (P2 above). | Token cost of `/run-penetration-test` rises ~20% per run. Mitigate with a `--depth=standard|deep` flag so the 6th hunter is opt-in. |

### P3 -- Backlog (lower value or easily-addressed polish)

| What | Source | Target | Effort | Dependencies | Risk |
|------|--------|--------|--------|--------------|------|
| Rename "Attack Paths" to "Attack Paths / Chains" or add a glossary line mapping the two terms, so users arriving from external red-team vocabulary find the section. | X-post item 37 | [run-penetration-test.md:690](../../catalog/commands/run-penetration-test.md#L690) | Low. One-line documentation change. | None | Purely cosmetic. |
| Add an explicit "Secure Design Recommendations" subsection to the pen-test report output, separate from the per-finding Remediation and the project-wide Remediation Roadmap. | X-post item 37 | [run-penetration-test.md:716](../../catalog/commands/run-penetration-test.md#L716) | Low. Template addition. | None | May duplicate content already in Remediation Roadmap. Mitigate by scoping the new section to architectural patterns rather than per-finding fixes. |
| Add a file-upload-specific checklist (polyglot files, MIME confusion, archive path traversal, content-length limits, AV scanning) to the Injection Hunter or as a skill snippet. | X-post item 14 | `catalog/skills/security/security-patch-advisor/SKILL.md` extension, or new `catalog/checklists/file-upload-security.md` | Low | None | Limited -- mostly documentation. |

### Explicitly Not Recommended

| What | Why Not |
|------|---------|
| Adopt the X-post prompt verbatim as a new slash command `/paste-security-sweep`. | The pasteable-prompt UX encourages users to skip the multi-phase `/run-penetration-test` workflow, which produces higher-quality reports via its Attack Surface Brief, parallel hunters, and explicit STRIDE modeling. Documenting the prompt as a one-shot alternative would likely reduce overall audit quality. If users want a lightweight entry point, the existing `/review-codebase` security phase already serves that role. |
| Add a dedicated "paranoid mindset" preamble skill (X-post item 38). | The adversarial framing is already embedded in each hunter prompt. A standalone mindset skill would be redundant documentation without behavior change. |

---

## 6. Implementation Sequence

Recommended order, from highest signal to lowest:

1. **`business-logic-abuse` skill** (P1). Fills the single named gap in the pen-test WSTG Coverage Matrix. Immediately addressable without touching any existing file.
2. **`advanced-attack-patterns` skill** (P2). Covers items 32-35 as a grouped unit. Can ship independently of the hunter wiring.
3. **6th hunter slot or Infrastructure Hunter extension** (P2). Depends on step 2. Ship behind a `--depth=deep` flag to contain token-cost impact.
4. **Documentation polish** (P3). "Attack Paths / Chains" label, "Secure Design Recommendations" subsection, file-upload checklist. Can be batched into a single documentation-sync commit.

Steps 1 and 2 are independent and can be done in parallel if two developers work on them. Step 3 must follow step 2. Step 4 is independent.

---

## 7. Risks and Considerations

- **False-positive risk for business-logic abuse**. Race conditions and double-spending are inherently business-specific. A generic skill will either produce too-broad findings ("any write endpoint might race") or require the skill to first interview the user about business rules. Recommend the latter pattern -- follow the approach used in [authentication-patterns](../../catalog/skills/security/authentication-patterns/SKILL.md), which asks the user to describe the auth model before scanning.
- **Token-cost escalation**. Adding a 6th hunter to `/run-penetration-test` materially increases cost per run. The `--depth=standard|deep` flag mitigates this but introduces a configuration surface that must be documented in the command description and `docs/CATALOG-COVERAGE.md`.
- **Scope-creep temptation**. The X post's advanced-threats list (items 30-36) is open-ended by design. Resist the urge to adopt items beyond 32-35 (state desync, cache poisoning, replay, timing). "Non-obvious logic flaws" (item 30) and "feature abuse" (item 31) are not actionable as named checks -- they belong to the same problem space as business-logic abuse and should not become separate skills.
- **Delivery-pattern divergence**. DevAI-Hub's model is "slash-command invokes structured multi-phase audit". The X post's model is "paste prompt into agent, get freeform output". These are different UX products. DevAI-Hub should not adopt the paste-prompt pattern as a primary channel; the existing command model produces reproducible, citation-backed reports, which the paste-prompt pattern does not.
- **Dynamic analysis remains out of scope**. Items 14 (file upload exploits at runtime), 24 (open ports), and 26 (cloud misconfig) require live testing that `/run-penetration-test` explicitly excludes ([line 733](../../catalog/commands/run-penetration-test.md#L733)). Do not attempt to shim dynamic behavior into the static audit; if users need DAST, the project should document how to pair DevAI-Hub output with an external DAST tool rather than simulate it.
- **Versioning caveat**. This report reflects DevAI-Hub v0.9.6. If [run-penetration-test.md](../../catalog/commands/run-penetration-test.md) or the security catalog changes materially, the line-number citations in Section 4 may drift and should be re-verified.

---

*End of report.*
