---
name: security-review
description: Identify security vulnerabilities across 10 domains including OWASP Top 10, race conditions, supply chain risks, and compliance gaps. Use for security audits, penetration test preparation, vulnerability assessment, or as Phase 3 of comprehensive code review.
summary_l0: "Identify security vulnerabilities across OWASP Top 10 and supply chain domains"
overview_l1: "This skill identifies security vulnerabilities and risks across 10 security domains, serving as Phase 3 of the 6-phase code review methodology. Use it when conducting security audits, identifying vulnerabilities across all attack surfaces, checking OWASP Top 10 compliance, assessing supply chain security, analyzing race conditions and concurrency risks, preparing for penetration testing, or meeting security compliance requirements. Key capabilities include OWASP Top 10 vulnerability scanning, injection attack detection, authentication and authorization review, sensitive data exposure analysis, race condition and concurrency risk assessment, supply chain dependency auditing, and compliance gap identification. The expected output is a security findings report with categorized vulnerabilities, severity ratings, exploitation scenarios, and remediation recommendations. Trigger phrases: security review, vulnerability scan, OWASP, security audit, penetration test prep, CVE check, security assessment, race condition."
---

# Code Review - Security Review

Identify security vulnerabilities and risks across 10 security domains. This skill is **Phase 3** of the 6-phase code review methodology.

## When to Use This Skill

Use this skill when you need to:

- Conduct security audit
- Identify vulnerabilities across all attack surfaces
- Check OWASP Top 10 compliance
- Assess supply chain security
- Analyze race conditions and concurrency risks
- Prepare for penetration testing
- Meet security compliance requirements

**Trigger phrases**: "security review", "vulnerability scan", "OWASP", "security audit", "penetration test prep", "CVE check", "security assessment", "race condition"

## What This Skill Does

### OWASP Top 10 (2021) Mapping

| ID | Vulnerability | Covered By Domain |
|----|---------------|-------------------|
| A01 | Broken Access Control | Domain 2: AuthN/AuthZ |
| A02 | Cryptographic Failures | Domain 8: Cryptography |
| A03 | Injection | Domain 1: Input/Output Safety |
| A04 | Insecure Design | Domain 2 + Domain 10 |
| A05 | Security Misconfiguration | Domain 6: CORS & Headers |
| A06 | Vulnerable Components | Domain 5: Supply Chain |
| A07 | Authentication Failures | Domain 2 + Domain 3: JWT |
| A08 | Data Integrity Failures | Domain 10: Data Integrity |
| A09 | Logging Failures | Domain 4: Secrets/PII |
| A10 | SSRF | Domain 1: Input/Output Safety |

### Severity Classification

| Level | Alias | Description |
|-------|-------|-------------|
| **P0** | CRITICAL | Immediate exploit risk, data breach potential |
| **P1** | HIGH | Significant vulnerability requiring urgent fix |
| **P2** | MEDIUM | Security weakness to address |
| **P3** | LOW | Minor hardening improvement |

### Scoring confidence (multi-reviewer / pipeline use)

When this review runs as one lens inside a multi-agent pipeline, or when `run-penetration-test` synthesis aggregates findings from several hunters, score and gate findings with the discrete confidence anchors in [../code-quality/references/confidence-anchored-scoring.md](../code-quality/references/confidence-anchored-scoring.md). Note the security-relevant exception in that policy's late gate: a **P0 at anchor 50+** (plausible-but-unconfirmed critical) is always surfaced rather than suppressed.

## Instructions

### Step 1: Dependency Vulnerability Scan

```bash
# Python
pip-audit
safety check

# JavaScript
npm audit
snyk test

# Java
mvn dependency-check:check
```

### Step 2: Static Security Analysis

```bash
# Python
bandit -r src/

# JavaScript
npm audit
eslint --plugin security src/

# Java
spotbugs with find-sec-bugs
```

### Step 3: 10-Domain Security Scan

Reference: `references/security-checklist.md`

Work through each domain systematically, applying its diagnostic question:

#### Domain 1: Input/Output Safety
**Diagnostic**: "Does any user-controlled input reach a sensitive sink without sanitization?"
- XSS (innerHTML, dangerouslySetInnerHTML, unescaped template output)
- SQL/NoSQL/Command/GraphQL injection
- SSRF (user-controlled URLs in server requests)
- Path traversal (../ in file paths)
- Prototype pollution (deep merge of user objects)

#### Domain 2: Authentication & Authorization
**Diagnostic**: "Can an authenticated user access resources belonging to another user or tenant?"
- Missing auth guards on endpoints
- Missing tenant checks in multi-tenant systems
- IDOR (direct object references without ownership check)
- Privilege escalation via client-provided roles
- Session fixation (session ID not rotated after login)

#### Domain 3: JWT & Token Security
**Diagnostic**: "What happens if an attacker captures a valid token? How long can they use it?"
- Algorithm confusion (accepting `none` or wrong algorithm)
- Hardcoded signing secrets
- Missing expiration validation
- Sensitive data in JWT payload
- Missing issuer/audience validation

#### Domain 4: Secrets and PII
**Diagnostic**: "If I grep for common secret patterns, what do I find?"
- API keys, credentials in source code
- Secrets in git history
- PII in logs without masking
- Secrets in error messages
- Unencrypted password storage

#### Domain 5: Supply Chain & Dependencies
**Diagnostic**: "If a dependency is compromised, what is the blast radius?"
- Unpinned dependencies (version ranges)
- Dependency confusion risks
- External scripts without SRI integrity
- Known CVEs in dependencies
- Abandoned packages (no maintenance 12+ months)

#### Domain 6: CORS & Security Headers
**Diagnostic**: "What security headers are set? Which are missing?"
- Permissive CORS on authenticated endpoints
- Missing CSP, X-Frame-Options, X-Content-Type-Options
- Missing HSTS
- Exposed internal headers (server version, debug info)

#### Domain 7: Runtime Risks
**Diagnostic**: "Can an attacker cause this service to become unresponsive with a single crafted request?"
- Unbounded loops controlled by user input
- Missing timeouts on external calls
- Missing rate limiting on public endpoints
- Sync I/O in async context
- ReDoS (catastrophic regex backtracking)

#### Domain 8: Cryptography
**Diagnostic**: "Are we using well-vetted cryptographic libraries with secure defaults?"
- Weak algorithms (MD5, SHA1 for security)
- Hardcoded IVs/salts
- Encryption without authentication (AES-CBC without HMAC)
- Insufficient key length
- Custom crypto implementations
- Insecure random (Math.random, random.random for security)

#### Domain 9: Race Conditions (Deep Dive)
**Diagnostic questions**:
1. "Is any shared state accessed by multiple threads/processes/requests without synchronization?"
2. "Are there check-then-act patterns where check and action are not atomic?"
3. "Do database operations that read and write the same row use appropriate isolation?"
4. "In distributed components, what happens if the same event is processed twice?"

Sub-categories:
- **9a: Shared State**: Unsynchronized concurrent access, non-thread-safe collections, global mutable state
- **9b: Check-Then-Act (TOCTOU)**: if-exists-then-use, balance-check-then-deduct, permission check separate from action
- **9c: Database Concurrency**: Missing locking, non-atomic counters, read-modify-write without isolation
- **9d: Distributed Systems**: Missing distributed locks, cache invalidation races, event ordering, split-brain

#### Domain 10: Data Integrity
**Diagnostic**: "If this operation fails halfway through, what state is the data left in?"
- Missing transactions for multi-step operations
- Weak validation before persistence
- Missing idempotency on retry-able paths
- Lost updates from concurrent writes
- Cascade failures from unguarded deletes

### Step 4: Document Findings

For each finding, document both **exploitability** (how easy to exploit) and **impact** (what damage results).

```markdown
## Security Finding

**Vulnerability**: [Type]
**File**: [path/to/file.py:42]
**Severity**: P0 (CRITICAL)
**Domain**: [1-10]
**OWASP**: [A01-A10 if applicable]
**CVE**: [If applicable]

### Description
[Detailed description]

### Exploitability
[How easy to exploit: trivial / moderate / complex]

### Impact
[What damage results: data breach / service disruption / data corruption]

### Vulnerable Code
```python
[problematic code]
```

### Remediation
```python
[fixed code]
```

### References
- [Relevant OWASP link or advisory]
```

## Common Vulnerabilities by Language

### Python
- SQL injection (raw queries, f-strings in SQL)
- Command injection (subprocess with shell=True)
- Pickle deserialization (arbitrary code execution)
- Insecure randomness (random module for security)

### JavaScript
- XSS (innerHTML, dangerouslySetInnerHTML)
- Prototype pollution (deep merge, Object.assign)
- Eval injection (eval, Function constructor)
- Path traversal (user input in require/readFile)

### Java
- SQL injection (string concatenation in queries)
- XXE (XML External Entity)
- Insecure deserialization (ObjectInputStream)
- Log injection (user input in log statements)

### C# / .NET
- SQL injection (string concatenation in SqlCommand)
- Insecure deserialization (BinaryFormatter)
- Path traversal (user input in File.Open)
- LDAP injection

### Go
- SQL injection (fmt.Sprintf in queries)
- Command injection (exec.Command with user input)
- Race conditions (goroutine shared state without mutex)
- Insecure TLS configuration

## Quality Checklist

- [ ] Dependency vulnerability scan completed
- [ ] Static security analysis run
- [ ] All 10 security domains checked with diagnostic questions
- [ ] Race conditions analyzed (all 4 sub-categories)
- [ ] OWASP Top 10 mapped
- [ ] Exploitability and impact documented for each finding
- [ ] Language-specific vulnerabilities checked
- [ ] Findings documented with severity (P0-P3)

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We have no sensitive data, so security doesn't apply" | Injection flaws and SSRF can compromise the underlying server even when the application itself holds no sensitive data, giving attackers a foothold into the broader network. |
| "The framework handles security for us" | Frameworks prevent common pitfalls but cannot prevent IDOR — a developer must still verify ownership before returning a record. Dozens of real-world breaches (e.g., Optus 2022) happened despite using secure frameworks. |
| "We'll add security later before launch" | Security findings discovered post-architecture (e.g., algorithm confusion in JWT, hardcoded secrets) require far more rework than findings caught during initial development. |
| "Our internal API isn't internet-facing so OWASP doesn't apply" | Insider threats and supply chain compromises mean internal APIs are regularly attacked; the Capital One breach in 2019 originated from an internal SSRF call. |
| "We passed a pentest last quarter, so we're fine" | A pentest is a point-in-time snapshot; new code paths, dependency CVEs, and configuration changes introduced after the test are not covered. |
| "Race conditions only matter at scale" | Check-Then-Act race conditions in balance deduction logic have been exploited at low request volumes via simple two-tab browser attacks, enabling duplicate payments and negative balances. |

## Verification

- [ ] All 10 security domains have been checked with their diagnostic questions and findings are documented
- [ ] Dependency vulnerability scan completed and output saved (e.g., `pip-audit`, `npm audit`)
- [ ] Static analysis tool run (bandit, eslint-plugin-security, or equivalent) with zero unreviewed findings
- [ ] Every finding includes severity (P0-P3), exploitability assessment, and remediation code
- [ ] OWASP Top 10 items are explicitly mapped to findings or marked "not applicable" with justification
- [ ] Race condition sub-categories (9a shared state, 9b TOCTOU, 9c database, 9d distributed) each addressed

## Related Skills

- `context-analysis` - Context understanding (Phase 1)
- `code-quality` - Code quality + SOLID review (Phase 2)
- `dependency-security-audit` - Detailed CVE scanning
- `performance-review` - Performance analysis (Phase 4)
- `testing-review` - Test assessment (Phase 5)
- `final-report` - Consolidated report (Phase 6)

---

**Version**: 2.0.0
**Last Updated**: February 2026
**Based on**: Nexus-Hub code review methodology + code-review-expert


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
