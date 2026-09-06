# Repository-Native Profiles, Reports, and Migration

The operational detail behind `SKILL.md` Steps 3, 7, and 9. Read cold; each section stands alone.

## 1. Profile contract

A profile is an ordered list of command groups. Nothing more. The value is in what it refuses to be: it is not a second implementation of the repository's validators, and it is not tied to a CI provider.

### Inputs

| Input | Required | Meaning |
|---|---|---|
| `--profile` | yes | one of `fast`, `full`, `platform`, `report`, `release` |
| `--platform` | no | override the detected host class; used to select the host-specific group |
| `--reports-dir` | no | where report artifacts are written; defaults to `reports/` |
| `--quiet` | no | suppress per-command output, keep the summary |
| `--list` | no | print the resolved command list and exit 0 without running anything |
| `--json` | no | emit the machine-readable summary to stdout |

`--list` is not optional in practice. It is what lets a test assert profile contents without executing minutes of work, and what lets a reviewer see what a profile will do before it does it.

### Outputs

| Output | Always |
|---|---|
| exit status | 0 only when every required group passed |
| `reports/summary.md` | yes, including after a failure |
| `reports/metadata/environment.json` | yes, including after a failure |
| JUnit XML per test group | when the group is a test runner that emits it |
| coverage file | when the runner emits one |
| SARIF or a SARIF index | when a static-analysis step emits one |

### Execution rules

- Each group runs with an explicit working directory. Never rely on an inherited one.
- Each command carries a timeout. A hung command must fail, not wait forever.
- Fail fast within a group; continue to the next group unless the failed group is declared blocking.
- Aggregate the exit status across groups. A profile that returns 0 because the last command happened to pass is worse than no profile.
- Redact secrets from captured output before it reaches a report. Match on known secret-shaped environment variable names and on the values of any variable whose name contains `TOKEN`, `SECRET`, `KEY`, or `PASSWORD`.

### The five profiles, by content

| Profile | Contains |
|---|---|
| `fast` | formatting, linting, syntax and schema parses, cheap structural validators. No test suite, no install. |
| `full` | everything in `fast`, plus the repository's complete validator chain, the complete test suite, coverage, and security scans. |
| `platform` | the host-specific subset: shell and interpreter variants, path semantics, native installer paths, anything whose behavior differs by operating system. |
| `report` | aggregation only. Reads what the other profiles wrote and produces the summary and metadata. Never re-runs a check. |
| `release` | packaging, manifest and version consistency, provenance, artifact integrity, publication dry run. Never a validation re-run. |

`report` being aggregation-only is what makes it safe to call after a failure.

## 2. Report directory schema

```text
reports/
  summary.md                    human-readable, appended to the provider run summary
  summary.json                  the same content, machine-readable
  junit/
    <group>.xml                 one file per test group
  coverage/
    coverage.xml                or the runner's native format
    html/                       optional, not uploaded by default
  sarif/
    index.json                  list of SARIF files with their producing tool
    <tool>.sarif
  metadata/
    environment.json
```

### `summary.md` required content

- Overall status: PASS, FAIL, or PARTIAL.
- One row per group: name, status, duration, counts.
- Coverage percentage where measured.
- Security findings by severity where scanned.
- Platform results where the `platform` profile ran.
- Total duration.
- Tool versions.
- Paths to the detailed artifacts.

Keep it short enough to read without scrolling. A summary that requires scrolling has become a log.

### `environment.json` required keys

```json
{
  "profile": "full",
  "host": "runner-or-hostname",
  "os": "Linux",
  "os_release": "6.x",
  "shell": "bash 5.2",
  "python": "3.11.16",
  "tools": {"shellcheck": "0.9.0"},
  "started_at": "2026-08-25T10:00:00Z",
  "finished_at": "2026-08-25T10:06:12Z",
  "status": "PASS"
}
```

Timestamps are UTC and ISO 8601. Never record a credential, a token, a full environment dump, or an absolute path containing a user name.

### Retention

| Artifact | Retention |
|---|---|
| run summary on the provider surface | provider default |
| uploaded report bundle | 7 days, explicit |
| coverage HTML | not uploaded |
| release artifacts | governed by the release process, not by this |

Seven days is chosen deliberately: long enough to debug a failure someone reports the next working day, short enough that the storage cost of a busy repository stays trivial. State the number rather than inheriting the provider's default, which is commonly 90 days.

## 3. Determinism

A report is only useful if two runs of the same tree produce comparable output. Sources of non-determinism to eliminate:

- Wall-clock durations in the machine-readable summary. Keep them in `summary.md`, exclude them from any comparison.
- Iteration order over a filesystem. Sort every glob result.
- Absolute paths. Emit repository-relative paths.
- Locale-dependent formatting. Force a stable locale for the run.
- Unordered set output from a scanner. Sort findings by file, then line, then rule.

## 4. Pinning

| Dependency class | Pin |
|---|---|
| CI provider actions and plugins | immutable commit identifier, plus a version comment |
| language runtimes | exact minor version in the profile's declared floor |
| test and lint tools | exact version in a lockfile or manifest |
| container base images | digest, not tag |

Every ceiling on a dependency carries an adjacent comment stating the unacceptable or unknown newer-version behavior, why it matters, the last verification date, the evidence observed, the newer-version test result when one was run, and the exact condition for lifting it. Where the original reason cannot be established, record that uncertainty rather than inventing a justification.

## 5. Existing-pipeline comparison fields

Step 9 of `SKILL.md` compares field by field. This is the list, and the shape of each finding.

| # | Field | PASS requires |
|---|---|---|
| 1 | Provider detected | the provider is named, or "none detected" is recorded |
| 2 | Profiles exist | all five, each runnable from one documented command |
| 3 | No duplicated validator | every pipeline step maps to a profile group, not to an inline command list |
| 4 | Feature-push runs nothing | no validation workflow triggers on an ordinary branch push |
| 5 | Integration gate is complete | the full and platform profiles run on the integration pull request |
| 6 | No duplicate post-merge suite | no workflow runs the complete suite on both the pull request and the merge |
| 7 | Post-merge is minimal | the merge event runs only smoke, publication, or provenance |
| 8 | Release is separate | tags and approved dispatch run only the release profile |
| 9 | Aggregate required check | exactly one per validation workflow, unconditional, allowlist verdict |
| 10 | No per-leg required context | no matrix leg name appears in the required list |
| 11 | Scoping is job-level | no workflow-level path or branch filter on a workflow producing a required check |
| 12 | Runner selection | hosted by default; self-hosted only where the isolation rules are met |
| 13 | Expensive legs pre-merge | every high-multiplier host leg runs on the integration pull request |
| 14 | Immutable references | every third-party action or plugin is SHA-pinned with a version comment |
| 15 | Least-privilege permissions | explicit at workflow or job scope in every workflow |
| 16 | Caching | keyed to a manifest; absent from cold-install jobs; no credentials cached |
| 17 | Concurrency | superseded validation cancels; releases and deployments do not |
| 18 | Untrusted forks | no secret exposure, no privileged trigger variant, no self-hosted execution |
| 19 | Reports produced | summary, JUnit, coverage, SARIF where applicable, metadata |
| 20 | Reports published | run summary on every result; artifacts uploaded unconditionally with explicit retention |
| 21 | Deployment boundary | deployment runs only from protected events or approved dispatch, over a validated artifact |
| 22 | Failure recovery | documented, and it requires a local reproduction before a re-run |
| 23 | External settings | documented in a runbook, not mutated automatically |

### Finding shape

```text
Field: 6 -- no duplicate post-merge suite
State: FAIL
Evidence: ci.yml triggers on pull_request into develop AND push to develop; the
          push leg additionally enables the macOS and Windows matrix legs
Cost: the merge run is more expensive than the pull-request run that already
      proved the same tree
Smallest change: drop the push trigger from ci.yml; move the merge event to a
      new minimal post-merge workflow
Decision: <approved | declined>
If declined: recorded as <version> known gap <id>, owner <who>, next step <what>
```

A finding without `Evidence` is an opinion. A declined finding without a recorded gap is a decision nobody will remember making.

## 6. Failure recovery

| Failure | Response |
|---|---|
| a profile group fails locally | fix it locally; no commit until the group is green |
| a profile crashes rather than failing | this is a profile defect, not a code defect; the runner must still write a summary and metadata |
| a required check fails after publication | classify, reproduce locally, fix, re-gate locally, then amend or add one narrowly scoped stabilization commit |
| a check fails and cannot be reproduced locally | do not re-run blindly. The gap between local and remote IS the finding: an environment difference, a missing local dependency, or an interpreter version floor |
| post-merge smoke fails | treat as an incident on the integration branch; do not start the release |
| a release step fails | stop. Do not tag or publish. Return to the integration branch |

The "cannot reproduce locally" row is the one that matters most. A repository whose CI catches a class of defect its local gate cannot has a hole in the local gate, and re-running until green hides it. Nexus-Hub found this the hard way with an interpreter version floor: a green local run on a newer interpreter proved nothing about the older one that actually gated the merge.
