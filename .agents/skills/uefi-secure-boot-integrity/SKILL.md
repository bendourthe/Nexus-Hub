---
name: uefi-secure-boot-integrity
description: "Verify UEFI Secure Boot, measured boot, and bootloader integrity against unauthorized firmware implants. Use this skill whenever the user says \"Secure Boot verification\", \"UEFI integrity\", \"bootkit detection\", \"dbx revocation\", or wants to know if a fleet still trusts a broken bootloader. SKIP, do NOT use for, writing bootkits, or TPM attestation policy (use tpm-measured-boot-attestation)."
summary_l0: "Verify UEFI Secure Boot dbx and bootloader integrity on a fleet"
overview_l1: "This skill checks that Secure Boot is on, that dbx is current, and that bootloaders match a known set. Trigger phrases: Secure Boot verification, UEFI integrity, bootkit detection, dbx revocation."
mitre_attack: [T1542.001, T1553.006]
nist_csf: [PR.DS, DE.CM]
---

# UEFI Bootkit and Secure Boot Integrity

If Secure Boot is off, every kernel check is theater. If dbx is old, yesterday's trusted bootloader is today's implant path.

## When to Use This Skill

Use this skill when:

- A fleet might have Secure Boot disabled
- A bootkit is in the threat model
- dbx has not been updated since imaging

Do NOT use this skill when:

- The user wants to author a bootkit
- The user wants to write TPM attestation policies only

**Trigger phrases**: "Secure Boot verification", "UEFI integrity", "bootkit detection", "dbx revocation"

## Instructions

### Step 1: Inventory firmware state

Secure Boot on/off, setup mode, and owner. Off is a finding, not a maybe.

### Step 2: Check db/dbx freshness

Revoked bootloaders should be in dbx. An image from 2018 is a finding.

### Step 3: Compare bootloader hashes to a known-good

Unexpected loaders need an owner. Signed but unknown is still unknown.

### Step 4: Look for leftover test keys

PK/KEK in setup mode or vendor test certs in production.

### Step 5: Hand off measured-boot claims to TPM skill

Event logs are the next layer, not this one.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| We turned it off to install a driver once | Then it stayed off. That is the incident. |
| OEM Secure Boot is enough forever | dbx updates exist because signed malware existed. Patch them. |
| Linux means we do not care | shim and grub are bootkits' favorite living-off-the-land. |

## Verification

- [ ] Secure Boot state inventoried
- [ ] dbx age recorded
- [ ] Unknown bootloaders listed

## Related Skills

- [[tpm-measured-boot-attestation]] -- next layer
- [[firmware-extraction-and-analysis]] -- device firmware dumps

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
