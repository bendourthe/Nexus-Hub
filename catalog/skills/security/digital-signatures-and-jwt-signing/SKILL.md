---
name: digital-signatures-and-jwt-signing
description: "Issue and verify digital signatures and JWTs with pinned algorithms, key IDs you control, and replay limits. Use this skill whenever the user says \"sign this JWT correctly\", \"code signing key\", \"detached signature verify\", \"JWS issuance\", or wants issuance that a confused verifier cannot bypass. SKIP, do NOT use for, attacking verifiers (use jwt-header-and-key-confusion-attacks), or HSM racking."
summary_l0: "Issue JWTs and digital signatures with pinned algorithms and controlled kids"
overview_l1: "This skill is the issuer side: JWS/JWT and document signatures with pinned algs, short TTL, and kids that map to your JWKS. Trigger phrases: sign this JWT correctly, code signing key, detached signature verify, JWS issuance."
d3fend_techniques: [D3-CH]
nist_csf: [PR.DS, PR.AA]
---

# Digital Signatures and JWT Signing

Issuing a token is an authorization decision you will live with until it expires. Sign narrowly and briefly.

## When to Use This Skill

Use this skill when:

- You mint JWTs or signed webhooks
- Code-signing is moving out of a shared SMB share
- Callback payloads need non-repudiation

Do NOT use this skill when:

- The task is to attack a verifier
- The task is to install an HSM

**Trigger phrases**: "sign this JWT correctly", "code signing key", "detached signature verify", "JWS issuance"

## Instructions

### Step 1: Pin the algorithm at issue time

RS256/ES256/EdDSA. Never 'none'. Never copy alg from the client.

### Step 2: Publish JWKS you own

Kids are identifiers into that JWKS, not file paths. Rotate by adding then removing.

### Step 3: Minimize claims and TTL

Audience, issuer, expiry, and a unique jti if you need replay control.

### Step 4: Separate signing roles

Access-token signing, refresh, and code-signing keys are not the same key.

### Step 5: Verify with the same pin

The issuer test suite should include the confused-deputy cases as negative tests even though this skill does not attack third parties.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Long-lived JWTs mean fewer logins | They also mean a stolen token is a long-lived badge. Prefer refresh. |
| We can put the private key in the mobile app to sign | Then it is not a private key. Sign on a server or HSM. |
| kid can be the filename | That is how path injection is born. Use opaque ids. |

## Verification

- [ ] Issuer pins alg
- [ ] JWKS is first-party
- [ ] TTL and audience are set on issued tokens

## Related Skills

- [[jwt-header-and-key-confusion-attacks]] -- verifier attacks are the dual of this skill
- [[key-management-and-hsm-integration]] -- the signing key lives there

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
