---
name: post-quantum-cryptography-migration
description: "Plan hybrid post-quantum migration for TLS, signatures, and stored ciphertext without breaking clients. Use this skill whenever the user says \"post-quantum migration\", \"hybrid Kyber TLS\", \"harvest now decrypt later\", \"PQC roadmap\", or wants a crypto inventory for quantum-safe algorithms. SKIP, do NOT use for, day-to-day cert expiry ops, or inventing new primitives."
summary_l0: "Plan hybrid post-quantum TLS and signature migration from a crypto inventory"
overview_l1: "This skill inventories cryptography, flags harvest-now-decrypt-later data, and plans hybrid TLS/signature migration. Trigger phrases: post-quantum migration, hybrid Kyber TLS, harvest now decrypt later, PQC roadmap."
nist_csf: [ID.RA, PR.DS]
---

# Post-Quantum Cryptography Migration

Adversaries record ciphertext today. Migration is a program, not a library bump the week a standard finalizes.

## When to Use This Skill

Use this skill when:

- Long-lived secrets sit on disk
- A vendor asked for a PQC roadmap
- TLS libraries gained hybrid groups and nobody enabled them

Do NOT use this skill when:

- The user wants this week's cert rotation
- The user wants a custom cipher

**Trigger phrases**: "post-quantum migration", "hybrid Kyber TLS", "harvest now decrypt later", "PQC roadmap"

## Instructions

### Step 1: Inventory algorithms and shelf-life

TLS groups, signature algs, VPNs, code-signing, and archived ciphertext. Note how many years the data must stay secret.

### Step 2: Flag harvest-now-decrypt-later stores

Backups and data-in-motion to partners are the first hybrids. Chatty short-lived session keys can wait.

### Step 3: Prefer hybrid, not a flag day

Classical plus ML-KEM so old clients still connect. Measure handshake failures.

### Step 4: Do not roll your own PQC

Use library support and standards. Custom combiners are a finding.

### Step 5: Revisit signatures and PKI

Root lifetimes measured in decades need a plan for PQ signatures, not just TLS groups.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Quantum is 20 years away | Recorded ciphertext does not care. Shelf-life does. |
| We will switch the week NIST says so | Vendors, HSMs, and clients will not. That is how you get an outage. |
| A new XOR combiner is conservative | It is how you get a paper and a breach. Use a standard hybrid. |

## Verification

- [ ] Crypto inventory exists
- [ ] HN-DL stores are identified
- [ ] Hybrid TLS is tested in staging if libraries allow

## Related Skills

- [[tls-certificate-lifecycle]] -- issuance stays classical until you change it on purpose
- [[cryptographic-control-audit]] -- the inventory feeds the audit

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
