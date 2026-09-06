---
name: tls-certificate-lifecycle
description: "Run TLS certificate issuance, rotation, pinning policy, and expiry monitoring without surprise outages. Use this skill whenever the user says \"certificate expiry monitoring\", \"rotate TLS certs\", \"ACME issuance\", \"mTLS service identity\", or wants to stop a 2 a.m. expiry outage. SKIP, do NOT use for, JWT key confusion, or CT typosquat hunting (use cert-transparency-and-typosquat-monitoring)."
summary_l0: "Issue rotate and monitor TLS certificates including mTLS identities"
overview_l1: "This skill runs the certificate as a production object: issuance, inventory, rotation, and expiry pages, including mTLS. Trigger phrases: certificate expiry monitoring, rotate TLS certs, ACME issuance, mTLS service identity."
d3fend_techniques: [D3-TLSC]
nist_csf: [PR.DS, DE.CM]
---

# TLS and Certificate Lifecycle

Certificates expire on a calendar, not on a sprint. If nobody owns the inventory, the outage owns you.

## When to Use This Skill

Use this skill when:

- A cert expired in production
- mTLS identities are copied as files on disk
- Nobody can list every hostname that needs a cert

Do NOT use this skill when:

- The user wants CT lookalike alerts
- The user wants JWT alg tests

**Trigger phrases**: "certificate expiry monitoring", "rotate TLS certs", "ACME issuance", "mTLS service identity"

## Instructions

### Step 1: Inventory every listener

Load balancers, ingress, mail, VPN, and sidecar mTLS. Include the ones in forgotten accounts.

### Step 2: Centralize issuance

ACME or enterprise PKI with an owner. Copy-pasted PFX files on shares are findings.

### Step 3: Rotate automatically and prove it

A staging job that renews at 30 days and a canary that fails if the presented serial is stale.

### Step 4: Treat mTLS like production identity

SPIFFE/SPIRE or short-lived workload certs beat a five-year server cert in a secret store.

### Step 5: Page on expiry, not on Twitter

Synthetic checks against the public hostname and the private ones.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Cloudfront will renew it | Until the alternate domain name you added last year. Inventory beats assumptions. |
| Pinning all certs is more secure | Pinning leaf certs is how you cause your own outage. Pin CAs with a backup, or pin SPKI with a rotation plan. |
| Wildcard certs simplify ops | They also simplify attacker reuse after one leak. Split where you can. |

## Verification

- [ ] Inventory lists every listener sampled
- [ ] A renewal job exists with an owner
- [ ] Expiry is monitored on a synthetic check

## Related Skills

- [[cert-transparency-and-typosquat-monitoring]] -- CT watching is brand defense, not your own cert ops
- [[key-management-and-hsm-integration]] -- private keys for issuance belong in HSM/KMS

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
