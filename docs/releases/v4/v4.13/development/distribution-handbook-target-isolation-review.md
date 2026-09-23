# Distribution handbook content review - explicit global target isolation

**Handbook:** `docs/handbooks/distribution.html` (id `distribution`)
**Reviewed on:** 2026-09-22
**Trigger:** The v4.0 BG-2 repair changed the handbook's declared code inputs `runner.py`, `cursor.py`, and `aider.py`.

## Claim review

The retained source says that the installer prepares a bundle, the runner selects platform and scope, adapters write native shapes, managed files are tracked, and host behavior requires verification. Those claims still hold. The changed runner now carries an explicit global target into integrations, Cursor's global root and generated attribution-helper path follow that target, and Aider's global config and attribution-guide reference do likewise. The source does not claim that an explicit global target writes into the real profile, nor does it prescribe one fixed global destination. No visible content change is warranted by these three code changes.

## Qualification

`build_presentation.py ... --check` reproduced the committed output hash `8463c66d85d0d354374b89ceb2a10ddf8c9fe5138a866ad13606776d763cc557` without changing the handbook. The existing build and Chromium rendered receipts attest to those exact output bytes and remain applicable. The new fake-home installer regression passed, 146 affected installer and platform-default tests passed with 2 optional skips, and the Windows native fast profile passed 17/17. Only the three code-input hashes and this content review receipt require refresh.
