# Security Checklist Reference

Quick-reference security checklist. Use before merging auth changes, payment integrations, or any code that handles user input or sensitive data. Maps to OWASP Top 10.

---

## Pre-Commit Security Checks

- [ ] No hardcoded credentials, API keys, or tokens in source files
- [ ] No secrets in `.env` files that are tracked by git
- [ ] `git log --all --full-history -- '*.env'` returns nothing sensitive
- [ ] `git diff HEAD` reviewed for accidental secret exposure
- [ ] Dependencies audited: `npm audit` / `pip audit` / `govulncheck ./...`

---

## Input Validation (A03: Injection)

- [ ] All external inputs validated at the system boundary (HTTP, CLI, file, env vars)
- [ ] No string concatenation used to build SQL queries -- parameterized queries only
- [ ] File paths sanitized with `os.path.realpath()` / `filepath.Clean()` and checked against allowed root
- [ ] No `eval()`, `exec()`, `shell=True` on user-supplied data
- [ ] HTML output escaped or sanitized with DOMPurify before rendering
- [ ] JSON schema validation on all API request bodies

---

## Authentication (A07: Identification and Authentication Failures)

- [ ] Passwords hashed with bcrypt, scrypt, or Argon2 -- never MD5 or SHA-1
- [ ] JWT stored in `httpOnly`, `Secure`, `SameSite=Strict` cookies -- not localStorage
- [ ] JWT signature verified server-side on every protected request
- [ ] JWT claims validated: `exp`, `iss`, `aud`
- [ ] Session tokens rotated on privilege escalation (login, role change)
- [ ] Rate limiting on login, password reset, and token refresh endpoints
- [ ] MFA available for privileged roles

---

## Authorization (A01: Broken Access Control)

- [ ] Authorization checked at the data layer, not just the route level
- [ ] Object IDs are not directly user-controllable without ownership verification (IDOR prevention)
- [ ] Admin-only endpoints protected with role check, not just authentication
- [ ] No path traversal possible via user-supplied file paths
- [ ] CORS restricted to known, trusted origins

---

## Secrets Management (A02: Cryptographic Failures)

- [ ] Secrets loaded from environment variables or a secrets manager -- never from source files
- [ ] TLS 1.2+ enforced; no SSL 3.0 or TLS 1.0
- [ ] Sensitive data encrypted at rest (PII, payment data, health records)
- [ ] Encryption keys rotated on a defined schedule
- [ ] No sensitive fields logged in plaintext (passwords, tokens, PII)

---

## Dependency Security (A06: Vulnerable Components)

- [ ] No dependencies with known critical/high CVEs (CI gate on `npm audit --audit-level=high`)
- [ ] All dependencies pinned to exact versions in production
- [ ] New dependencies reviewed: active maintenance, test coverage, single-maintainer risk
- [ ] Supply chain: verify package checksums / lockfile integrity

---

## HTTP Security Headers

All responses should include:

- [ ] `Content-Security-Policy` -- restrict script/style sources
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY` (or `SAMEORIGIN`)
- [ ] `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- [ ] `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] Remove `X-Powered-By`, `Server` headers (information disclosure)

---

## Error Handling (A05: Security Misconfiguration)

- [ ] Stack traces, file paths, and database errors never returned to clients
- [ ] Consistent error response shape -- no information disclosure via different error formats
- [ ] 404 and 403 responses return the same shape (don't confirm resource existence)
- [ ] Debug mode disabled in production (`DEBUG=False`, `NODE_ENV=production`)

---

## OWASP Top 10 Quick Map

| Rank | Risk | Primary Control |
|---|---|---|
| A01 | Broken Access Control | Authorization at data layer + IDOR check |
| A02 | Cryptographic Failures | TLS, encrypt at rest, no MD5/SHA-1 |
| A03 | Injection | Parameterized queries, input validation |
| A04 | Insecure Design | Threat modeling, secure defaults |
| A05 | Security Misconfiguration | Debug off, headers set, defaults changed |
| A06 | Vulnerable Components | `npm audit`, `pip audit`, pin deps |
| A07 | Auth Failures | bcrypt, JWT in httpOnly cookie, MFA |
| A08 | Software Integrity Failures | SBOM, lockfile, signed commits |
| A09 | Logging Failures | Log security events, no secrets in logs |
| A10 | SSRF | Validate + whitelist outbound URLs |

---

Related skills: `security-review`, `authentication-patterns`, `dependency-security-audit`, `cve-reachability-analyzer`, `security-patch-advisor`, `run-security-audit`
