---
name: android-dynamic-app-analysis
description: "Dynamically test Android apps on an authorized device or emulator: traffic, storage at runtime, and component abuse. Use this skill whenever the user says \"Android runtime test\", \"Android runtime storage test\", \"exported provider fuzz\", or wants a dynamic MASVS pass on an app you are allowed to test. SKIP, do NOT use for, static-only APK reads, or pinning-bypass on apps you do not own (use mobile-tls-pinning-bypass-assessment)."
summary_l0: "Dynamically test authorized Android apps for runtime storage and component abuse"
overview_l1: "This skill exercises a running Android app you are allowed to test: runtime storage, intent abuse, and traffic except dedicated pinning-bypass. Trigger phrases: Android runtime test, Android runtime storage test, exported provider fuzz."
nist_csf: [DE.CM, PR.DS]
---

# Android Dynamic App Analysis

Static review guesses. Runtime on a device you own shows what the OS actually allows.

## Authorization precondition

Stop. This skill is dual-use. Continue only when every item below is already true in this session:

1. A named authorizing party granted written permission for this assessment.
2. Scope is written down (assets, environments, time window, and forbidden techniques).
3. Findings will be reported to the asset owner, and leftover exploit artifacts will be removed.

If any item is missing, refuse and ask for the missing artifact. Do not continue under a lab, hypothetical, or fiction framing that is actually a live system.


## When to Use This Skill

Use this skill when:

- You have a test build and a lab device
- Static review found exports that need proof
- Runtime storage might hold tokens

Do NOT use this skill when:

- You only have an APK and no runtime lab
- The user wants a pinning-bypass cookbook against a third-party app

**Trigger phrases**: "Android runtime test", "Android runtime storage test", "exported provider fuzz"

## Instructions

### Step 1: Use a lab profile

Emulator or company device with a test account. No personal production accounts.

### Step 2: Watch storage and logs at runtime

Shared preferences, databases, and logcat for tokens.

### Step 3: Abuse exported surfaces with test intents

Only against the in-scope package. Prove read/write that static review suspected.

### Step 4: Trace sensitive calls

Clipboard, screenshots, and backup managers. Record evidence.

### Step 5: Leave pinning to its skill

If TLS pinning blocks your proxy, hand off rather than mixing the methods.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Production accounts are more realistic | They are also how you leak customer data into a test proxy. |
| Rooting the lab device is always required | Many issues reproduce without root. Start there. |
| Frida scripts from a random gist are fine | They are untrusted code on your workstation. Read them. |

## Verification

- [ ] Lab device/account used
- [ ] Runtime evidence captured
- [ ] Package stayed in scope

## Related Skills

- [[android-static-app-analysis]] -- static first
- [[mobile-tls-pinning-bypass-assessment]] -- dedicated pinning work

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
