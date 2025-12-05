---
template_id: go_security_review
template_name: Security Review - Go
version: 1.0.0
last_updated: 2025-12-03
language: Go
category: code_review
phase: security_review
phase_number: 3
difficulty: advanced
estimated_time_hours: 2-3
prerequisites:

  - code_review/code_quality/go_code_quality.md
related_templates:

  - code_review/code_quality/go_code_quality.md
tools:

  - go test (1.23+)
  - testify
tags:

  - code-review
  - security
  - code-review
  - go
---
# Go Security Review

## Objective
Systematically identify security vulnerabilities, insecure coding practices, and compliance gaps that could expose the application to attacks, data breaches, or regulatory violations.

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

### Vulnerability Assessment

- [ ] OWASP Top 10 vulnerabilities assessed

- [ ] SQL injection vectors identified

- [ ] Command injection points evaluated

- [ ] Path traversal vulnerabilities tested

- [ ] XML/JSON injection points checked

- [ ] Buffer overflow risks assessed (CGO usage)

### Dependency Security

- [ ] All dependencies scanned for known vulnerabilities (CVEs)

- [ ] Outdated packages with security patches identified

- [ ] Dependency chain analyzed for transitive vulnerabilities

- [ ] License compliance verified

- [ ] Supply chain risks assessed

### Authentication & Authorization

- [ ] Authentication mechanisms reviewed (JWT, OAuth, session tokens)

- [ ] Password storage security verified (bcrypt, argon2)

- [ ] Session management evaluated

- [ ] Authorization logic checked for privilege escalation

- [ ] Role-based access control (RBAC) implementation reviewed

- [ ] API authentication security assessed

### Data Protection

- [ ] Sensitive data encryption verified (at rest and in transit)

- [ ] Personally Identifiable Information (PII) handling reviewed

- [ ] Data exposure in logs/errors evaluated

- [ ] Database security assessed (parameterized queries, encryption)

- [ ] File upload security verified

- [ ] Data retention and deletion practices reviewed

### Secrets Management

- [ ] Hardcoded credentials searched and documented

- [ ] API keys and tokens in code identified

- [ ] Environment variable usage verified

- [ ] Secret management system evaluated

- [ ] Configuration file security checked

### Input Validation & Sanitization

- [ ] User input validation comprehensiveness assessed

- [ ] Input sanitization for SQL/command injection verified

- [ ] File upload restrictions evaluated

- [ ] API input validation checked

- [ ] JSON/XML parsing security reviewed

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
# Go Security Review

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

Please perform a comprehensive security review of this Go project following this protocol:

## Phase 1: Automated Vulnerability Scanning

1. **Dependency Vulnerability Scan**
   ```bash
   # Scan for known vulnerabilities in dependencies
   govulncheck ./...

   # Alternative: Nancy (Sonatype)
   go list -json -deps ./... | nancy sleuth

   # Check outdated dependencies
   go list -u -m all
   ```

2. **Static Security Analysis**
   ```bash
   # Run gosec security scanner
   gosec ./...

   # Or with detailed output
   gosec -fmt=json -out=results.json ./...

   # Run staticcheck with security focus
   staticcheck -checks="all,-ST1000" ./...
   ```

3. **Secret Detection**
   ```bash
   # Scan for hardcoded secrets
   trufflehog filesystem . --json

   # Or use gitleaks
   gitleaks detect --source . --verbose
   ```

## Phase 2: OWASP Top 10 Assessment

For each OWASP vulnerability category, systematically review the codebase:

1. **A01: Broken Access Control**
   - Review authorization logic in all HTTP handlers
   - Check for missing authorization checks
   - Verify users cannot access resources beyond permissions
   - Test for horizontal/vertical privilege escalation
   - Example locations: middleware, handlers, service layer

2. **A02: Cryptographic Failures**
   - Search for weak hashing algorithms (MD5, SHA1)
   - Verify TLS usage for sensitive data transmission
   - Check database encryption for sensitive fields
   - Review password storage (should use bcrypt, argon2, scrypt)
   - Identify sensitive data in logs or error messages

3. **A03: Injection**
   - **SQL Injection**: Verify parameterized queries
   ```go
   // Good: Parameterized query
   rows, err := db.Query("SELECT * FROM users WHERE id = ?", userID)

   // Bad: String concatenation
   query := "SELECT * FROM users WHERE id = " + userID // CRITICAL
   ```

   - **Command Injection**: Check `os/exec` usage
   ```go
   // Good: Separate arguments
   cmd := exec.Command("ping", "-c", "1", host)

   // Bad: Shell injection risk
   cmd := exec.Command("sh", "-c", "ping "+userHost) // CRITICAL
   ```

   - **Template Injection**: Check template rendering with user data
   - **LDAP/NoSQL Injection**: Review query construction

4. **A04: Insecure Design**
   - Review architecture for security anti-patterns
   - Assess threat modeling evidence
   - Check security requirements in design docs
   - Evaluate secure development lifecycle integration

5. **A05: Security Misconfiguration**
   - Check for debug mode in production
   - Review default configurations
   - Verify error messages don't leak sensitive information
   - Check for exposed admin interfaces
   - Review CORS configuration
   - Assess security headers (CSP, HSTS, X-Frame-Options)
   ```go
   // Check for:

   - Debug endpoints not protected
   - Stack traces in production
   - Verbose error messages
   - Default credentials
   ```

6. **A06: Vulnerable and Outdated Components**
   - Cross-reference dependency vulnerabilities from Phase 1
   - Identify components without security patches
   - Check for deprecated libraries
   - Review transitive dependency risks

7. **A07: Identification and Authentication Failures**
   - Review password complexity requirements
   - Check for weak session management
   - Verify multi-factor authentication implementation
   - Assess brute-force protection (rate limiting)
   - Check for authentication bypass vulnerabilities

8. **A08: Software and Data Integrity Failures**
   - Review CI/CD pipeline security
   - Check code signing and verification
   - Assess deserialization security (JSON, XML, gob)
   - Verify update mechanisms security
   ```go
   // Dangerous deserialization
   decoder := gob.NewDecoder(conn) // From untrusted source
   var data UserData
   decoder.Decode(&data) // RISKY
   ```

9. **A09: Security Logging and Monitoring Failures**
   - Assess logging comprehensiveness
   - Check for sensitive data in logs
   - Review log retention and protection
   - Verify alerting on suspicious activities
   - Check audit trail completeness

10. **A10: Server-Side Request Forgery (SSRF)**
    - Review URL handling and validation
    - Check for unvalidated redirects
    - Assess internal service requests
    - Verify allowlist for external requests

## Phase 3: Authentication & Authorization Deep Dive

1. **Password Security**
   ```go
   // Good: Using bcrypt
   import "golang.org/x/crypto/bcrypt"

   hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
   err = bcrypt.CompareHashAndPassword(hashedPassword, []byte(password))

   // Bad: Plain text or weak hashing
   if user.Password == inputPassword { // CRITICAL
   }

   hash := md5.Sum([]byte(password)) // CRITICAL - MD5 is broken
   ```

2. **Session Management**
   - Check session token generation (crypto/rand)
   ```go
   // Good: Cryptographically secure random
   import "crypto/rand"

   token := make([]byte, 32)
   rand.Read(token)

   // Bad: Predictable tokens
   token := fmt.Sprintf("%d", time.Now().Unix()) // CRITICAL
   ```
   - Verify session expiration and timeout
   - Review session fixation protection
   - Check for session data exposure

3. **Authorization Patterns**
   - Verify authorization checks on all protected resources
   - Check for missing middleware
   - Review role/permission enforcement
   - Test for privilege escalation paths

## Phase 4: Data Protection Review

1. **Sensitive Data Identification**
   - Identify PII (names, emails, addresses, phone numbers)
   - Locate financial data (credit cards, bank accounts)
   - Find health information (PHI/medical data)
   - Document authentication credentials

2. **Encryption Assessment**
   ```go
   // Good: Proper encryption
   import "crypto/aes"
   import "crypto/cipher"

   // Using standard crypto libraries

   // Bad: Custom crypto or weak algorithms
   import "encoding/base64"
   // base64 is encoding, not encryption!
   encoded := base64.StdEncoding.EncodeToString(secretData) // WARNING
   ```

3. **TLS Configuration**
   ```go
   // Good: Secure TLS configuration
   tlsConfig := &tls.Config{
       MinVersion:               tls.VersionTLS12,
       PreferServerCipherSuites: true,
       CipherSuites: []uint16{
           tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
           tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
       },
   }

   // Bad: Insecure TLS
   tlsConfig := &tls.Config{
       InsecureSkipVerify: true, // CRITICAL - Don't use in production
       MinVersion: tls.VersionTLS10, // CRITICAL - Too old
   }
   ```

4. **Data Exposure Risks**
   - Search for sensitive data in:
     - Error messages and stack traces
     - Log statements
     - Debug output
     - API responses
     - HTTP headers

## Phase 5: Input Validation & Sanitization

1. **SQL Injection Protection**
   ```go
   // Review all database queries
   // Good: Parameterized queries
   db.Query("SELECT * FROM users WHERE id = $1", userID)
   db.Exec("INSERT INTO users (name, email) VALUES ($1, $2)", name, email)

   // Bad: String formatting
   query := fmt.Sprintf("SELECT * FROM users WHERE id = %s", userID) // CRITICAL
   db.Query(query)
   ```

2. **Command Injection Protection**
   ```go
   // Review os/exec usage
   // Good: List arguments, avoid shell
   cmd := exec.Command("ls", "-la", userPath)

   // Bad: Shell with user input
   cmd := exec.Command("bash", "-c", "ls "+userPath) // CRITICAL
   os.System("rm " + userFile) // CRITICAL if available
   ```

3. **Path Traversal Prevention**
   ```go
   // Good: Clean and validate paths
   import "path/filepath"

   cleanPath := filepath.Clean(userPath)
   if !strings.HasPrefix(cleanPath, baseDir) {
       return errors.New("invalid path")
   }

   // Bad: Direct file access with user input
   file, err := os.Open(userPath) // RISKY without validation
   ```

4. **JSON/XML Parsing Security**
   ```go
   // Good: Limit decoder size
   decoder := json.NewDecoder(io.LimitReader(r.Body, 1048576)) // 1MB limit

   // Bad: Unbounded parsing
   var data interface{}
   json.Unmarshal(userInput, &data) // RISKY - could cause DoS
   ```

## Phase 6: Secrets Management

1. **Hardcoded Secrets Search**
   ```bash
   # Search for common secret patterns
   grep -r "password.*=.*\"" . --include="*.go"
   grep -r "api_key.*=.*\"" . --include="*.go"
   grep -r "secret.*=.*\"" . --include="*.go"
   grep -r "token.*=.*\"" . --include="*.go"
   ```

2. **Configuration File Review**
   - Check config files for secrets
   - Review environment variable usage
   - Verify secrets not in version control
   - Check .gitignore includes sensitive files

3. **Environment Variable Usage**
   ```go
   // Good: Load from environment
   apiKey := os.Getenv("API_KEY")
   if apiKey == "" {
       log.Fatal("API_KEY not set")
   }

   // Bad: Hardcoded
   const apiKey = "sk_live_abc123xyz" // CRITICAL
   ```

## Phase 7: Go-Specific Security Issues

1. **Race Conditions**
   ```bash
   # Always run with race detector
   go test -race ./...
   go build -race
   ```

2. **Type Confusion & Casting**
   ```go
   // Dangerous type assertions without checks
   value := data.(string) // RISKY - can panic

   // Safe type assertion
   value, ok := data.(string)
   if !ok {
       return errors.New("invalid type")
   }
   ```

3. **Integer Overflow**
   ```go
   // Be careful with integer operations
   // Check for overflow in arithmetic
   if size > math.MaxInt32 - offset {
       return errors.New("integer overflow")
   }
   ```

4. **Slice/Map Race Conditions**
   ```go
   // Concurrent map access
   var cache sync.Map // Use sync.Map for concurrent access

   // Or use mutex
   var mu sync.RWMutex
   var cache map[string]string
   ```

5. **CGO Security**
   - Review all CGO usage for buffer overflows
   - Check memory management in C code
   - Verify input validation at C boundaries

## Output Format

Please provide a comprehensive security report with the following structure:

### Executive Summary

- **Overall Security Risk**: [Critical/High/Medium/Low]

- **Critical Vulnerabilities**: [count]

- **High-Risk Issues**: [count]

- **Compliance Status**: [compliant/gaps identified]

- **Immediate Actions Required**: [yes/no and brief description]

### Critical Findings (Severity: CRITICAL)
| Issue | Location | CVSS Score | Description | Remediation |
|-------|----------|------------|-------------|-------------|
| [vulnerability] | [file:line] | [score] | [details] | [fix steps] |

### High-Risk Findings (Severity: HIGH)
| Issue | Location | Risk Level | Description | Remediation |
|-------|----------|------------|-------------|-------------|
| [vulnerability] | [file:line] | [High] | [details] | [fix steps] |

### Medium-Risk Findings (Severity: MEDIUM)
[Brief list with locations and remediation summary]

### Low-Risk Findings (Severity: LOW)
[Brief list with locations and improvement suggestions]

### OWASP Top 10 Assessment
| OWASP Category | Status | Issues Found | Risk Level |
|----------------|--------|--------------|------------|
| A01: Broken Access Control | [Pass/Fail] | [count] | [High/Med/Low] |
| A02: Cryptographic Failures | [Pass/Fail] | [count] | [High/Med/Low] |
| [... continue for all 10] | | | |

### Dependency Vulnerabilities
| Package | Current Version | Vulnerable | CVE | Severity | Fixed Version |
|---------|----------------|------------|-----|----------|---------------|
| [name] | [version] | [Yes/No] | [CVE-ID] | [Critical/High/Med/Low] | [version] |

### Secrets & Credentials Exposure

- **Hardcoded Secrets Found**: [count]

- **Locations**: [list of files and lines]

- **Types**: [API keys, passwords, tokens, etc.]

- **Git History Scan**: [secrets in commit history: yes/no]

### Authentication & Authorization

- **Password Storage**: [secure/insecure and method]

- **Session Management**: [secure/issues found]

- **Authorization Coverage**: [percentage of handlers protected]

- **Issues Identified**: [list of specific problems]

### Data Protection

- **Sensitive Data Inventory**: [types and locations]

- **Encryption at Rest**: [implemented/missing]

- **Encryption in Transit**: [TLS status and configuration]

- **PII Exposure Risks**: [high/medium/low and locations]

### Go-Specific Security Issues

- **Race Conditions**: [count from -race detector]

- **Unsafe Type Assertions**: [count and locations]

- **Integer Overflow Risks**: [locations]

- **CGO Security**: [issues if applicable]

### Compliance Assessment

- **GDPR**: [areas of concern]

- **HIPAA**: [if applicable, compliance status]

- **PCI DSS**: [if applicable, compliance status]

- **SOC 2**: [relevant findings]

### Immediate Action Items (Priority 1)
1. **[Critical Issue]**
   - **Location**: [file:line]
   - **Fix**: [specific remediation steps]
   - **Time Estimate**: [hours]
   - **Risk if Not Fixed**: [consequences]

### Short-term Actions (Priority 2 - within 1 week)
[List of high-priority items with remediation guidance]

### Medium-term Actions (Priority 3 - within 1 month)
[List of medium-priority improvements]

### Long-term Improvements (Priority 4 - strategic)
[List of systematic security enhancements]

### Security Tools Recommendations
```yaml
# Recommended security automation
pre-commit-hooks:

  - gosec (static security analysis)
  - gitleaks (secret scanning)
  - govulncheck (dependency vulnerabilities)

CI/CD integration:
  - gosec in GitHub Actions
  - govulncheck automated scanning
  - Dependency scanning (Dependabot, Renovate)
  - Container scanning (Trivy, Snyk)
```

```yaml
# Example GitHub Actions workflow
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
      - name: Run Gosec
        uses: securego/gosec@master
        with:
          args: './...'

      - name: Run govulncheck
        run: |
          go install golang.org/x/vuln/cmd/govulncheck@latest
          govulncheck ./...
```

### Positive Security Practices
Acknowledge what's done well:

- [Good practice observed]

- [Effective security measure implemented]

### Next Steps

- [ ] Remediate all critical vulnerabilities immediately

- [ ] Plan remediation sprints for high-risk issues

- [ ] Implement automated security scanning in CI/CD

- [ ] Conduct penetration testing after fixes

- [ ] Establish security code review process

- [ ] Provide security training for development team

## Notes

- **Confidentiality**: This security report contains sensitive information - handle appropriately

- **Responsible Disclosure**: If third-party vulnerabilities found, follow responsible disclosure

- **Retest**: After remediation, rerun security scans to verify fixes

- **Continuous Monitoring**: Implement ongoing security scanning and monitoring

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
