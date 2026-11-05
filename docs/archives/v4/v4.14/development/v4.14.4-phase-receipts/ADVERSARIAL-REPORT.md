# Adversarial Verification Report: v4.14.4 opt-in git bypass-flag guard

**Covers**: the hostile-input pass over the one runtime surface of the v4.14.4 plan (the `git-guardrails` opt-in mode in both hook languages) and the gate-record parser. Read with the Tier 3 section of [`v4.14.4-last-phase-evidence.md`](../v4.14.4-last-phase-evidence.md).

**Implementation**: `catalog/hooks/git-guardrails.sh` and `catalog/hooks/git-guardrails.ps1` at the Phase 5 tree (Phase 4 commit `6aeb67e58` plus the Phase 5 comment correction). **Breaker**: the member agent that wrote the code (a same-model breaker, which the skill advises against; the cross-model recommendation is carried to the coordinator as a human/second-model follow-up). **Date**: 2026-10-29. **Scope**: command text in the hook payload, `~/.nexus-hub/guardrails.json`, `NEXUS_GUARD_GIT_BYPASS`, the home directory, and the gate-record parser in `tests/skills/test_gate_record_recompute.py`. The breaker changed no code during the attack; fixes from the findings below were applied afterward and reran the affected checks.

## Attack Surface Summary

| # | Entry point | Input source | Trust level | Data type |
|---|---|---|---|---|
| E-1 | `tool_input.command` | the agent (the party being constrained) | untrusted | free text, multi-line |
| E-2 | `~/.nexus-hub/guardrails.json` | user-owned file, readable on every run | semi-trusted | JSON, possibly BOM, empty, array, scalar |
| E-3 | `NEXUS_GUARD_GIT_BYPASS` | the hook's own environment | trusted | `0`, `1`, anything else |
| E-4 | home directory (`HOME`, `USERPROFILE`) | environment | trusted | path |
| E-5 | `gate-record` blocks in the skill | repository file | trusted | table text |

| Entry points analyzed | Adversarial inputs generated | Tests written | Confirmed findings |
|---|---|---|---|
| 5 | about 190 (four probe batches run through both hooks) | 385 in the module, plus 5 for E-5 | 5 (3 fixed, 2 accepted limits) |

## Confirmed Findings

### AF-1: Without jq the `.sh` truncated the command at the first double quote (P0 for the existing blocks)
**Entry point**: E-1. **Category**: encoding and quoting. **Description**: the fallback extraction used `"[^"]*"`, so a command containing any quoted text was cut there and the rest was never scanned, including the pre-existing destructive-command patterns. `echo "hi" && git reset --hard` was allowed on a host without jq. **Proof test**: `test_a_quote_never_truncates_the_command_before_a_later_block` and the parity rows with quoted messages; before the fix the `sh` cases `git commit "--no-verify"`, `git commit -m "a; b" --no-verify`, and `bash -c "git commit -n"` returned 0 while the `ps1` returned 2. **Result**: confirmed on this jq-less host. **Fix applied**: the extraction accepts escaped characters; the same cases now return 2 on both.

### AF-2: Any value passed the PowerShell "is it an object" check (P2)
**Entry point**: E-2. **Description**: in Windows PowerShell 5.1 `-is [pscustomobject]` is true for scalars and arrays, so a file containing `true` or `[]` skipped the malformed-file warning. **Proof test**: `test_a_malformed_switch_file_means_off_with_one_warning[ps1-array]` and `[ps1-scalar]` failed with an empty stderr. **Fix applied**: the check uses the concrete `PSCustomObject` type; both now warn once.

### AF-3: A quoted inline gpgsign value evaded both hooks (P2)
**Entry point**: E-1. **Description**: `git -c commit.gpgsign="false" commit` returned 0 on both. **Proof**: probe batch 2. **Fix applied**: the value pattern accepts a quote on either side; both now return 2.

### AF-4: Quoted or computed flags and subcommands (P3, accepted limit)
**Entry point**: E-1. `git commit "-n"`, `git "commit" -n`, `g''it commit -n`, `F=--no-verify; git commit $F`, `git commit $'--no-verify'`, an alias (`git config alias.c 'commit -n'; git c`), and `python -c` that runs git all return 0 on both hooks (probe batch 4, identical on both). The design states that the hook matches text, not the argument vector git receives, and the decision record lists "a flag built at run time, quoted as a separate word, or handed to a program that runs git later" as a limit. **Disposition**: accepted under the documented trust model; no fix.

### AF-5: Environment skips, plumbing, unset, and full-access mode (P3, accepted limit)
**Entry point**: E-1 and E-3. `HUSKY=0`, `SKIP=lint`, `git commit-tree`, `git update-ref`, `git config --unset commit.gpgsign`, and `permission_mode: bypassPermissions` are not blocked. All are listed in the decision record and both hook headers. **Disposition**: accepted limit; no fix.

## Rejected Findings (Observed Refutations)

| # | Counter-hypothesis | Actual input sources | Per-route results | Observed kill evidence |
|---|---|---|---|---|
| RJ-1 | Typing `NEXUS_GUARD_GIT_BYPASS=0` into the command switches the guard off | command text; hook environment; switch file | command text: executed, still blocked (`NEXUS_GUARD_GIT_BYPASS=0 git commit --no-verify` returns 2 on both, also `env ...` and `export ...;` forms); environment: executed, `=0` allows (by design, the process environment is the trusted source); file: n/a to this counter-hypothesis | `test_the_variable_is_read_from_the_environment_never_from_the_command_text` |
| RJ-2 | A hostile `guardrails.json` crashes the hook and blocks every command | `guardrails.json` content | unclosed, prose, array, empty, scalar: executed, mode off with one warning, exit 0; BOM: executed, still honored; wrong value types (`"true"`, `1`): executed, off with no warning | `test_a_malformed_switch_file_means_off_with_one_warning`, `test_only_the_json_boolean_true_turns_the_mode_on`, `test_a_utf8_byte_order_mark_does_not_hide_the_switch` |
| RJ-3 | `-n` or a flag word inside a commit message triggers a false block | `-m`, `--message`, `-F`, `--file` values; heredoc bodies; here-strings | quoted values: executed, allowed; file-writing heredoc body: executed, allowed; interpreter heredoc: executed, blocked by design; here-string: executed, scanned (conservative) | `ALLOWED_FORMS` rows and probe batch 3 (70 cases, 0 mismatches against expectation) |
| RJ-4 | A malformed gate-record example is silently skipped | `gate-record` blocks | placeholder digest: executed, test fails naming the example; wrong digest after a threshold edit: executed, fails; zero examples: asserts at least three | Phase 2 history and `test_step_5_publishes_worked_examples` |

## Needs Live Validation

| # | Unobserved layer | Minimal safe test | Vulnerable vs. safe response | Potential severity |
|---|---|---|---|---|
| LV-1 | The real Claude Code PowerShell tool sends the same `tool_input.command` shape | In a live session on Windows, after the registration patch lands, run `git push --force` through the PowerShell tool | vulnerable: the command runs; safe: the hook blocks it with `BLOCKED` | High if the field name differs (the block would silently not apply) |
| LV-2 | A live session picks up a mid-session edit of `guardrails.json` | Edit the file in a live session, then run `git commit --no-verify` | vulnerable: still allowed after the edit; safe: blocked on the next command | Medium |

## Untested Areas

| Area | Reason not tested | Risk |
|---|---|---|
| macOS bash 3.2 and Linux | no such host available to this member | low to medium (the script avoids bash 4 features, but it was not run there) |
| `pwsh` 7 | only Windows PowerShell 5.1 was available | low |
| A hook-concurrency or very large command | no performance target in the plan | low |

## Overall Assessment

**Verdict**: CONDITIONAL PASS. **Confirmed vulnerabilities**: 3 fixed (one P0 in a pre-existing path, two P2), 2 accepted limits (P3). **Recommendation**: merge after the PowerShell-tool registration patch lands and the two live checks (LV-1, LV-2) are run by a person.
