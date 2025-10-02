# Phase 4: Performance & Load Testing

## Objective
Implement comprehensive performance testing to validate system speed, throughput, scalability, and resource usage.

## Performance Testing Checklist

### Performance Test Categories
- [ ] Response time testing (latency)
- [ ] Throughput testing (operations per second)
- [ ] Load testing (normal operational capacity)
- [ ] Stress testing (beyond normal capacity)
- [ ] Endurance testing (sustained load over time)
- [ ] Spike testing (sudden load increases)
- [ ] Scalability testing (growing data volumes)
- [ ] Resource usage testing (CPU, memory, I/O)

### Performance Metrics
- [ ] Average response time
- [ ] 95th percentile response time
- [ ] 99th percentile response time
- [ ] Maximum response time
- [ ] Throughput (requests/operations per second)
- [ ] CPU usage percentage
- [ ] Memory usage (peak and average)
- [ ] Disk I/O operations
- [ ] Network bandwidth usage
- [ ] Database query execution time

### Test Data Sets
- [ ] Small dataset (10-100 items)
- [ ] Medium dataset (1,000-10,000 items)
- [ ] Large dataset (100,000-1,000,000 items)
- [ ] Very large dataset (>1,000,000 items)
- [ ] Complex nested data structures
- [ ] Realistic production-like data

### Performance Baselines
- [ ] Baseline metrics established
- [ ] Performance targets defined
- [ ] Acceptable degradation thresholds
- [ ] Regression detection enabled
- [ ] Historical performance tracking

## Detailed Performance Testing Prompt

```
Please help me implement comprehensive performance and load testing for my application.

**Performance Context:**
- Expected load: [USERS/REQUESTS]
- Performance requirements: [LATENCY/THROUGHPUT]
- Resource constraints: [CPU/MEMORY/BANDWIDTH]
- Scaling requirements: [HORIZONTAL/VERTICAL]
- Critical operations: [LIST]

**Performance Test Implementation:**

### 1. Response Time Testing

```python
@timeout(300)
def test_06_response_time(self) -> None:
    """TEST 6: Response time measurement."""
    test_name = "Response Time Test"
    description = "Measures operation latency under normal conditions"
    timer = PerformanceTimer()
    timer.start()
    
    try:
        import numpy as np
        
        # Number of iterations
        iterations = 1000
        response_times = []
        
        # Prepare test data
        test_inputs = [
            {'id': i, 'data': f'test_{i}'}
            for i in range(iterations)
        ]
        
        # Measure individual response times
        for test_input in test_inputs:
            start = time.time()
            result = self.component.process(test_input)
            end = time.time()
            response_times.append((end - start) * 1000)  # Convert to ms
        
        elapsed = timer.stop()
        
        # Calculate statistics
        avg_response = np.mean(response_times)
        median_response = np.median(response_times)
        p95_response = np.percentile(response_times, 95)
        p99_response = np.percentile(response_times, 99)
        max_response = np.max(response_times)
        min_response = np.min(response_times)
        std_dev = np.std(response_times)
        
        metrics = {
            "Iterations": str(iterations),
            "Avg Response Time": f"{avg_response:.2f}ms",
            "Median Response": f"{median_response:.2f}ms",
            "95th Percentile": f"{p95_response:.2f}ms",
            "99th Percentile": f"{p99_response:.2f}ms",
            "Max Response": f"{max_response:.2f}ms",
            "Min Response": f"{min_response:.2f}ms",
            "Std Deviation": f"{std_dev:.2f}ms",
            "Total Time": f"{elapsed:.3f}s"
        }
        
        criteria = get_pass_criteria('response_time')
        passed = (
            avg_response <= criteria['max_avg_ms']
            and p95_response <= criteria['max_p95_ms']
            and p99_response <= criteria['max_p99_ms']
        )
        result_text = (
            f"Avg: {avg_response:.2f}ms, P95: {p95_response:.2f}ms, "
            f"P99: {p99_response:.2f}ms"
        )
        
        print(format_console_output(
            6, test_name, description, metrics, result_text, passed
        ))
        self.aggregator.add_result(
            test_name, "✅" if passed else "❌",
            f"{elapsed:.3f}s", metrics, passed
        )
        self.assertTrue(passed, result_text)
        
    except Exception as e:
        self._handle_test_exception(test_name, description, e, timer)
```

### 2. Throughput Testing

```python
@timeout(300)
def test_07_throughput(self) -> None:
    """TEST 7: Throughput measurement."""
    test_name = "Throughput Test"
    description = "Measures operations per second under sustained load"
    timer = PerformanceTimer()
    timer.start()
    
    try:
        # Test duration in seconds
        test_duration = 60
        operations_completed = 0
        errors = 0
        
        # Generate test data
        test_data_generator = self._create_data_generator()
        
        # Run for specified duration
        start_time = time.time()
        while (time.time() - start_time) < test_duration:
            try:
                test_input = next(test_data_generator)
                result = self.component.process(test_input)
                if result:
                    operations_completed += 1
            except Exception:
                errors += 1
        
        actual_duration = time.time() - start_time
        elapsed = timer.stop()
        
        # Calculate metrics
        throughput = operations_completed / actual_duration
        error_rate = (errors / (operations_completed + errors)) * 100
        
        metrics = {
            "Test Duration": f"{actual_duration:.2f}s",
            "Operations Completed": str(operations_completed),
            "Errors": str(errors),
            "Throughput": f"{throughput:.2f} ops/s",
            "Error Rate": f"{error_rate:.2f}%",
            "Avg Operation Time": f"{(actual_duration/operations_completed)*1000:.2f}ms"
        }
        
        criteria = get_pass_criteria('throughput')
        passed = (
            throughput >= criteria['min_ops_per_second']
            and error_rate <= criteria['max_error_rate_percent']
        )
        result_text = (
            f"Achieved {throughput:.2f} ops/s "
            f"(target: >={criteria['min_ops_per_second']} ops/s)"
        )
        
        print(format_console_output(
            7, test_name, description, metrics, result_text, passed
        ))
        self.aggregator.add_result(
            test_name, "✅" if passed else "❌",
            f"{elapsed:.3f}s", metrics, passed
        )
        self.assertTrue(passed, result_text)
        
    except Exception as e:
        self._handle_test_exception(test_name, description, e, timer)
```

### 3. Load Testing

```python
@timeout(600)
def test_08_load_handling(self) -> None:
    """TEST 8: Load handling under concurrent requests."""
    test_name = "Load Test"
    description = "Tests system behavior under normal operational load"
    timer = PerformanceTimer()
    timer.start()
    
    try:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Simulate concurrent users/requests
        concurrent_users = 50
        requests_per_user = 20
        total_requests = concurrent_users * requests_per_user
        
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        def simulate_user_request(user_id: int, request_num: int):
            """Simulate single user request."""
            start = time.time()
            try:
                test_input = {
                    'user_id': user_id,
                    'request': request_num,
                    'data': f'user_{user_id}_req_{request_num}'
                }
                result = self.component.process(test_input)
                elapsed_ms = (time.time() - start) * 1000
                return {'success': True, 'time': elapsed_ms}
            except Exception as e:
                elapsed_ms = (time.time() - start) * 1000
                return {'success': False, 'time': elapsed_ms, 'error': str(e)}
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for user_id in range(concurrent_users):
                for request_num in range(requests_per_user):
                    future = executor.submit(
                        simulate_user_request, user_id, request_num
                    )
                    futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                result = future.result()
                response_times.append(result['time'])
                if result['success']:
                    successful_requests += 1
                else:
                    failed_requests += 1
        
        elapsed = timer.stop()
        
        # Calculate statistics
        import numpy as np
        avg_response = np.mean(response_times)
        p95_response = np.percentile(response_times, 95)
        max_response = np.max(response_times)
        success_rate = (successful_requests / total_requests) * 100
        throughput = total_requests / elapsed
        
        metrics = {
            "Concurrent Users": str(concurrent_users),
            "Total Requests": str(total_requests),
            "Successful": str(successful_requests),
            "Failed": str(failed_requests),
            "Success Rate": f"{success_rate:.2f}%",
            "Avg Response": f"{avg_response:.2f}ms",
            "P95 Response": f"{p95_response:.2f}ms",
            "Max Response": f"{max_response:.2f}ms",
            "Throughput": f"{throughput:.2f} req/s",
            "Test Duration": f"{elapsed:.3f}s"
        }
        
        criteria = get_pass_criteria('load_test')
        passed = (
            success_rate >= criteria['min_success_rate_percent']
            and p95_response <= criteria['max_p95_response_ms']
            and throughput >= criteria['min_throughput']
        )
        result_text = (
            f"{success_rate:.1f}% success rate with {concurrent_users} "
            f"concurrent users ({throughput:.1f} req/s)"
        )
        
        print(format_console_output(
            8, test_name, description, metrics, result_text, passed
        ))
        self.aggregator.add_result(
            test_name, "✅" if passed else "❌",
            f"{elapsed:.3f}s", metrics, passed
        )
        self.assertTrue(passed, result_text)
        
    except Exception as e:
        self._handle_test_exception(test_name, description, e, timer)
```

### 4. Stress Testing

```python
@timeout(600)
def test_09_stress_limits(self) -> None:
    """TEST 9: Stress testing to find breaking points."""
    test_name = "Stress Test"
    description = "Identifies system limits by progressively increasing load"
    timer = PerformanceTimer()
    timer.start()
    
    try:
        import psutil
        
        # Progressively increase load until failure
        load_levels = [10, 50, 100, 200, 500, 1000]
        breaking_point = None
        results_by_load = []
        
        for load_size in load_levels:
            # Generate dataset
            dataset = self._generate_large_dataset(size=load_size)
            
            # Measure resource usage before
            process = psutil.Process()
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
            cpu_before = process.cpu_percent(interval=1)
            
            # Process dataset
            start = time.time()
            try:
                successful = 0
                for item in dataset:
                    result = self.component.process(item)
                    if result:
                        successful += 1
                
                process_time = time.time() - start
                
                # Measure resource usage after
                mem_after = process.memory_info().rss / 1024 / 1024  # MB
                cpu_after = process.cpu_percent(interval=1)
                
                results_by_load.append({
                    'load': load_size,
                    'success': True,
                    'processed': successful,
                    'time': process_time,
                    'throughput': load_size / process_time,
                    'memory_delta': mem_after - mem_before,
                    'memory_total': mem_after,
                    'cpu_usage': cpu_after
                })
                
            except Exception as e:
                breaking_point = load_size
                results_by_load.append({
                    'load': load_size,
                    'success': False,
                    'error': str(e)
                })
                break
        
        elapsed = timer.stop()
        
        # Analyze results
        max_successful_load = max(
            (r['load'] for r in results_by_load if r.get('success')),
            default=0
        )
        peak_throughput = max(
            (r['throughput'] for r in results_by_load if r.get('success')),
            default=0
        )
        peak_memory = max(
            (r['memory_total'] for r in results_by_load if r.get('success')),
            default=0
        )
        
        metrics = {
            "Load Levels Tested": str(len(results_by_load)),
            "Max Successful Load": str(max_successful_load),
            "Breaking Point": str(breaking_point) if breaking_point else "Not reached",
            "Peak Throughput": f"{peak_throughput:.2f} items/s",
            "Peak Memory": f"{peak_memory:.2f} MB",
            "Test Duration": f"{elapsed:.3f}s"
        }
        
        # Add per-level details
        for i, result in enumerate(results_by_load[:5]):  # First 5 levels
            if result.get('success'):
                metrics[f"Load {result['load']}"] = (
                    f"{result['throughput']:.1f} items/s, "
                    f"{result['memory_total']:.1f} MB"
                )
        
        criteria = get_pass_criteria('stress_test')
        passed = (
            max_successful_load >= criteria['min_load_capacity']
            and peak_memory <= criteria['max_memory_mb']
        )
        result_text = (
            f"Handled load up to {max_successful_load} items "
            f"(requirement: >={criteria['min_load_capacity']})"
        )
        
        print(format_console_output(
            9, test_name, description, metrics, result_text, passed
        ))
        self.aggregator.add_result(
            test_name, "✅" if passed else "❌",
            f"{elapsed:.3f}s", metrics, passed
        )
        self.assertTrue(passed, result_text)
        
    except Exception as e:
        self._handle_test_exception(test_name, description, e, timer)
```

### 5. Memory Profiling

```python
@timeout(300)
def test_10_memory_usage(self) -> None:
    """TEST 10: Memory usage profiling."""
    test_name = "Memory Profiling Test"
    description = "Monitors memory consumption and checks for leaks"
    timer = PerformanceTimer()
    timer.start()
    
    try:
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Force garbage collection before test
        gc.collect()
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run operations multiple times
        iterations = 100
        memory_samples = [baseline_memory]
        
        for i in range(iterations):
            # Process data
            dataset = self._generate_large_dataset(size=100)
            for item in dataset:
                result = self.component.process(item)
            
            # Sample memory every 10 iterations
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
        
        # Force garbage collection after test
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_samples.append(final_memory)
        
        elapsed = timer.stop()
        
        # Analyze memory usage
        peak_memory = max(memory_samples)
        avg_memory = sum(memory_samples) / len(memory_samples)
        memory_growth = final_memory - baseline_memory
        memory_leaked = memory_growth > (baseline_memory * 0.10)  # >10% growth
        
        metrics = {
            "Baseline Memory": f"{baseline_memory:.2f} MB",
            "Peak Memory": f"{peak_memory:.2f} MB",
            "Final Memory": f"{final_memory:.2f} MB",
            "Average Memory": f"{avg_memory:.2f} MB",
            "Memory Growth": f"{memory_growth:.2f} MB",
            "Growth Rate": f"{(memory_growth/baseline_memory)*100:.1f}%",
            "Iterations": str(iterations),
            "Memory Leak": "Detected" if memory_leaked else "None",
            "Test Duration": f"{elapsed:.3f}s"
        }
        
        criteria = get_pass_criteria('memory_profiling')
        passed = (
            peak_memory <= criteria['max_peak_memory_mb']
            and not memory_leaked
            and memory_growth <= criteria['max_growth_mb']
        )
        result_text = (
            f"Peak: {peak_memory:.1f}MB, Growth: {memory_growth:.1f}MB, "
            f"Leak: {'Yes' if memory_leaked else 'No'}"
        )
        
        print(format_console_output(
            10, test_name, description, metrics, result_text, passed
        ))
        self.aggregator.add_result(
            test_name, "✅" if passed else "❌",
            f"{elapsed:.3f}s", metrics, passed
        )
        self.assertTrue(passed, result_text)
        
    except Exception as e:
        self._handle_test_exception(test_name, description, e, timer)
```

### 6. Performance Configuration (test_config.py additions)

Add performance test criteria to test_config.py:

```python
def get_pass_criteria(test_name: str) -> dict:
    """Get pass/fail criteria for specific test."""
    criteria = {
        # ... existing criteria ...
        
        'response_time': {
            'max_avg_ms': 100,
            'max_p95_ms': 200,
            'max_p99_ms': 500
        },
        'throughput': {
            'min_ops_per_second': 100,
            'max_error_rate_percent': 1.0
        },
        'load_test': {
            'min_success_rate_percent': 99.0,
            'max_p95_response_ms': 500,
            'min_throughput': 50
        },
        'stress_test': {
            'min_load_capacity': 1000,
            'max_memory_mb': 2000
        },
        'memory_profiling': {
            'max_peak_memory_mb': 500,
            'max_growth_mb': 50
        }
    }
    return criteria.get(test_name, {'default': True})
```

**Deliverables:**
1. Response time tests with percentile analysis
2. Throughput tests with sustained load
3. Load tests with concurrent execution
4. Stress tests finding breaking points
5. Memory profiling with leak detection
6. Performance baseline documentation
7. Comprehensive performance metrics

**Success Criteria:**
- Response times within acceptable limits
- Throughput meets requirements
- System handles target concurrent load
- Breaking points documented
- No memory leaks detected
- All metrics properly collected and reported
```

## Expected Outcomes

### Performance Metrics Collected
- Response time statistics (avg, median, p95, p99, max)
- Throughput measurements (ops/sec, req/sec)
- Resource usage (CPU, memory, disk I/O)
- Concurrency handling (concurrent users/requests)
- Scalability limits (breaking points)
- Memory leak detection

### Performance Standards Validated
- Operations complete within time limits
- System handles expected load
- Resource usage stays within bounds
- No performance degradation over time
- Scalability meets requirements

### Performance Baselines Established
- Historical performance data
- Regression detection enabled
- Performance trends tracked
- Optimization opportunities identified

## Performance Testing Best Practices

### Load Generation
- Start with small loads and increase gradually
- Use realistic data distributions
- Simulate real user behavior patterns
- Include think time between operations
- Vary request patterns

### Resource Monitoring
- Monitor CPU, memory, disk, network
- Track resource usage over time
- Identify resource bottlenecks
- Detect memory leaks early
- Profile database query performance

### Result Analysis
- Compare against baselines
- Identify performance regressions
- Analyze outliers and anomalies
- Document performance characteristics
- Track improvements over time

## Next Steps
After completing performance testing, proceed to Phase 5: Test Maintenance & CI/CD Integration.
