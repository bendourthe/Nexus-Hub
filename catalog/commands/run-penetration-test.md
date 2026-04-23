---
description: Perform a deep, Shannon-inspired static security audit using 5 parallel specialist vulnerability hunters (or 6 with --depth=deep to add business-logic and advanced-attack coverage), OWASP WSTG-aligned, producing a full penetration test report with code-level findings, proof-of-concept snippets, and remediation guidance.
---

# Run Penetration Test

Perform a focused, parallel security audit of the codebase using five specialized vulnerability hunters running simultaneously — one per OWASP attack class — with an optional 6th hunter for business-logic and advanced-attack coverage under `--depth=deep`. Each hunter has full analysis time for its domain, unlike `/review-codebase` which covers security as one of eight concerns in a general health check.

**This command vs `/review-codebase`**: `/review-codebase` produces a comprehensive code health report across quality, architecture, performance, testing, and security. `/run-penetration-test` is security-only, with deeper OWASP coverage, parallel specialist analysis, STRIDE threat modeling, and a Shannon-style penetration test report. Use this command when you need a dedicated security audit rather than a general review.

**Scope**: This is static analysis — reading code, configuration, and dependencies to identify vulnerability patterns. It does not perform live exploitation, dynamic scanning, or network-level testing. Findings are supported by code-level proof-of-concept (vulnerable code snippets with annotations) rather than running exploits.

---

## Resolve Scope

Check whether the user provided a `--scope` argument specifying a subdirectory or file pattern to audit.

- **`--scope` provided**: Restrict all analysis to the specified path. Note the restricted scope in the report header.
- **No `--scope`**: Audit the entire codebase.

Check whether the user provided an `--output` argument specifying a custom report path.

- **`--output` provided**: Write the report to that path.
- **No `--output`**: Write to `docs/security/penetration-test-<YYYY-MM-DD>.md` where the date is today's date.

Check whether the user provided a `--depth` argument.

- **`--depth=deep`**: Spawn the optional 6th hunter (Business Logic & Advanced Attacks - see Hunter 6 below) alongside the five standard hunters. Aggregate cost increases by roughly 20%. Required to populate WSTG-BUSL coverage and the advanced-attack rows of the WSTG Coverage Matrix.
- **No `--depth` or `--depth=standard`**: Run the five standard hunters only. WSTG-BUSL and the advanced-attack rows remain marked "Not covered" in the final matrix.

Create the output directory if it does not exist.

**Always exclude from all analysis:**
- `node_modules/`, `vendor/`, `.venv/`, `dist/`, `build/`, `out/`
- Generated files (headers: `// generated`, `# auto-generated`)
- Binary files and lock files (`package-lock.json`, `yarn.lock`, `poetry.lock`)
- Test fixture files that contain deliberate vulnerable patterns for testing purposes (flag these explicitly if found)

---

## Phase 1: Attack Surface Mapping

Before launching the parallel hunters, build a complete picture of the codebase's attack surface. This context is passed to every hunter in Phase 2.

### 1.1 Technology Stack Identification

Scan manifests and configuration files to identify:
- Languages and frameworks in use (including versions where visible)
- Authentication libraries and patterns (JWT, sessions, OAuth, API keys)
- Database drivers and ORM libraries
- HTTP clients and external API integrations
- Template engines
- Serialization formats in use (JSON, XML, YAML, pickle, MessagePack, etc.)
- File upload or processing capabilities

### 1.2 Entry Point Enumeration

Map every point where external or user-supplied data enters the application:
- HTTP route handlers (REST endpoints, GraphQL resolvers, WebSocket handlers, RPC methods)
- CLI argument parsers
- File parsers (uploaded files, config files read at runtime)
- Message queue consumers
- Scheduled job inputs
- Environment variable reads that affect security decisions (e.g., `NODE_ENV`, debug flags)

For each entry point, note: path/location, HTTP method (if applicable), authentication required (yes/no/inferred), and data sources accepted (query params, body, headers, cookies, files).

### 1.3 Authentication and Authorization Boundaries

Identify:
- All authentication mechanisms and where they are enforced (middleware, decorators, route guards)
- All authorization checks and what resources they protect
- Any routes or operations that are intentionally public
- Any places where authentication is conditionally applied (e.g., gated behind environment variables)
- Token or session creation and validation logic
- Password storage, hashing, and comparison patterns

### 1.4 High-Value Target Identification

Flag components that carry the highest risk if compromised:
- Endpoints that modify user data, financial records, or access permissions
- Admin or privileged operation endpoints
- Payment processing or credential handling flows
- File read/write/delete operations
- External HTTP calls or subprocess executions
- Database write operations with user-supplied data

### 1.5 Produce the Attack Surface Brief

Compile the findings from 1.1-1.4 into an internal **Attack Surface Brief** structured as follows. This brief is injected verbatim into each Phase 2 hunter prompt.

```
ATTACK SURFACE BRIEF
====================
Project: <name>
Stack: <languages, frameworks, key libraries>
Auth mechanism: <e.g., JWT with HS256, session cookies, API keys>
Auth library: <e.g., jsonwebtoken 9.0.2, passport.js>
Template engine: <e.g., Handlebars, Jinja2, none>
Serialization: <e.g., JSON only, pickle in session store>
External HTTP: <yes/no — libraries used>
File handling: <yes/no — upload/read/write>
Database: <e.g., PostgreSQL via pg 8.11, no ORM>

Entry points (<count> total):
- <method> <path> [auth: yes/no] — <brief description>
  ...

High-value targets:
- <file:line> — <brief description>
  ...

Auth/authz boundary files:
- <file paths>

Scope restriction: <"full codebase" or path if --scope was used>
```

---

## Phase 2: Parallel Vulnerability Hunters

Launch the hunters simultaneously using concurrent Agent tool calls. The five standard hunters (Injection, XSS/Client-Side, Auth/Session, Access Control, Infrastructure/Configuration) always run. The optional 6th hunter (Business Logic & Advanced Attacks) runs only if `--depth=deep` was supplied. Each hunter receives the full Attack Surface Brief from Phase 1 as context. Wait for all hunters to complete before proceeding to Phase 3.

**Effort level**: Set `effortLevel: high` for each hunter agent (de-escalated one tier from the shipped `xhigh` default). Parallel fan-out multiplies per-agent cost, and `high` preserves the reasoning quality needed for vulnerability hunting without paying the `xhigh` premium per hunter. Reserve `xhigh` / `max` for the Phase 3 synthesis if the finding set is complex, not for the parallel hunting phase. See the **Effort-Level Strategy** section of [catalog/skills/ai-development/prompt-engineering/SKILL.md](../skills/ai-development/prompt-engineering/SKILL.md) for the decision table and the **explicit parallel fan-out** callout in [catalog/skills/orchestration/multi-agent-coordinator/SKILL.md](../skills/orchestration/multi-agent-coordinator/SKILL.md) for the prompting shape.

**Critical instruction for all hunters**: Before every Bash or file read tool call, output a one-sentence plain-language explanation of what the command does and what its impact will be. This is a hard requirement with no exceptions.

---

### Hunter 1: Injection Hunter

**Agent prompt**:

```
You are the Injection Vulnerability Hunter in a static security audit. Your task is to find every injection vulnerability in the codebase. Read as much of the codebase as needed to be thorough.

ATTACK SURFACE BRIEF:
<inject attack surface brief here>

## Your Scope

Hunt for every instance of the following vulnerability classes. For each finding, produce a structured entry (format below).

### Vulnerability Classes to Hunt

**SQL Injection (WSTG-INPV-05)**
- String concatenation or template literals used to build SQL queries with user-supplied input
- ORM raw query methods called with unsanitized input (e.g., `sequelize.query()`, `cursor.execute()` with f-strings)
- Dynamic table/column names derived from user input without allowlisting

**Command Injection (WSTG-INPV-12)**
- `exec()`, `spawn()`, `system()`, `os.system()`, `subprocess.run(shell=True)` with user-controlled arguments
- Template strings interpolated into shell commands
- Filename or path parameters passed directly to shell commands

**Server-Side Template Injection / SSTI (WSTG-INPV-18)**
- Template engines rendering user-supplied strings as templates (not as data)
- `render_template_string()`, `env.from_string()`, `new Function()` with user input
- Handlebars, Pug, Jinja2, Twig, Freemarker, Velocity — look for user-controlled template content

**XML/XXE Injection (WSTG-INPV-07)**
- XML parsers with external entity processing enabled
- `DOCTYPE` declarations accepted from user-supplied XML
- YAML parsers using unsafe load functions (`yaml.load()` without `Loader=yaml.SafeLoader`)

**XPath Injection (WSTG-INPV-09)**
- XPath queries built with string concatenation including user input

**LDAP Injection (WSTG-INPV-06)**
- LDAP filter strings built with user-supplied values without escaping

**Code Injection (WSTG-INPV-11)**
- `eval()`, `exec()`, `new Function()`, `compile()` with user-supplied code strings
- Dynamic `require()`/`import()` with user-controlled paths
- Python `pickle.loads()`, `marshal.loads()` on user-supplied data

**Path Traversal (WSTG-ATHZ-01)**
- File read/write/delete operations using user-supplied paths without canonicalization
- Missing `os.path.realpath()` / `path.resolve()` before file operations
- Missing check that resolved path starts within the allowed directory

## Reporting Format

For each finding, produce:

```
### [SEVERITY] <Short Title>
- **OWASP**: WSTG-INPV-XX
- **Location**: `file/path.ext:line`
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW
- **Description**: What the vulnerability is and why it is vulnerable.
- **Proof of Concept** (static):
  ```
  <vulnerable code snippet, 3-10 lines, annotated>
  ```
- **Impact**: What an attacker could achieve.
- **Remediation**: Specific fix with a before/after code example.
```

If a vulnerability class has no findings, include a one-line note: "No [class] findings — [brief reason, e.g., 'no SQL queries found in codebase' or 'all queries use parameterized form']."

Return ALL findings as a single structured Markdown block.
```

---

### Hunter 2: XSS and Client-Side Hunter

**Agent prompt**:

```
You are the XSS and Client-Side Vulnerability Hunter in a static security audit. Your task is to find every cross-site scripting and client-side vulnerability in the codebase. Read as much of the codebase as needed to be thorough.

ATTACK SURFACE BRIEF:
<inject attack surface brief here>

## Your Scope

**Reflected XSS (WSTG-INPV-01)**
- Server-rendered responses that include query parameters, form fields, or headers in HTML output without encoding
- Template engines outputting user data with raw/unescaped filters (e.g., `{{{ }}}` in Handlebars, `| safe` in Jinja2, `<%- %>` in EJS)
- Response bodies built with string concatenation including user input

**Stored XSS (WSTG-INPV-02)**
- User-supplied data stored in a database and later rendered in HTML without encoding
- Rich text or HTML fields stored and rendered — check if sanitization is applied and whether it uses an allowlist approach

**DOM-Based XSS (WSTG-CLNT-01)**
- JavaScript that assigns `location.hash`, `document.URL`, `document.referrer`, `window.name`, or URL parameters to `innerHTML`, `outerHTML`, `document.write()`, or `eval()`
- jQuery `html()`, `append()`, `prepend()` called with unencoded user data
- `dangerouslySetInnerHTML` in React receiving unsanitized content

**Content Security Policy Analysis (WSTG-CONF-12)**
- Presence and strength of CSP headers
- `unsafe-inline`, `unsafe-eval`, or wildcard source directives that undermine XSS protection
- Missing `frame-ancestors` directive

**Prototype Pollution (WSTG-CLNT-07)**
- Object merging or deep-copy functions that accept user-supplied keys without property name sanitization
- Missing checks for `__proto__`, `constructor`, `prototype` in merge/assign operations
- `lodash.merge()`, `jQuery.extend(true, ...)` with user-supplied objects containing prototype-polluting keys

**HTML Injection**
- Unencoded user input rendered into HTML attributes (especially `href`, `src`, `action`, `style`)
- User-supplied URLs used in `<a href>` or `<iframe src>` without scheme validation

## Reporting Format

For each finding:

```
### [SEVERITY] <Short Title>
- **OWASP**: WSTG-INPV-XX or WSTG-CLNT-XX
- **Location**: `file/path.ext:line`
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW
- **Description**: What is vulnerable and why.
- **Proof of Concept** (static):
  ```
  <vulnerable code snippet, 3-10 lines, annotated>
  ```
- **Impact**: What an attacker can achieve (session hijack, credential theft, defacement, etc.).
- **Remediation**: Specific fix (encode in correct context, use safe API, tighten CSP).
```

If a class has no findings, include a one-line note with reason.

Return ALL findings as a single structured Markdown block.
```

---

### Hunter 3: Authentication and Session Hunter

**Agent prompt**:

```
You are the Authentication and Session Security Hunter in a static security audit. Your task is to find every authentication weakness and session management vulnerability. Read as much of the codebase as needed to be thorough.

ATTACK SURFACE BRIEF:
<inject attack surface brief here>

## Your Scope

**JWT Vulnerabilities (WSTG-AUTHN-08)**
- Algorithm confusion: libraries that accept `alg: none` or allow the algorithm to be specified in the token header
- Weak or hardcoded signing secrets (short strings, demo keys, environment variables with insecure defaults)
- Missing token expiry validation (`exp` claim not checked)
- Missing issuer/audience validation
- Tokens stored in localStorage (XSS-accessible) instead of httpOnly cookies

**Broken Authentication (WSTG-AUTHN-01 through WSTG-AUTHN-10)**
- Missing rate limiting or account lockout on login endpoints (brute force risk)
- Password comparison using non-constant-time functions (timing oracle)
- Predictable password reset tokens (low entropy, sequential, time-based)
- Password reset tokens that do not expire or are not invalidated after use
- Multi-factor authentication bypass paths (fallback flows that skip MFA)
- Default or hardcoded credentials in configuration files or environment variable defaults

**Insecure Password Storage (WSTG-AUTHN-07)**
- Passwords hashed with MD5, SHA-1, or SHA-256 without salting
- Missing bcrypt, scrypt, argon2, or PBKDF2
- Passwords stored in plaintext or base64-encoded

**Session Management (WSTG-SESS-01 through WSTG-SESS-06)**
- Session tokens with insufficient entropy (short, sequential, or predictable)
- Session cookies missing `httpOnly`, `Secure`, or `SameSite` flags
- Session fixation: session ID not regenerated after authentication
- Missing session invalidation on logout (server-side session not destroyed)
- Long-lived sessions without re-authentication for sensitive operations

**Credential Storage and Transmission**
- API keys, tokens, or passwords hardcoded in source files
- Credentials logged in plaintext (check logging calls near auth flows)
- Auth tokens transmitted in URL parameters (visible in server logs and browser history)

## Reporting Format

For each finding:

```
### [SEVERITY] <Short Title>
- **OWASP**: WSTG-AUTHN-XX or WSTG-SESS-XX
- **Location**: `file/path.ext:line`
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW
- **Description**: What is wrong and why it creates an authentication risk.
- **Proof of Concept** (static):
  ```
  <vulnerable code snippet, 3-10 lines, annotated>
  ```
- **Impact**: What an attacker can achieve (account takeover, session hijack, credential theft).
- **Remediation**: Specific fix with before/after example where applicable.
```

If a class has no findings, include a one-line note with reason.

Return ALL findings as a single structured Markdown block.
```

---

### Hunter 4: Access Control Hunter

**Agent prompt**:

```
You are the Access Control and Authorization Hunter in a static security audit. Your task is to find every access control weakness, IDOR, privilege escalation, and CSRF vulnerability. Read as much of the codebase as needed to be thorough.

ATTACK SURFACE BRIEF:
<inject attack surface brief here>

## Your Scope

**Insecure Direct Object Reference / BOLA (WSTG-ATHZ-04)**
- Routes that accept an ID parameter and fetch a resource without verifying the requester owns or has permission to access that resource
- Queries like `findById(req.params.id)` without a `WHERE owner = currentUser` or equivalent ownership check
- File download/view endpoints that serve any file path without authorization

**Privilege Escalation (WSTG-ATHZ-03)**
- Admin-only or privileged operations that are accessible to lower-privilege roles
- Role checks based on client-supplied values (e.g., a role field in the request body)
- Missing authorization on internal or "hidden" endpoints (security through obscurity)
- Horizontal privilege escalation: user A accessing user B's data by manipulating an ID

**Missing Authorization (WSTG-ATHZ-01 / WSTG-ATHZ-02)**
- Routes or operations that perform state changes (write, delete, update) without any authorization check
- Authorization applied only at the route level but not at the service/data layer (broken object-level authorization)
- Inconsistent authorization — some routes in a group are protected, others are not

**CSRF (Cross-Site Request Forgery) (WSTG-SESS-05)**
- State-changing endpoints (POST/PUT/PATCH/DELETE) without CSRF token validation
- Cookies used for authentication without `SameSite=Strict` or `SameSite=Lax`
- Forms that submit to state-changing endpoints without anti-CSRF tokens

**CORS Misconfiguration (WSTG-CONF-07)**
- `Access-Control-Allow-Origin: *` on endpoints that use cookie-based authentication
- `Access-Control-Allow-Origin` dynamically set to match the request `Origin` header without validation
- `Access-Control-Allow-Credentials: true` combined with a permissive origin policy

**Mass Assignment**
- ORM or deserializer that binds request body fields directly to model attributes without a field allowlist
- User-supplied objects merged into internal data models without filtering sensitive fields (e.g., `isAdmin`, `role`, `balance`)

## Reporting Format

For each finding:

```
### [SEVERITY] <Short Title>
- **OWASP**: WSTG-ATHZ-XX or WSTG-SESS-XX or WSTG-CONF-XX
- **Location**: `file/path.ext:line`
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW
- **Description**: What is missing or wrong and what access it enables.
- **Proof of Concept** (static):
  ```
  <vulnerable code snippet, 3-10 lines, annotated>
  ```
- **Impact**: What an attacker can access or do.
- **Remediation**: Specific fix — what check to add, what field to restrict, what token to require.
```

If a class has no findings, include a one-line note with reason.

Return ALL findings as a single structured Markdown block.
```

---

### Hunter 5: Infrastructure and Configuration Hunter

**Agent prompt**:

```
You are the Infrastructure and Configuration Security Hunter in a static security audit. Your task is to find SSRF vulnerabilities, open redirects, dangerous deserialization, secrets in code, security misconfigurations, and dependency vulnerabilities. Read as much of the codebase as needed to be thorough.

ATTACK SURFACE BRIEF:
<inject attack surface brief here>

## Your Scope

**Server-Side Request Forgery / SSRF (WSTG-INPV-19)**
- HTTP client calls (`fetch`, `axios`, `requests.get`, `http.get`, `curl`) where the URL includes user-supplied input
- Missing allowlist validation before making outbound HTTP requests
- Missing checks to block requests to private/internal IP ranges (10.x, 172.16-31.x, 192.168.x, 127.x, 169.254.x, ::1)
- Cloud metadata endpoint access risk (169.254.169.254, fd00:ec2::254) in cloud-deployed applications

**Open Redirects (WSTG-CLNT-04)**
- Redirect responses (`res.redirect()`, `302` responses, `Location` header) where the redirect URL includes user-supplied input
- Missing validation that the redirect destination is a relative path or an allowlisted domain

**Security Headers (WSTG-CONF-08)**
- Missing or misconfigured `Content-Security-Policy`
- Missing `Strict-Transport-Security` (HSTS)
- Missing `X-Frame-Options` or CSP `frame-ancestors` directive
- Missing `X-Content-Type-Options: nosniff`
- Missing `Referrer-Policy`

**Secrets and Sensitive Data in Code (WSTG-CONF-06)**
- Hardcoded API keys, tokens, passwords, or cryptographic secrets in source files or configuration
- Default values for sensitive environment variables that are insecure (e.g., `process.env.SECRET || 'dev-secret'`)
- `.env` files checked into version control
- Secrets passed as command-line arguments (visible in process listings)

**Dangerous Deserialization (WSTG-INPV-11)**
- `pickle.loads()`, `marshal.loads()`, `yaml.load()` (without SafeLoader), `unserialize()` (PHP), `ObjectInputStream` (Java) on user-supplied data
- Cookie or session data deserialized without integrity verification

**Dependency Vulnerabilities (WSTG-CONF-05)**
- Check `package.json`, `requirements.txt`, `Gemfile`, `pom.xml`, `go.mod`, or equivalent for dependencies with known CVEs
- Note any dependency that has not been updated in over a year and is a security-sensitive library (auth, crypto, HTTP, XML parsing)
- Flag packages installed from non-official sources (git URLs, local paths) that warrant extra scrutiny

**Error Handling and Information Disclosure (WSTG-ERRH-01 / WSTG-ERRH-02)**
- Stack traces or internal error details returned to clients in production code paths
- Debug mode or verbose error output enabled by default or by environment variable with an insecure default
- Sensitive data (passwords, tokens, PII) logged in plaintext

**Insecure Cryptography (WSTG-CRYP-04)**
- Use of MD5 or SHA-1 for security purposes (signatures, password hashing, token generation)
- Hardcoded initialization vectors or static salts in cryptographic operations
- Symmetric encryption keys hardcoded in source

## Reporting Format

For each finding:

```
### [SEVERITY] <Short Title>
- **OWASP**: WSTG-INPV-XX / WSTG-CONF-XX / WSTG-ERRH-XX / WSTG-CRYP-XX
- **Location**: `file/path.ext:line`
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW
- **Description**: What is wrong and what risk it creates.
- **Proof of Concept** (static):
  ```
  <vulnerable code snippet or configuration excerpt, annotated>
  ```
- **Impact**: What an attacker or unauthorized party can achieve.
- **Remediation**: Specific fix — allowlist, header configuration, secret rotation procedure, or library upgrade.
```

If a class has no findings, include a one-line note with reason.

Return ALL findings as a single structured Markdown block.
```

---

### Hunter 6: Business Logic & Advanced Attacks Hunter (optional, `--depth=deep` only)

**Activation**: This hunter is spawned only when the user invoked the command with `--depth=deep`. If `--depth` is absent or set to `standard`, skip Hunter 6 and proceed directly to Phase 3 with the five hunters above. Running Hunter 6 increases aggregate cost by approximately 20% (one additional parallel agent with its own attack-surface context).

**Agent prompt**:

```
You are the Business Logic & Advanced Attacks Hunter in a deep static security audit. You cover two skill areas: business-logic-abuse (domain-aware invariant violations) and advanced-attack-patterns (architecture-level attack classes). These are flaws that generic vulnerability scanners miss because they depend on domain rules or architectural properties rather than input validation.

ATTACK SURFACE BRIEF:
<inject attack surface brief here>

## Your Scope

### Part A - Business-Logic Abuse

Apply the `business-logic-abuse` skill (see `catalog/skills/security/business-logic-abuse/SKILL.md`). The skill begins with a rule-elicitation step. If the operator has not provided the business rules (high-value workflows, critical invariants, idempotency guarantees, trust boundaries, state transitions), the hunter should:

1. Attempt to infer the rules from the codebase: look for ledger tables, reservation/quota models, multi-step workflow status columns, webhook handlers, idempotency-key infrastructure, payment integrations.
2. Document each inferred rule explicitly as an **assumption** in the findings table so the operator can confirm or correct.
3. Audit against the inferred rules using the six attack classes (race conditions, TOCTOU, double-spending, workflow bypass, idempotency violations, check-sequence abuse) documented in the skill.

### Part B - Advanced Attack Patterns

Apply the `advanced-attack-patterns` skill (see `catalog/skills/security/advanced-attack-patterns/SKILL.md`). Each of its four classes is gated on an applicability check:

1. **State desynchronization** - applicable if the system has distributed components, eventual-consistency stores, cache-vs-DB divergence, or multi-step workflow state.
2. **Cache poisoning** - applicable if any HTTP caching layer exists (CDN, reverse proxy, application cache).
3. **Replay attacks** - applicable if the system accepts signed requests or state-changing endpoints.
4. **Timing attack surfaces** - applicable if any branch depends on a secret or user-enumeration-sensitive input.

For each class, either produce findings or mark the class "Not applicable" with a one-line justification.

## Output Format

Return findings in the same structured Markdown format as the other 5 hunters. Use these finding-class headings in order:

- **Race Conditions (business logic)**
- **TOCTOU (business logic)**
- **Double-Spending / Replay-Within-Window (business logic)**
- **Workflow-State Bypass (business logic)**
- **Idempotency Violations (business logic)**
- **Check-Sequence Abuse (business logic)**
- **State Desynchronization (advanced)**
- **Cache Poisoning (advanced)**
- **Replay Attacks (advanced)**
- **Timing Attack Surfaces (advanced)**

For each class, either list findings or include a one-line "Not applicable because X" line. Every finding must cite a specific `file:line` and include a reproduction sketch or exploit trace.

Cross-link remediations to `catalog/skills/security/security-patch-advisor/SKILL.md` where a pattern patch exists.

Return ALL findings as a single structured Markdown block.
```

---

## Phase 3: Threat Model Synthesis

Once all hunters have returned their findings (5 standard hunters, or 6 when `--depth=deep` was used), synthesize the results.

### 3.1 Deduplicate and Normalize

Review all findings across all hunters. Remove exact duplicates. Where two hunters found overlapping issues at the same location, merge into a single finding that credits both OWASP categories. Under `--depth=deep`, watch for overlap between Hunter 4 (Access Control) and Hunter 6's workflow-bypass findings, and between Hunter 3 (Auth/Session) and Hunter 6's replay-attack findings - merge with dual-category credit where they cover the same `file:line`.

### 3.2 Severity Normalization

Apply a consistent severity scale across all hunter findings:

| Severity | Definition |
|----------|------------|
| **CRITICAL** | Direct path to RCE, authentication bypass, or full data exfiltration with no prerequisites |
| **HIGH** | Significant data exposure, privilege escalation, or session compromise requiring low attacker skill |
| **MEDIUM** | Vulnerability exploitable under specific conditions, requiring some user interaction or prior access |
| **LOW** | Defense-in-depth weakness, information leakage, or best-practice deviation with limited direct impact |

### 3.3 STRIDE Threat Model

Produce a STRIDE threat matrix for the most security-critical components identified in Phase 1 (auth flows, admin operations, external HTTP calls, file operations):

| Threat Category | Present? | Key Finding(s) |
|----------------|----------|----------------|
| **Spoofing** (forging identity) | Yes / No | e.g., "JWT alg:none not rejected — WSTG-AUTHN-08" |
| **Tampering** (modifying data or code) | Yes / No | e.g., "Mass assignment allows role elevation" |
| **Repudiation** (denying actions) | Yes / No | e.g., "No audit log on privileged operations" |
| **Information Disclosure** | Yes / No | e.g., "Stack traces returned to client — WSTG-ERRH-01" |
| **Denial of Service** | Yes / No | e.g., "No rate limiting on login endpoint" |
| **Elevation of Privilege** | Yes / No | e.g., "IDOR on /api/users/:id — WSTG-ATHZ-04" |

### 3.4 Attack Path for Critical Findings

For each CRITICAL or HIGH finding, construct an attack narrative: entry point → preconditions → exploit step → impact. Keep each path to 4-6 steps. Example format:

```
Attack Path: SQL Injection on /api/search
1. Entry point: GET /api/search?q=<payload> (unauthenticated)
2. Precondition: None — endpoint is public
3. Exploit: Inject UNION SELECT payload in q parameter
4. Vulnerable code: src/routes/search.js:34 — query built with string concatenation
5. Impact: Dump entire users table including password hashes
6. Lateral risk: Hashed passwords enable offline cracking → account takeover
```

### 3.5 Risk Matrix

Produce a summary risk matrix:

```
           LIKELIHOOD
           Low      Medium     High
         +--------+---------+--------+
 HIGH    | Monitor |  Plan   |Fix Now |
 I       +--------+---------+--------+
 M MEDIUM| Backlog |  Plan   |Fix Now |
 P       +--------+---------+--------+
 A LOW   | Ignore  | Backlog | Monitor|
 C       +--------+---------+--------+
 T
```

Map each CRITICAL/HIGH finding onto this matrix with a brief label.

---

## Phase 4: Report Generation

Compile all findings from all phases into the report file.

**Determine the current project version** using this priority: CHANGELOG.md → package.json → pyproject.toml → Cargo.toml → vUnknown.

**Write the report** to the output path determined in the Resolve Scope section. If the file already exists, overwrite it and note the regeneration timestamp.

---

```markdown
# Security Assessment: <Project Name>

**Version**: <version>
**Assessment Date**: <YYYY-MM-DD>
**Regenerated**: <timestamp> *(only if previously existed)*
**Assessor**: Claude Code — run-penetration-test command
**Methodology**: Static analysis — OWASP WSTG-aligned, Shannon-inspired parallel vulnerability hunting
**Scope**: <full codebase or restricted path>
**Files Analyzed**: <count>

---

## Executive Summary

| Severity | Count |
|----------|-------|
| Critical | _ |
| High | _ |
| Medium | _ |
| Low | _ |
| **Total** | _ |

**Security Posture**: [1-2 sentence assessment — e.g., "The application has critical injection vulnerabilities in its data access layer and missing authorization checks on several API endpoints. Immediate remediation of the CRITICAL findings is required before production deployment."]

### Top 3 Risks

1. **[CRITICAL/HIGH]** [Finding title] — [one-line impact] (`file:line`)
2. **[CRITICAL/HIGH]** [Finding title] — [one-line impact] (`file:line`)
3. **[HIGH/MEDIUM]** [Finding title] — [one-line impact] (`file:line`)

---

## Attack Surface

### Entry Points

| Method | Path / Handler | Auth Required | Risk Surface |
|--------|---------------|---------------|--------------|
| GET | `/api/search` | No | Query parameter injection |
| ... | ... | ... | ... |

### Trust Boundaries

[Brief description of where the application boundary lies — what is trusted (authenticated users, internal services) vs. untrusted (public internet, file uploads, external APIs).]

### Technology Stack

| Layer | Technology | Security Notes |
|-------|-----------|----------------|
| Runtime | Node.js 20 | — |
| Framework | Express 4.18 | — |
| Auth | jsonwebtoken 9.0 | — |
| Database | PostgreSQL via pg 8.11 | — |
| ... | ... | ... |

---

## Findings

*Ordered by severity: CRITICAL → HIGH → MEDIUM → LOW. Each finding includes location, evidence, and remediation.*

---

### Critical Findings

[All CRITICAL findings here, formatted as below]

---

**[CRITICAL] <Finding Title>**

- **OWASP**: WSTG-XXXX-XX — <Category Name>
- **Location**: [`file/path.ext:line`](file/path.ext)
- **Hunter**: Injection / XSS / Auth / Access Control / Infrastructure

**Description**: [What the vulnerability is, why this specific code is vulnerable, and what preconditions are required for exploitation.]

**Proof of Concept**:
```[language]
// Vulnerable code (file/path.ext:line)
<annotated vulnerable snippet>

// What an attacker sends:
<example payload or request>
```

**Impact**: [What an attacker can achieve — be specific: "read arbitrary files from the server filesystem", "execute arbitrary OS commands as the web process user", "access any other user's records by changing the id parameter".]

**Remediation**:
```[language]
// Before (vulnerable):
<vulnerable pattern>

// After (fixed):
<corrected pattern with explanation>
```

---

### High Findings

[All HIGH findings, same format]

---

### Medium Findings

[All MEDIUM findings, same format]

---

### Low Findings

[All LOW findings, same format — may use a more compact sub-format for clarity]

---

## Threat Model

### STRIDE Analysis

| Threat Category | Present? | Key Finding(s) |
|----------------|----------|----------------|
| **Spoofing** | Yes / No | [finding reference] |
| **Tampering** | Yes / No | [finding reference] |
| **Repudiation** | Yes / No | [finding reference] |
| **Information Disclosure** | Yes / No | [finding reference] |
| **Denial of Service** | Yes / No | [finding reference] |
| **Elevation of Privilege** | Yes / No | [finding reference] |

### Attack Paths / Chains

[Attack narratives for CRITICAL and HIGH findings, as constructed in Phase 3.4. Where multiple findings compose into a single end-to-end exploit (for example, an information-disclosure finding that enables a privilege-escalation finding), describe the chain explicitly: each link in the chain, each required precondition, and the ultimate impact.]

### Secure Design Recommendations

Architectural and design-level mitigations that prevent entire classes of vulnerabilities, distinct from the per-finding Remediation fields above and from the project-wide Remediation Roadmap below. Scope these recommendations to patterns the development team should adopt structurally rather than to one-off fixes. Typical shapes:

- **Centralize authorization in a policy middleware** rather than scattering `if user.role == 'admin':` checks across handlers.
- **Replace string-interpolated SQL with a single typed query layer** (ORM + parameterized statements) enforced by a lint rule.
- **Adopt a server-authoritative state machine** for any workflow where the UI walks a user through sequential steps.
- **Constant-time comparators for every secret comparison** (`hmac.compare_digest`, `crypto.timingSafeEqual`) - add a lint rule rejecting `==` on tokens.
- **Single idempotency-key middleware** applied to every state-changing endpoint rather than per-endpoint ad-hoc.
- **CDN / proxy boundary hardening**: strip client-sent `X-Forwarded-*` headers; whitelist cache-key inputs; audit `Vary` per response class.

Each recommendation should cite the findings it would preempt (e.g., "Preempts F-12, F-19, F-24") so the team can weigh architectural investment against the specific exploit paths it closes.

---

## Remediation Roadmap

Priority-ordered action list for the development team:

### Immediate (before next deployment)

| # | Finding | Location | Effort | Fix Summary |
|---|---------|----------|--------|-------------|
| 1 | [CRITICAL finding] | `file:line` | Low / Medium / High | [one-line fix description] |

### Short-Term (within 1 sprint)

| # | Finding | Location | Effort | Fix Summary |
|---|---------|----------|--------|-------------|

### Medium-Term (within 1 quarter)

| # | Finding | Location | Effort | Fix Summary |
|---|---------|----------|--------|-------------|

---

## OWASP WSTG Coverage Matrix

| WSTG Category | Tests Covered | Findings | Coverage |
|---------------|--------------|----------|----------|
| WSTG-INPV — Input Validation | INPV-01, 02, 05, 06, 07, 09, 11, 12, 18, 19 | _ | Full |
| WSTG-AUTHN — Authentication | AUTHN-01 through 10 | _ | Full |
| WSTG-SESS — Session Management | SESS-01 through 06 | _ | Full |
| WSTG-ATHZ — Authorization | ATHZ-01 through 04 | _ | Full |
| WSTG-CONF — Configuration | CONF-05, 06, 07, 08, 12 | _ | Partial |
| WSTG-CLNT — Client-Side | CLNT-01, 04, 07 | _ | Partial |
| WSTG-ERRH — Error Handling | ERRH-01, 02 | _ | Full |
| WSTG-CRYP — Cryptography | CRYP-04 | _ | Partial |
| WSTG-BUSL — Business Logic | *(static-audit coverage requires `--depth=deep`; see below)* BUSL-01, 03, 05, 06, 07, 09 | _ | Full (with `--depth=deep`); Not covered otherwise |
| WSTG-ATHZ — Cache Poisoning & Cache Deception | Cache-key hygiene, `Vary` correctness, header-injection, path-normalization differences | _ | Full (with `--depth=deep`); Not covered otherwise |
| WSTG-SESS — Replay & Token Binding | Nonce enforcement, timestamp-window validation, token-audience / token-binding checks | _ | Full (with `--depth=deep`); Partial otherwise |
| WSTG-CRYP — Timing Side Channels | User-enumeration timing, token-lookup timing, crypto-branch timing, regex backtracking | _ | Full (with `--depth=deep`); Partial otherwise |
| WSTG-INFO — Information Gathering | *(dynamic/network — not covered by static analysis)* | — | Not covered |

**Note**: This assessment covers static code analysis only. WSTG categories requiring live application testing (WSTG-INFO) and dynamic analysis (active DAST scanning, network-level testing) are out of scope for this command. WSTG-BUSL and the advanced-attack rows above are covered statically by the optional 6th hunter activated with `--depth=deep` (see Hunter 6 below); without the flag these rows are marked Not covered.
```

---

## Quality Checks

Before writing the report, verify:

- [ ] All active hunters completed and returned findings (5 standard; 6 when `--depth=deep` was used) (or explicit "no findings" notes per class)
- [ ] Every finding cites at least one specific `file:line` location
- [ ] Every finding has a Proof of Concept showing the actual vulnerable code
- [ ] Every finding has a concrete remediation step (not just "validate input")
- [ ] Severity assignments are consistent with the normalization table in Phase 3.2
- [ ] The STRIDE table addresses all 6 threat categories
- [ ] Attack paths exist for all CRITICAL and HIGH findings
- [ ] The remediation roadmap is ordered correctly (CRITICAL before HIGH before MEDIUM)
- [ ] The WSTG Coverage Matrix reflects what was actually tested
- [ ] Sections with no findings state explicitly what was checked and confirm it was clean

---

## Iterative Refinement

After producing the report, perform up to 3 internal review passes:

1. **Coverage**: Are there areas of the codebase (especially high-value targets identified in Phase 1) that were not addressed by any hunter? If so, investigate and add findings or explicit clean confirmations.
2. **Depth**: Do the Proof of Concept snippets actually show the vulnerable pattern, or are they placeholder stubs? Ensure every PoC contains real code from the codebase.
3. **Actionability**: Is every remediation specific enough that a developer could apply it without follow-up questions? Vague guidance like "add input validation" should be replaced with the specific function or library to use.

Stop when confident, or after 3 passes.

---

## Next Steps

Found X findings (Critical: _, High: _, Medium: _, Low: _) across Y vulnerability classes.

**How would you like to proceed?**

1. **Fix all** — Implement patches for all findings across all severity levels
2. **Fix Critical and High only** — Implement patches for the most impactful findings
3. **Fix specific findings** — Tell me which findings to address by number
4. **Generate dependency update PRs** — Address the dependency vulnerability findings
5. **Harden configuration** — Apply the security header and configuration fixes only
6. **Export report** — Generate a Word (.docx) version of this report via `/generate-report`
7. **No changes** — Assessment complete, no implementation needed
