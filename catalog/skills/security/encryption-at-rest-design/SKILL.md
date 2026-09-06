---
name: encryption-at-rest-design
description: "Design application-level and volume-level encryption at rest with key hierarchy, envelope encryption, and recovery. Use this skill whenever the user says \"envelope encryption\", \"encrypt the database at rest\", \"customer-managed keys\", \"field-level encryption\", or wants more than a checkbox on a cloud disk. SKIP, do NOT use for, TLS handshake debugging (use tls-certificate-lifecycle), or JWT alg attacks."
summary_l0: "Design envelope and field-level encryption at rest with a key hierarchy"
overview_l1: "This skill designs encryption at rest that would still hold if a disk image leaked: envelope keys, CMK/HSM roots, and recovery. Trigger phrases: envelope encryption, encrypt the database at rest, customer-managed keys, field-level encryption."
d3fend_techniques: [D3-FE]
nist_csf: [PR.DS, PR.AA]
---

# Applied Encryption at Rest

Disk encryption stops a stolen laptop. It does not stop a stolen database backup. Put keys where the backup is not.

## When to Use This Skill

Use this skill when:

- Backups leave the production account
- A compliance control asks for encryption at rest and the answer is 'EBS default'
- Regulated fields need a separate key

Do NOT use this skill when:

- The task is TLS cert rotation
- The task is JWT verification bugs

**Trigger phrases**: "envelope encryption", "encrypt the database at rest", "customer-managed keys", "field-level encryption"

## Instructions

### Step 1: Separate volume encryption from application encryption

Volume crypto is table stakes. Application envelope crypto protects backups and replicas.

### Step 2: Draw the key hierarchy

DEK per object or per table, KEK in an HSM/KMS, root access in a break-glass account. No DEKs in the repo.

### Step 3: Define rotation and recovery

A lost CMK without escrow is ransomware you run on yourself. Document dual control.

### Step 4: Place field-level crypto only where it pays

Primary search columns you cannot encrypt without a searchable scheme. Do not encrypt everything and then log it in plaintext.

### Step 5: Test the failure

Revoke a key in staging and watch the app fail closed, not skip decryption.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Provider default disk encryption is the control | Anyone with the VM role can read the volume. That is not backup protection. |
| We can store the DEK next to the ciphertext 'encrypted' | If the wrapping key is in the same blob, you have obfuscation. |
| Rotate by rewriting all rows this weekend | That is an outage plan. Use envelope rewrap. |

## Verification

- [ ] Key hierarchy diagram exists
- [ ] DEKs are not in git
- [ ] A staging key-revoke test failed closed

## Related Skills

- [[key-management-and-hsm-integration]] -- this skill consumes KMS/HSM; that one operates them
- [[tls-certificate-lifecycle]] -- in-transit is a different control

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
