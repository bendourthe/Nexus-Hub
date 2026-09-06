# Repository-Native CI Profile Guide

**Project**: Nexus-Hub
**Introduced**: v4.0.0
**Engine**: [`scripts/ci/`](../../../../../scripts/ci/)
**Contract**: [`ci-cd-lifecycle-contract.md`](ci-cd-lifecycle-contract.md) section 3

How to run Nexus-Hub's validation locally, what each profile costs, what it writes, and how an agent uses it during a plan phase without starting remote CI.

The point of the engine, in one sentence: the definitive command list lives in the repository, so a developer and a runner execute the same thing, and a green local run means what a green CI run means.

## Quick reference

| Profile | Command | Typical duration | Use it when |
|---|---|---|---|
| `fast` | `make ci-fast` | under 10 seconds | before every commit; during a phase |
| `full` | `make ci-full` | 10 to 20 minutes | at a phase boundary, and before the final commit |
| `platform` | `make ci-platform` | 2 to 20 minutes per host | when a change touches shell, PowerShell, or installer paths |
| `report` | `make ci-report` | under a second | to re-render evidence without re-running anything |
| `release` | `make ci-release` | under a minute | as part of the release flow only |

Where `make` is unavailable (a plain Windows shell), call the script directly. Everything `make` does is a one-line delegation:

```powershell
python scripts/ci/run.py --profile fast --reports-dir reports
python scripts/ci/run.py --profile full --reports-dir reports
python scripts/ci/run.py --profile platform --reports-dir reports
```

## What each profile runs

Rather than reproducing the command list here, where it would drift from the source, ask the engine. This resolves every command for the current host and exits 0 without executing anything:

```bash
python scripts/ci/run.py --profile full --list
```

The listing shows each group, its change-scope key, whether it is blocking, and which commands are skipped on this host and why.

| Profile | Contains |
|---|---|
| `fast` | catalog JSON parses, hygiene (Unicode, personal paths, docs conventions, doc budgets), workflow security, version sync |
| `full` | everything in `fast`, plus the catalog validators, security scans, platform contracts, docs validators, the hook and repo test suites, and all six extension suites |
| `platform` | shell lint (POSIX), PowerShell AST parse (Windows), and the Windows PowerShell 5.1 hook and installer legs |
| `report` | nothing. Aggregation only |
| `release` | version sync, platform read-contract freshness, and an advisory branch and repository-settings report |

Two design choices worth knowing:

- **`platform` is deliberately small.** A check that runs everywhere belongs in `full`, where it is paid for once. `platform` holds only what genuinely differs by host, so a three-OS matrix is not three copies of the same run.
- **`release` is never a validation re-run.** By the time a release runs, the integration pull request has already validated the tree. Re-running the suite on the release event would bill twice for the same answer.

## Dependencies

The engine itself is standard library only. Two profile COMMANDS have a dependency, and both are hard rather than optional:

| Dependency | Needed by | Why it is not optional |
|---|---|---|
| `PyYAML` | `fast`, `full` (the `workflows` group) | `check_required_check_coverage.py` parses every workflow file and REFUSES to pass without it. A silent pass there would re-permit the stranded-required-check defect the guard exists to catch. |
| `shellcheck` | `platform` (the `shell-lint` group, POSIX only) | a missing linter is reported as MISSING, which fails the run. "The tool is absent" and "the tool passed" must not look the same. |

A workflow job that calls a profile must install these. `ci.yml`'s `validate` job gets PyYAML transitively (it installs `pre-commit`), which is why the omission in `post-merge.yml` was invisible until that workflow ran the same profile on its own. An implicit dependency is one that only the first caller without it discovers.

## Options

| Option | Effect |
|---|---|
| `--profile <name>` | required; one of the five |
| `--list` | print the resolved commands and exit 0. Runs nothing |
| `--reports-dir <path>` | write report artifacts here. Omit to run without writing any |
| `--platform linux\|macos\|windows` | override host detection. Useful for inspecting another host's resolved commands with `--list` |
| `--base <revision>` | scope the run to what changed since that revision |
| `--quiet` | suppress per-command output on success. Failures always print |
| `--json` | print the machine-readable summary to stdout |

### `--base` and change scoping

`--base` classifies the diff and skips groups nothing changed touches:

```bash
python scripts/ci/run.py --profile full --base origin/develop --reports-dir reports
```

The classifier FAILS CLOSED, and the reason is worth stating: expressed as a workflow-level path filter, a misclassification meant the workflow did not start, which was loud. Expressed as a job-level condition, the same misclassification SKIPS a job, and a skipped job reports success. Silent.

So every ambiguous case runs everything:

| Situation | Decision |
|---|---|
| no `--base` given | run everything |
| the revision cannot be resolved | run everything |
| the diff is empty | run everything |
| a changed path matches no known prefix | run everything |
| a root-wide file changed (`Makefile`, `AGENTS.md`, an installer) | run everything |
| every changed path is documentation prose | run the docs group only |

The last row is the only skip the classifier will make on its own, and the reason the module exists. Every skip is reported with a reason in the run summary; a skip you cannot see is indistinguishable from a pass.

## Reports

With `--reports-dir reports`, a run writes:

```text
reports/
  summary.md                 concise, human-readable, ASCII-safe
  summary.json               the same content, machine-readable
  junit/<group>.xml          one JUnit suite per group
  metadata/environment.json  host, OS, interpreter, tool versions, timings, status
```

`reports/` is gitignored. The artifacts are per-run evidence, never source.

Three properties the reports are designed around:

- **A failing run still reports.** Every artifact is written after a failure, and each writer is attempted independently so one unwritable file does not cost the others. A run that fails and reports nothing is indistinguishable from a run that never started.
- **Two identical runs render identically.** Paths are repository-relative, files are written with LF endings, and no wall-clock value appears in a comparable field. A report you cannot diff is not evidence.
- **Credentials never reach an artifact.** Values of environment variables whose NAME contains `TOKEN`, `SECRET`, `PASSWORD`, `APIKEY`, or `CREDENTIAL` are replaced, longest value first, plus a backstop pattern for common token shapes. Matching on the name survives a vendor changing its token format; matching on the shape does not.

## Exit status

`0` when every required command passed. `1` when any required command failed, timed out, or could not be found.

A missing executable is a FAILURE, not a skip. "The tool is missing" and "the tool passed" must never look the same, and a `shutil.which` fallback that quietly skipped would make them identical.

An `advisory` command (currently only the docs-retention reporter) prints its failure and does not change the exit status.

## Using this during a plan phase

The lifecycle forbids a non-final phase from starting remote CI, so local profiles are how a phase proves itself:

1. **During the phase**: `make ci-fast` after each meaningful edit. Under ten seconds.
2. **At the phase boundary**: `make ci-full`, plus `make ci-platform` if the phase touched shell, PowerShell, or installer paths.
3. **Record the CI impact** (runbook step 8.3) rather than editing a workflow: name any new command, dependency, environment variable, test path, or artifact, and whether the pipeline already covers it. A no-op record is a valid outcome and is still written.
4. **Commit locally.** Do not push.
5. **In the final phase only**: run the terminal reconciliation via `[[cicd-architect]]`, complete the full local gate, then publish once.

## Relationship to the existing targets

`make validate`, `make lint`, and `make test` are retained and unchanged; they remain the fastest way to run one slice by hand.

Their relationship to the profiles is explicit rather than implied: `ci-full` runs a superset of `validate` plus `test`, so a green `ci-full` implies a green `validate`. The profiles do not copy the Makefile's command list, and the Makefile's `ci-*` targets do not copy the profiles' list. Each is a one-line delegation to `scripts/ci/run.py`.

That single-source property is the whole point. Before v4.0.0, `ci.yml` re-declared the validator sequence as 31 separate steps, and the two lists had already diverged in production: a duplicate YAML key silently dropped a security validator from CI for a period while the local list still ran it. A drift in that direction is invisible, because the check that stopped running still passes everywhere anyone looks.

## Adding a check

1. Add the command to the right `Group` in `scripts/ci/profiles.py`. It must already be a repository command a developer can run by hand; a profile that reimplements a validator has created a second source of truth.
2. Give it a timeout. A command that hangs must fail, not wait.
3. Scope it with `platforms=` if it only makes sense on one host. Never scope it with a runtime `which` check, which produces an invisible skip.
4. Run `python scripts/ci/run.py --profile <name> --list` and confirm it resolves.
5. `python -m pytest tests/ci -q`. The suite asserts unique names, present timeouts, known scope keys, and that `fast` and `release` run no test suite.

No workflow edit is needed: `.github/workflows/` calls the profile, not the command.
