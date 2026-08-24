## Attacker-Perspective: What the Auth Design Must Withstand

Every control above exists because a specific attack would otherwise succeed. This section flips to the attacker's view of the JWT and OAuth/OIDC surface so the design can be audited against it. It is offensive knowledge in service of a hardened verifier, not a standalone engagement: use it only inside an authorized assessment with documented scope, and keep every probe benign and pointed at reserved placeholders (`auth.example`, `attacker.example`). The concrete malformed-token structures, key-confusion mechanics, and flow-manipulation sequences live in [`references/auth-attack-methodology.md`](references/auth-attack-methodology.md) so this body stays within the size norm; the checklist below is the audit summary.

### JWT attack surface

A verifier is sound only if it pins the algorithm and binds the signature to a key the server chose, not one the token names. Audit for each of:

- **`alg: none` acceptance** - the verifier trusts the header's algorithm and accepts an unsigned token. Defense: pin `algorithms` server-side and reject `none` case-insensitively.
- **RS256 -> HS256 key confusion** - the token is re-signed with HMAC using the public RSA key as the secret, and a permissive verify call accepts it. Defense: bind each key to one algorithm family; pass an explicit algorithm allowlist to the verifier.
- **Weak HMAC secret** - an HS256 secret such as `secret` / `changeme` is recovered offline from a captured token. Defense: a >= 256-bit random secret, or RS256/ES256 so there is no shared secret.
- **`kid` / `jku` / `x5u` injection** - the verifier resolves its key from an attacker-influenced header (path traversal, SQLi, or a URL to the attacker's JWKS). Defense: never locate keys from token-controlled input; allowlist `kid` to known IDs and `jku` / `x5u` to your own issuer.
- **Claim-validation gaps** - signature verified but `exp` / `aud` / `iss` / `nbf` are not, so expired or cross-audience tokens replay. Defense: validate every registered claim on every request.
- **Token leakage and lifetime** - long-lived bearer tokens in `localStorage`, URLs, or non-`HttpOnly` cookies leak via XSS, referrers, and logs. Defense: short-lived access tokens, rotating refresh tokens with reuse detection, and `HttpOnly` + `Secure` + `SameSite` cookies.

### OAuth 2.0 / OIDC attack surface

OAuth attacks target the flow (the redirect, the binding state, the code exchange), not a single token. Audit for each of:

- **`redirect_uri` manipulation** - loose matching sends the authorization code to an attacker endpoint. Defense: exact-match against a pre-registered allowlist, no wildcards, no allowed target carrying an open redirect.
- **Missing / weak `state` (and OIDC `nonce`)** - the callback is not bound to the user's session, enabling login CSRF / code fixation. Defense: a random `state` bound to the session and rejected on mismatch; validate `nonce`.
- **PKCE downgrade** - a public client's `code_challenge` is not enforced, or the token endpoint accepts an exchange missing `code_verifier`. Defense: require `code_challenge` for public clients and reject any exchange whose verifier does not hash (S256) to the challenge.
- **Authorization-code injection / replay** - codes are not single-use or not bound to the requesting client. Defense: single-use, short-lived codes bound to `client_id` + `redirect_uri` + the PKCE challenge; revoke the grant on reuse.
- **IdP mix-up / scope escalation** - a multi-IdP client mis-attributes the issuer, or the resource server trusts a self-asserted scope. Defense: pin and validate the issuer per request (RFC 9207); enforce scope-to-resource policy server-side.

Hand every confirmed weakness to `security-review` / `security-patch-advisor` as a concrete control, and write it up via [[pentest-reporting]].
