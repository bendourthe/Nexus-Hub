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

## Expected Outcomes
- Established performance baselines
- Load testing infrastructure
- Performance regression detection
- Bottleneck identification
- Scalability validation
- Resource utilization insights

## Quick Start
Use `python_performance_testing.md` with your AI assistant to:
1. Design performance test strategy
2. Implement load and stress tests
3. Set up benchmarking infrastructure
4. Configure performance regression detection
5. Profile and optimize critical paths
