# C/Embedded Performance Review

## Objective
Systematically identify performance bottlenecks, resource inefficiencies, and real-time constraint violations in embedded C code. Provide data-driven optimization recommendations to improve execution speed, reduce memory footprint, minimize power consumption, and ensure real-time deadlines are met.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/performance_review/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/performance_review/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Review Checklist

### Execution Performance

- [ ] CPU profiling completed (gprof, Valgrind, embedded profiler)

- [ ] Interrupt latency measured

- [ ] Critical path timing analyzed

- [ ] Hot functions identified

- [ ] Real-time deadlines verified

### Memory Usage

- [ ] Flash/ROM usage measured and optimized

- [ ] RAM usage analyzed (static, stack, heap)

- [ ] Stack depth profiling completed

- [ ] Memory fragmentation assessed (if heap used)

- [ ] DMA buffer placement optimized

### Algorithm Efficiency

- [ ] Time complexity evaluated (O(n), O(n²))

- [ ] Space complexity assessed

- [ ] Lookup tables vs computation trade-offs

- [ ] Unnecessary computations identified

- [ ] Cache-friendly access patterns verified

### Peripheral & I/O

- [ ] Peripheral configuration optimized

- [ ] DMA usage opportunities identified

- [ ] Interrupt vs polling strategies evaluated

- [ ] Bus utilization analyzed

- [ ] Hardware acceleration leveraged

### Power Consumption

- [ ] Power profiling completed

- [ ] Sleep modes utilized effectively

- [ ] Peripheral clock gating implemented

- [ ] Active time minimized

- [ ] Low-power design patterns applied

### Real-Time Behavior

- [ ] Worst-case execution time (WCET) analyzed

- [ ] Deadline misses identified

- [ ] Priority inversion risks assessed

- [ ] Interrupt latency acceptable

- [ ] Jitter minimized

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C/Embedded Performance Review

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/performance_review"
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

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Review Protocol

Please perform a comprehensive performance review of this embedded C application following this protocol:

## Phase 1: Performance Profiling Setup

1. **CPU Profiling (Development Environment)**
   ```bash
   # GCC profiling with gprof
   # Add to CFLAGS: -pg
   # Run application, generates gmon.out
   gprof firmware.elf gmon.out > ${OUTPUT_DIR}/exports/profile.txt

   # Analyze profile.txt for:
   - Top time-consuming functions
   - Call counts
   - Call graph
   ```

2. **Embedded Profiling (Target Hardware)**
   ```c
   // Instrumentation profiling using GPIO toggle
   #define PROFILE_START() GPIO_SET(PROFILE_PIN)
   #define PROFILE_STOP()  GPIO_CLR(PROFILE_PIN)

   void critical_function(void) {
       PROFILE_START();
       // Function code
       PROFILE_STOP();
   }
   // Measure with oscilloscope or logic analyzer

   // Or use DWT (Data Watchpoint and Trace) on ARM Cortex-M
   void dwt_init(void) {
       CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
       DWT->CYCCNT = 0;
       DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
   }

   uint32_t start = DWT->CYCCNT;
   critical_function();
   uint32_t cycles = DWT->CYCCNT - start;
   uint32_t microseconds = cycles / (CPU_FREQ_MHZ);
   ```

3. **Memory Profiling**
   ```bash
   # Analyze map file for memory usage
   arm-none-eabi-nm -S -C --size-sort firmware.elf | grep -v " [bB] "

   # Or use size utility
   arm-none-eabi-size -A -x firmware.elf

   # Stack usage analysis (GCC)
   # Add to CFLAGS: -fstack-usage
   # Generates .su files with stack usage per function
   find . -name "*.su" -exec cat {} \;
   ```

4. **Real-Time Tracing**
   ```c
   // SEGGER SystemView for real-time task analysis
   #include "SEGGER_SYSVIEW.h"

   SEGGER_SYSVIEW_Start();
   // Trace tasks, interrupts, events in real-time

   // Or use trace buffer logging
   typedef struct {
       uint32_t timestamp;
       uint8_t event_id;
       uint32_t data;
   } trace_event_t;

   #define MAX_TRACE 256
   trace_event_t trace_buffer[MAX_TRACE];
   ```

## Phase 2: Execution Performance Analysis

1. **Identify Performance Hotspots**
   ```c
   // Look for functions consuming >5% of CPU time

   // Common hotspots in embedded:
   - Protocol parsing loops
   - Data filtering/processing
   - Floating-point math
   - String operations
   - Sensor data averaging
   - CRC/checksum calculations
   ```

2. **Interrupt Latency Analysis**
   ```c
   // Measure interrupt response time
   void IRQ_Handler(void) {
       GPIO_SET(INT_TIMING_PIN);  // Start measurement

       // Read interrupt source
       uint32_t status = PERIPHERAL->SR;

       // Handle interrupt
       process_interrupt(status);

       // Clear interrupt flag
       PERIPHERAL->SR = status;

       GPIO_CLR(INT_TIMING_PIN);  // End measurement
   }

   // Goals:
   // - ISR < 10 µs for most interrupts
   // - ISR < 1 µs for critical timing
   // - Defer work to main loop or task
   ```

3. **Real-Time Deadline Analysis**
   ```c
   // Identify real-time tasks and their deadlines

   // Example: Motor control loop must run every 1ms
   void motor_control_task(void) {
       static uint32_t last_exec = 0;
       uint32_t now = get_tick_count();

       if (now - last_exec > 1) {  // Deadline miss!
           deadline_miss_counter++;
       }

       last_exec = now;
       // Control algorithm
   }

   // Measure:
   - Best case execution time
   - Average case execution time
   - Worst case execution time (WCET)
   - Jitter (variation in execution time)
   ```

## Phase 3: Algorithm Optimization

1. **Computational Complexity**
   ```c
   // INEFFICIENT: O(n²) nested loops
   for (int i = 0; i < n; i++) {
       for (int j = 0; j < n; j++) {
           if (array1[i] == array2[j]) {
               count++;
           }
       }
   }

   // BETTER: O(n) with lookup table or sorting
   // Use hash table or sorted arrays for O(n log n) or O(n)

   // INEFFICIENT: Repeated calculations
   for (int i = 0; i < 100; i++) {
       float result = sqrt(value) * 1.5;  // sqrt() called 100 times
       data[i] = result;
   }

   // EFFICIENT: Hoist invariant computation
   float result = sqrt(value) * 1.5;
   for (int i = 0; i < 100; i++) {
       data[i] = result;
   }

   // INEFFICIENT: Division in loop
   for (int i = 0; i < n; i++) {
       scaled[i] = data[i] / scale_factor;
   }

   // EFFICIENT: Multiply by reciprocal
   float inv_scale = 1.0f / scale_factor;
   for (int i = 0; i < n; i++) {
       scaled[i] = data[i] * inv_scale;
   }
   ```

2. **Lookup Tables vs Computation**
   ```c
   // SLOW: Compute sine at runtime
   float angle_deg = 45.0f;
   float value = sinf(angle_deg * M_PI / 180.0f);

   // FAST: Pre-computed lookup table
   const float sin_table[360] = {
       0.0f, 0.0175f, 0.0349f, ...  // Pre-computed
   };

   uint16_t angle_int = (uint16_t)angle_deg;
   float value = sin_table[angle_int];

   // Trade-off: Flash space vs computation time
   // Good for: trig functions, exponentials, complex formulas
   // Use when: function called frequently, acceptable precision
   ```

3. **Fixed-Point vs Floating-Point**
   ```c
   // SLOW: Floating-point on MCU without FPU
   float temperature_c = adc_value * 0.01f - 50.0f;

   // FAST: Fixed-point arithmetic (Q16.16 format)
   // 1.0 = 65536 (2^16)
   int32_t scale_q16 = 655;        // 0.01 in Q16.16
   int32_t offset_q16 = -3276800;  // -50.0 in Q16.16
   int32_t temp_q16 = (adc_value * scale_q16) + offset_q16;
   int32_t temperature_c = temp_q16 >> 16;  // Convert to integer

   // Or use integer scaling
   // Temperature in 0.1°C units
   int16_t temperature_decideg = (adc_value * 10) / 100 - 500;
   ```

4. **Bit Manipulation Optimization**
   ```c
   // SLOW: Modulo and division
   int index = (counter % BUFFER_SIZE);
   int half = value / 2;

   // FAST: Bitwise operations (if power of 2)
   #define BUFFER_SIZE 64  // Must be power of 2
   int index = counter & (BUFFER_SIZE - 1);  // Equivalent to % 64
   int half = value >> 1;  // Equivalent to / 2

   // SLOW: Checking even/odd
   if (value % 2 == 0)

   // FAST: Bitwise AND
   if ((value & 1) == 0)

   // SLOW: Multiply by power of 2
   int result = value * 8;

   // FAST: Shift left
   int result = value << 3;
   ```

## Phase 4: Memory Optimization

1. **Flash/ROM Usage Analysis**
   ```bash
   # Identify large functions and data
   arm-none-eabi-nm -S --size-sort firmware.elf | tail -20

   # Common memory hogs:
   - Large lookup tables
   - String constants
   - Debug strings
   - Unoptimized code

   # Optimization strategies:
   # 1. Compiler optimization: -Os (size) or -O2/-O3 (speed)
   # 2. Remove debug strings in production
   # 3. Compress lookup tables
   # 4. Use const for read-only data (placed in Flash)
   ```

2. **RAM Usage Optimization**
   ```c
   // INEFFICIENT: Separate variables
   uint8_t flag1;
   uint8_t flag2;
   uint8_t flag3;
   uint8_t flag4;
   // Uses 4 bytes (or more with alignment)

   // EFFICIENT: Bit fields
   struct {
       uint8_t flag1 : 1;
       uint8_t flag2 : 1;
       uint8_t flag3 : 1;
       uint8_t flag4 : 1;
       uint8_t reserved : 4;
   } flags;
   // Uses 1 byte

   // INEFFICIENT: Large local arrays
   void process(void) {
       uint8_t buffer[1024];  // Stack usage!
   }

   // EFFICIENT: Static allocation
   static uint8_t s_buffer[1024];
   void process(void) {
       // Use s_buffer
   }

   // INEFFICIENT: Structure padding
   struct {
       uint8_t a;    // 1 byte
       uint32_t b;   // 4 bytes (padded to 8 total)
       uint8_t c;    // 1 byte (padded to 12 total)
   } inefficient;  // Total: 12 bytes with padding

   // EFFICIENT: Reorder members
   struct {
       uint32_t b;   // 4 bytes
       uint8_t a;    // 1 byte
       uint8_t c;    // 1 byte (padded to 8 total)
   } efficient;    // Total: 8 bytes
   ```

3. **Stack Usage Analysis**
   ```bash
   # GCC stack usage analysis
   # CFLAGS: -fstack-usage
   # Review .su files for each function

   # Find largest stack consumers
   cat *.su | sort -k2 -n -r | head -20

   # Linker script: ensure adequate stack size
   _Min_Stack_Size = 0x800;  /* 2KB for main stack */

   # Per-task stacks (RTOS)
   #define TASK_STACK_SIZE 512
   static uint32_t task_stack[TASK_STACK_SIZE];
   ```

4. **Data Structure Packing**
   ```c
   // Use packed structures for protocols (save RAM)
   struct __attribute__((packed)) protocol_header {
       uint8_t type;
       uint16_t length;
       uint32_t timestamp;
   };  // 7 bytes (no padding)

   // Use const for ROM placement
   const uint16_t crc_table[256] = { ... };  // In Flash, not RAM

   // Pool allocations instead of malloc
   #define PACKET_POOL_SIZE 10
   typedef struct {
       uint8_t data[64];
       bool in_use;
   } packet_t;

   static packet_t packet_pool[PACKET_POOL_SIZE];

   packet_t* alloc_packet(void) {
       for (int i = 0; i < PACKET_POOL_SIZE; i++) {
           if (!packet_pool[i].in_use) {
               packet_pool[i].in_use = true;
               return &packet_pool[i];
           }
       }
       return NULL;
   }
   ```

## Phase 5: Peripheral & I/O Optimization

1. **DMA Usage**
   ```c
   // SLOW: Polling or interrupt per byte
   for (int i = 0; i < len; i++) {
       while (!(UART->SR & UART_SR_TXE)) {}
       UART->DR = data[i];
   }

   // FAST: DMA transfer
   dma_config.src = data;
   dma_config.dst = &UART->DR;
   dma_config.length = len;
   dma_start(&dma_config);
   // CPU free to do other work

   // Benefits:
   - Zero CPU overhead during transfer
   - Faster transfer rates
   - Lower power (CPU can sleep)

   // Use DMA for:
   - UART/SPI/I2C data transfers
   - ADC continuous conversion
   - Memory-to-memory copies
   - DAC waveform generation
   ```

2. **Interrupt vs Polling Strategy**
   ```c
   // POLLING: Simple but CPU-intensive
   while (1) {
       if (UART->SR & UART_SR_RXNE) {
           data = UART->DR;
           process(data);
       }
       // CPU busy waiting
   }

   // INTERRUPT: Efficient, responsive
   void UART_IRQHandler(void) {
       if (UART->SR & UART_SR_RXNE) {
           data = UART->DR;
           data_ready_flag = true;
       }
   }

   void main_loop(void) {
       if (data_ready_flag) {
           data_ready_flag = false;
           process(data);
       }
       // CPU can sleep or do other work
   }

   // Guidelines:
   - Use polling for very fast, time-critical checks
   - Use interrupts for asynchronous events
   - Use DMA for bulk transfers
   ```

3. **Peripheral Clock Management**
   ```c
   // Disable unused peripheral clocks

   // Bad: All peripherals enabled
   RCC->APB1ENR = 0xFFFFFFFF;

   // Good: Only enable what's needed
   RCC->APB1ENR = RCC_APB1ENR_USART2EN | RCC_APB1ENR_TIM2EN;

   // Dynamically enable/disable
   void start_spi_transaction(void) {
       RCC->APB2ENR |= RCC_APB2ENR_SPI1EN;
       // Use SPI
       RCC->APB2ENR &= ~RCC_APB2ENR_SPI1EN;
   }

   // Benefits: Lower power consumption
   ```

4. **Cache and Memory Access Patterns**
   ```c
   // SLOW: Cache-unfriendly access (if cache present)
   for (int i = 0; i < N; i++) {
       for (int j = 0; j < M; j++) {
           sum += matrix[j][i];  // Column-major access
       }
   }

   // FAST: Cache-friendly access (sequential)
   for (int i = 0; i < N; i++) {
       for (int j = 0; j < M; j++) {
           sum += matrix[i][j];  // Row-major access
       }
   }

   // SLOW: Non-aligned access (may cause fault or slow access)
   uint32_t *ptr = (uint32_t *)((uint8_t *)data + 1);  // Misaligned
   uint32_t value = *ptr;

   // FAST: Aligned access
   uint32_t *ptr = (uint32_t *)data;  // Properly aligned
   uint32_t value = *ptr;
   ```

## Phase 6: Power Consumption Optimization

1. **Sleep Modes**
   ```c
   // INEFFICIENT: Always active
   while (1) {
       if (event_flag) {
           process_event();
           event_flag = false;
       }
       // CPU running at full speed
   }

   // EFFICIENT: Sleep when idle
   while (1) {
       if (event_flag) {
           process_event();
           event_flag = false;
       } else {
           __WFI();  // Wait For Interrupt (sleep)
       }
   }

   // Deep sleep for longer idle periods
   void enter_deep_sleep(void) {
       // Disable unnecessary peripherals
       RCC->APB1ENR = 0;
       RCC->APB2ENR = 0;

       // Configure wake-up source (e.g., RTC)
       // Enter stop mode
       PWR->CR |= PWR_CR_LPDS;
       SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;
       __WFI();

       // Wake-up: reconfigure clocks and peripherals
   }
   ```

2. **Dynamic Frequency Scaling**
   ```c
   // Reduce clock speed when performance not critical
   void set_low_power_mode(void) {
       // Switch to lower frequency (e.g., 8MHz from 72MHz)
       // Reduce voltage if supported
       // Power consumption ∝ frequency × voltage²
   }

   void set_high_performance_mode(void) {
       // Switch back to high frequency for demanding tasks
   }
   ```

3. **Peripheral Power Management**
   ```c
   // Turn off peripherals when not in use
   void sensor_read(void) {
       // Power on sensor
       GPIO_SET(SENSOR_PWR_PIN);
       delay_ms(10);  // Stabilization time

       // Read sensor
       adc_start();
       value = adc_read();

       // Power off sensor
       GPIO_CLR(SENSOR_PWR_PIN);
   }
   ```

## Phase 7: Compiler Optimization

1. **Optimization Level Selection**
   ```makefile
   # -O0: No optimization (debug)
   # -O1: Basic optimization
   # -O2: Moderate optimization (good balance)
   # -O3: Aggressive optimization (may increase code size)
   # -Os: Optimize for size
   # -Og: Optimize for debug (GCC 4.8+)

   # Recommended for embedded:
   CFLAGS_DEBUG = -Og -g3
   CFLAGS_RELEASE = -O2  # or -Os if Flash limited
   ```

2. **Function Inlining**
   ```c
   // Force inline for small, frequently-called functions
   static inline uint32_t max(uint32_t a, uint32_t b) {
       return (a > b) ? a : b;
   }

   // Prevent inlining (for ISRs, debugging)
   __attribute__((noinline)) void critical_function(void) {
       // ...
   }

   // Hot/Cold attributes (optimization hint)
   __attribute__((hot)) void frequently_called(void) {
       // Optimized for speed
   }

   __attribute__((cold)) void error_handler(void) {
       // Optimized for size, not speed
   }
   ```

3. **Loop Optimization**
   ```c
   // Loop unrolling (compiler may do automatically at -O2/-O3)
   // Manual unroll for critical loops
   for (int i = 0; i < 8; i++) {
       sum += data[i];
   }

   // Unrolled (reduce loop overhead)
   sum += data[0] + data[1] + data[2] + data[3] +
          data[4] + data[5] + data[6] + data[7];

   // Restrict pointers (tell compiler no aliasing)
   void process(uint32_t * restrict src, uint32_t * restrict dst, size_t n) {
       for (size_t i = 0; i < n; i++) {
           dst[i] = src[i] * 2;
       }
   }
   // Compiler can optimize better knowing src and dst don't overlap
   ```

## Output Format

Please provide a comprehensive performance report with the following structure:

### Executive Summary

- **Overall Performance**: [Excellent/Good/Fair/Poor]

- **Real-Time Compliance**: [Met/Violated - deadline miss count]

- **Resource Utilization**: [Flash: X%, RAM: Y%, CPU: Z%]

- **Critical Bottlenecks**: [count and brief description]

- **Optimization Potential**: [estimated improvement]

### Timing Analysis
**Critical Path Performance**:
| Operation | Current Time | Target | Status | Optimization |
|-----------|--------------|--------|--------|--------------|
| [ISR] | [µs] | [<10µs] | [Pass/Fail] | [suggestion] |
| [Task] | [ms] | [<5ms] | [Pass/Fail] | [strategy] |

**Top 10 Time-Consuming Functions**:
| Function | File | Time | % Total | Calls | Time/Call | Category |
|----------|------|------|---------|-------|-----------|----------|
| [name] | [path] | [µs/ms] | [%] | [count] | [µs] | [computation/I/O] |

### Memory Analysis
**Flash Usage**: [X KB / Y KB (Z%)]

- Code: [X KB]

- Constants: [X KB]

- Optimization potential: [X KB]

**RAM Usage**: [X KB / Y KB (Z%)]

- Static: [X KB]

- Stack: [X KB] (peak: [X KB])

- Heap: [X KB] (if used)

- Optimization potential: [X KB]

**Largest Memory Consumers**:
| Symbol | Size | Type | Location | Optimization |
|--------|------|------|----------|--------------|
| [name] | [KB] | [code/data] | [file] | [suggestion] |

### CPU Utilization

- **Average Load**: [%]

- **Peak Load**: [%]

- **Idle Time**: [%]

- **Interrupt Overhead**: [%]

### Critical Performance Issues (Priority 1)
| Issue | Location | Impact | Current | Target | Optimization |
|-------|----------|--------|---------|--------|--------------|
| [description] | [file:line] | [High] | [metric] | [goal] | [strategy] |

### Algorithm Inefficiencies
| Function | Complexity | Current Performance | Optimized Approach | Expected Gain |
|----------|------------|---------------------|-------------------|---------------|
| [name] | [O(n²)] | [X ms] | [O(n) with lookup table] | [10x faster] |

### Peripheral Performance

- **DMA Opportunities**: [count of locations where DMA could be used]

- **Interrupt Latency**: [average and max]

- **Bus Utilization**: [SPI/I2C/UART efficiency]

### Power Consumption Analysis

- **Active Current**: [mA at X MHz]

- **Sleep Current**: [µA]

- **Average Current**: [mA] (based on duty cycle)

- **Battery Life**: [estimated hours/days]

- **Optimization Potential**: [X% reduction]

### Quick Wins (High Impact, Low Effort)
1. **[Replace floating-point with fixed-point in filter()]**
   - **Location**: dsp.c:123
   - **Current**: 45 µs per sample
   - **Expected**: 5 µs per sample (9x faster)
   - **Effort**: 2 hours

2. **[Use DMA for UART transfers]**
   - **Location**: uart.c:89
   - **Current**: 80% CPU during transfer
   - **Expected**: <5% CPU overhead
   - **Effort**: 3 hours

### Medium-term Optimizations (1-3 days effort)
[List of optimizations requiring moderate refactoring]

### Strategic Optimizations (>3 days, architectural changes)
[List of major performance initiatives]

### Compiler Optimization Review
| Optimization | Current | Recommended | Impact |
|--------------|---------|-------------|--------|
| Optimization Level | [-O0] | [-O2/-Os] | [30% faster/smaller] |
| LTO | [Disabled] | [Enabled] | [10% smaller] |
| Stack Protection | [Enabled] | [Disabled for production] | [5% faster] |

### Real-Time Analysis
**Deadline Compliance**:
| Task | Period | WCET | Deadline | Margin | Status |
|------|--------|------|----------|--------|--------|
| [task] | [ms] | [ms] | [ms] | [%] | [Pass/Fail] |

**Priority Inversion Risks**: [Yes/No - locations if yes]
**Interrupt Nesting Issues**: [Safe/Issues found]

### Benchmark Results
**Before Optimization**:

- [Operation]: [time/throughput]

**After Optimization** (projected):

- [Operation]: [time/throughput]

**Improvement**: [X%] faster / [Y%] smaller / [Z%] lower power

### Performance Testing Recommendations
```c
// Recommended performance tests:

1. Timing benchmarks:
   - Measure all real-time critical functions
   - Verify worst-case execution time (WCET)
   - Test under interrupt load

2. Stress testing:
   - Maximum data rate
   - All peripherals active simultaneously
   - Worst-case scenarios

3. Power profiling:
   - Measure current in all states
   - Validate sleep mode entry/exit
   - Check for unexpected wake-ups

4. Long-term stability:
   - Run for 24+ hours
   - Monitor for performance degradation
   - Check for memory leaks (if heap used)
```

### Next Steps

- [ ] Implement quick win optimizations

- [ ] Enable compiler optimization flags

- [ ] Add performance monitoring to CI

- [ ] Establish performance budgets for new features

- [ ] Document optimization decisions

- [ ] Plan performance testing before deployment

## Notes

- Optimize based on profiling data, not assumptions

- Balance performance with code maintainability

- Consider power consumption in battery-powered devices

- Verify optimizations don't break functionality

- Real-time deadlines are hard constraints - must be met

- Document any trade-offs (speed vs size, power vs performance)

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/performance_review/analysis_scripts
mkdir -p ${OUTPUT_DIR}/performance_review/supporting_data
```

**Save files as follows**:

- Main report → `review/performance_review/performance_review_report.md`

- Findings data → `review/performance_review/performance_review_findings.json`

- Analysis scripts → `review/performance_review/analysis_scripts/`

- Supporting data → `review/performance_review/supporting_data/`
~~~
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
