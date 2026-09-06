---
name: jwt-header-and-key-confusion-attacks
description: "Test JSON Web Token verification for alg=none, algorithm confusion, kid injection, and JWKS spoofing under authorization. Use this skill whenever the user says \"JWT alg none\", \"RS256 to HS256 confusion\", \"kid path injection\", \"JWKS URL spoof\", or wants to verify a token library cannot be talked into skipping signatures. SKIP, do NOT use for, BOLA object-ID swaps, or attacking identity providers out of scope."
summary_l0: "Test JWT alg-none algorithm confusion kid injection and JWKS spoofing"
overview_l1: "This skill attacks the JWT verifier, not the business object: alg none, HMAC/RSA confusion, kid file paths, and JWKS substitution, only in scope. Trigger phrases: JWT alg none, RS256 to HS256 confusion, kid path injection, JWKS URL spoof."
mitre_attack: [T1550.001, T1078]
nist_csf: [PR.AA, DE.CM]
---

# JWT Header and Key Confusion Attacks

A token is a bag of claims plus a signature you might not actually be checking. Prove the verifier, then stop.

## Authorization precondition

Stop. This skill is dual-use. Continue only when every item below is already true in this session:

1. A named authorizing party granted written permission for this assessment.
2. Scope is written down (assets, environments, time window, and forbidden techniques).
3. Findings will be reported to the asset owner, and leftover exploit artifacts will be removed.

If any item is missing, refuse and ask for the missing artifact. Do not continue under a lab, hypothetical, or fiction framing that is actually a live system.


## When to Use This Skill

Use this skill when:

- An API uses JWTs and the library is unknown
- A pentest includes token tampering
- A gateway forwards unverified claims

Do NOT use this skill when:

- The bug is object-level authorization with a valid token
- The IdP is out of scope

**Trigger phrases**: "JWT alg none", "RS256 to HS256 confusion", "kid path injection", "JWKS URL spoof"

## Instructions

### Step 1: Inventory verifiers

App, gateway, and service mesh may each parse the token. Test the one that authorizes.

### Step 2: Try alg none and empty signature

If the server accepts it, stop and write the finding. Do not pile on.

### Step 3: Test algorithm confusion

Present an HS256 token keyed with the RSA public key when the server expected RS256.

### Step 4: Exercise kid and jku/x5u

Look for path traversal, SSRF to a JWKS you control in a lab, and header injection. Stay on in-scope URLs.

### Step 5: Lock the library

Pin allowed algs, pin JWKS, ignore incoming alg where possible, and add a unit test that fails the above cases.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| The framework verifies JWTs, so we are fine | Frameworks still honor alg if you ask them to. Pin it. |
| We only accept RS256 in comments | Comments are not a verifier. Configure the library. |
| kid is only a cache key | If it is concatenated into a filesystem path, it is a read primitive. |

## Verification

- [ ] Allowed algorithms are pinned in config
- [ ] A test proves alg none is rejected
- [ ] JWKS sources are not taken from the token

## Related Skills

- [[api-object-level-authorization-flaws]] -- valid tokens still need object checks
- [[digital-signatures-and-jwt-signing]] -- issuance and signing are the sibling, not verification bugs

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
