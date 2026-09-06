---
name: cryptographic-control-audit
description: "Audit deployed cryptography for broken algorithms, nonce reuse, homemade constructions, and key-handling failures. Use this skill whenever the user says \"crypto audit\", \"nonce reuse hunt\", \"find 3DES and RC4\", \"homemade CBC\", or wants a review of cryptographic controls in code and config. SKIP, do NOT use for, designing a new protocol, or PQC roadmaps (use post-quantum-cryptography-migration)."
summary_l0: "Audit deployed crypto for broken algorithms nonce reuse and homemade constructions"
overview_l1: "This skill reviews code and config for cryptographic malpractice: outdated ciphers, reused nonces, and invented protocols. Trigger phrases: crypto audit, nonce reuse hunt, find 3DES and RC4, homemade CBC."
d3fend_techniques: [D3-CH]
nist_csf: [ID.RA, PR.DS]
---

# Cryptographic Control Audit

Most 'crypto bugs' are protocol and key-handling bugs. Read the call sites, not the marketing of the library.

## When to Use This Skill

Use this skill when:

- A review must opine on cryptography
- Old ciphers still appear in configs
- A service rolls its own tokens

Do NOT use this skill when:

- The user wants a PQC multi-year plan
- The user wants to invent a cipher

**Trigger phrases**: "crypto audit", "nonce reuse hunt", "find 3DES and RC4", "homemade CBC"

## Instructions

### Step 1: List every cryptographic call site

TLS configs, token mints, password hashes, disk crypto, and 'custom' signing.

### Step 2: Ban the museum

MD5/SHA1 for security, DES/3DES/RC4, 1024-bit RSA, ECB, and static IVs. Exceptions need expiry dates.

### Step 3: Hunt nonce and IV reuse

CTR/GCM with a static nonce is a class break. Check backups of the counter.

### Step 4: Reject homemade transports

Encrypted blobs with a password in the query string, or HMAC then decrypt without verify.

### Step 5: Write findings as remove-or-justify

Each item has an owner and a library-supported replacement.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| It is only for internal traffic | Internal traffic is what attackers live on after phishing. |
| The nonce is random enough | Show the uniqueness budget. Random 32-bit nonces collide. |
| We hashed the password with SHA256, so we are modern | SHA256 is not a password KDF. Use Argon2/bcrypt/scrypt. |

## Verification

- [ ] Call-site inventory exists
- [ ] Every banned algorithm has a ticket or a dated exception
- [ ] GCM/CTR uniqueness is argued in writing

## Related Skills

- [[post-quantum-cryptography-migration]] -- forward-looking; this skill is the as-is audit
- [[encryption-at-rest-design]] -- findings often land there

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
