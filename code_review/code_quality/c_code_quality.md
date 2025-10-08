# C/Embedded Code Quality Review

## Objective
Systematically evaluate embedded C code for maintainability, reliability, and adherence to industry best practices including MISRA-C and CERT-C standards. Identify safety issues, complexity hotspots, and areas requiring refactoring for long-term firmware health.

## Review Checklist

### Coding Standards
- [ ] MISRA-C compliance verified (MISRA-C:2012 or MISRA-C:2004)
- [ ] CERT-C secure coding rules followed
- [ ] Project-specific coding standards applied
- [ ] Consistent naming conventions (variables, functions, types)
- [ ] Function and file organization standards met

### Code Complexity
- [ ] Functions under 50 lines (flagged if exceeded)
- [ ] Cyclomatic complexity under 10 per function
- [ ] Nesting depth under 4 levels
- [ ] Minimal use of goto statements
- [ ] Switch statements with default cases

### Safety & Reliability
- [ ] Pointer usage verified (NULL checks, bounds checking)
- [ ] Integer overflow/underflow protection
- [ ] Type conversions explicit and safe
- [ ] Volatile usage correct for hardware registers
- [ ] Critical sections properly protected

### Resource Management
- [ ] Stack usage analyzed (recursion avoided)
- [ ] Heap usage minimized or avoided
- [ ] Static vs dynamic allocation strategy consistent
- [ ] Memory alignment requirements met
- [ ] Resource leaks prevented

### Hardware Interface
- [ ] Memory-mapped register access safe
- [ ] Peripheral configuration correct
- [ ] Interrupt handlers lightweight and safe
- [ ] DMA usage correct (alignment, coherency)
- [ ] Timing-critical code identified

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C/Embedded Code Quality Review

Please perform a comprehensive code quality review of this embedded C project following this protocol:

## Phase 1: Static Analysis with Industry Tools

1. **MISRA-C Compliance Check**
   ```bash
   # Using PC-lint Plus, Cppcheck, or PRQA

   # Cppcheck with MISRA addon
   cppcheck --addon=misra.json --enable=all --suppress=missingIncludeSystem src/

   # PC-lint Plus
   lint-nt +v -w3 -i./inc src/*.c

   # Check for critical MISRA violations:
   # - Required rules (must follow)
   # - Advisory rules (should follow)
   # - Mandatory rules (absolutely must follow)
   ```

2. **CERT-C Secure Coding**
   ```bash
   # Check for CERT-C violations using static analyzers
   # Focus on:
   # - INT30-C: Integer overflow
   # - ARR38-C: Array bounds
   # - MEM30-C: Memory allocation
   # - STR31-C: String operations
   # - FIO30-C: File operations

   # Use tools like:
   clang --analyze -Xanalyzer -analyzer-checker=security src/*.c
   ```

3. **General Static Analysis**
   ```bash
   # Cppcheck for general issues
   cppcheck --enable=all --inconclusive --xml src/ 2> cppcheck_report.xml

   # Clang Static Analyzer
   scan-build make

   # Splint (secure programming lint)
   splint +posixlib src/*.c
   ```

## Phase 2: Coding Standards Assessment

1. **Naming Conventions**
   ```c
   // Check consistency across codebase:

   // Functions: lowercase with underscores or camelCase
   void init_uart(void);           // Good
   void InitUART(void);            // Acceptable if consistent
   void iuart(void);               // Bad: unclear

   // Variables: descriptive, lowercase with underscores
   uint32_t sensor_reading;        // Good
   uint32_t sr;                    // Bad: unclear

   // Constants/Macros: UPPERCASE with underscores
   #define MAX_BUFFER_SIZE 256     // Good
   #define maxbuffersize 256       // Bad: wrong case

   // Types: _t suffix or PascalCase
   typedef struct {
       uint8_t data[32];
   } sensor_data_t;                // Good

   // Global variables: prefix (g_ or global_)
   volatile uint32_t g_tick_count; // Good

   // Static variables: prefix (s_ or static_)
   static uint8_t s_buffer[64];    // Good
   ```

2. **File Organization**
   - Header guards: `#ifndef/#define/#endif` or `#pragma once`
   - Include order: system, third-party, local
   - Function order: public then private
   - One function per logical operation
   - Related functions grouped together

3. **Comment Quality**
   ```c
   // Good comments explain WHY, not WHAT

   // Bad: States the obvious
   i++;  // Increment i

   // Good: Explains reasoning
   // Delay required for sensor stabilization per datasheet section 4.2
   delay_ms(10);

   // Good: Function documentation
   /**
    * @brief Initialize UART peripheral for debug communication
    * @param baudrate Desired baud rate (9600, 115200, etc.)
    * @return 0 on success, -1 on error
    * @note Assumes 48MHz system clock
    */
   int uart_init(uint32_t baudrate);
   ```

## Phase 3: MISRA-C Critical Rules Review

1. **MISRA-C Required Rules (High Priority)**
   ```c
   // Rule 1.3: Undefined behavior must not occur
   int arr[5];
   arr[5] = 10;  // VIOLATION: Array out of bounds

   // Rule 2.1: Unreachable code
   if (true) {
       return 0;
       cleanup();  // VIOLATION: Unreachable
   }

   // Rule 8.13: Const correctness
   void process(uint8_t *data);         // Bad
   void process(const uint8_t *data);   // Good (if data not modified)

   // Rule 10.3: Implicit type conversions
   uint8_t a = 200;
   uint16_t b = a + 100;  // VIOLATION: Implicit conversion, potential overflow
   uint16_t b = (uint16_t)a + 100U;  // Good: Explicit

   // Rule 11.5: Pointer type conversions
   uint32_t *p = (uint32_t *)0x40000000;  // VIOLATION in strict MISRA
   // Better: Use explicit memory-mapped struct

   // Rule 14.4: Boolean comparisons
   if (flag == true)   // MISRA violation
   if (flag != false)  // MISRA violation
   if (flag)           // Acceptable

   // Rule 17.7: Function return values must be used
   gpio_set_pin(PIN_5);  // VIOLATION if function returns error code
   (void)gpio_set_pin(PIN_5);  // Good: Explicit void cast if intentional

   // Rule 21.3: Dynamic memory allocation
   void *ptr = malloc(100);  // VIOLATION in embedded context
   // Use static allocation instead
   ```

2. **MISRA-C Advisory Rules**
   ```c
   // Rule 2.3: Unused type declarations
   typedef struct { int x; } unused_t;  // Warning: Remove if unused

   // Rule 2.7: Unused function parameters
   void handler(uint32_t event, void *context) {
       // context unused - mark it
       (void)context;
   }

   // Rule 8.7: Functions with internal linkage
   void internal_func(void);  // Should be static if only used in this file
   static void internal_func(void);  // Good

   // Rule 15.5: Single exit point
   int process(void) {
       if (error1) return -1;
       if (error2) return -2;  // Advisory: Consider single exit
       return 0;
   }
   ```

## Phase 4: CERT-C Secure Coding Review

1. **Integer Security (INT)**
   ```c
   // INT30-C: Unsigned integer operations must not wrap
   uint32_t a = UINT32_MAX;
   uint32_t b = a + 1;  // VIOLATION: Wraps to 0

   // Protection:
   if (a > UINT32_MAX - 1) {
       // Handle overflow
   } else {
       b = a + 1;
   }

   // INT31-C: Integer conversions must not lose information
   int32_t large = 100000;
   int16_t small = large;  // VIOLATION: Data loss

   // INT32-C: Ensure operations don't overflow
   int32_t x = INT32_MAX;
   int32_t y = x * 2;  // VIOLATION: Overflow
   ```

2. **Array Security (ARR)**
   ```c
   // ARR30-C: Do not form out-of-bounds pointers
   uint8_t buffer[10];
   uint8_t *p = &buffer[10];  // VIOLATION: Out of bounds

   // ARR38-C: Library functions must not access beyond array
   char src[5] = "test";
   char dst[5];
   strcpy(dst, src);  // Potentially unsafe
   strncpy(dst, src, sizeof(dst));  // Better
   dst[sizeof(dst)-1] = '\0';  // Ensure null termination
   ```

3. **Memory Security (MEM)**
   ```c
   // MEM30-C: Do not access freed memory
   uint8_t *ptr = malloc(100);
   free(ptr);
   *ptr = 5;  // VIOLATION: Use after free

   // MEM35-C: Allocate sufficient memory
   typedef struct {
       uint8_t data[100];
   } large_t;
   large_t *p = malloc(sizeof(p));  // VIOLATION: Wrong size
   large_t *p = malloc(sizeof(*p)); // Good

   // MEM36-C: Do not modify string literals
   char *str = "Hello";
   str[0] = 'h';  // VIOLATION: Undefined behavior
   ```

4. **String Security (STR)**
   ```c
   // STR31-C: Guarantee string is null-terminated
   char buffer[10];
   strncpy(buffer, source, sizeof(buffer));  // May not null-terminate
   buffer[sizeof(buffer)-1] = '\0';  // Ensure termination

   // STR32-C: Do not pass non-null-terminated strings
   char buffer[5] = {'H', 'e', 'l', 'l', 'o'};  // Not null-terminated
   printf("%s", buffer);  // VIOLATION
   ```

## Phase 5: Embedded-Specific Quality Issues

1. **Volatile Usage**
   ```c
   // Correct volatile usage for hardware registers
   #define GPIO_ODR (*(volatile uint32_t *)0x40020014)

   // VIOLATION: Missing volatile
   uint32_t *gpio = (uint32_t *)0x40020014;
   *gpio = 0xFF;  // Compiler may optimize away

   // Good: Volatile for hardware and ISR-shared variables
   volatile uint32_t g_tick_counter;  // Updated in SysTick ISR

   // Bad: Volatile overuse
   volatile int local_var;  // Unnecessary for local variable
   ```

2. **Interrupt Handler Safety**
   ```c
   // ISR Best Practices

   // Good: Short, simple ISR
   void UART_IRQHandler(void) {
       // Clear interrupt flag
       UART->SR &= ~UART_SR_RXNE;

       // Read data and signal main loop
       g_rx_buffer[g_rx_index++] = UART->DR;
       g_data_ready = true;
   }

   // Bad: Heavy processing in ISR
   void UART_IRQHandler(void) {
       parse_protocol();      // Too complex
       update_display();      // Too long
       save_to_flash();       // Blocking operation
   }

   // Rule: Keep ISRs under 10 lines if possible
   // Use flags/queues to defer work to main loop or task
   ```

3. **Atomic Operations**
   ```c
   // Problem: Non-atomic multi-word access
   volatile uint32_t g_timestamp_high;
   volatile uint32_t g_timestamp_low;

   // VIOLATION: Race condition
   void update_timestamp(void) {
       g_timestamp_high = new_high;  // If interrupted here...
       g_timestamp_low = new_low;
   }

   // Solution 1: Disable interrupts (short critical sections only)
   void update_timestamp(void) {
       __disable_irq();
       g_timestamp_high = new_high;
       g_timestamp_low = new_low;
       __enable_irq();
   }

   // Solution 2: Use 32-bit atomic type (if supported)
   _Atomic uint64_t g_timestamp;
   ```

4. **Stack Usage**
   ```c
   // Bad: Large stack allocation
   void process_data(void) {
       uint8_t buffer[2048];  // VIOLATION: Stack overflow risk
       // ...
   }

   // Good: Static allocation
   static uint8_t s_buffer[2048];
   void process_data(void) {
       // Use s_buffer
   }

   // Bad: Recursion (limited/no stack in embedded)
   void recursive_func(int n) {
       if (n > 0) recursive_func(n - 1);  // VIOLATION
   }

   // Good: Iterative approach
   void iterative_func(int n) {
       for (int i = 0; i < n; i++) {
           // Process
       }
   }
   ```

5. **Memory Alignment**
   ```c
   // DMA requires aligned buffers

   // Bad: May not be aligned
   uint8_t dma_buffer[256];

   // Good: Force alignment
   uint8_t dma_buffer[256] __attribute__((aligned(4)));

   // Or use compiler-specific alignment
   #if defined(__GNUC__)
       #define ALIGN_4 __attribute__((aligned(4)))
   #elif defined(__ICCARM__)
       #define ALIGN_4 _Pragma("data_alignment=4")
   #endif

   ALIGN_4 uint8_t dma_buffer[256];
   ```

## Phase 6: Code Complexity Analysis

1. **Function Complexity**
   ```bash
   # Calculate cyclomatic complexity
   lizard -l c src/ -w -C 10

   # Or use pmccabe
   pmccabe src/*.c | sort -nr | head -20

   # Flag functions with:
   # - Complexity > 10 (refactor candidates)
   # - Lines > 50 (break into smaller functions)
   # - Nesting depth > 4 (simplify logic)
   ```

2. **Identify Complex Functions**
   ```c
   // Example of overly complex function (anti-pattern)
   int process_packet(uint8_t *data, uint16_t len) {
       if (data != NULL) {
           if (len > 0) {
               if (len < MAX_LEN) {
                   for (int i = 0; i < len; i++) {
                       if (data[i] == START_BYTE) {
                           // Nested logic continues...
                           // This is too complex!
                       }
                   }
               } else {
                   return ERROR_TOO_LONG;
               }
           } else {
               return ERROR_ZERO_LENGTH;
           }
       } else {
           return ERROR_NULL_PTR;
       }
       return SUCCESS;
   }

   // Refactored: Early returns, extracted functions
   int process_packet(uint8_t *data, uint16_t len) {
       if (data == NULL) return ERROR_NULL_PTR;
       if (len == 0) return ERROR_ZERO_LENGTH;
       if (len >= MAX_LEN) return ERROR_TOO_LONG;

       return parse_packet_data(data, len);
   }
   ```

## Phase 7: Common Embedded Anti-Patterns

1. **Magic Numbers**
   ```c
   // Bad: Magic numbers
   if (status & 0x04) {
       delay_ms(100);
   }

   // Good: Named constants
   #define STATUS_ERROR_BIT (1U << 2)
   #define STABILIZATION_DELAY_MS 100

   if (status & STATUS_ERROR_BIT) {
       delay_ms(STABILIZATION_DELAY_MS);
   }
   ```

2. **Busy Waiting Without Timeout**
   ```c
   // Bad: Infinite busy wait
   while (!(UART->SR & UART_SR_TXE)) {
       // Stuck forever if hardware fails
   }

   // Good: Timeout mechanism
   uint32_t timeout = 1000;
   while (!(UART->SR & UART_SR_TXE) && timeout--) {
       delay_us(1);
   }
   if (timeout == 0) {
       return ERROR_TIMEOUT;
   }
   ```

3. **Bitwise Operations Without Masks**
   ```c
   // Bad: Potential side effects
   REG |= VALUE;  // What if VALUE has unwanted bits set?

   // Good: Proper masking
   #define MASK 0x0F
   REG = (REG & ~MASK) | (VALUE & MASK);
   ```

4. **Printf in Production**
   ```c
   // Bad: printf in embedded production code
   printf("Sensor value: %d\n", sensor_val);  // Slow, large binary size

   // Good: Lightweight logging or conditional compilation
   #ifdef DEBUG_ENABLE
       LOG_DEBUG("Sensor: %d", sensor_val);
   #endif
   ```

## Output Format

Please provide a comprehensive quality report with the following structure:

### Executive Summary
- **Overall Quality Score**: [A-F grade]
- **MISRA-C Compliance**: [% compliance, violations by severity]
- **CERT-C Issues**: [count by severity]
- **Average Complexity**: [cyclomatic complexity score]
- **Critical Issues**: [count]
- **Safety Risk Level**: [Low/Medium/High/Critical]

### MISRA-C Compliance Report
| Rule | Severity | Violations | Example Location | Impact |
|------|----------|------------|------------------|--------|
| [Rule ID] | [Required/Advisory/Mandatory] | [count] | [file:line] | [description] |

**Summary**:
- Mandatory violations: [count] (MUST FIX)
- Required violations: [count]
- Advisory violations: [count]

### CERT-C Security Issues
| Rule | Description | Severity | Location | Remediation |
|------|-------------|----------|----------|-------------|
| [INT30-C] | [issue] | [High/Med/Low] | [file:line] | [fix] |

### Complexity Analysis
**High Complexity Functions** (Complexity >10):
| Function | File | Complexity | Lines | Recommendation |
|----------|------|------------|-------|----------------|
| [name] | [path] | [score] | [count] | [refactor suggestion] |

### Embedded-Specific Issues
**Volatile Usage**: [correct/incorrect usage count]
**Interrupt Safety**: [issues found]
**Stack Analysis**: [functions with large stack usage]
**Memory Alignment**: [alignment issues]
**Hardware Access**: [unsafe hardware access patterns]

### Code Smells & Anti-Patterns
| Pattern | Location | Severity | Description | Fix |
|---------|----------|----------|-------------|-----|
| [Magic numbers] | [file:line] | [Med] | [details] | [use constants] |
| [Busy wait] | [file:line] | [High] | [no timeout] | [add timeout] |

### Resource Usage Concerns
- **Large Stack Allocations**: [list functions with >512 bytes]
- **Recursion**: [recursive functions identified]
- **Dynamic Memory**: [malloc/free usage locations]
- **Global Variables**: [excessive global state]

### Technical Debt Summary
**Priority 1 (Safety-Critical)**: [Estimated hours]
- [Issue affecting safety or reliability]

**Priority 2 (High)**: [Estimated hours]
- [Significant quality issues]

**Priority 3 (Medium)**: [Estimated hours]
- [Maintainability improvements]

**Priority 4 (Low)**: [Estimated hours]
- [Style and minor issues]

### Recommendations

**Immediate Actions** (within 1 sprint):
1. Fix all MISRA-C mandatory violations
2. Address CERT-C high-severity issues
3. Fix interrupt safety problems
4. Remove undefined behavior

**Short-term Goals** (1-2 months):
1. Achieve >95% MISRA-C compliance
2. Refactor high-complexity functions
3. Add missing NULL pointer checks
4. Improve error handling

**Long-term Initiatives** (3-6 months):
1. Establish automated static analysis in CI
2. Create project coding standards document
3. Provide team training on MISRA-C/CERT-C
4. Implement code review checklist

### Tool Configuration Recommendations
```ini
# Cppcheck configuration (cppcheck.cfg)
--enable=all
--addon=misra.json
--suppress=missingIncludeSystem
--inline-suppr
--max-configs=20

# MISRA compliance targets
Required rules: 100%
Advisory rules: >90%
```

### Next Steps
- [ ] Address all safety-critical issues (Priority 1)
- [ ] Run static analysis tools in CI pipeline
- [ ] Create suppression list for intentional violations
- [ ] Document coding standards
- [ ] Plan refactoring sprint for complex functions
- [ ] Set up pre-commit hooks for static analysis

## Notes
- MISRA-C compliance is critical for safety-related projects
- Some MISRA rules may be impractical; document deviations
- Embedded code quality impacts reliability and safety
- Static analysis should be automated in build process
- Balance safety/quality with practical constraints
~~~
