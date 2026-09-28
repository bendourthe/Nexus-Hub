# Distribution handbook content review - redirected native roots

**Handbook:** `docs/handbooks/distribution.html` (id `distribution`)
**Reviewed on:** 2026-09-22
**Trigger:** The v4.3 DF-5 repair changed the handbook's declared installer, runner, and owned-file inputs.

## Claim review

The retained source says the installer prepares a bundle, the runner selects platform and scope, adapters write native shapes, and managed files are tracked. Those claims still hold. The changed adapters now refuse a native write when the managed root or an ancestor is a link or junction, or when a target leaves the managed root. The runner and installer surface the refusal reason. This is a safety boundary on the described flow, not a change to its distribution model. The handbook does not promise that linked native roots are writable, so no visible content change is warranted.

## Qualification

The presentation builder's `--check` reproduced output SHA-256 `8463c66d85d0d354374b89ceb2a10ddf8c9fe5138a866ad13606776d763cc557` without changing the handbook. Existing build and Chromium rendered receipts attest to those exact output bytes and remain applicable; this is not a new browser review. The affected installer suite passed 668 tests with 45 optional skips, the fast profile passed 17/17, and a real CLI dry run against a disposable `.copilot` junction reported `refuse-link-like-ancestor` while its external target remained empty.
