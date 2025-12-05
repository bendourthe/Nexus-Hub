---
template_id: python_security_review
template_name: Security Review - Python
version: 1.0.0
last_updated: 2025-12-03
language: Python
category: code_review
phase: security_review
phase_number: 3
difficulty: advanced
estimated_time_hours: 2-3
prerequisites:

  - code_review/code_quality/python_code_quality.md
related_templates:

  - code_review/code_quality/python_code_quality.md
tools:

  - pytest (8.3.4+)
  - black (24.12.0)
  - mypy (1.13.0)
  - ruff
tags:

  - code-review
  - security
  - code-review
  - python
---
# Python Security Review

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

- [ ] XSS (Cross-Site Scripting) vulnerabilities checked

- [ ] CSRF (Cross-Site Request Forgery) protection verified

- [ ] Command injection points evaluated

- [ ] Path traversal vulnerabilities tested

### Dependency Security

- [ ] All dependencies scanned for known vulnerabilities (CVEs)

- [ ] Outdated packages with security patches identified

- [ ] Dependency chain analyzed for transitive vulnerabilities

- [ ] License compliance verified

- [ ] Supply chain risks assessed

### Authentication & Authorization

- [ ] Authentication mechanisms reviewed (passwords, tokens, OAuth)

- [ ] Password storage security verified (hashing, salting)

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

- [ ] .env files and configuration security checked

### Input Validation & Sanitization

- [ ] User input validation comprehensiveness assessed

- [ ] Input sanitization for SQL/command injection verified

- [ ] File upload restrictions evaluated

- [ ] API input validation checked

- [ ] Deserialization security reviewed (pickle, yaml)

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
# Python Security Review

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

Please perform a comprehensive security review of this Python project following this protocol:

## Phase 1: Automated Vulnerability Scanning

1. **Dependency Vulnerability Scan**
   ```bash
   # Scan for known vulnerabilities in dependencies
   pip-audit
   # or
   safety check --json

   # Check for outdated packages
   pip list --outdated
   ```

2. **Static Security Analysis**
   ```bash
   # Run Bandit security linter
   bandit -r . -f json -o ${OUTPUT_DIR}/exports/bandit_report.json

   # Or run with verbose output
   bandit -r . -ll -i
   ```

3. **Secret Detection**
   ```bash
   # Scan for hardcoded secrets
   detect-secrets scan --all-files --force-use-all-plugins

   # Or use truffleHog
   truffleHog filesystem . --json
   ```

## Phase 2: OWASP Top 10 Assessment

For each OWASP vulnerability category, systematically review the codebase:

1. **A01: Broken Access Control**
   - Review authorization logic in all endpoints/routes
   - Check for missing authorization checks
   - Verify user cannot access resources beyond permissions
   - Test for horizontal/vertical privilege escalation
   - Example locations: API endpoints, view functions, resource access

2. **A02: Cryptographic Failures**
   - Search for weak hashing algorithms (MD5, SHA1)
   - Verify HTTPS/TLS usage for sensitive data transmission
   - Check database encryption for sensitive fields
   - Review password storage (should use bcrypt, argon2, scrypt)
   - Identify sensitive data in logs or error messages

3. **A03: Injection**
   - **SQL Injection**: Verify parameterized queries (SQLAlchemy, psycopg2)
   - **Command Injection**: Check `os.system()`, `subprocess` with user input
   - **LDAP/NoSQL Injection**: Review query construction
   - **Template Injection**: Check template rendering with user data
   - Search patterns:
     ```python
     # Dangerous patterns
     cursor.execute("SELECT * FROM users WHERE id = " + user_id)
     os.system(f"ping {user_input}")
     eval(user_input)
     exec(code_string)
     ```

4. **A04: Insecure Design**
   - Review architecture for security anti-patterns
   - Assess threat modeling evidence
   - Check security requirements in design docs
   - Evaluate secure development lifecycle integration

5. **A05: Security Misconfiguration**
   - Check for debug mode in production
   - Review default credentials or configurations
   - Verify error messages don't leak sensitive information
   - Check for exposed admin interfaces
   - Review CORS configuration
   - Assess security headers (CSP, HSTS, X-Frame-Options)

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
   - Assess deserialization security (pickle, yaml.unsafe_load)
   - Verify update mechanisms security

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
    - Verify allowlist/blocklist for external requests

## Phase 3: Authentication & Authorization Deep Dive

1. **Password Security**
   ```python
   # Search for weak password handling
   # Good: Using bcrypt/argon2
   import bcrypt
   hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

   # Bad: Plain text or weak hashing
   if user.password == input_password:  # CRITICAL
   hashlib.md5(password.encode())  # CRITICAL
   ```

2. **Session Management**
   - Check session token generation (cryptographically secure random)
   - Verify session expiration and timeout
   - Review session fixation protection
   - Check for session data exposure

3. **Authorization Patterns**
   - Verify authorization checks on all protected resources
   - Check for missing decorators/middleware
   - Review role/permission enforcement
   - Test for privilege escalation paths

## Phase 4: Data Protection Review

1. **Sensitive Data Identification**
   - Identify PII (names, emails, addresses, phone numbers)
   - Locate financial data (credit cards, bank accounts)
   - Find health information (PHI/medical data)
   - Document authentication credentials

2. **Encryption Assessment**
   ```python
   # Check for proper encryption usage
   # Good: Using cryptography library
   from cryptography.fernet import Fernet

   # Bad: Custom crypto or weak algorithms
   # base64 is encoding, not encryption!
   base64.b64encode(secret_data)  # WARNING
   ```

3. **Data Exposure Risks**
   - Search for sensitive data in:
     - Exception messages and stack traces
     - Log files
     - Debug output
     - API responses
     - Database queries visible in logs

## Phase 5: Input Validation & Sanitization

1. **SQL Injection Protection**
   ```python
   # Review all database queries
   # Good: Parameterized queries
   cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
   User.query.filter_by(id=user_id).first()

   # Bad: String concatenation
   cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # CRITICAL
   ```

2. **Command Injection Protection**
   ```python
   # Review subprocess and os calls
   # Good: List arguments, avoid shell=True
   subprocess.run(['ping', '-c', '1', host])

   # Bad: Shell=True with user input
   subprocess.run(f'ping {user_host}', shell=True)  # CRITICAL
   os.system(user_command)  # CRITICAL
   ```

3. **Deserialization Security**
   ```python
   # Check for unsafe deserialization
   # Bad: pickle with untrusted data
   pickle.loads(user_data)  # CRITICAL
   yaml.load(user_input)  # Use yaml.safe_load()
   eval(user_code)  # CRITICAL
   exec(user_script)  # CRITICAL
   ```

4. **File Upload Security**
   - Check file type validation (not just extension)
   - Verify file size limits
   - Review file storage location (outside web root)
   - Check for malicious file content scanning

## Phase 6: Secrets Management

1. **Hardcoded Secrets Search**
   ```bash
   # Search for common secret patterns
   grep -r "password\s*=\s*['\"]" .
   grep -r "api_key\s*=\s*['\"]" .
   grep -r "secret\s*=\s*['\"]" .
   grep -r "token\s*=\s*['\"]" .
   ```

2. **Configuration File Review**
   - Check .env files for secrets
   - Review config.py or settings.py
   - Verify secrets not in version control
   - Check .gitignore includes sensitive files

3. **Environment Variable Usage**
   - Verify secrets loaded from environment
   - Check for default/fallback secrets
   - Review environment variable naming

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

- **Authorization Coverage**: [percentage of endpoints protected]

- **Issues Identified**: [list of specific problems]

### Data Protection

- **Sensitive Data Inventory**: [types and locations]

- **Encryption at Rest**: [implemented/missing]

- **Encryption in Transit**: [TLS/HTTPS status]

- **PII Exposure Risks**: [high/medium/low and locations]

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

- pre-commit-hooks:
  - bandit (static security analysis)
  - detect-secrets (secret scanning)
  - safety (dependency vulnerabilities)

- CI/CD integration:
  - pip-audit in GitHub Actions
  - SAST tools (Semgrep, Snyk)
  - Dependency scanning (Dependabot, Renovate)
```

### Positive Security Practices
Acknowledge what's done well:

- [Good practice observed]

- [Effective security measure implemented]

## Phase 7: Modern Attack Vectors (2025)

### Supply Chain Security

**Dependency Attacks:**
- [ ] Dependency pinning with hash verification
  ```python
  # requirements.txt with hashes
  requests==2.32.0 --hash=sha256:abc123...
  ```
- [ ] Private package repository configuration (prevent dependency confusion)
- [ ] Typosquatting protection (check for similar package names)
  - Example: "requets" instead of "requests"
- [ ] SBOM (Software Bill of Materials) generation
  ```bash
  pip-audit --format json > sbom.json
  ```
- [ ] License compliance check (GPL, LGPL, Apache, MIT compatibility)
  ```bash
  pip-licenses --format=markdown
  ```

**Package Integrity:**
- [ ] Use `pip install --require-hashes` for production deployments
- [ ] Verify package signatures when available
- [ ] Monitor for package maintainer changes
- [ ] Check for unusual package update patterns

**Tools:**
- `pip-audit` - Vulnerability scanning
- `safety` - Dependency vulnerability checker
- `dependabot` / `renovate` - Automated dependency updates
- `oss-review-toolkit` - Comprehensive supply chain analysis

### CI/CD Security

**GitHub Actions Security:**
- [ ] Secrets handling - never log secrets
  ```yaml
  - name: Use secret
    run: echo "${{ secrets.API_KEY }}" | base64  # BAD - logs secret
    # GOOD - use secret directly in commands without echo
  ```
- [ ] PR title/body injection prevention
  ```yaml
  # BAD - injects user input
  - run: echo "PR title: ${{ github.event.pull_request.title }}"

  # GOOD - validate input first
  - name: Validate PR title
    run: |
      title="${{ github.event.pull_request.title }}"
      if [[ "$title" =~ [^\w\s\-] ]]; then
        echo "Invalid characters in PR title"
        exit 1
      fi
  ```
- [ ] Artifact signing and verification (sigstore, cosign)
  ```yaml
  - uses: sigstore/gh-action-sigstore-python@v1
    with:
      inputs: ./dist/*
  ```
- [ ] OIDC token usage vs long-lived credentials
  ```yaml
  permissions:
    id-token: write  # Required for OIDC
  ```
- [ ] Branch protection rules (require reviews, status checks)
- [ ] Workflow approval for external contributors

**GitLab CI Security:**
- [ ] Protected variables for sensitive data
- [ ] Pipeline approval requirements
- [ ] Security scanning jobs (SAST, dependency scanning)

**Jenkins Security:**
- [ ] Credential binding for secrets
- [ ] Restricted job permissions
- [ ] Audit logging enabled

### Container Security (if applicable)

**Image Security:**
- [ ] Base image vulnerabilities (use slim/alpine variants)
  ```dockerfile
  # BAD
  FROM python:3.12

  # GOOD
  FROM python:3.12-slim
  ```
- [ ] Running as non-root user
  ```dockerfile
  USER nobody
  ```
- [ ] Image scanning before deployment
  ```bash
  trivy image myapp:latest
  grype myapp:latest
  ```

**Secrets in Layers:**
- [ ] No secrets in container layers (use multi-stage builds)
  ```dockerfile
  # Multi-stage build to avoid secrets in final image
  FROM python:3.12 AS builder
  ARG GIT_TOKEN
  RUN git clone https://${GIT_TOKEN}@github.com/...

  FROM python:3.12-slim
  COPY --from=builder /app /app
  # GIT_TOKEN not in final image
  ```
- [ ] Use `.dockerignore` to exclude sensitive files
  ```
  .env
  secrets/
  credentials.json
  *.pem
  *.key
  ```

**Runtime Security:**
- [ ] Read-only root filesystem when possible
  ```yaml
  # Kubernetes
  securityContext:
    readOnlyRootFilesystem: true
  ```
- [ ] Drop unnecessary Linux capabilities
- [ ] Network policies to restrict traffic

**Tools:**
- `trivy` - Container vulnerability scanner
- `grype` - Container security scanner
- `snyk` - Container and dependency scanning
- `docker scan` - Built-in Docker scanning

### AI/LLM Security (if applicable)

**Prompt Injection:**
- [ ] Input validation for user prompts
  ```python
  def validate_prompt(user_input: str) -> str:
      # Remove common injection patterns
      blocked_patterns = [
          "ignore previous",
          "disregard above",
          "new instructions",
      ]
      for pattern in blocked_patterns:
          if pattern in user_input.lower():
              raise ValueError("Invalid prompt detected")
      return user_input
  ```
- [ ] Sandboxing for AI-generated code execution
- [ ] Output validation and sanitization
  ```python
  def sanitize_ai_output(output: str) -> str:
      # Remove potential script tags, SQL, etc.
      import bleach
      return bleach.clean(output, tags=[], strip=True)
  ```

**Training Data Privacy:**
- [ ] PII detection in training data
- [ ] Data anonymization before training
- [ ] Consent management for data usage

**Model Security:**
- [ ] API rate limiting to prevent model theft
  ```python
  from slowapi import Limiter
  limiter = Limiter(key_func=get_remote_address)

  @app.route("/api/generate")
  @limiter.limit("10/minute")
  def generate():
      ...
  ```
- [ ] Watermarking AI-generated content
- [ ] Model access control and authentication

**Cost Control:**
- [ ] Token limits per request
- [ ] Budget alerts for API usage
- [ ] Caching to reduce API calls

### Cloud-Specific Security

**AWS:**
- [ ] IAM role least privilege (avoid wildcard permissions)
- [ ] S3 bucket policies (block public access)
- [ ] CloudTrail logging enabled
- [ ] Secrets Manager for credentials (not hardcoded)
- [ ] Security Groups restrictive (not 0.0.0.0/0)

**Azure:**
- [ ] Managed identities for authentication
- [ ] Key Vault for secrets
- [ ] Network security groups configured
- [ ] Azure Security Center recommendations

**GCP:**
- [ ] Service accounts with minimal permissions
- [ ] Secret Manager integration
- [ ] VPC firewall rules
- [ ] Security Command Center monitoring

### Modern Threat Patterns

**API Security:**
- [ ] GraphQL query depth/complexity limits (prevent DoS)
- [ ] REST API versioning (prevent breaking changes)
- [ ] Webhook signature verification
  ```python
  import hmac
  import hashlib

  def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
      expected = hmac.new(
          secret.encode(),
          payload,
          hashlib.sha256
      ).hexdigest()
      return hmac.compare_digest(expected, signature)
  ```

**Frontend Security:**
- [ ] Content Security Policy (CSP) headers
  ```python
  @app.after_request
  def set_csp(response):
      response.headers['Content-Security-Policy'] = (
          "default-src 'self'; "
          "script-src 'self' 'unsafe-inline'; "
          "style-src 'self' 'unsafe-inline';"
      )
      return response
  ```
- [ ] Subresource Integrity (SRI) for CDN resources
- [ ] HTTPS-only cookies

**Zero Trust Architecture:**
- [ ] Service-to-service authentication
- [ ] Mutual TLS (mTLS) between services
- [ ] Short-lived credentials (rotate frequently)

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
