# Session History - Withdrawing the GitHub Usage Monitor

**Date**: 2026-08-22
**Branch**: `chore/remove-github-usage-monitor`
**Plan**: none. This is a bug-driven withdrawal, opened by a user report against the v3.18.1 release published hours earlier.
**Environment**: Windows 11, Git Bash and PowerShell, Python 3.12, pytest; GNU Make unavailable, so `make` targets ran as their constituent commands
**Outcome**: The extension is deleted and actively uninstalled from both VS Code and Cursor. The decision is recorded with the four alternatives it beat and the one thing that would reopen it.

## 1. The report

v3.18.1 shipped a fix for the GitHub Usage Monitor reporting 58% against a saturated allowance. After installing it, the user reported the monitor showing **0%** while `github.com/settings/billing` showed **2,000 min used / 2,000 min included**. The release had made the number worse, not better.

## 2. Investigation, in the order it actually happened

**The pipeline was exonerated first.** Running the shipped v3.18.1 code against a realistic payload produced 2,595 minutes / 129.77% - exactly the figure the plan predicted. The weighting worked. Three input conditions were then found to collapse to a display of 0%:

| Condition | drawdown | displayed |
|---|---|---|
| Repos resolve as public | 0 | **0%** |
| No Actions line items | 0 | **0%** |
| Repos unresolved | null | *unavailable* (honest) |

The third row mattered: unresolved data was already handled correctly, so the 0% was a *confident* zero, not a withheld one.

**The probe settled which.** `scripts/reconcile-drawdown.js` against the live account showed all 6,425 Actions minutes on two repositories, both currently public, and `H1 private+hosted+standard = 0.0 min (0 items)`. The probe's own verdict line read `NO CANDIDATE RECONCILES` and its ledger row classified the month `refutes`.

**Phase 3 worked.** The reconciliation classifier built the previous day refused to call a saturated month "support" and printed *"Do NOT tune a formula to close the gap - record the finding."* The anti-swing mechanism caught its own release.

**Root cause: point-in-time visibility.** The v3.18.1 plan recorded `Nexus-AI` as **private** on 2026-08-19; the probe found it **public** on 2026-08-22. Billing line items are historical, `GET /repos/{owner}/{repo}` answers for now. Counting `Nexus-AI` as private with the shipped weights gives 1,270.3 + 441.7 + 1,281.3 = **2,993.3 minutes = 149.7%**, which saturates a 2,000 cap and matches the page exactly.

## 3. Why it was withdrawn instead of fixed

Verified against live vendor documentation rather than inherited from the plan:

- `GET /{scope}/settings/billing/actions`, which returned `included_minutes` and `total_minutes_used`, was **closed down 2025-09-26**.
- Budgets API: only `budget_amount` / `consumed_amount`. `/usage` and `/usage/summary`: no allowance field. GraphQL: no billing surface.
- The line-item schema has **no discount-reason field and no visibility field**, so the public/private split - which the billing page's own wording requires - can only come from repository visibility, which is unavailable historically.

The maintainer set the terms explicitly: make it work reliably for any account with no configuration, or delete it. The first is impossible for a reason that is a property of the missing data, not of the implementation.

## 4. What was found along the way, and is worth keeping

**A shipped claim had expired.** GitHub's 2026 pricing page states that from **2026-03-01** self-hosted runners consume the quota "based on list price". The v3.18.1 policy document asserted they never draw down, and `classifySku` excluded them. Both were authored 2026-08-22, five months after the behavior changed. The do-not-invent rule catches inventing a claim; it did not catch *inheriting* one that had expired. Recorded as WN-1.

**The same page confirmed the weighting.** "Consume available usage based on list price" is GitHub stating the mechanism v3.18.1 derived. That is why the weighting decision record is superseded rather than deleted - its analysis was right.

## 5. Two fail-open gates, one caught in each direction

The first retirement guard asserted `extension_id in body`. It **passed with the retirement entry deleted**, because the id also appears in the explanatory comment beside it. Rewritten to parse the retirement array specifically, then verified by deleting the entry (fails) and restoring it (passes).

This is the second gate of this shape in two days; the v3.18.1 parity test had the same defect and the same fix. Asserting a string exists *somewhere in a file* is not a gate when the file also documents the thing.

## 6. What changed

| Area | Change |
|---|---|
| Deleted | `extensions/github-usage-monitor/` (84 tracked files), its CI workflow, `test_github_usage_monitor_workflow.py`, `test_github_monitor_naming.py`, the policy document, the drawdown ledger |
| Installers | GitHub install block removed from both; `remove_legacy_vscode_extensions` / `Remove-LegacyVSCodeExtensions` rewritten to sweep **both** `code` and `cursor` and to uninstall `nexus-hub.github-usage-monitor` |
| Tests | Roster trimmed to three monitors; dual-host assertions removed; new both-hosts retirement guard added |
| Docs | New withdrawal decision record; weighting record superseded in place; README "What's New" and extension listing rewritten; DEVLOG row; known-gaps v3.18.2 section |
| Version | 3.18.1 -> 3.18.2 across all six surfaces |

## 7. Verification

| Gate | Result |
|---|---|
| `check_version_sync.py` | Six surfaces at 3.18.2 |
| `test_installer_smoke.py` | 33 passed; retirement guard verified to fail with the entry removed |
| `tests/workflows/` | 73 passed, 8 skipped |
| `validate_decision_records.py` | 14 records OK |
| `bash -n installer.sh`, PowerShell AST parse of `installer.ps1` | Both clean |
| Catalog, permission, parity, unicode, IOC, workflow-security, required-checks, colocation, doc-budgets, registry, base-template, platform contracts, platform defaults | All pass |
| Platform read-contract | Re-stamped 3.18.1 -> 3.18.2, **not** re-verified: the full pass ran the same day and this release touches no platform discovery surface. Stated as such in the document. |

## 8. Deferred

- **MT-1**: `docs/archive/v3/v3.16/development/history` (39 files) remains due for archival. Out of scope for a withdrawal; wants its own reference-repair pass.
- **User settings**: `githubUsageMonitor.*` keys are left in `settings.json`. Inert, and deleting keys a user wrote is not the installer's call.
