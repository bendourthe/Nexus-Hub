---
name: security-review
description: Identify security vulnerabilities, OWASP Top 10 issues, supply chain risks, and compliance gaps. Use for security audits, penetration test preparation, vulnerability assessment, or as Phase 3 of comprehensive code review.
---

# Code Review - Security Review

Identify security vulnerabilities and risks in the codebase. This skill is **Phase 3** of the 6-phase code review methodology.

## When to Use This Skill

Use this skill when you need to:

- Conduct security audit
- Identify vulnerabilities
- Check OWASP Top 10 compliance
- Assess supply chain security
- Prepare for penetration testing
- Meet security compliance requirements

**Trigger phrases**: "security review", "vulnerability scan", "OWASP", "security audit", "penetration test prep", "CVE check", "security assessment"

## What This Skill Does

### OWASP Top 10 (2021)

| ID | Vulnerability | Focus |
|----|---------------|-------|
| A01 | Broken Access Control | Authorization, privilege escalation |
| A02 | Cryptographic Failures | Encryption, key management |
| A03 | Injection | SQL, XSS, command injection |
| A04 | Insecure Design | Architecture flaws |
| A05 | Security Misconfiguration | Defaults, hardening |
| A06 | Vulnerable Components | Dependencies, CVEs |
| A07 | Authentication Failures | Auth bypass, sessions |
| A08 | Data Integrity Failures | Deserialization, CI/CD |
| A09 | Logging Failures | Audit trails, monitoring |
| A10 | SSRF | Server-side request forgery |

### Severity Classification

- **CRITICAL**: Immediate exploit risk, data breach potential
- **HIGH**: Significant vulnerability requiring urgent fix
- **MEDIUM**: Security weakness to address
- **LOW**: Minor hardening improvement

## Instructions

### Step 1: Dependency Vulnerability Scan

```bash
# Python
pip-audit
safety check

# JavaScript
npm audit
snyk test

# Java
mvn dependency-check:check
```

### Step 2: Static Security Analysis

```bash
# Python
bandit -r src/

# JavaScript
npm audit
eslint --plugin security src/

# Java
spotbugs with find-sec-bugs
```

### Step 3: Manual Review Focus

1. **Input Validation**
   - User input sanitization
   - SQL parameterization
   - Command injection prevention

2. **Authentication/Authorization**
   - Password handling
   - Session management
   - Access control

3. **Data Protection**
   - Encryption at rest/transit
   - Sensitive data exposure
   - Secrets management

4. **Error Handling**
   - Information disclosure
   - Stack trace exposure

### Step 4: Document Findings

```markdown
## Security Finding

**Vulnerability**: SQL Injection
**File**: [path/to/file.py:42]
**Severity**: CRITICAL
**OWASP**: A03:2021 - Injection
**CVE**: [If applicable]

### Description
[Detailed description]

### Vulnerable Code
```python
query = f"SELECT * FROM users WHERE id = {user_id}"
```

### Remediation
```python
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

### References
- [OWASP Link]
```

## Common Vulnerabilities by Language

### Python
- SQL injection (raw queries)
- Command injection (subprocess)
- Pickle deserialization
- Insecure randomness

### JavaScript
- XSS (innerHTML, dangerouslySetInnerHTML)
- Prototype pollution
- Eval injection
- Path traversal

### Java
- SQL injection
- XXE (XML External Entity)
- Insecure deserialization
- Log injection

## Quality Checklist

- [ ] Dependency scan completed
- [ ] Static analysis run
- [ ] OWASP Top 10 reviewed
- [ ] Input validation checked
- [ ] Authentication reviewed
- [ ] Secrets management verified
- [ ] Findings documented with severity

## Related Skills

- `context-analysis` - Context understanding (Phase 1)
- `code-quality` - Code quality review (Phase 2)
- `dependency-security-audit` - Detailed CVE scanning
- `final-report` - Consolidated report (Phase 6)

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: AI Templates code_review/security_review/
