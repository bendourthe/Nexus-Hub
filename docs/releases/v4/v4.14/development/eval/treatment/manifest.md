# v4.14.2 Treatment Arm Manifest

**Covers**: the 12 measured runs of the v4.14.2 refactor-first evaluation's treatment arm: command line, loaded-skill hashes, per-run grades for both rules, transcripts, and cumulative spend. Read it with the admission file's frozen parameters, Resolved decision 8, and the control manifest.

**Recorded**: 2026-10-21

## Instrument

- **Skills**: a detached worktree at the Phase 4 commit, at `3c69fb5e7397a42de8bd51005bd486617dee7e8f` (`catalog/skills/*/*/`, copied flat into an empty home).
- **Model**: `claude-sonnet-5-5` at its default effort; CLI `2.1.283 (Claude Code)` (binary sha256 `9dbe16dafed59da5cdabbfe11ad0335738c753fad794989b47f9446accd6de3a`). Every run's stream init named this model and the run's session id.
- **Capture harness**: the same uncommitted harness as the control arm. All 12 runs used: `normalize.py` sha256 `18b56f33fe709ffce5e8ca32363d15fae136a37362df5808a3b4eb324dc32235`, `recorder.py` sha256 `94ab464ec436b7d590ee0ff5a32d9e9227e60724c54f33b055f0ad5616eb62ba`, `run_arm.py` sha256 `12d23295f78cf7eeb1fd2ecf814e9a143c9409f0c5b39b8f32046741889216bd`.
- **Command line** (identical to the control arm; binary path shown as `claude`):

```
claude -p --model claude-sonnet-5-5 --output-format stream-json --verbose --include-hook-events --setting-sources user,project --strict-mcp-config --session-id <session-id> --max-budget-usd 3.00 --permission-mode acceptEdits --permission-prompts none --allowedTools "Bash(python -m pytest)" "Bash(python -m pytest *)" --disallowedTools WebFetch WebSearch PowerShell
```

- **Loaded skills**: 340 skill directories, 1313 files, aggregate sha256 `6da62a133b2e1ec7472754a2614bc04f4a7ed77ea4a214a3d9af5969d64fd629`, identical in all 12 runs; per-file hashes in [skill-hashes.json](skill-hashes.json). The refactor-first anchor clause is present in every run's staged skills.

## Runs

| Run | Fixture | Session | Refactor-first | Enumerate-every-copy | Final suite green | Definitions left | Exact suite runs | Denied calls | Skill invocations | USD | Cumulative USD | Transcript |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `treatment-formula-1-t1` | formula | `a5e5b0cb-3009-4dba-a043-2d60f8beb128` | fail | fail | yes | batch.total, report.total, web.total | 2 | 1 | 0 | 0.6079 | 7.2066 | [transcript](runs/treatment-formula-1-t1/transcript.json) |
| `treatment-format-1-t1` | format | `c5e662d1-3125-45aa-810f-4f233916bf6b` | fail | fail | no | batch.display, report.display, web.display | 0 | 0 | 0 | 0.5057 | 7.7123 | [transcript](runs/treatment-format-1-t1/transcript.json) |
| `treatment-threshold-1-t1` | threshold | `a8891a17-e512-4d9e-820a-331c5d4ff62b` | fail | fail | no | batch.reached, report.reached, web.reached | 0 | 0 | 0 | 0.4997 | 8.2121 | [transcript](runs/treatment-threshold-1-t1/transcript.json) |
| `treatment-formula-2-t1` | formula | `9880cfe7-e016-4228-b77e-6ac1ec593f70` | fail | fail | no | batch.total, report.total, web.total | 0 | 0 | 0 | 0.5122 | 8.7243 | [transcript](runs/treatment-formula-2-t1/transcript.json) |
| `treatment-format-2-t1` | format | `d5ef8499-7425-4f50-8256-04a174e04e13` | fail | fail | no | batch.display, report.display, web.display | 0 | 0 | 0 | 0.5089 | 9.2331 | [transcript](runs/treatment-format-2-t1/transcript.json) |
| `treatment-threshold-2-t1` | threshold | `c244dccd-d9dc-4b84-9d5a-5e475404d988` | fail | fail | no | batch.reached, report.reached, web.reached | 0 | 0 | 0 | 0.5343 | 9.7674 | [transcript](runs/treatment-threshold-2-t1/transcript.json) |
| `treatment-formula-3-t1` | formula | `aafec27b-fb03-4bda-a3b5-477f57a5f007` | fail | fail | no | batch.total, report.total, web.total | 0 | 1 | 0 | 0.5245 | 10.2920 | [transcript](runs/treatment-formula-3-t1/transcript.json) |
| `treatment-format-3-t1` | format | `bcb79fa7-8f89-4dbf-8076-fe2aa732b71c` | fail | fail | no | batch.display, report.display, web.display | 0 | 0 | 0 | 0.5170 | 10.8090 | [transcript](runs/treatment-format-3-t1/transcript.json) |
| `treatment-threshold-3-t1` | threshold | `4ff3b775-cd88-4fff-b9b2-26ae251dc27f` | fail | fail | no | batch.reached, report.reached, web.reached | 0 | 0 | 0 | 0.5177 | 11.3267 | [transcript](runs/treatment-threshold-3-t1/transcript.json) |
| `treatment-formula-4-t1` | formula | `337dcfc3-60e6-4fb8-a844-9c84847d0967` | fail | fail | no | batch.total, report.total, web.total | 0 | 0 | 0 | 0.5062 | 11.8328 | [transcript](runs/treatment-formula-4-t1/transcript.json) |
| `treatment-format-4-t1` | format | `48b353d6-8d7f-470e-911b-c53542a7363c` | fail | fail | no | batch.display, report.display, web.display | 0 | 0 | 0 | 0.5115 | 12.3443 | [transcript](runs/treatment-format-4-t1/transcript.json) |
| `treatment-threshold-4-t1` | threshold | `56987859-8d51-485e-a617-57ef590472d6` | fail | fail | no | batch.reached, report.reached, web.reached | 0 | 0 | 0 | 0.5007 | 12.8450 | [transcript](runs/treatment-threshold-4-t1/transcript.json) |

Cumulative spend counts every model call in the shared ledger in run order, both arms included. Per-run `grade.json` and `capture-report.json` sit beside each transcript.

## Result

- Refactor-first: 0 of 12 pass. Enumerate-every-copy: 0 of 12 pass.
- Skill invocations across the 12 runs: 0.
- This arm's spend: USD 6.2463.
