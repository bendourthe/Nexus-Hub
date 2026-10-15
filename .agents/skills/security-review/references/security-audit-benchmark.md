# Application audit benchmark contract

This reference owns the inert application-audit corpus, source-only projections, deterministic scoring formulas, and two-attempt local evidence lifecycle. Use it when characterizing the security-audit workflow; it does not establish production safety, provider rankings, or a release verdict.

## Fixed corpus and declared inputs

The repository-only corpus contains exactly 16 seeds and 16 non-isomorphic benign controls: eight weakness classes in each of Python and TypeScript. Classes are SQL injection, OS command injection, path traversal, SSRF, unsafe deserialization, broken object authorization, insecure session cookies, and verbose error disclosure. Four holdouts cover one release-blocking and one medium seed per language. No fixture is imported or executed. Python is inspected as an AST; TypeScript uses a bounded two-function grammar that rejects unsupported lexical forms. Imports, module actions, live destinations, executable bits, links, and command payloads are forbidden.

`scripts/build-security-audit-projection.py` validates the frozen source manifest and creates two separately owned temporary roots. Only 32 source files with newly randomized neutral names enter the declared host target. Answers, pairings, severity, regions, oracles, canaries, scorer, README, and projection map stay outside all declared host targets, indexes, prompts, and inputs. Reusing a frozen map reproduces exactly the same source projection in a different physical root. Original hashes are checked before and after; cleanup validates ownership and refuses substituted roots.

The answer-side map is needed for subsequent verification. The lifecycle manager freezes it in an explicitly supplied separate local answer archive, normally `.nexus/security-audit-answers/`, which is ignored and never installed or included in tracked host evidence. Temporary answer roots and raw host records are removed; the minimal frozen map remains in that private archive. Removing the archive prevents future verification and must not be described as a verified replay. This separation does not attest process-wide inability to access other paths.

## Frozen candidate and attempts

`scripts/manage-security-audit-benchmark.py` owns five operations: `prepare-candidate`, `record-attempt`, `score-candidate`, `verify-candidate`, and `render-report`. It never launches a model, host, scanner, provider, source program, or remediation.

The subject manifest covers the security-review bundle, routing authority and manifest, code-search source and package metadata, original source corpus, and answer manifest. Generated evidence and projections are excluded. Candidate identity hashes exactly three canonical inputs: subject-manifest digest, invariant execution-context snapshot digest, and protocol-map digest. The snapshot contains reported host, platform, version, model, settings, registration, routing, timeout, no-retry policy, and `process_attestation: none`.

The fixed order is `sequential: 1`, then `concurrent-four: 4`. Attempt IDs derive from candidate ID plus mode. Candidate ID excludes projections, attempt IDs, receipts, results, and itself. Preparation generates one random projection map after identity calculation, freezes the map once, and publishes `run-plan.json` before recording either attempt. Identical inputs reuse the same plan and map; changing only an ID or projection never authorizes a rerun. A superseding candidate requires changed subject/context/protocol inputs and a corresponding documented reason; previous candidates remain.

Each attempt declares separate source, cache, index, and artifact state, the fixed worker count, the same invariant context, and the actual registered code-search outcome. Record `RAN`, `UNAVAILABLE`, `FAILED`, or `DECLINED`; never silently install a fallback. Root, content, scope, index, configuration, source, answer, projection, map, routing, receipt, envelope, and SARIF bindings are checked. Physical content checks establish local bytes; host execution remains self-attested. No external anchor proves when the plan was created or discovers omitted launches.

## Sole finding input and semantic matching

`scripts/score-security-audit.py` accepts explicit physically contained answer, map, plan, terminal, normalized envelope, and SARIF paths plus the frozen subject digest. The envelope is the sole finding-bearing input. SARIF must exactly equal the serializer's derived projection; its results never enter matching. Strict JSON limits, recursive duplicate-key rejection, Unicode checks, redaction, no-follow reads, identity checks, and path containment apply before scoring.

Every present envelope path must translate through the frozen answer-side map. Benign identities cannot satisfy seeds; unknown paths invalidate the attempt. Locationless findings remain eligible for semantic detection. Match one-to-one in stable seed-ID order using canonical weakness kind and language, plus the required structured source/sink identities when applicable. Qualified symbols must refer to declared modules and valid `RAN` graph/scanner receipts. Semantic matching does not consult the expected vulnerable module or region. Only after matching does location accuracy require that module and overlapping lines. Multiple eligible matches, duplicate IDs, ambiguous mappings, invalid dispositions, conflicting evidence, and unevaluable seeds make the attempt unscorable.

`confirmed` and complete `needs-live-validation` count. `rejected` never counts. `corrected` additionally requires a matching bound pre-remediation finding, a `RAN` remediation receipt, equivalent before/after scanner version and configuration, closed normalized remediation, and a separate read-only `RAN` verifier distinct from the fixer. Any optional remediation needs separate trusted approval and another disposable copy; a structural oracle never proves functional preservation or closes a production patch.

## Exact characterization formulas

Each valid score emits every target as `met`, `not_met`, or `unscorable`. A percentage compares integer products before display rounding. Missing evidence never reduces a denominator.

| Metric | Numerator | Denominator | Target |
| --- | --- | --- | --- |
| Seed recall | Semantically detected seeds | All 16 seeds | At least 90 percent |
| Blocking recall | Detected release-blocking seeds | All release-blocking seeds | 100 percent |
| Location accuracy | Detected seeds in the expected vulnerable identity with overlapping lines | All semantically detected seeds | At least 90 percent |
| Blocking location accuracy | Detected blocking seeds with correct identity and overlap | All semantically detected blocking seeds | 100 percent |
| Routing coverage | Correct positive/negative surface receipts plus selected owners with exactly one valid terminal receipt | Nine surfaces plus all selected owners | 100 percent |
| Required-stage completeness | Required selected stages with valid terminal receipts | All manifest-required selected stages | 100 percent |
| Closure completeness | Valid finding dispositions plus satisfied run-finalization obligation | All findings plus one run-finalization obligation | 100 percent |
| Artifact consistency | Matching frozen input/output relationships | All 20 protocol-required relationships | 100 percent |
| Benign high/critical | Unadjudicated active high/critical findings on benign identities | All 16 benign controls | Zero findings |

The routing evidence projection excludes physical inode identity so separately copied sources retain the same logical routing digest. The underlying physical inventory stays local. Baseline stages keep required-stage denominators nonzero. Selected `NOT_APPLICABLE` stages do not satisfy a required terminal receipt; genuinely unselected optional stages are excluded. Run finalization requires all selected terminal receipts and no failed remediation closure. An empty finding list still has one finalization obligation. Zero detected seeds makes location accuracy unscorable, never perfect. Any missing or mismatched required artifact relationship invalidates scoring rather than reducing its denominator.

Health, graph quality, and requested code-search outcomes are displayed independently. A metric miss or unavailable host outcome is informational. Deterministic corpus, scorer, binding, redaction, retention, or distribution defects block qualification; they cannot become informational target misses.

## Immutable local ledger and outcomes

Authoritative entries live under `ledger/entries/` with sequence, type, attempt ID, and hash in each filename. Hash preimages contain sequence, type, ID, artifact digests, plan digest, and prior-entry hash; they exclude current hash and filename. Terminal/outcome artifacts publish before their entries, using exclusive atomic publication, file flush, and directory flush. Windows uses no-replace `MoveFileExW`; Linux uses `renameat2(RENAME_NOREPLACE)`; macOS uses `renameatx_np(RENAME_EXCL)`. Unsupported primitives fail closed. Publication uses verified directory handles and never overwrites an existing artifact. Recovery accepts only byte-identical expected artifacts and entries.

The first attempt's terminal entry must exist before the second is recorded. Only after both terminals exist may `score-candidate` access answers and publish outcomes. Exactly two terminal entries and two outcome entries are required:

- `evaluated` contains canonical scorer output, including scorer-derived `unscorable`, and binds scorer version/code plus all input/output digests. Verification reruns the scorer and requires byte-identical output in either validity state.
- `not_scored` is limited to pre-scoring `FAILED`, `UNAVAILABLE`, or `DECLINED` with no envelope/SARIF. The lifecycle evaluator derives its reason from the terminal. It is forbidden for `RAN` or answer-dependent scoring defects.

Caller metrics and outcome classifications are never accepted. Verification rejects missing, forked, reordered, swapped, duplicate, stale, or substituted artifacts before rendering. `attempt-ledger.jsonl` is a deterministic non-authoritative projection. Reports derive exclusively from both verified outcomes and list all targets, bindings, actual limitations, and cleanup declarations. The unsigned local ledger cannot authenticate execution facts or prove absence of a completely omitted host launch.

Malformed or divergent supplied evidence is retained as `nexus.application-audit-rejected-input/v1`: only input kind, input digest, and a closed rejection code. Raw text is not retained. The scorer replays that typed invalidity and produces `evaluated/unscorable`; `not_scored` cannot replace it. This proves the retained rejection representation and its bound digest, not later access to the discarded raw preimage. The producer's run fingerprint remains distinct from the benchmark binding digest, and host-stage context uses the existing four-field closure contract derived by `producer_context()`.

## Verification commands

Run the focused repository tests with `python -m pytest -q tests/skills/test_security_audit_benchmark.py tests/skills/test_security_audit_benchmark_lifecycle.py`. Installer parity tests prove that scripts and this reference distribute recursively with security-review while corpus, answers, and raw benchmark artifacts remain absent from installed payloads. See the command-first workflow in `guides/reference/SECURITY_AUDIT.md`.
