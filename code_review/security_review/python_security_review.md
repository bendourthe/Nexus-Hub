# Python Security Review

## Objective
Systematically identify security vulnerabilities, insecure coding practices, and compliance gaps that could expose the application to attacks, data breaches, or regulatory violations.

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

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Security Review

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
   bandit -r . -f json -o bandit_report.json

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
~~~
