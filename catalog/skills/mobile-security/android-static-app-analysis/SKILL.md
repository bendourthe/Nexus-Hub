---
name: android-static-app-analysis
description: "Statically review Android APKs and source for exported components, insecure storage, and secret leakage. Use this skill whenever the user says \"APK static analysis\", \"exported Activity review\", \"Android debuggable flag\", \"secrets in strings.xml\", or wants a MASVS-style static pass. SKIP, do NOT use for, runtime instrumentation (use android-dynamic-app-analysis), or iOS binaries."
summary_l0: "Statically review Android APKs for exported components and leaked secrets"
overview_l1: "This skill reads the APK and source: manifest exports, backup flags, storage, and embedded secrets, mapped to MASVS. Trigger phrases: APK static analysis, exported Activity review, Android debuggable flag, secrets in strings.xml."
nist_csf: [ID.RA, PR.DS]
---

# Android Static App Analysis

The manifest is the attack surface. If it is exported and unprotected, the rest of the code review is already late.

## When to Use This Skill

Use this skill when:

- An APK or Android source is in scope
- A release still has android:debuggable
- Secrets show up in resources

Do NOT use this skill when:

- The user wants Frida runtime work
- The binary is iOS

**Trigger phrases**: "APK static analysis", "exported Activity review", "Android debuggable flag", "secrets in strings.xml"

## Instructions

### Step 1: Read the merged manifest

Exported activities, receivers, providers, and custom permissions. Unprotected exports are findings.

### Step 2: Check build flags

debuggable, backup, cleartext traffic, and network security config.

### Step 3: Hunt secrets

strings, BuildConfig, and mispackaged .env files. Treat as live until rotated.

### Step 4: Review local storage

MODE_WORLD_READABLE leftovers, unencrypted SQLite, and logs of PII.

### Step 5: Map to MASVS controls

Each finding cites a MASVS requirement so the report is not a pile of lint.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| It is not exported in the activity we use | The merged manifest includes library manifests. Read the merge. |
| Obfuscation hides secrets | Obfuscation hides names, not API keys in strings. |
| We will fix storage in the next app rewrite | The current APK is what is shipped. File it. |

## Verification

- [ ] Merged manifest reviewed
- [ ] Debuggable/backup flags recorded
- [ ] Findings map to MASVS IDs

## Related Skills

- [[android-dynamic-app-analysis]] -- runtime confirms what static suspects
- [[mobile-malware-family-triage]] -- malware APKs still start with static

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
