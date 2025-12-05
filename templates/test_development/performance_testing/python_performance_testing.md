---
template_id: python_performance_testing
template_name: Performance Testing - Python
version: 1.0.0
last_updated: 2025-12-03
language: Python
category: test_development
phase: performance_testing
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:

  - test_development/mocks_fixtures/python_mocks_fixtures.md
related_templates:

  - test_development/code_coverage/python_code_coverage.md
tools:

  - pytest (8.3.4+)

  - black (24.12.0)

  - mypy (1.13.0)

  - ruff
tags:

  - test-development

  - testing

  - performance

  - python
---
# Python Performance Testing

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
Implement comprehensive performance testing to validate system behavior under load, identify bottlenecks, measure response times, profile resource usage, detect performance regressions, and ensure scalability requirements are met.

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

- [ ] Baseline benchmarks established

- [ ] Performance regression tests configured

- [ ] Resource profiling set up

### Metrics and Monitoring

- [ ] Response time thresholds defined

- [ ] Throughput targets established

- [ ] Resource usage limits set

- [ ] Error rate thresholds configured

- [ ] Performance reports automated

### Test Infrastructure

- [ ] Load testing tools configured

- [ ] Benchmarking framework set up

- [ ] Performance test data prepared

- [ ] CI/CD integration planned

- [ ] Results storage and trending implemented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Performance Testing Implementation

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

Please implement comprehensive performance testing for this Python project following this protocol:

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

**Throughput Requirements**:
| Operation | Target RPS | Peak RPS | Concurrent Users |
|-----------|------------|----------|------------------|
| API endpoint | 100 | 500 | 1000 |
| Background job | 50 | 100 | N/A |

**Resource Limits**:

- **Memory**: <512MB per process

- **CPU**: <80% average, <95% peak

- **Database connections**: <50 concurrent

- **Response size**: <1MB per request

## Phase 2: Benchmarking with pytest-benchmark

### Setup pytest-benchmark

```bash
pip install pytest-benchmark
```

### Basic Benchmarking

```python
"""
Performance benchmarks for critical functions.

Uses pytest-benchmark to measure execution time and detect regressions.
"""
import pytest

def test_benchmark_user_search(benchmark):
    """Benchmark user search operation."""
    # Setup
    users = create_test_users(1000)

    # Benchmark the function
    result = benchmark(search_users, users, query="alice")

    # Validate result
    assert len(result) > 0

def test_benchmark_data_processing(benchmark):
    """Benchmark data processing pipeline."""
    data = generate_test_data(10000)

    result = benchmark(process_data, data)

    assert result.is_valid()
```

### Advanced Benchmarking

```python
def test_benchmark_with_setup(benchmark):
    """Benchmark with separate setup phase."""
    def setup():
        """Setup not included in timing."""
        return create_large_dataset(10000)

    def process_dataset(data):
        """Function to benchmark."""
        return transform_and_aggregate(data)

    # Setup runs once, only process_dataset is timed
    result = benchmark.pedantic(
        process_dataset,
        setup=setup,
        rounds=10,
        iterations=5,
        warmup_rounds=2
    )

    assert result.is_valid()

def test_benchmark_parametrized(benchmark, data_size):
    """Benchmark with different data sizes."""
    data = generate_data(data_size)

    result = benchmark(process_data, data)

    assert result is not None

# Parametrize to test different scales
@pytest.mark.parametrize("data_size", [100, 1000, 10000])
def test_scaling_benchmark(benchmark, data_size):
    """Benchmark scaling characteristics."""
    data = generate_data(data_size)

    result = benchmark(process_data, data)

    # Verify performance scales linearly
    assert benchmark.stats.mean < data_size * 0.001  # <1ms per item
```

### Benchmark Configuration

```ini
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
addopts = --benchmark-only
markers =
    benchmark: Performance benchmark tests

[tool.benchmark]
# Minimum rounds for statistical significance
min_rounds = 5
# Minimum time to run benchmark
min_time = 0.000005
# Maximum time for a single benchmark
max_time = 1.0
# Calibration precision
calibration_precision = 10
# Save results for comparison
save = True
autosave = True
```

### Running Benchmarks

```bash
# Run all benchmarks
pytest tests/benchmarks/ --benchmark-only

# Compare with previous results
pytest tests/benchmarks/ --benchmark-compare=0001

# Generate histogram
pytest tests/benchmarks/ --benchmark-histogram

# Save baseline
pytest tests/benchmarks/ --benchmark-save=baseline

# Fail if slower than baseline
pytest tests/benchmarks/ --benchmark-compare=baseline --benchmark-compare-fail=mean:10%
```

## Phase 3: Load Testing with Locust

### Setup Locust

```bash
pip install locust
```

### Basic Load Test

```python
"""
Load tests for API endpoints using Locust.

Run with: locust -f tests/load/test_api_load.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between

class APIUser(HttpUser):
    """Simulated user for API load testing."""

    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)

    def on_start(self):
        """Called when user starts - login/setup."""
        response = self.client.post("/api/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        self.token = response.json()["token"]

    @task(3)  # Weight: 3x more common than other tasks
    def get_users(self):
        """GET /api/users endpoint."""
        self.client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/users"
        )

    @task(1)
    def create_user(self):
        """POST /api/users endpoint."""
        self.client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "username": f"user_{self.environment.runner.user_count}",
                "email": f"user{self.environment.runner.user_count}@test.com"
            },
            name="/api/users"
        )

    @task(2)
    def get_user_detail(self):
        """GET /api/users/{id} endpoint."""
        user_id = random.randint(1, 1000)
        self.client.get(
            f"/api/users/{user_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/users/{id}"
        )
```

### Advanced Load Test Patterns

```python
from locust import HttpUser, task, between, events
import logging

class AdvancedAPIUser(HttpUser):
    """Advanced load testing with custom logic."""

    wait_time = between(1, 5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None

    @task
    def user_workflow(self):
        """Complete user workflow: register -> login -> action -> logout."""
        # Register
        username = f"user_{self.environment.runner.user_count}"
        response = self.client.post("/api/register", json={
            "username": username,
            "email": f"{username}@test.com"
        })

        if response.status_code == 201:
            self.user_id = response.json()["id"]

            # Login
            login_response = self.client.post("/api/login", json={
                "username": username,
                "password": "testpass"
            })

            if login_response.status_code == 200:
                token = login_response.json()["token"]

                # Perform actions
                self.client.get(
                    f"/api/users/{self.user_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )

                # Logout
                self.client.post(
                    "/api/logout",
                    headers={"Authorization": f"Bearer {token}"}
                )

    @events.test_start.add_listener
    def on_test_start(environment, **kwargs):
        """Called when load test starts."""
        logging.info("Load test starting...")

    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs):
        """Called when load test stops."""
        logging.info("Load test complete.")
        logging.info(f"Total requests: {environment.stats.total.num_requests}")
        logging.info(f"Total failures: {environment.stats.total.num_failures}")
```

### Running Load Tests

```bash
# Web UI mode
locust -f tests/load/test_api_load.py --host=http://localhost:8000

# Headless mode with specific parameters
locust -f tests/load/test_api_load.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless

# Generate HTML report
locust -f tests/load/test_api_load.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless \
    --html=report.html
```

## Phase 4: Stress Testing

### Stress Test Implementation

```python
"""
Stress tests to find breaking points.

Tests system behavior beyond normal capacity.
"""
from locust import HttpUser, task, constant_pacing

class StressTestUser(HttpUser):
    """High-load user for stress testing."""

    # No wait time - constant hammering
    wait_time = constant_pacing(0.1)  # 10 requests/second per user

    @task
    def stress_endpoint(self):
        """Stress test critical endpoint."""
        response = self.client.get("/api/expensive-operation")

        # Track when system starts failing
        if response.status_code != 200:
            logging.warning(
                f"Failure at {self.environment.runner.user_count} users: "
                f"{response.status_code}"
            )

# Run with increasing load until failure
# locust -f stress_test.py --host=http://localhost:8000 --users 1000 --spawn-rate 100
```

### Memory Stress Test

```python
import pytest
import psutil
import os

def test_memory_usage_under_load():
    """Test memory doesn't leak under repeated operations."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Perform many operations
    for i in range(1000):
        result = perform_operation(large_data=True)
        del result

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    # Assert memory didn't increase significantly
    assert memory_increase < 100, f"Memory leak detected: {memory_increase}MB increase"
```

## Phase 5: Response Time Testing

### Response Time Benchmarks

```python
import time
import statistics
import pytest

def test_response_time_p95():
    """Test that 95th percentile response time is acceptable."""
    response_times = []

    # Collect response times
    for _ in range(100):
        start = time.perf_counter()
        result = api_call()
        elapsed = time.perf_counter() - start
        response_times.append(elapsed * 1000)  # Convert to ms

    # Calculate percentiles
    p50 = statistics.median(response_times)
    p95 = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
    p99 = statistics.quantiles(response_times, n=100)[98]  # 99th percentile

    print(f"Response times - P50: {p50:.2f}ms, P95: {p95:.2f}ms, P99: {p99:.2f}ms")

    # Assert against requirements
    assert p50 < 100, f"P50 too high: {p50:.2f}ms"
    assert p95 < 200, f"P95 too high: {p95:.2f}ms"
    assert p99 < 500, f"P99 too high: {p99:.2f}ms"

@pytest.mark.parametrize("concurrency", [1, 10, 50, 100])
def test_response_time_under_concurrency(concurrency):
    """Test response time with varying concurrency."""
    import concurrent.futures
    import time

    start = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(api_call) for _ in range(concurrency)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    elapsed = time.perf_counter() - start
    avg_response_time = (elapsed / concurrency) * 1000

    print(f"Concurrency {concurrency}: {avg_response_time:.2f}ms average")

    # Response time shouldn't degrade significantly
    assert avg_response_time < 200, f"Response time degraded: {avg_response_time:.2f}ms"
```

## Phase 6: Profiling and Optimization

### CPU Profiling

```python
import cProfile
import pstats
from pstats import SortKey

def test_profile_slow_function():
    """Profile function to identify bottlenecks."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Run function to profile
    result = slow_function(large_data)

    profiler.disable()

    # Print profiling results
    stats = pstats.Stats(profiler)
    stats.sort_stats(SortKey.CUMULATIVE)
    stats.print_stats(20)  # Top 20 functions

    # Can also save to file
    stats.dump_stats("profile_results.prof")

# Using line_profiler for line-by-line profiling
# pip install line_profiler
# kernprof -l -v test_performance.py

@profile  # Decorator from line_profiler
def detailed_profile_function():
    """Line-by-line profiling."""
    data = load_data()
    processed = process_data(data)
    result = aggregate_data(processed)
    return result
```

### Memory Profiling

```python
# Using memory_profiler
# pip install memory_profiler

from memory_profiler import profile

@profile
def test_memory_usage():
    """Profile memory usage line-by-line."""
    data = load_large_dataset()
    processed = transform_data(data)
    result = aggregate_results(processed)
    return result

# Using tracemalloc (standard library)
import tracemalloc
import pytest

def test_memory_allocation():
    """Track memory allocations."""
    tracemalloc.start()

    # Perform operations
    result = perform_memory_intensive_operation()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Current memory: {current / 1024 / 1024:.2f}MB")
    print(f"Peak memory: {peak / 1024 / 1024:.2f}MB")

    # Assert memory usage is acceptable
    assert peak < 500 * 1024 * 1024, f"Peak memory too high: {peak / 1024 / 1024:.2f}MB"
```

### Query Performance Testing

```python
import pytest
import time

def test_database_query_performance(database):
    """Test database query performance."""
    # Warm up cache
    database.query("SELECT * FROM users WHERE id = 1")

    # Time multiple queries
    query_times = []
    for user_id in range(1, 101):
        start = time.perf_counter()
        result = database.query(f"SELECT * FROM users WHERE id = {user_id}")
        elapsed = time.perf_counter() - start
        query_times.append(elapsed * 1000)

    avg_time = sum(query_times) / len(query_times)
    max_time = max(query_times)

    print(f"Query performance - Avg: {avg_time:.2f}ms, Max: {max_time:.2f}ms")

    assert avg_time < 50, f"Average query too slow: {avg_time:.2f}ms"
    assert max_time < 100, f"Worst query too slow: {max_time:.2f}ms"
```

## Phase 7: Performance Regression Detection

### Setup Performance Baseline

```python
"""
Performance regression tests.

Compares current performance against baseline.
"""
import pytest
import json
from pathlib import Path

BASELINE_FILE = Path("tests/performance/baseline.json")

def save_baseline(name, metrics):
    """Save performance baseline."""
    baselines = {}
    if BASELINE_FILE.exists():
        baselines = json.loads(BASELINE_FILE.read_text())

    baselines[name] = metrics
    BASELINE_FILE.write_text(json.dumps(baselines, indent=2))

def load_baseline(name):
    """Load performance baseline."""
    if not BASELINE_FILE.exists():
        return None

    baselines = json.loads(BASELINE_FILE.read_text())
    return baselines.get(name)

def test_performance_regression(benchmark):
    """Test for performance regression."""
    # Run benchmark
    result = benchmark(function_to_test, test_data)

    # Get current performance
    current_time = benchmark.stats.mean

    # Compare with baseline
    baseline = load_baseline("function_to_test")

    if baseline is None:
        # First run - save as baseline
        save_baseline("function_to_test", {"mean": current_time})
        pytest.skip("Baseline saved, re-run to test regression")
    else:
        baseline_time = baseline["mean"]
        regression = ((current_time - baseline_time) / baseline_time) * 100

        print(f"Baseline: {baseline_time:.6f}s, Current: {current_time:.6f}s")
        print(f"Regression: {regression:+.2f}%")

        # Fail if more than 10% slower
        assert regression < 10, f"Performance regression: {regression:+.2f}%"
```

### CI/CD Integration

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  pull_request:
    branches: [ main ]

jobs:
  performance:
    runs-on: ubuntu-latest

    steps:

    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.11

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest-benchmark locust

    - name: Run benchmarks
      run: |
        pytest tests/benchmarks/ --benchmark-only --benchmark-json=benchmark.json

    - name: Check for regression
      run: |
        pytest tests/benchmarks/ --benchmark-compare=baseline --benchmark-compare-fail=mean:10%

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: benchmark.json
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
| Memory usage | <512MB | [value] | ✅/❌ |
| Database query | <50ms | [value] | ✅/❌ |

### Benchmark Results
```
Function: process_data
Mean: 45.23ms
Std Dev: 3.12ms
Min: 41.05ms
Max: 52.18ms
Iterations: 100
```

### Load Test Results
```
Endpoint: POST /api/users
Users: 100
RPS: 87.3
Response Time P50: 124ms
Response Time P95: 287ms
Response Time P99: 445ms
Failures: 0.2%
```

### Bottlenecks Identified
1. **Database Query in user_search()**

   - **Issue**: N+1 query problem

   - **Impact**: 200ms average response time

   - **Recommendation**: Implement query optimization

2. **JSON Serialization**

   - **Issue**: Large response payload

   - **Impact**: 150ms serialization time

   - **Recommendation**: Use faster serializer or pagination

### Performance Improvement Recommendations

- [ ] Optimize database queries (add indexes)

- [ ] Implement caching for frequent reads

- [ ] Add pagination for large result sets

- [ ] Enable compression for API responses

- [ ] Implement connection pooling

### Test Execution
```bash
# Run benchmarks
pytest tests/benchmarks/ --benchmark-only

# Run load tests
locust -f tests/load/test_api.py --users 100 --run-time 5m

# Profile specific function
python -m cProfile -o profile.stats test_slow_function.py
```

### Next Steps

- [ ] Establish performance baselines for all critical paths

- [ ] Integrate performance tests into CI/CD pipeline

- [ ] Set up performance monitoring in production

- [ ] Create performance dashboard

- [ ] Schedule regular performance reviews

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

1. **Performance test suite** with benchmarks and load tests

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
