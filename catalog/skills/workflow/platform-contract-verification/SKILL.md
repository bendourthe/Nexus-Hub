---
name: platform-contract-verification
description: Re-verify every supported AI platform's current skill/command/rule/hook discovery format against the living read-contract before a release, re-check its documented behavioral-default lever in the same pass, and fix any drift in the installers. Use this whenever running /update release on a distribution catalog that installs into multiple external AI platforms, whenever "check the platforms still work", "did any platform change its skill format", "did a platform rename a setting", "re-verify install paths", "re-verify the platform defaults", "the install stopped surfacing commands", or before shipping a catalog that other tools consume. SKIP for ordinary application projects that do not ship a multi-platform installer (the skill self-gates to a no-op there), and SKIP for one-off single-platform path questions.
summary_l0: "Re-verify each AI platform's discovery format and default lever before release; fix installer drift"
overview_l1: "A release-time gate for a distribution catalog (Nexus-Hub) whose installer materializes skills, commands, rules, and hooks into many external AI platforms (Claude, Codex/ChatGPT, Antigravity, Gemini, OpenCode, Cursor, ...). External platforms change where and how they read these artifacts after app updates, silently breaking a global install. This skill re-verifies each platform's CURRENT discovery format via targeted web searches, diffs the findings against docs/policy/platform-read-contracts.md, and on any drift updates the contract doc, the affected integration adapter under scripts/lib/integrations/, and both installers, then re-runs scripts/verify_platform_contracts.py. It self-gates to the Nexus-Hub repo (a repo shipping the contract doc + integrations tree) and is a silent no-op elsewhere, and it degrades gracefully offline. It adds no outbound dependency or credential: web search is the agent's own tool."
---

# Platform Read-Contract Verification

A pre-release verification gate for a distribution catalog that installs into multiple external AI platforms. External platforms (Claude Code, the Codex / ChatGPT desktop app, Antigravity, Gemini, OpenCode, Cursor, and others) periodically change where and how they discover skills, slash commands, rules, and hooks. When they do, a Nexus-Hub install that was correct last release silently stops surfacing the catalog. This skill re-establishes ground truth every release so the next release is guaranteed to work everywhere.

## When to Use This Skill

- As governance step 4 of `/update release` (invoked automatically by `catalog/commands/update.md`).
- Whenever a user reports "commands/skills stopped showing up in <platform>" after a platform app update.
- Before shipping any change to the installer's per-platform delivery.

**When NOT to use:**

- In an ordinary application project that does not ship a multi-platform installer. The skill detects this and is a silent no-op (it does real work only in a repo that contains BOTH `docs/policy/platform-read-contracts.md` and `scripts/lib/integrations/`).
- For a one-off "where does platform X read Y" question with no release in progress (answer it directly).
- Offline / no web-search tool available: degrade to a logged no-op; never block the release.

## Instructions

### Step 0 - Self-gate

Confirm this repo is a multi-platform distribution catalog: both `docs/policy/platform-read-contracts.md` and `scripts/lib/integrations/` MUST exist. If either is absent, print one line ("platform-contract-verification: not a distribution catalog, skipping") and stop. Do not mention the skill otherwise.

### Step 1 - Enumerate the platforms

This pass covers **two** contracts. They are separate documents with a deliberate scope boundary, and neither should grow into the other.

| Contract | Owns | Gating |
|---|---|---|
| `docs/policy/platform-read-contracts.json` + `.md` | Where each platform READS each surface (instruction file, skills, commands, rules, hooks) | **HARD-GATES the release** via `meta.verified_for_version` |
| `docs/policy/platform-defaults-levers.md` | Whether each platform documents a settable **behavioral default** (reasoning effort, model pin, approval/autonomy policy) | **Advisory only** - rides along, never blocks |

The read-contract has two co-located files: `docs/policy/platform-read-contracts.json` is the machine-readable source of truth (consumed by both `scripts/verify_platform_contracts.py` and the installer's `runner.py` verify path), and `docs/policy/platform-read-contracts.md` is the human-readable table plus narrative. Treat the JSON as authoritative; the `.md` mirrors it.

Read the JSON's `contract_checks` (per-platform expected read-paths), its `install_verify` entries (the post-install surface checks), and its `meta` block (`last_verified`, `verified_for_version`). List every platform and its declared read-paths (instruction file, skills, commands/slash surface, rules, hooks) at global and workspace scope, plus its "Sources" URLs from the `.md`.

Then read `docs/policy/platform-defaults-levers.md` (when present) and list each platform's classification (VERIFIED / UNVERIFIED), its lever keys, its config file, and its source URL. A platform that changes or removes a documented lever should surface at the same moment as one that changes its discovery path, which is why both are enumerated in one pass rather than on separate cadences.

### Step 2 - Re-verify each platform against its current docs (web search)

For each platform, run targeted web searches for its CURRENT discovery format, prioritizing official docs (the Sources URLs first, then a fresh search). Confirm, for each surface: the exact directory, the file format (folder-per-skill `SKILL.md`? flat `.md`? TOML?), the discovery depth (one level vs nested), the invocation syntax (`/name`, `$name`, `/prompts:name`), and any global-vs-project difference. If a platform's docs are unreachable, record it as "unverified this cycle" and move on (do not guess).

While you are already on the vendor's documentation, re-check that platform's **lever** row in the same visit: are the documented key names unchanged, is the config file path unchanged, and does the source URL still resolve without redirecting to a new host? A redirect is not cosmetic; it is the earliest signal that a vendor has reorganized or renamed a product. The v3.16.0 pass found three (Claude 301 to `code.claude.com`, OpenAI Codex 308 to `learn.chatgpt.com`, and `docs.windsurf.com` 307 to `docs.devin.ai`, the last confirming a rebrand first-hand).

The same evidence rule governs both contracts: a lever is recorded only when a **fetched official vendor page** names it. Never a blog, forum, aggregator, issue tracker, or analogy to a similar-looking platform. "No lever documented" is a valid and expected result.

### Step 3 - Diff against the contract doc

For each surface, compare the verified format to the contract doc row. Classify each as MATCH, DRIFT (path/format changed), or UNVERIFIED. Summarize the diffs before changing anything.

Do the same for each lever row: MATCH, DRIFT (a key renamed, a path moved, allowed values changed), or UNVERIFIED. A lever that has been **removed** by the vendor is the highest-severity finding in this half, because Nexus-Hub may be seeding a setting the platform no longer honours.

### Step 4 - Fix drift (with confirmation)

For each DRIFT finding, in lockstep:

1. Update the platform's entry in `docs/policy/platform-read-contracts.json` (the `contract_checks` row and, if a post-install surface path changed, its `install_verify` entry). Mirror the same change into the `docs/policy/platform-read-contracts.md` table (plus its Source URL).
2. Update the platform's adapter in `scripts/lib/integrations/<platform>.py` (path, flatten flag, or the `_mirror_*` override) to match.
3. Update both `scripts/installer.sh` and `scripts/installer.ps1` if the delivery call changed (keep them byte-equivalent in behavior).
4. Add a `CHANGELOG.md` `[Unreleased]` note describing the platform format change and the fix.

Use the shared adapters (`flatten_skills`, `commands_to_skills`, `commands_to_slash`) rather than bespoke copy logic; most drift is a path or a subdir-name change in the integration config.

For a **lever** DRIFT finding, the lockstep is shorter because no installer is involved:

1. Update the platform's row and detail section in `docs/policy/platform-defaults-levers.md`, including the source URL and the verification date.
2. Update its entry in `configs/platform-defaults.json` (key names, `source_url`, `verified`), then run `python scripts/sync_platform_defaults.py --check`.
3. If the vendor REMOVED a lever Nexus-Hub was seeding, remove it from `configs/platform-defaults.json` too. Reclassify the platform UNVERIFIED, or `install_target.mode = "not-writable"` if other levers remain. Leaving it declared would keep writing a setting the platform ignores.
4. Add a `CHANGELOG.md` `[Unreleased]` note.

The completeness tests in `tests/validators/test_platform_defaults_levers.py` enforce the invariants for you: every registered integration is classified exactly once, every VERIFIED row carries a source URL and an ISO date, and no platform may appear in `configs/platform-defaults.json` without a VERIFIED classification.

### Step 5 - Re-run the code-vs-contract checker

Run `python scripts/verify_platform_contracts.py`. It MUST exit 0 (installer code matches the updated JSON contract). Then run `make validate` and the integration tests. Fix any failure before the release proceeds.

### Step 6 - Re-stamp the freshness marker

This cycle is only complete once the contract is stamped for the release being cut. In `docs/policy/platform-read-contracts.json`'s `meta` block, set `last_verified` to today's date and `verified_for_version` to the version this release will publish (the value `.claude-plugin/plugin.json` is bumped to). Update the "Last verified" line at the top of the `.md` to the same date. Then run `python scripts/check_platform_contract_freshness.py --version <release-version>` and confirm it exits 0. This is the guard that hard-gates the release: until the marker matches the release version, `make validate` and CI fail, so a release literally cannot ship on a stale contract.

**The lever contract is deliberately NOT gated this way, and that asymmetry must survive future edits.** Append a dated row to the re-verification log at the bottom of `docs/policy/platform-defaults-levers.md` recording the scope and the outcome. Do **not** add a `verified_for_version` marker, a freshness script, or any `make validate` / CI check for it.

The reasoning, so nobody "fixes" it later: the read-contract governs whether an install **works at all**, so shipping on a stale one silently empties a user's install, and blocking is correct. A lever contract governs the **value of a default the user can change**, so a stale one at worst seeds a setting that is merely outdated. Gating on it would let a vendor renaming a setting on a Tuesday wedge every unrelated release until someone ran a research pass. That is the same reasoning that keeps the model-prompting freshness check advisory (see `/update release` governance step 5) while the read-contract check hard-gates.

If a lever row goes unverified this cycle, record it in the log as unverified and continue. Never re-stamp a read-contract marker to make a lever finding go away; they are independent.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "No platform would change its paths between releases." | Codex deprecated custom prompts and moved to skills; Antigravity's global paths moved from `~/.gemini/antigravity/` to `~/.gemini/config/`. Both silently emptied installs. Formats DO drift; that is why this gate exists. |
| "The install copied files successfully, so it works." | A successful copy to the wrong path is the exact failure mode. Delivery success is not discovery success; verify against the platform's real read-path. |
| "verify_platform_contracts.py passed, so we are fine." | That checker only proves code matches the JSON contract. If the JSON itself is stale relative to the platform's current behavior, it passes while installs break. Only the web-search re-verification (this skill) keeps the contract true. |
| "I'll just skip it this release, nothing changed." | You cannot silently skip: `check_platform_contract_freshness.py` fails `make validate` and CI the moment the version is bumped past the stamped `verified_for_version`. Skipping forces you to either do the verification or consciously re-stamp a stale marker (a visible, reviewable act). If offline, record 'unverified this cycle' explicitly. |
| "The lever contract should hard-gate too, for consistency." | Consistency is the wrong goal here. A stale read-contract silently empties an install; a stale lever contract at worst seeds an outdated default the user can change. Gating the lever contract would let a vendor renaming a setting wedge every unrelated release. The asymmetry is the design, not an oversight. |
| "The lever is obviously still there, I don't need to open the page." | Three vendor doc hosts moved between the v3.15 and v3.16 cycles, one of them a full product rebrand. A redirect is the earliest signal a vendor reorganized; you only see it by fetching. Assuming a lever is unchanged is how `.kimi/agent.yaml` shipped. |
| "I found a lever on a blog post that matches, close enough." | A lever is recorded only from a fetched official vendor page. Nexus-Hub shipped a fabricated `.kimi/agent.yaml` once and had to drop it in v3.15.0. "No lever documented" is a valid result; a plausible-sounding invented one is not. |

## Verification

- [ ] Self-gate ran: in a non-catalog repo the skill is a no-op; in Nexus-Hub it proceeded.
- [ ] Every platform entry in `docs/policy/platform-read-contracts.json` is classified MATCH / DRIFT / UNVERIFIED for this cycle.
- [ ] Every DRIFT finding has a corresponding JSON + `.md` + adapter + installer edit and a CHANGELOG note.
- [ ] `docs/policy/platform-read-contracts.json` `meta.last_verified` is today and `meta.verified_for_version` equals the release version; the `.md` "Last verified" line matches.
- [ ] `python scripts/verify_platform_contracts.py` exits 0.
- [ ] `python scripts/check_platform_contract_freshness.py --version <release-version>` exits 0.
- [ ] Every platform in `docs/policy/platform-defaults-levers.md` (when the file exists) is classified MATCH / DRIFT / UNVERIFIED for this cycle, and a dated row is appended to its re-verification log.
- [ ] Any lever DRIFT is reflected in BOTH `docs/policy/platform-defaults-levers.md` and `configs/platform-defaults.json`, and `python scripts/sync_platform_defaults.py --check` exits 0.
- [ ] No `verified_for_version` marker, freshness script, or CI check was added for the lever contract; it remains advisory.
- [ ] `make validate` passes and the integration test suite is green.

## Related Skills

- `[[version-upgrade]]` - the release version bump this gate runs before.
- `[[known-gaps-tracker]]` - sibling release governance step; record any UNVERIFIED platform as a known gap.
- `[[model-routing]]` - another best-effort, self-degrading release-time assessment step.
