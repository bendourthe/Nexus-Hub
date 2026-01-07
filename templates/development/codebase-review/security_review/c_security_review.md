---
template_id: c_security_review
template_name: Security Review - C
version: 1.0.0
last_updated: 2025-12-03
language: C
category: code_review
phase: security_review
phase_number: 3
difficulty: advanced
estimated_time_hours: 2-3
prerequisites:

  - code_review/code_quality/c_code_quality.md
related_templates:

  - code_review/code_quality/c_code_quality.md
tools:

  - unity

  - cmocka

  - check
tags:

  - code-review

  - security

  - code-review

  - c
---
# C/Embedded Security Review

## Objective
Systematically identify security vulnerabilities, unsafe programming practices, and compliance gaps in embedded C code that could expose the device to attacks, data breaches, remote exploitation, or physical security compromise.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/security_review/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/security_review/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Review Checklist

### Memory Safety

- [ ] Buffer overflow vulnerabilities identified and fixed

- [ ] Stack overflow protection mechanisms in place

- [ ] Heap corruption risks assessed (if heap used)

- [ ] Use-after-free vulnerabilities prevented

- [ ] NULL pointer dereferences protected against

### Input Validation

- [ ] All external inputs validated (UART, SPI, I2C, network, USB)

- [ ] Bounds checking on array accesses

- [ ] String operations safe (no strcpy, sprintf)

- [ ] Integer overflow/underflow checked

- [ ] Protocol parsing robust against malformed data

### Cryptography & Authentication

- [ ] Cryptographic implementation reviewed (avoid custom crypto)

- [ ] Key storage secure (no hardcoded keys)

- [ ] Random number generation cryptographically secure

- [ ] Secure boot / firmware authentication implemented

- [ ] Debug interfaces protected in production

### Code Injection & Control Flow

- [ ] No command injection vulnerabilities

- [ ] Return-oriented programming (ROP) mitigations

- [ ] Stack canaries or stack protection enabled

- [ ] Control flow integrity verified

- [ ] Function pointer validation

### Information Disclosure

- [ ] No sensitive data in debug output

- [ ] Secrets not in plaintext in memory

- [ ] Side-channel attack vectors assessed

- [ ] Timing attacks considered

- [ ] Memory cleared after use (keys, passwords)

### Secure Firmware Updates

- [ ] Firmware signature verification

- [ ] Rollback protection mechanism

- [ ] Secure bootloader implementation

- [ ] Over-the-air (OTA) update security

- [ ] Update authentication and integrity

## Severity Classification

Use this framework to classify and prioritize all findings from the code review.

### CRITICAL (Fix Immediately)

**Definition:** Issues that create immediate risks to system stability, data integrity, or compliance.

**Examples:**

- Security vulnerabilities (SQL injection, XSS, authentication bypass)

- Resource leaks (unclosed connections, file handles, memory leaks)

- Data loss risks (destructive operations without validation)

- Thread safety violations (race conditions, deadlocks)

- Compliance violations (GDPR, HIPAA, PCI-DSS)

**Action Required:**

- Block deployment until fixed

- Require hotfix within 24 hours

- Add tests to prevent regression

- Document root cause and fix

---

### HIGH (Fix Before Next Release)

**Definition:** Issues that significantly impact maintainability, performance, or correctness but don't cause immediate failures.

**Examples:**

- Incorrect business logic (wrong calculations, flawed algorithms)

- Performance bottlenecks (O(n²) algorithms, missing indexes, inefficient queries)

- Memory inefficiency (loading large datasets into memory unnecessarily)

- Breaking API changes without deprecation

- Missing critical error handling (network errors, API failures not caught)

**Action Required:**

- Schedule fix in current sprint

- Cannot release without resolution

- Update documentation

- Performance test after fix

---

### MEDIUM (Fix in Next Cycle)

**Definition:** Code smells and technical debt that reduce maintainability but don't affect correctness.

**Examples:**

- High complexity (cyclomatic complexity >10, functions >100 lines)

- Code duplication (>10 lines duplicated across modules)

- Poor naming (unclear variable/function names, inconsistent conventions)

- Missing tests (<80% coverage on critical paths)

- Incomplete error messages (no context for debugging)

**Action Required:**

- Add to backlog

- Prioritize in next sprint planning

- Consider during refactoring opportunities

- Track technical debt metrics

---

### LOW (Nice to Have)

**Definition:** Style inconsistencies and minor optimizations that don't impact functionality.

**Examples:**

- Style violations (linting warnings, formatting issues)

- Minor performance optimizations (in non-critical code paths)

- Missing documentation on helper functions

- Verbose code that could be more concise

- Debug statements left in code

**Action Required:**

- Fix opportunistically during other work

- Batch with other low-priority changes

- Good for new contributors

- Can be deferred indefinitely

---

## Severity Assignment Guidelines

**When to Escalate Severity:**

- Issue affects **production environment** → escalate one level

- Issue affects **customer-facing features** → escalate one level

- Issue has **no workaround** → escalate one level

- Issue appears in **multiple locations** → escalate one level

**When to De-escalate Severity:**

- Issue only in **test/development code** → de-escalate one level

- Issue has **easy workaround** → de-escalate one level

- Issue is **isolated to single module** → de-escalate one level

- Issue **rarely executed** (edge case) → de-escalate one level

**Examples:**

- Memory leak in production API: **HIGH → CRITICAL** (production + customer-facing)

- Style violation in test file: **LOW → Ignore** (test code + style only)

- Duplicated logic across 15 modules: **MEDIUM → HIGH** (multiple locations)

---

## Reporting Format

For each finding, include:

**1. Severity Level:** [CRITICAL/HIGH/MEDIUM/LOW]

**2. Location:** File path and line numbers

**3. Issue Description:** What's wrong and why it matters

**4. Impact:** Specific consequences of not fixing

**5. Recommendation:** How to fix (with code example if applicable)

**6. Effort Estimate:** Time to fix (hours/days)

**Example Finding:**
```markdown
### HIGH: Performance Bottleneck in User Search

**Location:** `src/services/userService:145-167`

**Issue:** The user search function loads all users into memory and performs linear search on every request.

**Impact:**

- Response time degrades with user count (currently 500ms for 10k users)

- High memory usage (50MB+ per request)

- Poor scalability (can't handle >100k users)

**Recommendation:**
Move filtering to database with indexed query:

- Add database index on search fields

- Use database LIKE/ILIKE queries

- Implement pagination (limit results to 50)

- Add caching for common searches

**Effort:** 3 hours (2 hours implementation + 1 hour testing)

**Priority:** Must fix before next release (performance SLA violation)
```

---


## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C/Embedded Security Review

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/security_review"
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

Please perform a comprehensive security review of this embedded C project following this protocol:

## Phase 1: Automated Security Scanning

1. **Static Analysis for Security**
   ```bash
   # Flawfinder - C/C++ security scanner
   flawfinder --html --context src/ > ${OUTPUT_DIR}/exports/security_report.html

   # RATS - Rough Auditing Tool for Security
   rats --html src/*.c > ${OUTPUT_DIR}/exports/rats_report.html

   # Cppcheck with security checks
   cppcheck --enable=warning,style,performance,portability \
            --addon=cert.py --addon=threadsafety.py src/

   # Clang Static Analyzer (security checkers)
   scan-build -enable-checker security.insecureAPI.strcpy \
              -enable-checker security.insecureAPI.gets \
              make
   ```

2. **CWE Top 25 Scanning**
   ```bash
   # Focus on most dangerous software weaknesses for embedded:
   # CWE-119: Buffer overflow
   # CWE-120: Buffer copy without checking size
   # CWE-125: Out-of-bounds read
   # CWE-787: Out-of-bounds write
   # CWE-190: Integer overflow
   # CWE-416: Use after free
   # CWE-476: NULL pointer dereference
   # CWE-362: Race condition
   ```

3. **Compiler Security Flags Check**
   ```bash
   # Verify security-related compiler flags in Makefile

   # Stack protection
   -fstack-protector-strong  # or -fstack-protector-all

   # Position independent code (if applicable)
   -fPIC -fPIE

   # Format string protection
   -Wformat -Wformat-security

   # Fortify source (bounds checking)
   -D_FORTIFY_SOURCE=2

   # No executable stack
   -Wl,-z,noexecstack

   # RELRO (relocation read-only)
   -Wl,-z,relro,-z,now
   ```

## Phase 2: Memory Safety Analysis

1. **Buffer Overflow Vulnerabilities**
   ```c
   // Critical: Search for unsafe string functions

   // CRITICAL VIOLATIONS:
   strcpy(dest, src);           // No bounds checking
   strcat(dest, src);           // No bounds checking
   sprintf(buffer, fmt, ...);   // No bounds checking
   gets(buffer);                // Extremely dangerous
   scanf("%s", buffer);         // No bounds checking

   // SAFE ALTERNATIVES:
   strncpy(dest, src, sizeof(dest));
   dest[sizeof(dest)-1] = '\0';  // Ensure null termination

   strncat(dest, src, sizeof(dest) - strlen(dest) - 1);

   snprintf(buffer, sizeof(buffer), fmt, ...);

   fgets(buffer, sizeof(buffer), stdin);

   // BEST: Use safe string libraries
   #include "safe_str_lib.h"  // ISO/IEC TR 24731
   strcpy_s(dest, sizeof(dest), src);
   ```

2. **Array Bounds Checking**
   ```c
   // VIOLATION: No bounds check
   void process_data(uint8_t *data, uint16_t index) {
       uint8_t buffer[64];
       buffer[index] = data[index];  // CRITICAL: index could be >63
   }

   // SAFE: Bounds checking
   void process_data(uint8_t *data, uint16_t index) {
       uint8_t buffer[64];
       if (index >= sizeof(buffer)) {
           return ERROR_OUT_OF_BOUNDS;
       }
       buffer[index] = data[index];
   }

   // SAFE: Length parameter
   int process_data(const uint8_t *data, size_t data_len,
                     uint16_t index) {
       uint8_t buffer[64];
       if (index >= sizeof(buffer) || index >= data_len) {
           return ERROR_OUT_OF_BOUNDS;
       }
       buffer[index] = data[index];
       return SUCCESS;
   }
   ```

3. **Stack Overflow Protection**
   ```c
   // VIOLATION: Large stack allocation
   void parse_command(void) {
       char buffer[2048];  // CRITICAL: Stack overflow risk
       // ...
   }

   // SAFE: Static allocation
   static char s_buffer[2048];
   void parse_command(void) {
       // Use s_buffer
   }

   // Check stack usage in linker output
   // Ensure adequate stack size in linker script
   _Min_Stack_Size = 0x400;  /* 1KB minimum */
   ```

4. **Pointer Safety**
   ```c
   // VIOLATION: Missing NULL checks
   void process(data_t *data) {
       data->field = value;  // CRITICAL: Null pointer dereference
   }

   // SAFE: NULL pointer check
   void process(data_t *data) {
       if (data == NULL) {
           return ERROR_NULL_POINTER;
       }
       data->field = value;
   }

   // VIOLATION: Use after free (if heap used)
   uint8_t *buffer = malloc(256);
   free(buffer);
   buffer[0] = 0;  // CRITICAL: Use after free

   // SAFE: NULL after free
   uint8_t *buffer = malloc(256);
   free(buffer);
   buffer = NULL;
   ```

5. **Integer Overflow/Underflow**
   ```c
   // VIOLATION: Integer overflow
   uint16_t calculate_size(uint16_t items, uint16_t item_size) {
       return items * item_size;  // CRITICAL: Can overflow
   }

   // SAFE: Overflow check
   uint16_t calculate_size(uint16_t items, uint16_t item_size,
                           uint16_t *result) {
       if (items > 0 && item_size > UINT16_MAX / items) {
           return ERROR_OVERFLOW;
       }
       *result = items * item_size;
       return SUCCESS;
   }

   // VIOLATION: Sign conversion
   int16_t signed_val = -100;
   uint16_t unsigned_val = signed_val;  // CRITICAL: Becomes large positive

   // SAFE: Explicit check
   if (signed_val < 0) {
       return ERROR_INVALID_VALUE;
   }
   unsigned_val = (uint16_t)signed_val;
   ```

## Phase 3: Input Validation & Protocol Security

1. **External Input Validation**
   ```c
   // VIOLATION: Trusting external input
   void uart_receive_handler(void) {
       uint8_t length = UART_RX_DATA;  // From external source
       uint8_t buffer[64];
       for (uint8_t i = 0; i < length; i++) {  // CRITICAL: length not validated
           buffer[i] = read_uart();
       }
   }

   // SAFE: Input validation
   void uart_receive_handler(void) {
       uint8_t length = UART_RX_DATA;
       uint8_t buffer[64];

       // Validate length
       if (length > sizeof(buffer)) {
           length = sizeof(buffer);  // Truncate or reject
       }

       for (uint8_t i = 0; i < length; i++) {
           buffer[i] = read_uart();
       }
   }
   ```

2. **Protocol Parsing Security**
   ```c
   // VIOLATION: No length validation
   typedef struct {
       uint8_t type;
       uint16_t length;
       uint8_t data[];  // Flexible array member
   } packet_t;

   void parse_packet(uint8_t *raw) {
       packet_t *pkt = (packet_t *)raw;
       // CRITICAL: pkt->length could be malicious
       memcpy(buffer, pkt->data, pkt->length);
   }

   // SAFE: Length validation
   #define MAX_PACKET_DATA 256

   int parse_packet(const uint8_t *raw, size_t raw_len) {
       if (raw == NULL || raw_len < sizeof(packet_t)) {
           return ERROR_INVALID_INPUT;
       }

       const packet_t *pkt = (const packet_t *)raw;

       // Validate length field
       if (pkt->length > MAX_PACKET_DATA) {
           return ERROR_TOO_LARGE;
       }

       // Ensure raw buffer has enough data
       if (raw_len < sizeof(packet_t) + pkt->length) {
           return ERROR_TRUNCATED;
       }

       memcpy(buffer, pkt->data, pkt->length);
       return SUCCESS;
   }
   ```

3. **State Machine Attack Resistance**
   ```c
   // VIOLATION: Missing state validation
   typedef enum {
       STATE_INIT,
       STATE_CONNECTED,
       STATE_AUTHENTICATED,
       STATE_ACTIVE
   } conn_state_t;

   conn_state_t g_state = STATE_INIT;

   void process_command(uint8_t cmd) {
       if (cmd == CMD_EXECUTE) {
           execute_privileged_action();  // CRITICAL: No state check
       }
   }

   // SAFE: State validation
   void process_command(uint8_t cmd) {
       // Validate current state
       if (g_state != STATE_AUTHENTICATED) {
           return ERROR_UNAUTHORIZED;
       }

       if (cmd == CMD_EXECUTE) {
           execute_privileged_action();
       }
   }
   ```

## Phase 4: Cryptography & Key Management

1. **Hardcoded Secrets Detection**
   ```c
   // CRITICAL VIOLATIONS: Search for patterns like:

   const uint8_t aes_key[] = {
       0x2b, 0x7e, 0x15, 0x16, ...  // CRITICAL: Hardcoded key
   };

   #define API_KEY "a3f8d92e1..."      // CRITICAL: Hardcoded secret

   const char *password = "admin123";   // CRITICAL: Default password

   // SAFE: Key derivation or secure storage
   // - Keys derived from unique device ID + secret
   // - Keys stored in secure element or OTP memory
   // - Keys never in plaintext in code
   ```

2. **Weak Cryptography**
   ```c
   // CRITICAL: Weak or obsolete algorithms
   // Avoid:

   - MD5 for hashing

   - SHA-1 for signatures

   - DES, 3DES for encryption

   - RC4 stream cipher

   - Custom/homebrew crypto

   // Use:

   - SHA-256, SHA-3 for hashing

   - AES-128/256 for encryption

   - HMAC-SHA256 for authentication

   - Established libraries: mbedTLS, WolfSSL
   ```

3. **Random Number Generation**
   ```c
   // VIOLATION: Weak RNG for security
   srand(time(NULL));
   uint32_t session_id = rand();  // CRITICAL: Predictable

   // SAFE: Hardware RNG or cryptographic PRNG
   uint32_t get_random(void) {
       // Use hardware RNG if available
       while (!(RNG->SR & RNG_SR_DRDY)) {}
       return RNG->DR;
   }

   // Or use crypto library PRNG
   mbedtls_ctr_drbg_random(&ctr_drbg, output, length);
   ```

4. **Secure Key Storage**
   ```c
   // VIOLATION: Key in RAM (vulnerable to attacks)
   uint8_t aes_key[32];
   load_key_from_flash(aes_key);
   aes_encrypt(data, aes_key);
   // Key remains in memory

   // BETTER: Clear key after use
   uint8_t aes_key[32];
   load_key_from_flash(aes_key);
   aes_encrypt(data, aes_key);
   memset(aes_key, 0, sizeof(aes_key));  // Clear key

   // BEST: Use secure element or hardware crypto
   // Key never leaves secure storage
   secure_element_encrypt(data, KEY_ID_0);
   ```

## Phase 5: Secure Boot & Firmware Updates

1. **Firmware Authentication**
   ```c
   // VIOLATION: No firmware verification
   void bootloader_update(void) {
       memcpy(FLASH_BASE, new_firmware, firmware_size);
       jump_to_application();  // CRITICAL: Unsigned firmware
   }

   // SAFE: Signature verification
   int bootloader_update(const uint8_t *firmware,
                          size_t size,
                          const uint8_t *signature) {
       // Verify signature using public key
       if (!verify_signature(firmware, size, signature)) {
           return ERROR_INVALID_SIGNATURE;
       }

       // Verify firmware integrity
       uint32_t crc = calculate_crc32(firmware, size);
       if (crc != expected_crc) {
           return ERROR_CORRUPTED;
       }

       // Safe to flash
       flash_write(FLASH_BASE, firmware, size);
       return SUCCESS;
   }
   ```

2. **Rollback Protection**
   ```c
   // VIOLATION: No version check
   void bootloader_update(firmware_t *fw) {
       flash_write(fw);  // CRITICAL: Could downgrade to vulnerable version
   }

   // SAFE: Version checking and anti-rollback
   typedef struct {
       uint32_t version;
       uint32_t min_version;  // Minimum allowed version
       uint8_t data[];
   } firmware_t;

   int bootloader_update(const firmware_t *new_fw) {
       firmware_t *current_fw = (firmware_t *)FLASH_BASE;

       // Prevent downgrade below minimum version
       if (new_fw->version < current_fw->min_version) {
           return ERROR_ROLLBACK_PREVENTED;
       }

       // Additional checks...
       return flash_write(new_fw);
   }
   ```

3. **Debug Interface Protection**
   ```c
   // CRITICAL: Debug interfaces in production

   // Check for:

   - JTAG/SWD enabled in production

   - Debug UART with shell access

   - Backdoor commands for testing

   // SAFE: Disable debug in production
   #ifdef PRODUCTION_BUILD
       // Disable JTAG/SWD
       DBGMCU->CR = 0;

       // Disable debug features
       #define DEBUG_UART_ENABLE 0
   #else
       #define DEBUG_UART_ENABLE 1
   #endif

   // Or use hardware write-protection
   // Program option bytes to disable debug after production
   ```

## Phase 6: Side-Channel & Physical Attacks

1. **Timing Attacks**
   ```c
   // VIOLATION: Timing-dependent comparison
   int verify_password(const char *input) {
       const char *correct = "secret";
       // CRITICAL: Early exit reveals information
       for (int i = 0; correct[i]; i++) {
           if (input[i] != correct[i]) {
               return 0;  // Timing leak
           }
       }
       return 1;
   }

   // SAFE: Constant-time comparison
   int verify_password(const char *input, size_t len) {
       const char *correct = "secret";
       const size_t correct_len = 6;

       if (len != correct_len) {
           // Still compare to prevent timing leak
           len = correct_len;
       }

       volatile uint8_t diff = 0;
       for (size_t i = 0; i < correct_len; i++) {
           diff |= (input[i] ^ correct[i]);
       }

       return (diff == 0);
   }
   ```

2. **Power Analysis Protection**
   ```c
   // Consider power analysis attacks for critical operations

   // Countermeasures:

   - Random delays during crypto operations

   - Dummy operations to mask power signature

   - Hardware crypto engine (constant power)

   void protected_crypto(void) {
       // Random delay
       delay_us(get_random() % 100);

       // Actual crypto operation
       aes_encrypt(data, key);

       // Dummy operation
       if (get_random() & 1) {
           dummy_operation();
       }
   }
   ```

3. **Fault Injection Protection**
   ```c
   // VIOLATION: Single authentication check
   if (verify_signature(data, sig)) {
       grant_access();
   }

   // BETTER: Redundant checks
   bool auth1 = verify_signature(data, sig);
   bool auth2 = verify_signature(data, sig);

   if (auth1 && auth2 && (auth1 == auth2)) {
       grant_access();
   }

   // Also check for impossible values
   if (auth_result != AUTH_PASS && auth_result != AUTH_FAIL) {
       // Possible fault injection detected
       security_fault_handler();
   }
   ```

## Phase 7: Race Conditions & Concurrency

1. **Interrupt Race Conditions**
   ```c
   // VIOLATION: Non-atomic access
   volatile uint32_t g_counter = 0;

   void main_loop(void) {
       g_counter++;  // CRITICAL: Not atomic on multi-instruction operations
   }

   void interrupt_handler(void) {
       g_counter++;  // Race condition with main loop
   }

   // SAFE: Atomic access or protection
   void main_loop(void) {
       __disable_irq();
       g_counter++;
       __enable_irq();
   }

   // Or use atomic operations (C11)
   _Atomic uint32_t g_counter = 0;
   atomic_fetch_add(&g_counter, 1);
   ```

2. **TOCTOU (Time-of-Check-Time-of-Use)**
   ```c
   // VIOLATION: Check then use
   if (buffer_available()) {
       data_t value = read_buffer();  // CRITICAL: Buffer state could change
       process(value);
   }

   // SAFE: Atomic check and use
   int result = read_buffer_safe(&value);
   if (result == SUCCESS) {
       process(value);
   }
   ```

## Output Format

Please provide a comprehensive security report with the following structure:

### Executive Summary

- **Overall Security Risk**: [Critical/High/Medium/Low]

- **Critical Vulnerabilities**: [count] - MUST FIX IMMEDIATELY

- **High-Risk Issues**: [count]

- **CWE Top 25 Issues**: [count and types]

- **Exploitability**: [Remote/Local/Physical access required]

### Critical Findings (Severity: CRITICAL)
| CWE | Vulnerability | Location | CVSS | Description | Remediation | Effort |
|-----|---------------|----------|------|-------------|-------------|--------|
| [CWE-119] | [Buffer overflow] | [file:line] | [9.8] | [details] | [fix] | [hours] |

### High-Risk Findings (Severity: HIGH)
| CWE | Issue | Location | Risk | Description | Remediation |
|-----|-------|----------|------|-------------|-------------|
| [CWE-476] | [NULL deref] | [file:line] | [High] | [details] | [fix] |

### Medium-Risk Findings (Severity: MEDIUM)
[Brief list with locations and remediation summary]

### Low-Risk Findings (Severity: LOW)
[Brief list with locations and improvement suggestions]

### CWE Top 25 Assessment
| CWE | Name | Status | Issues Found | Risk Level |
|-----|------|--------|--------------|------------|
| CWE-119 | Buffer Overflow | [Pass/Fail] | [count] | [Critical/High] |
| CWE-120 | Buffer Copy without Check | [Pass/Fail] | [count] | [Critical/High] |
| CWE-125 | Out-of-bounds Read | [Pass/Fail] | [count] | [High/Med] |
| CWE-787 | Out-of-bounds Write | [Pass/Fail] | [count] | [Critical] |
| CWE-190 | Integer Overflow | [Pass/Fail] | [count] | [High/Med] |
| [... Top 25 CWEs] | | | | |

### Memory Safety Analysis

- **Buffer Overflows**: [count and locations]

- **Stack Overflows**: [risk level and evidence]

- **NULL Pointer Dereferences**: [count]

- **Use-After-Free**: [if heap used, count]

- **Integer Overflows**: [count]

### Input Validation Assessment

- **External Input Points**: [count]

- **Validated Inputs**: [count and %]

- **Missing Validation**: [locations]

- **Unsafe String Operations**: [count using strcpy, sprintf, etc.]

### Cryptography Security

- **Weak Algorithms**: [list if found]

- **Hardcoded Keys**: [count and locations] - CRITICAL

- **RNG Quality**: [Hardware/PRNG/Weak]

- **Key Storage**: [Secure/Insecure]

- **Crypto Library**: [mbedTLS/WolfSSL/Custom/None]

### Firmware Update Security

- **Signature Verification**: [Implemented/Missing]

- **Rollback Protection**: [Yes/No]

- **Secure Boot**: [Yes/No]

- **Debug Interface Protection**: [Production-safe/Exposed]

### Race Conditions & Concurrency

- **Shared Resource Access**: [Protected/Unprotected]

- **Interrupt Safety**: [Safe/Issues found]

- **Atomic Operations**: [Proper/Improper usage]

### Compiler Security Posture
| Security Feature | Status | Notes |
|------------------|--------|-------|
| Stack Protection | [Enabled/Disabled] | [-fstack-protector-strong] |
| FORTIFY_SOURCE | [Enabled/Disabled] | [-D_FORTIFY_SOURCE=2] |
| Format Security | [Enabled/Disabled] | [-Wformat-security] |
| NX Stack | [Enabled/Disabled] | [-z,noexecstack] |

### Attack Surface Analysis

- **Remote Attack Vectors**: [network, wireless, etc.]

- **Local Attack Vectors**: [USB, UART, debug interfaces]

- **Physical Attack Vectors**: [JTAG, side-channel, fault injection]

### Immediate Action Items (Priority 1)
1. **[Critical Buffer Overflow in parse_packet()]**

   - **Location**: protocol.c:145

   - **CWE**: CWE-119

   - **Fix**: Add length validation before memcpy

   - **Time Estimate**: 2 hours

   - **Risk if Not Fixed**: Remote code execution

### Short-term Actions (Priority 2 - within 1 week)
[List of high-priority security improvements]

### Medium-term Actions (Priority 3 - within 1 month)
[List of medium-priority security enhancements]

### Long-term Security Improvements (Priority 4 - strategic)
[List of architectural security improvements]

### Security Testing Recommendations
```c
// Recommended security testing:

1. Fuzzing:

   - Protocol parsers

   - Input handlers

   - Bootloader

2. Static Analysis (automated in CI):

   - Flawfinder

   - Cppcheck with CERT addon

   - SonarQube

3. Dynamic Analysis:

   - JTAG debugging with deliberate faults

   - Power analysis (if high-security device)

   - Side-channel testing

4. Penetration Testing:

   - External interfaces (UART, network, USB)

   - Firmware update mechanism

   - Debug interface access
```

### Secure Development Recommendations
1. Enable all compiler security flags

2. Use static analysis in CI pipeline

3. Conduct security code reviews for all changes

4. Implement secure coding training for team

5. Follow CERT-C secure coding standard

6. Use memory-safe string functions

7. Implement defense in depth

### Positive Security Practices
Acknowledge what's done well:

- [Good practice observed]

- [Effective security measure implemented]

### Next Steps

- [ ] Fix all critical vulnerabilities IMMEDIATELY

- [ ] Enable compiler security flags

- [ ] Implement input validation on all external interfaces

- [ ] Add firmware signature verification

- [ ] Disable debug interfaces in production builds

- [ ] Conduct penetration testing after fixes

- [ ] Establish secure development lifecycle

## Notes

- **Confidentiality**: This security report contains sensitive vulnerability information

- **Responsible Disclosure**: If third-party library issues found, follow disclosure process

- **Retest**: After remediation, rerun security scans and penetration tests

- **Continuous Monitoring**: Implement ongoing security scanning in CI/CD

- **Threat Modeling**: Consider device-specific threats (automotive, medical, IoT, etc.)

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/security_review/analysis_scripts
mkdir -p ${OUTPUT_DIR}/security_review/supporting_data
```

**Save files as follows**:

- Main report → `review/security_review/security_review_report.md`

- Findings data → `review/security_review/security_review_findings.json`

- Analysis scripts → `review/security_review/analysis_scripts/`

- Supporting data → `review/security_review/supporting_data/`
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
