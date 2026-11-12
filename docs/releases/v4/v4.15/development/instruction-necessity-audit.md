# Instruction Necessity Audit

**Version**: v4.15.0
**Date**: 2026-10-31
**Status**: Three approved conversions applied, conditional recurrence absorbed, and focused checks passed; final validation remains open. No instruction was removed.
**Source revision**: `ff69aff882f5cc825939507d326edce904ce65eb`

This audit covers the repository's `AGENTS.md` and separately proposes two contextual changes to distributed instruction templates. The user's global instruction files are outside scope. Every trust boundary, data-loss, security, accessibility, verification, and edit-preservation requirement remains in force.

## Baseline

| Measurement | Before | After |
|---|---|---|
| Source lines, including blank lines | 572 | 572 |
| UTF-8 bytes with checkout line endings | 68,531 | 68,709 |
| Characters after CRLF-to-LF normalization | 67,767 | 67,945 |
| Approximate tokens, existing deterministic `estimate_tokens` | 16,243 | 16,272 |
| Raw SHA-256 | `9a64393530d9874156ae1df6a22e3083ec8d24eab3a94e98027c9928f704f237` | `976bce6e7a7955960a0207f2d8930faebb55665d0a84d556a58f60661b77f731` |
| LF-normalized SHA-256 | `bd651d10235655a9b368613fd1246e3b4a191468ad1e9b2907fdaf7746bf34cf` | `de60e523b4f96da5da7d71f3cd6ab0d304c750d999e2e024f214e511f49016fe` |

The token estimate comes from `scripts.check_memory_integration_budget.estimate_tokens`, also imported by `scripts/measure_rendered_context.py`. It counts word runs and standalone punctuation. It is a repeatable approximation, not a provider tokenizer or a measured prompt-cache result. The plan's 541-line figure describes its historical baseline; it is not the current before figure.

The final root-file estimate increased by 29 tokens after C1 and the two factual alignments below. It does not claim a smaller root instruction file. Across all thirteen substantive templates, the sum of the same estimates changed from 40,770 to 40,236, a reduction of 534. That sum compares repository templates, not any single installed session, and proves no behavioral quality, provider charge, latency, or cache result. All eight budgeted documents remain within their existing word ceilings; no ceiling was raised.

## Enumeration Method

A source unit is one authored normative prose paragraph, list item, or distribution-table row. Multiple clauses within one source unit retain one verdict and one reason. Repeated prescriptions at separate source locations remain separate units, so the count describes the instruction surface rather than a deduplicated policy count. Fenced frontmatter and body examples attach to their introducing required-schema unit; quoted examples, factual inventory, section labels, and historical explanations do not become additional standing rules.

The manual audit contains 165 unique source units: 162 keep, 1 make contextual, 0 remove, and 2 defer. An independent pass scans `AGENTS.md` without reading this table, identifies 149 lexical candidates, excludes 27 reviewed non-obligations, and adds 43 reviewed semantic obligations missed by the lexical scan. The source result is 165. Verification must compare the entire source-anchor set with this table, not merely compare the totals.

## Rule Verdicts

Source references below use line numbers in the pinned baseline. A keep verdict means the named failure mode still exists; it does not certify every historical count or example in the paragraph.

| ID | Source | Rule | Verdict | Failure without the rule |
|---|---|---|---|---|
| R001 | AGENTS.md:7 | Hide Windows console children. | keep | Automation can create visible console windows and steal focus. |
| R002 | AGENTS.md:54 | Route security, operational, OT, and mobile skills to their owning categories. | keep | Similar names can put a new skill in the wrong discovery surface. |
| R003 | AGENTS.md:56 | Discuss new categories and register their plugin scan roots. | keep | An unregistered category can be invisible to plugin discovery. |
| R004 | AGENTS.md:65 | Use concise kebab-case skill directory names. | keep | Invalid names break standard discovery and registration. |
| R005 | AGENTS.md:69 | Supply the required name, description, summary, and overview frontmatter. | keep | Missing fields break discovery or progressive disclosure. |
| R006 | AGENTS.md:80 | Author descriptions with explicit trigger and skip wording. | keep | Implicit descriptions under-trigger or match unrelated requests. |
| R007 | AGENTS.md:82 | Include likely user trigger phrases verbatim. | keep | The discovery layer can miss the user's vocabulary. |
| R008 | AGENTS.md:83 | Include an explicit skip clause. | keep | Broad trigger coverage can invoke a skill for adjacent work. |
| R009 | AGENTS.md:84 | Cover synonyms and adjacent intents. | keep | Literal-only matching omits common user requests. |
| R010 | AGENTS.md:85 | Lead with the action and then its trigger surface. | keep | A description can name a topic without stating its operation. |
| R011 | AGENTS.md:99 | Keep the body within its documented size limits and loading tier. | keep | Large bodies spend context even when supporting detail is unnecessary. |
| R012 | AGENTS.md:101 | Link reference files for on-demand loading. | keep | Supporting material otherwise becomes an unconditional context cost. |
| R013 | AGENTS.md:106 | Move occasionally needed detail out of the main body. | keep | Inlining every case obscures the operational path. |
| R014 | AGENTS.md:107 | Put deterministic heavy operations in bundled scripts. | keep | Repeated prose execution is less reproducible and costs more context. |
| R015 | AGENTS.md:108 | Keep always-loaded frontmatter concise. | keep | Small per-skill excess multiplies across the full catalog. |
| R016 | AGENTS.md:110 | Write skill bodies as executable runbooks. | keep | A topic tutorial can leave the agent without actions or observable gates. |
| R017 | AGENTS.md:116 | Treat invocation-policy fields as optional strict booleans. | keep | Strings or invented defaults can silently change who may invoke a skill. |
| R018 | AGENTS.md:123 | Reject impossible invocation combinations and quoted booleans. | keep | A skill can become unreachable or falsely appear restricted. |
| R019 | AGENTS.md:125 | Keep command-derived skills user-invoked and delegation directional. | keep | Automatic delegation can invoke a user-only command indirectly. |
| R020 | AGENTS.md:127 | Verify platform invocation levers from fetched official documents. | keep | Unsupported control fields can be presented as enforced behavior. |
| R021 | AGENTS.md:131 | Keep framework mappings optional and validate their list shape. | keep | Optional compliance metadata can incorrectly become a mandatory schema. |
| R022 | AGENTS.md:157 | Document declared framework mappings in a referenced standards companion. | keep | A plausible identifier can lack an explanation or public definition. |
| R023 | AGENTS.md:159 | Keep closed OWASP membership distinct from growing framework catalogs. | keep | Shape-only checks accept impossible closed-set IDs; fixed rosters reject new open-set IDs. |
| R024 | AGENTS.md:161 | Keep framework output current and retain operational body requirements. | keep | A generated coverage matrix can be stale or mistaken for executable guidance. |
| R025 | AGENTS.md:165 | Conform to the name and description requirements of the skill standard. | keep | A locally accepted skill can fail downstream discovery. |
| R026 | AGENTS.md:167 | Supply the required ordered body sections and observable verification. | keep | A skill can omit triggers, actions, failure modes, or a proving result. |
| R027 | AGENTS.md:207 | Split or move detail before the body exceeds its hard size cap. | keep | Unbounded body growth makes the working manual difficult to use. |
| R028 | AGENTS.md:211 | Assign one owner to each overlapping concern. | keep | Multiple skills can report the same defect or prescribe conflicting rules. |
| R029 | AGENTS.md:215 | Report missing delegates and continue without inventing their coverage. | keep | A review can appear complete when a required specialty was unavailable. |
| R030 | AGENTS.md:219 | Use real rejected candidates and mode-based finding caps. | keep | Cosmetic findings can bury important defects or imitate thoroughness. |
| R031 | AGENTS.md:223 | Keep optional bundled resources in the documented subdirectories. | keep | Unrecognized resource placement can undermine packaging and discovery. |
| R032 | AGENTS.md:225 | Reference bundled files and rely on recursive skill-tree copying. | keep | An orphan resource can be unusable or duplicated by unnecessary installer edits. |
| R033 | AGENTS.md:231 | Update every catalog-state surface when registering a skill. | keep | One skill can be present in the filesystem but absent from a focused install. |
| R034 | AGENTS.md:233 | Register the skill in the Markdown index. | keep | Human and agent discovery can omit the new skill. |
| R035 | AGENTS.md:238 | Add the skill entry using the existing machine-readable schema. | keep | Consumers can fail on missing or invented fields. |
| R036 | AGENTS.md:240 | Update the category's marketplace count. | keep | The marketplace can advertise an inconsistent catalog size. |
| R037 | AGENTS.md:242 | Make the skill reachable from a module or bundle. | keep | A valid skill can remain inaccessible to focused installs. |
| R038 | AGENTS.md:244 | Reconcile aggregate counts and maintain reviewable catalog diffs. | keep | Catalog membership and displayed totals can diverge. |
| R039 | AGENTS.md:246 | Run the registry emission and strict check procedures. | keep | A hand-written entry can miss shape, text, or reachability defects. |
| R040 | AGENTS.md:250 | Validate catalog integrity and relevant shell syntax after skill registration. | keep | Registration or shell defects can ship without their existing checks. |
| R041 | AGENTS.md:256 | Prefer local capability over external wrappers. | keep | Avoidable external dependencies can expand the data-flow surface. |
| R042 | AGENTS.md:260 | Allow the specified local-only MCP class. | keep | The decision tree can reject a capability with no external destination. |
| R043 | AGENTS.md:261 | Use an instruction-native skill when it is sufficient. | keep | An unnecessary subprocess adds installation and trust costs. |
| R044 | AGENTS.md:262 | Recreate locally executable patterns under an internal owner. | keep | A wrapper can transmit data unnecessarily for locally available logic. |
| R045 | AGENTS.md:263 | Admit a trusted wrapper only when all three conditions hold. | keep | Familiar vendor branding can be mistaken for sufficient justification. |
| R046 | AGENTS.md:264 | Require the vendor to be the user's existing intrinsic destination. | keep | An unrelated third party can receive the user's work. |
| R047 | AGENTS.md:265 | Establish that local recreation does not reduce the data-flow surface. | keep | A remote wrapper can be selected despite a sufficient local alternative. |
| R048 | AGENTS.md:266 | Require substantial value from the remaining external capability. | keep | Small convenience gains can introduce disproportionate dependencies. |
| R049 | AGENTS.md:267 | State the three wrapper conditions in the entry comment. | keep | A registry decision can become unauditable after its original discussion. |
| R050 | AGENTS.md:268 | Drop entries outside the admitted classes. | keep | The allow policy can become an open-ended vendor list. |
| R051 | AGENTS.md:272 | Record the five process and data-flow audit answers. | keep | A configuration can hide its execution and disclosure consequences. |
| R052 | AGENTS.md:274 | Identify who runs the MCP process. | keep | Execution ownership and privileges can be unclear. |
| R053 | AGENTS.md:275 | Identify outbound calls and destinations. | keep | Data can leave the machine without a reviewable destination. |
| R054 | AGENTS.md:276 | Identify required API keys. | keep | Installation can acquire an undisclosed credential requirement. |
| R055 | AGENTS.md:277 | State whether source, prompts, or queries leave the machine. | keep | Users can mistake a local process for local-only processing. |
| R056 | AGENTS.md:278 | State the existing commercial relationship. | keep | An intrinsic destination can be confused with a new service enrollment. |
| R057 | AGENTS.md:282 | Exclude the listed service-only capability classes. | keep | A convenience wrapper can bypass the local-first decision tree. |
| R058 | AGENTS.md:286 | Maintain the authoritative MCP classification matrix. | keep | Registry membership can outlive its evidence and admission rationale. |
| R059 | AGENTS.md:290 | Use generic distributed names and keep provenance in the matrix. | keep | Distributed artifacts can imply unsupported upstream integration. |
| R060 | AGENTS.md:294 | Follow the canonical Markdown guide. | keep | Generated documents can render incorrectly across supported readers. |
| R061 | AGENTS.md:296 | Maintain concise source summaries on durable system documents. | keep | A reader can select an irrelevant or stale document from its header. |
| R062 | AGENTS.md:300 | Separate lists from preceding prose. | keep | A Markdown renderer can merge the list into the paragraph. |
| R063 | AGENTS.md:301 | Use loose lists for items with body content. | keep | Multi-sentence list items become difficult to scan. |
| R064 | AGENTS.md:302 | Avoid fragile two-space nesting. | keep | Renderers can disagree on the hierarchy. |
| R065 | AGENTS.md:303 | Separate nested code fences from list prose. | keep | Code can render as inline or malformed preformatted text. |
| R066 | AGENTS.md:307 | Separate lists, fences, tables, and headings with blank lines. | keep | Structural Markdown can render inconsistently. |
| R067 | AGENTS.md:308 | Use the declared list markers and spacing. | keep | Mixed list syntax makes generated document structure less predictable. |
| R068 | AGENTS.md:309 | Use four-space nested-list indentation. | keep | A nested item can become a sibling in another renderer. |
| R069 | AGENTS.md:310 | Indent nested code blocks at the containing list level. | keep | A code block can leave the intended list item. |
| R070 | AGENTS.md:311 | Use ATX headings, one H1, and no skipped levels. | keep | Heading structure can misrepresent the document hierarchy. |
| R071 | AGENTS.md:312 | Keep each paragraph or item on one source line. | keep | Artificial wrapping creates noisy diffs and fragile generated text. |
| R072 | AGENTS.md:313 | Use ASCII punctuation for English Markdown. | keep | Windows console and encoding paths can corrupt punctuation. |
| R073 | AGENTS.md:314 | Check generated Markdown structure before committing it. | keep | Successful code tests do not detect malformed documentation. |
| R074 | AGENTS.md:320 | Use command naming and instruction conventions. | keep | The filename-derived slash surface can diverge from the documented command. |
| R075 | AGENTS.md:322 | Update command counts when that field exists. | keep | Marketplace metadata can become inconsistent. |
| R076 | AGENTS.md:324 | Choose a compatibility shim or an explicit removal note on rename. | keep | Existing command users can lose their entry point silently. |
| R077 | AGENTS.md:326 | Derive the command list at runtime instead of maintaining copies. | keep | Static command lists drift when a command changes. |
| R078 | AGENTS.md:330 | Keep model intent generic and refresh the per-plan concrete map. | keep | Shared instructions can pin an unavailable or outdated model. |
| R079 | AGENTS.md:338 | Use a Bash shebang and strict mode in hooks. | keep | A failed shell operation can be ignored unintentionally. |
| R080 | AGENTS.md:339 | Give Python hooks a module docstring and type annotations. | keep | Hook contracts and data expectations become harder to inspect. |
| R081 | AGENTS.md:340 | Keep diagnostics on stderr and protocol output on stdout. | keep | A consumer can parse an error message as a successful result. |
| R082 | AGENTS.md:341 | Follow the security-hook implementation patterns. | keep | A guard can fail open on malformed or adversarial inputs. |
| R083 | AGENTS.md:343 | Ship and qualify equivalent PowerShell hook siblings. | keep | Windows can silently lose a guard provided on POSIX. |
| R084 | AGENTS.md:347 | Use native PowerShell behavior and fail in the safe direction. | keep | Emulated shell behavior can introduce encoding or dependency failures. |
| R085 | AGENTS.md:349 | Register existing supported hook events using the established convention. | keep | An invented event or duplicate registration can leave a hook inactive. |
| R086 | AGENTS.md:353 | Reserve Notification for attention or permission waits. | keep | A notifier can interrupt the user at the wrong lifecycle point. |
| R087 | AGENTS.md:354 | Distinguish turn end from task completion and avoid subagent completion alerts. | keep | Routine background progress can produce false completion notifications. |
| R088 | AGENTS.md:358 | Test new hooks through the shared implementation fixture. | keep | One shell implementation can pass while its sibling diverges. |
| R089 | AGENTS.md:364 | Retain tests of durable behavior. | keep | Pruning by age alone can discard useful regression protection. |
| R090 | AGENTS.md:366 | Retain tests for observable shipped CLI and runtime behavior. | keep | User-facing regressions can lose direct coverage. |
| R091 | AGENTS.md:367 | Retain tests of reusable contracts. | keep | Protocol or installer guarantees can change silently. |
| R092 | AGENTS.md:368 | Retain tests of enforcement boundaries. | keep | An allowlist or required rejection can fail without detection. |
| R093 | AGENTS.md:369 | Retain regressions for previously real defects. | keep | A known failure can return after a test cleanup. |
| R094 | AGENTS.md:370 | Retain representative fixtures for recurring failure classes. | keep | A future defect can fall outside overly narrow happy paths. |
| R095 | AGENTS.md:372 | Remove historical-text assertions and consolidate shared invariants. | keep | Wording-only changes can fail many tests without revealing behavior. |
| R096 | AGENTS.md:374 | Reassess large test files before splitting or extracting logic. | keep | Mechanical splits or duplicated fixture logic can hide the true ownership problem. |
| R097 | AGENTS.md:376 | Preserve shell parity coverage during test consolidation. | keep | Deduplication can accidentally remove a supported platform's behavior check. |
| R098 | AGENTS.md:380 | Use existing hook events and matchers for phase automation. | keep | A second event system can depend on a declined extension runtime. |
| R099 | AGENTS.md:384 | Edit behavioral defaults at their single declared source. | keep | Consumers and generated defaults can disagree. |
| R100 | AGENTS.md:386 | Regenerate derived defaults rather than hand-editing them. | keep | The next generation pass can overwrite a manual change. |
| R101 | AGENTS.md:388 | Update only the owned core settings keys in place. | keep | Whole-file serialization can alter unrelated hook registration. |
| R102 | AGENTS.md:396 | Seed only officially verified levers and reachable default-model values. | keep | Invented files or inaccessible model pins can break a user's platform. |
| R103 | AGENTS.md:398 | Require verified classification for every seeded platform. | keep | A newly registered platform can bypass the lever-evidence requirement. |
| R104 | AGENTS.md:400 | Preserve existing user defaults and detection-gate install-time seeding. | keep | Installation can overwrite preferences or configure an absent product. |
| R105 | AGENTS.md:402 | Keep behavioral defaults distinct from file-read contracts. | keep | A coverage claim can be inferred from a setting rather than a verified read path. |
| R106 | AGENTS.md:406 | Keep organization content separate and track its additive ownership. | keep | Disconnect or repair can remove catalog or user-owned material. |
| R107 | AGENTS.md:408 | Preserve organization precedence, manifest ownership, and guidance-only authority. | keep | Imported guidance can gain unintended enforcement or cleanup authority. |
| R108 | AGENTS.md:410 | Explain consequential choices before requesting a decision. | keep | A user can approve an action without understanding its effects or alternatives. |
| R109 | AGENTS.md:418 | Make distributed changes reach supported installer destinations. | keep | A locally correct artifact can remain unavailable after installation. |
| R110 | AGENTS.md:422 | Open the owning integration adapter when debugging a runtime. | keep | Work can target an obsolete or unrelated entry point. |
| R111 | AGENTS.md:448 | Rely on recursive skill copying and preserve each platform's discovery format. | keep | Redundant installer edits or unsupported layout can break discovery. |
| R112 | AGENTS.md:449 | Use the existing command distribution surfaces. | keep | A command can be added locally without reaching its supported hosts. |
| R113 | AGENTS.md:450 | Put command companions in style guides rather than slash-command directories. | keep | Reference prose can become an accidental command. |
| R114 | AGENTS.md:451 | Rely on the existing recursive agent distribution. | keep | An unnecessary copy mechanism can drift from the common installer. |
| R115 | AGENTS.md:452 | Register hook behavior in settings as well as shipping its file. | keep | A copied hook can remain inactive. |
| R116 | AGENTS.md:453 | Use the recursive rule distribution path. | keep | An unnecessary platform-specific copy can miss supported systems. |
| R117 | AGENTS.md:454 | Use the recursive document-template distribution path. | keep | Templates can be present in source but absent from user installations. |
| R118 | AGENTS.md:455 | Propagate shared instruction changes to all thirteen substantive templates. | keep | The five-file parity check can miss the other eight platforms' guidance. |
| R119 | AGENTS.md:456 | Copy shipped standalone scripts explicitly in both installers. | keep | A new capability can exist on only one operating system. |
| R120 | AGENTS.md:457 | Keep platform-defaults source internal and derive its distributed effects. | keep | A source-only file can be mistaken for a directly installed contract. |
| R121 | AGENTS.md:458 | Keep repository-only default-sync tooling out of installer payloads. | keep | Users can receive maintenance tools they cannot use correctly. |
| R122 | AGENTS.md:459 | Keep repository-only required-check tooling internal. | keep | Installer payload can acquire an unsupported maintenance dependency. |
| R123 | AGENTS.md:460 | Reconcile index metadata used by instruction templates. | keep | A newly registered skill can remain absent from installed guidance. |
| R124 | AGENTS.md:461 | Register integration subclasses at the common dispatcher. | keep | An implemented adapter can remain unreachable. |
| R125 | AGENTS.md:462 | Use the project-surface override for project-local integration behavior. | keep | A platform can bypass ownership and overwrite rules of the common installer. |
| R126 | AGENTS.md:468 | Skip installer edits for already recursive artifact families. | keep | Unnecessary copy logic creates a second distribution owner. |
| R127 | AGENTS.md:469 | Add shipped script copies to both installers. | keep | Platform installation can silently omit a required executable. |
| R128 | AGENTS.md:470 | Prefer lazy dependency handling and declare hard requirements in both installers. | keep | A new dependency can break supported machines without a useful recovery path. |
| R129 | AGENTS.md:471 | Apply common template edits to all five lockstep files. | keep | One platform can retain an incompatible instruction contract. |
| R130 | AGENTS.md:472 | Run broad Make validation and lint after edits. | make contextual | The current wording repeats broad checks between edits and selects a tool absent on stock Windows. |
| R131 | AGENTS.md:473 | Document the change under Unreleased. | keep | A shipped behavior change can be absent from release history. |
| R132 | AGENTS.md:477 | Explain each dependency ceiling and its lifting condition with evidence. | keep | A dependency pin can outlive its reason or hide a known data-flow change. |
| R133 | AGENTS.md:483 | Read the platform coverage contract before adding or claiming support. | keep | Similar host names can be mistaken for identical discovery capabilities. |
| R134 | AGENTS.md:487 | Produce required checks from unconditionally triggered workflows. | keep | An untriggered required workflow can remain pending indefinitely. |
| R135 | AGENTS.md:491 | Require an aggregate check rather than a matrix-leg context. | keep | A skipped matrix can fail to produce the required leg name. |
| R136 | AGENTS.md:492 | Explicitly gate dependencies instead of relying on needs alone. | keep | A skipped required check can appear successful after a dependency fails. |
| R137 | AGENTS.md:499 | Apply the stated age and closure retention rules. | defer | The paragraph names legacy archive placement; its owning policy must be reconciled before changing or relying on it. |
| R138 | AGENTS.md:510 | Use repository-native profiles as the canonical validation list. | keep | A hand-transcribed Make target can omit a required check. |
| R139 | AGENTS.md:518 | Prefer one canonical profile invocation over a manually copied step list. | keep | Individually green checks can describe different source revisions. |
| R140 | AGENTS.md:524 | Keep release content on main and avoid direct feature commits there. | keep | Installer users can receive incomplete phase work. |
| R141 | AGENTS.md:525 | Integrate version work through develop. | keep | Feature and stable publication can lose their declared separation. |
| R142 | AGENTS.md:526 | Complete version, tag, and hosted release publication together. | keep | A pushed tag can exist without a downloadable hosted release. |
| R143 | AGENTS.md:530 | Keep intermediate commits local and validate one final integration. | keep | Per-phase remote runs validate knowingly incomplete work and multiply CI cost. |
| R144 | AGENTS.md:532 | Document activation, validation, rollback, boundaries, and references for changed opt-in surfaces. | keep | A user can enable a capability without knowing how to validate or disable it. |
| R145 | AGENTS.md:536 | Record significant decisions with the stated exemptions. | keep | Policy or compatibility decisions can be repeated without their reasoning. |
| R146 | AGENTS.md:538 | Use lifecycle decision locations, alternatives, and prior rejected decisions. | keep | A rejected design can be proposed again without examining why it lost. |
| R147 | AGENTS.md:542 | Never hand-edit generated catalog data except new-skill registration. | defer | This conflicts with line 244's deliberate hand-maintenance and the canonical profile's source ownership. |
| R148 | AGENTS.md:543 | Never commit secrets. | keep | Credentials can enter shared and published history. |
| R149 | AGENTS.md:544 | Obtain required authority for destructive Git operations. | keep | A routine command can discard or rewrite someone else's work. |
| R150 | AGENTS.md:545 | Quote SKILL.md summary values. | keep | Frontmatter can fail YAML parsing downstream. |
| R151 | AGENTS.md:546 | Use the declared new-skill security-score defaults and adjust known limits. | keep | Registration can misstate the scope of its security assessment. |
| R152 | AGENTS.md:550 | Check scope fit before adding implementation structure. | keep | A local task can create speculative production machinery. |
| R153 | AGENTS.md:552 | Name the shipped behavior, live caller, or compatibility contract before adding an abstraction. | keep | Future plans can become unsupported production code prematurely. |
| R154 | AGENTS.md:557 | Validate after catalog JSON changes. | keep | Catalog shape or count defects can ship unnoticed. |
| R155 | AGENTS.md:558 | Retain required discovery frontmatter. | keep | The MCP discovery layer can lose summary and overview data. |
| R156 | AGENTS.md:559 | Include rationalizations and verification in new skills. | keep | A skill can omit failure anticipation or observable completion. |
| R157 | AGENTS.md:560 | Apply Bash safety rules to Bash work. | keep | Shell code can mishandle inputs or continue after errors. |
| R158 | AGENTS.md:563 | Review creation of a new skill category. | keep | Catalog structure can expand without its required scan and ownership changes. |
| R159 | AGENTS.md:564 | Check authority before changing installer scripts. | keep | A distribution change can exceed the approved task's scope. |
| R160 | AGENTS.md:565 | Check authority before changing hook registration logic. | keep | A configuration change can silently change active guardrails. |
| R161 | AGENTS.md:566 | Check authority before version mutation. | keep | A local implementation checkpoint can be mistaken for a release. |
| R162 | AGENTS.md:569 | Keep existing skills unless their deletion is approved. | keep | Installed users can lose a capability without a reviewed replacement. |
| R163 | AGENTS.md:570 | Keep dependencies, environment secrets, and generated build output out of commits. | keep | Published history can contain secrets or large disposable artifacts. |
| R164 | AGENTS.md:571 | Do not skip validation of catalog JSON changes. | keep | A local exception can bypass the catalog's consistency gate. |
| R165 | AGENTS.md:572 | Do not remove discovery frontmatter. | keep | A valid-looking skill can disappear from MCP discovery. |

## Conversion Proposal

The agreed cap is three conversions, with no removals. The actual user preference, received through the coordinator on 2026-10-31, is `Three conversions, no removals (Recommended)`. This records a concrete implementation preference inside the approved plan; it does not modify the signed publication authority. One conversion concerns the root audit; two concern distributed templates and therefore do not change the 165-unit denominator. The coordinator owns the root-file change, and this worker owns only the admitted template counterparts.

| Candidate | Current scope | Proposed trigger | Protection retained |
|---|---|---|---|
| C1 | `AGENTS.md:472`, broad Make checks after edits | At each phase boundary, run affected checks plus the fast profile; run the complete profile once on the finished candidate. New hooks and changed installer delivery retain their targeted checks. | Every required final check, real-boundary verification, and supported-host validation remains required. |
| C2 | Distributed templates, one explanation before every Read, Glob, or Grep call | Explain a new investigation or a sensitive, costly, or surprising read before it starts; one explanation may cover related reads in the same batch. | Required disclosure and any explicit user request for per-call narration still apply. |
| C3 | Distributed templates, mandatory description parameter on every shell tool | Supply the field when the tool exposes it; otherwise state the command's purpose in a concise preceding explanation. | The description remains a plain sentence of at most 120 characters when supported; no nonexistent tool argument is invented. |

Every shared-section change can affect five machine-guarded templates and eight other substantive templates. The eight must be checked individually because five-file parity cannot prove their coverage. A cap of three bounds that work. No change to the user's global `CLAUDE.md` or other global instruction file is proposed.

### Coordinator-Owned Root Delta

`AGENTS.md` is a read-only worker input under the admitted claims. The coordinator applied only the line beginning `5. **Validate**:` under its signed coordinator scope. The coordinator reported strict Unicode, diff, and baseline template-parity checks passing. The worker independently observed exactly one removed and one added root-file line, then completed C2, C3, and the focused tests. T204 can therefore close without this worker writing or accepting a new root-file baseline.

Approved replacement, applied by the coordinator:

```text
5. **Validate**: per phase, run affected checks plus `python scripts/ci/run.py --profile fast`. Run `python scripts/ci/run.py --profile full` once on the finished candidate before publication. Include affected hook-parity and throwaway installer-delivery checks. Outside plans, use the canonical pre-publication gate.
```

### Removal List

Empty, as selected by the user. The audit found no instruction whose motivating failure mode was demonstrated to have disappeared. The two deferred contradictions are not removal approvals and do not authorize a behavioral change.

### Global Recommendations

The user's mandatory per-read explanation and shell-description rules also appear in distributed templates. Their global copies are outside the repository. Keep obeying the current user's instructions during this session; a future distributed-template edit does not retroactively change them.

## Source Enumeration Cross-Check

The independent lexical pass scans nonempty source lines outside fenced code blocks, ignores headings, HTML comments, and table separators, and matches whole words from `must|should|never|do not|required|prefer|use|run|write|before|apply|keep|follow|include|update|register|place|discuss|treat|naming|carry|preserve|filter|gate|record|check|default|every|when|decision|rules`, case-insensitively. It does not read the audit table. Quoted examples are adjudicated separately.

The enumeration and original table apply to the pinned before revision. The coordinator's three root-line changes do not rewrite those historical verdicts. The changed source now has the same 572 physical lines; its two previously deferred facts have the explicit resolutions below.

Reviewed exclusions, all non-obligations:

- Purpose, inventory, loading description, and historical rationale: 5, 11, 46, 96, 98, 102, 254, 336, 362, 389, 414, 416, 481, 494, 528, 554.
- Quoted examples and their introduction or explanation: 87, 89, 90, 92.
- Table headers: 118, 446.
- Reference pointers and introductory labels with no additional obligation: 227, 305, 466, 568.
- The invocation-field table's descriptive value at 120 is covered by its declaring contract at 116 and validity constraint at 123.

Reviewed semantic additions, each inspected in source and represented by its own verdict row: 7, 82, 99, 106, 107, 123, 233, 238, 240, 242, 256, 260, 261, 264, 265, 266, 274, 275, 276, 277, 278, 282, 303, 308, 311, 313, 366, 367, 369, 370, 450, 451, 454, 473, 525, 544, 563, 564, 565, 566, 569, 570, 572. These include imperative verbs outside the lexical seed, inherited list predicates, and explicit schema or distribution rules. They are not inferred from the number of audit rows.

## Boundary Language

The source and all thirteen substantive templates were reviewed for the named boundary concerns. `Autonomous Operation`, `Consequential Decisions`, `Construction Discipline`, `MCP Registry Policy`, and `User Attribution` were compared with their pinned original bodies in every template. All 65 comparisons preserve the original bytes or original absence of a section; generic-instructions has no MCP Registry Policy heading. No safety boundary changed. The two converted conventions govern narration and an optional tool argument, not authority or verification.

Representative source wording is `Before adding a new module, builder, protocol field, CLI option, fixture, or abstraction, name the shipped behavior, the active call site, or the explicit compatibility contract that requires it`. Its trigger is already contextual and remains a keep verdict. The template scope reviewed includes preserving current user content, stopping on destructive actions outside the request, explaining consequential decisions, verification before completion, and keeping platform-neutral bodies free of model-specific claims. No additional boundary-language change is justified by this review. No new model identifier was introduced.

### Template Counterparts

The five lockstep files are base-claude, base-codex, base-cursor, base-gemini, and base-opencode. C3 changed its existing line in all five. C2 changed its existing line in base-claude, base-codex, and base-gemini; the rule was absent in the other two, and no new rule was added. Parity exited 0 after each conceptual change. The worker opened the edited base-codex and base-gemini lines and confirmed their C2 and C3 wording is identical. No invariant block was edited; preservation of the invariant bodies is the valid null branch of this phase's verification expectation.

The eight non-lockstep templates were checked individually:

| Template | Actual C2 counterpart | Actual C3 counterpart | Result |
|---|---|---|---|
| base-google-shared.md | Replaced | Replaced | Both current conventions match the approved triggers; protected blocks unchanged. |
| base-aider.md | Absent, no addition | Replaced | Tool-argument convention changed; protected blocks unchanged. |
| base-kimi.md | Absent, no addition | Replaced | Tool-argument convention changed; protected blocks unchanged. |
| base-openclaw.md | Absent, no addition | Replaced | Tool-argument convention changed; protected blocks unchanged. |
| base-pi.md | Absent, no addition | Replaced | Tool-argument convention changed; protected blocks unchanged. |
| base-qwen.md | Absent, no addition | Replaced | Tool-argument convention changed; protected blocks unchanged. |
| base-windsurf.md | Absent, no addition | Replaced | Tool-argument convention changed; protected blocks unchanged. |
| generic-instructions.md | Absent, no addition | Absent, no addition | Entire file byte-identical; no fabricated counterpart. |

Exactly four existing C2 lines and twelve existing C3 lines changed. The three-conversion cap includes the coordinator's C1. The root audit's original verdict distribution remains 162 keep, 1 make contextual, 0 remove, and 2 defer; its one make-contextual verdict is now applied. The two template conventions remain a separate denominator. The two deferred factual contradictions have now been aligned with their existing owners, as recorded below, without removal or a new policy.

### Deferred-Fact Resolution

| Original unit | Existing owner evidence | Coordinator resolution | Remaining obligation |
|---|---|---|---|
| R137, retention description | `docs/policy/docs-retention.md` state 3 names one minor behind and history only; state 3b requires proven closure or verified transfer for plans and comparisons and keeps ledgers active by default with bounded exceptions. `scripts/check_docs_retention.py` declares `ARCHIVE_AFTER_MINORS = 1`, `AGING_SUBDIR = "development/history"`, and `ARCHIVES_ROOT = "docs/archives"`. | Root retention summary now matches those already-existing rules and the advisory detector. No archive ran and no new permission to move a ledger was granted. | Resolved as a stale summary, not a new retention-policy decision. The policy's old footer description does not override its explicit state or executable constant. |
| R147, catalog ownership | `scripts/check_registry_entries.py` states that the four registry files are hand-edited on purpose, emits paste-ready entries, and never writes. `Makefile` lines 91-100 refuses the legacy catalog builder unless explicitly forced in a disposable copy. Root line 244 already describes deliberate hand-maintenance. | Root names the four hand-maintained registry files and preserves other generated artifacts under their owning generators. No data file or generator was changed. | Resolved as a stale generated-data claim, not a blanket license to edit every data artifact. |

The final disposition has 164 retained or factually aligned units, one applied root contextual conversion, zero removals, and zero unresolved deferred units from this audit. The original 165-row table remains the record of what the audit found before repair. There are still only three contextual conversions in total, including C2 and C3. The root diff contains exactly three replaced lines: C1 plus two factual alignments.

## Recurrence

Owner: the existing `/update release` architecture-refactor step in `catalog/commands/update.md`. Its new handoff triggers only when project instructions or substantive templates changed, reviews only the changed standing rules, and compares available project-local line and approximate-token figures. If no baseline exists, it must say so. Unrelated releases do not gain an instruction audit. No new governance step, skill, command, hook, or validator was created.

The warrant is the approved conventions' distribution impact: C2 had four existing counterparts and C3 had twelve among thirteen substantive templates. The owner uses the project's available baseline rather than hardcoding this repository's 165 source units, 572 lines, or 16,243 estimated tokens. Those measurements remain in this release's audit. The plan's requirement for automated governance qualification is satisfied by the complete reproducible structural and mutation exercise in the Phase 2 history: eight tests passed in 22.00 seconds, including seven independent negative controls. Mechanical success does not prove future agent judgment.

## Inherited Work

- The rewrite prerequisite is satisfied: both the published `v4.12.0` tag and rewritten tip `ba468f5f` are ancestors of the admitted base. The archived v4.12.0 plan records release publication and back-merge. Its earlier decision record's pending-publication sentence is stale and is not proof of an unfinished rewrite.
- `DF-6-v4133` is resolved in the archived v4.13 ledger. Do not reopen it from the plan's historical inherited table.
- `DF-2-v4133` migrated to active v4.14.0 and remains a coordinator reconciliation item. This worker has no authority to edit that ledger or begin paid pilot calls.
- Refresh this audit against the integrated instruction source after the active v4.14.6 through v4.14.8 work lands. A pinned-source audit is not proof about a later instruction revision.

## Verification

- Independent source enumeration and full table/source set equality: PASS, terminal exit 0, `source_lexical=149 exclusions=27 semantic_additions=43 source_rules=165 audit_rows=165 unique_anchors=165 missing=0 unexpected=0`.
- ASCII and document-shape checks: PASS, terminal exit 0, `keep=162 make_contextual=1 remove=0 defer=2; ASCII=clean; fences=balanced; heading_labels=clean`.
- Fast profile: PASS, terminal exit 0, `18 passed, 0 failed, 0 skipped, 0 advisory` in 150.2 seconds. This is the fast profile, not comprehensive validation.
- Baseline template parity: PASS, terminal exit 0, all five lockstep templates present. The strict Unicode scan of both audit documents exits 0.
- The Phase 1 source inspection showed only the T201 plan mark and two new audit documents. Its supported attribution installation created a private worktree Git guard, retained the existing hook chain, and reported VERIFIED. Phase 2 subsequently contains only the approved instruction conventions, conditional release-owner handoff, their evidence, and coordinator-owned source/tracker deltas.
- Phase 2 focused template contracts: PASS, 163 tests in 7.59 seconds. The recurrence exercise: PASS, eight tests in 22.00 seconds. Strict Unicode and diff checks exit 0; template parity exits 0 after each conceptual edit. These are focused results, not the final comprehensive gate.
- The initial Phase 2 fast invocation recorded 16 passes and two failed hygiene checks. After causal repairs, the affected hygiene selection passed eight checks in 99.0 seconds; the final shortened templates passed all 163 focused tests again in 17.01 seconds. Personal-path and word-budget checks exit 0, and no word ceiling changed. Fresh and repeated public Codex and Gemini workspace rendering also passed, preserving surrounding user bytes and delivering exactly one managed body with both new conventions.
- T202 is complete: the user selected three conversions and no removals. T203's generic comprehensive profile obligation is deferred to the finished-candidate gate; the recorded focused checks and fast profile satisfy the phase-1 cadence.
