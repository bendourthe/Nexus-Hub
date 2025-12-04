# Performance Testing

## Purpose
Establish comprehensive performance testing practices to validate system behavior under load, identify bottlenecks, measure response times, profile resource usage, and ensure scalability requirements are met.

## What This Review Covers

### Performance Test Types

- Load testing (normal and peak loads)

- Stress testing (beyond capacity)

- Spike testing (sudden load increases)

- Endurance testing (sustained load)

- Scalability testing (growth patterns)

### Performance Metrics

- Response time and latency

- Throughput and requests per second

- Resource utilization (CPU, memory, I/O)

- Concurrency and parallelism

- Error rates under load

### Benchmarking

- Baseline performance measurement

- Performance regression detection

- Comparative benchmarking

- Profiling and bottleneck identification

- Optimization validation

### Tools and Frameworks

- pytest-benchmark for microbenchmarks

- locust for load testing

- Apache JMeter alternatives

- Memory profiling tools

- Performance monitoring integration

## When to Use This Template

- Validating performance requirements

- Testing API/service scalability

- Identifying performance bottlenecks

- Preventing performance regressions

- Capacity planning

- Optimizing critical paths

## Related Templates

- **Test Cases**: Functional testing

- **CI/CD Integration**: Automated performance gates

- **Code Coverage**: Ensuring critical paths are tested

- **Production Monitoring**: Real-world validation

- **Reward Hacking**: Validates performance test effectiveness

## Expected Outcomes

- Established performance baselines

- Load testing infrastructure

- Performance regression detection

- Bottleneck identification

- Scalability validation

- Resource utilization insights

## Available Templates

| Language | Template File |
|----------|---------------|
| **Python** | [python_performance_testing.md](python_performance_testing.md) |
| **JavaScript/TypeScript** | [javascript_performance_testing.md](javascript_performance_testing.md) |
| **Java** | [java_performance_testing.md](java_performance_testing.md) |
| **C#** | [csharp_performance_testing.md](csharp_performance_testing.md) |
| **Go** | [go_performance_testing.md](go_performance_testing.md) |
| **C** | [c_performance_testing.md](c_performance_testing.md) |
| **C++** | [cpp_performance_testing.md](cpp_performance_testing.md) |

## Quick Start
Use the appropriate template file with your AI assistant to:
1. Design performance test strategy
2. Implement load and stress tests
3. Set up benchmarking infrastructure
4. Configure performance regression detection
5. Profile and optimize critical paths
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
