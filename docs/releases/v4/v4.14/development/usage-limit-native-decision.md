# Usage-Limit Native Decision Evidence

Status: locally committed source and fresh integrated qualification; hosted integration and installed platform-hook delivery remain pending.
Scope: the user-approved separate maintenance repair within the v4.14 run; frozen member plans and native authority are unchanged.
Source baseline: `fix/usage-limit-native-decision` at `6e3a7dd2ada110971e1ec8ab8b7897b419281e23`, before the maintenance commit and final integrated validation.

## Behavior

The guard creates one home-owned pending decision bound to the canonical project, platform and observed usage episode. Hooks, sessions, reminders and additional crossing windows share it. An atomic claim reserves delivery; claimed, delivered and uncertain delivery remains pending until a genuine submitted answer. Repeated offered context recovers output lost before a claim without creating a second actual question. Repository JSON is not spending authority.

The agent detects its actually exposed question tools, preferring `functions.request_user_input_async` when available. The ordered choices are Wait for reset (Recommended), Hand off, then Continue on credits. Credits are never first or preselected, and silence never authorizes them. Only a host without a native API gets one concise text question. An ambiguous API failure keeps the question pending without a second prompt or text fallback. Unknown usage, cost and reset facts remain unknown.

Answered episodes expire on the existing hysteresis clear rule or a materially changed reset period, including a future reset change. Pending episodes remain shared. Original question, delivery and submitted-answer facts are archived once per decision ID before ledger replacement. Equal history is reusable; conflicting or unavailable history prevents replacement and emits one non-question stop notice stating that no new spending authority exists. It does not invent a native BLOCKED or PAUSED verdict. Current spend observations remain separate from original question facts.

An actual host warning can bootstrap the same lifecycle through `offer-warning` with its genuine warning reference, a caller-attested audit input. No usage figure, cost or reset is invented, and warning-only state cannot exempt the native completion gate. Credits cover that warning episode only. The completion gate conservatively preserves legacy answered decisions and independently confirms current tracked usage before pending, wait or handoff releases a usage stop; unavailable observations remain unknown.

The [usage guide](../../../../guides/usage-limit-handoff.md) documents the claim, delivered, uncertain, answer and warning interfaces. The [session-handoff skill](../../../../../catalog/skills/workflow/session-handoff/SKILL.md) owns host delivery and chat handoff behavior.

## Split Source Qualification

These are separate runs, not one fresh combined suite. The earlier broad result precedes the final targeted protocol changes. Unchanged affected coverage is retained while changed protocol and real-shell gate paths were rerun. The fresh combined integrated-source result is recorded below.

| Scope | Result | Evidence under the private root |
|---|---|---|
| Three affected usage modules before final protocol additions | 406 passed in 46.58 s | `usage-native-worker-1792721716713/reset-compatible.stdout` |
| Final protocol module | 50 passed in 6.71 s | `usage-native-worker-1792721716713/review-fixed-source-pins.json` records the observed result; no separate raw log was retained |
| Final real Bash and PowerShell completion-gate cases | 30 passed in 68.23 s | `usage-native-worker-1792721716713/gate-reset-history-final.stdout` |
| Repository and installed console-window guards | Both exit 0 with silent stdout/stderr | `usage-native-worker-1792721716713/reset-history-console-guards.json` |

The affected files are `catalog/hooks/tests/test_usage_guard.py`, `catalog/hooks/tests/test_usage_probe.py`, `catalog/hooks/tests/test_usage_native_decision.py` and `catalog/hooks/tests/test_completion_gate_usage_handoff.py`. All four were run together through the pinned hidden Python/pytest launcher with `-q -p no:cacheprovider` for the integrated qualification below. Do not sum the separate results into a combined passing-suite claim.

Regression-first failures remain in `reset-history-red.stdout`, `warning-bootstrap-red.stdout` and `future-reset-pinned-old-red.stdout` in the worker evidence folder. Final targeted cases cover unknown-reset clear/re-cross episodes for wait, handoff and credits; future reset changes; immutable archive collisions/failure; offered-output recovery; direct warning delivery; original cost facts; and request/answer replay refusal. Old per-window prompting and repository-decision expectations now assert shared-ledger behavior; detection, probe and security coverage remains.

## Integrated Source Qualification

The usage implementation was preserved in local commit `6bb1c6ea38a720c89ec12da91237bb69cc6f87ea` before a guarded merge of committed checker/console integration `d0f59f3736757ac260565a0787f47a71b8863ea7`. The merge applied 26 incoming paths without conflicts and preserved all 12 named usage source, metadata and evidence files byte-for-byte; official guard proof reports zero accepts.

On that combined source, the four affected files passed together: **440 passed in 160.41 seconds**, with JUnit reporting 440 tests, zero failures, zero errors and zero skips. Hidden Python PID 3328 exited 0. Raw stdout, stderr, JUnit, launch and terminal-process receipts are retained under `usage-native-integration-1792728214634`. The source and installed console guards passed silently; the expanded source guard also passed for the installer command. Spelling and release-document link checks passed; skill validation passed with zero errors and 66 warnings. Strict registry and attribution checks passed before the local implementation commit.

The canonical manifest contains 2063 managed entries and matches the staged index. The final source CLI refuses replay of the genuine private preview claim with exit 1 and `decision already answered`, so no second native question was emitted. The native run-record SHA-256 remains `246a0a40f4e28ffc02c3acc957dce4627d4ff3f1848c19d3cb359922590b884a`. These local results do not establish hosted integration or installed adoption.

## Checker Followup Integration

PR #521 merged to develop at `7c3260743fc660919516f65f4b852c82e0d6021a` after all 46 checks passed on head `ea6e611fbbbe4f110055891bfb6cde723bc1c782`. Its post-merge run passed, and the committed merge tree matches the tested merge tree. A guarded merge into the fresh LF usage checkout preserved 11 usage source, metadata and evidence files byte-for-byte. The only conflict was the generated manifest; regeneration from the merged index produced 2064 managed entries, SHA-256 `2fcb9debbac4bbda1687db3968353efaca9310bd4e25e1649d2efd5faf543229`, with zero accepts for these source changes.

The first fresh four-file run reported 439 passed and one Cursor decision-claim persistence failure in 112.37 seconds. The persistence helper exposed no underlying error code, so no root cause is claimed. The private state path measured 207 characters. One standalone retry and then 100 independently parameterized Cursor cases passed; diagnostic wrappers logged and re-raised underlying I/O errors without changing behavior. The fresh four-file rerun passed **440 tests in 118.77 seconds**. These are separate runs, not an accumulated test count. Raw first-run, diagnostic and rerun receipts are under `usage-native-lf-preparation-1792775695172/merge-checker-1792777042693`. The unexplained initial failure is retained.

Runtime adoption and installed hook distribution remain open. A separate read-only installation review found that accepted installer activity left stale guard records. The user authorized exactly 90 official diff/accept/check sequences for the reviewed current hashes; all 90 completed, installed bytes and native authority stayed unchanged, and no further accepts are authorized. This exception did not authorize adoption or substitute for complete source and transaction qualification.

## Genuine Private UI Preview

The coordinator called the real `functions.request_user_input_async` tool once for a clearly labeled private preview. Request `call_a30e19c503a34d24bba9b336db04f24c` was actually emitted, and the genuine submitted answer was Wait for reset (Recommended). The real source CLI bound delivered and answer transitions and read back `decision: wait`. A repeated claim was refused with `decision already answered`.

The actual host reply exposed `questionItemId` as `["request_user_input_async","call_a30e19c503a34d24bba9b336db04f24c",0]`, with no separate submitted-message identifier. That genuine question-item reference is the recorded response identifier. It is not a separate globally unique answer ID, cryptographic host attestation, or proof that the CLI independently authenticated the host submission. Agents must supply IDs observed from the actual interaction; no synthetic authorization ID was created.

The isolated preview used synthetic 99.5 percent usage and a test USD 1 allowance. The question explicitly restricted the answer to the fixture. It did not pause the real v4.14 goal, authorize real credits, observe live account usage, or alter a genuine native run record. Retained receipts are `native-ui-preview-session/genuine-host-reply.json`, `genuine-binding-result.json`, `latest-source-readback.json` and `replayed-claim-refused.json` under the worker folder. They record observed host interaction and are not server-signed approval evidence.

## Cooperative Writer Boundary

The source probe and decision writers join `~/.nexus-hub/state/usage-probe/activity.lock` through a Windows byte lock or POSIX flock. Module import has no filesystem/network effects. The adopter holds exclusive ownership before protected baselines through mutation, final checks or rollback. Writers check the canonical `.runtime-adoption.lock` marker before and after acquiring ownership. A present marker or unavailable lock permits validated cache reads only, with no live credential/network fetch or decision writes. Process exit releases the OS lock; no presence-only stale eviction steals ownership.

Coverage is limited to cooperative usage probe/cache/decision writers. Native checker and completion-gate state writes, other installers/test sessions, and older installed platform hooks remain outside this rendezvous. The reserved quiet interval still excludes those operations. This maintenance has not distributed the source hooks to installed platform locations; runtime-only adoption does not deploy them. Separately verified authorized distribution remains open.

## Private Updater Qualification

Updater proof is separate from actual runtime adoption and source publication qualification. Every artifact below is explicitly `UNPUBLISHED_PRIVATE_FIXTURE`. No live qualifier or live updater was run.

| Candidate | Private result | Limit |
|---|---|---|
| V12r2 `059510738597957b8de46dba349280856ceddc65ef1a3e1f56b5175cf814f42d` | Positive transaction, injected post-swap rollback and retained-helper refusal passed | Rollback/refusal restored original bytes and physical identities; proofs retain V12 labels |
| V13 `555d9585cbee31a01056f7d905c2d9bdc8ebcf0a788bcbfa49f9f7591ed5c5c2` | Fresh positive transaction and separately captured 10 closure cases passed | Only immutable source artifacts were reused; home/work and identity baseline were fresh |
| V14 `c5976a798480d327013540df888984ee4edf9630e695ebf49dccd597d2cb8692` | Fresh positive transaction and separately captured 10 closure cases passed in 9.620 s | Exact new managed count 2063; V13 differs only in the 2062-to-2063 count constant |

V14 adds the actual canonical-LF `catalog/hooks/tests/test_usage_native_decision.py` to the pinned private 2062-file source. The old 2059 tree remains immutable. New manifest SHA-256 is `ef2357adb1164642b170480d7019c19d8f5d0e7256b09efdf27c382b70e89d25`; added test canonical SHA-256 is `e6e3da505164cbc138b144fcfcf23552ad25dc53bb56ebe3163344e519180064`. Old/new verifiers report clean 2059/2063 results; runtime verification reports 10. Actual `record member-implement-start --help` and `check-member --help` both return 0. Before baseline and after transaction, a competing OS lock is excluded while a real source guard reads a private cached 99.5 percent crossing without usage writes or live probes.

V14 summary: `runtime-adoption-v12-candidate-oct23/v14-e39dd7a8/qualification-v14.json`, SHA-256 `510c8cd82dc74759332ab7f89af9e94fdc81b327efc5e58be72601f019af9ac0`. Closure receipt: `runtime-adoption-v14-candidate-oct23/closure-v14-result.json`. Earlier V14 preparation is preserved in `v14-private-qualification-7a0789df`: Windows rejected its long private path before receipt creation or adoption; a fresh sibling with short paths passed without updater changes.

The shared private source guard remains canonical `44f0609197bdab160d50cd78f3f95ce8e5e9368b1caefc81299ec27a1eca0ae2`. These transaction fixtures do not establish final published guard provenance. Separate provenance coverage and future matched-source adoption must establish that boundary. No idle desktop observation, live platform-hook deployment, real spending or machine-wide lock guarantee is claimed.

## Source Pins and Integration Boundary

Raw source hashes below are retained in `usage-native-worker-1792721716713/review-fixed-source-pins.json`. Line-ending normalization can produce different canonical-LF hashes; raw hashes are not substituted for manifest pins.

| File | Raw SHA-256 |
|---|---|
| `catalog/hooks/_usage_probe.py` | `fed7eb7f7200a088673d959fcf1256485a907937b168280758053fb0a86b1553` |
| `catalog/hooks/usage-guard.py` | `1383d074b98be124b8a803dffdf32eaee1d01ee87eb4e8961a4e29e2bf96cd27` |
| `scripts/completion_gate.py` | `027dee8f850da71067cbfa0ea2de66a2a13f62919611b4ba160ce67a47ac99ee` |
| `catalog/skills/workflow/session-handoff/SKILL.md` | `ec8093c1d53d93e76ba9e39bff7b0f7a00a11e0bd3443cbbe7eda753ac10dbf8` |
| `docs/guides/usage-limit-handoff.md` | `f69016c7232335ee20738eb1abd3a22a1e774b37cd7cb2125950ebca9be966d7` |
| `catalog/hooks/tests/test_usage_guard.py` | `a1076532d384f3ca1bdc0b9085f6ef1b58dd08e08dd4bb34a3d0c0c208c7b7dd` |
| `catalog/hooks/tests/test_usage_probe.py` | `16f37660e60c534664d08a26826cb2a81282b94a4affe77d9058bf06110185f7` |
| `catalog/hooks/tests/test_completion_gate_usage_handoff.py` | `c803da7d0dd91aae73677b8047c4ea514fc7cdda91b0f9e600f5e479c40ccd6f` |
| `catalog/hooks/tests/test_usage_native_decision.py` | `3a5d5e9c726dcb86d489464a21038becda46873a5c0ed9c89b8c55a1aea1c786` |

Private evidence root: `%TEMP%/nexus-v4140-native-hook-budget-oct17`. Local files/test outputs are not publication, deployment or completion receipts. The coordinator owns metadata, manifest generation, final integrated tests, attribution, commit, publication and reviewed runtime adoption. Native plan authority, budgets, run records and installed native scripts were not edited. Guarded source/document writes use the pinned official helper with zero accepts; documentation apply proof is retained separately with final raw candidate hashes.


## Final Review and Local Verification

The frozen 17-file maintenance diff was reviewed across all 10 directory bundles with correctness, maintainability, testing, project-standards, security, performance, API-contract, reliability, adversarial and agent-native lenses. Two P2 findings and one P3 finding were corrected: the adoption assurance now excludes native gate/checker writes, later sessions receive the existing stopping decision as non-question context, and the configuration describes shared episodes rather than per-session questions. Independent delta review approved the fixes. Session status retains at most 128 valid session notices, never grants another claim or spending authority, and never emits a Stop continuation. Missing identifiers or notice-persistence failure preserve conservative stopping context.

Five targeted cases failed before the status fix. The final four-file observed run passed all 451 cases in 107.60 seconds, including 11 new status cases. Earlier attempts are retained: one wrapper timed out without a verdict; a reconstructed environment omitted registered PATHEXT and caused 14 PowerShell adapter failures; controlled Get-Command and a single PowerShell case verified the environment correction. Two obsolete cross-session silence assertions were updated. A corrected run then passed 450 with one decision-write failure whose underlying OS error was unavailable. All 300 isolated repetitions passed, and the final observed run logged no Path.write_text or os.replace errors. The isolated failure remains unexplained; no retry workaround or repair of its cause is claimed. Receipts are retained under review-status-fix-1792778896118 in the private evidence root.

The indexed supply-chain manifest contains 2064 entries with SHA-256 5f966e212766d14acb20f87e0351c091376987bcb1eb5f4f70fcadde437ba53b. The private V17r2 updater passed 24 read-only accepted-installation admission cases and the unchanged 28 closure plus 23 wrapper unit cases. The admission observer preserved the actual 95 script files, clean identities, both manifests, pinned source inputs and native authority, with zero additional accepts and no adoption. These bounded results do not establish final merged-source qualification, a complete production mixed-baseline transaction, runtime adoption or platform-hook delivery.
