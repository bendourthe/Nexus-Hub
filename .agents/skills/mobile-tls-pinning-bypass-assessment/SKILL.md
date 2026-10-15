---
name: mobile-tls-pinning-bypass-assessment
description: "Assess mobile TLS pinning and intercept traffic on apps you are authorized to test, including bypass of pinning in a lab. Use this skill whenever the user says \"bypass certificate pinning on our app\", \"Frida unpin\", \"mobile proxy intercept\", or wants to know whether pinning actually binds to your CA set. SKIP, do NOT use for, intercepting third-party apps without permission, or general Android static review."
summary_l0: "Assess and lab-bypass TLS pinning on authorized mobile apps"
overview_l1: "This skill tests whether mobile pinning is real, then intercepts traffic in a lab you own. Dual-use with a hard authorization gate. Trigger phrases: bypass certificate pinning on our app, Frida unpin, mobile proxy intercept."
nist_csf: [PR.DS, DE.CM]
---

# Mobile Traffic Interception and Pinning Bypass

Pinning that never fails closed is decoration. Prove it on an app you are allowed to break, then fix the pin set.

## Authorization precondition

Stop. This skill is dual-use. Continue only when every item below is already true in this session:

1. A named authorizing party granted written permission for this assessment.
2. Scope is written down (assets, environments, time window, and forbidden techniques).
3. Findings will be reported to the asset owner, and leftover exploit artifacts will be removed.

If any item is missing, refuse and ask for the missing artifact. Do not continue under a lab, hypothetical, or fiction framing that is actually a live system.


## When to Use This Skill

Use this skill when:

- You have written permission to test the app
- A proxy sees TLS errors you need to classify
- Pinning is a release requirement

Do NOT use this skill when:

- The app is a third-party bank or messenger you do not own
- You only needed a static APK read

**Trigger phrases**: "bypass certificate pinning on our app", "Frida unpin", "mobile proxy intercept"

## Instructions

### Step 1: Confirm authorization and lab isolation

Company test build, test account, isolated Wi-Fi. Stop otherwise.

### Step 2: Establish a baseline intercept

System CA vs custom pin. Record whether the app fails closed.

### Step 3: Attempt lab bypass only on the in-scope package

Instrumentation, network-security-config overrides on debug builds, or an official debug flag. Document the method.

### Step 4: Classify the pin

Leaves vs SPKI vs CA. Recommend a pin set that operations can rotate.

### Step 5: Never publish bypasses against unnamed third-party apps

The deliverable is your app's posture.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| If we can unpin it, so can criminals, so we should not pin | Criminals already control the device in that story. Pinning still raises the cost on unmodified devices and on some malware. |
| Debug builds without pinning are equivalent to production | They are not. Test the release flavor. |
| A blog unpin script is in-scope for any APK | Without authorization it is an attack on someone else. |

## Verification

- [ ] Written authorization recorded
- [ ] Fail-closed behavior documented
- [ ] Bypass stayed on the in-scope package

## Related Skills

- [[android-dynamic-app-analysis]] -- broader runtime testing
- [[tls-certificate-lifecycle]] -- what you should pin to

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
