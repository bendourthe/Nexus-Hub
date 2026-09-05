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

**Trigger phrases**: "security review", "vulnerability scan", "OWASP", "security audit", "penetration test prep", "CVE check", "security assessment", "race condition", "scanner receipt", "re-scan", "independent verifier"

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

### Step 0: Establish the Coverage Denominator

Before reviewing findings, enumerate the entire target as a flat component inventory. Include every top-level module, package, service, transport, and deployable unit visible in the source tree, build manifests, and deployment configuration. Do not build the inventory from the subsystems that look security-sensitive; that silently turns a hot-spot sample into the denominator.

Rebuild this inventory for every new clone, revision, or release under review. A prior inventory is context, not evidence that newly added components were considered.

Track every component in one coverage record:

| Component | Kind | Status | Review action or omission reason |
|---|---|---|---|
| `api` | service | COVERED | Reviewed route registration, authentication boundary, and input-to-sink paths |
| `generated-client` | package | OMITTED | Generated from the reviewed schema; generator output is outside the declared scope |
| `worker` | deployable unit | UNCOVERED | No review action assigned yet |

Use exactly these states:

- **COVERED**: at least one logged review action names what was examined and records its result. Reading or listing a component without a review action is not coverage.
- **OMITTED**: intentionally outside the assessment, with a concrete reason such as declared scope, build-time-only tooling, generated code, or vendored third-party code.
- **UNCOVERED**: no review action or justified omission exists yet. This is the default for every newly enumerated component; an unassigned component stays visible rather than disappearing.

Let `M` be the complete component denominator, `N` the COVERED count, `O` the OMITTED count, and `U` the UNCOVERED count. Verify `N + O + U = M`, then report: `N of M components covered; O omitted for the reasons below; U remain UNCOVERED.` Never describe the whole target as fully reviewed while `U > 0`. When `O > 0`, describe the assessment as scoped and name every omission instead of implying whole-target completeness.

If time or budget cannot cover a large target, scale the number of review passes or state the incomplete coverage. Never shrink `M` to fit the available effort. This follows the established `[[model-prompting-research]]` pattern: an unresearched model is reported as UNVERIFIED rather than omitted silently.

### Step 0A: Choose the Closure Schema

A full security-audit workflow uses schema v2 from `references/closure-gate-review-record.md`. Schema v2 adds a scanner-receipt ledger, remediation receipts, and an independent verifier. A focused or manual review may keep schema v1 when it states, in the coverage artifact, that deterministic scanner completeness is not claimed.

Do not copy the schema field list into this skill. The reference file is the record shape; this skill owns when to choose v1 versus v2 and where the receipts appear in the report.

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

For a full security-audit workflow, follow `references/local-scanner-recipes.md`. Semgrep owns local SAST and gitleaks owns secrets scanning. Check that each binary exists before invoking it, prefer repository config, record version, target scope, config fingerprint, command, exit code, and artifact path, and never auto-install or fall back to a hosted scanner. Redact gitleaks matches. If a ruleset would fetch over the network, disclose it and require authorization.

Focused reviews may still use language-native tools:

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

### Step 3A: Track Multi-Altitude Traversal

Domain coverage and altitude coverage are orthogonal. Checking all 10 domains at one zoom level can still miss defects that exist only across modules, within a feature's end-to-end flow, or inside one parser. Track a separate altitude ledger and attach evidence to each required pass:

| Altitude | Required review pass | Defects it surfaces |
|---|---|---|
| Whole project | Map architecture, trust boundaries, authorization model, and cross-module data flow | Boundary gaps, confused deputies, inconsistent authorization, unsafe service composition |
| File by file | Review each file's responsibilities, imports, exported surface, and security-sensitive state | Hidden entry points, unsafe defaults, local trust assumptions, missed handlers |
| Functionality by functionality | Trace every feature from source to sink and apply every relevant defect class, not only the headline risk | Workflow bypass, missing validation on alternate steps, cross-layer inconsistencies |
| Function by function | Inspect parsing, memory use, encoding, length arithmetic, and comparison logic in security-sensitive functions | Truncation, overflow, canonicalization, parser differentials, subtle logic errors |

Record each altitude as COVERED with a logged action and result, OMITTED with a reason, or UNCOVERED. A component or domain checklist does not substitute for this ledger. The report may claim the review is complete only when both the component denominator and the required altitude passes are fully accounted for.

### Step 3B: Sweep Every Proven-Dirty Sink

Once attacker-influenced data or control reaches a security-sensitive operation, enumerate that sink's other trigger paths before rating, downgrading, rejecting, or closing the finding. Include every route, command, action, internal caller, and the subsystem's own deserialization or import path.

Use a sink-sweep record:

| Sink | Trigger path | Input source | Result | Evidence |
|---|---|---|---|---|
| `execute_task` | HTTP `POST /tasks` | request body | REACHABLE | Handler-to-call trace and safe reproduction |
| `execute_task` | worker dispatch | decoded queue message | UNKNOWN | Worker implementation unavailable |
| `execute_task` | CLI `task run` | command argument | NOT-APPLICABLE | CLI invokes a separate non-executing renderer |

A passing check is negative evidence for that trigger path only. It does not clear the sink. A trigger that cannot be resolved is UNKNOWN, never unaffected; preserve it as an explicit coverage caveat or route the finding to `needs-live-validation` when an unobservable layer is decisive. Apply `[[adversarial-verifier]]`'s rejection proof burden to any attempt to kill the candidate after this sweep.

### Step 4: Document Findings

For each finding, document both **exploitability** (how easy to exploit) and **impact** (what damage results).

#### Rejection Gate

Apply the refutation-validity taxonomy and rejection proof burden owned by `[[adversarial-verifier]]` before marking any candidate rejected. A bare non-reproduction or route list is not enough: the owner requires a reason-specific counter-hypothesis, the sink's actual input sources, a result for every applicable route, and observed build or configuration evidence for reachability claims. When an unobservable layer is the only remaining barrier, route the candidate to `needs-live-validation` through `[[pentest-reporting]]` rather than rejecting or understating it. This skill references that gate but does not restate its taxonomy.

Begin the report with the coverage artifact before listing individual findings. For schema v2, insert the scanner-receipt ledger immediately after component and altitude coverage and before findings:

```markdown
### Scanner Receipts

| Scanner | Applicable | State | Version | Target scope | Config fingerprint | Command | Exit | Artifact or omission |
|---|---|---|---|---|---|---|---|---|
| semgrep | yes | RAN | 1.2.3 | src/ (`scope-src`) | config-default | `semgrep --json src` | 0 | artifacts/semgrep.json |
| checkov | no | NOT_APPLICABLE | n/a | n/a | n/a | n/a | n/a | No supported IaC files |
```

Deterministic coverage is `complete` only when every applicable scanner `RAN`. `UNAVAILABLE`, `FAILED`, and `DECLINED` make coverage degraded. Never claim complete scanner coverage while any applicable scanner is missing, unavailable, failed, or declined.

```markdown
### Asking the model about code without tripping safety classifiers

Finding vulnerabilities in source code is permitted work, so a refusal on such a request is a false positive to work around by rephrasing, not a boundary to respect. Two phrasings trip classifiers needlessly. First, prefer asking whether a program has bugs over asking whether it compiles or runs without errors: "are there any bugs in this program" reads as review, while "does this compile without errors" reads as a request to run untrusted code. Second, when the code is in a lesser-known language or dialect, give the model that language's documentation as context in the same turn, because an unfamiliar syntax plus a security question is a common false-positive shape. A refusal after rephrasing is the finding to record, not the reason to skip the review.

## Security Review Coverage

**Coverage statement**: N of M components covered; O omitted; U UNCOVERED.

### Component Coverage

| Component | Kind | Status | Review action or omission reason |
|---|---|---|---|
| ... | ... | COVERED / OMITTED / UNCOVERED | ... |

### Altitude Coverage

| Altitude | Status | Logged action and result |
|---|---|---|
| Whole project | COVERED / OMITTED / UNCOVERED | ... |
| File by file | COVERED / OMITTED / UNCOVERED | ... |
| Functionality by functionality | COVERED / OMITTED / UNCOVERED | ... |
| Function by function | COVERED / OMITTED / UNCOVERED | ... |

### Proven-Dirty Sink Sweeps

| Sink | Trigger path | Input source | Result | Evidence |
|---|---|---|---|---|
| ... | ... | ... | REACHABLE / BLOCKED / NOT-APPLICABLE / UNKNOWN | ... |
```

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

### Step 5: Run the Deterministic Closure Gate

Do not ask the reviewer to re-read its own report and grade whether it missed anything. A reasoner re-reading its own work tends to ratify the same omissions, while noticing an absent component, candidate, or receipt is precisely the task it already failed. Replace that self-audit with a mechanical claim-to-evidence set difference.

Build the local review record defined in `references/closure-gate-review-record.md`, then run the bundled pure-standard-library gate:

```bash
python scripts/closure-gate.py review-record.json
```

The gate computes five schema-v1 diffs, and six additional schema-v2 diffs when `schema_version` is `2`:

- Component inventory minus components with a logged review action or an explicit `OMITTED` / `UNCOVERED` caveat, surfacing components silently implied as covered.
- Findings minus findings with one of the four terminal or explicitly pending dispositions, surfacing dropped candidates. A `needs-live-validation` item counts as explicitly pending only when its safe-test receipt is complete.
- Confirmed findings minus evidence-bearing facts, surfacing unproven confirmations.
- Rejected findings minus the route-complete rejection record owned by `[[adversarial-verifier]]`, surfacing rejections that skipped their proof burden.
- Report claims minus matching evidence-bearing facts, surfacing claims with no recorded support. Use the claim classes in `[[verification-before-completion]]`'s fraud-class table; do not invent a second taxonomy here.
- Applicable scanners minus successful `RAN` receipts, including silent omissions and a complete-coverage claim over `UNAVAILABLE`, `FAILED`, or `DECLINED` scanners.
- Malformed or unsupported receipt states, including missing tool version and `NOT_APPLICABLE` without evidence.
- Scanner-sourced `corrected` findings minus equivalent before/after receipts.
- Before/after pairs that disagree on detector, config fingerprint, or target scope.
- New after-scan findings without a terminal or explicitly pending disposition.
- A fixer who is the only verifier, or a remediation with no independent read-only verifier.

After remediation, record the post-fix receipt before closing. The same detector, ruleset/config fingerprint, and target scope must re-scan the corrected finding. The patch-producing context cannot be the only verifier: a separate read-only reviewer must sign the before/after delta. A no-fix audit may omit remediations and verifiers, but it must still ship the scanner-receipt ledger.

Any non-empty diff is a FAILURE, not advice. The report does not ship until every diff is empty or each remaining component is recorded as an explicit caveat. Verify coverage and rejection claims as aggressively as confirmations because those two claim types suppress further work. The gate is Nexus-Hub-native and deliberately does not reproduce an external run-directory layout.

`tests/skills/test_closure_gate.py` seeds every mismatch class, proves a clean record passes, asserts the explicit-caveat path, checks the CLI exit codes, and verifies recursive installer distribution. Exit `0` is clean, exit `1` is a non-empty closure diff, and exit `2` is malformed or unreadable input. Schema-v1 fixtures must keep passing unchanged.

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

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We have no sensitive data, so security doesn't apply" | Injection flaws and SSRF can compromise the underlying server even when the application itself holds no sensitive data, giving attackers a foothold into the broader network. |
| "The framework handles security for us" | Frameworks prevent common pitfalls but cannot prevent IDOR -- a developer must still verify ownership before returning a record. Dozens of real-world breaches (e.g., Optus 2022) happened despite using secure frameworks. |
| "We'll add security later before launch" | Security findings discovered post-architecture (e.g., algorithm confusion in JWT, hardcoded secrets) require far more rework than findings caught during initial development. |
| "Our internal API isn't internet-facing so OWASP doesn't apply" | Insider threats and supply chain compromises mean internal APIs are regularly attacked; the Capital One breach in 2019 originated from an internal SSRF call. |
| "We passed a pentest last quarter, so we're fine" | A pentest is a point-in-time snapshot; new code paths, dependency CVEs, and configuration changes introduced after the test are not covered. |
| "Race conditions only matter at scale" | Check-Then-Act race conditions in balance deduction logic have been exploited at low request volumes via simple two-tab browser attacks, enabling duplicate payments and negative balances. |
| "I reviewed the security-sensitive modules, so the target is covered" | A hot-spot list is not the target denominator. Any module, package, service, transport, or deployable unit without a review action must remain visible as OMITTED or UNCOVERED. |
| "One route to this sink is blocked, so the sink is safe" | The clean result applies only to that route. Another command, internal caller, decoded message, or import path may still reach the same operation and must be recorded separately. |
| "The component ledger is complete, so every applicable scanner ran" | Component coverage is not scanner coverage. An applicable scanner without a receipt is a silent omission, and `UNAVAILABLE` or `DECLINED` degrades deterministic completeness. |
| "I produced the patch, so I can sign the re-scan" | The fixer cannot be the only verifier. A separate read-only reviewer must consume the before/after receipts and the patch diff. |

## Verification

- [ ] All 10 security domains have been checked with their diagnostic questions and findings are documented
- [ ] The target was re-enumerated for the reviewed revision, and every component appears exactly once as COVERED, OMITTED, or UNCOVERED
- [ ] The coverage arithmetic holds (`N + O + U = M`), every omission has a reason, and the report does not imply completeness while any component is UNCOVERED
- [ ] Whole-project, file-by-file, functionality-by-functionality, and function-by-function passes each have a logged status and result; domain coverage was not substituted for altitude coverage
- [ ] Every proven-dirty sink has a trigger-path sweep covering routes, commands, actions, internal callers, and subsystem deserialization or import paths where applicable
- [ ] Negative evidence is scoped to the tested trigger path, and every unresolved path remains UNKNOWN or produces `needs-live-validation`
- [ ] Dependency vulnerability scan completed and output saved (e.g., `pip-audit`, `npm audit`)
- [ ] Static analysis followed `references/local-scanner-recipes.md` when this run is a full security audit: Semgrep and gitleaks were discovered locally or recorded `UNAVAILABLE`, no tool was auto-installed, and gitleaks output contains no matched secret values
- [ ] Every finding includes severity (P0-P3), exploitability assessment, and remediation code
- [ ] Every rejected finding satisfies `[[adversarial-verifier]]`'s observed, route-complete rejection record
- [ ] Every candidate blocked only by an unobservable layer is routed to `needs-live-validation` rather than rejected or rated Low
- [ ] `scripts/closure-gate.py` exits `0` for the current `references/closure-gate-review-record.md` shape, and all reported diff sets are empty
- [ ] Full security-audit runs used schema v2; any schema-v1 review stated that deterministic scanner completeness is not claimed
- [ ] Every inventory scanner has a receipt in `RAN`, `NOT_APPLICABLE`, `UNAVAILABLE`, `FAILED`, or `DECLINED`, and complete scanner coverage is claimed only when every applicable scanner `RAN`
- [ ] Every scanner-sourced correction has equivalent before and after receipts, and an independent read-only verifier distinct from the fixer signed the delta
- [ ] Every `OMITTED` or `UNCOVERED` component that has no logged review action carries an explicit caveat rather than disappearing from the closure record
- [ ] `tests/skills/test_closure_gate.py` passes, including every seeded mismatch class, malformed-data handling, and recursive distribution
- [ ] OWASP Top 10 items are explicitly mapped to findings or marked "not applicable" with justification
- [ ] Race condition sub-categories (9a shared state, 9b TOCTOU, 9c database, 9d distributed) each addressed

## Related Skills

- [[context-analysis]] -- Context understanding (Phase 1)
- [[code-quality]] -- Code quality + SOLID review (Phase 2)
- [[dependency-security-audit]] -- detailed CVE scanning behind Domain 5 (supply chain)
- [[performance-review]] -- Performance analysis (Phase 4)
- [[testing-review]] -- Test assessment (Phase 5)
- [[final-report]] -- Consolidated report (Phase 6)
- [[security-patch-advisor]] -- generate fixes for the XSS, injection, and SSRF findings this review surfaces
- [[adversarial-verifier]] -- owns the valid/invalid refutation taxonomy and the proof burden required to reject a candidate
- [[pentest-reporting]] -- owns `needs-live-validation` receipts and the confirmed-versus-potential severity reporting discipline
- [[model-prompting-research]] -- established precedent for reporting an unverified inventory item instead of omitting it silently
- Local security-audit user guide -- `guides/reference/SECURITY_AUDIT.md`

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
