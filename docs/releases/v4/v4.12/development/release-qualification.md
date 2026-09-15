# v4.12.0 release qualification

Release preparation follows the user-approved actual diff from v4.11.2 to integration commit `bd16d3996d9474a6bc43e1ba836049ee7e009cc9`. This record distinguishes completed integration from the tag, publication and downloaded-artifact gates that run afterward.

## Integration and documentation

PR #217 and post-merge run 34925451808 passed. Both live handbooks passed the pre-version check. The release changes only two version constants among the distribution handbook's code inputs; its behavior, sources, generator and final HTML bytes are unchanged. Those two hashes were rebound after reviewing the diff; the existing 200-state rendered evidence still describes the exact output. The overview is unchanged. The [archive snapshot](../../../../archives/v4/v4.12/handbooks/snapshot.json) preserves the map, mapped inputs, outputs and review receipts under their original repository-relative paths.

README counts and internal MCP names match the current catalog. Its new release section covers user attribution, setup checks and enforcement limits. The changelog is the approved actual-diff body; the devlog adds one bounded index row. The design record and portable evidence now name the completed integration. Historical failed receipts remain immutable.

## Layout, Git and CI

The canonicalize-layout detection path found no legacy active version or archive-container migrations. Living handbooks and decisions already exist; the active v4.12 plan and comparison directories are canonical. No unrelated move or deletion is needed. The tracked-file inventory and .gitignore review found no new release scratch files admitted to the tree. Existing duplicated instruction templates and retained evidence are intentional source/distribution or historical copies, not deletion candidates. The snapshot is explicitly archival. No new helper abstraction or project restructuring is introduced by release preparation.

Required checks remain validate, shellcheck, colocation, verify and ci-required. The final feature already added native attribution coverage to Windows and macOS; Linux collects the repository suite. The release makes no pipeline change. Post-merge remains smoke/provenance only. Branch cleanup reports no merged remote candidates and automatic deletion is enabled. Existing unmerged recovery refs and stashes remain preserved. The GitHub About count mismatch (336 versus 337 skills) remains the previously tracked WN-3 advisory.

## Platform contracts

The 2026-09-14 cycle fetched official discovery documentation for Claude, Codex, Cursor, Antigravity, Gemini Code Assist, Gemini CLI, OpenCode, Kimi, Qwen, Windsurf, Pi and Copilot. The release pass additionally checked [OpenClaw](https://docs.openclaw.ai/concepts/agent): workspace AGENTS.md and workspace/managed skills remain supported. The thirteen public contract rows are MATCH; Nexus-AI remains UNVERIFIED because its source is private. Machine verification passes all fourteen declared adapter contracts; that is code-versus-contract evidence, not fourteen live application launches.

The [Cursor hook documentation](https://cursor.com/docs/hooks) and [Aider configuration reference](https://aider.chat/docs/config/aider_conf.html) support the new policy delivery. Claude attribution was verified earlier in this cycle. Other behavioral-default rows retain their previous dated evidence; no fresh verification is asserted for those keys. No live model roster was supplied to the advisory prompting check, so it reports UNKNOWN rather than a fabricated refresh. No prompting freshness marker changes.

## Queued-plan impact and known gaps

- v4.11.1: content impact on T010-T014 and final verification T018-T024. Resume against the now-integrated cache guidance and presentation changes instead of replaying Phases 1-3; geometry and semantic-diagram qualification remain open.
- v4.13.0: content impact on T001 baseline and the final installer/qualification pass. Synthetic native-runner tests must account for installed Git identity prerequisites. The evaluator, trace and isolation owners remain separate; this release does not qualify its native runner or change its order.
- v4.15.0: content and ordering impact on T005-T013. Its planned pre-push hook and both installer activation paths must compose with the new attribution dispatcher, preserve prior hooks and test both guards. Do not overwrite core.hooksPath or duplicate hook ownership.
- Older released plans with unchecked historical tasks are not inferred to be queued. The enumerator reports 84 undeclared statuses; those remain unknown rather than a claim of no impact. No queued plan was edited or renumbered. Preserve the existing sequence and reassess the named tasks before implementation.

Known gaps retain four warnings and four historical quality-gate gaps, with the target-manifest defect resolved. T021 remains open because the user observed five Code-sidebar contributors despite the one-contributor Insights result. A release does not settle GitHub cache state, read-only PR refs, the earlier blocked historical review or the earlier incomplete host run. Portable implementation and required integration checks are complete independently.

## Publication gates

Release-note approval is complete. Local release checks, manifest generation, the protected release merges, immediate pre-tag branch assertion, publication, archive download verification and isolated installed behavior are recorded in external release receipts as they execute. No pending gate is represented here as passed in advance.
