---
description: Perform a comprehensive security audit and active remediation loop — scanning for exposed secrets, git hygiene failures, missing auth, unvalidated inputs, insecure installer credential handling, and dangerous code patterns, then fixing every finding until the report is clean.
---

# Run Security Audit

Perform a full security audit of the codebase and then act on every finding. This command has two modes: report-only (default) and fix mode (`--fix`), which applies remediations in severity order and re-audits until no P0 or P1 findings remain.

**This command vs `/run-penetration-test`**: `/run-penetration-test` is a static, read-only analysis that produces a formatted penetration test report — it does not modify code. `/run-security-audit` is an active remediation workflow: it audits, opens the findings file, patches every issue it can, and loops until clean. Use `/run-penetration-test` when you need a deliverable audit report for review. Use this command when you want to actually fix the problems.

**Scope**: Static analysis of source code, configuration files, dependency manifests, and git history. This command does not perform live exploitation or network-level scanning.

---

## Phase 0: Resolve Scope and Mode

Check whether the user provided any flags:

- **`--scope <path>`**: Restrict all analysis to the specified path or glob. Note the restriction in the report header.
- **`--output <path>`**: Write the audit report to this path. Default: `docs/security/security-audit-<YYYY-MM-DD>.md` where the date is today's date.
- **`--fix`**: After writing the initial report, enter the remediation loop and apply fixes. Without this flag, stop after writing the report.
- **`--history`**: Also scan git commit history for secrets (slow on large repos; opt-in only).

Create the output directory if it does not exist.

**Always exclude from all analysis:**
- `node_modules/`, `vendor/`, `.venv/`, `dist/`, `build/`, `out/`
- Generated files (headers: `// generated`, `# auto-generated`)
- Binary files and lock files (`package-lock.json`, `yarn.lock`, `poetry.lock`, `go.sum`)
- Test fixture files that contain deliberate vulnerable patterns for testing purposes — flag these explicitly rather than treating them as real findings

---

## Severity Classification

All findings use the P0–P3 scale throughout every phase.

| Level | Alias | Meaning | Required Action |
|-------|-------|---------|-----------------|
| P0 | CRITICAL | Secret exposure, credential in git, unprotected payment/admin route, RCE-class input bug | Fix immediately; blocks merge and release |
| P1 | HIGH | Missing auth on user-data route, missing input validation, weak crypto, CVE with public exploit | Fix before merge or release |
| P2 | MEDIUM | Missing security header, unpinned dependency, verbose error in production, CORS misconfiguration | Fix in current sprint or create tracked follow-up |
| P3 | LOW | Code style/hygiene that could become a security concern, informational note | Optional; address if effort is low |

---

## Pre-Analysis: Collect Before Writing

Complete all nine analysis phases before writing a single line to the report. Collect findings into an internal working set, then emit the report in one pass. This prevents early sections from contradicting later discoveries.

For each finding record:
- **ID**: sequential number (F-001, F-002, …)
- **Severity**: P0 / P1 / P2 / P3
- **Phase**: which phase discovered it
- **Location**: file path and line number(s)
- **Title**: one-line description
- **Description**: what the vulnerability is and why it is dangerous
- **Evidence**: the exact code snippet (≤ 10 lines) or git object reference
- **Remediation**: concrete steps to fix it

---

## Phase 1: Secret and Credential Scanning

Search all tracked source files, configuration files, and scripts for hardcoded secrets.

### 1.1 High-Entropy String Detection

Scan for strings that match known secret formats:

```
# AWS
AKIA[0-9A-Z]{16}
AWS_SECRET[^=]*=[^$\n]{20,}

# Generic API keys / tokens (base64/hex, 20+ chars, assigned to a key-like variable)
(?i)(api_key|apikey|api_secret|token|secret|password|passwd|pwd|credential)\s*[=:]\s*['"]?[A-Za-z0-9+/=_\-]{20,}

# Private keys
-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----

# JWT secrets / signing keys
(?i)(jwt_secret|signing_key|secret_key)\s*[=:]\s*['"]?.{16,}

# Connection strings with embedded credentials
(mongodb|postgres|mysql|redis|amqp|ftp):\/\/[^:]+:[^@]+@

# OAuth / third-party service keys (Stripe, Twilio, SendGrid, etc.)
sk_live_[0-9a-zA-Z]{24,}
SG\.[A-Za-z0-9\-_]{22}\.[A-Za-z0-9\-_]{43}
AC[0-9a-f]{32}
```

For each match: record exact file, line, and the masked value (show only the first 4 and last 4 characters of the secret; never log the full value).

Flag as **P0** if: in a tracked source file. Flag as **P1** if: in an untracked file that is not in `.gitignore`.

### 1.2 Environment File Audit

Locate all `.env`, `.env.*`, `*.secrets`, `*.credentials`, `secrets.json`, `credentials.json`, and similar files:

- Are any of them tracked by git? → **P0**
- Do they contain actual secret values (not `PLACEHOLDER` or `<your-key-here>`)? Note which variables are populated vs. template-only.
- Is there a `.env.example` or `.env.template` committed for developer onboarding? (Absence is a **P3** recommendation.)

### 1.3 Configuration and Template Files

Inspect configuration files (`*.yaml`, `*.yml`, `*.json`, `*.toml`, `*.ini`, `*.xml`, `*.conf`) and any template files that are rendered into configuration at install time:

- Do rendered output files ever receive actual secret values and then get written to git-tracked paths?
- Do installer-generated CLAUDE.md, settings.json, or hook configuration files contain resolved API keys, tokens, or passwords? → **P0**

---

## Phase 2: Git and File Hygiene

### 2.1 Tracked Secret Files

Run the equivalent of `git ls-files` and check the output for files that should never be committed:

```
Pattern list to flag:
.env, .env.*, *.pem, *.key, *.p12, *.pfx, *.jks, *.crt (private),
id_rsa, id_ecdsa, id_ed25519, credentials, credentials.json,
secrets.json, auth.json, *.token, *.secret, keystore.*,
.netrc, .npmrc (if containing tokens), .pypirc (if containing passwords)
```

Any match that is tracked by git → **P0**.

### 2.2 .gitignore Completeness

Inspect `.gitignore` (and `.gitignore` files in subdirectories) and verify it covers all of the following:

```
# Secrets and credentials
.env
.env.*
!.env.example
!.env.template
*.pem
*.key
*.p12
*.pfx
*.jks
id_rsa
id_ecdsa
id_ed25519
credentials.json
secrets.json
auth.json
*.token
*.secret
.netrc

# OS and editor artifacts
.DS_Store
Thumbs.db
*.swp

# Dependency directories
node_modules/
vendor/
.venv/
__pycache__/

# Build output
dist/
build/
out/
*.exe (if generated)
```

Missing patterns for secret file types → **P1**. Missing patterns for OS/build artifacts → **P3**.

### 2.3 Git History Scan (opt-in with `--history`)

If `--history` was specified, scan the git object store for secrets that were committed and later removed:

```bash
git log --all --oneline --diff-filter=D -- '*.env' '*.pem' '*.key' 'credentials*' 'secrets*'
git log --all -S 'AKIA' --oneline
git log --all -S 'BEGIN PRIVATE KEY' --oneline
```

If secrets are found in history even if removed from HEAD → **P0**. Provide the exact remediation command:

```bash
# Remove a specific file from all history (requires git filter-repo)
pip install git-filter-repo
git filter-repo --path <file-to-purge> --invert-paths --force
# After purging, all collaborators must re-clone
```

**Never run this command automatically.** Flag it as a manual remediation step requiring user confirmation.

---

## Phase 3: Installer and Distribution Security

Inspect all installer scripts (`*.ps1`, `*.sh`, `*.bat`, `install.*`, `setup.*`) and any code that writes configuration files to the user's system.

### 3.1 Credential Input Handling

For each installer that prompts for or accepts API keys, tokens, passwords, or connection strings:

- **Where is the value written?** Identify every `Write-File`, `echo >`, `Set-Content`, `tee`, or equivalent that persists the value.
- **Is the storage path git-tracked?** → **P0** if yes.
- **Is the value stored in plaintext?** Verify whether encryption is applied before writing:
  - Windows: DPAPI (`ConvertFrom-SecureString` / `ConvertTo-SecureString`) or Windows Credential Manager
  - macOS/Linux: OS keychain (`security add-generic-password`, `secret-tool store`) or `gpg --symmetric`
  - Cross-platform fallback: environment variable injection at runtime (never write the secret to disk)
- Plaintext credential stored to any disk path → **P1** (or **P0** if the path could be synced or tracked).

### 3.2 Generated File Review

Inspect the content of files the installer generates and writes to the user's system (CLAUDE.md, settings.json, hook scripts, `.env` files written by the installer):

- Does the generated content contain resolved secret values? → **P0**
- Are template placeholders like `{{API_KEY}}` preserved and resolved at runtime instead of at write time? (Preferred pattern.)
- Is every installer-written file that could contain credentials added to `.gitignore` by the installer itself?

### 3.3 Sync and Cloud Storage Risks

If the project writes files into OneDrive, Dropbox, iCloud, or similar sync-enabled directories:

- Are credential files written to these paths? → **P1** (secrets leave the machine even if not in git)
- Recommend writing secrets to `%APPDATA%` / `~/.config/` paths outside sync scope, or to the OS keychain.

---

## Phase 4: Input Validation and Sanitization

Map every external input boundary and audit each one for validation coverage.

### 4.1 Entry Point Inventory

Enumerate all locations where external or user-supplied data enters the application:
- HTTP route handlers (REST, GraphQL, WebSocket, RPC)
- CLI argument parsers
- File content parsers (uploaded files, config files read at runtime)
- Environment variable reads used in security decisions
- Message queue consumers

For each entry point note: location, input source, and whether a validation schema is applied.

### 4.2 Missing Schema Validation

**TypeScript/JavaScript**: Every `req.body`, `req.query`, `req.params`, `req.headers`, CLI arg, or file parse result must pass through a Zod `.parse()` or `.safeParse()` call before use. Flag any handler that reads input without schema validation → **P1**.

**Python**: Every route function, CLI handler, and file parser should validate with Pydantic or `marshmallow` before accessing fields. Bare dict access on `request.json`, `request.args`, or `os.environ` without validation → **P1**.

**Bash/Shell**: Every variable that originates from user input, file content, or command output must be quoted and sanitized before use in commands → **P1**.

### 4.3 SQL Injection

Scan for SQL string construction using concatenation or f-strings/template literals:

```python
# VULNERABLE
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")

# SAFE
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

Any parameterless SQL string construction → **P0**.

### 4.4 Cross-Site Scripting (XSS)

- `dangerouslySetInnerHTML` without DOMPurify sanitization → **P1**
- `innerHTML`, `outerHTML`, `document.write` with non-static content → **P1**
- Server-rendered templates inserting user data without escaping → **P1**

### 4.5 Command Injection

**Shell scripts**: Unquoted variable expansions in command context, `eval "$user_input"`, `bash -c "$user_input"` → **P0**.

**Node.js**: `child_process.exec()` or `execSync()` with user-derived strings → **P0**. Use `execFile()` or `spawn()` with argument arrays instead.

**Python**: `subprocess.Popen(shell=True, args=user_input)`, `os.system(user_input)` → **P0**.

### 4.6 Path Traversal

File path construction that incorporates user input without canonicalization:

```python
# VULNERABLE
open(base_dir + "/" + user_filename)

# SAFE
resolved = os.path.realpath(os.path.join(base_dir, user_filename))
assert resolved.startswith(os.path.realpath(base_dir) + os.sep)
```

Flag any unsanitized path join with user-supplied components → **P1**.

### 4.7 Unsafe Deserialization

- `pickle.loads(user_data)` or `pickle.load(file_from_user)` → **P0**
- `yaml.load(data)` without `Loader=yaml.SafeLoader` → **P1**
- `eval()` / `exec()` / `compile()` on user-supplied strings → **P0**
- Node.js `JSON.parse()` of user input is generally safe but flag if the result is used as a function or constructor without type checks.

---

## Phase 5: Authentication and Authorization

### 5.1 Route Protection Coverage

Enumerate all HTTP routes (or equivalent operation handlers). For each route, determine:
- Is authentication enforced (middleware, decorator, guard, explicit check)?
- What resources does it access — user data, admin operations, payment flows, file I/O?
- Is the authentication check applied consistently (not conditionally gated behind an environment variable)?

Any route touching user data, financial records, or admin operations without authentication → **P0**.

Any route where authentication is conditionally disabled (e.g., `if process.env.NODE_ENV !== 'production'`) → **P1**.

### 5.2 Authorization (Object-Level and Function-Level)

- After authenticating, does the code verify the authenticated user is authorized to access the specific resource? Flag IDOR risks (e.g., `GET /api/orders/:id` without checking that the order belongs to the requesting user) → **P0**.
- Are admin-only operations protected by a role check in addition to authentication? → **P0** if missing.
- Is authorization enforced at the data layer as well as the route layer? (Route-level checks alone are insufficient if the data access function is called elsewhere.) → **P1** if missing.

### 5.3 JWT and Session Security

- JWTs stored in `localStorage` or `sessionStorage` → **P1** (use `httpOnly` cookies instead)
- JWT signature not verified server-side on every protected request → **P0**
- Missing `exp`, `iss`, or `aud` claim validation → **P1**
- Session cookies missing `httpOnly`, `Secure`, or `SameSite=Strict` / `SameSite=Lax` flags → **P1**
- Long or non-expiring token TTLs (> 24 hours for access tokens, > 30 days for refresh tokens without rotation) → **P2**

### 5.4 Password Storage

- Passwords hashed with MD5, SHA-1, or SHA-256 without salt or iterations → **P0** (use bcrypt, argon2, or scrypt)
- Passwords stored in plaintext → **P0**
- Passwords logged or returned in API responses → **P0**

### 5.5 Rate Limiting and Brute-Force Protection

Check for rate limiting on:
- Login / authentication endpoints → missing is **P1**
- Password reset / OTP verification endpoints → missing is **P1**
- Any endpoint that performs expensive or privilege-escalating operations → missing is **P2**

---

## Phase 6: Dependency and Supply Chain Security

### 6.1 CVE Scanning

Identify the package manager(s) in use and note the appropriate audit commands. **Do not run these commands automatically** — note them as remediation actions:

| Ecosystem | Audit command |
|-----------|--------------|
| npm / pnpm / yarn | `npm audit --json` |
| Python pip | `pip-audit` or `safety check` |
| Go modules | `govulncheck ./...` |
| Rust cargo | `cargo audit` |
| Ruby | `bundle audit` |

If lock files or manifests are present, read them to identify known high-severity CVEs based on package names and version ranges you can reason about. Flag any package known to have a critical unpatched CVE → **P0**.

### 6.2 Version Pinning

- Floating version ranges (`^`, `~`, `>=`, `*`) in production dependencies → **P2**
- No lock file present when one is expected → **P1**
- Development dependencies pinned identically to production — both should be pinned in production but distinguish the risk

### 6.3 Suspicious or High-Risk Dependencies

- Dependencies with no recent commits, a single maintainer, and no test suite that handle authentication, cryptography, or network I/O → **P2** (recommend manual audit)
- Dependencies that use `unsafe`, `cgo`, `ctypes`, or `ffi` — note them and verify they are well-maintained

---

## Phase 7: Configuration and Infrastructure Security

### 7.1 Debug Modes and Error Exposure

- Debug mode enabled via environment variable with no guard against production use (e.g., `DEBUG=*`, `FLASK_ENV=development` with no prod check) → **P1**
- Stack traces, file paths, or database errors returned to the client in error responses → **P1**
- Verbose logging that includes request bodies, headers, or user PII → **P2**

### 7.2 Security Headers

Check HTTP server configuration and middleware for the presence of required security headers. Missing headers to flag:

| Header | Required value | Severity if missing |
|--------|---------------|---------------------|
| `Content-Security-Policy` | Restrictive policy, no `unsafe-eval` | P1 |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | P1 |
| `X-Frame-Options` | `DENY` or `SAMEORIGIN` | P1 |
| `X-Content-Type-Options` | `nosniff` | P1 |
| `Referrer-Policy` | `no-referrer` or `strict-origin-when-cross-origin` | P2 |
| `Permissions-Policy` | Restrict camera, microphone, geolocation | P3 |

### 7.3 CORS Configuration

- `Access-Control-Allow-Origin: *` on endpoints that handle authenticated requests or set cookies → **P1**
- CORS origin whitelist that includes `null` (allows file:// origins) → **P1**
- Credentials allowed (`Access-Control-Allow-Credentials: true`) with a wildcard origin → **P0**

### 7.4 TLS and Transport Security

- HTTP endpoints that handle credentials or sensitive data without TLS redirect → **P1**
- TLS certificate verification disabled in HTTP client calls (`verify=False`, `rejectUnauthorized: false`, `InsecureSkipVerify: true`) → **P1**
- Outbound HTTP calls (not HTTPS) to external APIs handling tokens or user data → **P1**

### 7.5 Client-Bundle Secret Leakage

**Next.js / React / Vue / SvelteKit**: Variables prefixed with `NEXT_PUBLIC_`, `VITE_`, `REACT_APP_`, or equivalent are bundled into the client. Verify that no secret keys, API secrets, or internal infrastructure URLs are exposed this way → **P0** if a secret is found.

---

## Phase 8: Dangerous Code Patterns (SAST)

### 8.1 Dynamic Code Execution

Scan for patterns that execute arbitrary code:

```
# JavaScript / TypeScript
eval(
new Function(
setTimeout(user_input      # string form
setInterval(user_input     # string form

# Python
eval(
exec(
compile(

# Bash
eval "
eval '$
```

Any of the above with a variable or user-controlled argument → **P0**.

### 8.2 Weak Cryptography

- **Hashing**: MD5 or SHA-1 used for passwords, tokens, or integrity checks → **P0**. (MD5/SHA-1 for non-security purposes like checksums are **P3**.)
- **Symmetric encryption**: DES, 3DES, RC4, or AES-ECB mode → **P0**
- **Randomness for security purposes**: `Math.random()`, `random.random()`, `rand()` used to generate tokens, session IDs, CSRF tokens, or password reset codes → **P0** (use `crypto.randomBytes`, `secrets.token_hex`, `/dev/urandom`)
- **Key size**: RSA keys < 2048 bits, EC keys < 256 bits → **P1**

### 8.3 Timing Attacks

String equality comparisons for secrets, tokens, or HMACs using `===`, `==`, or `strcmp` (which short-circuit) → **P1**. Use constant-time comparison:

```python
import hmac
hmac.compare_digest(token_a, token_b)  # Python
```

```typescript
import { timingSafeEqual } from 'crypto'
timingSafeEqual(Buffer.from(a), Buffer.from(b))  // Node.js
```

### 8.4 Regular Expression Denial of Service (ReDoS)

Scan for regex patterns with nested quantifiers or alternation applied to user-controlled strings. Classic ReDoS patterns:

```
(a+)+
([a-zA-Z]+)*
(a|aa)+
```

Flag any regex with catastrophic backtracking potential applied to unconstrained input → **P2**.

### 8.5 Prototype Pollution (JavaScript / TypeScript)

- `Object.assign(target, user_object)` where `user_object` is not schema-validated → **P1**
- Deep merge utilities called with user-controlled objects without key sanitization → **P1**
- Check for `__proto__`, `constructor`, `prototype` in JSON key blacklists — absence is a **P1**

### 8.6 Insecure File Operations

- `fs.readFile`, `open()`, or equivalent called with a path derived from user input without sanitization → **P1** (path traversal risk)
- Temporary files created with predictable names in world-writable directories → **P2**
- Files created without restrictive permissions (`chmod 600` equivalent) when they may contain sensitive data → **P2**

---

## Phase 9: Write the Audit Report

Write the full findings report to the resolved output path.

### Report Structure

```markdown
# Security Audit Report
**Date**: <YYYY-MM-DD>
**Scope**: <full codebase | --scope value>
**Mode**: <report-only | --fix>
**Total findings**: P0: N | P1: N | P2: N | P3: N

---

## Executive Summary
<2–4 sentences: overall security posture, most critical issues, recommended immediate actions>

---

## Findings

### F-001 · P0 · <Title>
**Phase**: <phase name>
**Location**: `<file>:<line>`
**Description**: <what and why>
**Evidence**:
\`\`\`<lang>
<code snippet — masked secrets, never full values>
\`\`\`
**Remediation**: <concrete steps>

---

[repeat for each finding, sorted P0 → P3]

---

## Summary Statistics
| Severity | Count | Fixed | Remaining |
|----------|-------|-------|-----------|
| P0 | N | 0 | N |
| P1 | N | 0 | N |
| P2 | N | 0 | N |
| P3 | N | 0 | N |

---

## Remediation Checklist
- [ ] F-001: <title>
- [ ] F-002: <title>
[...]
```

After writing the report, open it in the editor for the user to review before any fixes are applied.

---

## Remediation Loop (--fix mode only)

If `--fix` was not specified, stop here. Present the report path to the user and suggest re-running with `--fix` to apply remediations.

If `--fix` is active, proceed through the following fix passes in order. After each complete pass, re-run all nine analysis phases and update the report. Continue looping until no P0 or P1 findings remain.

### Fix Pass 1: Secret Exposure (P0s from Phases 1–3)

For each hardcoded secret found in source or config files:

1. Identify the secret's purpose (which service, which environment).
2. Create or update `.env` (for development) and `.env.production` (for production) with the variable. Use a descriptive name: `STRIPE_SECRET_KEY`, `DATABASE_URL`, `OPENAI_API_KEY`.
3. Replace the hardcoded value in source with a `process.env.VAR_NAME` / `os.environ["VAR_NAME"]` / `$env:VAR_NAME` reference.
4. Add the `.env` and `.env.production` files to `.gitignore` if not already present.
5. Add or update `.env.example` with the variable name and a placeholder value.
6. If the secret was also in a file tracked by git: stage the removal, but **do not commit or run `git filter-repo`** — output the exact commands for the user to run manually with an explanation of the git history risk.

For installer-stored credentials found in plaintext:

7. Replace plaintext storage with the appropriate encrypted mechanism for the target platform (DPAPI on Windows, OS keychain on macOS/Linux).
8. If writing to a sync-enabled path (OneDrive, Dropbox), relocate to `%APPDATA%` or `~/.config/` and update the installer's write path.

### Fix Pass 2: Git Hygiene (P0/P1s from Phase 2)

For every secret-bearing file that is git-tracked:

1. Add the file pattern to `.gitignore`.
2. Instruct the user (do not run automatically): `git rm --cached <file>` to untrack without deleting, followed by a new commit.
3. If the secret appeared in git history, provide the `git filter-repo` command and a warning that all collaborators must re-clone after the history rewrite.

### Fix Pass 3: Missing Authentication (P0/P1s from Phase 5)

For each unprotected route identified:

1. Identify the authentication middleware or decorator pattern already used elsewhere in the codebase and apply the same pattern.
2. If no auth middleware exists yet, implement the minimal required guard using the framework's documented approach (e.g., `authenticate` middleware in Express, `@login_required` in Django, `AuthGuard` in NestJS).
3. Add an authorization check for any route vulnerable to IDOR — verify the resource belongs to the authenticated user before returning or modifying it.

### Fix Pass 4: Input Validation (P0/P1s from Phase 4)

For each unvalidated entry point:

1. **TypeScript/JavaScript**: Define a Zod schema at the top of the route handler file. Apply `.parse()` (throws on failure) or `.safeParse()` (returns result object) before any business logic.
2. **Python**: Define a Pydantic model or marshmallow schema. Validate before accessing fields.
3. **Bash**: Quote all variable expansions. Replace `eval "$user_input"` with argument arrays or parameterized calls.
4. **SQL**: Replace all string-concatenated queries with parameterized equivalents.

Do not invent validation rules — infer them from how the value is used (numeric IDs, email addresses, enum-bound strings, etc.). Use the most specific type and format constraints the usage implies.

### Fix Pass 5: Security Headers and Config (P1/P2s from Phase 7)

Add missing security headers to the HTTP server or middleware configuration. Use the project's existing middleware stack — do not introduce a new library if the headers can be set directly. Update CORS configuration to use an explicit allowlist.

### Fix Pass 6: Dependency Updates (P1/P2s from Phase 6)

For each dependency with a known CVE:

1. Check whether a patched version is available.
2. If yes: update the version in the manifest and regenerate the lock file.
3. If no patch exists: note the finding as unresolved and recommend a mitigation or replacement package.

Do not perform broad version bumps beyond what is needed to address the specific CVE.

---

## Verification Pass

After the final remediation loop iteration, perform these checks:

1. **Git staging area**: Confirm no secret-bearing files are staged or tracked (`git status`, `git ls-files`).
2. **Secret patterns**: Re-run Phase 1 scans. Zero matches expected.
3. **Environment files**: Confirm `.env` and all credential files are listed in `.gitignore`.
4. **Installer output**: If installer scripts were modified, trace the code path that writes credentials to disk and confirm encryption is applied before write.
5. **Report update**: Mark fixed findings in the Remediation Checklist. Update the Summary Statistics table with a "Fixed" count for each severity.
6. **Final status**: If P0 and P1 counts are zero, print a clean bill of health. If any remain (e.g., CVEs with no available patch, git history issues requiring manual rewrite), list them explicitly as "Pending Manual Action".

---

## Edge Cases

- **Monorepo**: If the codebase contains multiple packages or services, audit each one independently and merge findings into a single report with package-prefixed finding IDs (e.g., `api/F-001`, `web/F-002`).
- **Generated code**: If secrets appear in generated files, the fix must target the generator or template, not the generated output.
- **Test files with intentionally vulnerable patterns**: Do not fix test fixtures. Flag them with a note: "Test fixture — deliberate vulnerable pattern, not a production risk."
- **False positives**: If a high-entropy string is not a secret (e.g., a test vector, a public key, a base64-encoded non-sensitive value), note it as a **P3 informational** entry and do not attempt remediation.
- **Secrets in CI/CD configuration**: If `.github/workflows/`, `.gitlab-ci.yml`, or similar files contain hardcoded secrets (not `${{ secrets.NAME }}` references), treat identically to source-code secrets → **P0**.
