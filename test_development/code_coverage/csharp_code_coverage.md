# C# Code Coverage Analysis

## Objective
Implement comprehensive code coverage measurement using Coverlet and dotCover, analyze coverage gaps, establish coverage goals (80%+ target), create systematic improvement strategies, integrate coverage into CI/CD, and maintain high-quality test coverage for .NET projects.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/code_coverage/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/code_coverage/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Coverage Setup

- [ ] Coverlet or dotCover installed and configured

- [ ] Test framework integration enabled

- [ ] Coverage configuration file created

- [ ] HTML/XML report generation configured

- [ ] CI/CD coverage reporting set up

### Coverage Analysis

- [ ] Current coverage baseline measured

- [ ] Coverage gaps identified and prioritized

- [ ] Critical paths coverage verified

- [ ] Edge cases coverage assessed

- [ ] Untested code documented

### Coverage Goals

- [ ] Target coverage defined (80%+ recommended)

- [ ] Coverage thresholds set by module

- [ ] Critical path coverage requirements established

- [ ] Coverage improvement plan created

- [ ] Timeline for improvements defined

### Coverage Integration

- [ ] Coverage gates in CI/CD configured

- [ ] Coverage reports automated

- [ ] Coverage trends tracked

- [ ] Coverage regression prevention enabled

- [ ] Team coverage standards documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Code Coverage Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/code_coverage"
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

Please implement comprehensive code coverage measurement and improvement for this .NET/C# project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Coverage Setup and Configuration

### Install Coverage Tools

**Option 1: Using Coverlet (Cross-platform, open-source)**:

```bash
# Install Coverlet as global tool
dotnet tool install --global coverlet.console

# Or add to test project
dotnet add package coverlet.collector
dotnet add package coverlet.msbuild
```

**Option 2: Using Visual Studio Code Coverage** (Windows only):

- Built into Visual Studio Enterprise

- Run from Test Explorer or command line

**Option 3: Using dotCover CLI** (JetBrains):
```bash
# Install dotCover CLI
dotnet tool install --global JetBrains.dotCover.GlobalTool
```

### Configure Coverage with Coverlet

**Add to test project (.csproj)**:
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <IsPackable>false</IsPackable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
    <PackageReference Include="xunit" Version="2.6.2" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.4" />
    <PackageReference Include="coverlet.collector" Version="6.0.0" />
    <PackageReference Include="coverlet.msbuild" Version="6.0.0" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\MyApp\MyApp.csproj" />
  </ItemGroup>
</Project>
```

**Create coverlet.runsettings**:
```xml
<?xml version="1.0" encoding="utf-8" ?>
<RunSettings>
  <DataCollectionRunSettings>
    <DataCollectors>
      <DataCollector friendlyName="XPlat Code Coverage">
        <Configuration>
          <Format>json,cobertura,lcov,opencover</Format>
          <Exclude>[*.Tests]*,[*.TestHelpers]*</Exclude>
          <ExcludeByAttribute>Obsolete,GeneratedCodeAttribute,CompilerGeneratedAttribute</ExcludeByAttribute>
          <ExcludeByFile>**/Migrations/**/*.cs</ExcludeByFile>
          <IncludeDirectory>../MyApp/bin/Debug/</IncludeDirectory>
          <SingleHit>false</SingleHit>
          <UseSourceLink>true</UseSourceLink>
          <IncludeTestAssembly>false</IncludeTestAssembly>
          <SkipAutoProps>true</SkipAutoProps>
          <DeterministicReport>true</DeterministicReport>
          <Threshold>80</Threshold>
          <ThresholdType>line,branch</ThresholdType>
          <ThresholdStat>total</ThresholdStat>
        </Configuration>
      </DataCollector>
    </DataCollectors>
  </DataCollectionRunSettings>
</RunSettings>
```

**Alternative: Using Directory.Build.props** (Solution-wide):
```xml
<Project>
  <PropertyGroup>
    <CollectCoverage>true</CollectCoverage>
    <CoverletOutputFormat>cobertura,json,lcov,opencover</CoverletOutputFormat>
    <CoverletOutput>./coverage/</CoverletOutput>
    <Exclude>[*.Tests]*,[*.TestHelpers]*</Exclude>
    <ExcludeByAttribute>Obsolete,GeneratedCode,CompilerGenerated</ExcludeByAttribute>
    <ExcludeByFile>**/Migrations/*.cs,**/Program.cs</ExcludeByFile>
    <Threshold>80</Threshold>
    <ThresholdType>line,branch</ThresholdType>
    <ThresholdStat>total</ThresholdStat>
  </PropertyGroup>
</Project>
```

### Configure ReportGenerator for HTML Reports

```bash
# Install ReportGenerator
dotnet tool install --global dotnet-reportgenerator-globaltool

# Or add to project
dotnet add package ReportGenerator
```

**Create reportgenerator.runsettings**:
```xml
<Configuration>
  <Reports>
    <Report>coverage/coverage.cobertura.xml</Report>
  </Reports>
  <TargetDirectory>coverage/report</TargetDirectory>
  <ReportTypes>
    Html;Badges;Cobertura;TextSummary;JsonSummary
  </ReportTypes>
  <SourceDirectories>
    <SourceDirectory>../src</SourceDirectory>
  </SourceDirectories>
  <HistoryDirectory>coverage/history</HistoryDirectory>
  <Verbosity>Info</Verbosity>
</Configuration>
```

### Configure Visual Studio Code Coverage

**Create .runsettings**:
```xml
<?xml version="1.0" encoding="utf-8"?>
<RunSettings>
  <DataCollectionRunSettings>
    <DataCollectors>
      <DataCollector friendlyName="Code Coverage"
                     uri="datacollector://Microsoft/CodeCoverage/2.0"
                     assemblyQualifiedName="Microsoft.VisualStudio.Coverage.DynamicCoverageDataCollector, Microsoft.VisualStudio.TraceCollector, Version=11.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a">
        <Configuration>
          <CodeCoverage>
            <ModulePaths>
              <Include>
                <ModulePath>.*MyApp\.dll$</ModulePath>
              </Include>
              <Exclude>
                <ModulePath>.*Tests\.dll$</ModulePath>
                <ModulePath>.*TestHelpers\.dll$</ModulePath>
              </Exclude>
            </ModulePaths>

            <Attributes>
              <Exclude>
                <Attribute>^System\.Diagnostics\.CodeAnalysis\.ExcludeFromCodeCoverageAttribute$</Attribute>
                <Attribute>^System\.CodeDom\.Compiler\.GeneratedCodeAttribute$</Attribute>
              </Exclude>
            </Attributes>

            <Sources>
              <Exclude>
                <Source>.*\\Migrations\\.*</Source>
              </Exclude>
            </Sources>

            <Functions>
              <Exclude>
                <Function>^.*\.Program\.Main\(.*\)$</Function>
              </Exclude>
            </Functions>
          </CodeCoverage>
        </Configuration>
      </DataCollector>
    </DataCollectors>
  </DataCollectionRunSettings>
</RunSettings>
```

## Phase 2: Measure Current Coverage

### Run Coverage Analysis

**Using Coverlet with dotnet test**:
```bash
# Run tests with coverage
dotnet test --collect:"XPlat Code Coverage" --settings coverlet.runsettings

# Run tests with specific format
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=cobertura

# Generate HTML report
reportgenerator \
  -reports:"**/coverage.cobertura.xml" \
  -targetdir:"coverage/report" \
  -reporttypes:"Html;Badges"

# Open HTML report
start coverage/report/index.html  # Windows
open coverage/report/index.html   # macOS
xdg-open coverage/report/index.html  # Linux
```

**Using Visual Studio**:
```bash
# Run with code coverage
dotnet test --collect:"Code Coverage" --settings:.runsettings

# Convert .coverage to XML using CodeCoverage.exe
CodeCoverage.exe analyze /output:coverage.coveragexml coverage.coverage
```

**Using dotCover CLI**:
```bash
# Run tests with coverage
dotnet dotcover test --dcReportType=HTML --dcOutput=coverage/report.html

# Generate detailed report
dotnet dotcover test --dcReportType=DetailedXML --dcOutput=coverage/report.xml
```

### Analyze Coverage Report

**Terminal output example**:
```
Calculating coverage result...
  Generating report 'coverage/coverage.cobertura.xml'

+------------------+--------+--------+--------+
| Module           | Line   | Branch | Method |
+------------------+--------+--------+--------+
| MyApp            | 76.32% | 68.45% | 81.25% |
| MyApp.Services   | 67.42% | 55.56% | 70.59% |
| MyApp.Controllers| 89.11% | 84.21% | 92.00% |
| MyApp.Repositories| 87.50% | 79.31% | 90.00% |
+------------------+--------+--------+--------+

Average coverage: 78.89%
```

### Identify Coverage Gaps

**Create coverage gap analyzer**:

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Xml.Linq;

namespace MyApp.CoverageAnalysis
{
    /// <summary>
    /// Analyze coverage gaps and prioritize improvements.
    /// </summary>
    public class CoverageGapAnalyzer
    {
        public static void AnalyzeCoverageGaps(string coberturaFile)
        {
            var doc = XDocument.Load(coberturaFile);
            var packages = doc.Descendants("package");

            var gaps = new List<CoverageGap>();

            foreach (var package in packages)
            {
                var packageName = package.Attribute("name")?.Value ?? "Unknown";

                foreach (var classElement in package.Descendants("class"))
                {
                    var className = classElement.Attribute("name")?.Value ?? "Unknown";
                    var lineRate = double.Parse(classElement.Attribute("line-rate")?.Value ?? "0");
                    var branchRate = double.Parse(classElement.Attribute("branch-rate")?.Value ?? "0");

                    var avgCoverage = (lineRate + branchRate) / 2.0 * 100;

                    if (avgCoverage < 80.0)
                    {
                        gaps.Add(new CoverageGap
                        {
                            ClassName = className,
                            PackageName = packageName,
                            AvgCoverage = avgCoverage,
                            LineCoverage = lineRate * 100,
                            BranchCoverage = branchRate * 100,
                            Priority = avgCoverage < 50.0 ? "HIGH" : "MEDIUM"
                        });
                    }
                }
            }

            gaps = gaps.OrderBy(g => g.AvgCoverage).ToList();

            Console.WriteLine("=".PadRight(80, '='));
            Console.WriteLine("Coverage Gap Analysis");
            Console.WriteLine("=".PadRight(80, '='));
            Console.WriteLine($"{"Class",-50} {"Avg",8} {"Lines",8} {"Branch",8} {"Priority",10}");
            Console.WriteLine("-".PadRight(80, '-'));

            foreach (var gap in gaps)
            {
                Console.WriteLine(
                    $"{gap.ClassName,-50} " +
                    $"{gap.AvgCoverage,7:F1}% " +
                    $"{gap.LineCoverage,7:F1}% " +
                    $"{gap.BranchCoverage,7:F1}% " +
                    $"{gap.Priority,10}");
            }

            Console.WriteLine($"\nTotal classes needing improvement: {gaps.Count}");
        }

        private class CoverageGap
        {
            public string ClassName { get; set; }
            public string PackageName { get; set; }
            public double AvgCoverage { get; set; }
            public double LineCoverage { get; set; }
            public double BranchCoverage { get; set; }
            public string Priority { get; set; }
        }
    }
}
```

Run analysis:
```bash
dotnet run --project CoverageAnalysis -- coverage/coverage.cobertura.xml
```

## Phase 3: Prioritize Coverage Improvements

### Coverage Improvement Matrix

| Priority | Criteria | Action |
|----------|----------|--------|
| **Critical** | Core business logic <50% coverage | Immediate test creation |
| **High** | Public APIs <70% coverage | Test in current sprint |
| **Medium** | Utilities <80% coverage | Test in next sprint |
| **Low** | DTOs/Models <80% coverage | Test when modified |

### Identify Critical Paths

```csharp
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace MyApp.CoverageAnalysis
{
    /// <summary>
    /// Identify critical code paths requiring coverage.
    /// </summary>
    public class CriticalPathAnalyzer
    {
        public static void AnalyzeCriticalPaths(string sourceDirectory)
        {
            var files = Directory.GetFiles(sourceDirectory, "*.cs", SearchOption.AllDirectories);

            foreach (var file in files)
            {
                var code = File.ReadAllText(file);
                var tree = CSharpSyntaxTree.ParseText(code);
                var root = tree.GetRoot();

                var critical = new List<CriticalPath>();

                var methods = root.DescendantNodes().OfType<MethodDeclarationSyntax>();

                foreach (var method in methods)
                {
                    // Public methods are critical
                    if (method.Modifiers.Any(m => m.IsKind(SyntaxKind.PublicKeyword)))
                    {
                        critical.Add(new CriticalPath
                        {
                            Name = method.Identifier.Text,
                            Line = method.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
                            Reason = "Public API"
                        });
                    }

                    // Methods with try-catch are critical
                    var tryStatements = method.DescendantNodes().OfType<TryStatementSyntax>();
                    if (tryStatements.Any())
                    {
                        critical.Add(new CriticalPath
                        {
                            Name = method.Identifier.Text,
                            Line = method.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
                            Reason = "Error handling"
                        });
                    }
                }

                if (critical.Any())
                {
                    Console.WriteLine($"\n{file}:");
                    foreach (var path in critical)
                    {
                        Console.WriteLine($"  Line {path.Line}: {path.Name} ({path.Reason})");
                    }
                }
            }
        }

        private class CriticalPath
        {
            public string Name { get; set; }
            public int Line { get; set; }
            public string Reason { get; set; }
        }
    }
}
```

## Phase 4: Systematic Coverage Improvement

### Strategy 1: Fill Happy Path Coverage

```csharp
/**
 * Add tests for basic functionality of uncovered code.
 *
 * Focus on main execution paths first.
 */

// Uncovered class
public class DiscountCalculator
{
    public decimal CalculateDiscount(decimal price, CustomerType customerType)
    {
        return customerType switch
        {
            CustomerType.Premium => price * 0.20m,
            CustomerType.Regular => price * 0.10m,
            _ => 0m
        };
    }
}

// Add basic coverage tests (xUnit)
using Xunit;

public class DiscountCalculatorTests
{
    private readonly DiscountCalculator _calculator = new();

    [Fact]
    public void CalculateDiscount_PremiumCustomer_Returns20Percent()
    {
        var discount = _calculator.CalculateDiscount(100m, CustomerType.Premium);
        Assert.Equal(20m, discount);
    }

    [Fact]
    public void CalculateDiscount_RegularCustomer_Returns10Percent()
    {
        var discount = _calculator.CalculateDiscount(100m, CustomerType.Regular);
        Assert.Equal(10m, discount);
    }

    [Fact]
    public void CalculateDiscount_GuestCustomer_ReturnsZero()
    {
        var discount = _calculator.CalculateDiscount(100m, CustomerType.Guest);
        Assert.Equal(0m, discount);
    }
}
```

### Strategy 2: Cover Edge Cases

```csharp
/**
 * Add tests for boundary conditions and edge cases.
 */

using Xunit;

public class DiscountCalculatorEdgeCaseTests
{
    private readonly DiscountCalculator _calculator = new();

    [Fact]
    public void CalculateDiscount_ZeroPrice_ReturnsZero()
    {
        var discount = _calculator.CalculateDiscount(0m, CustomerType.Premium);
        Assert.Equal(0m, discount);
    }

    [Fact]
    public void CalculateDiscount_NegativePrice_ReturnsNegativeDiscount()
    {
        var discount = _calculator.CalculateDiscount(-100m, CustomerType.Premium);
        Assert.Equal(-20m, discount); // Or should throw?
    }

    [Fact]
    public void CalculateDiscount_VeryLargePrice_ReturnsCorrectDiscount()
    {
        var discount = _calculator.CalculateDiscount(1_000_000m, CustomerType.Premium);
        Assert.Equal(200_000m, discount);
    }

    [Theory]
    [InlineData(0.01)]
    [InlineData(10.0)]
    [InlineData(99.99)]
    [InlineData(1000.0)]
    [InlineData(1000000.0)]
    public void CalculateDiscount_VariousPrices_ReturnsNonNegative(decimal price)
    {
        var discount = _calculator.CalculateDiscount(price, CustomerType.Premium);
        Assert.True(discount >= 0);
    }

    [Fact]
    public void CalculateDiscount_MaxDecimal_DoesNotOverflow()
    {
        var discount = _calculator.CalculateDiscount(decimal.MaxValue, CustomerType.Premium);
        Assert.True(discount > 0);
    }
}
```

### Strategy 3: Cover Error Paths

```csharp
/**
 * Add tests for error handling and exceptional conditions.
 */

// Class with error handling
public class UserService
{
    private readonly IUserRepository _repository;
    private readonly ILogger<UserService> _logger;

    public async Task<User?> LoadUserDataAsync(long userId)
    {
        try
        {
            var user = await _repository.FindByIdAsync(userId);

            if (user == null)
            {
                throw new UserNotFoundException($"User not found: {userId}");
            }

            return user;
        }
        catch (DatabaseException ex)
        {
            _logger.LogError(ex, "Database error loading user: {UserId}", userId);
            throw;
        }
        catch (UserNotFoundException ex)
        {
            _logger.LogWarning("User not found: {UserId}", userId);
            return null;
        }
    }
}

// Tests covering error paths (xUnit + Moq)
using Moq;
using Xunit;

public class UserServiceErrorHandlingTests
{
    private readonly Mock<IUserRepository> _mockRepository;
    private readonly Mock<ILogger<UserService>> _mockLogger;
    private readonly UserService _service;

    public UserServiceErrorHandlingTests()
    {
        _mockRepository = new Mock<IUserRepository>();
        _mockLogger = new Mock<ILogger<UserService>>();
        _service = new UserService(_mockRepository.Object, _mockLogger.Object);
    }

    [Fact]
    public async Task LoadUserDataAsync_DatabaseError_ThrowsAndLogs()
    {
        _mockRepository.Setup(r => r.FindByIdAsync(123))
            .ThrowsAsync(new DatabaseException("Connection failed"));

        await Assert.ThrowsAsync<DatabaseException>(() =>
            _service.LoadUserDataAsync(123));

        _mockLogger.Verify(
            l => l.Log(
                LogLevel.Error,
                It.IsAny<EventId>(),
                It.Is<It.IsAnyType>((v, t) => v.ToString().Contains("Database error")),
                It.IsAny<DatabaseException>(),
                It.IsAny<Func<It.IsAnyType, Exception?, string>>()),
            Times.Once);
    }

    [Fact]
    public async Task LoadUserDataAsync_UserNotFound_ReturnsNullAndLogs()
    {
        _mockRepository.Setup(r => r.FindByIdAsync(999))
            .ReturnsAsync((User?)null);

        var result = await _service.LoadUserDataAsync(999);

        Assert.Null(result);
        _mockLogger.Verify(
            l => l.Log(
                LogLevel.Warning,
                It.IsAny<EventId>(),
                It.Is<It.IsAnyType>((v, t) => v.ToString().Contains("User not found")),
                null,
                It.IsAny<Func<It.IsAnyType, Exception?, string>>()),
            Times.Once);
    }
}
```

### Strategy 4: Cover Branch Conditions

```csharp
/**
 * Ensure all branches of conditional logic are tested.
 */

public class ShippingCalculator
{
    public decimal CalculateShippingCost(
        double weight,
        Destination destination,
        bool express)
    {
        var baseCost = (decimal)(weight * 2.5);

        if (destination == Destination.International)
        {
            baseCost *= 3;
        }
        else if (destination == Destination.Remote)
        {
            baseCost *= 1.5m;
        }

        if (express)
        {
            baseCost *= 2;
        }

        return baseCost;
    }
}

// Tests covering all branches
using Xunit;

public class ShippingCalculatorBranchTests
{
    private readonly ShippingCalculator _calculator = new();

    [Theory]
    [InlineData(Destination.Domestic, false, 25.0)]
    [InlineData(Destination.Domestic, true, 50.0)]
    [InlineData(Destination.International, false, 75.0)]
    [InlineData(Destination.International, true, 150.0)]
    [InlineData(Destination.Remote, false, 37.5)]
    [InlineData(Destination.Remote, true, 75.0)]
    public void CalculateShippingCost_AllBranches_ReturnsCorrectCost(
        Destination destination,
        bool express,
        decimal expected)
    {
        var cost = _calculator.CalculateShippingCost(10.0, destination, express);
        Assert.Equal(expected, cost);
    }
}
```

## Phase 5: Coverage Reporting and Tracking

### Generate Comprehensive Reports

```bash
# Generate all report types
dotnet test --collect:"XPlat Code Coverage" --settings coverlet.runsettings

# Generate HTML report with history
reportgenerator \
  -reports:"**/coverage.cobertura.xml" \
  -targetdir:"coverage/report" \
  -reporttypes:"Html;Badges;Cobertura;JsonSummary" \
  -historydir:"coverage/history"

# Reports generated:
# - coverage/report/index.html (browsable HTML)
# - coverage/coverage.cobertura.xml (for CI/CD)
# - coverage/report/Summary.json (for analysis)
# - coverage/report/badge_*.svg (badges)
```

### Coverage Badge

```markdown
# Add to README.md
![Line Coverage](coverage/report/badge_linecoverage.svg)
![Branch Coverage](coverage/report/badge_branchcoverage.svg)
![Method Coverage](coverage/report/badge_methodcoverage.svg)
```

### Track Coverage Over Time

```csharp
using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Xml.Linq;

namespace MyApp.CoverageAnalysis
{
    /// <summary>
    /// Track coverage metrics over time.
    /// </summary>
    public class CoverageTracker
    {
        public static void RecordCoverage()
        {
            var coberturaFile = "coverage/coverage.cobertura.xml";
            var historyFile = "coverage-history.json";

            if (!File.Exists(coberturaFile))
            {
                Console.Error.WriteLine("No coverage.cobertura.xml found");
                return;
            }

            var doc = XDocument.Load(coberturaFile);
            var coverage = doc.Root?.Attribute("line-rate")?.Value ?? "0";
            var lineCoverage = double.Parse(coverage) * 100;

            var history = new List<CoverageRecord>();
            if (File.Exists(historyFile))
            {
                var json = File.ReadAllText(historyFile);
                history = JsonSerializer.Deserialize<List<CoverageRecord>>(json)
                    ?? new List<CoverageRecord>();
            }

            history.Add(new CoverageRecord
            {
                Date = DateTime.Now,
                LineCoverage = lineCoverage
            });

            var options = new JsonSerializerOptions { WriteIndented = true };
            File.WriteAllText(historyFile, JsonSerializer.Serialize(history, options));

            Console.WriteLine($"Coverage recorded: {lineCoverage:F1}% lines");
        }

        private class CoverageRecord
        {
            public DateTime Date { get; set; }
            public double LineCoverage { get; set; }
        }
    }
}
```

### Coverage Diff for PRs

```csharp
using System;
using System.IO;
using System.Text.Json;

namespace MyApp.CoverageAnalysis
{
    /// <summary>
    /// Show coverage changes in pull request.
    /// </summary>
    public class CoverageDiff
    {
        public static void CompareCoverage(string basePath, string currentPath)
        {
            var baseRecord = LoadCoverage(basePath);
            var currentRecord = LoadCoverage(currentPath);

            var diff = currentRecord - baseRecord;

            Console.WriteLine(new string('=', 80));
            Console.WriteLine("Coverage Diff");
            Console.WriteLine(new string('=', 80));
            Console.WriteLine($"Base coverage:    {baseRecord:F2}%");
            Console.WriteLine($"Current coverage: {currentRecord:F2}%");
            Console.WriteLine($"Difference:       {diff:+0.00;-0.00}%");

            if (diff < -0.5)
            {
                Console.WriteLine($"\n❌ Coverage decreased by {Math.Abs(diff):F2}%");
                Environment.Exit(1);
            }
            else if (diff < 0)
            {
                Console.WriteLine($"\n⚠️ Coverage decreased slightly by {Math.Abs(diff):F2}%");
            }
            else
            {
                Console.WriteLine("\n✅ Coverage maintained or improved");
            }
        }

        private static double LoadCoverage(string path)
        {
            var json = File.ReadAllText(path);
            var summary = JsonSerializer.Deserialize<JsonDocument>(json);
            return summary?.RootElement.GetProperty("summary")
                .GetProperty("linecoverage").GetDouble() ?? 0.0;
        }
    }
}
```

## Phase 6: Coverage in CI/CD

### GitHub Actions Coverage Integration

```yaml
# .github/workflows/coverage.yml
name: Coverage

on: [push, pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup .NET
        uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '8.0.x'

      - name: Restore dependencies
        run: dotnet restore

      - name: Run tests with coverage
        run: |
          dotnet test --no-restore \
            --collect:"XPlat Code Coverage" \
            --settings coverlet.runsettings

      - name: Generate coverage report
        run: |
          dotnet tool install --global dotnet-reportgenerator-globaltool
          reportgenerator \
            -reports:"**/coverage.cobertura.xml" \
            -targetdir:"coverage/report" \
            -reporttypes:"Html;Badges;Cobertura;JsonSummary"

      - name: Check coverage threshold
        run: |
          COVERAGE=$(grep -oP 'line-rate="\K[^"]*' coverage/coverage.cobertura.xml | head -1)
          COVERAGE_PCT=$(echo "$COVERAGE * 100" | bc)
          if (( $(echo "$COVERAGE_PCT < 80" | bc -l) )); then
            echo "Coverage $COVERAGE_PCT% is below threshold 80%"
            exit 1
          fi

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage.cobertura.xml
          fail_ci_if_error: true

      - name: Archive coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: coverage/report/
```

### Coverage Regression Prevention

```yaml
# Add to existing workflow

- name: Check for coverage regression
  run: |
    # Download base coverage from main branch
    git fetch origin main
    git show origin/main:coverage/Summary.json > ${OUTPUT_DIR}/exports/base-summary.json

    # Compare with current
    dotnet run --project CoverageAnalysis -- \
      compare base-summary.json coverage/report/Summary.json
```

## Output Format

Please provide a comprehensive coverage analysis with the following structure:

### Coverage Summary

- **Overall Coverage**: [percentage]

- **Line Coverage**: [percentage]

- **Branch Coverage**: [percentage]

- **Method Coverage**: [percentage]

- **Total Lines**: [count]

- **Covered Lines**: [count]

- **Uncovered Lines**: [count]

### Coverage by Assembly
| Assembly | Line | Branch | Method | Priority |
|----------|------|--------|--------|----------|
| MyApp.Services | 76% | 68% | 81% | High |
| MyApp.Controllers | 89% | 84% | 92% | Low |
| MyApp.Repositories | 87% | 79% | 90% | Medium |

### Critical Coverage Gaps
1. **MyApp.Services.UserService** (67% line coverage)
   - **Missing**: Error handling branches
   - **Priority**: Critical - core business logic
   - **Action**: Add exception handling tests

2. **MyApp.Security.AuthService** (78% line coverage)
   - **Missing**: Edge cases in authentication
   - **Priority**: High - security-critical
   - **Action**: Add boundary condition tests

### Coverage Improvement Plan
**Sprint 1** (Target: 75% → 80%):

- [ ] Add error handling tests for service layer

- [ ] Cover authentication edge cases

- [ ] Test repository exception handling

**Sprint 2** (Target: 80% → 85%):

- [ ] Add branch coverage for conditionals

- [ ] Test validation logic thoroughly

- [ ] Cover integration scenarios

**Sprint 3** (Target: 85% → 90%):

- [ ] Add async/await edge cases

- [ ] Cover all exception types

- [ ] Test disposal patterns

### Coverage Reports Generated

- **HTML Report**: `coverage/report/index.html`

- **Cobertura XML**: `coverage/coverage.cobertura.xml` (for CI/CD)

- **JSON Summary**: `coverage/report/Summary.json` (for analysis)

- **Badges**: `coverage/report/badge_*.svg` (for README)

### Coverage Thresholds

- **Minimum Overall**: 80%

- **Critical Assemblies**: 90%

- **New Code**: 100%

- **CI/CD Gate**: Fail if <80%

### Best Practices Implemented

- [ ] Coverage measured on every test run

- [ ] HTML reports for detailed analysis

- [ ] Coverage tracked over time with history

- [ ] Regression prevention in CI/CD

- [ ] Critical paths prioritized

- [ ] Team coverage goals established

### Next Steps

- [ ] Fix identified coverage gaps

- [ ] Set up coverage dashboard

- [ ] Schedule coverage review meetings

- [ ] Document coverage standards

- [ ] Integrate coverage diff in PRs

- [ ] Track coverage trends monthly

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

1. **Complete coverage configuration** (.csproj, coverlet.runsettings, or .runsettings)
2. **Current coverage analysis** with gaps identified
3. **Prioritized improvement plan** with specific actions
4. **Test implementations** to fill critical gaps (xUnit, NUnit, or MSTest)
5. **Coverage reporting infrastructure** (HTML, Cobertura, JSON)
6. **CI/CD integration** with coverage gates
7. **Coverage tracking utilities** for trends
8. **Coverage diff tools** for PR reviews
9. **Team documentation** on coverage standards
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
