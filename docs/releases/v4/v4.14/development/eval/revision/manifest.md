# v4.14.2 Revision Round Manifest

**Covers**: the 12 measured runs of the v4.14.2 refactor-first evaluation's revision round: command line, loaded-skill hashes, per-run grades for both rules, transcripts, and cumulative spend. Read it with the admission file's frozen parameters, Resolved decision 8, and the control manifest.

**Recorded**: 2026-10-21

## Instrument

- **Skills**: a detached worktree at the Phase 4 commit plus the two uncommitted revised wordings recorded in the evaluation file, at `3c69fb5e7397a42de8bd51005bd486617dee7e8f` (`catalog/skills/*/*/`, copied flat into an empty home).
- **Model**: `claude-sonnet-5-5` at its default effort; CLI `2.1.283 (Claude Code)` (binary sha256 `9dbe16dafed59da5cdabbfe11ad0335738c753fad794989b47f9446accd6de3a`). Every run's stream init named this model and the run's session id.
- **Capture harness**: the same uncommitted harness as the control arm. All 12 runs used: `normalize.py` sha256 `18b56f33fe709ffce5e8ca32363d15fae136a37362df5808a3b4eb324dc32235`, `recorder.py` sha256 `94ab464ec436b7d590ee0ff5a32d9e9227e60724c54f33b055f0ad5616eb62ba`, `run_arm.py` sha256 `12d23295f78cf7eeb1fd2ecf814e9a143c9409f0c5b39b8f32046741889216bd`.
- **Command line** (identical to the control arm; binary path shown as `claude`):

```
claude -p --model claude-sonnet-5-5 --output-format stream-json --verbose --include-hook-events --setting-sources user,project --strict-mcp-config --session-id <session-id> --max-budget-usd 3.00 --permission-mode acceptEdits --permission-prompts none --allowedTools "Bash(python -m pytest)" "Bash(python -m pytest *)" --disallowedTools WebFetch WebSearch PowerShell
```

- **Loaded skills**: 340 skill directories, 1313 files, aggregate sha256 `bfe92c58a48ce9d08ac9b811ba16e63f31aee3b156254b3d259773c3990c0ef5`, identical in all 12 runs; per-file hashes in [skill-hashes.json](skill-hashes.json). The refactor-first anchor clause is present in every run's staged skills.

## Runs

| Run | Fixture | Session | Refactor-first | Enumerate-every-copy | Final suite green | Definitions left | Exact suite runs | Denied calls | Skill invocations | USD | Cumulative USD | Transcript |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `treatment-formula-1-r1` | formula | `88f7add1-1b13-483e-b8ae-7db15b5cea91` | fail | fail | yes | batch.total, report.total, web.total | 1 | 1 | 0 | 0.5382 | 13.3831 | [transcript](runs/treatment-formula-1-r1/transcript.json) |
| `treatment-format-1-r1` | format | `d68a6abc-c16a-4547-98ad-d48101398816` | fail | fail | no | batch.display, report.display, web.display | 0 | 0 | 0 | 0.5266 | 13.9098 | [transcript](runs/treatment-format-1-r1/transcript.json) |
| `treatment-threshold-1-r1` | threshold | `1f21dab2-7591-4381-9a63-4688acf31991` | fail | fail | no | batch.reached, report.reached, web.reached | 0 | 0 | 0 | 0.4945 | 14.4043 | [transcript](runs/treatment-threshold-1-r1/transcript.json) |
| `treatment-formula-2-r1` | formula | `d98d4d2b-f0bb-4286-a0ce-2a95c752eb10` | fail | fail | no | batch.total, report.total, web.total | 0 | 1 | 0 | 0.5242 | 14.9285 | [transcript](runs/treatment-formula-2-r1/transcript.json) |
| `treatment-format-2-r1` | format | `87171914-4c57-4f62-a8af-f0c60a5d1664` | fail | fail | yes | batch.display, report.display, web.display | 1 | 0 | 0 | 0.5108 | 15.4393 | [transcript](runs/treatment-format-2-r1/transcript.json) |
| `treatment-threshold-2-r1` | threshold | `007d70c4-b3e7-4880-8352-5d280e28505b` | fail | fail | yes | batch.reached, report.reached, web.reached | 1 | 0 | 0 | 0.4953 | 15.9347 | [transcript](runs/treatment-threshold-2-r1/transcript.json) |
| `treatment-formula-3-r1` | formula | `867db0cc-73d0-43a2-9df5-c115f89f2ae6` | fail | fail | no | batch.total, report.total, web.total | 0 | 0 | 0 | 0.5301 | 16.4648 | [transcript](runs/treatment-formula-3-r1/transcript.json) |
| `treatment-format-3-r1` | format | `c6ac1062-6b04-4417-a270-e854c67978d3` | fail | fail | no | batch.display, report.display, web.display | 0 | 0 | 0 | 0.5115 | 16.9763 | [transcript](runs/treatment-format-3-r1/transcript.json) |
| `treatment-threshold-3-r1` | threshold | `f0569814-cdb7-451f-a6bf-19fdc189cd34` | fail | fail | yes | batch.reached, report.reached, web.reached | 1 | 0 | 0 | 0.5203 | 17.4966 | [transcript](runs/treatment-threshold-3-r1/transcript.json) |
| `treatment-formula-4-r1` | formula | `d3e77830-aee5-4af2-a081-feffbb18f78c` | fail | fail | yes | batch.total, report.total, web.total | 1 | 1 | 0 | 0.5321 | 18.0287 | [transcript](runs/treatment-formula-4-r1/transcript.json) |
| `treatment-format-4-r1` | format | `c68c408d-c793-4c7e-aa30-df1e6d1d9f8c` | fail | fail | no | batch.display, report.display, web.display | 0 | 0 | 0 | 0.5279 | 18.5566 | [transcript](runs/treatment-format-4-r1/transcript.json) |
| `treatment-threshold-4-r1` | threshold | `42d461b4-0445-4a89-a4a9-43c541ebf5ee` | fail | fail | yes | batch.reached, report.reached, web.reached | 1 | 0 | 0 | 0.5025 | 19.0592 | [transcript](runs/treatment-threshold-4-r1/transcript.json) |

Cumulative spend counts every model call in the shared ledger in run order, both arms included. Per-run `grade.json` and `capture-report.json` sit beside each transcript.

## Result

- Refactor-first: 0 of 12 pass. Enumerate-every-copy: 0 of 12 pass.
- Skill invocations across the 12 runs: 0.
- This arm's spend: USD 6.2142.
