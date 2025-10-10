# C++ Security Review

## Objective
Systematically identify security vulnerabilities, memory safety issues, and insecure coding practices that could expose the application to attacks, crashes, data corruption, or exploitation. Focus on C++-specific vulnerabilities including memory safety, buffer overflows, and undefined behavior.

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

- [ ] Buffer overflow vulnerabilities identified

- [ ] Use-after-free vulnerabilities checked

- [ ] Double-free vulnerabilities assessed

- [ ] Memory leaks detected

- [ ] Null pointer dereferences identified

- [ ] Uninitialized memory usage checked

### Undefined Behavior

- [ ] Signed integer overflow checked

- [ ] Strict aliasing violations identified

- [ ] Out-of-bounds access detected

- [ ] Dangling references/pointers found

- [ ] Data races identified

- [ ] Undefined evaluation order issues

### Input Validation

- [ ] User input validation comprehensiveness assessed

- [ ] Buffer size validation verified

- [ ] Integer overflow in calculations checked

- [ ] Format string vulnerabilities identified

- [ ] Command injection vectors evaluated

### Sanitizer Testing

- [ ] AddressSanitizer (ASan) run completed

- [ ] UndefinedBehaviorSanitizer (UBSan) run completed

- [ ] ThreadSanitizer (TSan) run for concurrent code

- [ ] MemorySanitizer (MSan) run for uninitialized memory

- [ ] LeakSanitizer findings reviewed

### Cryptography

- [ ] Weak cryptographic algorithms identified

- [ ] Random number generation security assessed

- [ ] Cryptographic library usage reviewed

- [ ] Key management practices evaluated

- [ ] Secure data erasure verified

### Dependency Security

- [ ] All dependencies scanned for known vulnerabilities (CVEs)

- [ ] Outdated packages with security patches identified

- [ ] Dependency chain analyzed for transitive vulnerabilities

- [ ] License compliance verified

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Security Review

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

Please perform a comprehensive security review of this C++ project following this protocol:

## Phase 1: Automated Security Scanning

1. **Dependency Vulnerability Scan**
   ```bash
   # For vcpkg (check for known vulnerabilities manually)
   vcpkg list

   # For Conan
   conan search "*" --remote=all

   # Check CVE databases for each dependency
   # Use tools like OWASP Dependency-Check
   dependency-check --project "ProjectName" --scan ./
   ```

2. **Static Analysis Security Tools**
   ```bash
   # Run clang-tidy with security checks
   clang-tidy -checks='clang-analyzer-*,cert-*,bugprone-*' src/**/*.cpp

   # Run cppcheck with security focus
   cppcheck --enable=warning,style,performance,portability,information \
            --inconclusive --std=c++17 src/

   # Flawfinder for C/C++ security issues
   flawfinder src/

   # RATS (Rough Auditing Tool for Security)
   rats -w 3 src/
   ```

3. **Sanitizer Execution**
   ```bash
   # Build with AddressSanitizer
   cmake -DCMAKE_CXX_FLAGS="-fsanitize=address -fno-omit-frame-pointer" ..
   make
   ./run_tests

   # Build with UndefinedBehaviorSanitizer
   cmake -DCMAKE_CXX_FLAGS="-fsanitize=undefined -fno-omit-frame-pointer" ..
   make
   ./run_tests

   # Build with ThreadSanitizer (for multithreaded code)
   cmake -DCMAKE_CXX_FLAGS="-fsanitize=thread" ..
   make
   ./run_tests

   # Build with MemorySanitizer (Clang only)
   cmake -DCMAKE_CXX_FLAGS="-fsanitize=memory -fno-omit-frame-pointer" ..
   make
   ./run_tests
   ```

## Phase 2: Memory Safety Deep Dive

1. **Buffer Overflow Detection**
   ```cpp
   // Search for dangerous patterns
   // BAD: Fixed-size buffers with user input
   char buffer[100];
   scanf("%s", buffer);  // No bounds checking
   strcpy(buffer, user_input);  // No bounds checking
   gets(buffer);  // Never use - no bounds checking

   // BAD: Array indexing without bounds checking
   int arr[10];
   arr[user_index] = value;  // No validation of user_index

   // GOOD: Use std::string and std::vector
   std::string buffer;
   std::getline(std::cin, buffer);  // Safe

   std::vector<int> arr(10);
   if (user_index < arr.size()) {
       arr[user_index] = value;
   }

   // Check for:
   - C-style string functions (strcpy, strcat, sprintf)
   - Fixed-size buffers with unbounded input
   - Array access without bounds checking
   - Integer overflow in size calculations
   ```

2. **Use-After-Free Detection**
   ```cpp
   // Search for dangerous patterns
   // BAD: Use after free
   Widget* ptr = new Widget();
   delete ptr;
   ptr->method();  // Use-after-free

   // BAD: Dangling references
   Widget& getWidget() {
       Widget local;
       return local;  // Returns reference to local that will be destroyed
   }

   // BAD: Iterator invalidation
   std::vector<int> vec = {1, 2, 3};
   for (auto it = vec.begin(); it != vec.end(); ++it) {
       vec.push_back(*it);  // Reallocation invalidates iterators
   }

   // GOOD: RAII with smart pointers
   auto ptr = std::make_unique<Widget>();
   // Automatic cleanup, no use-after-free possible

   // Check for:
   - Manual delete followed by access
   - Returning references to locals
   - Iterator invalidation
   - Storing pointers/references to temporary objects
   ```

3. **Double-Free Detection**
   ```cpp
   // Search for dangerous patterns
   // BAD: Double free
   int* ptr = new int(42);
   delete ptr;
   delete ptr;  // Double free - undefined behavior

   // BAD: Deleting non-owning pointer
   int* ptr1 = new int(42);
   int* ptr2 = ptr1;
   delete ptr1;
   delete ptr2;  // Double free

   // GOOD: Smart pointers prevent double-free
   auto ptr = std::make_unique<int>(42);
   // Automatic cleanup, no double-free possible

   // Check for:
   - Multiple delete on same pointer
   - Deleting non-owning pointers
   - Missing copy/move constructor deletion
   ```

4. **Memory Leak Detection**
   ```cpp
   // Search for patterns that leak memory
   // BAD: Missing delete
   void function() {
       Widget* ptr = new Widget();
       if (error_condition) {
           return;  // Leak: ptr not deleted
       }
       delete ptr;
   }

   // BAD: Exception safety leak
   void function() {
       Widget* ptr1 = new Widget();
       Widget* ptr2 = new Widget();  // If this throws, ptr1 leaks
       // ...
       delete ptr1;
       delete ptr2;
   }

   // GOOD: RAII prevents leaks
   void function() {
       auto ptr = std::make_unique<Widget>();
       if (error_condition) {
           return;  // No leak: automatic cleanup
       }
   }

   // Check for:
   - new without corresponding delete
   - Resource acquisition without RAII
   - Exception safety issues
   - Missing cleanup in error paths
   ```

## Phase 3: Undefined Behavior Detection

1. **Integer Overflow**
   ```cpp
   // Check for integer overflow vulnerabilities
   // BAD: Unchecked arithmetic
   int size = user_input;
   int* buffer = new int[size];  // What if size is negative or huge?

   size_t total = width * height;  // Can overflow
   char* buffer = new char[total];

   // BAD: Signed integer overflow (undefined behavior)
   int a = INT_MAX;
   int b = a + 1;  // Undefined behavior

   // GOOD: Check for overflow
   if (width > SIZE_MAX / height) {
       throw std::overflow_error("Size calculation overflow");
   }
   size_t total = width * height;

   // Use SafeInt or similar for checked arithmetic
   SafeInt<size_t> safe_total = safe_width * safe_height;

   // Check for:
   - Arithmetic on user-controlled integers
   - Size calculations that can overflow
   - Array allocations with unchecked sizes
   - Signed integer overflow
   ```

2. **Null Pointer Dereference**
   ```cpp
   // Check for null pointer dereferences
   // BAD: No null check
   Widget* ptr = getWidget();
   ptr->method();  // What if getWidget() returned nullptr?

   // BAD: Dereferencing after delete
   delete ptr;
   ptr->method();  // Undefined behavior

   // GOOD: Check for null
   Widget* ptr = getWidget();
   if (ptr) {
       ptr->method();
   }

   // BETTER: Use references or smart pointers
   std::unique_ptr<Widget> ptr = getWidget();
   if (ptr) {
       ptr->method();
   }

   // Check for:
   - Dereferencing without null checks
   - Assumptions that pointers are valid
   - Missing validation of returned pointers
   ```

3. **Uninitialized Memory**
   ```cpp
   // Check for uninitialized variable usage
   // BAD: Uninitialized variables
   int value;
   if (value > 10) {  // Undefined behavior: value not initialized
       // ...
   }

   // BAD: Uninitialized arrays
   int buffer[100];
   for (int i = 0; i < 100; ++i) {
       process(buffer[i]);  // Undefined behavior if not all initialized
   }

   // GOOD: Initialize variables
   int value = 0;
   int value{};  // C++11 uniform initialization

   std::vector<int> buffer(100, 0);  // Initialized to 0

   // Use MemorySanitizer to detect uninitialized reads
   ```

4. **Data Races**
   ```cpp
   // Check for data races in concurrent code
   // BAD: Unsynchronized access
   class Counter {
       int count = 0;
   public:
       void increment() { ++count; }  // Race condition
       int get() const { return count; }
   };

   // GOOD: Proper synchronization
   class Counter {
       std::atomic<int> count{0};
   public:
       void increment() { count.fetch_add(1, std::memory_order_relaxed); }
       int get() const { return count.load(std::memory_order_relaxed); }
   };

   // Or use mutex
   class Counter {
       int count = 0;
       mutable std::mutex mtx;
   public:
       void increment() {
           std::lock_guard<std::mutex> lock(mtx);
           ++count;
       }
       int get() const {
           std::lock_guard<std::mutex> lock(mtx);
           return count;
       }
   };

   // Use ThreadSanitizer to detect data races
   ```

## Phase 4: Input Validation & Injection

1. **Command Injection**
   ```cpp
   // Check for command injection vulnerabilities
   // BAD: Unsanitized input to system()
   std::string filename = user_input;
   system(("rm " + filename).c_str());  // Command injection

   // BAD: Using popen with user input
   FILE* pipe = popen(user_command.c_str(), "r");

   // GOOD: Avoid system commands with user input
   // Use C++ filesystem library instead
   std::filesystem::remove(filename);

   // If system call necessary, sanitize and validate input
   if (std::regex_match(filename, std::regex("[a-zA-Z0-9._-]+"))) {
       // Safe: validated filename
   }
   ```

2. **Format String Vulnerabilities**
   ```cpp
   // Check for format string bugs
   // BAD: User-controlled format string
   printf(user_input);  // Format string vulnerability
   sprintf(buffer, user_input);

   // GOOD: Fixed format string
   printf("%s", user_input.c_str());
   std::cout << user_input;  // C++ streams are safe

   // Check for:
   - printf family with user-controlled format
   - sprintf family functions
   - Legacy C formatting functions
   ```

3. **SQL Injection (if using databases)**
   ```cpp
   // Check for SQL injection vulnerabilities
   // BAD: String concatenation for SQL
   std::string query = "SELECT * FROM users WHERE id = " + user_id;
   database.execute(query);

   // GOOD: Prepared statements/parameterized queries
   auto stmt = database.prepare("SELECT * FROM users WHERE id = ?");
   stmt.bind(1, user_id);
   stmt.execute();
   ```

4. **Path Traversal**
   ```cpp
   // Check for path traversal vulnerabilities
   // BAD: Unsanitized file paths
   std::string filename = user_input;
   std::ifstream file("/data/" + filename);  // Could be "../../../etc/passwd"

   // GOOD: Validate and sanitize paths
   std::filesystem::path base_path = "/data/";
   std::filesystem::path full_path = base_path / filename;
   full_path = std::filesystem::canonical(full_path);

   if (full_path.string().find(base_path.string()) != 0) {
       throw std::runtime_error("Path traversal attempt");
   }
   ```

## Phase 5: Cryptography & Secrets

1. **Weak Cryptographic Algorithms**
   ```cpp
   // Search for weak crypto
   // BAD: Weak hashing algorithms
   MD5, SHA1  // Cryptographically broken

   // BAD: Weak encryption
   DES, 3DES, RC4  // Weak or broken

   // GOOD: Strong algorithms
   SHA-256, SHA-3, BLAKE2
   AES-256-GCM, ChaCha20-Poly1305

   // Check for:
   - Use of MD5, SHA1 for security purposes
   - Use of DES, 3DES, RC4
   - Home-grown cryptography
   ```

2. **Random Number Generation**
   ```cpp
   // Check for weak random number generation
   // BAD: Predictable randomness
   srand(time(NULL));
   int random = rand();  // Not cryptographically secure

   // GOOD: Cryptographically secure random
   #include <random>
   std::random_device rd;
   std::mt19937 gen(rd());  // For non-security purposes

   // For security-critical random numbers
   // Use platform-specific secure random (Windows: BCryptGenRandom, Linux: /dev/urandom)
   ```

3. **Hardcoded Secrets**
   ```cpp
   // Search for hardcoded secrets
   // BAD: Hardcoded credentials
   const char* password = "admin123";
   const std::string api_key = "sk-1234567890abcdef";
   std::string secret = "my_secret_key";

   // Search patterns:
   grep -r "password\s*=\s*\"" src/
   grep -r "api[_-]?key" src/
   grep -r "secret" src/
   grep -r "token\s*=\s*\"" src/

   // GOOD: Load secrets from environment or secure storage
   const char* password = std::getenv("DB_PASSWORD");
   ```

4. **Secure Memory Erasure**
   ```cpp
   // Check for secure erasure of sensitive data
   // BAD: Not guaranteed to erase
   std::string password = get_password();
   password.clear();  // May be optimized away
   memset(&password[0], 0, password.size());  // May be optimized away

   // GOOD: Secure erasure
   #include <cstring>
   std::string password = get_password();
   std::memset_explicit(&password[0], 0, password.size());  // C23
   // or use explicit_bzero() on Unix
   // or use SecureZeroMemory() on Windows

   // Or use a secure string class that guarantees zeroing
   ```

## Phase 6: Concurrency & Thread Safety

1. **Data Race Detection**
   ```bash
   # Run with ThreadSanitizer
   cmake -DCMAKE_CXX_FLAGS="-fsanitize=thread -g" ..
   make
   ./run_tests
   ```

2. **Deadlock Risks**
   ```cpp
   // Check for deadlock patterns
   // BAD: Lock order issues
   std::mutex m1, m2;

   // Thread 1:
   std::lock_guard<std::mutex> lock1(m1);
   std::lock_guard<std::mutex> lock2(m2);

   // Thread 2:
   std::lock_guard<std::mutex> lock2(m2);  // Deadlock!
   std::lock_guard<std::mutex> lock1(m1);

   // GOOD: Use std::scoped_lock or std::lock
   std::scoped_lock lock(m1, m2);  // Deadlock-free
   ```

3. **Thread Safety**
   - Review shared state access
   - Verify proper synchronization
   - Check for race conditions
   - Identify lock-free algorithm issues

## Phase 7: OWASP Top 10 for C++

Adapt OWASP Top 10 to C++ context:

1. **Memory Corruption Vulnerabilities**
   - Buffer overflows
   - Use-after-free
   - Double-free
   - Type confusion

2. **Injection Flaws**
   - Command injection
   - SQL injection
   - Format string bugs

3. **Broken Authentication**
   - Weak password hashing
   - Insecure session management

4. **Sensitive Data Exposure**
   - Unencrypted sensitive data
   - Weak cryptography
   - Information leakage

5. **Security Misconfiguration**
   - Debug code in production
   - Unnecessary features enabled
   - Default credentials

## Output Format

Please provide a comprehensive security report with the following structure:

### Executive Summary

- **Overall Security Risk**: [Critical/High/Medium/Low]

- **Memory Safety Issues**: [count]

- **Critical Vulnerabilities**: [count]

- **High-Risk Issues**: [count]

- **Immediate Actions Required**: [yes/no and brief description]

### Critical Findings (Severity: CRITICAL)
| Issue | Location | Type | Description | Remediation |
|-------|----------|------|-------------|-------------|
| [vulnerability] | [file:line] | [Buffer overflow/UAF/etc] | [details] | [fix steps] |

### Sanitizer Results
**AddressSanitizer (ASan)**:

- Heap buffer overflows: [count]

- Stack buffer overflows: [count]

- Use-after-free: [count]

- Memory leaks: [count]

**UndefinedBehaviorSanitizer (UBSan)**:

- Signed integer overflow: [count]

- Null pointer dereference: [count]

- Misaligned access: [count]

- Other UB: [count]

**ThreadSanitizer (TSan)**:

- Data races: [count]

- Deadlocks: [count]

**MemorySanitizer (MSan)**:

- Uninitialized memory reads: [count]

### Memory Safety Assessment
**Buffer Overflows**:
| Location | Type | Severity | Fix |
|----------|------|----------|-----|
| [file:line] | [stack/heap] | [Critical/High] | [use std::vector/std::string] |

**Use-After-Free**:
| Location | Severity | Description | Fix |
|----------|----------|-------------|-----|
| [file:line] | [Critical] | [details] | [use smart pointers] |

**Memory Leaks**:
| Location | Leak Type | Size | Fix |
|----------|-----------|------|-----|
| [file:line] | [definite/possible] | [bytes] | [use RAII/smart pointers] |

### Undefined Behavior Issues
| Issue | Location | Severity | Description | Fix |
|-------|----------|----------|-------------|-----|
| [Integer overflow] | [file:line] | [High] | [details] | [add overflow checks] |

### Input Validation Issues

- **Command Injection Risks**: [count and locations]

- **Format String Bugs**: [count and locations]

- **Path Traversal Risks**: [count and locations]

- **SQL Injection Risks**: [count and locations]

### Cryptography Assessment

- **Weak Algorithms**: [list of MD5/SHA1/DES usage]

- **Weak Random**: [use of rand() for security]

- **Hardcoded Secrets**: [count and types]

- **Insecure Key Storage**: [issues found]

### Concurrency Issues

- **Data Races**: [count and locations from TSan]

- **Deadlock Risks**: [potential deadlock scenarios]

- **Race Conditions**: [logic-level races]

### Dependency Vulnerabilities
| Package | Version | CVE | Severity | Fixed Version |
|---------|---------|-----|----------|---------------|
| [name] | [version] | [CVE-ID] | [Critical/High/Med] | [version] |

### Compliance Assessment

- **CWE Top 25**: [compliance status]

- **CERT C++ Coding Standard**: [violations found]

- **MISRA C++ (if applicable)**: [violations]

### Immediate Action Items (Priority 1)
1. **[Critical Memory Safety Issue]**
   - **Location**: [file:line]
   - **Fix**: [specific remediation steps]
   - **Time Estimate**: [hours]
   - **Risk if Not Fixed**: [consequences]

### Short-term Actions (Priority 2 - within 1 week)
[List of high-priority security items with remediation guidance]

### Medium-term Actions (Priority 3 - within 1 month)
[List of medium-priority security improvements]

### Long-term Improvements (Priority 4 - strategic)
[List of systematic security enhancements]

### Security Tools Recommendations
```cmake
# Recommended sanitizer builds
# CMakeLists.txt
option(ENABLE_ASAN "Enable AddressSanitizer" OFF)
if(ENABLE_ASAN)
    add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address)
endif()

option(ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)
if(ENABLE_UBSAN)
    add_compile_options(-fsanitize=undefined)
    add_link_options(-fsanitize=undefined)
endif()

# CI/CD integration
# - Run ASan/UBSan/TSan builds in CI
# - Use static analyzers (clang-tidy, cppcheck)
# - Dependency vulnerability scanning
```

### Positive Security Practices
Acknowledge what's done well:

- Good use of RAII for resource management

- Smart pointers used consistently

- Proper input validation in [module]

### Next Steps

- [ ] Fix all critical memory safety issues immediately

- [ ] Run sanitizers regularly in CI/CD

- [ ] Implement automated security scanning

- [ ] Plan security remediation sprints

- [ ] Conduct penetration testing after fixes

- [ ] Establish secure coding guidelines for team

- [ ] Provide security training for development team

## Notes

- **Confidentiality**: This security report contains sensitive information - handle appropriately

- **Responsible Disclosure**: If third-party vulnerabilities found, follow responsible disclosure

- **Retest**: After remediation, rerun sanitizers and security scans to verify fixes

- **Continuous Monitoring**: Implement ongoing security scanning and fuzzing

- **Memory Safety**: Prioritize modern C++ patterns (RAII, smart pointers) over manual management

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
