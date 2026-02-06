# Security & Reliability Checklist (10 Domains)

Reference checklist for comprehensive security review. Used by the `security-review` skill during Phase 3 of code review.

---

## Domain 1: Input/Output Safety

| Risk | What to Look For |
|------|------------------|
| **XSS** | Unescaped user input rendered in HTML, `innerHTML`, `dangerouslySetInnerHTML` |
| **SQL Injection** | String interpolation in queries, missing parameterized queries |
| **NoSQL Injection** | Unsanitized `$where`, `$regex`, or user-controlled operators |
| **Command Injection** | User input passed to `exec`, `system`, `subprocess` without sanitization |
| **GraphQL Injection** | Dynamic query construction from user input |
| **SSRF** | User-controlled URLs in server-side HTTP requests without allowlist |
| **Path Traversal** | User input in file paths without canonicalization (`../` attacks) |
| **Prototype Pollution** | Deep merge of user-controlled objects without property filtering |

**Diagnostic**: "Does any user-controlled input reach a sensitive sink (query, command, file path, HTML output) without sanitization?"

---

## Domain 2: Authentication & Authorization

| Risk | What to Look For |
|------|------------------|
| **Missing auth guards** | Endpoints or routes without authentication middleware |
| **Missing tenant checks** | Multi-tenant data accessed without tenant_id filtering |
| **IDOR** | Direct object references without ownership verification |
| **Privilege escalation** | Trusting client-provided roles or permissions |
| **Session fixation** | Session IDs not rotated after authentication |
| **Weak password policy** | No minimum length, complexity, or breach check |

**Diagnostic**: "Can an authenticated user access or modify resources belonging to another user or tenant?"

---

## Domain 3: JWT & Token Security

| Risk | What to Look For |
|------|------------------|
| **Algorithm confusion** | Accepting `none` algorithm, or allowing `HS256` when `RS256` is expected |
| **Hardcoded secrets** | JWT signing keys in source code or config files |
| **Missing expiration** | Tokens without `exp` claim or not validating expiration |
| **Sensitive payload data** | PII, passwords, or secrets stored in JWT claims |
| **Missing issuer/audience** | Not validating `iss` or `aud` claims |
| **No refresh rotation** | Refresh tokens that are not rotated on use |

**Diagnostic**: "What happens if an attacker captures a valid token? How long can they use it?"

---

## Domain 4: Secrets and PII

| Risk | What to Look For |
|------|------------------|
| **API keys in code** | Hardcoded credentials, API keys, or connection strings in source |
| **Secrets in git history** | Previously committed secrets (even if deleted in HEAD) |
| **PII in logs** | Email, phone, SSN, or IP addresses logged without masking |
| **Secrets in error messages** | Stack traces or error responses leaking internal details |
| **Missing data masking** | Sensitive fields displayed in full in UI or API responses |
| **Unencrypted storage** | Passwords stored in plaintext or reversible encryption |

**Diagnostic**: "If I grep the codebase for common secret patterns (key, secret, password, token), what do I find?"

---

## Domain 5: Supply Chain & Dependencies

| Risk | What to Look For |
|------|------------------|
| **Unpinned dependencies** | Version ranges (`^`, `~`, `>=`) that allow unvetted updates |
| **Dependency confusion** | Private package names that could collide with public registries |
| **Untrusted CDNs** | External scripts loaded without `integrity` (SRI) attributes |
| **Known CVEs** | Dependencies with published vulnerabilities |
| **Abandoned packages** | Dependencies with no maintenance activity for 12+ months |
| **Excessive permissions** | Packages requesting filesystem, network, or OS access unnecessarily |

**Diagnostic**: "If a dependency is compromised, what is the blast radius?"

---

## Domain 6: CORS & Security Headers

| Risk | What to Look For |
|------|------------------|
| **Permissive CORS** | `Access-Control-Allow-Origin: *` on authenticated endpoints |
| **Missing CSP** | No Content-Security-Policy header |
| **Missing X-Frame-Options** | Clickjacking vulnerability |
| **Missing X-Content-Type-Options** | MIME sniffing attacks |
| **Exposed internal headers** | Server version, internal IPs, or debug info in response headers |
| **Missing HSTS** | HTTP Strict Transport Security not configured |

**Diagnostic**: "What security headers are set on the main responses? Which are missing?"

---

## Domain 7: Runtime Risks

| Risk | What to Look For |
|------|------------------|
| **Unbounded loops** | Loops controlled by user input without max iteration limit |
| **Missing timeouts** | HTTP calls, database queries, or external calls without timeout |
| **Missing rate limiting** | Public endpoints without request throttling |
| **Sync I/O in async context** | Blocking file/network operations on event loop or async thread |
| **Resource exhaustion** | Unbounded queues, connection pools without limits |
| **ReDoS** | Regular expressions with catastrophic backtracking potential |

**Diagnostic**: "Can an attacker cause this service to become unresponsive with a single crafted request?"

---

## Domain 8: Cryptography

| Risk | What to Look For |
|------|------------------|
| **Weak algorithms** | MD5, SHA1 for security purposes (acceptable for checksums only) |
| **Hardcoded IVs/salts** | Initialization vectors or salts that are static or predictable |
| **Encryption without authentication** | AES-CBC without HMAC (use AES-GCM instead) |
| **Insufficient key length** | RSA < 2048 bits, AES < 128 bits |
| **Custom crypto** | Home-grown encryption or hashing schemes |
| **Insecure random** | `Math.random()`, `random.random()` for security-sensitive values |

**Diagnostic**: "Are we using well-vetted cryptographic libraries with secure defaults?"

---

## Domain 9: Race Conditions

This domain warrants deep analysis due to its subtlety and high impact.

### 9a: Shared State Access

| Pattern | Risk |
|---------|------|
| Unsynchronized concurrent access to shared variables | Data corruption, inconsistent state |
| Non-thread-safe collections used across threads | Silent data loss, crashes |
| Global mutable state modified by multiple handlers | Unpredictable behavior |

### 9b: Check-Then-Act (TOCTOU)

| Pattern | Risk |
|---------|------|
| `if exists then use` without atomic operation | File/resource may change between check and use |
| `if balance >= amount then deduct` without lock | Double-spend, negative balance |
| Permission check separate from action | Privilege escalation window |

### 9c: Database Concurrency

| Pattern | Risk |
|---------|------|
| Read-modify-write without transaction isolation | Lost updates |
| Missing optimistic/pessimistic locking | Concurrent overwrites |
| Non-atomic counter increments (`count = count + 1`) | Incorrect tallies |
| `SELECT ... UPDATE` without `FOR UPDATE` | Phantom reads |

### 9d: Distributed Systems

| Pattern | Risk |
|---------|------|
| Missing distributed locks for shared resources | Duplicate processing |
| Cache invalidation races | Stale data served |
| Event ordering assumptions | Incorrect state transitions |
| Split-brain scenarios | Data divergence |

**Diagnostic questions**:
1. "Is any shared state accessed by multiple threads/processes/requests without synchronization?"
2. "Are there any check-then-act patterns where the check and action are not atomic?"
3. "Do database operations that read and write the same row use appropriate isolation?"
4. "In distributed components, what happens if the same event is processed twice?"

---

## Domain 10: Data Integrity

| Risk | What to Look For |
|------|------------------|
| **Missing transactions** | Multi-step database operations without transactional boundaries |
| **Weak validation before persistence** | Data written without schema or constraint validation |
| **Missing idempotency** | Non-idempotent operations on retry-able paths (payments, emails) |
| **Lost updates** | Concurrent writes without conflict detection |
| **Cascade failures** | Deletes without considering foreign key relationships |
| **Inconsistent state** | Partial writes (some tables updated, others not) on failure |

**Diagnostic**: "If this operation fails halfway through, what state is the data left in?"

---

## Usage

For each domain, the reviewer should:
1. Scan the relevant code areas
2. Apply the diagnostic question
3. For each finding, document both **exploitability** (how easy to exploit) and **impact** (what damage results)
4. Classify severity: P0 (immediate exploit risk) through P3 (hardening improvement)
