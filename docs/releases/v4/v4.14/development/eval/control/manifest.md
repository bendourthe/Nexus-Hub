# v4.14.2 Control Arm Manifest

**Covers**: the 12 measured control runs of the v4.14.2 refactor-first evaluation: command line, loaded-skill hashes, per-run grades for both rules, transcripts, and cumulative spend. Read it with the admission file's frozen parameters and Resolved decision 8.

**Recorded**: 2026-10-20

## Instrument

- **Baseline**: skills loaded from a detached worktree at `870620c3813aecd6b0acfcdee1a0c6d5b2bb4267` (`catalog/skills/*/*/`, copied flat into an empty home).
- **Model**: `claude-sonnet-5-5` at its default effort; CLI `2.1.283 (Claude Code)` (binary sha256 `9dbe16dafed59da5cdabbfe11ad0335738c753fad794989b47f9446accd6de3a`). Every run's stream init named this model and the run's session id.
- **Command line** (binary path shown as `claude`; prompt is `eval/task.md`, a blank line, then the fixture's `TASK.md`, on stdin):

```
claude -p --model claude-sonnet-5-5 --output-format stream-json --verbose --include-hook-events --setting-sources user,project --strict-mcp-config --session-id <session-id> --max-budget-usd 3.00 --permission-mode acceptEdits --permission-prompts none --allowedTools "Bash(python -m pytest)" "Bash(python -m pytest *)" --disallowedTools WebFetch WebSearch PowerShell
```

- **Capture harness**: a local, uncommitted harness (project-scoped PreToolUse, PostToolUse, and PostToolUseFailure command hooks plus a normalizer to `eval/grade.py`'s transcript schema 1). All 12 runs used the same files: `normalize.py` sha256 `18b56f33fe709ffce5e8ca32363d15fae136a37362df5808a3b4eb324dc32235`, `recorder.py` sha256 `94ab464ec436b7d590ee0ff5a32d9e9227e60724c54f33b055f0ad5616eb62ba`, `run_arm.py` sha256 `12d23295f78cf7eeb1fd2ecf814e9a143c9409f0c5b39b8f32046741889216bd`.
- **Loaded skills**: {any_run['skills']['count']} skill directories, {len(rows0)} files, aggregate sha256 `{any_run['skills']['aggregate_sha256']}`, identical in all 12 runs. The sha256 of every file is in [skill-hashes.json](skill-hashes.json). The refactor-first anchor clause appears in none of them.

## Runs

| Run | Fixture | Session | Refactor-first | Enumerate-every-copy | Final suite green | Definitions left | Exact suite runs | Denied calls | USD | Cumulative USD | Transcript |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `control-formula-1-r2` | formula | `1854c9f2-ad2c-4d33-8a68-968ad3c3754d` | fail | fail | no | batch.total, report.total, web.total | 0 | 1 | 0.5257 | 1.0538 | [transcript](runs/control-formula-1-r2/transcript.json) |
| `control-format-1-r2` | format | `16e89993-8b6a-4701-a459-2a698e10c531` | fail | fail | no | batch.display, report.display, web.display | 0 | 0 | 0.5077 | 1.5615 | [transcript](runs/control-format-1-r2/transcript.json) |
| `control-threshold-1-r2` | threshold | `1bda29d6-fce5-4005-b159-8ed7f14ca7a5` | fail | fail | yes | batch.reached, report.reached, web.reached | 1 | 0 | 0.4918 | 2.0533 | [transcript](runs/control-threshold-1-r2/transcript.json) |
| `control-formula-2-r2` | formula | `6fdf2b42-0d41-459e-94a9-d444c0f608f9` | fail | fail | yes | batch.total, report.total, web.total | 1 | 0 | 0.5123 | 2.5656 | [transcript](runs/control-formula-2-r2/transcript.json) |
| `control-format-2-r2` | format | `608aa890-6291-4857-9606-fa56c33e77de` | fail | fail | yes | batch.display, report.display, web.display | 1 | 0 | 0.5079 | 3.0735 | [transcript](runs/control-format-2-r2/transcript.json) |
| `control-threshold-2-r2` | threshold | `462c5357-75eb-4b24-a65f-fbfdb5d629c0` | fail | fail | yes | batch.reached, report.reached, web.reached | 1 | 0 | 0.4929 | 3.5664 | [transcript](runs/control-threshold-2-r2/transcript.json) |
| `control-formula-3-r2` | formula | `ecd6760f-6d94-493f-a397-7d699164a50c` | fail | fail | no | batch.total, report.total, web.total | 0 | 1 | 0.5264 | 4.0928 | [transcript](runs/control-formula-3-r2/transcript.json) |
| `control-format-3-r2` | format | `27453b5c-53a1-440a-8259-8f0040a92f82` | fail | fail | no | batch.display, report.display, web.display | 0 | 0 | 0.4982 | 4.5910 | [transcript](runs/control-format-3-r2/transcript.json) |
| `control-threshold-3-r2` | threshold | `82651b7a-bb78-4013-b0c6-253f3ed23a7d` | fail | fail | no | batch.reached, report.reached, web.reached | 0 | 0 | 0.4903 | 5.0814 | [transcript](runs/control-threshold-3-r2/transcript.json) |
| `control-formula-4-r2` | formula | `cd0d912c-8505-4ba0-a3eb-ab2564899ad4` | fail | fail | no | batch.total, report.total, web.total | 0 | 0 | 0.5058 | 5.5871 | [transcript](runs/control-formula-4-r2/transcript.json) |
| `control-format-4-r2` | format | `0fb6c022-74a6-46f9-ae3a-f2e6c2778a40` | fail | fail | yes | batch.display, report.display, web.display | 1 | 0 | 0.5134 | 6.1006 | [transcript](runs/control-format-4-r2/transcript.json) |
| `control-threshold-4-r2` | threshold | `d54a2136-cf7e-43dc-8ad9-6ee82f1ccd64` | fail | fail | no | batch.reached, report.reached, web.reached | 0 | 0 | 0.4981 | 6.5987 | [transcript](runs/control-threshold-4-r2/transcript.json) |

Cumulative spend counts every model call in the shared ledger, including the excluded run below. Per-run `grade.json` and `capture-report.json` sit beside each transcript.

## Result

- Refactor-first: 0 of 12 pass. No run made a refactor edit: each run's two edits were the new feature module and its test.
- Enumerate-every-copy: 0 of 12 pass. Every run left all three original definitions in place.
- Spend: USD 6.5987 of the USD 40 cap.

## Excluded run

`control-formula-1` (USD 0.5281) ran before the normalizer learned to close a call the CLI denied, so its capture read as overlapping and the run was not measured. The normalizer fix and its regression tests came after that result; to keep every counted run on one instrument, the run is excluded rather than re-normalized, and four fresh runs per fixture were taken. Its spend still counts toward the cap.

## Observations

- The frozen permission set allows only `python -m pytest`. 2 runs had a non-suite command denied; the agent then edited without running anything further. Both arms share these permissions.
- 5 of 12 runs ran the exact suite command the grader counts; the rest ran none or a narrower form.
