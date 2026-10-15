---
name: identity-threat-detection
description: "Detect identity-based attacks across IdP and SSO logs (Entra ID, Okta, Google Workspace, Active Directory) - impossible travel, MFA fatigue or push bombing, password spraying and brute force, token or session theft, and authentication-process tampering. Make sure to use this skill whenever the user says \"detect account takeover\", \"impossible travel detection\", \"MFA fatigue detection\", \"password spray detection\", \"brute force detection\", \"sign-in anomaly detection\", \"identity threat detection\", or \"Okta/Entra/Azure AD anomalies\", even when they only hand you a sign-in log export and ask what looks wrong. SKIP, do NOT use for: implementing authentication itself (use [[authentication-patterns]]) or cloud resource misconfiguration (use [[cloud-security-posture-detection]])."
summary_l0: "Detect account-takeover patterns in IdP and SSO sign-in logs from the defender seat"
overview_l1: "This skill drives defensive detection of identity-based attacks from IdP and SSO telemetry (Entra ID, Okta, Google Workspace, Active Directory). It teaches a deterministic detection pass over sign-in and audit logs: baseline normal access per identity, then hunt impossible travel, MFA fatigue or push bombing, password spraying and credential-stuffing brute force, token and session theft (impossible-token-reuse, anomalous device or IP for an existing session), and authentication-process tampering (new MFA methods, conditional-access or federation changes, added app credentials). Each pattern is expressed as a concrete log query with a tuned threshold to manage false positives, and every confirmed hit maps to ATT&CK valid-accounts, credential-access, and authentication-modification techniques. The output is a prioritized set of detection findings with the identity, evidence, and a recommended containment handoff; the skill detects and triages only and never weakens authentication or performs the attacks it hunts."
mitre_attack: [T1078, T1556, T1110]
d3fend_techniques: [D3-PA]
nist_csf: [PR.AC, DE.CM, DE.AE]
---

# Identity Threat Detection

Detect identity-based attacks across IdP and SSO logs (Entra ID, Okta, Google Workspace, Active Directory): impossible travel, MFA fatigue, password spraying and brute force, token or session theft, and authentication-process tampering. This is a defender-seat detection workflow; it queries logs and triages findings and never weakens authentication or runs the attacks it hunts.

## When to Use This Skill

- You are handed sign-in or audit-log exports from an identity provider and need to find account-takeover signals.
- An alert suggests impossible travel, a burst of MFA prompts, or repeated failed logins, and you need to confirm or dismiss it.
- You suspect a stolen session or token is being replayed from an unfamiliar device or IP.
- You need to detect password spraying (one password against many accounts) or credential stuffing across the tenant.
- You are auditing for stealthy authentication-process tampering: newly registered MFA methods, conditional-access rule changes, federation or trust changes, or added application credentials.

**When NOT to use:**

- Building or configuring the authentication flow itself (MFA enrollment, OAuth, session design) - use [[authentication-patterns]].
- Detecting misconfigured cloud resources, storage, or IAM policy posture - use [[cloud-security-posture-detection]].
- Pivoting from a confirmed identity compromise into host-to-host movement - hand off to [[lateral-movement-detection]].
- Any request to spray, brute force, phish, or otherwise exercise the attacks against live accounts - out of scope; detection only.

## Instructions

### 1. Scope the data and baseline normal

1. Identify the log sources available (interactive and non-interactive sign-ins, audit/directory-change logs) and the time window.
2. For each identity, baseline normal access: usual countries/ASNs, device IDs, client apps, and working hours. Detection thresholds in later steps are deltas from this baseline.
3. Note privileged identities (admins, service accounts, break-glass) separately; they warrant tighter thresholds.

### 2. Detect impossible travel and geo-velocity anomalies

1. For each identity, order successful sign-ins by time and compute the implied travel speed between consecutive locations.
2. Flag pairs that exceed plausible travel (for example two countries minutes apart) as impossible travel, an indicator of a shared or stolen credential (ATT&CK T1078).
3. Suppress known false positives first: corporate VPN egress, mobile-carrier CGNAT, and cloud-relay IPs. Document the suppression list so it is auditable, not silent.

### 3. Detect MFA fatigue and push bombing

1. Query for a high count of MFA challenges to a single identity in a short window, especially many denies followed by one approve.
2. Flag a rapid sequence of push prompts (push bombing) as an MFA-fatigue attempt against a valid account whose password is already known to the attacker.
3. Correlate the approval that ended the burst with the device and IP that proceeded to sign in; that is the takeover moment.

### 4. Detect password spraying and brute force

1. Spraying signature: many distinct accounts hit with a small number of common passwords from one or few source IPs/ASNs in a window. Pivot on source IP and on failure-reason code, not on a single account (ATT&CK T1110, brute force).
2. Brute force / stuffing signature: a high failed-attempt rate against one account, or reused credential pairs across many accounts.
3. Set a per-window threshold tuned to your tenant size; record the threshold so a reviewer can see why a burst did or did not fire.
4. Flag any spray that produced even one success for immediate containment handoff.

### 5. Detect token and session theft

1. Look for an existing session presenting from a new device, IP, or user-agent without a fresh authentication event (session replay).
2. Flag the same session token or refresh token used from two distinct locations near-simultaneously (impossible token reuse).
3. Correlate token anomalies with any phishing report from [[phishing-analysis-and-defense]] that targeted the same identity.

### 6. Detect authentication-process tampering

1. Hunt directory/audit logs for newly registered MFA methods, especially on an account that just had an anomalous sign-in (attacker persistence).
2. Flag changes to conditional-access policies, federation/trust settings, or identity-provider configuration that weaken enforcement (ATT&CK T1556, modify authentication process).
3. Flag added application or service-principal credentials (new client secrets or certificates) that grant token issuance outside interactive sign-in.

### 7. Prioritize findings and hand off containment

1. For each confirmed detection, write one finding line: identity, pattern, evidence (query + matched events), baseline delta, and the ATT&CK mapping.
2. Rank by blast radius (privileged identity, success achieved, persistence established) ahead of unsuccessful noise.
3. Recommend the containment handoff (session revocation, credential reset, MFA-method review) to [[authentication-patterns]]; this skill detects, it does not execute the reset.

Framework mappings are documented in [references/standards.md](references/standards.md).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The login succeeded with a valid password, so it is legitimate" | A valid credential is exactly what a stolen-credential or sprayed account looks like; valid-accounts abuse (T1078) produces clean successes. Only the baseline delta, geo-velocity, and device checks distinguish the real owner from the attacker. |
| "Impossible travel is always the VPN, so I can ignore those alerts" | Blanket-ignoring impossible travel hides the one real takeover among the VPN noise. The fix is an auditable suppression list of known egress IPs in step 2.3, not muting the detection; a silent mute means a stolen session signs in unchallenged. |
| "Failed logins do not matter, only successes do" | Password spraying is visible only in the failure pattern across many accounts before it lands a success; if you watch successes alone you detect the takeover after it happens instead of during the spray, losing your containment window. |
| "A few MFA prompts are normal, users mistap" | A burst of denies ending in one approve is the fatigue-attack signature, not mistaps; treating the burst as user error in step 3 lets the attacker wear the user down and walk in on the approval. |
| "I checked sign-ins, I do not need the audit log" | Authentication-process tampering (new MFA methods, conditional-access edits, added app secrets) lives in the directory/audit log, not the sign-in log. Skipping step 6 leaves attacker persistence in place after you close the sign-in alert. |

## Verification

- [ ] The log sources and time window are recorded, and a per-identity access baseline is established.
- [ ] Impossible-travel candidates are listed with computed velocity and an auditable suppression list of known egress IPs.
- [ ] MFA-fatigue bursts are surfaced with the deny-then-approve sequence and the device/IP that followed the approval.
- [ ] Password-spray and brute-force detections pivot on source IP and failure-reason, with the firing threshold documented.
- [ ] Token/session-theft checks for new-device session reuse and impossible token reuse are run and their results recorded.
- [ ] The audit log is searched for new MFA methods, conditional-access/federation changes, and added app credentials.
- [ ] Each confirmed finding carries identity, evidence, baseline delta, ATT&CK mapping, and a containment handoff recommendation.

## Related Skills

- [[security-framework-mapping]] - assign and verify the ATT&CK / D3FEND / NIST CSF identifiers used here.
- [[authentication-patterns]] - receives the containment handoff (session revocation, credential reset, MFA-method review) for confirmed takeovers.
- [[cloud-audit-log-detection]] - extends identity detections into cloud control-plane audit logs once an account is compromised.
- [[lateral-movement-detection]] - picks up where a confirmed identity compromise pivots into host-to-host movement.
