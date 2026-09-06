---
name: tpm-measured-boot-attestation
description: "Use TPM quotes and measured-boot event logs to attest that a host booted a known set of components. Use this skill whenever the user says \"TPM quote verification\", \"measured boot PCR\", \"remote attestation policy\", or wants to bind access to a PCR policy. SKIP, do NOT use for, Secure Boot dbx inventory (use uefi-secure-boot-integrity), or HSM application keys."
summary_l0: "Attest hosts with TPM quotes and measured-boot PCR policies"
overview_l1: "This skill verifies TPM quotes against a PCR policy and event log so access can depend on a known boot. Trigger phrases: TPM quote verification, measured boot PCR, remote attestation policy."
d3fend_techniques: [D3-TBPA]
nist_csf: [PR.DS, PR.AA]
---

# TPM Measured-Boot Attestation

Secure Boot is local opinion. Attestation is a verifier's opinion. If nobody verifies the quote, the TPM is a paperweight.

## When to Use This Skill

Use this skill when:

- You need remote proof of boot integrity
- BitLocker/PCR bindings are unexplained
- A zero-trust device signal should include boot

Do NOT use this skill when:

- The user only wants Secure Boot on/off
- The user wants to store app DEKs in an HSM

**Trigger phrases**: "TPM quote verification", "measured boot PCR", "remote attestation policy"

## Instructions

### Step 1: Collect event logs and quotes in a lab first

Understand PCR0-7 meaning on your OEM before you enforce.

### Step 2: Write a policy of allowed measurements

Golden PCR values or replayed event logs. OEM firmware updates will change them; plan that.

### Step 3: Verify signatures on quotes

AK certs, nonce freshness, and clock. A replayed quote is not attestation.

### Step 4: Bind an action

Issue a device cert, allow ZTNA, or unlock a volume. Attestation without an action is a report.

### Step 5: Plan firmware updates

A policy that cannot be updated is how you brick a fleet after a BIOS patch.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| PCR values will never change | They change on the first firmware update. Budget for it. |
| We can skip the nonce | Then an old quote works forever. |
| TPM is present, so we are attested | Presence is not verification. |

## Verification

- [ ] Quote verification uses a nonce
- [ ] Policy names allowed measurements
- [ ] Firmware-update path is documented

## Related Skills

- [[uefi-secure-boot-integrity]] -- local boot controls
- [[ztna-broker-deployment]] -- a place to consume device signals

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
