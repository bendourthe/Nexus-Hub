---
name: slsa-provenance-and-sigstore-verification
description: "Verify SLSA provenance and Sigstore signatures so deployed artifacts map to a known build, not to a USB stick. Use this skill whenever the user says \"verify SLSA provenance\", \"cosign verify\", \"Sigstore policy\", \"rebuild the artifact\", or wants admission control that checks provenance. SKIP, do NOT use for, SSVC ticket ordering, or designing envelope encryption."
summary_l0: "Verify SLSA provenance and Sigstore signatures before admitting artifacts"
overview_l1: "This skill checks that images and binaries carry provenance and signatures you can verify at admit time. Trigger phrases: verify SLSA provenance, cosign verify, Sigstore policy, rebuild the artifact."
d3fend_techniques: [D3-SCI]
nist_csf: [PR.DS, ID.SC]
---

# Build Provenance Verification (SLSA/Sigstore)

A scanned unsigned blob is still an untrusted blob. Provenance says who built it and from what. Check it before it runs.

## When to Use This Skill

Use this skill when:

- Admission controllers allow any image
- A supply-chain incident needs 'what ran'
- Releases are copied by hand

Do NOT use this skill when:

- The user wants SSVC ranking
- The user wants KMS envelope design

**Trigger phrases**: "verify SLSA provenance", "cosign verify", "Sigstore policy", "rebuild the artifact"

## Instructions

### Step 1: Require signatures at admit

Cosign/Sigstore or your enterprise PKI. Unsigned fails closed in prod.

### Step 2: Require provenance attestations

SLSA predicate with builder identity and source repo. A signature on a mystery blob is not enough.

### Step 3: Pin the builder

GitHub Actions / internal builder identities. A signature from 'some guy's laptop' is a finding.

### Step 4: Keep verification offline-capable

Cache trust roots. Do not make deploy depend on a best-effort network call without a fallback policy.

### Step 5: Record what was admitted

Digest, provenance, and who signed. That is the incident-response breadcrumb.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| We already scan the image | Scanners do not prove origin. Provenance does. |
| Developers will hate failed deploys | They will hate production running an unknown blob more. Start in warn, then enforce. |
| Rebuilding locally is provenance | A local rebuild without identity is a hope. Use a named builder. |

## Verification

- [ ] Prod admit path verifies signatures
- [ ] Provenance predicate is required
- [ ] Builder identity is pinned

## Related Skills

- [[dependency-security-audit]] -- library CVEs vs artifact origin
- [[vulnerability-prioritization-with-ssvc]] -- when a signed artifact is still vulnerable

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
