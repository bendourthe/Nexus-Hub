# Comparison - Cybersecurity Skills Library

**Project**: Nexus-Hub
**Source**: `https://github.com/mukul975/Anthropic-Cybersecurity-Skills` (Git repository)
**Source revision**: `f762615`, committed 2026-08-20 (single squashed commit; shallow clone)
**Source scale**: 817 skills, 4,512 files, 29 claimed security domains (46 distinct `subdomain:` values in practice)
**Source license**: Apache-2.0 (all 817 skills declare `license: Apache-2.0`)
**Nexus-Hub license**: MIT
**Authoring cycle**: v3.17.6 (in flight)
**Adoption target**: v3.20.1
**Date**: 2026-08-20
**Scope**: `repo` - full 11-dimension comparison

> **Slotting note (revised 2026-08-20).** The original target recorded here was v3.17.12, resolved on the false premise that v3.17.11 was the last planned version. Plans already existed through v3.20.0; the walk-forward resolution enumerated version directories in alphabetical order, which places `v3.18` before `v3.5`, and terminated early. Corrected target: **v3.20.1**, rank 9 of 15 in `docs/v3/roadmap-prioritization.md`. The confirmed content scope (a broad expansion from 40 to 80 security-domain skills) is feature-scale work, so it belongs in a minor rather than a patch, which is the second reason the original slot was wrong. The plan is at `../plans/adoption-cybersecurity-skills.md`, named slug-first with the target version as a field inside it.

## Executive Summary

The source is an unusually close neighbour to Nexus-Hub rather than a loose analogy. It is a folder-per-skill catalog on the same `SKILL.md` open standard, using **byte-identical framework-mapping frontmatter keys** to the ones Nexus-Hub already declares (`mitre_attack`, `nist_csf`, `nist_ai_rmf`, `atlas_techniques`), and the same `references/standards.md` companion convention that `AGENTS.md` recommends. Convergence on that many conventions makes a small set of items unusually cheap to adopt and makes one headline item architecturally impossible.

Three conclusions drive everything below.

1. **Bulk content adoption is foreclosed on Tier-1 grounds.** Nexus-Hub loads `name` + `description` + `summary_l0` + `overview_l1` for every catalog skill in every session. Measured, that is already ~104k tokens across 273 skills (~382 tokens/skill). Importing 817 skills at our Tier-1 rate projects to **~416k tokens permanently resident**, before any skill body loads. It would also make a general-purpose development harness roughly 75% cybersecurity.
2. **The license blocks text reuse.** Apache-2.0 content cannot be relicensed into an MIT catalog. Adoption must be independent authorship on the same topics from primary sources, not prose transfer. This raises per-skill effort from Low to Medium and happens to align exactly with the existing reverse-engineer-first policy.
3. **Two reversals: the source beats Nexus-Hub on its own declared norms.** Their SKILL.md bodies comply with the <=500-line target that `AGENTS.md` sets and Nexus-Hub itself violates 107 times. Their framework mapping covers 6 frameworks with a machine-readable ATT&CK Navigator export; ours covers 5 with Markdown only, and is applied to just 19 of 273 skills.

Highest-value adoptions are therefore **tooling and mapping**, not content: the MITRE F3 field, a Navigator layer export, agentskills.io conformance validation, and a `standards.md` backfill. The confirmed broad content expansion rides on top of those, delivered as ~40 **consolidated, independently authored, vendor-neutral** skills rather than ~200 verbatim vendor-specific imports.

## Step 1.5 - Source Security Scan

**Verdict: CLEAR.** Scanned before any source content was ingested into working context. The repository has no dependency manifest, no install hooks, and no committed binaries beyond a banner PNG.

| Signal | Count | Adjudication |
|---|---|---|
| `subprocess` / `exec` / `eval` patterns | 1,127 | Wrappers around forensic and offensive CLIs (Volatility3, `dd`, KAPE, Impacket). List-form arguments with bounded `timeout=`; no shell-string interpolation of user input. Benign. |
| Files making outbound HTTP calls | 315 | Named threat-intelligence APIs (VirusTotal, urlscan.io, crt.sh, MISP, MITRE CTI, Malpedia) reading a **user-supplied** API key from the environment. Legitimate, but policy-relevant for adoption (see Step 5). |
| "Ignore previous instructions" strings | 11 | **All defensive.** Detection regexes and test fixtures inside prompt-injection *defense* skills (`detecting-ai-model-prompt-injection-attacks`, `defending-llms-with-guardrails`, `implementing-llm-guardrails-for-security`). Textbook false-positive class. |
| HTML comments | 121 | Documentation annotations inside code examples. No agent-directed text. |
| Long base64-shaped blob | 1 | A hexadecimal Diffie-Hellman MODP prime constant in `implementing-zero-knowledge-proof-for-authentication`. Not an encoded payload. |
| Zero-width / bidi control characters | 0 | None. |
| Install hooks (`postinstall`, `setup.py`) | 0 | No dependency manifest exists. |

Scanning a security-domain corpus is the pathological case for pattern-based gates: the defensive skill and the attack payload contain identical strings, and only the surrounding role (a regex constant versus imperative prose) separates them. A naive gate keyed on the injection phrase alone would have BLOCKed a clean repository. The value of this step was adjudication, not detection.

Incidental observation, not a finding against the source: their `.github/workflows/validate-skills.yml` applies `paths:` filters at **workflow** level on `pull_request`. That is the exact antipattern Nexus-Hub removed in v3.17.6 - if such a check is ever marked required, unrelated PRs sit Pending forever. Independent confirmation that the v3.17.6 fix targets a real and common trap.

## Step 2-3 - Dimension Comparison

Legend: `+` external-only (adoption candidate) - `=` Nexus-Hub-only (strength to preserve) - `~` both, different approach - `.` equivalent

| # | Dimension | Nexus-Hub | Source | Verdict |
|---|---|---|---|---|
| 1 | Project identity | 273 skills, 21 categories, general-purpose dev harness, MIT | 817 skills, single cybersecurity domain, Apache-2.0 | `~` Different purpose; not a defect on either side |
| 2 | Technology stack | Python + Bash + PowerShell; installers for 14+ platforms | Python 3 stdlib only, no manifest | `=` Our cross-platform installer has no counterpart |
| 3 | AI assistant configuration | 14 default-installed platforms, per-platform read-contract, marker-merged instruction files | Claims 26+ platforms via the open standard; no installer | `=` Ours is materially deeper; theirs is "clone and point at it" |
| 4 | Project structure | `catalog/skills/<category>/<name>/` - **category enforced by directory** | `skills/<name>/` flat - category in free-text `subdomain:` | `=` Directory enforcement is structurally stronger (see drift below) |
| 5 | Skills and capabilities | 40 security-domain skills (15 security, 16 security-operations, 9 compliance) | 817, all security | `+` Large content gap in specific domains |
| 6 | Commands and automation | 18 commands + 3 aliases, multi-platform slash surfaces | None | `=` No counterpart |
| 7 | CI/CD and hooks | 31 hooks with `.sh`/`.ps1` parity, enforced by test | 3 workflows, no hooks | `=` No counterpart |
| 8 | Documentation | AGENTS.md, decision records, known-gaps, per-version docs tree | README, ATTACK_COVERAGE.md, SECURITY.md, CONTRIBUTING.md, CITATION.cff | `~` Ours deeper on governance; **theirs has a published coverage map we lack** |
| 9 | Testing strategy | pytest hook suite, `make validate`, trigger evals (12 skills) | `validate-skill.py`, `validate-agentskills.py`, **0 eval files** | `=` Routing evals are ours alone |
| 10 | Security posture | secret-scan, git-guardrails, skill-security-scan, egress-redaction | Authorized-use policy, SECURITY.md, dual-use disclaimer | `~` Ours is enforcement; theirs is policy text |
| 11 | Developer experience | One-line bootstrap, `nexus-hub` CLI, doctor/repair | `git clone` | `=` No counterpart |

### 3a. Framework mapping - the substantive gap

| Framework | Source | Nexus-Hub | Verdict |
|---|---|---|---|
| MITRE ATT&CK (`mitre_attack`) | 805 skills | 19 skills | `~` Same key, 42x their density |
| NIST CSF 2.0 (`nist_csf`) | 804 | 19 | `~` Same key |
| MITRE D3FEND (`d3fend_techniques`) | 139 | 19 | `~` Same key |
| NIST AI RMF (`nist_ai_rmf`) | 97 | 3 | `~` Same key |
| MITRE ATLAS (`atlas_techniques`) | 93 | 4 | `~` Same key |
| **MITRE F3 (`mitre_f3`)** | **94** | **absent** | **`+` Sixth framework we do not model at all** |
| Coverage output | Markdown + **`attack-navigator-layer.json`** (100KB) | Markdown only (`build_framework_coverage.py`, 278 lines) | `+` Navigator export missing |
| `references/standards.md` companion | 351 of 817 | 19 of 273 | `+` We recommend it in AGENTS.md but barely populate it |

MITRE F3 (Fight Fraud Framework, v1.1, released 2026-04-09 by MITRE CTID with JPMorganChase, Citigroup, Lloyds, Standard Chartered, CrowdStrike, Verizon Business and FS-ISAC) is an ATT&CK-compatible TTP catalog for cyber-enabled financial fraud, covering the ground ATT&CK leaves after initial compromise. It is a genuine gap: Nexus-Hub's `security-framework-mapping` skill and `build_framework_coverage.py` both model exactly five frameworks.

### 3b. Reversals - where the source is better

**Body-size discipline.** `AGENTS.md` sets a <=500-line target and an 800-line hard cap for SKILL.md bodies. Measured:

| | Avg lines | >500 lines | >800 lines | Max |
|---|---|---|---|---|
| Source | 221 | 12 of 817 (1.5%) | 2 (0.2%) | 1,346 |
| **Nexus-Hub** | **491** | **107 of 273 (39%)** | **47 (17%)** | **2,544** |

Nexus-Hub authored the norm and violates it at 26x their rate. `AGENTS.md` grandfathers pre-existing skills, so this is not a rule breach, but it is a measured quality inversion and the most actionable self-directed finding in this report.

**Published coverage map.** `ATTACK_COVERAGE.md` maps 291 unique ATT&CK techniques across 149 parent techniques to all 14 Enterprise tactics, with per-tactic coverage bars and links to the skills teaching each technique. Nexus-Hub's generator can produce the data but nothing equivalent is committed or published.

### 3c. Where Nexus-Hub is clearly stronger

- **Category integrity.** Their `subdomain:` is a free-text frontmatter field. It has drifted to **46 distinct values against a README claim of 29**, with parallel spellings (`red-teaming` 33 / `red-team` 2; `soc-operations` 35 / `security-operations` 28; `identity-access-management` 37 / `identity-and-access-management` 2 / `identity-security` 1; `ot-ics-security` 28 / `ot-security` 1; `zero-trust-architecture` 17 / `zero-trust` 1). Their validator absorbs this deliberately through a `_SUBDOMAIN_ALIASES` map, so it is an accommodation rather than a broken gate - but the accommodation is only necessary because the taxonomy is not structurally enforced. Nexus-Hub's `catalog/skills/<category>/` layout makes this class of drift impossible.
- **Placeholder lint.** Their `validate-agentskills.py` blanket-rejects any `<` or `>` in frontmatter as an injection risk. Nexus-Hub's v3.15.2 lint is semantic: it flags only multi-word lowercase placeholders while exempting CLI notation, uppercase template tokens, and fenced or inline code. Ours is strictly more precise.
- **Routing evals.** `evals/trigger-cases.json` exists in 12 Nexus-Hub skills and 0 of theirs. Nothing in their repository asserts that a prompt actually routes to the intended skill.
- **Name/directory agreement.** Both enforce it (`validate_skills.py:360`; their `validate-agentskills.py`). Genuinely equivalent - `.`

### 3d. agentskills.io conformance - an unmeasured exposure

Their `tools/agentskills-skill.schema.json` encodes the open standard: `name` and `description` required; `license`, `compatibility`, `metadata`, `allowed-tools` recognized as optional; additional top-level keys permitted (`additionalProperties: true`).

Nexus-Hub places `summary_l0`, `overview_l1`, `disable-model-invocation`, `user-invocable` and the framework keys at **top level**. Under the permissive reading this is conformant. Under the schema's own "strict compliance" note those belong nested under `metadata:`. Nexus-Hub flattens skills to `skills/<name>/` for 10+ platforms explicitly "per the SKILL.md open standard" (`AGENTS.md`) yet **never references agentskills.io anywhere** and has no conformance check. We are making a standards-alignment claim we do not test.

`allowed-tools` is a recognized standard field with no Nexus-Hub equivalent, adjacent to our invocation-policy levers. It is **not adoptable on this evidence**: the do-not-invent rule in `AGENTS.md` requires a fetched official vendor document, and a third-party schema's attribution ("agentskills.io open standard (Anthropic, 2025-12-18)") is not that. Nexus-Hub has made this mistake before - the fabricated `.kimi/agent.yaml` companion dropped in v3.15.0.

## Step 5 - Security and Reverse-Engineering Assessment

### 5.1 Threat model comparison

| Axis | Nexus-Hub today | If source scripts were adopted |
|---|---|---|
| New runtime dependencies | None (stdlib Python, Bash, PowerShell) | `requests` plus forensic binaries (Volatility3, KAPE, Impacket, hashcat) |
| Outbound destinations | **Zero by policy** | VirusTotal, urlscan.io, crt.sh, MISP, MITRE CTI, Malpedia (315 files) |
| Credentials required | None | VirusTotal, urlscan, OTX API keys |
| Does source code / prompt / query text leave the machine | No | **Yes** - file hashes, URLs, domains and IOCs are submitted to third parties |
| New commercial relationship | None | VirusTotal / urlscan accounts |
| Maintenance surface | - | +1,095 Python scripts |
| License | MIT throughout | **Apache-2.0 - cannot be relicensed as MIT** |

Two independent constraints point the same way. Adopting their `scripts/agent.py` layer would breach the zero-outbound posture, add credential sprawl, and put threat-intel lookups (hash and IOC submission is a reputation-lookup service, adjacent to the hard-no "search-as-service" class) into the catalog. Adopting their prose would create a mixed-license tree. **Therefore: adopt neither artifact. Adopt the topic gaps only, authored independently from primary sources.** Every item below is consequently bucket 2, `skill-native`: Markdown guidance, zero dependencies, zero outbound calls, zero credentials.

Primary sources for independent authorship (all public, no credential, no new dependency): MITRE ATT&CK, D3FEND, ATLAS and F3; NIST CSF 2.0, AI RMF, SP 800-171; OWASP API Security Top 10 and MASVS; IEC 62443; CISA Zero Trust Maturity Model; NERC CIP; SLSA and Sigstore specifications.

### 5.2 Per-item risk scorecard and 5.3 reverse-engineering viability

| # | Item | Risk | RE class | Grounds |
|---|---|---|---|---|
| A1 | `mitre_f3` optional frontmatter field + validator support | None | `skill-native` | Frontmatter key and list-shape validation. No outbound call, no dependency. |
| A2 | ATT&CK Navigator layer JSON export from `build_framework_coverage.py` | None | `re-full` | Navigator layer format is a public open schema. Generated locally from SKILL.md files already on disk. |
| A3 | Committed + published coverage map (our `ATTACK_COVERAGE.md` equivalent) | None | `re-full` | Generator output committed as a doc. Local only. |
| A4 | agentskills.io conformance validator | None | `re-full` | ~120 lines of stdlib Python over local files. Schema is public. |
| A5 | `references/standards.md` backfill for the 19 mapped skills | None | `skill-native` | Markdown documenting existing mappings against public framework definitions. |
| A6 | SKILL.md body-size remediation (47 skills over the 800-line cap) | None | `skill-native` | Pushes body content into `references/`. Our own declared norm. |
| B1-B12 | ~40 consolidated security skills across 12 gap domains | Low | `skill-native` | Independently authored vendor-neutral guidance from primary sources. Dual-use items carry the authorization gate. |
| X1 | Their `scripts/agent.py` threat-intel wrappers (315 files) | **High** | `drop-outright` | Breaches zero-outbound posture; adds 3 API keys; submits hashes/IOCs to third parties; reputation-lookup-as-service is adjacent to the hard-no list. **MCP Registry Policy** bucket 5. |
| X2 | Verbatim SKILL.md prose reuse | **High** | `drop-outright` | Apache-2.0 cannot be relicensed into an MIT catalog. Legal, not technical. |
| X3 | Vendor-product-specific skills (Dragos, Zscaler, Prisma Access, Guardicore, 42Crunch, Tailscale, NextDNS) | Medium | `drop-outright` as written; **folded into B-items** | Conflicts with Nexus-Hub's vendor-neutral capability convention. Consolidated into vendor-agnostic skills instead. |
| X4 | `allowed-tools` frontmatter field | Low | `drop-outright` **pending evidence** | Do-not-invent rule: needs a fetched official vendor doc, not a third-party schema's attribution. Revisit if primary documentation is found. |
| X5 | Free-text `subdomain:` taxonomy | Low | `drop-outright` | We are structurally better. Adopting it would import the 46-value drift. |

No item reaches bucket 4 (`vendor-intrinsic`); nothing here requires a third party as an intrinsic destination. Nothing requires a new API key, dependency, or data processor, so the **MCP Registry Policy** gate is satisfied by exclusion: the two items that would have triggered it (X1, X3) are dropped by name.

### 5.4 Recommendation ordering

Per Step 5.4, `skill-native` first, then RE builds, then vendor-intrinsic (none), with drops moved to NOT-recommended. P-tier operates *within* each bucket.

**Bucket 1 - skill-native**

| Item | Value | Effort | P |
|---|---|---|---|
| A1 `mitre_f3` field + validator | High | Low | **P0** |
| A5 `standards.md` backfill (19 skills) | Medium | Low | **P1** |
| A6 Body-size remediation (47 over cap) | High | Medium | **P1** |
| B1-B12 ~40 consolidated security skills | High | High | **P1** |

**Bucket 2 - reverse-engineered local builds**

| Item | Value | Effort | P |
|---|---|---|---|
| A2 Navigator layer export | High | Low | **P0** |
| A4 agentskills.io conformance validator | High | Low | **P0** |
| A3 Committed coverage map | Medium | Low | **P1** |

**Bucket 3 - vendor-intrinsic**: none.

**Bucket 4 - NOT recommended**: X1, X2, X3, X4, X5 (grounds above).

## Step 6 - Sequenced Adoption Plan

Ordering respects dependencies: the F3 field must exist before the generator can emit F3 coverage; the generator must emit before a coverage map can be committed.

### Phase 1 - Framework mapping foundation (P0, enables everything downstream)

1. **A1** Add `mitre_f3` as a sixth optional framework field. Touches: the optional-fields table in `AGENTS.md`; list-shape validation in `scripts/validate_skills.py`; the `FRAMEWORKS` list in `scripts/build_framework_coverage.py`; the `security-framework-mapping` skill. Zero Tier-1 cost for skills that omit it, consistent with the existing optional-field contract.
2. **A2** Add `--navigator-layer <path>` to `build_framework_coverage.py`, emitting an ATT&CK Navigator layer JSON from `mitre_attack` values already on disk.
3. **A4** Add `scripts/check_agentskills_conformance.py` (stdlib only, read-only) asserting `name`/`description` presence, kebab-case, name-equals-directory, and the 1,024-char description bound. Register in `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py` - a repo-internal guard needing **no** installer copy step. Wire into `make validate`.

### Phase 2 - Coverage visibility and mapping density (P1)

4. **A3** Commit the generated coverage map and wire a freshness check.
5. **A5** Author `references/standards.md` for the 19 skills declaring framework fields, satisfying the companion-file guidance the orphan-bundle audit already anticipates.

### Phase 3 - Self-directed quality remediation (P1)

6. **A6** Bring the 47 skills over the 800-line cap into compliance by relocating body content into `references/`. Highest-value item that originates from measuring ourselves against the source rather than from the source's content.

### Phase 4 - Security content expansion (P1, largest phase)

7. **B1-B12** ~40 new skills, independently authored, vendor-neutral, consolidating their granular vendor-specific coverage. Two new categories are implied; per `AGENTS.md` ("Ask first: creating a new skill category") both require maintainer approval before Phase 4 opens.

| # | Proposed Nexus-Hub skills | New | Consolidates (source count) | Category |
|---|---|---|---|---|
| B1 | IOC enrichment, threat-actor TTP profiling, threat-intel feed operations, infrastructure pivoting and attribution, leak-site monitoring, certificate-transparency and typosquat monitoring | 6 | threat-intelligence (52) | `security-operations` |
| B2 | ICS protocol anomaly detection (Modbus/DNP3), SCADA and historian threat detection, OT network segmentation and zones (IEC 62443), OT incident response, OT regulatory compliance (NERC CIP) | 5 | ot-ics-security (29) | **new category** `ot-security` |
| B3 | API authorization flaws (BOLA/BFLA/BOPLA), API inventory and shadow endpoints, API rate limiting and abuse detection, API schema validation and gateway controls, JWT attack surface | 5 | api-security (28) | `security` |
| B4 | Applied encryption at rest, TLS and certificate management, key management and HSM, digital signatures and JWT signing, post-quantum migration, cryptographic audit | 6 | cryptography (16) | `security` |
| B5 | Android static analysis, Android dynamic analysis, iOS app assessment, mobile traffic interception and pinning bypass, mobile malware triage | 5 | mobile-security (13) | **new category** `mobile-security` |
| B6 | Zero-trust architecture design (CISA maturity model), ZTNA access-broker deployment, microsegmentation | 3 | zero-trust-architecture (18) | `security` |
| B7 | Honeytoken deployment, deception and adversary engagement (MITRE Engage) | 2 | deception-technology (6) | `security-operations` |
| B8 | Firmware extraction and analysis, UEFI bootkit and Secure Boot integrity, TPM measured-boot attestation | 3 | hardware-firmware (6) | `security-operations` |
| B9 | Smart-contract security audit | 1 | blockchain-security (2) | `security` |
| B10 | Bluetooth and wireless security assessment | 1 | wireless-security (2) | `security` |
| B11 | Vulnerability triage with SSVC; build-provenance verification (SLSA/Sigstore) | 2 | vulnerability-management, supply-chain-security | `security` |
| B12 | Purple-team exercise design and execution | 1 | purple-team (1) | `security-operations` |
| | **Total** | **40** | **~173 source skills consolidated 4.3:1** | |

Result: 40 to 80 security-domain skills; catalog 273 to 313. Tier-1 cost **+40 x ~382 = ~15k tokens (~104k to ~119k, +14%)**. Bounded and acceptable - and only bounded *because* of the 4.3:1 consolidation. A 1:1 import of the same 173 skills would add ~66k tokens.

Every offensive or dual-use skill (B3 authorization flaws, B5 pinning bypass, B9, B10, B12) must carry the authorization gate already used by `advanced-attack-patterns`, `business-logic-abuse` and `ai-attack-patterns`: an explicit scope-and-written-permission precondition.

### Phase 5 - Mandatory closing phase

Architecture refactor, known-gaps update, CI/CD gate, registry consistency across the three `data/` files (hand-edited per convention - **do not** run `build_skills_catalog.py`), `make validate`, `make lint`, `make test`, trigger evals.

## Step 7 - Risks and Conflicts

| Risk | Severity | Mitigation |
|---|---|---|
| **Apache-2.0 to MIT relicensing** | **High** | Independent authorship from primary sources only. No verbatim prose, no scripts, no `references/` reuse. If any text reuse is later desired, the alternative is retaining Apache-2.0 notices on those files, producing a mixed-license catalog - not recommended. |
| Two new categories (`ot-security`, `mobile-security`) | Medium | `AGENTS.md` requires maintainer approval first. Gate before Phase 4 opens. Alternative: fold both into `security-operations` and avoid new categories entirely. |
| Catalog centre of gravity shifts toward security | Medium | 80 of 313 skills (26%) are security-domain, up from 15%. Consistent with the confirmed broad-expansion choice; noted so it is a deliberate outcome. |
| Semver: feature-scale growth in a patch slot | Medium | Flagged in the header. Revisit as v3.18.0 if release discipline is preferred over slot order. |
| Tier-1 growth (+14%) | Low | Bounded by 4.3:1 consolidation. Keep `summary_l0` at <=15 words and `overview_l1` at <=150 words per the existing contract. |
| 40 new skills each need `evals/trigger-cases.json` | Low | Optional by contract (WARN, never FAIL). Prioritize positives-plus-near-miss-negatives for the B3/B5/B9/B10 offensive skills where mis-routing is costliest. |
| Registry churn across three `data/` files | Low | Hand-edit per the documented convention. |
| `mitre_f3` adds a sixth framework to maintain | Low | Optional field; absence is never an error and costs no Tier-1 tokens. |

### Explicitly NOT recommended

- **X1** Their 315 outbound-calling `scripts/agent.py` files - breaches zero-outbound posture, adds three API keys, submits hashes and IOCs to third parties. **MCP Registry Policy** bucket 5.
- **X2** Verbatim prose reuse - Apache-2.0/MIT incompatibility.
- **X3** Vendor-product-specific skills as written - conflicts with the vendor-neutral capability convention; folded into B-items instead.
- **X4** `allowed-tools` frontmatter - fails the do-not-invent rule on current evidence. Revisit only with fetched official vendor documentation.
- **X5** Free-text `subdomain:` taxonomy - would import 46-value drift into a structurally sound layout.
- **Their 777 non-adopted skills** - Tier-1 arithmetic and domain fit. Nexus-Hub is a general-purpose harness; a 75%-cybersecurity catalog serves neither audience.

## Verification

- [x] Step 1.5 scan produced a **CLEAR** verdict before ingestion
- [x] Source type correctly identified (`repo`) and full 11-dimension comparison applied
- [x] Every dimension evaluated for both projects
- [x] Every claim cites a file path, a measured count, or a named convention
- [x] Adoption items have concrete target locations
- [x] Priorities consistent with the value/effort matrix
- [x] Conflicts with existing conventions explicitly flagged (vendor-neutrality, new categories, license, semver)
- [x] Items not recommended include reasoning
- [x] Step 5 complete: threat model table, per-item risk scorecard, per-item RE classification
- [x] Step 5.4 ordering used: skill-native, then RE builds, then vendor-intrinsic (none), drops moved out
- [x] Step 6.5 adoption target resolved and confirmed with the user; recorded in the header
- [x] **MCP Registry Policy** cited by name for every item involving outbound calls, API keys, or new dependencies (X1, X3)
