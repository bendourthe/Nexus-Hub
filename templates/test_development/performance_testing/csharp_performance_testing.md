---
template_id: csharp_performance_testing
template_name: Performance Testing - C#
version: 1.0.0
last_updated: 2025-12-03
language: C#
category: test_development
phase: performance_testing
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:

  - test_development/mocks_fixtures/csharp_mocks_fixtures.md
related_templates:

  - test_development/code_coverage/csharp_code_coverage.md
tools:

  - NUnit (4.2.2)

  - xUnit

  - MSTest
tags:

  - test-development

  - testing

  - performance

  - c#
---
# C# Performance Testing

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                ► │ [COMPLETE]
│ Phase 4: Mocks & Fixtures                      ► │ [COMPLETE]
│ Phase 5: Performance Testing                    ► │ ● CURRENT
│ Phase 6: Code Coverage                             ► │ [NEXT]
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 4 (Mocks & Fixtures) should be completed first
**Next Step:** Phase 6 (Code Coverage)

---


## Objective
Implement comprehensive performance testing to validate system behavior under load, identify bottlenecks, measure response times, profile resource usage, detect performance regressions, and ensure scalability requirements are met using C#/.NET tooling.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/performance_testing/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/performance_testing/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Performance Test Coverage

- [ ] Load tests implemented for critical endpoints

- [ ] Stress tests validate beyond-capacity behavior

- [ ] Baseline benchmarks established with BenchmarkDotNet

- [ ] Performance regression tests configured

- [ ] Resource profiling set up

### Metrics and Monitoring

- [ ] Response time thresholds defined

- [ ] Throughput targets established

- [ ] Resource usage limits set (memory, GC pauses)

- [ ] Error rate thresholds configured

- [ ] Performance reports automated

### Test Infrastructure

- [ ] BenchmarkDotNet configured

- [ ] Load testing tools set up (NBomber, K6)

- [ ] Performance test data prepared

- [ ] CI/CD integration planned

- [ ] Results storage and trending implemented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Performance Testing Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/performance_testing"
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

Please implement comprehensive performance testing for this C#/.NET project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Performance Requirements Definition

### Define Performance Targets

Document expected performance characteristics:

**Response Time Requirements**:
| Endpoint/Operation | P50 (median) | P95 | P99 | Timeout |
|-------------------|--------------|-----|-----|---------|
| GET /api/users | <100ms | <200ms | <500ms | 2s |
| POST /api/users | <200ms | <400ms | <1s | 5s |
| Database query | <50ms | <100ms | <200ms | 1s |
| Cache lookup | <5ms | <10ms | <20ms | 100ms |

**Throughput Requirements**:
| Operation | Target RPS | Peak RPS | Concurrent Requests |
|-----------|------------|----------|---------------------|
| REST API | 100 | 500 | 200 |
| Message processing | 50 | 100 | N/A |

**Resource Limits**:

- **Memory**: <1GB working set

- **GC Pause**: <50ms P99

- **CPU**: <80% average, <95% peak

- **Thread pool**: <500 threads

- **Database connections**: <50 concurrent

## Phase 2: Benchmarking with BenchmarkDotNet

### Setup BenchmarkDotNet

```xml
<!-- Add to .csproj -->
<ItemGroup>
    <PackageReference Include="BenchmarkDotNet" Version="0.13.10" />
    <PackageReference Include="BenchmarkDotNet.Diagnostics.Windows" Version="0.13.10" />
</ItemGroup>
```

### Basic Benchmark

```csharp
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Running;
using BenchmarkDotNet.Jobs;
using System.Collections.Generic;
using System.Linq;

namespace PerformanceTests.Benchmarks
{
    /// <summary>
    /// Benchmark for data processing operations.
    ///
    /// Run with: dotnet run -c Release --project BenchmarkProject
    /// </summary>
    [MemoryDiagnoser]
    [SimpleJob(RuntimeMoniker.Net80)]
    [MinColumn, MaxColumn, MeanColumn, MedianColumn]
    public class DataProcessingBenchmark
    {
        private List<User> _testUsers;
        private string _searchQuery;

        [GlobalSetup]
        public void Setup()
        {
            // Setup runs once before all benchmarks
            _testUsers = GenerateTestUsers(1000);
            _searchQuery = "test";
        }

        [Benchmark(Baseline = true)]
        public List<User> LinearSearch()
        {
            var results = new List<User>();
            foreach (var user in _testUsers)
            {
                if (user.Name.Contains(_searchQuery))
                {
                    results.Add(user);
                }
            }
            return results;
        }

        [Benchmark]
        public List<User> LinqWhere()
        {
            return _testUsers
                .Where(u => u.Name.Contains(_searchQuery))
                .ToList();
        }

        [Benchmark]
        public List<User> LinqQuery()
        {
            return (from user in _testUsers
                    where user.Name.Contains(_searchQuery)
                    select user).ToList();
        }

        [Benchmark]
        public List<User> ParallelLinq()
        {
            return _testUsers
                .AsParallel()
                .Where(u => u.Name.Contains(_searchQuery))
                .ToList();
        }

        [Benchmark]
        public List<User> SpanBased()
        {
            var results = new List<User>();
            var span = _testUsers.AsSpan();
            foreach (var user in span)
            {
                if (user.Name.Contains(_searchQuery))
                {
                    results.Add(user);
                }
            }
            return results;
        }

        private List<User> GenerateTestUsers(int count)
        {
            // Implementation
            return Enumerable.Range(1, count)
                .Select(i => new User { Id = i, Name = $"User{i}" })
                .ToList();
        }
    }

    public class User
    {
        public int Id { get; set; }
        public string Name { get; set; }
    }

    public class Program
    {
        public static void Main(string[] args)
        {
            BenchmarkRunner.Run<DataProcessingBenchmark>();
        }
    }
}
```

### Advanced BenchmarkDotNet Patterns

```csharp
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Engines;
using BenchmarkDotNet.Diagnostics.Windows.Configs;
using System;
using System.Collections.Generic;

namespace PerformanceTests.Benchmarks
{
    /// <summary>
    /// Advanced benchmark patterns with parameterization and diagnostics.
    /// </summary>
    [MemoryDiagnoser]
    [ThreadingDiagnoser]
    [SimpleJob(RunStrategy.Monitoring, warmupCount: 3, targetCount: 5)]
    [MinColumn, MaxColumn, MeanColumn, MedianColumn, StdDevColumn]
    [RPlotExporter] // Generate plots
    public class AdvancedBenchmarks
    {
        [Params(100, 1000, 10000)]
        public int DataSize { get; set; }

        private List<string> _data;
        private readonly Consumer _consumer = new Consumer();

        [GlobalSetup]
        public void GlobalSetup()
        {
            Console.WriteLine($"Setting up benchmark with DataSize: {DataSize}");
        }

        [IterationSetup]
        public void IterationSetup()
        {
            // Runs before each iteration
            _data = GenerateTestData(DataSize);
        }

        [IterationCleanup]
        public void IterationCleanup()
        {
            // Cleanup after each iteration
            _data = null;
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();
        }

        [Benchmark]
        [Arguments(100)]
        [Arguments(1000)]
        public void BenchmarkWithArguments(int iterations)
        {
            for (int i = 0; i < iterations; i++)
            {
                ProcessData(_data);
            }
        }

        [Benchmark]
        public void StringConcatenation()
        {
            string result = "";
            for (int i = 0; i < DataSize; i++)
            {
                result += i.ToString();
            }
            _consumer.Consume(result);
        }

        [Benchmark]
        public void StringBuilder()
        {
            var sb = new System.Text.StringBuilder();
            for (int i = 0; i < DataSize; i++)
            {
                sb.Append(i);
            }
            _consumer.Consume(sb.ToString());
        }

        [Benchmark]
        public void StringCreate()
        {
            var result = string.Create(DataSize * 5, DataSize, (span, size) =>
            {
                for (int i = 0; i < size; i++)
                {
                    i.ToString().AsSpan().CopyTo(span);
                    span = span.Slice(i.ToString().Length);
                }
            });
            _consumer.Consume(result);
        }

        private List<string> GenerateTestData(int size)
        {
            var data = new List<string>(size);
            for (int i = 0; i < size; i++)
            {
                data.Add($"Item{i}");
            }
            return data;
        }

        private void ProcessData(List<string> data)
        {
            // Processing logic
        }
    }

    /// <summary>
    /// Benchmark comparing different collection types.
    /// </summary>
    [MemoryDiagnoser]
    [SimpleJob]
    public class CollectionBenchmarks
    {
        private const int ItemCount = 10000;

        [Benchmark]
        public List<int> ListAddition()
        {
            var list = new List<int>();
            for (int i = 0; i < ItemCount; i++)
            {
                list.Add(i);
            }
            return list;
        }

        [Benchmark]
        public List<int> ListWithCapacity()
        {
            var list = new List<int>(ItemCount);
            for (int i = 0; i < ItemCount; i++)
            {
                list.Add(i);
            }
            return list;
        }

        [Benchmark]
        public int[] ArrayFill()
        {
            var array = new int[ItemCount];
            for (int i = 0; i < ItemCount; i++)
            {
                array[i] = i;
            }
            return array;
        }

        [Benchmark]
        public HashSet<int> HashSetAddition()
        {
            var set = new HashSet<int>();
            for (int i = 0; i < ItemCount; i++)
            {
                set.Add(i);
            }
            return set;
        }
    }
}
```

### Running BenchmarkDotNet

```bash
# Run benchmarks in Release mode
dotnet run -c Release --project BenchmarkProject

# Run specific benchmark
dotnet run -c Release --project BenchmarkProject --filter *DataProcessingBenchmark*

# Run with specific runtime
dotnet run -c Release --project BenchmarkProject --runtimes net6.0 net8.0

# Export results
dotnet run -c Release --project BenchmarkProject --exporters json html

# Run with memory profiler
dotnet run -c Release --project BenchmarkProject --profiler ETW
```

## Phase 3: Load Testing with NBomber

### Setup NBomber

```xml
<!-- Add to .csproj -->
<ItemGroup>
    <PackageReference Include="NBomber" Version="5.5.0" />
    <PackageReference Include="NBomber.Http" Version="5.5.0" />
</ItemGroup>
```

### Basic Load Test

```csharp
using NBomber.CSharp;
using NBomber.Http.CSharp;
using System;
using System.Net.Http;

namespace PerformanceTests.LoadTests
{
    /// <summary>
    /// Basic load test for REST API using NBomber.
    ///
    /// Run with: dotnet run --project LoadTestProject
    /// </summary>
    public class BasicApiLoadTest
    {
        public static void Main()
        {
            using var httpClient = new HttpClient();

            var scenario = Scenario.Create("api_load_test", async context =>
            {
                var request = Http.CreateRequest("GET", "http://localhost:5000/api/users")
                    .WithHeader("Accept", "application/json");

                var response = await Http.Send(httpClient, request);

                return response;
            })
            .WithWarmUpDuration(TimeSpan.FromSeconds(5))
            .WithLoadSimulations(
                Simulation.RampingInject(
                    rate: 100,
                    interval: TimeSpan.FromSeconds(1),
                    during: TimeSpan.FromSeconds(30)
                ),
                Simulation.Inject(
                    rate: 100,
                    interval: TimeSpan.FromSeconds(1),
                    during: TimeSpan.FromMinutes(1)
                ),
                Simulation.RampingInject(
                    rate: 0,
                    interval: TimeSpan.FromSeconds(1),
                    during: TimeSpan.FromSeconds(30)
                )
            );

            NBomberRunner
                .RegisterScenarios(scenario)
                .WithReportFileName("api_load_test")
                .WithReportFormats(ReportFormat.Html, ReportFormat.Csv)
                .Run();
        }
    }
}
```

### Advanced NBomber Scenarios

```csharp
using NBomber.CSharp;
using NBomber.Http.CSharp;
using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;

namespace PerformanceTests.LoadTests
{
    /// <summary>
    /// Advanced load test with multiple scenarios and user workflows.
    /// </summary>
    public class AdvancedApiLoadTest
    {
        public static void Main()
        {
            using var httpClient = new HttpClient
            {
                BaseAddress = new Uri("http://localhost:5000")
            };

            // Scenario 1: Read-heavy workflow
            var readScenario = Scenario.Create("read_scenario", async context =>
            {
                var step1 = await Step.Run("get_users", context, async () =>
                {
                    var request = Http.CreateRequest("GET", "/api/users");
                    var response = await Http.Send(httpClient, request);
                    return response;
                });

                await Task.Delay(1000); // Simulate user think time

                var userId = context.Random.Next(1, 1000);
                var step2 = await Step.Run("get_user_detail", context, async () =>
                {
                    var request = Http.CreateRequest("GET", $"/api/users/{userId}");
                    var response = await Http.Send(httpClient, request);
                    return response;
                });

                return Response.Ok();
            })
            .WithWarmUpDuration(TimeSpan.FromSeconds(10))
            .WithLoadSimulations(
                Simulation.KeepConstant(copies: 50, during: TimeSpan.FromMinutes(2))
            );

            // Scenario 2: Write-heavy workflow
            var writeScenario = Scenario.Create("write_scenario", async context =>
            {
                var step1 = await Step.Run("create_user", context, async () =>
                {
                    var user = new
                    {
                        Username = $"user_{context.ScenarioInfo.ThreadId}_{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}",
                        Email = $"user{context.Random.Next(1, 10000)}@test.com"
                    };

                    var request = Http.CreateRequest("POST", "/api/users")
                        .WithJsonBody(user);

                    var response = await Http.Send(httpClient, request);
                    return response;
                });

                await Task.Delay(2000);

                var step2 = await Step.Run("update_user", context, async () =>
                {
                    var userId = context.Random.Next(1, 1000);
                    var update = new { Bio = "Updated bio text" };

                    var request = Http.CreateRequest("PUT", $"/api/users/{userId}")
                        .WithJsonBody(update);

                    var response = await Http.Send(httpClient, request);
                    return response;
                });

                return Response.Ok();
            })
            .WithWarmUpDuration(TimeSpan.FromSeconds(10))
            .WithLoadSimulations(
                Simulation.KeepConstant(copies: 20, during: TimeSpan.FromMinutes(2))
            );

            // Scenario 3: Spike test
            var spikeScenario = Scenario.Create("spike_scenario", async context =>
            {
                var request = Http.CreateRequest("GET", "/api/health");
                var response = await Http.Send(httpClient, request);
                return response;
            })
            .WithWarmUpDuration(TimeSpan.FromSeconds(5))
            .WithLoadSimulations(
                Simulation.RampingInject(
                    rate: 10,
                    interval: TimeSpan.FromSeconds(1),
                    during: TimeSpan.FromSeconds(30)
                ),
                Simulation.Inject(
                    rate: 200, // Spike
                    interval: TimeSpan.FromSeconds(1),
                    during: TimeSpan.FromSeconds(10)
                ),
                Simulation.RampingInject(
                    rate: 10,
                    interval: TimeSpan.FromSeconds(1),
                    during: TimeSpan.FromSeconds(30)
                )
            );

            NBomberRunner
                .RegisterScenarios(readScenario, writeScenario, spikeScenario)
                .WithReportFileName("advanced_load_test")
                .WithReportFormats(ReportFormat.Html, ReportFormat.Csv, ReportFormat.Md)
                .WithTestSuite("API Load Tests")
                .WithTestName("Full API Test Suite")
                .Run();
        }
    }
}
```

### NBomber with Data Feed

```csharp
using NBomber.CSharp;
using NBomber.Http.CSharp;
using System.Collections.Generic;
using System.Linq;

namespace PerformanceTests.LoadTests
{
    public class DataFeedLoadTest
    {
        public static void Main()
        {
            // Create test data feed
            var users = Enumerable.Range(1, 1000)
                .Select(i => new { Id = i, Username = $"user{i}" })
                .ToList();

            var feed = Feed.CreateCircular("users_feed", users);

            using var httpClient = new HttpClient();

            var scenario = Scenario.Create("data_feed_test", async context =>
            {
                var user = feed.GetNextItem(context.ScenarioInfo);

                var request = Http.CreateRequest("GET", $"/api/users/{user.Id}");
                var response = await Http.Send(httpClient, request);

                return response;
            })
            .WithWarmUpDuration(TimeSpan.FromSeconds(5))
            .WithLoadSimulations(
                Simulation.Inject(
                    rate: 50,
                    interval: TimeSpan.FromSeconds(1),
                    during: TimeSpan.FromMinutes(2)
                )
            );

            NBomberRunner
                .RegisterScenarios(scenario)
                .WithReportFileName("data_feed_test")
                .Run();
        }
    }
}
```

## Phase 4: Stress Testing

### Stress Test Implementation

```csharp
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Xunit;
using Xunit.Abstractions;

namespace PerformanceTests.StressTests
{
    /// <summary>
    /// Stress tests to find system breaking points.
    /// </summary>
    public class StressTests
    {
        private readonly ITestOutputHelper _output;
        private readonly HttpClient _httpClient;

        public StressTests(ITestOutputHelper output)
        {
            _output = output;
            _httpClient = new HttpClient
            {
                BaseAddress = new Uri("http://localhost:5000")
            };
        }

        [Fact]
        public async Task TestMaxConcurrentRequests()
        {
            const int maxConcurrency = 1000;
            var successCount = 0;
            var failureCount = 0;
            var responseTimes = new ConcurrentBag<long>();

            var sw = Stopwatch.StartNew();

            var tasks = Enumerable.Range(0, maxConcurrency)
                .Select(async i =>
                {
                    var requestSw = Stopwatch.StartNew();
                    try
                    {
                        var response = await _httpClient.GetAsync("/api/users");
                        requestSw.Stop();
                        responseTimes.Add(requestSw.ElapsedMilliseconds);

                        if (response.IsSuccessStatusCode)
                        {
                            Interlocked.Increment(ref successCount);
                        }
                        else
                        {
                            Interlocked.Increment(ref failureCount);
                        }
                    }
                    catch (Exception)
                    {
                        Interlocked.Increment(ref failureCount);
                    }
                });

            await Task.WhenAll(tasks);
            sw.Stop();

            var avgResponseTime = responseTimes.Average();
            var p95ResponseTime = CalculatePercentile(responseTimes.OrderBy(x => x).ToList(), 95);

            _output.WriteLine("Stress Test Results:");
            _output.WriteLine($"  Concurrent Requests: {maxConcurrency}");
            _output.WriteLine($"  Success: {successCount}");
            _output.WriteLine($"  Failures: {failureCount}");
            _output.WriteLine($"  Success Rate: {100.0 * successCount / maxConcurrency:F2}%");
            _output.WriteLine($"  Total Duration: {sw.ElapsedMilliseconds}ms");
            _output.WriteLine($"  Avg Response Time: {avgResponseTime:F2}ms");
            _output.WriteLine($"  P95 Response Time: {p95ResponseTime}ms");

            Assert.True(successCount > maxConcurrency * 0.95,
                $"Too many failures: {failureCount}/{maxConcurrency}");
        }

        [Fact]
        public void TestMemoryStress()
        {
            var initialMemory = GC.GetTotalMemory(true);

            // Perform memory-intensive operations
            var dataList = new List<byte[]>();
            for (int i = 0; i < 10000; i++)
            {
                var data = new byte[10000];
                dataList.Add(data);
                ProcessData(data);
            }

            dataList.Clear();
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();

            var finalMemory = GC.GetTotalMemory(false);
            var memoryIncrease = finalMemory - initialMemory;

            _output.WriteLine("Memory Stress Test:");
            _output.WriteLine($"  Initial Memory: {initialMemory / 1024 / 1024}MB");
            _output.WriteLine($"  Final Memory: {finalMemory / 1024 / 1024}MB");
            _output.WriteLine($"  Memory Increase: {memoryIncrease / 1024 / 1024}MB");

            Assert.True(memoryIncrease < 100 * 1024 * 1024,
                $"Potential memory leak: {memoryIncrease / 1024 / 1024}MB increase");
        }

        [Fact]
        public async Task TestSustainedLoad()
        {
            const int durationMinutes = 5;
            const int requestsPerSecond = 100;

            var stopwatch = Stopwatch.StartNew();
            var endTime = TimeSpan.FromMinutes(durationMinutes);
            var successCount = 0;
            var failureCount = 0;

            while (stopwatch.Elapsed < endTime)
            {
                var tasks = Enumerable.Range(0, requestsPerSecond)
                    .Select(async _ =>
                    {
                        try
                        {
                            var response = await _httpClient.GetAsync("/api/users");
                            if (response.IsSuccessStatusCode)
                            {
                                Interlocked.Increment(ref successCount);
                            }
                            else
                            {
                                Interlocked.Increment(ref failureCount);
                            }
                        }
                        catch
                        {
                            Interlocked.Increment(ref failureCount);
                        }
                    });

                await Task.WhenAll(tasks);
                await Task.Delay(1000);
            }

            _output.WriteLine("Sustained Load Test:");
            _output.WriteLine($"  Duration: {durationMinutes} minutes");
            _output.WriteLine($"  Total Requests: {successCount + failureCount}");
            _output.WriteLine($"  Success: {successCount}");
            _output.WriteLine($"  Failures: {failureCount}");
            _output.WriteLine($"  Success Rate: {100.0 * successCount / (successCount + failureCount):F2}%");

            Assert.True(failureCount < (successCount + failureCount) * 0.01,
                "Failure rate too high under sustained load");
        }

        private void ProcessData(byte[] data)
        {
            // Simulate data processing
        }

        private long CalculatePercentile(List<long> sortedValues, int percentile)
        {
            if (sortedValues.Count == 0) return 0;
            int index = (int)Math.Ceiling(percentile / 100.0 * sortedValues.Count) - 1;
            return sortedValues[Math.Max(0, Math.Min(index, sortedValues.Count - 1))];
        }
    }
}
```

## Phase 5: Profiling and Optimization

### .NET Diagnostic Tools

```csharp
using System;
using System.Diagnostics;
using System.Linq;

namespace PerformanceTests.Profiling
{
    /// <summary>
    /// Performance monitoring utilities using .NET diagnostics.
    /// </summary>
    public class PerformanceMonitor
    {
        public static void PrintMemoryUsage()
        {
            var process = Process.GetCurrentProcess();

            Console.WriteLine("Memory Usage:");
            Console.WriteLine($"  Working Set: {process.WorkingSet64 / 1024 / 1024}MB");
            Console.WriteLine($"  Private Memory: {process.PrivateMemorySize64 / 1024 / 1024}MB");
            Console.WriteLine($"  Managed Memory: {GC.GetTotalMemory(false) / 1024 / 1024}MB");
            Console.WriteLine($"  GC Gen 0: {GC.CollectionCount(0)} collections");
            Console.WriteLine($"  GC Gen 1: {GC.CollectionCount(1)} collections");
            Console.WriteLine($"  GC Gen 2: {GC.CollectionCount(2)} collections");
        }

        public static void PrintThreadPoolStats()
        {
            ThreadPool.GetAvailableThreads(out int workerThreads, out int ioThreads);
            ThreadPool.GetMaxThreads(out int maxWorkerThreads, out int maxIoThreads);

            Console.WriteLine("Thread Pool Stats:");
            Console.WriteLine($"  Worker Threads: {maxWorkerThreads - workerThreads}/{maxWorkerThreads}");
            Console.WriteLine($"  I/O Threads: {maxIoThreads - ioThreads}/{maxIoThreads}");
        }

        public static void MonitorGCPauses(Action action)
        {
            var gcCount0 = GC.CollectionCount(0);
            var gcCount1 = GC.CollectionCount(1);
            var gcCount2 = GC.CollectionCount(2);

            var sw = Stopwatch.StartNew();
            action();
            sw.Stop();

            Console.WriteLine("GC Activity:");
            Console.WriteLine($"  Gen 0 Collections: {GC.CollectionCount(0) - gcCount0}");
            Console.WriteLine($"  Gen 1 Collections: {GC.CollectionCount(1) - gcCount1}");
            Console.WriteLine($"  Gen 2 Collections: {GC.CollectionCount(2) - gcCount2}");
            Console.WriteLine($"  Execution Time: {sw.ElapsedMilliseconds}ms");
        }
    }
}
```

### Using dotnet-trace and dotnet-counters

```bash
# Install diagnostic tools
dotnet tool install --global dotnet-trace
dotnet tool install --global dotnet-counters
dotnet tool install --global dotnet-dump

# List running .NET processes
dotnet-counters ps

# Monitor real-time performance counters
dotnet-counters monitor --process-id <PID>

# Collect performance trace
dotnet-trace collect --process-id <PID> --duration 00:00:30

# Analyze trace with PerfView or Visual Studio
# speedscope can also visualize traces

# Collect memory dump
dotnet-dump collect --process-id <PID>

# Analyze dump
dotnet-dump analyze <dump-file>
```

## Phase 6: Performance Regression Detection

### Baseline Management

```csharp
using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace PerformanceTests.Regression
{
    /// <summary>
    /// Performance baseline management for regression detection.
    /// </summary>
    public class PerformanceBaseline
    {
        private const string BaselineFile = "performance-baseline.json";
        private Dictionary<string, BenchmarkResult> _baselines;

        public PerformanceBaseline()
        {
            _baselines = Load();
        }

        public void Save(string name, BenchmarkResult result)
        {
            _baselines[name] = result;
            WriteToFile();
        }

        public BenchmarkResult Get(string name)
        {
            return _baselines.TryGetValue(name, out var result) ? result : null;
        }

        public RegressionResult Compare(string name, BenchmarkResult current)
        {
            var baseline = Get(name);

            if (baseline == null)
            {
                Save(name, current);
                return new RegressionResult
                {
                    IsRegression = false,
                    IsNewBaseline = true,
                    PercentChange = null
                };
            }

            double percentChange = ((current.Mean - baseline.Mean) / baseline.Mean) * 100;
            bool isRegression = percentChange > 10.0; // 10% threshold

            return new RegressionResult
            {
                IsRegression = isRegression,
                IsNewBaseline = false,
                PercentChange = percentChange,
                BaselineValue = baseline.Mean,
                CurrentValue = current.Mean
            };
        }

        public void PrintComparison(string name, RegressionResult result)
        {
            Console.WriteLine($"\n=== Performance Comparison: {name} ===");

            if (result.IsNewBaseline)
            {
                Console.WriteLine("New baseline created");
                return;
            }

            Console.WriteLine($"Baseline: {result.BaselineValue:F4}ms");
            Console.WriteLine($"Current:  {result.CurrentValue:F4}ms");
            Console.WriteLine($"Change:   {(result.PercentChange > 0 ? "↑" : "↓")} {Math.Abs(result.PercentChange.Value):F2}%");

            if (result.IsRegression)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("\n❌ Performance regression detected!");
                Console.ResetColor();
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("\n✅ No performance regression");
                Console.ResetColor();
            }
        }

        private Dictionary<string, BenchmarkResult> Load()
        {
            if (File.Exists(BaselineFile))
            {
                var json = File.ReadAllText(BaselineFile);
                return JsonSerializer.Deserialize<Dictionary<string, BenchmarkResult>>(json)
                    ?? new Dictionary<string, BenchmarkResult>();
            }
            return new Dictionary<string, BenchmarkResult>();
        }

        private void WriteToFile()
        {
            var options = new JsonSerializerOptions { WriteIndented = true };
            var json = JsonSerializer.Serialize(_baselines, options);
            File.WriteAllText(BaselineFile, json);
        }
    }

    public class BenchmarkResult
    {
        public double Mean { get; set; }
        public string Unit { get; set; }
        public DateTime Timestamp { get; set; }
    }

    public class RegressionResult
    {
        public bool IsRegression { get; set; }
        public bool IsNewBaseline { get; set; }
        public double? PercentChange { get; set; }
        public double BaselineValue { get; set; }
        public double CurrentValue { get; set; }
    }
}
```

## Phase 7: CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  pull_request:
    branches: [ main ]
  schedule:

    - cron: '0 2 * * *'

jobs:
  performance:
    runs-on: ubuntu-latest

    steps:

    - uses: actions/checkout@v3

    - name: Setup .NET
      uses: actions/setup-dotnet@v3
      with:
        dotnet-version: '8.0.x'

    - name: Restore dependencies
      run: dotnet restore

    - name: Build
      run: dotnet build -c Release --no-restore

    - name: Run BenchmarkDotNet tests
      run: dotnet run -c Release --project BenchmarkProject

    - name: Check for regressions
      run: dotnet test -c Release --filter Category=Regression

    - name: Run NBomber load tests
      run: dotnet run -c Release --project LoadTestProject

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: |
          BenchmarkDotNet.Artifacts/**
          LoadTestResults/**

    - name: Comment PR
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: '## Performance Test Results\n\nSee artifacts for detailed results.'
          });
```

## Output Format

Please provide a comprehensive performance testing implementation with the following structure:

### Performance Test Summary

- **Benchmarks Implemented**: [count]

- **Load Tests Created**: [count]

- **Performance Baselines Established**: [yes/no]

- **Regression Detection Configured**: [yes/no]

- **Profiling Tools Set Up**: [list]

### Performance Requirements
| Metric | Target | Measured | Status |
|--------|--------|----------|--------|
| API response P95 | <200ms | [value] | ✅/❌ |
| Throughput | 100 RPS | [value] | ✅/❌ |
| Memory usage | <1GB | [value] | ✅/❌ |
| GC pause P99 | <50ms | [value] | ✅/❌ |

### Benchmark Results
```
Benchmark: DataProcessingBenchmark.LinqWhere
Mean: 45.23 ms
StdDev: 3.12 ms
Allocated: 85 KB
Gen 0: 15
```

### Load Test Results
```
Scenario: api_load_test
RPS: 87.3
Response Time P50: 124ms
Response Time P95: 287ms
Response Time P99: 445ms
Success Rate: 99.8%
```

### Bottlenecks Identified
1. **LINQ Query in UserService**

   - **Issue**: Multiple enumerations causing N iterations

   - **Impact**: 200ms average processing time

   - **Recommendation**: Use compiled query or AsNoTracking()

2. **JSON Serialization**

   - **Issue**: Reflection-based serialization overhead

   - **Impact**: 150ms for large responses

   - **Recommendation**: Use System.Text.Json source generators

### Performance Improvement Recommendations

- [ ] Optimize database queries (use AsNoTracking for read-only)

- [ ] Implement response caching with IMemoryCache

- [ ] Add pagination for large result sets

- [ ] Enable response compression middleware

- [ ] Use Span<T> and Memory<T> for buffer operations

### Test Execution
```bash
# Run BenchmarkDotNet
dotnet run -c Release --project BenchmarkProject

# Run NBomber load tests
dotnet run -c Release --project LoadTestProject

# Profile with dotnet-trace
dotnet-trace collect --process-id <PID>
```

### Next Steps

- [ ] Establish performance baselines for all critical operations

- [ ] Integrate performance tests into CI/CD pipeline

- [ ] Set up Application Insights for production monitoring

- [ ] Create performance dashboard with metrics

- [ ] Schedule regular performance review meetings

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

1. **Performance test suite** with BenchmarkDotNet and NBomber tests

2. **Performance baselines** documented

3. **Load test scenarios** for critical endpoints

4. **Profiling results** with bottleneck identification

5. **Regression detection** configuration

6. **CI/CD integration** for automated performance gates

7. **Performance report** with metrics and recommendations
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
