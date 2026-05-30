---
name: regression-root-cause-analyzer
description: Identify root causes of regressions using diff analysis, git bisect, test failure correlation, and change impact analysis. Use when a previously passing test fails, CI/CD pipelines break after a deployment, or recent changes introduce unexpected behavior.
summary_l0: "Identify regression root causes with diff analysis, bisect, and change impact tracing"
overview_l1: "This skill systematically identifies the root cause of regressions by combining diff analysis, git bisect integration, test failure correlation, change impact analysis, and timeline reconstruction. Use it when determining which commit or merge introduced a regression, analyzing CI/CD pipeline failures after a deployment, correlating multiple test failures to a single root cause change, performing change impact analysis to understand blast radius, reconstructing the timeline of events leading to a regression, distinguishing genuine regressions from flaky tests, or investigating performance regressions. Key capabilities include automated bisect-driven commit isolation, diff-to-failure correlation, blast radius mapping, timeline reconstruction, flaky test discrimination, and performance regression profiling. The expected output is a root cause report identifying the specific commit, the change that caused it, the mechanism of the regression, and recommended remediation. Trigger phrases: find the regression, what broke the build, which commit caused, regression analysis, CI pipeline broke, test started failing, root cause of regression, bisect the failure, what change caused this."
---

# Regression Root Cause Analyzer

Systematically identify the root cause of regressions in CI/CD environments by combining diff analysis, git bisect integration, test failure correlation, change impact analysis, and timeline reconstruction. This skill bridges the gap between "something broke" and "this specific change caused it because of this specific reason".

## Iron Law: No Fixes Without Root Cause Investigation First

Do not write, propose, or apply a fix until you have identified the specific change and the specific mechanism that produced the regression. A fix applied before the root cause is known is a guess, and a guess that happens to make the symptom disappear is worse than no fix: it hides the real defect, leaves the blast radius unaddressed, and ships a second bug as often as it removes the first.

The gate is binary. Before any fix:

1. **Name the regression precisely.** What behavior changed, from what to what, observed how (the failing test, the error, the metric).
2. **Locate the introducing change.** Identify the commit (via the timeline + bisect steps below) and the specific lines within it.
3. **Explain the mechanism.** State *why* that change causes *this* symptom. "Commit abc123 broke it" is a location, not a root cause; "abc123 changed the default timeout from 30s to 3s, so the slow integration path now exceeds it" is a root cause.
4. **Only then** design the fix, and verify it against the exact reproduction.

If you cannot complete steps 1-3, you are not ready to fix. Keep investigating. A symptom that disappears for a reason you cannot articulate has not been fixed; it has been disturbed.

### After 3 Failed Fixes, Question the Architecture, Not the Bug

When three or more fix attempts have failed to resolve the regression, stop fixing. The repeated failure is itself evidence: it tells you the mental model of where the bug lives is wrong. Continuing to patch the suspected location wastes effort on a hypothesis the evidence has already rejected.

Failure-pattern signals that you are fixing the wrong thing:

- Each fix moves the symptom rather than removing it (the same failure reappears one layer over, or a different test starts failing).
- The fix "should work" by your reasoning but the test still fails, repeatedly.
- You are adding special-cases or guards rather than changing the logic that produces the value.

When you hit this signal, escalate the question from "what line is wrong?" to "is the boundary / contract / data flow itself wrong?" Re-examine the assumptions: which component is *assumed* to own this state, whether the interface contract actually holds, whether the regression is in the component you keep editing or in one upstream of it. The 3-failure threshold is a circuit breaker that forces this re-framing before sunk cost drives a fourth, fifth, and sixth doomed patch.

### Multi-Component Boundary Evidence Gathering

When a regression spans several components and you do not yet know *which* component breaks, do not guess and start editing. Instrument first, then locate, then investigate the one that breaks.

1. **Instrument each component boundary.** Add a cheap, temporary observation (a log line, an assertion, a recorded value) at every boundary the data crosses on the failing path: input to component A, A's output / B's input, B's output, and so on.
2. **Run once to find WHERE it breaks.** A single run now tells you the first boundary at which the value is wrong. The break is between the last boundary where the value was correct and the first where it was wrong - that narrows a multi-component mystery to one component in one run.
3. **Investigate only that component.** Now apply the Iron Law within the isolated component: name the regression at that boundary, locate the introducing change, explain the mechanism.

This converts "something in this pipeline is wrong" into "component B corrupts the value between its input and output" without editing any production logic on a hunch. Remove the instrumentation once the root cause is confirmed.

## When to Use This Skill

Use this skill when you need to:

- Determine which commit or merge introduced a regression
- Analyze CI/CD pipeline failures that started after a recent deployment or merge
- Correlate multiple test failures to a single root cause change
- Perform change impact analysis to understand the blast radius of a code modification
- Reconstruct the timeline of events that led to a regression
- Distinguish between a genuine regression and a flaky test or environment issue
- Investigate performance regressions that appeared after recent changes

**Trigger phrases**: "find the regression", "what broke the build", "which commit caused", "regression analysis", "CI pipeline broke", "test started failing", "root cause of regression", "bisect the failure", "what change caused this"

## What This Skill Does

### Methodology Overview

Regression root cause analysis follows a structured investigation pipeline:

1. **Timeline Reconstruction** -- Establish when the regression first appeared by examining CI/CD history, test results over time, and deployment logs.
2. **Diff Analysis** -- Examine all code changes between the last known good state and the first known bad state to identify candidate causes.
3. **Git Bisect Integration** -- Use binary search across commits to pinpoint the exact commit that introduced the regression.
4. **Test Failure Correlation** -- Analyze which tests fail together and map them to common code paths or shared dependencies to identify the root cause.
5. **Change Impact Analysis** -- Evaluate the blast radius of the identified change to understand all areas potentially affected beyond the reported failure.

### Regression Categories

| Category | Characteristics | Investigation Approach |
|----------|----------------|----------------------|
| Functional Regression | Previously correct output is now wrong | Diff analysis + bisect |
| Performance Regression | Response time or throughput degraded | Timeline reconstruction + profiling |
| Compatibility Regression | Works in one environment, fails in another | Environment diff + dependency analysis |
| Flaky Test (not a regression) | Intermittent failure unrelated to changes | Failure frequency analysis |
| Transitive Regression | Caused by a dependency update, not direct code change | Dependency diff analysis |

## Instructions

### Step 1: Reconstruct the Timeline

Before analyzing code, establish the exact window during which the regression was introduced.

**Python: CI timeline reconstructor**

```python
from dataclasses import dataclass
from datetime import datetime
import subprocess
import json

@dataclass
class BuildResult:
    commit_hash: str
    timestamp: datetime
    status: str  # "pass" or "fail"
    branch: str
    failed_tests: list[str]

class TimelineReconstructor:
    """Reconstruct when a regression first appeared."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def get_commit_log(self, since: str, until: str = "HEAD") -> list[dict]:
        """Get structured commit log between two points."""
        result = subprocess.run(
            [
                "git", "log", f"{since}..{until}",
                "--format=%H|%aI|%s|%an",
                "--no-merges",
            ],
            cwd=self.repo_path,
            capture_output=True, text=True,
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            commits.append({
                "hash": parts[0],
                "timestamp": parts[1],
                "subject": parts[2],
                "author": parts[3],
            })
        return commits

    def find_regression_window(
        self, build_results: list[BuildResult]
    ) -> tuple[BuildResult, BuildResult] | None:
        """Find the last passing build and first failing build."""
        sorted_results = sorted(build_results, key=lambda b: b.timestamp)

        last_pass = None
        first_fail = None

        for result in sorted_results:
            if result.status == "pass":
                last_pass = result
                first_fail = None  # Reset: a pass after a fail means flakiness
            elif result.status == "fail" and first_fail is None:
                first_fail = result

        if last_pass and first_fail:
            return (last_pass, first_fail)
        return None

    def get_commits_in_window(
        self, good: BuildResult, bad: BuildResult
    ) -> list[dict]:
        """Get all commits between the last good and first bad builds."""
        return self.get_commit_log(good.commit_hash, bad.commit_hash)

    def is_flaky_failure(
        self, build_results: list[BuildResult], test_name: str,
        threshold: float = 0.3,
    ) -> bool:
        """Determine if a test failure is likely flaky rather than a regression."""
        recent = sorted(build_results, key=lambda b: b.timestamp)[-20:]
        fail_count = sum(
            1 for b in recent if test_name in b.failed_tests
        )
        pass_count = sum(
            1 for b in recent
            if b.status == "pass" or test_name not in b.failed_tests
        )
        total = fail_count + pass_count
        if total == 0:
            return False
        failure_rate = fail_count / total
        # A flaky test fails intermittently; a regression fails consistently
        return 0.1 < failure_rate < threshold
```

The JavaScript and Java equivalents of this timeline reconstructor are in [references/multi-language-examples.md](references/multi-language-examples.md#step-1-timeline-reconstruction).

### Step 2: Analyze Diffs Between Good and Bad States

Examine the code changes within the regression window to identify candidate causes.

**Python: Diff analyzer**

```python
import subprocess
import re
from dataclasses import dataclass

@dataclass
class DiffHunk:
    file_path: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    added_lines: list[str]
    removed_lines: list[str]
    context: str

class DiffAnalyzer:
    """Analyze diffs between good and bad commits."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def get_diff(self, good_commit: str, bad_commit: str) -> str:
        """Get the unified diff between two commits."""
        result = subprocess.run(
            ["git", "diff", good_commit, bad_commit],
            cwd=self.repo_path,
            capture_output=True, text=True,
        )
        return result.stdout

    def parse_diff(self, diff_text: str) -> list[DiffHunk]:
        """Parse a unified diff into structured hunks."""
        hunks = []
        current_file = None
        hunk_header_re = re.compile(
            r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)"
        )
        file_header_re = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)

        for file_match in file_header_re.finditer(diff_text):
            current_file = file_match.group(1)

        lines = diff_text.split("\n")
        i = 0
        while i < len(lines):
            file_match = re.match(r"^\+\+\+ b/(.+)$", lines[i])
            if file_match:
                current_file = file_match.group(1)
                i += 1
                continue

            hunk_match = hunk_header_re.match(lines[i])
            if hunk_match and current_file:
                old_start = int(hunk_match.group(1))
                old_count = int(hunk_match.group(2) or "1")
                new_start = int(hunk_match.group(3))
                new_count = int(hunk_match.group(4) or "1")
                context = hunk_match.group(5).strip()

                added = []
                removed = []
                i += 1
                while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("diff "):
                    if lines[i].startswith("+"):
                        added.append(lines[i][1:])
                    elif lines[i].startswith("-"):
                        removed.append(lines[i][1:])
                    i += 1

                hunks.append(DiffHunk(
                    file_path=current_file,
                    old_start=old_start, old_count=old_count,
                    new_start=new_start, new_count=new_count,
                    added_lines=added, removed_lines=removed,
                    context=context,
                ))
                continue
            i += 1

        return hunks

    def rank_hunks_by_risk(self, hunks: list[DiffHunk]) -> list[tuple[DiffHunk, float]]:
        """Rank diff hunks by their likelihood of causing a regression."""
        scored = []
        for hunk in hunks:
            score = 0.0
            # Larger changes are riskier
            change_size = len(hunk.added_lines) + len(hunk.removed_lines)
            score += min(change_size / 50.0, 1.0) * 0.3

            # Changes to conditionals are risky
            conditional_keywords = ["if", "else", "elif", "switch", "case", "?"]
            for line in hunk.added_lines + hunk.removed_lines:
                if any(kw in line for kw in conditional_keywords):
                    score += 0.2
                    break

            # Changes to error handling are risky
            error_keywords = ["catch", "except", "throw", "raise", "finally"]
            for line in hunk.added_lines + hunk.removed_lines:
                if any(kw in line for kw in error_keywords):
                    score += 0.15
                    break

            # Deletions are riskier than additions
            if len(hunk.removed_lines) > len(hunk.added_lines):
                score += 0.15

            # Changes to test files are lower risk for production regressions
            if "test" in hunk.file_path.lower():
                score *= 0.5

            scored.append((hunk, min(score, 1.0)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def get_changed_files(self, good_commit: str, bad_commit: str) -> list[str]:
        """Get the list of files changed between two commits."""
        result = subprocess.run(
            ["git", "diff", "--name-only", good_commit, bad_commit],
            cwd=self.repo_path,
            capture_output=True, text=True,
        )
        return [f for f in result.stdout.strip().split("\n") if f]
```

### Step 3: Integrate Git Bisect

Automate git bisect to find the exact commit that introduced the regression.

**Python: Git bisect automation**

```python
import subprocess
import json
from datetime import datetime

class GitBisector:
    """Automated git bisect for regression identification."""

    def __init__(self, repo_path: str, test_command: str):
        self.repo_path = repo_path
        self.test_command = test_command
        self.bisect_log = []

    def run_cmd(self, cmd: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd, cwd=self.repo_path,
            capture_output=True, text=True,
        )

    def bisect(self, good_commit: str, bad_commit: str) -> dict:
        """Run automated bisect and return the first bad commit."""
        self.run_cmd(["git", "bisect", "start", bad_commit, good_commit])

        result = self.run_cmd([
            "git", "bisect", "run", "sh", "-c", self.test_command,
        ])

        # Parse the output to find the first bad commit
        first_bad = None
        for line in result.stdout.splitlines():
            if "is the first bad commit" in line:
                first_bad = line.split()[0]
                break

        # Get detailed info about the bad commit
        commit_info = {}
        if first_bad:
            info_result = self.run_cmd([
                "git", "show", "--stat", "--format=%H%n%aI%n%an%n%s%n%b",
                first_bad,
            ])
            parts = info_result.stdout.split("\n", 4)
            commit_info = {
                "hash": parts[0] if len(parts) > 0 else "",
                "timestamp": parts[1] if len(parts) > 1 else "",
                "author": parts[2] if len(parts) > 2 else "",
                "subject": parts[3] if len(parts) > 3 else "",
                "body": parts[4] if len(parts) > 4 else "",
            }

        self.run_cmd(["git", "bisect", "reset"])
        return {
            "first_bad_commit": first_bad,
            "commit_info": commit_info,
            "bisect_output": result.stdout,
        }

    def bisect_with_skip(
        self, good_commit: str, bad_commit: str,
        skip_patterns: list[str] = None,
    ) -> dict:
        """Run bisect, skipping commits that match certain patterns."""
        self.run_cmd(["git", "bisect", "start", bad_commit, good_commit])

        while True:
            current = self.run_cmd(["git", "rev-parse", "HEAD"])
            current_hash = current.stdout.strip()

            # Check if this commit should be skipped
            if skip_patterns:
                msg = self.run_cmd(
                    ["git", "log", "-1", "--format=%s", current_hash]
                )
                subject = msg.stdout.strip()
                if any(p in subject for p in skip_patterns):
                    self.run_cmd(["git", "bisect", "skip"])
                    continue

            # Run the test
            test_result = subprocess.run(
                self.test_command, shell=True,
                cwd=self.repo_path, capture_output=True,
            )

            if test_result.returncode == 0:
                mark = self.run_cmd(["git", "bisect", "good"])
            else:
                mark = self.run_cmd(["git", "bisect", "bad"])

            self.bisect_log.append({
                "commit": current_hash,
                "result": "good" if test_result.returncode == 0 else "bad",
            })

            if "is the first bad commit" in mark.stdout:
                first_bad = mark.stdout.split()[0]
                self.run_cmd(["git", "bisect", "reset"])
                return {"first_bad_commit": first_bad, "log": self.bisect_log}

            if "bisect run" in mark.stdout.lower() and "done" in mark.stdout.lower():
                self.run_cmd(["git", "bisect", "reset"])
                return {"first_bad_commit": None, "log": self.bisect_log}
```

The JavaScript equivalent of this bisect automation is in [references/multi-language-examples.md](references/multi-language-examples.md#step-3-git-bisect-integration).

### Step 4: Correlate Test Failures

When multiple tests fail, correlating them can reveal the single root cause.

**Python: Test failure correlator**

```python
from collections import defaultdict
from dataclasses import dataclass

@dataclass
class TestFailure:
    test_name: str
    error_type: str
    error_message: str
    file_path: str
    stack_trace: str

class TestFailureCorrelator:
    """Correlate multiple test failures to find common root causes."""

    def __init__(self):
        self.failures = []

    def add_failure(self, failure: TestFailure):
        self.failures.append(failure)

    def group_by_error_type(self) -> dict[str, list[TestFailure]]:
        """Group failures by error type."""
        groups = defaultdict(list)
        for f in self.failures:
            groups[f.error_type].append(f)
        return dict(groups)

    def group_by_common_stack_frame(self) -> dict[str, list[TestFailure]]:
        """Group failures that share a common stack frame."""
        frame_to_tests = defaultdict(list)
        for f in self.failures:
            frames = set()
            for line in f.stack_trace.split("\n"):
                if "File" in line or "at " in line:
                    frames.add(line.strip())
            for frame in frames:
                frame_to_tests[frame].append(f)

        # Return only frames shared by multiple failures
        return {
            frame: tests
            for frame, tests in frame_to_tests.items()
            if len(tests) > 1
        }

    def find_common_dependency(
        self, test_to_imports: dict[str, set[str]]
    ) -> list[tuple[str, int]]:
        """Find modules imported by all failing tests but few passing tests."""
        failing_names = {f.test_name for f in self.failures}
        failing_imports = defaultdict(int)
        passing_imports = defaultdict(int)

        for test_name, imports in test_to_imports.items():
            for imp in imports:
                if test_name in failing_names:
                    failing_imports[imp] += 1
                else:
                    passing_imports[imp] += 1

        # Score each module: high failing count + low passing count = suspicious
        scored = []
        for module, fail_count in failing_imports.items():
            pass_count = passing_imports.get(module, 0)
            if fail_count > 1:
                score = fail_count - (pass_count * 0.5)
                scored.append((module, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def generate_correlation_report(self) -> str:
        """Generate a human-readable correlation report."""
        lines = ["# Test Failure Correlation Report", ""]

        error_groups = self.group_by_error_type()
        lines.append(f"## Failures by Error Type ({len(self.failures)} total)")
        lines.append("")
        for error_type, failures in error_groups.items():
            lines.append(f"### {error_type} ({len(failures)} failures)")
            for f in failures:
                lines.append(f"- {f.test_name}: {f.error_message[:100]}")
            lines.append("")

        stack_groups = self.group_by_common_stack_frame()
        if stack_groups:
            lines.append("## Common Stack Frames")
            lines.append("")
            for frame, failures in sorted(
                stack_groups.items(), key=lambda x: len(x[1]), reverse=True
            )[:10]:
                lines.append(f"### Shared by {len(failures)} failures")
                lines.append(f"Frame: `{frame}`")
                for f in failures:
                    lines.append(f"- {f.test_name}")
                lines.append("")

        return "\n".join(lines)
```

### Step 5: Perform Change Impact Analysis

After identifying the root cause commit, analyze its full blast radius.

**Python: Change impact analyzer**

```python
import subprocess
import re
from collections import defaultdict

class ChangeImpactAnalyzer:
    """Analyze the impact of a change across the codebase."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def get_changed_symbols(self, commit_hash: str) -> dict[str, list[str]]:
        """Extract the functions/classes changed in a commit."""
        diff = subprocess.run(
            ["git", "diff", f"{commit_hash}~1", commit_hash, "-U0"],
            cwd=self.repo_path,
            capture_output=True, text=True,
        ).stdout

        symbols = defaultdict(list)
        current_file = None

        for line in diff.split("\n"):
            file_match = re.match(r"^\+\+\+ b/(.+)$", line)
            if file_match:
                current_file = file_match.group(1)
                continue

            hunk_match = re.match(r"@@ .+ @@ (.+)", line)
            if hunk_match and current_file:
                context = hunk_match.group(1).strip()
                symbols[current_file].append(context)

        return dict(symbols)

    def find_callers(self, symbol_name: str, file_type: str = "*.py") -> list[dict]:
        """Find all callers of a changed symbol."""
        result = subprocess.run(
            ["git", "grep", "-n", symbol_name, "--", file_type],
            cwd=self.repo_path,
            capture_output=True, text=True,
        )

        callers = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            match = re.match(r"(.+?):(\d+):(.+)", line)
            if match:
                callers.append({
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "context": match.group(3).strip(),
                })
        return callers

    def assess_blast_radius(self, commit_hash: str) -> dict:
        """Assess the full impact of a commit's changes."""
        changed_symbols = self.get_changed_symbols(commit_hash)

        impact = {
            "directly_changed_files": list(changed_symbols.keys()),
            "changed_symbols": changed_symbols,
            "affected_callers": {},
            "risk_level": "low",
        }

        total_callers = 0
        for file_path, symbols in changed_symbols.items():
            for symbol in symbols:
                # Extract function/method name from context
                name_match = re.search(r"(?:def|function|void|public)\s+(\w+)", symbol)
                if name_match:
                    name = name_match.group(1)
                    callers = self.find_callers(name)
                    if callers:
                        impact["affected_callers"][name] = callers
                        total_callers += len(callers)

        # Assess risk level
        if total_callers > 20:
            impact["risk_level"] = "critical"
        elif total_callers > 10:
            impact["risk_level"] = "high"
        elif total_callers > 5:
            impact["risk_level"] = "medium"

        return impact
```

The Java equivalent of this change impact analyzer is in [references/multi-language-examples.md](references/multi-language-examples.md#step-5-change-impact-analysis).

### Step 6: Generate the Root Cause Report

Combine all findings into a structured report that links the regression to its exact cause.

**Python: Report generator**

```python
def generate_root_cause_report(
    regression_window: tuple,
    bisect_result: dict,
    diff_analysis: list,
    failure_correlation: str,
    impact_assessment: dict,
) -> str:
    """Generate a comprehensive regression root cause report."""
    report_lines = [
        "# Regression Root Cause Report",
        "",
        "## Timeline",
        f"- Last passing build: {regression_window[0].commit_hash} "
        f"({regression_window[0].timestamp})",
        f"- First failing build: {regression_window[1].commit_hash} "
        f"({regression_window[1].timestamp})",
        "",
        "## Root Cause Commit",
        f"- Commit: {bisect_result.get('first_bad_commit', 'unknown')}",
    ]

    commit_info = bisect_result.get("commit_info", {})
    if commit_info:
        report_lines.extend([
            f"- Author: {commit_info.get('author', 'unknown')}",
            f"- Date: {commit_info.get('timestamp', 'unknown')}",
            f"- Subject: {commit_info.get('subject', 'unknown')}",
        ])

    report_lines.extend([
        "",
        "## Impact Assessment",
        f"- Risk level: {impact_assessment.get('risk_level', 'unknown')}",
        f"- Directly changed files: {len(impact_assessment.get('directly_changed_files', []))}",
        f"- Affected callers: {sum(len(v) for v in impact_assessment.get('affected_callers', {}).values())}",
        "",
        "## Test Failure Correlation",
        failure_correlation,
        "",
        "## Recommended Actions",
        "1. Review the root cause commit for the specific logical error",
        "2. Generate a targeted patch using the bug-to-patch-generator skill",
        "3. Validate the fix against all affected callers",
        "4. Add regression tests covering the exact failure scenario",
    ])

    return "\n".join(report_lines)
```

## Common Rationalizations

Each row is an excuse that precedes skipping the root-cause investigation, with the concrete failure mode it causes.

| Rationalization | Reality |
|---|---|
| "I can see the fix, no need to bisect." | The fix you can "see" addresses the symptom you can see. Without the introducing change and its mechanism, you do not know whether your fix removes the cause or just masks one of its effects. Locate the change first; the fix is often different from your first guess. |
| "It's obviously the most recent commit." | Recency is salience, not evidence. Regressions frequently lurk in an earlier commit and surface later when test coverage, ordering, or data changes. Bisect against a reliable reproduction instead of trusting the last thing that landed. |
| "The test is probably just flaky." | "Probably flaky" is a hypothesis, not a finding. Run the failure-frequency check: a test that fails consistently on the bad commit and passes consistently on the good one is a regression, not flakiness. Dismissing a real regression as flaky ships the bug. |
| "Three fixes didn't work, let me try a fourth." | Three failed fixes are evidence your model of where the bug lives is wrong. A fourth patch in the same place repeats the mistake. Stop and question the architecture / boundary, per the Iron Law section. |
| "It's a one-line change, the cause is self-evident." | One-line changes are exactly where an inverted condition or a changed default hides. Self-evidence suppresses the mechanism question. State why the line causes this symptom before fixing it. |
| "The fix made the symptom go away, so I'm done." | A disappeared symptom with no articulated mechanism is a disturbed bug, not a fixed one. Confirm the fix against a reproduction that fails without it and passes with it, and check the blast radius for the same cause elsewhere. |
| "It only happens in CI, so it's an environment issue." | Maybe - but "environment" is a category, not a root cause. A dependency bump, runner update, or ordering change IS a regression with a locatable introducing change. Investigate the environment changelog the same way you investigate the code changelog. |

## Best Practices

- Always verify that the failing test reliably fails on the bad commit and reliably passes on the good commit before starting bisect. A flaky test will produce incorrect results.
- Examine the full "Caused by" chain in Java stack traces and the complete traceback in Python. The root cause is often several layers deep in the exception chain.
- When multiple tests fail simultaneously, correlate them before investigating individually. A single root cause often explains many failures, and investigating them separately wastes time.
- Use change impact analysis proactively when merging large pull requests. Understanding the blast radius before merging prevents regressions from reaching production.
- Keep CI build history for at least 30 days with full test output. Timeline reconstruction depends on historical data.
- Automate the bisect process with a reliable test script. Manual bisect is error-prone and slow for large commit ranges.
- Document each regression root cause in a post-mortem or decision log so that the team can learn from patterns and prevent similar regressions.
- When the regression window contains merge commits, use `git bisect --first-parent` to bisect along the main branch first, then investigate the specific merge if needed.

## Common Pitfalls

- **Confusing correlation with causation in test failures.** Two tests failing at the same time does not mean they share a root cause. They may have been affected by different changes that happened to land together.
- **Trusting git bisect results when the test is flaky.** If the test intermittently passes on the bad commit, bisect will point to the wrong commit. Always verify test reliability first.
- **Ignoring environment changes as a regression cause.** A regression may be caused by a CI runner update, a dependency version change, or an infrastructure modification rather than a code change. Check the environment changelog alongside the code changelog.
- **Stopping at the commit level without identifying the specific line.** Knowing that commit abc123 introduced the regression is helpful, but the investigation is not complete until you identify the specific logical error and why it causes the failure.
- **Assuming the most recent commit is the cause.** Recent commits are more visible, but the regression may have been introduced earlier and only surfaced now due to a change in test coverage or execution order.
- **Neglecting transitive regressions.** A dependency update (in package.json, requirements.txt, pom.xml) can introduce regressions without any direct code change in your repository. Always check dependency diffs.
- **Not accounting for merge order.** In repositories with frequent merges, the order in which commits are integrated matters. A change that works in isolation may fail when combined with another change that was merged around the same time.
- **Failing to distinguish between test regression and production regression.** A test may start failing due to a change in test infrastructure or test data, not because of a production code bug. Verify that the regression also manifests in the production code path.
