---
name: phishing-analysis-and-defense
description: "Analyze a suspected phishing email from the defender's seat (headers and authentication results, sender reputation, defanged URLs, attachment indicators) and drive the response: block the sender and payload, hunt for who clicked or replied, and reinforce user reporting. Make sure to use this skill whenever the user says \"analyze a phishing email\", \"is this email phishing\", \"phishing investigation\", \"examine suspicious email headers\", \"check this URL for phishing\", \"phishing response\", or \"investigate a reported email\", even when they only paste a raw header block or a suspicious link. SKIP, do NOT use for: spam-filter tuning or email infrastructure setup (use [[network-engineer]]) or credential reset after a confirmed compromise (use [[authentication-patterns]])."
summary_l0: "Analyze a suspected phishing email and drive block, hunt, and report response"
overview_l1: "This skill drives defensive triage of a reported or suspected phishing email and the response that follows. It teaches a deterministic sequence: read the full headers and authentication results (SPF, DKIM, DMARC, Authentication-Results, Received hops), assess sender and reply-to reputation, defang and inspect every URL and redirect, and characterize attachments by type and indicators without opening or executing them. Findings drive a graded verdict (benign, suspicious, confirmed phishing) and a response: block the sender and payload at the gateway, hunt the mail logs for every other recipient and for who clicked or replied, and reinforce the user-reporting loop. All URL and attachment handling is done defanged and in isolation; the skill never visits a live malicious link, never opens an attachment outside a sandbox owned by another workflow, and maps each indicator to ATT&CK phishing techniques for the incident record."
mitre_attack: [T1566, T1566.001, T1566.002]
d3fend_techniques: [D3-FA]
nist_csf: [PR.AT, DE.CM, RS.AN]
---

# Phishing Analysis and Defense

Triage a reported or suspected phishing email defensively (authentication results, sender reputation, defanged URLs, attachment indicators), reach a graded verdict, and drive the block-hunt-report response. This is a defender-seat workflow: every URL is defanged, no live malicious link is visited, and no attachment is opened outside an isolated sandbox.

## When to Use This Skill

- A user forwards or reports an email and asks whether it is phishing.
- You are handed a raw header block or `.eml` / `.msg` file and need an authentication and routing verdict.
- You need to inspect one or more suspicious URLs or redirect chains from a message safely.
- An email carries an unexpected attachment and you need to characterize it without detonating it here.
- A confirmed phishing message requires a response: blocking the sender, hunting for other recipients, and identifying who clicked or replied.

**When NOT to use:**

- Tuning spam-filter rules or standing up mail infrastructure (SPF/DKIM/DMARC publishing, MX records) - use [[network-engineer]].
- Resetting or rotating credentials after a user has already entered them on a phishing page - that handoff belongs to [[authentication-patterns]].
- Full reverse engineering of a malicious attachment payload - characterize indicators here and route the sample to [[malware-triage-analysis]].
- Any request to send a phishing email, build a lure, or test users with a live payload - out of scope; this skill is defense only.

## Instructions

### 1. Preserve the message as evidence

1. Work from the original message source, not a reply or screenshot. Export the full `.eml` / `.msg` or the complete raw headers.
2. Record reporter, received time, and mailbox so the hunt in step 6 can scope correctly.
3. Treat the message as read-only evidence; do not click, reply, forward to the sender, or unsubscribe.

### 2. Read authentication results and routing

1. Parse the authentication verdicts the receiving gateway recorded: SPF, DKIM, DMARC, and the consolidated Authentication-Results header. A DMARC fail or alignment mismatch on a brand domain is a strong spoofing indicator.
2. Walk the Received hops bottom-to-top to reconstruct the true origin; note any hop that contradicts the claimed From domain.
3. Compare From, Reply-To, Return-Path, and the envelope sender. A Reply-To pointing to a different free-mail or look-alike domain is a classic redirect-the-reply tactic (ATT&CK T1566).

### 3. Assess sender and display-name reputation

1. Check the From domain for look-alike spoofing: homoglyphs, added hyphens, swapped TLDs, and subdomain padding (for example `brand[.]secure-login[.]example`).
2. Note display-name impersonation where the visible name matches a known executive or vendor but the address does not.
3. Record domain age and first-seen where your enrichment sources allow; freshly registered sending domains weigh toward malicious.

### 4. Defang and inspect URLs

1. Extract every URL, including those behind buttons, in HTML link text, and inside redirect or tracking wrappers.
2. Defang each before writing it anywhere: render as `hxxp://` and bracket the dots, for example `hxxp://login[.]example[.]com/verify`.
3. Resolve the final destination only through passive enrichment or a sandboxed analysis surface; never load the live URL in your own browser.
4. Flag credential-harvest signals: a link whose visible text differs from its href, a destination that mimics a login page, or a data-collecting form on a non-brand domain (ATT&CK T1566.002, spearphishing link).

### 5. Characterize attachments without executing

1. Identify each attachment by true file type (magic bytes), not the displayed extension; flag double extensions and mismatches.
2. Hash each attachment (SHA-256) and check the hash against your threat-intel sources; do not open the file here.
3. Note high-risk types: macro-enabled office documents, script files, archives hiding executables, and HTML attachments that render a fake login form (ATT&CK T1566.001, spearphishing attachment).
4. If deeper analysis is needed, route the hash and file to [[malware-triage-analysis]] rather than opening it in your environment.

### 6. Reach a verdict and drive the response

1. Assign a graded verdict: benign, suspicious (needs more data), or confirmed phishing, citing the specific indicators that drove it.
2. On confirmed phishing, block the sender domain/address and the payload (URL and file hash) at the gateway.
3. Hunt the mail logs for every other recipient of the same campaign (subject, sender, URL, or hash pivot) and for any user who clicked the link or replied; flag clickers for credential-reset handoff to [[authentication-patterns]].
4. Purge or quarantine remaining copies from inboxes where your platform supports it.

### 7. Reinforce reporting and close the loop

1. Acknowledge the reporter so the report-suspicious-email behavior is positively reinforced (NIST CSF PR.AT).
2. Capture the campaign indicators (sender, defanged URLs, hashes) into the incident record for [[security-review]] and future detection.
3. Where many users received it but few reported it, note the awareness gap as a training input, not a blame exercise.

Framework mappings are documented in [references/standards.md](references/standards.md).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "SPF passed, so the email is legitimate" | SPF authenticates the envelope sender, not the visible From; an attacker can pass SPF on a look-alike domain while spoofing the display name. Only the DMARC alignment and Reply-To checks in step 2 catch that, and skipping them green-lights a spoof. |
| "I'll just click the link to see where it goes" | Loading the live URL from your own browser hands the attacker your IP, session, and a confirmed-live-target signal, and may auto-trigger a drive-by or harvest page. Defang and use passive resolution; the click is exactly the action the attacker is engineering. |
| "It's only one reported email, no need to hunt the logs" | Phishing arrives as a campaign; one report usually means dozens of silent recipients and some clickers. Skipping the recipient and clicker hunt in step 6 leaves compromised accounts live while you close the single ticket. |
| "The attachment looks like a PDF, it's safe to open" | The displayed extension and icon are attacker-controlled; magic-byte inspection routinely reveals a script or macro document masquerading as a PDF. Opening it on your workstation detonates the payload the analysis was meant to contain. |
| "The user fell for it, so I should flag them" | Blame suppresses future reporting, which is your earliest detection signal. The report-acknowledgement and awareness framing in step 7 is what keeps the next phish getting reported instead of hidden. |

## Verification

- [ ] The original message source (`.eml` / `.msg` or full raw headers) is preserved as read-only evidence.
- [ ] SPF, DKIM, DMARC, and Received-hop results are recorded, with any alignment or routing contradiction explicitly noted.
- [ ] From, Reply-To, Return-Path, and envelope sender are compared and any mismatch is documented.
- [ ] Every extracted URL is written defanged (`hxxp://`, bracketed dots) and no live malicious link was visited.
- [ ] Each attachment is identified by magic bytes and hashed (SHA-256); no attachment was opened outside an isolated sandbox.
- [ ] A graded verdict (benign / suspicious / confirmed phishing) is recorded with the indicators that drove it.
- [ ] On a confirmed verdict, the sender and payload are blocked, the recipient/clicker hunt is run, and the reporter is acknowledged.

## Related Skills

- [[security-framework-mapping]] - assign and verify the ATT&CK / D3FEND / NIST CSF identifiers used here.
- [[malware-triage-analysis]] - receives any suspicious attachment hash and file for safe static triage.
- [[identity-threat-detection]] - hunts the sign-in logs for the accounts of users who clicked or replied to a confirmed phish.
- [[security-review]] - consumes the campaign indicators and awareness gaps this skill produces.
