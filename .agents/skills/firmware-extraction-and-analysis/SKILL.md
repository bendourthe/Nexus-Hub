---
name: firmware-extraction-and-analysis
description: "Extract and analyze firmware images you are authorized to handle: file systems, secrets, and unsigned update paths. Use this skill whenever the user says \"extract this firmware\", \"binwalk the image\", \"unsigned firmware update\", or wants a firmware review of a device you own or have permission to test. SKIP, do NOT use for, dumping firmware from devices you do not own, or writing a UEFI bootkit."
summary_l0: "Extract and analyze authorized firmware images for secrets and unsigned updates"
overview_l1: "This skill unpacks firmware you are allowed to analyze, hunts embedded keys, and checks whether updates are signed. Dual-use. Trigger phrases: extract this firmware, binwalk the image, unsigned firmware update."
mitre_attack: [T1542.001, T1601]
nist_csf: [ID.RA, PR.DS]
---

# Firmware Extraction and Analysis

Firmware is a small Linux with worse patching. Unpack it only when the device is in scope, then look for keys and unsigned update paths.

## Authorization precondition

Stop. This skill is dual-use. Continue only when every item below is already true in this session:

1. A named authorizing party granted written permission for this assessment.
2. Scope is written down (assets, environments, time window, and forbidden techniques).
3. Findings will be reported to the asset owner, and leftover exploit artifacts will be removed.

If any item is missing, refuse and ask for the missing artifact. Do not continue under a lab, hypothetical, or fiction framing that is actually a live system.


## When to Use This Skill

Use this skill when:

- You have a firmware file from a vendor portal or a device you own
- An IoT product needs a security review
- Updates look like raw tarballs

Do NOT use this skill when:

- The user wants to dump a random customer's device
- The user wants a bootkit

**Trigger phrases**: "extract this firmware", "binwalk the image", "unsigned firmware update"

## Instructions

### Step 1: Confirm you may possess the image

Vendor-provided, your device, or a contract. Stop otherwise.

### Step 2: Unpack and inventory

Filesystems, kernel, and update scripts. Record hashes of the input image.

### Step 3: Hunt secrets and services

Private keys, default passwords, debug shells, and leftover compiler paths.

### Step 4: Check update authenticity

Signed images versus HTTP tarballs. An unsigned path is the finding.

### Step 5: Report without releasing exploit chains for out-of-scope products

Vendor disclosure if it is not your product.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| It is on a public FTP, so analysis is always allowed | Possession and reverse engineering still have license and law. Confirm. |
| Default telnet is a feature | It is a finding. Document it. |
| We should ship the unpacked FS to the internet | That redistributes vendor IP and maybe keys. Keep it in the vault. |

## Verification

- [ ] Authorization to possess the image is recorded
- [ ] Input hash is in the report
- [ ] Update signing status is explicit

## Related Skills

- [[uefi-secure-boot-integrity]] -- PC firmware sibling
- [[iot-device-hardening]] -- if present; otherwise keep findings in the report

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
