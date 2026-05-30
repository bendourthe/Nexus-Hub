# Regression Root Cause Analyzer - Multi-Language Examples

This reference holds the JavaScript and Java implementations of the analyzers documented in `regression-root-cause-analyzer/SKILL.md`. The skill body keeps the Python implementations inline as the primary examples; the equivalents below are factored out here so the body stays within the size norm. Each example mirrors the Python version step-for-step, so read the corresponding step in the SKILL.md for the methodology and use the snippet here when your project is a JavaScript or Java codebase.

## Step 1: Timeline Reconstruction

### JavaScript: CI timeline reconstructor

```javascript
const { execSync } = require("child_process");

class TimelineReconstructor {
  constructor(repoPath) {
    this.repoPath = repoPath;
  }

  getCommitLog(since, until = "HEAD") {
    const output = execSync(
      `git log ${since}..${until} --format="%H|%aI|%s|%an" --no-merges`,
      { cwd: this.repoPath, encoding: "utf-8" }
    );

    return output.trim().split("\n").filter(Boolean).map(line => {
      const [hash, timestamp, subject, author] = line.split("|", 4);
      return { hash, timestamp, subject, author };
    });
  }

  findRegressionWindow(buildResults) {
    const sorted = [...buildResults].sort(
      (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
    );

    let lastPass = null;
    let firstFail = null;

    for (const result of sorted) {
      if (result.status === "pass") {
        lastPass = result;
        firstFail = null;
      } else if (result.status === "fail" && firstFail === null) {
        firstFail = result;
      }
    }

    return lastPass && firstFail ? { lastPass, firstFail } : null;
  }

  isFlakyFailure(buildResults, testName, threshold = 0.3) {
    const recent = [...buildResults]
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, 20);

    const failCount = recent.filter(
      b => b.failedTests.includes(testName)
    ).length;
    const total = recent.length;

    if (total === 0) return false;
    const failureRate = failCount / total;
    return failureRate > 0.1 && failureRate < threshold;
  }
}
```

### Java: CI timeline reconstructor

```java
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

public class TimelineReconstructor {
    public record BuildResult(String commitHash, Instant timestamp,
                               String status, List<String> failedTests) {}

    public record RegressionWindow(BuildResult lastPass, BuildResult firstFail) {}

    public static Optional<RegressionWindow> findRegressionWindow(
            List<BuildResult> buildResults) {
        List<BuildResult> sorted = buildResults.stream()
            .sorted(Comparator.comparing(BuildResult::timestamp))
            .toList();

        BuildResult lastPass = null;
        BuildResult firstFail = null;

        for (BuildResult result : sorted) {
            if ("pass".equals(result.status())) {
                lastPass = result;
                firstFail = null;
            } else if ("fail".equals(result.status()) && firstFail == null) {
                firstFail = result;
            }
        }

        if (lastPass != null && firstFail != null) {
            return Optional.of(new RegressionWindow(lastPass, firstFail));
        }
        return Optional.empty();
    }

    public static boolean isFlakyFailure(
            List<BuildResult> buildResults, String testName, double threshold) {
        List<BuildResult> recent = buildResults.stream()
            .sorted(Comparator.comparing(BuildResult::timestamp).reversed())
            .limit(20)
            .toList();

        long failCount = recent.stream()
            .filter(b -> b.failedTests().contains(testName))
            .count();
        int total = recent.size();
        if (total == 0) return false;

        double failureRate = (double) failCount / total;
        return failureRate > 0.1 && failureRate < threshold;
    }
}
```

## Step 3: Git Bisect Integration

### JavaScript: Git bisect automation

```javascript
const { execSync } = require("child_process");

class GitBisector {
  constructor(repoPath, testCommand) {
    this.repoPath = repoPath;
    this.testCommand = testCommand;
  }

  run(cmd) {
    try {
      return execSync(cmd, {
        cwd: this.repoPath,
        encoding: "utf-8",
        stdio: "pipe",
      });
    } catch (err) {
      return err.stdout || err.message;
    }
  }

  bisect(goodCommit, badCommit) {
    this.run(`git bisect start ${badCommit} ${goodCommit}`);
    const output = this.run(
      `git bisect run sh -c '${this.testCommand}'`
    );

    let firstBad = null;
    for (const line of output.split("\n")) {
      if (line.includes("is the first bad commit")) {
        firstBad = line.split(" ")[0];
        break;
      }
    }

    let commitInfo = {};
    if (firstBad) {
      const info = this.run(
        `git show --stat --format="%H%n%aI%n%an%n%s" ${firstBad}`
      );
      const parts = info.split("\n");
      commitInfo = {
        hash: parts[0],
        timestamp: parts[1],
        author: parts[2],
        subject: parts[3],
      };
    }

    this.run("git bisect reset");
    return { firstBadCommit: firstBad, commitInfo };
  }
}
```

## Step 5: Change Impact Analysis

### Java: Change impact analyzer

```java
import java.util.*;
import java.util.regex.*;
import java.io.*;

public class ChangeImpactAnalyzer {
    private final String repoPath;

    public ChangeImpactAnalyzer(String repoPath) {
        this.repoPath = repoPath;
    }

    public record ImpactReport(
        List<String> changedFiles,
        Map<String, List<String>> changedSymbols,
        Map<String, List<CallerInfo>> affectedCallers,
        String riskLevel
    ) {}

    public record CallerInfo(String file, int line, String context) {}

    public Map<String, List<String>> getChangedSymbols(String commitHash)
            throws IOException, InterruptedException {
        ProcessBuilder pb = new ProcessBuilder(
            "git", "diff", commitHash + "~1", commitHash, "-U0"
        );
        pb.directory(new File(repoPath));
        Process proc = pb.start();
        String output = new String(proc.getInputStream().readAllBytes());
        proc.waitFor();

        Map<String, List<String>> symbols = new LinkedHashMap<>();
        String currentFile = null;
        Pattern filePattern = Pattern.compile("^\\+\\+\\+ b/(.+)$", Pattern.MULTILINE);
        Pattern hunkPattern = Pattern.compile("^@@ .+ @@ (.+)$", Pattern.MULTILINE);

        for (String line : output.split("\\n")) {
            Matcher fileMatcher = filePattern.matcher(line);
            if (fileMatcher.matches()) {
                currentFile = fileMatcher.group(1);
                symbols.putIfAbsent(currentFile, new ArrayList<>());
                continue;
            }
            Matcher hunkMatcher = hunkPattern.matcher(line);
            if (hunkMatcher.matches() && currentFile != null) {
                symbols.get(currentFile).add(hunkMatcher.group(1).trim());
            }
        }
        return symbols;
    }

    public ImpactReport assessBlastRadius(String commitHash)
            throws IOException, InterruptedException {
        Map<String, List<String>> changedSymbols = getChangedSymbols(commitHash);
        Map<String, List<CallerInfo>> affectedCallers = new LinkedHashMap<>();

        int totalCallers = 0;
        Pattern namePattern = Pattern.compile(
            "(?:def|function|void|public|private|protected)\\s+(\\w+)"
        );

        for (var entry : changedSymbols.entrySet()) {
            for (String symbol : entry.getValue()) {
                Matcher m = namePattern.matcher(symbol);
                if (m.find()) {
                    String name = m.group(1);
                    // Use git grep to find callers
                    ProcessBuilder pb = new ProcessBuilder(
                        "git", "grep", "-n", name
                    );
                    pb.directory(new File(repoPath));
                    Process proc = pb.start();
                    String grepOutput = new String(
                        proc.getInputStream().readAllBytes()
                    );
                    proc.waitFor();

                    List<CallerInfo> callers = new ArrayList<>();
                    for (String line : grepOutput.split("\\n")) {
                        String[] parts = line.split(":", 3);
                        if (parts.length == 3) {
                            callers.add(new CallerInfo(
                                parts[0],
                                Integer.parseInt(parts[1]),
                                parts[2].trim()
                            ));
                        }
                    }
                    if (!callers.isEmpty()) {
                        affectedCallers.put(name, callers);
                        totalCallers += callers.size();
                    }
                }
            }
        }

        String riskLevel = totalCallers > 20 ? "critical"
            : totalCallers > 10 ? "high"
            : totalCallers > 5 ? "medium" : "low";

        return new ImpactReport(
            new ArrayList<>(changedSymbols.keySet()),
            changedSymbols, affectedCallers, riskLevel
        );
    }
}
```
