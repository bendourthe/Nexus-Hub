---
name: authentication-patterns
description: Authentication and authorization patterns (OAuth 2.0, OIDC, JWT, session management, MFA, passkeys, RBAC/ABAC) plus the attacker-perspective JWT and OAuth methodology the design must withstand -- alg:none, RS256/HS256 key confusion, weak-secret cracking, kid/jku injection, claim-validation gaps, token leakage, redirect_uri manipulation, weak state/nonce, PKCE downgrade, code injection. Use when implementing login flows, securing APIs, or reviewing or red-teaming auth architecture under authorization. SKIP, do NOT use for generic input-validation lint (use security-review), web-app injection or access-control review such as SSRF/XXE/IDOR (use advanced-attack-patterns), or any test without documented authorization and scope.
summary_l0: "Implement authentication with OAuth 2.0, JWT, session management, MFA, and passkeys"
overview_l1: "This skill provides authentication and authorization patterns including OAuth 2.0, OIDC, JWT, session management, MFA, and passkeys. Use it when implementing login flows, securing APIs, reviewing auth architecture, adding multi-factor authentication, or implementing modern passwordless patterns. Key capabilities include OAuth 2.0 flow implementation (authorization code, PKCE, client credentials), OIDC integration, JWT design and validation, session management with secure cookie configuration, MFA implementation, passkey/WebAuthn support, RBAC and ABAC authorization models, and token refresh and revocation strategies. It also folds in the attacker-perspective JWT and OAuth methodology the design must withstand (alg:none, key confusion, weak-secret cracking, kid/jku injection, redirect_uri manipulation, PKCE downgrade), with deep probes in references/auth-attack-methodology.md. The expected output is authentication implementation code with secure token handling, session management, and authorization policies. Trigger phrases: authentication, OAuth, OIDC, JWT, session management, MFA, passkeys, login flow, API security, authorization, RBAC, JWT attacks, alg:none, key confusion, PKCE bypass, token leakage."
---

# Authentication Patterns

Comprehensive guidance for implementing secure authentication and authorization systems. Covers OAuth 2.0 flows, OpenID Connect, JWT lifecycle management, session security, password hashing, multi-factor authentication, passkeys/WebAuthn, role-based and attribute-based access control, API key management, and common vulnerability prevention.

## When to Use This Skill

Use this skill for:

- Implementing OAuth 2.0 authorization code flow with PKCE
- Integrating OpenID Connect for SSO (Single Sign-On)
- Designing JWT issuance, validation, and refresh token rotation
- Building secure session management with cookies or tokens
- Implementing password hashing with bcrypt or Argon2
- Adding MFA (TOTP, WebAuthn/passkeys) to an application
- Designing RBAC or ABAC authorization models
- Managing API keys for service-to-service communication
- Configuring security headers (CSP, CORS, HSTS)
- Reviewing auth architecture for common vulnerabilities

**Trigger phrases**: "authentication", "authorization", "OAuth", "OIDC", "JWT", "session management", "login flow", "MFA", "passkeys", "WebAuthn", "RBAC", "ABAC", "API key", "CORS", "CSRF", "password hashing", "refresh token"

## What This Skill Does

Provides production-grade authentication patterns including:

- **OAuth 2.0**: Authorization code + PKCE, client credentials, device flow
- **OpenID Connect**: ID tokens, userinfo endpoint, discovery
- **JWT**: Structure, signing algorithms, validation, refresh rotation
- **Sessions**: Cookie security, token storage, session fixation prevention
- **Passwords**: Hashing (bcrypt, Argon2), salting, migration strategies
- **MFA**: TOTP setup, WebAuthn/passkeys registration and assertion
- **Access Control**: RBAC middleware, ABAC policies, permission models
- **API Security**: API key management, rate limiting, scope enforcement
- **Headers**: CSP, CORS, HSTS, X-Frame-Options configuration

## Instructions

### Step 1: Understand OAuth 2.0 Flows

Full walkthrough: [step-1-understand-oauth-2-0-flows.md](references/step-1-understand-oauth-2-0-flows.md) (load this step when you reach it).

### Step 2: Implement JWT Lifecycle

Full walkthrough: [step-2-implement-jwt-lifecycle.md](references/step-2-implement-jwt-lifecycle.md) (load this step when you reach it).

### Step 3: Secure Session Management

Full walkthrough: [step-3-secure-session-management.md](references/step-3-secure-session-management.md) (load this step when you reach it).

### Step 4: Implement Password Hashing

Full walkthrough: [step-4-implement-password-hashing.md](references/step-4-implement-password-hashing.md) (load this step when you reach it).

### Step 5: Add Multi-Factor Authentication

Full walkthrough: [step-5-add-multi-factor-authentication.md](references/step-5-add-multi-factor-authentication.md) (load this step when you reach it).

### Step 6: Implement Role-Based Access Control (RBAC)

Full walkthrough: [step-6-implement-role-based-access-control-rbac.md](references/step-6-implement-role-based-access-control-rbac.md) (load this step when you reach it).

### Step 7: Configure Security Headers

Full walkthrough: [step-7-configure-security-headers.md](references/step-7-configure-security-headers.md) (load this step when you reach it).

### Step 8: Prevent Common Vulnerabilities

Full walkthrough: [step-8-prevent-common-vulnerabilities.md](references/step-8-prevent-common-vulnerabilities.md) (load this step when you reach it).

## Attacker-Perspective: What the Auth Design Must Withstand

Detailed guidance lives in [attacker-perspective-what-the-auth-design-must-withstand.md](references/attacker-perspective-what-the-auth-design-must-withstand.md) (load on demand).

## Best Practices

- **Use PKCE for all OAuth flows**: Even confidential clients benefit from PKCE as defense-in-depth
- **Short-lived access tokens**: 5-15 minutes; use refresh tokens for longer sessions
- **Rotate refresh tokens**: Issue a new refresh token on every use; detect reuse attacks
- **Store tokens in HttpOnly cookies**: Not localStorage or sessionStorage
- **Use Argon2id for passwords**: OWASP-recommended; bcrypt is acceptable but Argon2id is stronger
- **Never store plaintext passwords**: This rule has no exceptions
- **Regenerate session IDs**: After login, logout, privilege escalation, and periodically
- **Implement rate limiting on auth endpoints**: Prevent brute-force attacks
- **Log all authentication events**: Successful logins, failures, MFA challenges, token refreshes
- **Use SameSite cookies**: Set to `Lax` or `Strict` to prevent CSRF
- **Validate JWT claims thoroughly**: Always check `iss`, `aud`, `exp`, and `nbf`
- **Use asymmetric signing (RS256)**: Allows resource servers to validate without the signing key

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We can skip PKCE because our client is confidential" | Authorization code interception attacks (via open redirects or referrer headers) are possible even with confidential clients; PKCE prevents code replay at zero implementation cost. |
| "JWTs are stateless so we don't need refresh token rotation" | Without rotation, a stolen refresh token grants indefinite access until expiry; rotation with reuse detection (family-based revocation) limits the window to a single use, as demonstrated by the approach recommended after the Auth0 token reuse incidents. |
| "bcrypt with cost 10 is fine for new projects" | Cost 10 was calibrated for ~2012 hardware; modern GPUs can test billions of candidates per second -- cost 12 or Argon2id is the current OWASP minimum. |
| "We store access tokens in localStorage because it's simpler" | XSS in any third-party script on the page (analytics, chat widgets) can exfiltrate localStorage tokens silently; HttpOnly cookies are immune to JavaScript access. |
| "Session ID regeneration after login is optional" | Session fixation allows an attacker to pre-set a known session ID, then hijack it after the victim authenticates -- a P0 vulnerability with trivial exploitation. |
| "We check authorization at the route level, which is sufficient" | Route-level checks prevent accessing the wrong endpoint; IDOR exploits occur at the data layer when a user passes a valid endpoint but with another user's resource ID, bypassing route guards entirely. |
| "We verify the JWT signature, so the token is trustworthy" | A verifier that reads the algorithm from the token header accepts an `alg:none` token or an RS256->HS256 key-confusion forgery; the signature check is only sound when the algorithm and key are pinned server-side, not named by the token. |
| "PKCE is enabled, so our authorization code is safe" | PKCE protects only when the authorization server enforces `code_challenge` and the token endpoint rejects an exchange missing `code_verifier`; an unenforced PKCE downgrades silently and a stolen code is replayable as if PKCE were absent. |
| "Our redirect_uri allowlist uses a prefix match for flexibility" | Prefix or substring matching lets `https://app.example.attacker.example/cb` pass and leaks the authorization code; only full-string exact matching against pre-registered URIs closes redirect_uri manipulation. |

## Verification

- [ ] OAuth 2.0 flows use PKCE (`code_challenge_method: S256`) confirmed in code or config
- [ ] Refresh token rotation is implemented and reuse detection revokes the token family on replay
- [ ] Password hashing uses Argon2id or bcrypt with cost >= 12 (verified in source, not just docs)
- [ ] All session cookies have `Secure`, `HttpOnly`, and `SameSite` attributes set in code
- [ ] JWT validation explicitly checks `iss`, `aud`, `exp`, and `alg` -- no `none` algorithm accepted
- [ ] Rate limiting is applied to the login endpoint (verified by attempting >10 requests/minute)

When the attacker-perspective methodology is exercised (auditing or red-teaming the auth surface), also confirm:

- [ ] Written authorization, scope, and rules of engagement are documented before any probe; targets are in scope and any data used is synthetic or marked test data
- [ ] Every probe used benign placeholders (`auth.example`, `attacker.example`, a placeholder secret) -- no real token, secret, or third-party host was used
- [ ] The verifier rejects `alg: none` and pins an algorithm allowlist (confirmed by submitting a `none` and a cross-family token and observing rejection)
- [ ] Verification keys are never resolved from token-controlled `kid` / `jku` / `x5u` input (confirmed in source)
- [ ] `redirect_uri` is exact-matched against a pre-registered allowlist and `state` / `nonce` are enforced (confirmed by a mismatched-callback probe)
- [ ] Each confirmed weakness maps to a concrete defensive control handed to `security-review` / `security-patch-advisor`

## References

- [references/auth-attack-methodology.md](references/auth-attack-methodology.md) - Deep attacker-perspective JWT and OAuth/OIDC methodology (alg:none, RS256/HS256 key confusion, weak-secret cracking, kid/jku/x5u injection, claim-validation gaps, token leakage; redirect_uri manipulation, weak state/nonce, PKCE downgrade, code injection, IdP mix-up/scope escalation) with benign probes, defenses, and a WSTG/CWE standards map. The methodology section in this skill summarizes each vector; this file carries the concrete structures and sequences and feeds `pentest-reporting`.
- [references/agent-policy-resolution.md](references/agent-policy-resolution.md) - Declarative tool-call authorization for AI agents being built: the deterministic resolution priority order (Specific Deny > Specific Ask > Specific Allow > Wildcard Deny > Wildcard Ask > Wildcard Allow), fail-closed predicates, and convenience presets. Distinct from human / service authentication; applies when an agent grants tools.

## Related Skills

- [[security-review]] -- application security assessment including auth review
- [[jwt-header-and-key-confusion-attacks]] -- alg=none, key confusion, and kid injection against JWT verification (this skill covers issuance and session design)
- [[digital-signatures-and-jwt-signing]] -- signing-key lifecycle and algorithm choice for tokens this skill's verifiers consume
- [[advanced-attack-patterns]] -- the replay / token-binding and injection attack surface that pairs with this skill's JWT and OAuth methodology
- [[pentest-reporting]] -- writes up confirmed auth weaknesses (CVSS, evidence, retest) using the standards map in the references file
- [[security-patch-advisor]] -- patch generation for the auth weaknesses surfaced by the methodology section
- [[pre-commit-checklist]] -- security checks before committing auth code
- [[dependency-security-audit]] -- auditing auth library vulnerabilities
- [[cicd-architect]] -- securing CI/CD pipelines with service accounts and tokens
- [[agentic-endpoint-hardening]] -- agent-credential isolation: placeholder keys in the agent environment, real keys injected by a broker outside the trust seam

---

**Version**: 1.1.0
**Last Updated**: June 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
