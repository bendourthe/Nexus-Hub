# Phase 6 -- Framework Coverage + Defensive Security Content

**Plan**: [`docs/archives/v2/v2.3/plans/adoption-ecc-cybersec-skills.md`](../../plans/adoption-ecc-cybersec-skills.md)
**Date**: 2026-05-29
**Status**: Closed
**Sub-tasks**: T017, T018, T019, T020, T021

## Goal

Build a framework coverage-matrix generator over the Phase 1 mapping convention, then re-author two curated defensive security skill packs and their helper scripts. Bulk import of the source cybersecurity corpus is explicitly rejected (plan appendix N5 / N6 / N7); this phase ships curated, re-authored, defensive-only content. All deliverables are local and zero-outbound per the MCP Registry Policy reverse-engineer-first decision tree.

## Decisions taken before coding

- **New category sign-off (T018 gate)**: T018 requires maintainer approval before creating a skill category (AGENTS.md "Ask first"). The user approved a **new `security-operations` category** (over the documented fallback of nesting under `security/`), on the basis that the existing `security/` category is application-security focused while the new content is operational (DFIR, threat hunting, detection engineering, IR, cloud / endpoint / identity / phishing detection).
- **Curation scope**: the plan suggested ~10-15 in batch 1 plus a second batch, but told us to "prefer fewer excellent skills over many copied ones." The user chose **Full ~15** -- batch 1 of 8 (DFIR / hunting / IR) and batch 2 of 7 (cloud / endpoint / phishing).
- **Authoring strategy**: the 15 skills were drafted by five parallel subagents from a single rigorous spec with pre-assigned, pre-verified framework IDs (ATT&CK technique IDs and NIST CSF 1.1 categories are stable and vouched for; leaving ID selection to a subagent risked hallucinated codes that would fail the skill's own Verification). The data-registry edits and helper scripts were authored centrally to keep the three counters consistent and avoid concurrent JSON edits.

## What was built

### T017 -- framework coverage-matrix generator

`scripts/build_framework_coverage.py` reads the optional framework-mapping frontmatter fields from Phase 1 (`mitre_attack` / `atlas_techniques` / `d3fend_techniques` / `nist_csf` / `nist_ai_rmf`) across `catalog/skills/` and emits a coverage matrix:

- A **summary table** (distinct controls covered + skill tags, per framework).
- **Per-framework detail tables** mapping each control ID to the skills tagged with it.
- Markdown (default) or JSON (`--format json`), to stdout or a `--out <file>` artifact.

It ships its own tolerant bracket-list parser (the existing `validate_skills.py` frontmatter reader leaves `[...]` as a raw string), accepts `--root` so it slots into the `tests/validators/conftest.py` subprocess harness, and is read-only / local / zero-outbound. A catalog with no tagged skills produces a successful empty matrix, not an error. After the Phase 6 content landed the matrix spans 34 ATT&CK techniques, 6 D3FEND countermeasures, and 10 NIST CSF categories. Registered as an explicit-name copy step in both `scripts/installer.sh` and `scripts/installer.ps1`. Covered by 6 pytest cases in `tests/validators/test_build_framework_coverage.py` (untagged tree, tagged skill, shared control across two skills, multi-id and bare-scalar parsing, `--out` file write, missing-root error).

### T018 -- defensive batch 1 (DFIR / threat hunting / incident response)

Eight skills under `catalog/skills/security-operations/`: `memory-forensics`, `hunting-credential-dumping`, `disk-artifact-forensics`, `siem-detection-engineering`, `log-threat-hunting`, `lateral-movement-detection`, `ransomware-incident-response`, `persistence-mechanism-hunting`. Each carries a pushy description (verbatim trigger phrases + SKIP clause), ATT&CK / D3FEND / NIST CSF framework tags, a `references/standards.md` companion, a Common Rationalizations table citing concrete failure modes, and a binary Verification checklist tied to observable artifacts.

### T019 -- defensive batch 2 (cloud / endpoint / phishing)

Seven skills, same quality bar and filters: `cloud-security-posture-detection`, `cloud-audit-log-detection`, `container-runtime-detection`, `phishing-analysis-and-defense`, `identity-threat-detection`, `malware-triage-analysis` (plus `endpoint-edr-detection`, drafted alongside batch 1). All content re-authored from public MITRE / NIST knowledge -- no third-party SKILL.md text copied, no source repository named in the artifact (Reverse-Engineering Attribution Rule). The mandate filter held throughout: defensive / detection / forensics / IR only; the phishing and malware-triage skills explicitly state "defense only" and "never write malware," and every skill's "When NOT to use" fences off offensive / evasion use.

### T020 -- deterministic helper scripts

Two skills ship a helper with `.sh` + `.ps1` parity:

- `memory-forensics/scripts/volatility-runner.{sh,ps1}` -- a thin, read-only wrapper around a locally-installed Volatility 3 (`vol`) that runs a fixed triage plugin set (process tree, hidden-process carve, module list, injection scan, network connections, handles, cmdline) against a memory image into a per-case output directory, hashing the image first for chain of custody. Requires Volatility 3 installed; fetches no symbol packs over the network; never executes carved samples.
- `log-threat-hunting/scripts/ioc-log-scan.{sh,ps1}` -- a local read-only IOC sweep that fixed-string-matches an indicator list against a log file and reports per-indicator counts and matching lines (comment and blank lines in the IOC list are ignored).

Both bash scripts follow the project safety rules (`set -euo pipefail`, quoted expansions, `command -v` capability checks, per-item failure isolation under `-e`), are shellcheck-clean at `--severity=warning`, are referenced from their parent SKILL.md so the orphan-bundle audit passes, and were functionally verified (the IOC sweep against a fixture log returning correct counts; the Volatility wrapper's missing-`vol` precondition path returning exit 1).

### Registration

One programmatic pass read each SKILL.md frontmatter verbatim and registered all 15 skills: `data/skills.json` (212 -> 227 entries; `statistics.total_skills` 208 -> 223; new `categories.security-operations` = 15), `data/marketplace.json` (new "Security Operations" category, skill_count 15), and `data/SKILL_INDEX.md` (+15 rows; 211 -> 226 skills across 22 -> 23 categories). The JSON diffs are pure appends. `AGENTS.md` gained the new category in its list, a placement-guidance paragraph, and an updated catalog-overview count.

## Testing and results

- `tests/` 298 passed, 0 failed (was 291; +6 coverage-generator cases plus one), in 8m39s (runtime dominated by `tests/integrations` real file-tree installs over a OneDrive-synced path).
- `tests/validators` 44 passed (the 6 new `build_framework_coverage` cases included).
- Four CI validators (no-personal-paths, unicode-safety, supply-chain-iocs, workflow-security) all exit 0.
- Per-skill bundle audit: 233 skills, 0 orphans. Quality-heuristics pass: 0 new warnings (the 15 new skills clear it; the pre-existing 574-warning grandfathered debt under WN-v23-4 is unchanged).
- shellcheck clean on both installers and the two new helper scripts.
- Coverage matrix verified to populate from the new tags (34 / 6 / 10 across ATT&CK / D3FEND / CSF).

## Deviations

- **Skill body length**: the 15 skills came in at 89-156 physical lines each, below the 160-280-line band suggested in the drafting brief, partly because the project's no-hard-wrap rule keeps each paragraph and bullet on one physical line. They are fully conformant (the AGENTS.md SKILL.md size norm is an upper bound, not a lower bound) and pass every gate; recorded as the optional-enrichment item DF-v23-2.
- **Count drift**: the pre-existing `statistics.total_skills` drift (WN-v23-1) was carried forward consistently (+15 across all counters) rather than reconciled, since the absolute reconciliation is outside the Phase 6 sub-task scope.

## Known gaps recorded

- **QG-v23-1** -- the CI `shellcheck` job lints `catalog/hooks/*.sh` but not the new per-skill helper scripts under `catalog/skills/**/scripts/`. The one-line fix (broaden `find catalog/hooks` to `find catalog`) is proposed but not auto-applied per the "never silently rewrite CI" rule.
- **DF-v23-2** -- the defensive skill bodies are concise and fully conformant but could optionally be deepened with platform-specific query examples (Splunk SPL / KQL / Sigma) in a future catalog-quality pass.

See [`docs/archives/v2/v2.3/known-gaps.md`](../../known-gaps.md).

## Next steps

- Phase 7: installer instruction-file parity (v2.2.0 known-gaps DF-001 / MT-2 / MT-1).
- Optional: apply the QG-v23-1 CI fix and (separately) reconcile WN-v23-1 at the next `make build-catalog` rebaseline.
