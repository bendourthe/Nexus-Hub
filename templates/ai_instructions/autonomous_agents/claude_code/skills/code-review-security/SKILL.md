---
name: code-review-security
description: Systematically identify security vulnerabilities, insecure coding practices, and compliance gaps - assess authentication, authorization, data protection, and OWASP Top 10 vulnerabilities
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Code Review
tags: [code-review, security, vulnerabilities, workflow, phase-3]
priority: HIGH
based_on: AI Templates Code Review Workflow, Anthropic Claude Code Best Practices 2025
---

# Code Review Security Assessment

Systematically identify security vulnerabilities, insecure coding practices, and compliance gaps that could expose the application to attacks or data breaches. This skill is **Phase 3** of the complete code review workflow, examining authentication, authorization, data protection, dependency vulnerabilities, and adherence to security best practices.

## When to Use This Skill

Use this skill as **Phase 3** after completing context and quality reviews:

- ✅ After [Phase 1: Context Analysis](../code-review-context-analysis/SKILL.md) and [Phase 2: Quality Review](../code-review-quality/SKILL.md) complete

- ✅ Pre-production security audit

- ✅ Compliance assessment preparation

- ✅ Post-incident security hardening

- ✅ Third-party code integration review

- ✅ Open-source project security audit

- ✅ Regulatory compliance verification

- ✅ Penetration testing preparation

**This skill is essential when**:

- You need to identify OWASP Top 10 vulnerabilities

- You're auditing authentication and authorization

- You want to detect hardcoded secrets and credentials

- You're assessing data protection practices

- You need to comply with security standards

## What This Skill Does

This skill implements **Phase 3: Security Review** of the six-phase code review workflow:

### Complete Workflow
- Phase 1: [Context Analysis](../code-review-context-analysis/SKILL.md) - Project understanding

- Phase 2: [Quality Review](../code-review-quality/SKILL.md) - Code maintainability

- **Phase 3: Security Review (This Skill)** - Vulnerability identification

- Phase 4: [Performance Review](../code-review-performance/SKILL.md) - Bottleneck analysis

- Phase 5: [Testing Review](../code-review-testing/SKILL.md) - Test coverage evaluation

- Phase 6: [Final Report](../code-review-final-report/SKILL.md) - Consolidated findings

## Why Security Review Matters

**Without Security Review**:
```
Team: *deploys without security audit*
Application: *contains critical vulnerabilities*
Attackers: *exploit security gaps*
Result:

- ❌ Data breaches and unauthorized access

- ❌ Injection attacks compromise data

- ❌ Authentication bypass allows impersonation

- ❌ Sensitive data exposure causes compliance violations

- ❌ Financial and reputational damage

- ❌ Legal liability and regulatory fines
```

**With Security Review**:
```
Team: *performs comprehensive security audit*
Application: *vulnerabilities identified and fixed*
Attackers: *find hardened, secure application*
Result:

- ✅ Data protected from unauthorized access

- ✅ Injection attacks prevented

- ✅ Authentication properly enforced

- ✅ Sensitive data encrypted and protected

- ✅ Compliance requirements met

- ✅ Risk minimized, trust maintained
```

## Benefits of Security Review

### Risk Mitigation
- **Prevent Breaches**: Identify vulnerabilities before attackers do

- **Protect Data**: Ensure sensitive information stays secure

- **Maintain Trust**: Build confidence with users and stakeholders

- **Avoid Costs**: Prevent expensive breaches and remediation

### Compliance
- **Meet Standards**: Verify compliance with GDPR, HIPAA, PCI-DSS, SOC 2

- **Audit Readiness**: Prepare for security audits and assessments

- **Legal Protection**: Reduce legal liability and regulatory risk

- **Certifications**: Support security certification processes

### Security Culture
- **Education**: Teach developers secure coding practices

- **Awareness**: Build security mindset across the team

- **Continuous Improvement**: Establish ongoing security practices

- **Best Practices**: Implement industry-standard security patterns

## Prerequisites

### Required
- Completion of [Phase 1: Context Analysis](../code-review-context-analysis/SKILL.md) and [Phase 2: Quality Review](../code-review-quality/SKILL.md)

- Source code access

- Security scanning tools installed

- Understanding of OWASP Top 10

### Recommended
- Access to dependency vulnerability databases

- Secret scanning tools

- Static Application Security Testing (SAST) tools

- Dynamic Application Security Testing (DAST) tools

- Penetration testing experience

### Knowledge
- Common vulnerability types (injection, XSS, CSRF)

- Authentication and authorization patterns

- Cryptography best practices

- Secure coding principles

- Compliance requirements (GDPR, HIPAA, etc.)

## Instructions

### Step 1: Automated Vulnerability Scanning

**Run automated security tools to identify common vulnerabilities:**

1. **Dependency Vulnerability Scanning**

   **Python**:
   ```bash
   # Install scanning tools
   pip install pip-audit safety

   # Scan for known CVEs
   pip-audit

   # Alternative scanner
   safety check --json

   # Check for outdated packages with security fixes
   pip list --outdated
   ```

   **JavaScript/TypeScript**:
   ```bash
   # NPM audit
   npm audit --production
   npm audit fix --dry-run

   # Or with Yarn
   yarn audit

   # Snyk for comprehensive scanning
   npm install -g snyk
   snyk test
   ```

   **Java**:
   ```bash
   # OWASP Dependency-Check
   mvn dependency-check:check

   # Or with Gradle
   gradle dependencyCheckAnalyze
   ```

   **Go**:
   ```bash
   # Govulncheck for Go vulnerabilities
   go install golang.org/x/vuln/cmd/govulncheck@latest
   govulncheck ./...
   ```

   **C/C++**:
   ```bash
   # Cppcheck for security issues
   cppcheck --enable=warning,style,performance,portability,information src/

   # Flawfinder for C/C++ vulnerabilities
   flawfinder src/
   ```

   **C#**:
   ```bash
   # .NET security scanning
   dotnet list package --vulnerable --include-transitive
   ```

2. **Static Application Security Testing (SAST)**

   **Python**:
   ```bash
   # Bandit - Python security linter
   pip install bandit
   bandit -r . -f json -o security_report.json

   # Semgrep - multi-language security scanner
   pip install semgrep
   semgrep --config=auto .
   ```

   **JavaScript**:
   ```bash
   # ESLint with security plugins
   npm install eslint-plugin-security
   npx eslint . --ext .js,.ts

   # NodeJsScan for Node.js
   pip install nodejsscan
   nodejsscan .
   ```

   **Java**:
   ```bash
   # SpotBugs with security plugin
   mvn spotbugs:check

   # Find Security Bugs
   mvn com.github.spotbugs:spotbugs-maven-plugin:spotbugs
   ```

   **All Languages**:
   ```bash
   # Semgrep (supports multiple languages)
   semgrep --config=p/security-audit .
   semgrep --config=p/owasp-top-ten .
   ```

3. **Secret Detection**

   **All Languages**:
   ```bash
   # detect-secrets
   pip install detect-secrets
   detect-secrets scan --all-files --force-use-all-plugins

   # TruffleHog
   pip install truffleHog
   trufflehog filesystem . --json

   # GitLeaks (if Git repository)
   git clone https://github.com/gitleaks/gitleaks
   gitleaks detect --source . --verbose
   ```

### Step 2: OWASP Top 10 Assessment

**Systematically review for each OWASP vulnerability category:**

1. **A01: Broken Access Control**

   **What to Check**:

   - Authorization checks on all protected resources

   - User cannot access resources beyond permissions

   - No horizontal/vertical privilege escalation

   - Proper role-based access control (RBAC)

   **Python Example**:
   ```python
   # Bad: Missing authorization check
   @app.route('/admin/users/<int:user_id>')
   def view_user(user_id):
       user = User.query.get(user_id)
       return render_template('user.html', user=user)  # No auth check!

   # Good: Proper authorization
   @app.route('/admin/users/<int:user_id>')
   @login_required
   @admin_required
   def view_user(user_id):
       user = User.query.get_or_404(user_id)
       if not current_user.can_view_user(user):
           abort(403)
       return render_template('user.html', user=user)
   ```

   **JavaScript Example**:
   ```javascript
   // Bad: No authorization check
   app.get('/api/users/:id', async (req, res) => {
       const user = await User.findById(req.params.id);
       res.json(user);  // Anyone can view any user!
   });

   // Good: Authorization middleware
   app.get('/api/users/:id',
       authenticate,
       authorize('admin', 'self'),
       async (req, res) => {
           if (req.user.id !== req.params.id && !req.user.isAdmin) {
               return res.status(403).json({ error: 'Forbidden' });
           }
           const user = await User.findById(req.params.id);
           res.json(user);
       }
   );
   ```

   **Java Example**:
   ```java
   // Bad: Missing security annotation
   @GetMapping("/admin/users/{id}")
   public User getUser(@PathVariable Long id) {
       return userRepository.findById(id).orElseThrow();
   }

   // Good: Proper authorization
   @GetMapping("/admin/users/{id}")
   @PreAuthorize("hasRole('ADMIN') or #id == authentication.principal.id")
   public User getUser(@PathVariable Long id) {
       return userRepository.findById(id)
           .orElseThrow(() -> new ResourceNotFoundException("User not found"));
   }
   ```

2. **A02: Cryptographic Failures**

   **What to Check**:

   - No weak hashing algorithms (MD5, SHA1)

   - HTTPS/TLS for sensitive data transmission

   - Encrypted storage for sensitive data

   - Proper password hashing (bcrypt, argon2, scrypt)

   - No sensitive data in logs

   **Python Example**:
   ```python
   # Bad: Weak password hashing
   import hashlib
   password_hash = hashlib.md5(password.encode()).hexdigest()  # CRITICAL

   # Good: Strong password hashing
   import bcrypt
   password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

   # Bad: Sensitive data in logs
   logger.info(f"User logged in: {username} with password {password}")  # CRITICAL

   # Good: Safe logging
   logger.info(f"User logged in: {username}")
   ```

   **Go Example**:
   ```go
   // Bad: Using MD5
   import "crypto/md5"
   hash := md5.Sum([]byte(password))  // Insecure

   // Good: Using bcrypt
   import "golang.org/x/crypto/bcrypt"
   hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
   ```

   **C# Example**:
   ```csharp
   // Bad: Plain text password storage
   user.Password = password;  // CRITICAL

   // Good: Hashed password with salt
   using Microsoft.AspNetCore.Identity;
   var hasher = new PasswordHasher<User>();
   user.PasswordHash = hasher.HashPassword(user, password);
   ```

3. **A03: Injection**

   **SQL Injection**:

   **Python**:
   ```python
   # Bad: SQL injection vulnerability
   cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # CRITICAL

   # Good: Parameterized query
   cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

   # Good: ORM usage
   user = User.query.filter_by(id=user_id).first()
   ```

   **JavaScript**:
   ```javascript
   // Bad: SQL injection
   const query = `SELECT * FROM users WHERE email = '${email}'`;  // CRITICAL
   db.query(query);

   // Good: Parameterized query
   db.query('SELECT * FROM users WHERE email = ?', [email]);
   ```

   **Java**:
   ```java
   // Bad: SQL injection
   String query = "SELECT * FROM users WHERE name = '" + username + "'";  // CRITICAL
   Statement stmt = connection.createStatement();
   ResultSet rs = stmt.executeQuery(query);

   // Good: Prepared statement
   String query = "SELECT * FROM users WHERE name = ?";
   PreparedStatement pstmt = connection.prepareStatement(query);
   pstmt.setString(1, username);
   ResultSet rs = pstmt.executeQuery();
   ```

   **Command Injection**:

   **Python**:
   ```python
   # Bad: Command injection
   os.system(f"ping {user_input}")  # CRITICAL
   subprocess.call(f"ls {directory}", shell=True)  # CRITICAL

   # Good: Safe subprocess usage
   subprocess.run(['ping', '-c', '1', user_input], check=True)
   subprocess.run(['ls', directory], check=True)
   ```

   **C/C++**:
   ```c
   // Bad: Command injection
   char command[256];
   sprintf(command, "ls %s", user_input);  // CRITICAL
   system(command);

   // Good: Avoid system() with user input
   // Use safer APIs or validate/sanitize input thoroughly
   ```

4. **A04: Insecure Design**

   **What to Check**:

   - Security requirements in design documentation

   - Threat modeling evidence

   - Secure architecture patterns

   - Defense in depth implementation

5. **A05: Security Misconfiguration**

   **Python Example**:
   ```python
   # Bad: Debug mode in production
   app.config['DEBUG'] = True  # CRITICAL in production

   # Bad: Exposing error details
   @app.errorhandler(Exception)
   def handle_error(e):
       return str(e), 500  # Leaks implementation details

   # Good: Proper configuration
   app.config['DEBUG'] = False
   app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

   @app.errorhandler(Exception)
   def handle_error(e):
       logger.error(f"Error: {e}")
       return "Internal server error", 500
   ```

   **JavaScript Example**:
   ```javascript
   // Bad: CORS misconfiguration
   app.use(cors({ origin: '*' }));  // Allows any origin

   // Good: Restricted CORS
   app.use(cors({
       origin: process.env.ALLOWED_ORIGINS.split(','),
       credentials: true
   }));
   ```

6. **A06: Vulnerable and Outdated Components**

   Cross-reference findings from Step 1 dependency scanning:

   - Identify CVEs with CVSS score > 7.0

   - Check for available security patches

   - Assess transitive dependency risks

7. **A07: Identification and Authentication Failures**

   **Python Example**:
   ```python
   # Bad: Weak session management
   session['user_id'] = user.id
   # No timeout, no token rotation

   # Good: Secure session management
   from flask_login import login_user
   login_user(user, remember=False, duration=timedelta(hours=2))
   session.permanent = False
   session.modified = True

   # Bad: No rate limiting on login
   @app.route('/login', methods=['POST'])
   def login():
       user = authenticate(request.form['username'], request.form['password'])
       # No brute-force protection

   # Good: Rate limiting
   from flask_limiter import Limiter
   limiter = Limiter(app, key_func=lambda: request.remote_addr)

   @app.route('/login', methods=['POST'])
   @limiter.limit("5 per minute")
   def login():
       user = authenticate(request.form['username'], request.form['password'])
   ```

   **Java Example**:
   ```java
   // Bad: Weak password policy
   if (password.length() >= 6) {  // Too weak
       // Accept password
   }

   // Good: Strong password policy
   if (password.length() >= 12 &&
       password.matches(".*[A-Z].*") &&
       password.matches(".*[a-z].*") &&
       password.matches(".*\\d.*") &&
       password.matches(".*[!@#$%^&*].*")) {
       // Accept password
   }
   ```

8. **A08: Software and Data Integrity Failures**

   **Python Example**:
   ```python
   # Bad: Unsafe deserialization
   import pickle
   data = pickle.loads(user_input)  # CRITICAL - arbitrary code execution

   # Good: Safe deserialization
   import json
   data = json.loads(user_input)

   # Bad: Unsafe YAML loading
   import yaml
   config = yaml.load(user_input)  # Unsafe

   # Good: Safe YAML loading
   config = yaml.safe_load(user_input)
   ```

9. **A09: Security Logging and Monitoring Failures**

   **Python Example**:
   ```python
   # Bad: No security logging
   def login(username, password):
       user = authenticate(username, password)
       if user:
           return "Success"
       return "Failed"

   # Good: Security event logging
   import logging
   security_logger = logging.getLogger('security')

   def login(username, password):
       user = authenticate(username, password)
       if user:
           security_logger.info(f"Successful login: {username} from {request.remote_addr}")
           return "Success"
       else:
           security_logger.warning(f"Failed login attempt: {username} from {request.remote_addr}")
           return "Failed"
   ```

10. **A10: Server-Side Request Forgery (SSRF)**

    **Python Example**:
    ```python
    # Bad: SSRF vulnerability
    import requests
    url = request.args.get('url')
    response = requests.get(url)  # Can access internal services!

    # Good: URL validation
    from urllib.parse import urlparse

    ALLOWED_DOMAINS = ['api.example.com', 'cdn.example.com']

    url = request.args.get('url')
    parsed = urlparse(url)

    if parsed.netloc not in ALLOWED_DOMAINS:
        abort(403, "Domain not allowed")

    if parsed.scheme not in ['http', 'https']:
        abort(403, "Invalid scheme")

    response = requests.get(url, timeout=5)
    ```

### Step 3: Authentication & Authorization Deep Dive

**Conduct detailed review of authentication and authorization mechanisms:**

1. **Password Security Audit**

   Search for:

   - Plain text password storage

   - Weak hashing algorithms

   - Missing password complexity requirements

   - No password expiration policy

   - Password hints or recovery questions

2. **Session Management Review**

   Check for:

   - Secure session token generation (cryptographically random)

   - Session fixation protection

   - Session timeout and expiration

   - Secure cookie attributes (HttpOnly, Secure, SameSite)

   - Session invalidation on logout

   **Python Example**:
   ```python
   # Good: Secure cookie configuration
   app.config.update(
       SESSION_COOKIE_SECURE=True,
       SESSION_COOKIE_HTTPONLY=True,
       SESSION_COOKIE_SAMESITE='Lax',
       PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
   )
   ```

3. **Multi-Factor Authentication (MFA)**

   Verify:

   - MFA available for sensitive operations

   - Secure MFA token generation

   - Backup authentication methods

   - MFA enrollment process security

### Step 4: Data Protection Assessment

**Evaluate how sensitive data is protected:**

1. **Sensitive Data Identification**

   Identify and catalog:

   - Personally Identifiable Information (PII)

   - Payment card data

   - Health information

   - Authentication credentials

   - API keys and secrets

   - Encryption keys

2. **Encryption Verification**

   **Data at Rest**:
   ```python
   # Python: Database field encryption
   from cryptography.fernet import Fernet

   class User(db.Model):
       ssn_encrypted = db.Column(db.LargeBinary)

       def set_ssn(self, ssn):
           cipher = Fernet(encryption_key)
           self.ssn_encrypted = cipher.encrypt(ssn.encode())

       def get_ssn(self):
           cipher = Fernet(encryption_key)
           return cipher.decrypt(self.ssn_encrypted).decode()
   ```

   **Data in Transit**:

   - HTTPS/TLS enforced for all sensitive endpoints

   - No mixed content (HTTP and HTTPS)

   - Certificate validation enabled

   - Minimum TLS version 1.2 or higher

3. **Data Exposure Prevention**

   Search for sensitive data in:

   - Log files

   - Error messages

   - URLs and query parameters

   - Client-side code

   - Configuration files

   - Version control history

   **Bad Patterns to Find**:
   ```python
   # Bad: Password in logs
   logger.info(f"Login attempt: {username}:{password}")

   # Bad: Sensitive data in URL
   return redirect(f'/reset?token={reset_token}&email={email}')

   # Bad: API key in code
   API_KEY = "sk-1234567890abcdef"  # CRITICAL
   ```

### Step 5: Input Validation & Sanitization

**Review all user input handling:**

1. **Input Validation Patterns**

   **Python**:
   ```python
   # Good: Input validation
   from wtforms import validators

   class UserForm(FlaskForm):
       email = StringField('Email', validators=[
           validators.DataRequired(),
           validators.Email(),
           validators.Length(max=254)
       ])
       age = IntegerField('Age', validators=[
           validators.NumberRange(min=0, max=150)
       ])
   ```

   **JavaScript**:
   ```javascript
   // Good: Input sanitization
   const validator = require('validator');

   function sanitizeInput(input) {
       return validator.escape(validator.trim(input));
   }

   // Good: Type validation
   function validateAge(age) {
       return Number.isInteger(age) && age >= 0 && age <= 150;
   }
   ```

2. **File Upload Security**

   **Check for**:

   - File type validation (extension and MIME type)

   - File size limits

   - Malware scanning

   - Safe file storage location

   - Filename sanitization

   **Python Example**:
   ```python
   ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
   MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

   def allowed_file(filename):
       return '.' in filename and \
              filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

   @app.route('/upload', methods=['POST'])
   def upload_file():
       if 'file' not in request.files:
           return "No file", 400

       file = request.files['file']

       if not allowed_file(file.filename):
           return "Invalid file type", 400

       if len(file.read()) > MAX_FILE_SIZE:
           return "File too large", 400

       file.seek(0)

       # Sanitize filename
       filename = secure_filename(file.filename)
       file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
   ```

3. **XSS Prevention**

   **Python (Flask)**:
   ```python
   # Good: Automatic escaping in templates (Jinja2)
   # {{ user_input }}  automatically escaped

   # If manual rendering:
   from markupsafe import escape
   safe_output = escape(user_input)
   ```

   **JavaScript**:
   ```javascript
   // Bad: innerHTML with user input
   element.innerHTML = userInput;  // XSS vulnerability

   // Good: textContent
   element.textContent = userInput;

   // Good: DOMPurify for rich content
   import DOMPurify from 'dompurify';
   element.innerHTML = DOMPurify.sanitize(userInput);
   ```

4. **CSRF Protection**

   **Python (Flask)**:
   ```python
   from flask_wtf.csrf import CSRFProtect

   csrf = CSRFProtect(app)

   # Forms automatically protected
   # AJAX needs CSRF token in header
   ```

### Step 6: Secrets Management Review

**Detect and document all hardcoded secrets:**

1. **Search Patterns**

   Look for:

   - API keys: `api[_-]?key`, `apikey`, `api[_-]secret`

   - Passwords: `password\s*=\s*["']`, `pwd\s*=`

   - Tokens: `token\s*=\s*["']`, `access[_-]token`

   - Credentials: `username.*password`, `user.*pass`

   - Private keys: `BEGIN.*PRIVATE KEY`

   - Database URLs: `postgres://`, `mysql://` with credentials

2. **Environment Variables Usage**

   **Python**:
   ```python
   # Bad: Hardcoded secret
   SECRET_KEY = 'hardcoded-secret-key-123'  # CRITICAL

   # Good: Environment variable
   import os
   SECRET_KEY = os.environ.get('SECRET_KEY')
   if not SECRET_KEY:
       raise ValueError("SECRET_KEY environment variable not set")
   ```

   **JavaScript**:
   ```javascript
   // Bad: API key in code
   const API_KEY = 'sk-1234567890';  // CRITICAL

   // Good: Environment variable
   const API_KEY = process.env.API_KEY;
   if (!API_KEY) {
       throw new Error('API_KEY environment variable required');
   }
   ```

3. **Secrets Management Tools**

   Recommend:

   - AWS Secrets Manager

   - HashiCorp Vault

   - Azure Key Vault

   - Google Secret Manager

   - Docker secrets

   - Kubernetes secrets

### Step 7: Generate Security Report

**Compile findings into structured security report:**

```markdown
# Security Review Report

**Project**: [Name]
**Date**: [Date]
**Reviewer**: [Name]

## Executive Summary

- **Overall Security Rating**: [Critical / High Risk / Medium Risk / Low Risk]

- **Critical Vulnerabilities**: [Count]

- **High-Risk Issues**: [Count]

- **Medium-Risk Issues**: [Count]

- **Low-Risk Issues**: [Count]

- **Compliance Status**: [Compliant / Non-Compliant / Partial]

## Vulnerability Summary

### Critical (CVSS 9.0-10.0) - Immediate Action Required
| ID | Vulnerability | Location | CVSS | Impact | Remediation |
|----|---------------|----------|------|--------|-------------|
| C-1 | SQL Injection | auth.py:45 | 9.8 | Data breach | Use parameterized queries |

### High (CVSS 7.0-8.9) - Urgent Attention Needed
| ID | Vulnerability | Location | CVSS | Impact | Remediation |
|----|---------------|----------|------|--------|-------------|
| H-1 | XSS | views.py:120 | 7.3 | Session hijacking | Sanitize output |

### Medium (CVSS 4.0-6.9) - Plan Remediation
| ID | Vulnerability | Location | CVSS | Impact | Remediation |
|----|---------------|----------|------|--------|-------------|
| M-1 | Weak password policy | auth.py:30 | 5.3 | Account compromise | Enforce strong passwords |

### Low (CVSS 0.1-3.9) - Address When Possible
| ID | Vulnerability | Location | CVSS | Impact | Remediation |
|----|---------------|----------|------|--------|-------------|
| L-1 | Missing security headers | config.py | 2.1 | Limited | Add security headers |

## OWASP Top 10 Assessment

### A01: Broken Access Control - [Fail/Pass]
- **Findings**: [List issues]

- **Risk Level**: [Critical/High/Medium/Low]

- **Recommendations**: [Actions]

### A02: Cryptographic Failures - [Fail/Pass]
- **Findings**: [List issues]

- **Risk Level**: [Critical/High/Medium/Low]

- **Recommendations**: [Actions]

### A03: Injection - [Fail/Pass]
- **Findings**: [List issues]

- **Risk Level**: [Critical/High/Medium/Low]

- **Recommendations**: [Actions]

[Continue for all OWASP Top 10...]

## Dependency Vulnerabilities

### Critical Dependencies
| Package | Current | Fixed Version | CVE | CVSS | Recommendation |
|---------|---------|---------------|-----|------|----------------|
| [name] | [ver] | [ver] | CVE-YYYY-XXXXX | 9.1 | Update immediately |

### Outdated Packages with Security Patches
| Package | Current | Latest | Security Fixes | Recommendation |
|---------|---------|--------|----------------|----------------|
| [name] | [ver] | [ver] | [count] | Update in next sprint |

## Authentication & Authorization

### Password Security
- **Hashing Algorithm**: [bcrypt/argon2/insecure]

- **Password Policy**: [Strong/Weak/None]

- **Password Storage**: [Secure/Insecure]

- **Issues**: [List problems]

### Session Management
- **Token Generation**: [Secure/Insecure]

- **Session Timeout**: [Configured/Missing]

- **Session Fixation Protection**: [Yes/No]

- **Issues**: [List problems]

### Authorization
- **RBAC Implementation**: [Yes/No/Partial]

- **Missing Authorization**: [List endpoints]

- **Privilege Escalation Risks**: [List issues]

## Data Protection

### Encryption Status
- **Data at Rest**: [Encrypted/Not Encrypted]

- **Data in Transit**: [HTTPS/Mixed/HTTP]

- **Sensitive Fields**: [List and protection status]

### Data Exposure
- **In Logs**: [Count] instances

- **In URLs**: [Count] instances

- **In Error Messages**: [Count] instances

- **Client-Side**: [Count] instances

## Secrets Management

### Hardcoded Secrets Found
| Location | Type | Severity | Recommendation |
|----------|------|----------|----------------|
| config.py:15 | API Key | Critical | Move to environment variables |

### Recommendations
- Migrate to [secrets management solution]

- Implement secret rotation

- Audit secret access

## Compliance Assessment

### GDPR Compliance
- **Data Inventory**: [Complete/Incomplete]

- **Consent Management**: [Implemented/Missing]

- **Right to Erasure**: [Implemented/Missing]

- **Data Breach Notification**: [Implemented/Missing]

### [Other Regulations]
- [Assessment for applicable regulations]

## Remediation Roadmap

### Immediate (Week 1) - Critical Items
1. **[Vulnerability]**

   - **Risk**: [Description]

   - **Effort**: [Hours]

   - **Owner**: [Team/Person]

### Short-term (Weeks 2-4) - High Priority
1. **[Issue]**

   - **Risk**: [Description]

   - **Effort**: [Days]

### Medium-term (Months 2-3) - Medium Priority
1. **[Issue]**

   - **Effort**: [Weeks]

## Positive Findings

- [Security practices done well]

- [Effective security controls]

## Next Steps

- [ ] Fix all critical vulnerabilities (P0)

- [ ] Update vulnerable dependencies

- [ ] Implement secret management

- [ ] Add automated security scanning to CI/CD

- [ ] Conduct penetration testing

- [ ] Proceed to [Phase 4: Performance Review](../code-review-performance/SKILL.md)
```

## Multi-Language Support

This skill supports comprehensive security review for:

- **Python** - Django, Flask, FastAPI applications

- **JavaScript/TypeScript** - Node.js, React, Angular, Vue applications

- **Java** - Spring Boot, Jakarta EE applications

- **Go** - Standard library, Gin, Echo applications

- **C** - System programming, embedded applications

- **C++** - Modern C++, Qt, Boost applications

- **C#** - .NET Core, ASP.NET applications

Each language has specific security concerns, vulnerability patterns, and scanning tools.

## Common Pitfalls and Solutions

### Pitfall 1: Only Relying on Automated Tools

**Problem**: Automated scanners miss logic flaws and complex vulnerabilities.

**Solution**: Combine automated scanning with manual code review of authentication, authorization, and business logic.

### Pitfall 2: Ignoring Low-Severity Findings

**Problem**: Multiple low-severity issues can combine into high-severity exploits.

**Solution**: Address all findings systematically, prioritize by exploitability and impact.

### Pitfall 3: Not Testing Fixes

**Problem**: Security fixes can introduce new vulnerabilities or break functionality.

**Solution**: Test all security fixes thoroughly, use security regression tests.

### Pitfall 4: Treating Security as One-Time Activity

**Problem**: New vulnerabilities emerge continuously in dependencies and code changes.

**Solution**: Integrate security into CI/CD pipeline, conduct regular audits.

## Success Criteria

- [ ] All automated security scans completed

- [ ] OWASP Top 10 vulnerabilities assessed

- [ ] Dependency vulnerabilities identified and prioritized

- [ ] Authentication and authorization audited

- [ ] Data protection practices reviewed

- [ ] Hardcoded secrets detected and documented

- [ ] Input validation comprehensively evaluated

- [ ] Security report generated with remediation plan

- [ ] Critical vulnerabilities have fix timeline

- [ ] Team ready for performance review

## Related Skills

### Code Review Workflow
1. [Phase 1: Context Analysis](../code-review-context-analysis/SKILL.md)

2. [Phase 2: Quality Review](../code-review-quality/SKILL.md)

3. **Phase 3: Security Review (This Skill)**

4. [Phase 4: Performance Review](../code-review-performance/SKILL.md)

5. [Phase 5: Testing Review](../code-review-testing/SKILL.md)

6. [Phase 6: Final Report](../code-review-final-report/SKILL.md)

## Additional Resources

### Security Tools
- **Python**: bandit, safety, pip-audit, semgrep

- **JavaScript**: ESLint security plugins, npm audit, snyk

- **Java**: SpotBugs, Find Security Bugs, OWASP Dependency-Check

- **Go**: gosec, govulncheck, staticcheck

- **C/C++**: cppcheck, flawfinder, clang-tidy

- **Multi-language**: semgrep, SonarQube, Snyk, GitLeaks

### Security Standards
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)

- [CWE Top 25](https://cwe.mitre.org/top25/)

- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

### Secure Coding Guidelines
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)

- [SEI CERT Coding Standards](https://wiki.sei.cmu.edu/confluence/display/seccode)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: AI Templates Code Review Workflow, Anthropic Claude Code Best Practices 2025
**Template Source**: `code_review/security_review/*.md`
