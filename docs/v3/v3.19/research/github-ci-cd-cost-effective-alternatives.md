# Cost-Effective CI/CD for GitHub Repositories

## Executive Summary

The best way to maintain a comprehensive CI/CD pipeline without exhausting GitHub Actions minutes is to use a **hybrid architecture**:

1. Keep the actual CI logic inside each repository as ordinary scripts, Make targets, or another repository-native command interface.
2. Continue using GitHub Actions as the trigger, status-check system, reporting interface, and merge gate.
3. Run private-repository jobs on your own **self-hosted runners** instead of GitHub-hosted runners.
4. Keep using standard GitHub-hosted runners for public repositories, where standard runner usage is generally free.
5. Generate structured test outputs and concise GitHub job summaries rather than relying only on raw console logs.

This approach preserves pull-request checks, logs, annotations, downloadable reports, and branch-protection integration while avoiding usage-based GitHub-hosted compute charges for private repositories.

---

## 1. Verify Which Repositories Are Actually Consuming Minutes

A public repository such as [`bendourthe/Nexus-Hub`](https://github.com/bendourthe/Nexus-Hub) should not normally consume the limited Actions minutes allocated to private repositories when it uses standard GitHub-hosted runners such as:

```yaml
runs-on: ubuntu-latest
```

```yaml
runs-on: windows-latest
```

```yaml
runs-on: macos-latest
```

GitHub's billing documentation states that:

- Standard GitHub-hosted runners are free for public repositories.
- Self-hosted runner execution does not consume GitHub-hosted runner minutes.
- Monthly minute allowances apply primarily to private repositories using GitHub-hosted runners.
- Larger GitHub-hosted runners may remain billable, including in situations where standard public-repository runners would be free.

Before restructuring all repositories, inspect the detailed Actions usage report in your GitHub billing settings. Group usage by:

- Repository
- Runner operating system
- Runner SKU
- Workflow
- Date or billing period

This should reveal which private repository or specialized runner type is actually exhausting the allowance.

Relevant GitHub documentation:

- [GitHub Actions billing concepts](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Viewing product and license usage](https://docs.github.com/en/billing/how-tos/products/view-productlicense-use)

---

## 2. What It Means to Put CI/CD "Directly in the Codebase"

The workflow files under `.github/workflows/` are already stored in the codebase, but they are mainly **orchestration definitions**. They tell GitHub:

- When a workflow should run
- Which operating system should execute it
- Which commands should be called
- What constitutes success or failure
- Which reports or artifacts should be published

They do not supply the computing resources themselves.

The commands still need to run somewhere:

- A GitHub-hosted virtual machine
- A self-hosted GitHub Actions runner
- A local development computer
- A Jenkins, Woodpecker, or GitLab CI server
- Another hosted CI service
- A fully self-hosted Git forge and CI platform

Moving YAML files into a different repository directory does not eliminate the need for compute. The more useful design goal is to make the CI pipeline **independent of the orchestration platform**.

---

## 3. Recommended Architecture

### 3.1 Create One Authoritative CI Entry Point per Repository

Instead of embedding hundreds of individual commands directly in GitHub Actions YAML, define a small number of stable repository-native entry points.

For example:

```bash
make ci-fast
make ci-full
make ci-report
```

A cross-platform Python interface may be even more portable:

```bash
python scripts/ci/run.py --profile fast
python scripts/ci/run.py --profile full
python scripts/ci/run.py --profile release
```

A practical profile structure could be:

| Command or Profile | Purpose |
|---|---|
| `ci-fast` | Formatting, linting, structural validation, and fast unit tests |
| `ci-full` | Full unit, integration, security, installer, and compatibility suite |
| `ci-platform` | Platform-specific validation for Linux, Windows, or macOS |
| `ci-report` | Aggregation of JUnit, coverage, static-analysis, and security outputs |
| `ci-release` | Packaging, installation smoke tests, provenance, and release verification |

This creates one source of truth:

- Developers run the same commands locally.
- Pre-commit or pre-push hooks call the fast profile.
- Pull-request workflows call the full profile.
- Release workflows call the release profile.
- A different CI service can use the same commands without reimplementing the pipeline.

`Nexus-Hub` already appears to have several useful foundations for this architecture, including a Makefile, pre-commit configuration, Python validators, and an extensive test suite. The main improvement would be to make the GitHub Actions YAML thinner and move the definitive test logic into repository-native scripts.

---

### 3.2 Use GitHub-Hosted Runners for Public Repositories

For public repositories such as `Nexus-Hub`, standard GitHub-hosted runners remain the simplest option.

Advantages include:

- No standard runner-minute charge for public repositories
- Maintained Linux, Windows, and macOS environments
- Native pull-request checks and annotations
- Integrated logs and summaries
- Downloadable artifacts
- Easy branch-protection integration
- Better isolation from potentially malicious public pull requests

A persistent personal self-hosted runner should generally not execute untrusted pull requests from public forks. Malicious workflow code could attempt to access the runner machine, credentials, network, or persistent storage.

GitHub security guidance:

- [Adding self-hosted runners](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners)

---

### 3.3 Use Self-Hosted GitHub Actions Runners for Private Repositories

For private repositories, self-hosted GitHub Actions runners are likely the best fit.

A GitHub workflow can remain mostly unchanged. Replace a GitHub-hosted runner label such as:

```yaml
runs-on: ubuntu-latest
```

with a self-hosted label:

```yaml
runs-on: [self-hosted, linux, x64, personal-ci]
```

For Windows-specific jobs:

```yaml
runs-on: [self-hosted, windows, x64, personal-ci]
```

GitHub still performs the orchestration:

- Detects pushes and pull requests
- Queues jobs
- Sends jobs to the appropriate runner
- Displays live logs
- Creates checks on pull requests
- Shows pass/fail status
- Publishes summaries and artifacts

The actual CPU, memory, storage, and operating-system time come from your own machine rather than a GitHub-hosted environment.

A modest dedicated Linux computer is usually sufficient for:

- Formatting and linting
- Python and Node.js tests
- Containerized integration tests
- Dependency audits
- Security scanning
- Packaging
- Documentation builds

A Windows runner is needed for faithful validation of:

- PowerShell 5.1 behavior
- Windows installers
- Registry-dependent behavior
- Windows-specific paths and permissions
- Native Windows tooling

Genuine macOS compatibility testing normally requires real macOS hardware or a hosted macOS environment.

#### Recommended Self-Hosted Runner Security Controls

A self-hosted runner should ideally be:

- Dedicated to CI rather than used as a daily personal workstation
- Registered only to the repositories that require it
- Operated under a restricted, non-administrator account
- Isolated from personal files and unrelated credentials
- Kept separate from company secrets and production access
- Cleaned, reset, or reimaged between jobs where practical
- Restricted from executing untrusted public-fork pull requests
- Configured with only the minimum required network access
- Monitored for failed jobs, disk growth, and stale processes

---

## 4. Improve the Event Model to Avoid Duplicate Testing

A common source of unnecessary CI usage is running the complete suite twice:

1. Once on the pull request
2. Again immediately after the pull request is merged

The better structure is:

### Pull Request: Complete Merge Gate

Run all checks required to establish that the change is safe to merge:

- Formatting and linting
- Structural and policy validation
- ShellCheck
- PowerShell parsing
- Complete unit tests
- Integration tests
- Linux installation and bootstrap tests
- Windows PowerShell 5.1 tests
- Windows installer tests
- macOS installation or bootstrap tests
- Security scans
- Dependency audits
- Supply-chain checks
- Packaging validation, where appropriate

Configure the important checks as required before merging.

### Push to `main` or `develop`: Post-Merge Work Only

After the merge, run only tasks that inherently depend on the final branch state:

- Deployment
- Release publishing
- Documentation publishing
- Final package generation
- Provenance generation
- A concise post-merge smoke test
- Environment-specific deployment verification

This avoids paying for or waiting on a second full validation pass that provides little additional assurance.

---

## 5. Ensure Platform-Specific Tests Run Before Merge

A pipeline can appear comprehensive while still allowing platform-specific failures to merge.

For example, a workflow may:

- Run Ubuntu tests on pull requests
- Run Windows and macOS only after a push to the shared branch

In that design, Windows and macOS failures are discovered only after the change has already been merged.

That is especially important when a repository has already encountered defects that appear under Windows PowerShell 5.1 but not under PowerShell 7 on Ubuntu. In that situation, Windows validation is a meaningful merge gate rather than optional compatibility testing.

When the requirement is that merged changes be fully tested, the supported operating-system matrix should run on the pull request before merge.

For a public repository, there is little billing incentive to postpone standard Windows or macOS jobs until after merge because standard GitHub-hosted execution is generally free.

---

## 6. Enforce the Result with Required Checks

A detailed report is useful, but the checks must also be authoritative.

GitHub status checks can provide:

- Pass/fail results
- Logs
- Error messages
- Source-code annotations
- Test results
- Links to artifacts
- Job summaries

When configured as required checks on a protected branch, GitHub prevents merging until those checks pass.

Relevant documentation:

- [About status checks](https://docs.github.com/en/pull-requests/reference/status-checks)
- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

### Public Repositories

Protected branches and rulesets are available for public repositories on GitHub Free.

### Private Repositories

Protected branches and rulesets for private repositories may require GitHub Pro, Team, or Enterprise, depending on the repository ownership and plan.

This creates two practical options:

#### Option A: GitHub Pro Plus Self-Hosted Runners

This provides:

- Fixed subscription cost
- No GitHub-hosted minute charges for self-hosted jobs
- Required status checks
- Protected branches
- Native GitHub merge enforcement

#### Option B: GitHub Free Plus Self-Hosted Runners

This provides:

- Free self-hosted execution
- Native GitHub checks and logs
- No GitHub-hosted minute charges

However, private-repository branch enforcement may be limited. You may need to voluntarily avoid merging failed changes or use a different repository-hosting platform with stronger free private-repository controls.

---

## 7. Strict Pull-Request Validation

GitHub pull-request workflows generally test a generated merge result rather than only the isolated feature-branch head. This helps determine whether the proposed change works when combined with the target branch.

For stronger assurance:

- Require the pull-request branch to be up to date before merging.
- Use required status checks.
- Prevent administrators from bypassing rules where appropriate.
- Avoid allowing stale successful checks to remain valid after the base branch changes.
- Require all supported-platform checks before merge.

Relevant documentation:

- [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)

---

## 8. Merge Queue Considerations

A merge queue provides stronger protection for repositories with many concurrent pull requests because it tests the actual merge group immediately before merging.

However, GitHub merge-queue availability depends on repository ownership and subscription level. A public repository owned directly by a personal account may not have the same eligibility as an organization-owned repository.

For a mostly solo-maintained repository, strict required checks and an up-to-date branch requirement are usually sufficient.

Relevant documentation:

- [Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)

---

## 9. Produce Clear, Structured CI Reports

Do not rely exclusively on thousands of lines of console output. The repository-native test harness should generate structured results.

A recommended layout is:

```text
reports/
├── summary.md
├── junit/
│   ├── unit.xml
│   ├── integration.xml
│   └── platform.xml
├── coverage/
│   ├── coverage.xml
│   └── html/
├── security/
│   ├── findings.sarif
│   └── dependency-audit.json
└── metadata/
    └── environment.json
```

### Recommended Outputs

#### 1. GitHub Job Summary

Create a concise Markdown summary containing:

- Overall status
- Number of passed tests
- Number of failed tests
- Number of skipped tests
- Coverage percentage
- Security findings
- Platform matrix results
- Links to detailed artifacts
- Environment and tool versions

#### 2. JUnit XML

Use JUnit XML for machine-readable test reporting and integration with test-report rendering tools.

#### 3. Coverage Reports

Generate both:

- XML or JSON for automation
- HTML for detailed inspection

#### 4. SARIF

Use SARIF for supported static-analysis and security findings so issues can appear as source-code annotations.

#### 5. Downloadable Artifacts

Upload detailed reports for later inspection, with a deliberately short retention period when long-term storage is unnecessary.

---

## 10. Example GitHub Actions Reporting Workflow

```yaml
- name: Run complete CI suite
  run: python scripts/ci/run.py --profile full --reports-dir reports

- name: Publish readable summary
  if: always()
  shell: bash
  run: cat reports/summary.md >> "$GITHUB_STEP_SUMMARY"

- name: Upload detailed reports
  if: always()
  uses: actions/upload-artifact@<pinned-commit-sha>
  with:
    name: ci-report-${{ runner.os }}
    path: reports/
    retention-days: 7
```

On Windows, the summary publishing step may use PowerShell:

```yaml
- name: Publish readable summary
  if: always()
  shell: pwsh
  run: Get-Content reports/summary.md | Out-File -FilePath $env:GITHUB_STEP_SUMMARY -Append
```

Relevant GitHub documentation:

- [Workflow commands and job summaries](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands)

---

## 11. Comparison of Available Approaches

| Approach | GitHub Minute Cost | Merge Integration | Maintenance Burden | Assessment |
|---|---:|---|---|---|
| Standard GitHub-hosted runners for public repositories | None for standard runners | Excellent | Very low | Best for public repositories such as `Nexus-Hub` |
| Self-hosted GitHub Actions for private repositories | No GitHub-hosted minute charge | Excellent, subject to branch-protection availability | Moderate | Best overall private-repository option |
| Local scripts and pre-push hooks only | None | Weak; hooks can be bypassed | Low | Useful supplement, not authoritative CI |
| Independent CI server using GitHub webhooks | No GitHub-hosted minute charge | Good after configuration | High | Useful when full infrastructure control is needed |
| Another hosted CI provider | Usually subject to another quota or billing model | Usually good | Low to moderate | Often moves rather than solves the quota problem |
| Fully self-hosted Git forge and CI | Your hardware and administration cost | Fully controllable | Highest | Appropriate only when reducing dependence on GitHub is a broader objective |

---

## 12. Why Local Hooks Alone Are Not Enough

Local pre-commit and pre-push hooks are valuable for fast feedback, but they should not replace authoritative CI.

They can be bypassed by:

- Running Git with hook-disabling flags
- Using a different workstation
- Misconfigured local dependencies
- A developer forgetting to install the hooks
- Differences between local and clean environments

Use local hooks for:

- Formatting
- Linting
- Fast unit tests
- Secret detection
- Basic structural checks

Use CI for:

- Clean-environment validation
- Full test suites
- Integration tests
- Platform matrices
- Security scans
- Packaging and installation tests
- Required merge checks

---

## 13. Independent Self-Hosted CI Platforms

A separate CI server can also solve the GitHub Actions minute problem.

Potential platforms include:

- Jenkins
- Woodpecker CI
- Drone CI
- GitLab Runner
- Buildkite agents
- TeamCity
- Gitea Actions
- Forgejo Actions

A typical design would be:

1. GitHub receives a push or pull request.
2. A webhook notifies the CI server.
3. The CI server clones the repository.
4. The server executes the repository-native CI entry point.
5. The server publishes a status back to the GitHub commit or pull request.
6. Detailed reports are hosted by the CI server or uploaded elsewhere.

This provides full control but adds maintenance requirements:

- Server patching
- Authentication
- HTTPS and certificates
- Backup and recovery
- Runner cleanup
- Plugin maintenance
- Status-report integration
- Secret management
- Log retention
- Availability monitoring

For a small number of personal repositories, self-hosted GitHub Actions runners are usually simpler than operating a completely independent CI control plane.

---

## 14. Suggested Repository Structure

A portable CI implementation could use the following structure:

```text
repository/
├── .github/
│   └── workflows/
│       ├── pull-request.yml
│       ├── post-merge.yml
│       └── release.yml
├── scripts/
│   └── ci/
│       ├── run.py
│       ├── profiles.py
│       ├── reporting.py
│       └── platforms/
│           ├── linux.py
│           ├── windows.py
│           └── macos.py
├── tests/
├── reports/
│   └── .gitkeep
├── Makefile
├── pyproject.toml
└── .pre-commit-config.yaml
```

The GitHub Actions workflow should orchestrate the pipeline rather than duplicate its implementation.

Example:

```yaml
name: Pull Request Validation

on:
  pull_request:
    branches:
      - main
      - develop

concurrency:
  group: pr-${{ github.event.pull_request.number }}-${{ github.workflow }}
  cancel-in-progress: true

jobs:
  linux:
    runs-on: [self-hosted, linux, x64, personal-ci]
    steps:
      - uses: actions/checkout@<pinned-commit-sha>
      - run: python scripts/ci/run.py --profile full --platform linux

  windows:
    runs-on: [self-hosted, windows, x64, personal-ci]
    steps:
      - uses: actions/checkout@<pinned-commit-sha>
      - shell: pwsh
        run: python scripts/ci/run.py --profile full --platform windows
```

For a public repository, the same workflow can use standard GitHub-hosted labels:

```yaml
runs-on: ubuntu-latest
```

and:

```yaml
runs-on: windows-latest
```

---

## 15. Additional Cost and Efficiency Controls

Even with self-hosted runners, the following improvements reduce wasted execution time and improve feedback speed.

### Path Filters

Avoid running expensive workflows when only unrelated files change.

Example:

```yaml
on:
  pull_request:
    paths-ignore:
      - "docs/**"
      - "**/*.md"
```

Use this carefully. Documentation changes may still require link checks, documentation builds, or example-code validation.

### Concurrency Cancellation

Cancel outdated workflow runs when a newer commit is pushed to the same pull request:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### Dependency Caching

Cache package-manager downloads and build outputs where safe.

Examples include:

- `pip`
- `uv`
- `npm`
- `pnpm`
- `Maven`
- `Gradle`
- compiler caches

Do not cache mutable or sensitive directories indiscriminately.

### Test Splitting

Run fast checks first so obvious failures stop the pipeline early.

A useful order is:

1. Structural validation
2. Formatting
3. Linting
4. Fast unit tests
5. Full unit tests
6. Integration tests
7. Packaging and installation
8. Security and supply-chain scans
9. Expensive platform-specific validation

### Conditional Platform Jobs

Run the full operating-system matrix when platform-sensitive files change, while preserving a scheduled full matrix to detect hidden cross-platform regressions.

This optimization should only be introduced when path ownership is well understood. Overly aggressive conditions can create untested gaps.

### Scheduled Full Validation

A nightly or weekly scheduled workflow can provide additional assurance for:

- Dependency changes
- External service changes
- Platform image changes
- Security database updates
- Long-running tests
- Full compatibility matrices

For private repositories, scheduled jobs can run on self-hosted hardware.

---

## 16. Security and Supply-Chain Recommendations

A comprehensive CI/CD pipeline should also protect the pipeline itself.

Recommended practices include:

- Pin third-party GitHub Actions to immutable commit SHAs.
- Review Dependabot or Renovate updates to action references.
- Use least-privilege `permissions:` declarations.
- Avoid exposing secrets to pull requests from forks.
- Separate build and deployment credentials.
- Prefer short-lived credentials where available.
- Protect deployment environments with approvals.
- Store generated reports without embedding credentials or tokens.
- Sanitize logs and command output.
- Avoid executing untrusted code on persistent privileged runners.
- Keep the runner operating system and tooling patched.
- Use disposable or ephemeral runners for higher-risk workloads where practical.

Example permissions restriction:

```yaml
permissions:
  contents: read
```

Add permissions only where required, such as:

```yaml
permissions:
  contents: read
  security-events: write
```

---

## 17. Concrete Recommendation for Your Repositories

### Public Repositories, Including `Nexus-Hub`

Recommended approach:

1. Keep standard GitHub-hosted Actions.
2. Confirm through the billing report that public standard-runner jobs are not consuming private Actions minutes.
3. Re-enable or consolidate the main CI workflow as appropriate.
4. Run the complete supported-platform matrix on pull requests.
5. Configure important checks as required before merge.
6. Avoid rerunning the complete suite after merge.
7. Keep only release, deployment, publishing, or concise smoke jobs on pushes to shared branches.
8. Continue using GitHub-native summaries, annotations, and artifacts.

### Private Repositories

Recommended approach:

1. Install a dedicated self-hosted Linux runner.
2. Add a self-hosted Windows runner when Windows-specific validation is required.
3. Use real Mac hardware or deliberately limited hosted macOS execution when genuine macOS testing is necessary.
4. Keep GitHub Actions as the orchestration and reporting layer.
5. Move the true pipeline logic into repository-native commands such as:
   - `ci-fast`
   - `ci-full`
   - `ci-platform`
   - `ci-report`
   - `ci-release`
6. Configure pull-request workflows as the complete merge gate.
7. Avoid duplicate full-suite execution after merge.
8. Use GitHub Pro only when private-repository protected branches and enforced required checks justify the fixed subscription cost.

---

## 18. Recommended Implementation Sequence

A practical migration sequence is:

### Phase 1: Audit

- Review GitHub Actions billing usage by repository and runner type.
- Identify private repositories consuming the allowance.
- Identify workflows that run both before and after merge.
- List all supported operating systems and test categories.
- Determine which checks are true merge requirements.

### Phase 2: Consolidate CI Logic

- Create one repository-native CI runner.
- Add fast, full, platform, report, and release profiles.
- Make local execution and GitHub execution use the same commands.
- Generate structured reports.

### Phase 3: Separate Workflow Responsibilities

- Pull request: complete validation
- Push to shared branch: deployment or concise smoke checks
- Release: packaging and publishing
- Schedule: extended or long-running validation

### Phase 4: Add Self-Hosted Runners

- Provision a dedicated Linux machine.
- Add a Windows runner where needed.
- Register runners only to appropriate private repositories.
- Apply least-privilege and isolation controls.
- Test labels and runner selection.

### Phase 5: Enforce Merge Quality

- Configure required checks.
- Require the branch to be current before merge.
- Prevent bypasses where the GitHub plan supports it.
- Confirm that failed platform checks block merging.

### Phase 6: Improve Reporting

- Add Markdown job summaries.
- Add JUnit XML.
- Add coverage reports.
- Add SARIF where supported.
- Upload detailed artifacts with short retention.

---

## Conclusion

The central distinction is:

> The CI/CD logic can and should live in the repository, but the computation must still run somewhere.

The most practical design is therefore:

- **Repository-native CI scripts** as the single source of truth
- **GitHub Actions** for triggers, pull-request integration, checks, and reporting
- **GitHub-hosted runners for public repositories**
- **Self-hosted runners for private repositories**
- **Complete pre-merge validation**
- **Minimal post-merge duplication**
- **Structured, downloadable reports**

This preserves a comprehensive CI/CD pipeline and clear reporting while avoiding the recurring cost of GitHub-hosted runner minutes for private repositories.
