# v4.9.0 Application-Security Audit Final-Phase Evidence

This active release record covers the local audit implementation, its whole-plan functional review, repository reconciliation, and publication prerequisites. Maintainers use it to distinguish verified deterministic contracts from unavailable host characterization and pending integration evidence.

**Status**: LOCAL GATE PASS; INTEGRATION PENDING. Phases 1-6 are committed; Phase 7 corrections, CI reconciliation and local qualification are complete. This evidence is included in the final Phase 7 commit before publication. No remote success is claimed in this local record.

**Plan**: [Local Agentic Application-Security Audit Pipeline](../plans/v4.9.0-adoption-visa-vulnerability-agentic-harness.md).

**Review inputs**: user authorization to implement the entire plan; Phase 6 commit `ae630cd50cf1458e6c836a4265ab34eed4920925`; integration base `843c147dead74e20c13dd296a8567753e8948a5d`; current Phase 7 working-tree corrections. The final local commit will identify the exact published tree without embedding its own future SHA in this file.

**Integration refresh**: before publication, origin/develop advanced to `b6197859fcd97dac77262d4c90b03e91110c67f0` through PR 189, adding only two v4.11 planning documents. They merged cleanly into the final local tree; all seven documentation checks passed again and the benchmark subject/candidate remained unchanged. The final phase commit incorporates this update so its diff against the remote integration branch contains no apparent deletion of those documents.

## Architecture refactor

The complete bounded detector results and every candidate disposition are retained in [the scan report](qualification/v4.9-layout-public.md) and its [machine-readable evidence](qualification/v4.9-layout-public.json). Large private diagnostic outputs have recorded hashes; their complete candidate projections are preserved without copied source text or private paths. The authoritative Git inventory covers long paths omitted by the existing filesystem helper.

> Tracked baseline: 5,218 files; 196,824,280 bytes; 2,351 documentation files. Duplicate groups: 72, covering 183 files. Empty directories: 6, including 4 placeholders. Single-child directories: 84. Deep directories: 769. Deprecated-term candidates: 762. Working-tree lexical zero-inbound candidates: 1,441. Historical lifespan candidates: 1,383. Historical unresolved links: 811. Known-gap ledgers: 37. Public candidate dispositions: 5,332.

> Source inventory SHA-256: `4351e1553cae074a083dfa5ef09e60e22c8fc6209fc8955d836924d2cba6b5af`. Public projection SHA-256: `50f2c5c73f099c2567e28d555c071122a8268fb18c80b9f8de792c12c838b9f5`.

The in-scope co-location failure was repaired by adding a v4.9 adoption record that references the frozen v4.8 analysis. The original comparison and sibling plans were preserved. `python scripts/check_doc_colocation.py` now exits 0. No unrelated directory, archive, fixture, duplicate, or branch was moved or deleted. Catalog nesting and hash-named benchmark paths retain their contract owners.

## Known-gaps reconciliation

All 37 reachable canonical/archive ledgers have source hashes, recorded open identifiers, and owner/disposition entries in the scan JSON. Legacy singular archive/version layouts contain no tracked ledgers. Historical recorded IDs are not asserted to be current defect totals. Phase 7 does not edit another release's ledger; existing v4.3 CI migration and v4.0 documentation migration ownership is retained. The inherited retarget commit `fb573c8a` appends a plan-location note to the v4.8 ledger without changing its prior findings; that existing branch delta is preserved and distinguished from this phase's reconciliation.

The audit subsection of [known gaps](../known-gaps.md) owns Windows/POSIX coverage qualification (MT-2), terminal CI selection and remote proof (QG-1), and the ancillary private verification-harness cleanup limitation. No malformed graph, corpus, scorer, binding, redaction, retention, mutation, or Goal failure has been deferred. The two graph findings were corrected in shared deep-pass cycle 1.

Fresh v4.5 sequencing evidence:

> PR 162 merged into develop at `765d9f32b158647cb2328972ed72d1f8e8d0c313`. PR 164 merged into main at `8f60904d88d3a29f130a85de1f689c60ed249fa2`; `git rev-parse 'v4.5.0^{}'` returns that same commit. PR 165 back-merged into develop at `51e692ac0544deb7fbdd0a33b1760d203c96f9ca`. Both required ancestry checks against freshly fetched `origin/develop` exit 0.

The prerequisite's [CI run 33944168549](https://github.com/bendourthe/Nexus-Hub/actions/runs/33944168549) and [CodeQL run 33944168546](https://github.com/bendourthe/Nexus-Hub/actions/runs/33944168546) both conclude success for head `b99c43d6611c5ca20275449a4b901f520b0a17f6`. This historical prerequisite evidence does not substitute for the new branch's PR checks.

## Living docs architecture

The scan covers `docs/handbooks/`, `docs/decisions/`, `docs/README.md`, `docs/DEVLOG.md`, and `docs/todos.md`. Decisions pass for 38 records. The separately owned handbook plan retains the atlas/presentation work; this nonvisual audit creates no HTML or invented testing/validation subtree.

> Living navigation now uses `releases/v<MAJOR>/v<MAJOR>.<MINOR>/` and links the current audit plan. The progress tracker reports 336 catalog skills and the six committed audit phases. Markdown remains authoritative. No existing handbook HTML is regenerated.

The frozen scan report's navigation assignment is completed by these Phase 7 edits. Its historical lifespan/link baselines have zero v4.9 source candidates and retain their original owners.

## Git-tree hygiene

Command: `python scripts/check_release_preconditions.py --branches --repo-settings`.

```text
Branch hygiene (merged into origin/develop)
  7 merged branch(es) are cleanup candidates:
    - origin/chore/post-v4.8.0-backmerge
    - origin/docs/release-docs-reconciliation-and-v4.10-plan
    - origin/docs/v4.11-evidence-improvement
    - origin/feat/v4.8.0-agentic-loops
    - origin/fix/owned-temp-file-mode
    - origin/fix/v4.8.0-open-items
    - origin/release/v4.8.0
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  OK: repository description agrees with README.md
```

The check exits 0. No branch cleanup was performed. A fresh diff against `origin/develop` reports no changes under reserved v4.5 release, prompt-injection, egress, execution-isolation, or endpoint-hardening paths.

## CI/CD coverage

The [complete 23-field comparison](qualification/v4.9-ci-preflight.md) records provider detection, repository-native profiles, event separation, runners, aggregate gate, permissions, action pinning, caches, concurrency, paths, artifacts, deployment, and failure recovery. The user's subsequent instruction to resolve the remaining failures and finish Phase 7/integration authorizes the previously presented Windows audit test selection, Git long-path checkout support, and existing interpreter-gate selection. All three changes are applied. The new Unicode regression joins the Windows selection as a direct part of the requested local failure repair; eleven files are now selected. The preflight report preserves the earlier proposal snapshot; current application and review evidence is recorded here.

> Local CI-engine, report, aggregate-gate, and workflow-contract checks: 155 passed. Prepared patch: five files, 120 insertions, two deletions; SHA-256 `ddd250def9f62ccdaf692c6cb03bff7ef4cee1c7bad4469c9b084dd09b4a97ca`. Four proposed regression tests fail on the baseline and pass in the temporary patch check. This is proposal validation, not proof that the working pipeline has changed.

Current application verification: 117 CI contract tests pass after the eleventh-file addition. [Independent CI review](qualification/v4.9-cycle2-ci-review.md) approves the checkout ordering, pre-merge interpreter selection and bounded Windows coverage. No workflow trigger, permission, action pin, job name or repository setting was changed. The full pipeline comparison retains explicitly owned historical migration differences instead of silently rewriting unrelated jobs.

Live protection on main/develop requires `validate`, `shellcheck`, `colocation`, `verify`, and `ci-required`, with strict checks, administrator enforcement, PRs, and resolved conversations. The aggregate must include every supported-OS installer job below; individual matrix names need not become additional protection contexts.

| Required PR installer/Windows job | Local execution | Required remote result |
|---|---|---|
| `bootstrap (ubuntu-latest)` | Unavailable on Windows | Terminal success |
| `bootstrap (macos-latest)` | Unavailable on Windows | Terminal success |
| `bootstrap-windows` | Installer postcondition exercised locally | Terminal success |
| `install-smoke (ubuntu-latest)` | Unavailable on Windows | Terminal success |
| `install-smoke (macos-latest)` | Unavailable on Windows | Terminal success |
| `install-smoke (windows-latest)` | Shared Windows postcondition exercised locally | Terminal success |
| `installer-smoke (ubuntu-latest)` | Unavailable on Windows | Terminal success |
| `installer-smoke (macos-latest)` | Unavailable on Windows | Terminal success |
| `installer-smoke (windows-latest)` | Real PowerShell installer passed locally | Terminal success |
| `tests-windows` | Matching local audit cases exercised; eleven-file selection now wired | Terminal success |

The actual PowerShell 5.1 installer ran with isolated HOME/workspace and the local example organization bundle. `check_installer_smoke.py` reports PASS. [Installed-artifact evidence](qualification/v4.9-final-local-snapshot.json) verifies all 24 security-review bundle files byte-for-byte, fixture/answer exclusion, and real installed closure/SARIF subprocess output. The existing version remains 4.8.0 until the separate post-integration release flow performs a version bump.

[Platform verification](qualification/v4.9-platform-verification.md) records 14 repository contract rows and all 17 default-lever rows, primary sources, and explicit unverified native-host surfaces. Internal contract/default checks pass. The pre-existing Copilot boolean/string discrepancy and Antigravity legacy workflow-path discrepancy retain independent maintenance owners; the audit's native skill delivery does not depend on either. No provider configuration, installer destination, or verification marker was silently changed.

## Tier 3 deep pass

### Inputs and blast radius

Verdict: **run**. The diff changes distributed security-review and agent-presets content, local CLI contracts, a graph-query implementation seam, schema validation, safe filesystem handling, normalized output, SARIF, and benchmark persistence. Positive triggers are distributed behavior, security/schema boundaries, public CLI/output contracts, and generated artifacts. A documentation-only no-op would be false.

The reviewed inputs are the approved seven-phase plan, the user's full-implementation authorization, the integration base and Phase 6 commit above, current Phase 7 fixes, all phase histories, the final benchmark run plan, and the available Windows/Python/PowerShell environment. Native provider invocation and registered code-search host tools are unavailable; the separate local stdio MCP qualification is explicitly identified.

### Whole-plan feature inventory

The matrix covers 15 independently observable feature families. Every row has a representative real boundary exercise. Platform-specific variants and human-host journeys retain explicit limits; this count is not a claim that every platform ran.

| Feature | Task | Artifact | Real boundary and input | Expected and observed result | Environment/evidence |
|---|---|---|---|---|---|
| Backward-compatible application profile | T001-T003 | `security-review/scripts/closure-gate.py` | CLI with legacy, complete, and malformed records | Legacy accepted; malformed profile rejected without target mutation | Windows; Phase 1 history and adversarial report |
| Strict evidence decoding | T001-T003 | `_strict_json.py` | Closure file and SARIF stdin with duplicate/nonfinite/oversized/Unicode inputs | Stable rejection; no partial output | Windows; adversarial report |
| Contained source identity | T002-T003 | `_safe_artifact.py`, `_target_manifest.py` | Real temporary Git trees, hard links, junctions, bound file reads | Unsafe identity/paths rejected; valid content hashed | Windows; dedicated suites, MT-2 for unavailable variants |
| Bounded surface inventory | T004-T006 | `collect-security-audit-inventory.py` | Installed CLI on inert application text | Nine surfaces accounted; incomplete/binary input rejected; source unchanged | Windows; boundary exercise and adversarial report |
| Conditional owner queue | T004-T007 | `resolve-security-audit-routing.py`, routing manifest | Installed resolver on collected and tampered inventory | Planned selected owners, cap four; no owner invocation; invalid evidence incomplete | Windows; boundary exercise |
| Read-only workflow/approval handoff | T007 | `/review`, agent-presets/security-review skills | Contract checks and normalized approved/unapproved remediation records | No default mutation; authorization, equivalent rescan and independent verifier required | Windows; workflow/closure suites; human language review pending |
| Qualified graph queries | T008-T010 | Existing code-search query manager and probe | Real stdio MCP with qualified, missing, ambiguous and bounded inputs | Qualified results, empty missing result, retained ambiguity; unchanged original source/index | Windows; final qualified-explore JSON |
| Graph evidence admission | T008-T010 | `_graph_receipt.py` | Projector plus real closure CLI with absent seed/contradictory receipt | Both invalid routes rejected after cycle 1 | Windows; independent 131-case retest |
| Closure-owned envelope | T011-T013 | `_audit_envelope.py` and closure summary | Real installed CLI with four dispositions and degraded coverage | One canonical envelope; evaluator-owned degraded health; stable dispositions | Windows; installed snapshot and boundary exercise |
| Redacted SARIF | T014-T016 | `_normalized_audit.py`, `emit-sarif.py` | Installed stdin/stdout serializer, repeated input, forged paths/IDs | Two active results, deterministic bytes; malformed input exit 2; no source reads | Windows; installed snapshot and adversarial report |
| Fixed inert corpus/projection | T017 | `_benchmark_corpus.py`, projection CLI, repository fixtures | CLI on 16 seeds/16 benign controls and malformed manifest | Source-only opaque projection; answer exclusion; fixed denominator; no fixture execution | Windows; Phase 6 history and adversarial report |
| Deterministic scoring | T018 | `_benchmark_scoring.py`, score CLI | Bound synthetic envelope/SARIF and invalid identities | Separate recall/location/FP accounting; unknown path unscorable; no release verdict | Windows; 78-test benchmark suite and adversarial CLI exercise |
| Immutable declared attempts | T019-T020 | Benchmark manager, protocol and lifecycle | All five CLI operations; ordering/replacement/drift controls | Exact sequential/concurrent pair; immutable retained entries; invalid order/drift rejected | Windows; adversarial report and final candidate verification |
| Observational report | T019-T020 | Release-only recorder and rendered benchmark Markdown | Final candidate preparation, two terminal recordings, score/verify/render | Both PRE_SCORING_UNAVAILABLE; limitations visible; prior attempts preserved | Windows; benchmark report and current four-entry verification |
| Recursive distribution/exclusion | T021 | Existing installer/flattening and installed security-review bundle | Actual PowerShell installer, byte comparison, installed CLI invocation | All 24 bundle files equal; source/answer fixtures excluded; installed export works | Windows; final local snapshot; six-platform flatten contract suite |

Paths abbreviated to security-review filenames above live under `catalog/skills/code-review/security-review/scripts/`; routing scripts live under `catalog/skills/workflow/agent-presets/scripts/`. Exact commands, phases and baseline results remain in the committed phase histories and [independent adversarial report](qualification/v4.9-adversarial-public.md).

### Rendered surfaces

No browser UI, HTML, PDF, DOCX or PPTX is produced by this plan. SARIF/JSON consumers are exercised through parser/serializer boundaries; Markdown reports through rendering-content and link/format checks. Browser geometry, accessibility and interface-review delegates are not applicable to this nonvisual output. No screenshot or visual-quality claim is made.

### Adversarial and convergence review

The independent adversarial pass exercised 15 entrypoint families, retained nine considered-but-rejected candidates, and identified two confirmed graph-admission defects. Both were fixed and independently retested: 131 passed, zero runtime findings remain. Its prior broader boundary run passed 462 tests with nine explicit platform skips; that baseline is distinguished from the post-fix retest. The report preserves the initial failure rather than rewriting it as a clean first pass.

The [final independent convergence review](qualification/v4.9-final-convergence.md) finds zero missing, partial, contradictory or unrequested implementation features across T001-T021. It independently passes 13 targeted graph/producer/scorer regressions and verifies the current candidate's four entries. Its approval covers implementation convergence; it explicitly preserves unfinished Phase 7 release gates.

### Goal-vs-plan sufficiency

| Question | Answer | Evidence | Change needed now | Owner |
|---|---|---|---|---|
| What did implementation teach that the plan did not know? | The public qualified explore path needed its existing exact resolver reused; evidence admission needed explicit absent-seed and zero-result/location rejection. Windows hash-named receipts exceed legacy Git and validator path limits. | Approved Phase 3 A1, real MCP probe, adversarial AF-1/AF-2, reproduced Unicode failure | Graph and native long-path corrections complete; Windows CI coverage applied | Audit implementation and Phase 7 CI |
| What assumption proved false? | Current host code-search registration was absent, and platform compatibility mirrors/default seeds are not uniformly confirmed by current vendor docs. | Bound empty registration/context and two UNAVAILABLE terminals; platform report | Preserve unavailable characterization and independent platform ownership | Benchmark evaluator; platform maintenance |
| What would a Goal reader expect that no phase delivered? | No missing deterministic feature established by the exercises and independent convergence. Active-host accuracy and real provider invocation remain unavailable, consistent with approved Option A. | Feature inventory, independent zero-gap review, retained target outcomes, explicit assurance contract | Complete final local/remote gates | Phase 7 |
| What requested outcome lacks a task? | The user requested full implementation; T001-T031 cover implementation, final verification and green integration. Tag/release remains explicitly delegated after integration. | User authorization, seven phases, T031 and dispatcher release handoff | Finish pending gates; do not call local implementation a completed integration | Implementation/release owners |

### Shared fix budget and disposition

`fix_rerun_cycles_used = 2` of 3. Cycle 1 corrected absent graph seeds, contradictory zero-result graph receipts, comparison co-location, and directly related living navigation/count drift. Graph/envelope recheck: 126 passed; independent retest: 131 passed; co-location: exit 0; refreshed real MCP and installed CLI checks: exit 0. The changed benchmark subject produced candidate `bd37a8b8e91ba5c28001d068445a6b3e65a97fada223e5c7b1441ab6bdb3506c` and retained both new outcomes.

Cycle 2 followed the complete full-profile failure artifact. A real long filename reproduced the Unicode validator's exit-2 read failure. Native Windows path handling now preserves scanning, exclusions, explicit paths and atomic repair; POSIX semantics remain unchanged. The long-path regression passes, and the [independent validator review](qualification/v4.9-cycle2-validator-review.md) reports zero findings after native/UNC/idempotence and alias/exclusion probes. Git Bash was prepended only to the validation child process's PATH; the actual interpreter gate then passed. The previously repaired comparison check passed again. The affected profile reports 13 passed, zero failed; the other lightweight groups report 22 passed, zero failed. The original test and extension groups remain valid, and changed validator/CI tests pass separately. No test was disabled and no long artifact was excluded.

NOT COVERED: native platform invocation and Linux/macOS-specific filesystem/installer branches on this Windows host; owners are platform-contract verification and MT-2, with exact PR jobs above. Human workflow interpretation is pending the tester's observations. These limits are not converted into passing host metrics.

Ancillary cleanup limit: automatic approval review rejected removal of a separate private synthetic adversarial-harness directory with reason `blocked by policy`. No alternate deletion was attempted. Declared benchmark projection roots and the public MCP disposable copy report complete cleanup; the independent harness residue is separately owned and is excluded from publication.

Gate disposition: **LOCAL GO**, with the documented ancillary and environment limits. Runtime findings are resolved, independent implementation convergence is approved, and all original failing profile groups have successful current-tree reruns. The final Windows selection is exercised by 420 passing audit tests with nine platform skips plus the separate 37-passing Unicode suite with one POSIX skip. No local failure is waived. Hosted installer/check outcomes remain required before integration.

## Goal-vs-codebase review

The Goal is a provider-neutral, local application-audit path with conditional specialists, qualified reachability, truthful closure health, redacted SARIF and bounded observational characterization, using existing owners with no default mutation or new provider runtime.

The feature inventory maps each implementation family to a real exercised artifact. Host recall, location accuracy, benign false positives, stage completeness, fingerprint ratios and concurrency comparisons are UNAVAILABLE for both declared attempts, not zero or successful. The [benchmark report](security-audit-benchmark.md) shows every target and assurance limitation. The independent review approves T001-T021 implementation convergence with zero missing, partial, contradictory or unrequested features; its full requirement matrix and considered/rejected findings are retained in the linked report. The two cycle-2 reviews additionally approve the validator and CI dependency seams. Hosted integration gates remain separate.

## Human/manual testing

Suggestions were sent after implementation: run an authorized read-only `/review security` on a supported host with registered code-search, then one without graph tooling. Confirm conditional routing, visibly degraded coverage, unchanged target files, redacted SARIF and understandable remediation approval. Never execute the inert fixture applications.

Environment/actions/artifacts/deviations: no human observations were supplied; the user instead instructed completion of local stabilization and integration. The current agent host has no registered code-search tools; the local MCP fixture qualification and synthetic CLI checks above do not substitute for human interpretation of these journeys. Disposition: suggestions delivered; human execution NOT PERFORMED. This is a transparent manual-coverage limit, not a fabricated successful run or a waiver of the automated required journeys.

## Full-suite testing and stabilization

Completed command: `python scripts/ci/run.py --profile full --quiet --reports-dir .nexus/v4.9-final-full-reports`. Result: 41 commands passed, three failed, exit 1 in 5,041.3 seconds. Hook tests: 1,319 passed, 35 skipped. Repository tests: 5,007 passed, 77 skipped. All seven extension checks passed. The three failures were Unicode reads of long ledger filenames, the local PATH selecting unusable Bash, and comparison co-location observed before its cycle-1 repair.

Current correction evidence is preserved in [local gate results](qualification/v4.9-local-gates.json). With Git Bash first on the child process PATH, `python scripts/ci/run.py --profile full --only hygiene,interpreters,docs --quiet` passes all 13 commands. The remaining lightweight profile groups pass all 22 commands. The original nine successful test/extension commands plus these current reruns cover all 44 full-profile commands. This is explicitly a composed current-tree gate; the original full invocation did not exit 0. Fresh changed-scope validator/interpreter/CI tests: 160 passed, one platform skip; final CI selection tests: 117 passed. No redundant rerun of unchanged hour-long test groups is presented as necessary evidence.

Fresh focused results available: benchmark 78 passed, 98.63% coverage; integration/contracts/distribution 119 passed; graph/envelope after cycle 1 126 passed; independent graph proof plus those suites 131 passed; safe-artifact focused run 36 passed with seven explicit platform skips. These sets overlap and must not be added into a fabricated unique total. Broader independent baseline: 462 passed, nine skips. Bundle validation: zero errors, 64 existing warnings. CI contract group: 155 passed.

The real final installer passes shared postconditions; all 24 installed audit files are byte-equal and installed SARIF emits deterministic bytes. The final public MCP probe reports original source unchanged, query index unchanged, disposable-copy cleanup complete, nine graph receipts, and graph quality unknown. Unknown quality remains unknown.

Final eleven-file Windows selection: the ten audit files completed with 420 passed, nine skipped in 522.46 seconds; the added Unicode validator file completed separately with 37 passed and one POSIX skip. Both invocations are successful and their scopes are disjoint; this is not represented as one combined invocation. The later integration-base documentation refresh also passes all seven docs commands. All locally applicable gates required for the final commit are complete.

Final candidate replay command:

```powershell
python catalog/skills/code-review/security-review/scripts/manage-security-audit-benchmark.py verify-candidate --root . --candidates docs/releases/v4/v4.9/development/security-audit-benchmark/candidates --answer-archive .nexus/security-audit-answers --candidate-id bd37a8b8e91ba5c28001d068445a6b3e65a97fada223e5c7b1441ab6bdb3506c
```

> Exit 0; candidate verified; four retained entries. Final subject inventory: 159 files; canonical subject digest `1bdbc22f8b3a46e5dd898ad5e37d3ed0641c7a8df4ede106f990e365dd295ed7`. Both attempts have `PRE_SCORING_UNAVAILABLE`. Original source unchanged; declared projection cleanup complete.

The private answer archive is required for independent local replay and is intentionally excluded from installed/public host inputs. All earlier candidate directories and prior derived reports remain preserved; a new candidate was required because graph subject bytes changed. Subject/context/protocol bindings are validated by the lifecycle, not inferred from a Git commit label.

Current checks: Ruff and Python compilation pass for the corrected graph files. A baseline/current Ruff comparison for the validator and CI files finds zero introduced findings; unrelated existing style findings are retained. Strict Unicode passes for the promoted evidence; the repository's Markdown self-check and local-link check are applied directly because `markdownlint-cli2` is not installed. No automated markdownlint success is claimed. The scoped diff is whitespace-clean. The older v4.8 ledger has only the inherited retarget note from `fb573c8a`; Phase 7 leaves it and the sibling handbook plan unchanged.

Model-prompting freshness: the native `codex debug models` enumeration succeeded. Passing its returned slugs to `check_model_prompting_freshness.py --advisory --platform codex` reports DRIFTED: the local CLI's returned roster omits recorded `gpt-6-astra`. This is that CLI's observed surface, not a claim that the active session model or vendor model ceased to exist. The check exits 0, no profile/marker was changed, and model-prompting maintenance owns the next refresh.

## Publication preflight

Branching model: develop/main. Remote: `origin` (`git@github-bendourthe:bendourthe/Nexus-Hub.git`), repository `bendourthe/Nexus-Hub`. Feature branch: `feat/v4.9.0-visa-vulnerability-agentic-harness`. PR target: `develop`. The user's latest instruction explicitly requests finishing Phase 7 and integration after reviewing the pending CI scope. Final publication inputs will be presented at the local commit boundary; no hosted success is claimed here.

The exact final commit SHA and file/commit counts are presented after local gates pass. The user's explicit request to finish Phase 7 and integration supplies authority for this prepared publication and green-check integration; this record does not treat silence as approval. Required checks are `validate`, `shellcheck`, `colocation`, `verify`, `ci-required`, including all supported installer/Windows results named above. A red result reopens stabilization and requires a concrete failure artifact and narrow correction before republishing; no branch-protection bypass is authorized.

Remote run IDs, immutable check URLs, installer artifacts and merge SHA belong in the PR/CI evidence and release handoff keyed to the checked commit. This local record must not be amended merely to narrate checks on its own commit. Post-merge verification remains minimal; version bump, changelog, tag and GitHub Release stay with the separately gated release flow.
