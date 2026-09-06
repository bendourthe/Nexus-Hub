---
name: ios-app-security-review
description: "Review iOS apps for keychain misuse, ATS exceptions, URL scheme hijack, and leftover debug entitlements. Use this skill whenever the user says \"iOS appsec review\", \"ATS exception audit\", \"keychain accessibility\", \"URL scheme hijack\", or wants a MASVS-style iOS pass. SKIP, do NOT use for, Android APK review, or jailbreak exploit development."
summary_l0: "Review iOS apps for keychain ATS URL schemes and debug entitlements"
overview_l1: "This skill reviews iOS binaries and source you are allowed to inspect: ATS, keychain classes, custom URL schemes, and entitlements. Trigger phrases: iOS appsec review, ATS exception audit, keychain accessibility, URL scheme hijack."
nist_csf: [PR.DS, ID.RA]
---

# iOS App Security Assessment

iOS is not 'secure by default' once ATS is punched full of holes and the keychain is AfterFirstUnlock for a refresh token.

## When to Use This Skill

Use this skill when:

- An IPA or iOS source is in scope
- ATS exceptions proliferate
- A URL scheme opens authenticated state

Do NOT use this skill when:

- The app is Android
- The user wants a jailbreak toolchain

**Trigger phrases**: "iOS appsec review", "ATS exception audit", "keychain accessibility", "URL scheme hijack"

## Instructions

### Step 1: Read entitlements and Info.plist

Debug, get-task-allow, ATS exceptions, and URL schemes.

### Step 2: Classify keychain items

Accessibility and access groups. Long-lived tokens need the tightest class you can survive.

### Step 3: Test URL schemes and universal links

Unvalidated parameters into authenticated screens are findings.

### Step 4: Check local storage and logs

Files in caches, screenshots, and os_log of secrets.

### Step 5: Map to MASVS-iOS

Same as Android: controls, not vibes.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| App Store review already covered security | App Store review is not your threat model. |
| Keychain means it is safe | Keychain with kSecAttrAccessibleAlways is a speed bump. |
| ATS exceptions are temporary | Temporary exceptions become the production network profile. Calendar them. |

## Verification

- [ ] ATS exceptions listed
- [ ] Keychain accessibility recorded for tokens
- [ ] URL schemes tested or marked N/A

## Related Skills

- [[android-static-app-analysis]] -- sibling platform static review
- [[mobile-tls-pinning-bypass-assessment]] -- when ATS and pinning interact

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
