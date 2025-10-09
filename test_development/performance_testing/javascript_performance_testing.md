# JavaScript Performance Testing

## Objective
Implement comprehensive performance testing to validate system behavior under load, identify bottlenecks, measure response times, profile resource usage, detect performance regressions, and ensure scalability requirements are met using JavaScript/Node.js tooling.

## Output Directory Structure

All test outputs should be saved in organized directories:

```
tests/
└── performance_testing/
    ├── test_files/
    ├── test_data/
    ├── test_reports/
    └── test_configs/
```

**Directory Setup**:
- Create `tests/` directory in repository root if it doesn't exist
- Create `tests/performance_testing/` subdirectory for this testing phase
- All test files, data, reports, and configurations go in the phase-specific directory

**Expected Outputs**:
- `test_files/` - Actual test implementation files
- `test_data/` - Test fixtures, mock data, sample inputs
- `test_reports/` - Test execution reports, coverage reports, performance results
- `test_configs/` - Framework configurations, test runner settings

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
- [ ] Load testing tools configured (k6, autocannon)
- [ ] Benchmarking framework set up
- [ ] Performance test data prepared
- [ ] CI/CD integration planned
- [ ] Results storage and trending implemented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Performance Testing Implementation

Please implement comprehensive performance testing for this JavaScript/Node.js project following this protocol:

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
| WebSocket | 50 | 100 | 500 |

**Resource Limits**:
- **Memory**: <512MB per process
- **CPU**: <80% average, <95% peak
- **Event loop lag**: <10ms
- **Response size**: <1MB per request

## Phase 2: Benchmarking with Benchmark.js

### Setup Benchmark.js

```bash
npm install --save-dev benchmark microtime
```

### Basic Benchmarking

```javascript
/**
 * Performance benchmarks for critical functions.
 *
 * Uses Benchmark.js to measure execution time and detect regressions.
 */
const Benchmark = require('benchmark');
const suite = new Benchmark.Suite();

// Import functions to test
const { processData, searchUsers, transformData } = require('../src/lib');

suite
  .add('Array.prototype.map', () => {
    const data = Array.from({ length: 1000 }, (_, i) => i);
    data.map(x => x * 2);
  })
  .add('for loop', () => {
    const data = Array.from({ length: 1000 }, (_, i) => i);
    const result = [];
    for (let i = 0; i < data.length; i++) {
      result.push(data[i] * 2);
    }
  })
  .add('processData', () => {
    const data = generateTestData(1000);
    processData(data);
  })
  .on('cycle', (event) => {
    console.log(String(event.target));
  })
  .on('complete', function() {
    console.log('Fastest is ' + this.filter('fastest').map('name'));
  })
  .run({ async: true });
```

### Advanced Benchmarking

```javascript
const Benchmark = require('benchmark');
const { performance } = require('perf_hooks');

/**
 * Advanced benchmark with custom setup and teardown.
 */
class AdvancedBenchmark {
  constructor(name) {
    this.suite = new Benchmark.Suite(name);
    this.results = [];
  }

  addTest(name, fn, options = {}) {
    this.suite.add(name, fn, {
      setup: options.setup || (() => {}),
      teardown: options.teardown || (() => {}),
      onStart: () => {
        console.log(`Starting: ${name}`);
      },
      onCycle: (event) => {
        const bench = event.target;
        this.results.push({
          name: bench.name,
          hz: bench.hz,
          mean: bench.stats.mean * 1000, // ms
          deviation: bench.stats.deviation * 1000
        });
      }
    });
    return this;
  }

  run() {
    return new Promise((resolve) => {
      this.suite
        .on('complete', () => {
          this.printResults();
          resolve(this.results);
        })
        .run({ async: true });
    });
  }

  printResults() {
    console.log('\n=== Benchmark Results ===\n');
    this.results.forEach(result => {
      console.log(`${result.name}:`);
      console.log(`  Operations/sec: ${result.hz.toFixed(2)}`);
      console.log(`  Mean time: ${result.mean.toFixed(4)}ms`);
      console.log(`  Deviation: ±${result.deviation.toFixed(4)}ms`);
    });
  }
}

// Usage
const bench = new AdvancedBenchmark('Data Processing');

bench
  .addTest('JSON.parse', () => {
    JSON.parse('{"key": "value", "number": 123}');
  })
  .addTest('JSON.stringify', () => {
    JSON.stringify({ key: 'value', number: 123 });
  })
  .addTest('Array operations', () => {
    const arr = Array.from({ length: 1000 }, (_, i) => i);
    arr.filter(x => x % 2 === 0).map(x => x * 2);
  }, {
    setup: function() {
      // Setup code not included in timing
      this.testData = generateLargeDataset(10000);
    }
  })
  .run();
```

### Parametrized Benchmarking

```javascript
/**
 * Benchmark scaling characteristics with different data sizes.
 */
function benchmarkScaling() {
  const sizes = [100, 1000, 10000, 100000];
  const results = {};

  sizes.forEach(size => {
    const suite = new Benchmark.Suite(`Size: ${size}`);

    suite
      .add(`Process ${size} items`, () => {
        const data = Array.from({ length: size }, (_, i) => i);
        processData(data);
      })
      .on('complete', function() {
        const bench = this[0];
        results[size] = {
          hz: bench.hz,
          mean: bench.stats.mean * 1000
        };

        // Check if performance scales linearly
        const msPerItem = bench.stats.mean * 1000 / size;
        console.log(`${size} items: ${msPerItem.toFixed(6)}ms per item`);
      })
      .run();
  });

  return results;
}
```

## Phase 3: Load Testing with k6

### Setup k6

```bash
# Install k6 (see https://k6.io/docs/getting-started/installation/)
# Windows (Chocolatey): choco install k6
# macOS (Homebrew): brew install k6
# Linux: See k6 documentation
```

### Basic Load Test

```javascript
/**
 * k6 load test for API endpoints.
 *
 * Run with: k6 run tests/load/api-load-test.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Load test configuration
export const options = {
  stages: [
    { duration: '30s', target: 20 },  // Ramp up to 20 users
    { duration: '1m', target: 20 },   // Stay at 20 users
    { duration: '30s', target: 100 }, // Ramp up to 100 users
    { duration: '2m', target: 100 },  // Stay at 100 users
    { duration: '30s', target: 0 },   // Ramp down to 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'], // Error rate < 1%
    errors: ['rate<0.1'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';

export function setup() {
  // Setup code - runs once before test
  const loginRes = http.post(`${BASE_URL}/api/login`, JSON.stringify({
    username: 'testuser',
    password: 'testpass'
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  return { token: loginRes.json('token') };
}

export default function(data) {
  // Main test function - runs repeatedly
  const params = {
    headers: {
      'Authorization': `Bearer ${data.token}`,
      'Content-Type': 'application/json',
    },
  };

  // GET /api/users
  let res = http.get(`${BASE_URL}/api/users`, params);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  }) || errorRate.add(1);

  sleep(1);

  // POST /api/users
  res = http.post(`${BASE_URL}/api/users`, JSON.stringify({
    username: `user_${__VU}_${Date.now()}`,
    email: `user${__VU}@test.com`
  }), params);

  check(res, {
    'status is 201': (r) => r.status === 201,
    'response time < 400ms': (r) => r.timings.duration < 400,
  }) || errorRate.add(1);

  sleep(2);

  // GET /api/users/:id
  const userId = Math.floor(Math.random() * 1000) + 1;
  res = http.get(`${BASE_URL}/api/users/${userId}`, params);
  check(res, {
    'status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'response time < 150ms': (r) => r.timings.duration < 150,
  }) || errorRate.add(1);

  sleep(1);
}

export function teardown(data) {
  // Teardown code - runs once after test
  console.log('Load test complete');
}
```

### Advanced Load Test Patterns

```javascript
import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// Custom metrics
const customDuration = new Trend('custom_duration');
const failureCounter = new Counter('failures');

export const options = {
  scenarios: {
    // Constant load
    constant_load: {
      executor: 'constant-vus',
      vus: 50,
      duration: '2m',
      tags: { scenario: 'constant' },
    },
    // Ramping load
    ramping_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 100 },
        { duration: '3m', target: 100 },
        { duration: '1m', target: 0 },
      ],
      tags: { scenario: 'ramping' },
      startTime: '2m', // Start after constant_load
    },
    // Spike test
    spike_test: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      maxVUs: 200,
      stages: [
        { duration: '30s', target: 10 },
        { duration: '10s', target: 100 }, // Spike
        { duration: '30s', target: 10 },
      ],
      tags: { scenario: 'spike' },
      startTime: '6m',
    },
  },
  thresholds: {
    'http_req_duration{scenario:constant}': ['p(95)<300'],
    'http_req_duration{scenario:ramping}': ['p(95)<500'],
    'http_req_duration{scenario:spike}': ['p(95)<1000'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';

export default function() {
  group('User workflow', () => {
    // Register
    group('Register', () => {
      const username = `user_${__VU}_${Date.now()}`;
      const res = http.post(`${BASE_URL}/api/register`, JSON.stringify({
        username,
        email: `${username}@test.com`,
        password: 'testpass123'
      }), {
        headers: { 'Content-Type': 'application/json' },
      });

      const success = check(res, {
        'registration successful': (r) => r.status === 201,
      });

      if (!success) {
        failureCounter.add(1);
        return;
      }
    });

    sleep(1);

    // Login
    let token;
    group('Login', () => {
      const res = http.post(`${BASE_URL}/api/login`, JSON.stringify({
        username: `user_${__VU}_${Date.now()}`,
        password: 'testpass123'
      }), {
        headers: { 'Content-Type': 'application/json' },
      });

      const success = check(res, {
        'login successful': (r) => r.status === 200,
      });

      if (success) {
        token = res.json('token');
      } else {
        failureCounter.add(1);
      }
    });

    if (!token) return;

    sleep(1);

    // Perform actions
    group('Actions', () => {
      const params = {
        headers: { 'Authorization': `Bearer ${token}` },
      };

      // Measure custom duration
      const start = Date.now();
      const res = http.get(`${BASE_URL}/api/profile`, params);
      customDuration.add(Date.now() - start);

      check(res, {
        'profile retrieved': (r) => r.status === 200,
      });
    });

    sleep(1);
  });
}
```

## Phase 4: Load Testing with Autocannon

### Setup Autocannon

```bash
npm install --save-dev autocannon
```

### Basic Autocannon Load Test

```javascript
/**
 * Autocannon load test for Node.js HTTP servers.
 *
 * Run with: node tests/load/autocannon-test.js
 */
const autocannon = require('autocannon');

async function runLoadTest() {
  const result = await autocannon({
    url: 'http://localhost:3000/api/users',
    connections: 100,        // Concurrent connections
    pipelining: 10,          // Requests per connection
    duration: 30,            // Test duration in seconds
    method: 'GET',
    headers: {
      'Authorization': 'Bearer test-token'
    }
  });

  console.log('Load Test Results:');
  console.log(`Requests: ${result.requests.total}`);
  console.log(`Throughput: ${result.throughput.total} bytes`);
  console.log(`Duration: ${result.duration}s`);
  console.log(`Req/sec: ${result.requests.average}`);
  console.log(`Latency:`);
  console.log(`  Mean: ${result.latency.mean}ms`);
  console.log(`  P50: ${result.latency.p50}ms`);
  console.log(`  P95: ${result.latency.p95}ms`);
  console.log(`  P99: ${result.latency.p99}ms`);
  console.log(`Errors: ${result.errors}`);

  return result;
}

runLoadTest();
```

### Advanced Autocannon Tests

```javascript
const autocannon = require('autocannon');
const { performance } = require('perf_hooks');

class AutocannonRunner {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.results = [];
  }

  async runTest(config) {
    const defaultConfig = {
      url: this.baseUrl,
      connections: 100,
      duration: 30,
      timeout: 10,
    };

    const mergedConfig = { ...defaultConfig, ...config };

    console.log(`\nRunning: ${mergedConfig.title || 'Load Test'}`);
    const start = performance.now();

    const result = await autocannon(mergedConfig);

    const duration = performance.now() - start;

    const summary = {
      title: mergedConfig.title,
      duration: duration / 1000,
      requests: result.requests.total,
      rps: result.requests.average,
      latency: {
        mean: result.latency.mean,
        p50: result.latency.p50,
        p95: result.latency.p95,
        p99: result.latency.p99,
      },
      errors: result.errors,
      timeouts: result.timeouts,
    };

    this.results.push(summary);
    this.printSummary(summary);

    return result;
  }

  printSummary(summary) {
    console.log('\n=== Test Summary ===');
    console.log(`Title: ${summary.title}`);
    console.log(`Duration: ${summary.duration.toFixed(2)}s`);
    console.log(`Total Requests: ${summary.requests}`);
    console.log(`Req/sec: ${summary.rps.toFixed(2)}`);
    console.log(`Latency:`);
    console.log(`  Mean: ${summary.latency.mean.toFixed(2)}ms`);
    console.log(`  P50: ${summary.latency.p50}ms`);
    console.log(`  P95: ${summary.latency.p95}ms`);
    console.log(`  P99: ${summary.latency.p99}ms`);
    console.log(`Errors: ${summary.errors}`);
    console.log(`Timeouts: ${summary.timeouts}`);
  }

  printAllResults() {
    console.log('\n=== All Test Results ===\n');
    this.results.forEach((result, i) => {
      console.log(`${i + 1}. ${result.title}`);
      console.log(`   RPS: ${result.rps.toFixed(2)}, P95: ${result.latency.p95}ms`);
    });
  }
}

// Usage
async function main() {
  const runner = new AutocannonRunner('http://localhost:3000');

  // Test different endpoints
  await runner.runTest({
    title: 'GET /api/users',
    url: 'http://localhost:3000/api/users',
    connections: 50,
    duration: 30,
  });

  await runner.runTest({
    title: 'POST /api/users',
    url: 'http://localhost:3000/api/users',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: 'testuser',
      email: 'test@example.com'
    }),
    connections: 50,
    duration: 30,
  });

  runner.printAllResults();
}

main();
```

## Phase 5: Profiling with Clinic.js

### Setup Clinic.js

```bash
npm install --save-dev clinic
```

### CPU Profiling

```javascript
/**
 * Run with: clinic doctor -- node app.js
 *
 * Generates CPU and event loop analysis.
 */

// In your application code, add profiling hooks
const { performance, PerformanceObserver } = require('perf_hooks');

// Monitor slow operations
const obs = new PerformanceObserver((items) => {
  items.getEntries().forEach((entry) => {
    if (entry.duration > 100) { // Slower than 100ms
      console.warn(`Slow operation: ${entry.name} took ${entry.duration}ms`);
    }
  });
});
obs.observe({ entryTypes: ['measure'] });

// Measure specific operations
function expensiveOperation(data) {
  performance.mark('operation-start');

  // Your code here
  const result = processData(data);

  performance.mark('operation-end');
  performance.measure('expensive-operation', 'operation-start', 'operation-end');

  return result;
}
```

### Memory Profiling

```javascript
/**
 * Run with: clinic heapprofiler -- node app.js
 *
 * Generates memory allocation analysis.
 */

const v8 = require('v8');
const { writeHeapSnapshot } = v8;

// Take heap snapshot for analysis
function takeHeapSnapshot(label = 'snapshot') {
  const filename = `./heap-${label}-${Date.now()}.heapsnapshot`;
  writeHeapSnapshot(filename);
  console.log(`Heap snapshot written to ${filename}`);
}

// Monitor memory usage
function logMemoryUsage() {
  const usage = process.memoryUsage();
  console.log('Memory Usage:');
  console.log(`  RSS: ${(usage.rss / 1024 / 1024).toFixed(2)} MB`);
  console.log(`  Heap Total: ${(usage.heapTotal / 1024 / 1024).toFixed(2)} MB`);
  console.log(`  Heap Used: ${(usage.heapUsed / 1024 / 1024).toFixed(2)} MB`);
  console.log(`  External: ${(usage.external / 1024 / 1024).toFixed(2)} MB`);
}

// Check for memory leaks
function detectMemoryLeak() {
  const baseline = process.memoryUsage().heapUsed;

  // Perform operations
  for (let i = 0; i < 1000; i++) {
    performOperation();
  }

  global.gc && global.gc(); // Force garbage collection if --expose-gc

  const current = process.memoryUsage().heapUsed;
  const increase = current - baseline;

  console.log(`Memory increase: ${(increase / 1024 / 1024).toFixed(2)} MB`);

  if (increase > 50 * 1024 * 1024) { // 50MB threshold
    console.warn('Potential memory leak detected');
  }
}
```

### Event Loop Monitoring

```javascript
/**
 * Run with: clinic bubbleprof -- node app.js
 *
 * Visualizes async operations and event loop delays.
 */

const { monitorEventLoopDelay } = require('perf_hooks');

// Monitor event loop lag
const h = monitorEventLoopDelay({ resolution: 20 });
h.enable();

setInterval(() => {
  console.log('Event Loop Stats:');
  console.log(`  Min: ${(h.min / 1e6).toFixed(2)}ms`);
  console.log(`  Max: ${(h.max / 1e6).toFixed(2)}ms`);
  console.log(`  Mean: ${(h.mean / 1e6).toFixed(2)}ms`);
  console.log(`  P50: ${(h.percentile(50) / 1e6).toFixed(2)}ms`);
  console.log(`  P99: ${(h.percentile(99) / 1e6).toFixed(2)}ms`);

  if (h.percentile(99) > 10000000) { // 10ms
    console.warn('High event loop lag detected!');
  }
}, 10000);

process.on('exit', () => {
  h.disable();
});
```

## Phase 6: Performance Regression Detection

### Baseline Management

```javascript
/**
 * Performance regression testing with baseline comparison.
 */
const fs = require('fs');
const path = require('path');

const BASELINE_FILE = path.join(__dirname, 'performance-baseline.json');

class PerformanceBaseline {
  constructor() {
    this.baselines = this.load();
  }

  load() {
    if (fs.existsSync(BASELINE_FILE)) {
      return JSON.parse(fs.readFileSync(BASELINE_FILE, 'utf8'));
    }
    return {};
  }

  save() {
    fs.writeFileSync(BASELINE_FILE, JSON.stringify(this.baselines, null, 2));
  }

  set(name, metrics) {
    this.baselines[name] = {
      ...metrics,
      timestamp: new Date().toISOString()
    };
    this.save();
  }

  get(name) {
    return this.baselines[name];
  }

  compare(name, currentMetrics) {
    const baseline = this.get(name);

    if (!baseline) {
      console.log(`No baseline for ${name}, saving current as baseline`);
      this.set(name, currentMetrics);
      return { isRegression: false, isNewBaseline: true };
    }

    const regression = {};
    let hasRegression = false;

    Object.keys(currentMetrics).forEach(key => {
      if (typeof currentMetrics[key] === 'number' && baseline[key]) {
        const percentChange = ((currentMetrics[key] - baseline[key]) / baseline[key]) * 100;
        regression[key] = {
          baseline: baseline[key],
          current: currentMetrics[key],
          change: percentChange
        };

        if (percentChange > 10) { // 10% regression threshold
          hasRegression = true;
        }
      }
    });

    return { isRegression: hasRegression, regression, baseline };
  }

  printComparison(name, comparison) {
    console.log(`\n=== Performance Comparison: ${name} ===`);

    if (comparison.isNewBaseline) {
      console.log('New baseline created');
      return;
    }

    Object.entries(comparison.regression).forEach(([metric, data]) => {
      const symbol = data.change > 0 ? '↑' : '↓';
      const color = data.change > 10 ? '\x1b[31m' : '\x1b[32m'; // Red if regression

      console.log(`${metric}:`);
      console.log(`  Baseline: ${data.baseline.toFixed(2)}`);
      console.log(`  Current: ${data.current.toFixed(2)}`);
      console.log(`${color}  Change: ${symbol} ${Math.abs(data.change).toFixed(2)}%\x1b[0m`);
    });

    if (comparison.isRegression) {
      console.error('\n❌ Performance regression detected!');
    } else {
      console.log('\n✅ No performance regression');
    }
  }
}

module.exports = PerformanceBaseline;
```

### Integration Test

```javascript
const Benchmark = require('benchmark');
const PerformanceBaseline = require('./performance-baseline');

async function runRegressionTests() {
  const baseline = new PerformanceBaseline();

  const suite = new Benchmark.Suite();
  const results = {};

  suite
    .add('Data processing', () => {
      processData(generateTestData(1000));
    })
    .add('User search', () => {
      searchUsers(testUsers, 'test query');
    })
    .on('cycle', (event) => {
      const bench = event.target;
      results[bench.name] = {
        hz: bench.hz,
        mean: bench.stats.mean * 1000,
        deviation: bench.stats.deviation * 1000
      };
    })
    .on('complete', function() {
      // Compare each test with baseline
      Object.entries(results).forEach(([name, metrics]) => {
        const comparison = baseline.compare(name, metrics);
        baseline.printComparison(name, comparison);

        if (comparison.isRegression) {
          process.exit(1); // Fail CI build
        }
      });
    })
    .run({ async: true });
}

runRegressionTests();
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
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  performance:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Run benchmarks
      run: npm run benchmark

    - name: Check for regressions
      run: npm run benchmark:regression

    - name: Start application
      run: |
        npm start &
        sleep 10

    - name: Run load tests
      run: npm run load-test

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: |
          benchmark-results.json
          load-test-results.json

    - name: Comment PR
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const results = JSON.parse(fs.readFileSync('benchmark-results.json'));
          const comment = `## Performance Test Results\n\n${results.summary}`;
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });
```

### Package.json Scripts

```json
{
  "scripts": {
    "benchmark": "node tests/benchmarks/run-all.js",
    "benchmark:regression": "node tests/benchmarks/regression-test.js",
    "load-test": "k6 run tests/load/api-load-test.js",
    "load-test:autocannon": "node tests/load/autocannon-test.js",
    "profile:cpu": "clinic doctor -- node app.js",
    "profile:memory": "clinic heapprofiler -- node app.js",
    "profile:async": "clinic bubbleprof -- node app.js"
  }
}
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
| Event loop lag | <10ms | [value] | ✅/❌ |

### Benchmark Results
```
Function: processData
Operations/sec: 2,453 ops/sec
Mean: 0.4076ms
Std Dev: ±0.0234ms
Iterations: 24,530
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
1. **JSON Serialization in /api/users**
   - **Issue**: Large response payload
   - **Impact**: 150ms serialization time
   - **Recommendation**: Implement response streaming or pagination

2. **Database Connection Pool**
   - **Issue**: Connection pool exhaustion under load
   - **Impact**: Requests queuing, increased latency
   - **Recommendation**: Increase pool size or implement connection management

### Performance Improvement Recommendations
- [ ] Optimize JSON serialization (use faster-json-stringify)
- [ ] Implement response caching with Redis
- [ ] Add pagination for large result sets
- [ ] Enable gzip compression for API responses
- [ ] Optimize database connection pooling

### Test Execution
```bash
# Run benchmarks
npm run benchmark

# Run load tests
k6 run tests/load/api-load-test.js
npm run load-test:autocannon

# Profile application
npm run profile:cpu
npm run profile:memory
```

### Next Steps
- [ ] Establish performance baselines for all critical paths
- [ ] Integrate performance tests into CI/CD pipeline
- [ ] Set up performance monitoring in production
- [ ] Create performance dashboard with historical trends
- [ ] Schedule regular performance reviews
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
