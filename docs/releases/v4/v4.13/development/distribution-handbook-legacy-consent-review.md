# Distribution handbook content review - consented legacy removal and skill-index pointer

**Handbook:** `docs/handbooks/distribution.html` (id `distribution`)
**Reviewed on:** 2026-09-25
**Trigger:** v4.13.3 Phases 4 and 5 changed four of the handbook's declared code inputs: `scripts/installer.sh`, `scripts/installer.ps1`, `scripts/lib/integrations/runner.py`, and `scripts/lib/integrations/cursor.py`.

## Claim review

What changed in those inputs:

- Both installers accept a consent flag, forward it to each runner call, and print one combined legacy-instruction report.
- The runner parses that flag and `NEXUS_HUB_SKILL_INDEX`, adds a `legacy` block to the install summary and a `legacy-report` subcommand, and re-runs installs once in pointer mode.
- Cursor's workspace instruction write goes through the shared cleanup-aware merge owner.

Each handbook claim was checked against the candidate:

- "Both installer entry points prepare the bundle and invoke platform integration logic. The Python integration runner selects the requested platform and scope." Still true; the new flag and variable ride on the same invocation.
- "Owned-file writing consults the installation manifest. It can repair an artifact created by Nexus-Hub while preserving a file authored by the user." Still true. The new cleanup path strengthens preservation: a shared instruction file is never altered outside the managed block without a per-span consent token.
- "Adapters return file actions and track managed paths." Still true. The two new actions, `detected` and `backed-up`, are report-only, and the manifest deliberately does not record them.
- "Unchanged bytes can remain unchanged on a second run." Still true. The byte-preserving renderer keeps an unchanged file unchanged, including CRLF and BOM files that the previous `read_text` path normalized.

No claim is false, so no visible content change is required.

The handbook does not describe shared instruction-file merging, the consented legacy removal, or the opt-in skill-index pointer. Those behaviors are documented in `docs/decisions/proposed/tooling/2026-09-24-legacy-instruction-block-removal.md`, `docs/policy/platform-read-contracts.md`, and the v4.13.3 capability-usage draft. Adding a section is a coverage choice for the next handbook refresh, not a correctness repair.

## Qualification

`build_presentation.py docs/handbooks/_sources/distribution/model.json --out docs/handbooks/distribution.html --root . --check` reproduced the committed output hash `25ffd7b98de194f81f0a33035b4b184546c394214843318bec54573a2d22efb5` without changing the handbook. The existing build and Chromium rendered receipts attest to those exact output bytes and remain applicable. Only the four code-input hashes and this content review receipt are refreshed.
