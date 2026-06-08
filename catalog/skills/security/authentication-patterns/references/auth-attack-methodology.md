# Auth Attack Methodology -- JWT and OAuth/OIDC Reference

Deep attacker-perspective methodology for the JWT and OAuth/OIDC attack surface that the authentication design in [`../SKILL.md`](../SKILL.md) must withstand. The SKILL.md body carries a one-line summary of each vector and the defensive requirement; this file carries the concrete malformed-token structures, key-confusion mechanics, and flow-manipulation sequences that would otherwise inflate the always-on-trigger body. Read it the way a defender reads an attacker's playbook: each control in the body exists because one of these vectors would otherwise succeed.

## Authorized use only

This is offensive methodology re-authored to harden the system under test. Use it only inside an authorized engagement with documented scope and rules of engagement. Every token, secret, and host below is a benign placeholder (`auth.example`, `app.example`, `attacker.example`, and the literal weak secret `secret`) - never a real credential, and never pointed at a third party you are not authorized to test. The deliverable of any assessment is the defensive control, not a forged token. Each section ends with the remediation that closes the class.

## How to read this file

For each vector: **Reach** (what makes the surface present), **Confirm** (a benign probe that proves the weakness), **Escalate** (how far the class goes, demonstrated only as far as the RoE allows), and **Defend** (the control the auth design must carry). Stop at Confirm unless the engagement explicitly authorizes escalation.

---

## JWT -- JSON Web Token attacks

A JWT is `base64url(header).base64url(payload).signature`. Every attack below targets a verifier that trusts an attacker-influenced part of the header, or that fails to bind the signature to a key and algorithm the server chose rather than the token named.

### J1. `alg: none` -- signature stripping

**Reach**: the verifier reads the algorithm from the token header instead of pinning it server-side.

**Confirm**: set `"alg": "none"` (or a case variant like `"None"` / `"nOnE"` to dodge a naive string check), drop the signature, and keep the trailing dot.

```text
header  = {"alg":"none","typ":"JWT"}
payload = {"sub":"victim","role":"admin","exp":4102444800}
token   = base64url(header) + "." + base64url(payload) + "."     # empty signature
```

If an authenticated route accepts this, the verifier never checked the signature, so any claims are forgeable.

**Defend**: pin the accepted algorithm(s) server-side (`algorithms: ['RS256']`); never derive the verification algorithm from the token header; reject `none` explicitly and case-insensitively.

### J2. RS256 -> HS256 key confusion

**Reach**: the verifier publishes its RSA *public* key (a JWKS endpoint or a docs page) and uses a permissive verify call that will accept a symmetric algorithm.

**Confirm**: re-sign the token with HMAC-SHA256 using the PUBLIC key bytes as the HMAC secret. A verifier that switches to HS256 (because the token said so) validates the HMAC with the very public key it publishes, since one "verify with this key" call served both families.

```text
forged = HS256( base64url(header{"alg":"HS256"}) + "." + base64url(payload),
                key = <the server's PEM public key, verbatim bytes> )
```

**Defend**: bind each key to a single algorithm family; use a verify API that takes an explicit algorithm allowlist; never feed an RSA public key into an HMAC verifier.

### J3. Weak HMAC secret cracking

**Reach**: tokens are HS256-signed with a low-entropy or default secret (`secret`, `changeme`, a short passphrase, a framework default).

**Confirm**: the signature is an offline oracle. Run a wordlist against the captured token until a candidate secret reproduces the signature. (General-purpose JWT-cracking tools and `hashcat` mode 16500 do this; point them at a local wordlist, never a live service.)

```text
captured_jwt  +  local_wordlist  ->  recovered HMAC secret  ->  forge arbitrary claims
```

**Defend**: use a >= 256-bit random secret for HS* algorithms, or prefer RS256/ES256 so there is no shared secret to crack; store the secret in a secrets manager and rotate on any suspicion of exposure.

### J4. `kid` / `jku` / `x5u` header injection

**Reach**: the verifier uses an attacker-influenced header field to LOCATE the verification key - `kid` as a filesystem path or DB lookup key, or `jku` / `x5u` as a URL to fetch the key set.

**Confirm**:

- `kid` path traversal to a predictable file whose contents the attacker knows or controls (then sign with those contents), or to an empty/static file paired with a weak verifier.
- `kid` SQL or command injection when the lookup is an unparameterized query or shell call.
- `jku` / `x5u` pointed at the attacker's JWKS so the verifier fetches an attacker public key and validates the attacker's own signature.

```text
{"alg":"RS256","kid":"../../../../etc/hostname","typ":"JWT"}
{"alg":"RS256","kid":"key1' UNION SELECT 'attacker-known-key' --","typ":"JWT"}
{"alg":"RS256","jku":"https://attacker.example/jwks.json","typ":"JWT"}
```

**Defend**: never resolve keys from token-controlled input; pin `kid` to an internal allowlist of known key IDs; if `jku` / `x5u` is supported at all, allowlist the host to your own issuer and ignore any other value.

### J5. Claim-validation gaps (exp / nbf / iss / aud)

**Reach**: the verifier checks the signature but not the registered claims.

**Confirm**: replay an expired token (no `exp` check), present a token minted for a different audience (`aud` not checked, so a token issued for service A is accepted by service B), or a token from an untrusted issuer (`iss` not pinned). A `nbf` far in the future combined with no validation can also confuse downstream logic.

**Defend**: validate `exp`, `nbf`, `iss`, and `aud` on every request with a small clock-skew tolerance; reject any token whose `aud` is not this resource server and whose `iss` is not the pinned issuer.

### J6. Token leakage and lifetime

**Reach**: long-lived bearer tokens stored or transmitted where they leak - `localStorage`, URLs / query strings (then `Referer` headers and access logs), or non-`HttpOnly` cookies.

**Confirm**: a token readable by any in-page script (XSS), a token in a `Referer` header sent to a third party, or a token captured from a server log is replayable for its full lifetime from anywhere.

**Defend**: short-lived access tokens (5-15 min) plus rotating refresh tokens with reuse detection; `HttpOnly` + `Secure` + `SameSite` cookies, never `localStorage`; never place tokens in URLs; consider sender-constrained tokens (DPoP / mTLS). The replay-binding mechanics pair with the replay-attack section of [[advanced-attack-patterns]].

---

## OAuth 2.0 / OIDC attacks

OAuth attacks target the *flow* - the redirect, the binding state, the code exchange - rather than a single token's bytes.

### O1. `redirect_uri` manipulation / open redirect

**Reach**: the authorization server matches `redirect_uri` loosely (prefix / substring match, wildcard subdomain) or an allowed host itself contains an open redirect.

**Confirm**: coerce a `redirect_uri` that sends the authorization code to an attacker-controlled endpoint.

```text
# loose prefix/substring match accepts an attacker subdomain
https://auth.example/authorize?response_type=code&client_id=app&redirect_uri=https://app.example.attacker.example/cb

# allowed host carries an open redirect that forwards the code onward
https://auth.example/authorize?response_type=code&client_id=app&redirect_uri=https://app.example/out?to=https://attacker.example
```

**Escalate**: the leaked authorization code (or, in the implicit flow, the access token in the fragment) is exchanged or replayed by the attacker for the victim's session.

**Defend**: exact-match `redirect_uri` against a pre-registered allowlist (full string including path); no wildcards; ensure no allowed redirect target contains an open redirect.

### O2. Missing / weak `state` -- CSRF on the callback

**Reach**: the client does not bind the authorization request to the user's session with an unguessable `state` value.

**Confirm**: the attacker starts a flow, captures their own authorization `code`, then tricks a victim into hitting the client callback with it - linking the attacker's identity to the victim's session (login CSRF / account fixation).

```text
# victim is induced to load the attacker's pre-captured callback
https://app.example/oauth/callback?code=<attacker-code>&state=<absent-or-static>
```

**Defend**: generate a random `state`, bind it to the session, and reject any callback whose `state` does not match. For OIDC, also generate and validate `nonce` to bind the ID token to the originating request.

### O3. PKCE downgrade / bypass

**Reach**: a public client relies on PKCE, but the authorization server does not *enforce* `code_challenge`, or the token endpoint accepts an exchange missing `code_verifier`.

**Confirm**: omit `code_challenge` from the authorization request, or send the code exchange without `code_verifier`. If tokens are still issued, a stolen authorization code is usable without the verifier, so PKCE provided no protection.

```text
# token exchange that should fail if PKCE were enforced, but succeeds
POST /oauth/token
grant_type=authorization_code&code=<stolen-code>&client_id=app&redirect_uri=https://app.example/cb
# (no code_verifier sent)
```

**Defend**: the authorization server must require `code_challenge` for public clients and reject any token request whose `code_verifier` does not hash (S256) to the stored `code_challenge`.

### O4. Authorization-code injection / replay

**Reach**: the token endpoint does not bind the code to the client that requested it, or accepts a code more than once.

**Confirm**: inject a code obtained in one context into another client's session (code injection), or replay a single code twice and observe a second token issuance.

**Defend**: codes are single-use, short-lived (<= 60s), and bound to `client_id` + `redirect_uri` + the PKCE challenge; revoke the entire grant on any second use of a code.

### O5. IdP mix-up / scope escalation

**Reach**: a multi-IdP client does not track WHICH issuer a given response came from; or scopes are not re-checked at the resource server.

**Confirm**: redirect an authorization response to the wrong issuer's token endpoint so the client sends the code (and its client secret) to the attacker-influenced IdP (mix-up); or present a token whose granted scope was silently widened because the resource server trusts the token's self-asserted `scope` claim without policy.

**Defend**: pin the issuer per authorization request and validate the `iss` in the response (RFC 9207, OAuth 2.0 Authorization Server Issuer Identification); enforce scope-to-resource policy at the resource server, never trusting a self-asserted scope claim alone.

---

## Standards mapping

| Vector | OWASP WSTG | CWE | OWASP Top 10 (2021) |
|--------|-----------|-----|---------------------|
| JWT `alg:none` / key confusion | WSTG-SESS-10 | CWE-347 | A02 |
| Weak HMAC secret | WSTG-SESS-10 | CWE-326 / CWE-521 | A02 |
| `kid` / `jku` / `x5u` injection | WSTG-SESS-10 | CWE-345 / CWE-918 | A07 |
| Claim-validation gaps | WSTG-SESS-10 | CWE-287 / CWE-613 | A07 |
| Token leakage and lifetime | WSTG-SESS-04 | CWE-522 / CWE-200 | A07 |
| `redirect_uri` / open redirect | WSTG-CLNT-04 | CWE-601 | A01 |
| Missing / weak `state` (CSRF) | WSTG-SESS-05 | CWE-352 | A01 |
| PKCE downgrade / code injection | WSTG-ATHZ-05 | CWE-294 / CWE-310 | A07 |
| IdP mix-up / scope escalation | WSTG-ATHZ-05 | CWE-285 | A01 |

These identifiers feed [[pentest-reporting]] (for the finding write-up) and the cross-framework coverage matrix.
