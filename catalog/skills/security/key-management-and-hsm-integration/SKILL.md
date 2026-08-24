---
name: key-management-and-hsm-integration
description: "Operate keys in KMS or HSM with dual control, separation of roles, and no raw key export. Use this skill whenever the user says \"HSM integration\", \"KMS key policy\", \"no export of private keys\", \"dual control key ceremony\", or wants to stop keys living in env files. SKIP, do NOT use for, designing field-level encryption schemas, or TLS expiry monitors."
summary_l0: "Operate KMS and HSM keys with dual control and no raw export"
overview_l1: "This skill puts cryptographic keys in KMS/HSM, writes key policies, and runs ceremonies that do not print PEMs into chat. Trigger phrases: HSM integration, KMS key policy, no export of private keys, dual control key ceremony."
d3fend_techniques: [D3-KBPI]
nist_csf: [PR.AA, PR.DS]
---

# Key Management and HSM Integration

If the application can print the private key, you do not have an HSM. You have a slow filesystem.

## When to Use This Skill

Use this skill when:

- Private keys are in git or env vars
- A KMS policy allows decrypt to the world
- A ceremony is 'email the PEM'

Do NOT use this skill when:

- The user wants envelope-encryption application design only
- The user wants cert expiry paging

**Trigger phrases**: "HSM integration", "KMS key policy", "no export of private keys", "dual control key ceremony"

## Instructions

### Step 1: Classify keys

Root, intermediate, application DEK wrapping, and code-signing are different roles. Do not share them.

### Step 2: Move material into KMS/HSM

Generate inside the module. Import only with a documented exception.

### Step 3: Write deny-export policies

IAM/KMS conditions that forbid GetKey and raw decrypt to humans. Apps decrypt via API, not via file.

### Step 4: Split ceremonies

Two people, two factors, logged. Break-glass keys live in a safe with a paper process.

### Step 5: Audit use, not just creation

Decrypt volume by principal. A silent key is either unused or exfiltrated.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| The env var is in the secret manager, so it is fine | A retrieve-able PEM is still export. Prefer sign/decrypt APIs. |
| Developers need the key to debug | They need a staging key with no production decrypt. That is cheaper than a breach. |
| HSM is too slow | Then wrap DEKs and do bulk crypto in memory. Do not skip the root of trust. |

## Verification

- [ ] Production private keys are non-exportable
- [ ] Key policy is reviewed
- [ ] A dual-control ceremony is documented

## Related Skills

- [[encryption-at-rest-design]] -- uses these keys
- [[digital-signatures-and-jwt-signing]] -- signing keys belong here too

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
