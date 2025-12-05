---
template_id: csharp_maintenance_cicd
template_name: Maintenance & CI/CD - C#
version: 1.0.0
last_updated: 2025-12-03
language: C#
category: test_development
phase: maintenance_cicd
phase_number: 7
difficulty: intermediate
estimated_time_hours: 3-5
prerequisites:

  - test_development/code_coverage/csharp_code_coverage.md
related_templates:

  - test_development/reward_hacking/csharp_reward_hacking.md
tools:

  - NUnit (4.2.2)

  - xUnit

  - MSTest
tags:

  - test-development

  - c#
---
# C# Test Maintenance & CI/CD Integration

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                ► │ [COMPLETE]
│ Phase 4: Mocks & Fixtures                      ► │ [COMPLETE]
│ Phase 5: Performance Testing                   ► │ [COMPLETE]
│ Phase 6: Code Coverage                         ► │ [COMPLETE]
│ Phase 7: Maintenance & CI/CD                    ► │ ● CURRENT
│ Phase 8: Reward Hacking Validation                 ► │ [NEXT]
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 6 (Code Coverage) should be completed first
**Next Step:** Phase 8 (Reward Hacking Validation)

---


## Objective
Establish comprehensive test automation infrastructure, integrate tests into CI/CD pipelines, implement quality gates, manage test maintenance, handle flaky tests, optimize test execution, and ensure sustainable testing practices for C#/.NET projects.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/maintenance_cicd/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/maintenance_cicd/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### CI/CD Configuration

- [ ] GitHub Actions/GitLab CI pipeline configured

- [ ] Test stages defined (unit, integration, e2e)

- [ ] Parallel execution enabled

- [ ] Test result reporting set up

- [ ] Artifact storage configured

### Quality Gates

- [ ] Code coverage threshold enforced (80%+)

- [ ] Test pass rate requirement set (100%)

- [ ] Performance regression checks enabled

- [ ] Security scanning integrated

- [ ] Deployment gates configured

### Test Maintenance

- [ ] Flaky test detection implemented

- [ ] Test execution time monitoring enabled

- [ ] Obsolete test cleanup process established

- [ ] Test documentation maintained

- [ ] Test data management automated

### Pre-commit Hooks

- [ ] Code formatting checks (dotnet format)

- [ ] Linting (StyleCop, Roslynator)

- [ ] Static analysis (SonarAnalyzer)

- [ ] Fast test subset execution

- [ ] Commit hooks configured

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Test Maintenance & CI/CD Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/maintenance_cicd"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**

- All generated files should be saved with the `${OUTPUT_DIR}/` prefix

- Examples:

  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`

  - Template files → `${OUTPUT_DIR}/templates/template.yaml`

  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

Please implement comprehensive test automation and maintenance infrastructure for this C#/.NET project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: CI/CD Pipeline Configuration

### GitHub Actions Setup

**Create `.github/workflows/tests.yml`**:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  DOTNET_VERSION: '8.0.x'

jobs:
  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v3

      - name: Setup .NET
        uses: actions/setup-dotnet@v3
        with:
          dotnet-version: ${{ env.DOTNET_VERSION }}

      - name: Restore dependencies
        run: dotnet restore

      - name: Check formatting
        run: dotnet format --verify-no-changes --verbosity diagnostic

      - name: Run StyleCop analyzers
        run: dotnet build /p:TreatWarningsAsErrors=true

      - name: Run Security Analysis
        run: dotnet build /p:RunAnalyzersDuringBuild=true /p:EnableNETAnalyzers=true

  unit-tests:
    name: Unit Tests
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        dotnet-version: ['6.0.x', '7.0.x', '8.0.x']

    steps:

      - uses: actions/checkout@v3

      - name: Setup .NET ${{ matrix.dotnet-version }}
        uses: actions/setup-dotnet@v3
        with:
          dotnet-version: ${{ matrix.dotnet-version }}

      - name: Restore dependencies
        run: dotnet restore

      - name: Build
        run: dotnet build --no-restore --configuration Release

      - name: Run unit tests
        run: |
          dotnet test \
            --no-build \
            --configuration Release \
            --filter "FullyQualifiedName~UnitTests" \
            --collect:"XPlat Code Coverage" \
            --results-directory ./coverage \
            --logger "trx;LogFileName=test-results.trx"

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/**/coverage.cobertura.xml
          flags: unit-tests
          name: codecov-${{ matrix.os }}-${{ matrix.dotnet-version }}

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.os }}-${{ matrix.dotnet-version }}
          path: |
            **/test-results.trx
            coverage/

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:

          - 5432:5432

      sqlserver:
        image: mcr.microsoft.com/mssql/server:2022-latest
        env:
          ACCEPT_EULA: Y
          SA_PASSWORD: TestP@ssw0rd
        ports:

          - 1433:1433

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:

          - 6379:6379

    steps:

      - uses: actions/checkout@v3

      - name: Setup .NET
        uses: actions/setup-dotnet@v3
        with:
          dotnet-version: ${{ env.DOTNET_VERSION }}

      - name: Restore dependencies
        run: dotnet restore

      - name: Build
        run: dotnet build --no-restore --configuration Release

      - name: Run integration tests
        env:
          ConnectionStrings__Postgres: "Host=localhost;Database=testdb;Username=postgres;Password=testpass"
          ConnectionStrings__SqlServer: "Server=localhost;Database=testdb;User Id=sa;Password=TestP@ssw0rd;TrustServerCertificate=True"
          ConnectionStrings__Redis: "localhost:6379"
        run: |
          dotnet test \
            --no-build \
            --configuration Release \
            --filter "FullyQualifiedName~IntegrationTests" \
            --collect:"XPlat Code Coverage" \
            --results-directory ./coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/**/coverage.cobertura.xml
          flags: integration-tests

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v3

      - name: Setup .NET
        uses: actions/setup-dotnet@v3
        with:
          dotnet-version: ${{ env.DOTNET_VERSION }}

      - name: Install Security Scan Tools
        run: dotnet tool install --global security-scan

      - name: Restore dependencies
        run: dotnet restore

      - name: Run Security Analysis
        run: dotnet build /p:RunAnalyzersDuringBuild=true

      - name: Dependency vulnerability check
        run: dotnet list package --vulnerable --include-transitive || true

      - name: Run Snyk security scan
        uses: snyk/actions/dotnet@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

  quality-gate:
    name: Quality Gate
    runs-on: ubuntu-latest
    needs: [lint, unit-tests, integration-tests, security]
    steps:

      - name: Quality gate passed
        run: echo "All quality checks passed!"
```

### GitLab CI Configuration

**Create `.gitlab-ci.yml`**:

```yaml
stages:

  - lint

  - test

  - quality

  - deploy

variables:
  DOTNET_VERSION: "8.0"
  NUGET_PACKAGES_DIRECTORY: '.nuget'

cache:
  paths:

    - .nuget/

before_script:

  - dotnet restore

lint:
  stage: lint
  image: mcr.microsoft.com/dotnet/sdk:${DOTNET_VERSION}
  script:

    - dotnet format --verify-no-changes

    - dotnet build /p:TreatWarningsAsErrors=true

unit-tests:
  stage: test
  image: mcr.microsoft.com/dotnet/sdk:${DOTNET_VERSION}
  script:

    - dotnet test
        --filter "FullyQualifiedName~UnitTests"
        --collect:"XPlat Code Coverage"
        --results-directory ./coverage
        --logger "trx;LogFileName=test-results.trx"
  coverage: '/Total\s+\|\s+(\d+(?:\.\d+)?)/'
  artifacts:
    reports:
      junit: '**/test-results.trx'
      coverage_report:
        coverage_format: cobertura
        path: coverage/**/coverage.cobertura.xml
    paths:

      - coverage/

integration-tests:
  stage: test
  image: mcr.microsoft.com/dotnet/sdk:${DOTNET_VERSION}
  services:

    - postgres:14

    - redis:7
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: testpass
  script:

    - dotnet test
        --filter "FullyQualifiedName~IntegrationTests"
        --collect:"XPlat Code Coverage"
  artifacts:
    paths:

      - coverage/

quality-gate:
  stage: quality
  image: mcr.microsoft.com/dotnet/sdk:${DOTNET_VERSION}
  script:

    - dotnet tool install -g dotnet-reportgenerator-globaltool

    - reportgenerator
        -reports:coverage/**/coverage.cobertura.xml
        -targetdir:coverage/report
        -reporttypes:TextSummary

    - cat coverage/report/Summary.txt
  needs:

    - unit-tests

    - integration-tests
```

## Phase 2: Quality Gates Configuration

### Project Configuration

**Configure in `Directory.Build.props`**:

```xml
<Project>
  <PropertyGroup>
    <!-- Code Analysis -->
    <EnableNETAnalyzers>true</EnableNETAnalyzers>
    <AnalysisLevel>latest</AnalysisLevel>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>

    <!-- Code Coverage -->
    <CollectCoverage>true</CollectCoverage>
    <CoverletOutputFormat>cobertura,opencover</CoverletOutputFormat>
    <CoverletOutput>./coverage/</CoverletOutput>
    <Threshold>80</Threshold>
    <ThresholdType>line,branch</ThresholdType>

    <!-- Testing -->
    <IsTestProject Condition="$(MSBuildProjectName.Contains('Tests'))">true</IsTestProject>
  </PropertyGroup>

  <!-- Analyzer Packages -->
  <ItemGroup>
    <PackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers" Version="8.0.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
    </PackageReference>
    <PackageReference Include="StyleCop.Analyzers" Version="1.2.0-beta.556">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
    </PackageReference>
    <PackageReference Include="Roslynator.Analyzers" Version="4.7.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
    </PackageReference>
    <PackageReference Include="SonarAnalyzer.CSharp" Version="9.16.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
    </PackageReference>
  </ItemGroup>

  <!-- Test Project References -->
  <ItemGroup Condition="'$(IsTestProject)' == 'true'">
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
    <PackageReference Include="xunit" Version="2.6.4" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.6">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
    </PackageReference>
    <PackageReference Include="coverlet.collector" Version="6.0.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
    </PackageReference>
    <PackageReference Include="FluentAssertions" Version="6.12.0" />
    <PackageReference Include="Moq" Version="4.20.70" />
  </ItemGroup>
</Project>
```

**Configure in `.editorconfig`**:

```ini
root = true

[*]
charset = utf-8
indent_style = space
indent_size = 4
insert_final_newline = true
trim_trailing_whitespace = true

[*.{cs,csx,vb,vbx}]
# Code Quality Rules
dotnet_diagnostic.CA1000.severity = warning
dotnet_diagnostic.CA1001.severity = error
dotnet_diagnostic.CA1031.severity = warning

# Style Rules
dotnet_sort_system_directives_first = true
dotnet_separate_import_directive_groups = false

# Code Coverage minimum thresholds
# Enforced by Coverlet
```

### Test Pass Rate Gate

```csharp
// tests/Common/QualityGateListener.cs
using Xunit.Abstractions;
using Xunit.Sdk;

namespace Tests.Common
{
    /// <summary>
    /// Quality gate enforcement for test suite.
    /// </summary>
    public class QualityGateListener : ITestListener
    {
        private int _totalTests = 0;
        private int _passedTests = 0;
        private int _failedTests = 0;

        public void TestFinished(ITestResultMessage testResult)
        {
            _totalTests++;

            switch (testResult)
            {
                case ITestPassed:
                    _passedTests++;
                    break;
                case ITestFailed:
                    _failedTests++;
                    break;
            }
        }

        public void TestRunComplete()
        {
            var passRate = _totalTests > 0
                ? (double)_passedTests / _totalTests * 100
                : 0;

            Console.WriteLine(new string('=', 60));
            Console.WriteLine($"Test Pass Rate: {passRate:F1}% ({_passedTests}/{_totalTests})");
            Console.WriteLine(new string('=', 60));

            if (passRate < 100)
            {
                Console.WriteLine("⚠️  WARNING: Not all tests passed");
                Console.WriteLine($"Failed tests: {_failedTests}");
            }
            else
            {
                Console.WriteLine("✅ Quality Gate Passed: All tests passed");
            }

            if (_failedTests > 0)
            {
                Console.WriteLine("\n❌ Quality Gate Failed: Some tests did not pass");
                Console.WriteLine("All tests must pass before merge.");
                Environment.Exit(1);
            }
        }
    }
}
```

### Performance Regression Gate

```csharp
// tests/Benchmarks/PerformanceGate.cs
using System.Text.Json;
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Running;

namespace Tests.Benchmarks
{
    /// <summary>
    /// Performance regression detection.
    /// </summary>
    public class PerformanceGate
    {
        private const string BaselineFile = "tests/Benchmarks/baseline.json";
        private const double RegressionThreshold = 0.10; // 10%

        private Dictionary<string, long> _benchmarks = new();
        private Dictionary<string, long> _baseline = new();

        public PerformanceGate()
        {
            LoadBaseline();
        }

        private void LoadBaseline()
        {
            if (File.Exists(BaselineFile))
            {
                var json = File.ReadAllText(BaselineFile);
                _baseline = JsonSerializer.Deserialize<Dictionary<string, long>>(json)
                    ?? new Dictionary<string, long>();
            }
        }

        public void RecordBenchmark(string name, long durationMs)
        {
            _benchmarks[name] = durationMs;
        }

        public void CheckRegressions()
        {
            if (!_baseline.Any())
            {
                SaveBaseline();
                Console.WriteLine("📊 Baseline performance metrics saved");
                return;
            }

            var regressions = new List<(string Name, long Baseline, long Current, double Regression)>();

            foreach (var (name, current) in _benchmarks)
            {
                if (_baseline.TryGetValue(name, out var baseline))
                {
                    var regression = (double)(current - baseline) / baseline;

                    if (regression > RegressionThreshold)
                    {
                        regressions.Add((name, baseline, current, regression));
                    }
                }
            }

            if (regressions.Any())
            {
                Console.WriteLine("\n❌ Performance Regression Detected:");
                foreach (var (name, baseline, current, regression) in regressions)
                {
                    Console.WriteLine($"  {name}: {regression * 100:F1}% slower");
                    Console.WriteLine($"    Baseline: {baseline}ms, Current: {current}ms");
                }
                throw new Exception("Performance regression gate failed");
            }

            Console.WriteLine("✅ Performance Gate Passed: No regressions detected");
        }

        private void SaveBaseline()
        {
            var json = JsonSerializer.Serialize(_benchmarks, new JsonSerializerOptions
            {
                WriteIndented = true
            });
            File.WriteAllText(BaselineFile, json);
        }
    }
}
```

## Phase 3: Pre-commit Hooks

### Install Husky.NET

```bash
dotnet tool install --global Husky
dotnet husky install
```

**Configure in `.husky/pre-commit`**:

```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Format check
dotnet format --verify-no-changes || {
    echo "Code formatting issues detected. Run 'dotnet format' to fix."
    exit 1
}

# Build with warnings as errors
dotnet build /p:TreatWarningsAsErrors=true || {
    echo "Build failed with warnings/errors."
    exit 1
}

# Run fast tests
dotnet test --filter "Category=Fast" --no-build || {
    echo "Fast tests failed."
    exit 1
}
```

### Configure .editorconfig

**Create `.editorconfig`**:

```ini
root = true

[*.cs]
# Organize usings
dotnet_sort_system_directives_first = true
dotnet_separate_import_directive_groups = false

# this. preferences
dotnet_style_qualification_for_field = false:warning
dotnet_style_qualification_for_property = false:warning
dotnet_style_qualification_for_method = false:warning
dotnet_style_qualification_for_event = false:warning

# Language keywords vs BCL types preferences
dotnet_style_predefined_type_for_locals_parameters_members = true:warning
dotnet_style_predefined_type_for_member_access = true:warning

# Parentheses preferences
dotnet_style_parentheses_in_arithmetic_binary_operators = always_for_clarity:suggestion
dotnet_style_parentheses_in_relational_binary_operators = always_for_clarity:suggestion

# Code style rules
csharp_prefer_braces = true:warning
csharp_prefer_simple_using_statement = true:suggestion

# Naming conventions
dotnet_naming_rule.interface_should_be_begins_with_i.severity = warning
dotnet_naming_rule.interface_should_be_begins_with_i.symbols = interface
dotnet_naming_rule.interface_should_be_begins_with_i.style = begins_with_i

# Symbol specifications
dotnet_naming_symbols.interface.applicable_kinds = interface
dotnet_naming_symbols.interface.applicable_accessibilities = public, internal, private, protected

# Naming styles
dotnet_naming_style.begins_with_i.required_prefix = I
dotnet_naming_style.begins_with_i.capitalization = pascal_case
```

### StyleCop Configuration

**Create `stylecop.json`**:

```json
{
  "$schema": "https://raw.githubusercontent.com/DotNetAnalyzers/StyleCopAnalyzers/master/StyleCop.Analyzers/StyleCop.Analyzers/Settings/stylecop.schema.json",
  "settings": {
    "documentationRules": {
      "companyName": "YourCompany",
      "copyrightText": "Copyright (c) {companyName}. All rights reserved.",
      "xmlHeader": false,
      "fileNamingConvention": "stylecop"
    },
    "orderingRules": {
      "usingDirectivesPlacement": "outsideNamespace",
      "systemUsingDirectivesFirst": true
    }
  }
}
```

## Phase 4: Test Parallelization

### xUnit Parallel Configuration

**Configure in `xunit.runner.json`**:

```json
{
  "$schema": "https://xunit.net/schema/current/xunit.runner.schema.json",
  "parallelizeAssembly": true,
  "parallelizeTestCollections": true,
  "maxParallelThreads": 0,
  "methodDisplay": "method",
  "methodDisplayOptions": "all"
}
```

### Handle Non-Thread-Safe Tests

```csharp
using Xunit;

namespace Tests.Integration
{
    /// <summary>
    /// Tests that must run serially.
    /// </summary>
    [Collection("Database Collection")]
    public class DatabaseMigrationTests
    {
        [Fact]
        public void TestMigration001()
        {
            // Test implementation
        }

        [Fact]
        public void TestMigration002()
        {
            // Test implementation
        }
    }

    // Define collection for serial execution
    [CollectionDefinition("Database Collection", DisableParallelization = true)]
    public class DatabaseCollection
    {
    }
}
```

### MSTest Parallel Configuration

```csharp
[assembly: Parallelize(Workers = 0, Scope = ExecutionScope.MethodLevel)]
```

## Phase 5: Flaky Test Management

### Retry Attribute

```csharp
// tests/Common/RetryFactAttribute.cs
using System;
using System.ComponentModel;
using Xunit;
using Xunit.Sdk;

namespace Tests.Common
{
    /// <summary>
    /// Retry attribute for flaky tests.
    /// </summary>
    [XunitTestCaseDiscoverer("Tests.Common.RetryFactDiscoverer", "Tests")]
    public class RetryFactAttribute : FactAttribute
    {
        public int MaxRetries { get; set; } = 3;
        public int DelayMs { get; set; } = 1000;
    }

    public class RetryFactDiscoverer : IXunitTestCaseDiscoverer
    {
        readonly IMessageSink diagnosticMessageSink;

        public RetryFactDiscoverer(IMessageSink diagnosticMessageSink)
        {
            this.diagnosticMessageSink = diagnosticMessageSink;
        }

        public IEnumerable<IXunitTestCase> Discover(
            ITestFrameworkDiscoveryOptions discoveryOptions,
            ITestMethod testMethod,
            IAttributeInfo factAttribute)
        {
            var maxRetries = factAttribute.GetNamedArgument<int>(nameof(RetryFactAttribute.MaxRetries));
            var delayMs = factAttribute.GetNamedArgument<int>(nameof(RetryFactAttribute.DelayMs));

            yield return new RetryTestCase(
                diagnosticMessageSink,
                discoveryOptions.MethodDisplayOrDefault(),
                discoveryOptions.MethodDisplayOptionsOrDefault(),
                testMethod,
                maxRetries,
                delayMs);
        }
    }

    // Usage
    public class FlakyTests
    {
        [RetryFact(MaxRetries = 3, DelayMs = 2000)]
        public void FlakyExternalApiCall()
        {
            // Test implementation
        }
    }
}
```

### Track Flaky Tests

```csharp
// tests/Common/FlakyTestTracker.cs
using System.Text.Json;

namespace Tests.Common
{
    /// <summary>
    /// Track flaky test occurrences.
    /// </summary>
    public class FlakyTestTracker
    {
        private const string FlakyLog = "tests/flaky-tests.json";
        private Dictionary<string, FlakyTestInfo> _flakyTests = new();

        public FlakyTestTracker()
        {
            LoadLog();
        }

        private void LoadLog()
        {
            if (File.Exists(FlakyLog))
            {
                var json = File.ReadAllText(FlakyLog);
                _flakyTests = JsonSerializer.Deserialize<Dictionary<string, FlakyTestInfo>>(json)
                    ?? new Dictionary<string, FlakyTestInfo>();
            }
        }

        public void RecordFlaky(string testName)
        {
            if (!_flakyTests.ContainsKey(testName))
            {
                _flakyTests[testName] = new FlakyTestInfo();
            }

            _flakyTests[testName].Count++;
            _flakyTests[testName].LastSeen = DateTime.UtcNow;
        }

        public void SaveLog()
        {
            var json = JsonSerializer.Serialize(_flakyTests, new JsonSerializerOptions
            {
                WriteIndented = true
            });
            File.WriteAllText(FlakyLog, json);
        }

        public void Report()
        {
            var sorted = _flakyTests
                .OrderByDescending(x => x.Value.Count)
                .Take(10);

            if (sorted.Any())
            {
                Console.WriteLine("\n⚠️  Top Flaky Tests:");
                foreach (var (test, data) in sorted)
                {
                    Console.WriteLine($"  {test}: {data.Count} failures");
                }
            }
        }

        public class FlakyTestInfo
        {
            public int Count { get; set; }
            public DateTime LastSeen { get; set; }
        }
    }
}
```

## Phase 6: Test Maintenance Practices

### Monitor Test Execution Time

```csharp
// tests/Common/SlowTestDetector.cs
using Xunit.Abstractions;
using Xunit.Sdk;

namespace Tests.Common
{
    /// <summary>
    /// Monitor slow tests.
    /// </summary>
    public class SlowTestDetector : ITestListener
    {
        private const long SlowTestThresholdMs = 1000;
        private readonly List<SlowTest> _slowTests = new();
        private DateTime _startTime;

        public void TestStarting(ITestStarting testStarting)
        {
            _startTime = DateTime.UtcNow;
        }

        public void TestFinished(ITestResultMessage testResult)
        {
            var duration = (long)(DateTime.UtcNow - _startTime).TotalMilliseconds;

            if (duration > SlowTestThresholdMs)
            {
                _slowTests.Add(new SlowTest(
                    testResult.Test.DisplayName,
                    duration
                ));

                Console.WriteLine($"\n⚠️  Slow test: {testResult.Test.DisplayName} ({duration / 1000.0:F2}s)");
            }
        }

        public void PrintReport()
        {
            if (_slowTests.Any())
            {
                Console.WriteLine("\n" + new string('=', 60));
                Console.WriteLine("Slow Tests Detected:");

                foreach (var test in _slowTests.OrderByDescending(t => t.Duration).Take(10))
                {
                    Console.WriteLine($"  {test.Duration / 1000.0:F2}s: {test.Name}");
                }

                Console.WriteLine(new string('=', 60));
            }
        }

        private record SlowTest(string Name, long Duration);
    }
}
```

### Document Test Purpose

```csharp
namespace Tests.Auth
{
    /// <summary>
    /// User Authentication Test Suite
    ///
    /// <para>Purpose:</para>
    /// <para>Validate user login, logout, and session management functionality.</para>
    ///
    /// <para>Coverage:</para>
    /// <list type="bullet">
    ///   <item>Valid credential login</item>
    ///   <item>Invalid credential handling</item>
    ///   <item>Session token generation and validation</item>
    ///   <item>Multi-factor authentication flow</item>
    ///   <item>Password reset process</item>
    /// </list>
    ///
    /// <para>Maintenance Notes:</para>
    /// <list type="bullet">
    ///   <item>Update TestValidLogin() if authentication logic changes</item>
    ///   <item>MockEmailService fixture required for password reset tests</item>
    ///   <item>Tests use in-memory database for speed</item>
    ///   <item>External API calls are mocked</item>
    /// </list>
    ///
    /// <para>Dependencies:</para>
    /// <list type="bullet">
    ///   <item>AuthService</item>
    ///   <item>UserRepository</item>
    ///   <item>JwtTokenProvider</item>
    /// </list>
    ///
    /// <para>Last Review: 2024-01-15</para>
    /// <para>Reviewed By: alice@example.com</para>
    /// </summary>
    public class AuthenticationTests
    {
        // Test implementation
    }
}
```

## Phase 7: Test Result Reporting

### ReportGenerator Configuration

```bash
# Install ReportGenerator
dotnet tool install -g dotnet-reportgenerator-globaltool

# Generate HTML report
reportgenerator \
    -reports:"coverage/**/coverage.cobertura.xml" \
    -targetdir:"coverage/report" \
    -reporttypes:Html
```

### Custom Test Reporter

```csharp
// tests/Common/CustomTestReporter.cs
using System.Text.Json;

namespace Tests.Common
{
    /// <summary>
    /// Generate custom JSON test report.
    /// </summary>
    public class CustomTestReporter
    {
        private readonly List<TestResult> _results = new();
        private DateTime _startTime;
        private int _totalTests = 0;
        private int _passedTests = 0;
        private int _failedTests = 0;

        public void Start()
        {
            _startTime = DateTime.UtcNow;
        }

        public void RecordResult(string name, string status, long duration, string? failureMessage = null)
        {
            _totalTests++;
            if (status == "Passed") _passedTests++;
            else _failedTests++;

            _results.Add(new TestResult
            {
                Name = name,
                Status = status,
                Duration = duration,
                FailureMessage = failureMessage
            });
        }

        public void GenerateReport(string outputPath = "test-report.json")
        {
            var duration = (long)(DateTime.UtcNow - _startTime).TotalMilliseconds;

            var report = new
            {
                Timestamp = DateTime.UtcNow,
                Summary = new
                {
                    Total = _totalTests,
                    Passed = _passedTests,
                    Failed = _failedTests,
                    Duration = duration
                },
                Results = _results
            };

            var json = JsonSerializer.Serialize(report, new JsonSerializerOptions
            {
                WriteIndented = true
            });

            File.WriteAllText(outputPath, json);
            Console.WriteLine($"\n📊 Custom test report saved to: {outputPath}");
        }

        private class TestResult
        {
            public string Name { get; set; } = string.Empty;
            public string Status { get; set; } = string.Empty;
            public long Duration { get; set; }
            public string? FailureMessage { get; set; }
        }
    }
}
```

## Output Format

Please provide a comprehensive CI/CD and maintenance implementation with the following structure:

### CI/CD Configuration Summary

- **Platform**: [GitHub Actions/GitLab CI/Azure DevOps]

- **Pipeline Stages**: [list stages]

- **Parallel Execution**: [enabled/disabled, worker count]

- **Test Types Automated**: [unit, integration, e2e]

- **Quality Gates**: [list gates]

### Quality Gate Configuration
| Gate | Threshold | Current | Status |
|------|-----------|---------|--------|
| Code Coverage | 80% | [value] | ✅/❌ |
| Test Pass Rate | 100% | [value] | ✅/❌ |
| Performance | <10% regression | [value] | ✅/❌ |

### Pre-commit Hooks Configured

- [ ] Code formatting (dotnet format)

- [ ] Linting (StyleCop, Roslynator)

- [ ] Static analysis (SonarAnalyzer)

- [ ] Fast test execution

- [ ] Coverage check

### Test Maintenance Status
**Slow Tests Identified**:
| Test | Duration | Recommendation |
|------|----------|----------------|
| [test_name] | [time] | [optimization] |

**Flaky Tests**:
| Test | Failure Rate | Action |
|------|--------------|--------|
| [test_name] | [rate] | [fix planned] |

### Test Execution Metrics

- **Total Tests**: [count]

- **Average Execution Time**: [duration]

- **Parallel Workers**: [count]

- **Tests per Second**: [rate]

- **Coverage**: [percentage]

### CI/CD Pipeline Visualization
```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌────────┐
│  Lint   │────▶│   Unit   │────▶│Integration │────▶│ Deploy │
└─────────┘     │  Tests   │     │   Tests    │     └────────┘
                └──────────┘     └────────────┘
                     │                 │
                     ▼                 ▼
                ┌─────────┐       ┌─────────┐
                │Coverage │       │Security │
                │  Gate   │       │  Scan   │
                └─────────┘       └─────────┘
```

### Best Practices Implemented

- [ ] All tests automated in CI/CD

- [ ] Quality gates prevent regressions

- [ ] Pre-commit hooks catch issues early

- [ ] Parallel execution for speed

- [ ] Flaky tests tracked and fixed

- [ ] Test maintenance schedule established

### Next Steps

- [ ] Monitor and optimize slow tests

- [ ] Fix identified flaky tests

- [ ] Review and update obsolete tests

- [ ] Enhance test documentation

- [ ] Set up test result dashboard

- [ ] Schedule regular test maintenance reviews

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p tests/{phase_name}/test_files
mkdir -p tests/{phase_name}/test_data
mkdir -p tests/{phase_name}/test_reports
mkdir -p tests/{phase_name}/test_configs
```

**Save files as follows**:

- Test files → `tests/{phase_name}/test_files/`

- Test data → `tests/{phase_name}/test_data/`

- Test reports → `tests/{phase_name}/test_reports/`

- Test configs → `tests/{phase_name}/test_configs/`

Replace `{phase_name}` with the specific phase (test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).

~~~

## Output Format

The AI assistant should deliver:

1. **Complete CI/CD pipeline configuration** (GitHub Actions or GitLab CI)

2. **Quality gate implementation** with thresholds (.NET tooling)

3. **Pre-commit hook configuration** with all checks

4. **Test parallelization setup** for faster execution

5. **Flaky test detection and tracking** system

6. **Test maintenance procedures** and documentation

7. **Test reporting infrastructure** with dashboards

8. **Execution metrics and monitoring** setup
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**

- [ ] All directories created successfully

- [ ] All files saved in correct subdirectories

- [ ] No files created in repository root

- [ ] Directory structure matches expected layout
