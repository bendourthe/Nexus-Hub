# JavaScript Security Review

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
- [ ] XSS (Cross-Site Scripting) vulnerabilities checked
- [ ] CSRF (Cross-Site Request Forgery) protection verified
- [ ] SQL/NoSQL injection vectors identified
- [ ] Command injection points evaluated
- [ ] Path traversal vulnerabilities tested

### Dependency Security
- [ ] All dependencies scanned for known vulnerabilities (CVEs)
- [ ] Outdated packages with security patches identified
- [ ] Dependency chain analyzed for transitive vulnerabilities
- [ ] License compliance verified
- [ ] Supply chain risks assessed (package integrity)

### Authentication & Authorization
- [ ] Authentication mechanisms reviewed (JWT, sessions, OAuth)
- [ ] Password storage security verified (hashing, salting)
- [ ] Session management evaluated
- [ ] Authorization logic checked for privilege escalation
- [ ] API authentication security assessed
- [ ] Token security reviewed (storage, expiration, refresh)

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
- [ ] Input sanitization for XSS/injection verified
- [ ] File upload restrictions evaluated
- [ ] API input validation checked
- [ ] Deserialization security reviewed (JSON, YAML)

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Security Review

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

Please perform a comprehensive security review of this JavaScript project following this protocol:

## Phase 1: Automated Vulnerability Scanning

1. **Dependency Vulnerability Scan**
   ```bash
   # NPM audit for known vulnerabilities
   npm audit

   # Generate detailed JSON report
   npm audit --json > ${OUTPUT_DIR}/exports/npm-audit.json

   # Check for outdated packages with security issues
   npm outdated

   # Use Snyk for comprehensive scanning
   npx snyk test

   # Or use OWASP Dependency-Check
   dependency-check --project "ProjectName" --scan ./
   ```

2. **Static Security Analysis**
   ```bash
   # ESLint security plugins
   npx eslint . --ext .js,.jsx,.ts,.tsx \
     --plugin security \
     --plugin no-secrets

   # Run semgrep for security patterns
   npx semgrep --config=auto src/

   # Use retire.js for outdated libraries
   npx retire --path ./
   ```

3. **Secret Detection**
   ```bash
   # Scan for hardcoded secrets
   npx detect-secrets-launcher --baseline .secrets.baseline

   # Use truffleHog
   truffleHog filesystem . --json

   # Check for common secret patterns
   grep -r "password\s*=\s*['\"]" src/
   grep -r "api_key\s*=\s*['\"]" src/
   grep -r "secret\s*=\s*['\"]" src/
   ```

## Phase 2: OWASP Top 10 Assessment

For each OWASP vulnerability category, systematically review the codebase:

1. **A01: Broken Access Control**
   - Review authorization logic in all API endpoints/routes
   - Check for missing authorization checks
   - Verify users cannot access resources beyond permissions
   - Test for horizontal/vertical privilege escalation
   - Check for insecure direct object references (IDOR)

2. **A02: Cryptographic Failures**
   ```javascript
   // Search for weak cryptographic patterns:

   // Good: Using established crypto libraries
   const crypto = require('crypto');
   const hash = crypto.createHash('sha256').update(data).digest('hex');

   // Bad: Weak hashing or encryption
   // MD5, SHA1 are cryptographically broken
   crypto.createHash('md5'); // CRITICAL
   crypto.createHash('sha1'); // WARNING

   // Bad: Custom encryption
   function customEncrypt(data) { /* ... */ } // CRITICAL

   // Bad: Using encoding as encryption
   Buffer.from(secret).toString('base64'); // NOT ENCRYPTION!
   ```

3. **A03: Injection**
   - **SQL Injection**: Verify parameterized queries
   ```javascript
   // Good: Parameterized query
   db.query('SELECT * FROM users WHERE id = ?', [userId]);

   // Bad: String concatenation
   db.query(`SELECT * FROM users WHERE id = ${userId}`); // CRITICAL
   ```

   - **NoSQL Injection**: Check MongoDB query construction
   ```javascript
   // Good: Sanitized input
   const user = await User.findOne({ username: sanitize(input) });

   // Bad: Direct user input
   const user = await User.findOne(JSON.parse(userInput)); // CRITICAL
   ```

   - **Command Injection**: Review shell command execution
   ```javascript
   // Good: Use array arguments, avoid shell
   const { exec } = require('child_process');
   execFile('ping', ['-c', '1', host]);

   // Bad: Shell execution with user input
   exec(`ping ${userHost}`); // CRITICAL
   ```

   - **XSS (Cross-Site Scripting)**: Check HTML rendering
   ```javascript
   // React: Good (auto-escaped)
   <div>{userContent}</div>

   // React: Bad (dangerous)
   <div dangerouslySetInnerHTML={{__html: userContent}} /> // WARNING

   // Vanilla JS: Bad (XSS vulnerability)
   element.innerHTML = userInput; // CRITICAL
   ```

4. **A04: Insecure Design**
   - Review architecture for security anti-patterns
   - Assess threat modeling evidence
   - Check security requirements in design
   - Evaluate rate limiting and resource controls

5. **A05: Security Misconfiguration**
   ```javascript
   // Check for dangerous configurations:

   // Bad: Debug mode in production
   if (process.env.NODE_ENV !== 'production') {
       app.use(errorHandler());
   }

   // Bad: Exposing sensitive info in errors
   app.use((err, req, res, next) => {
       res.status(500).json({
           error: err.stack // CRITICAL: leaks stack trace
       });
   });

   // Bad: Missing security headers
   // Should use helmet.js or equivalent

   // Bad: CORS misconfiguration
   app.use(cors({
       origin: '*' // WARNING: too permissive
   }));
   ```

6. **A06: Vulnerable and Outdated Components**
   - Cross-reference dependency vulnerabilities from Phase 1
   - Identify components without security patches
   - Check for deprecated libraries
   - Review package-lock.json for dependency pinning

7. **A07: Identification and Authentication Failures**
   ```javascript
   // Review authentication patterns:

   // Good: Strong password hashing
   const bcrypt = require('bcrypt');
   const hashedPassword = await bcrypt.hash(password, 10);

   // Bad: Weak or no hashing
   if (user.password === inputPassword) { /* ... */ } // CRITICAL

   // Good: JWT with proper configuration
   const jwt = require('jsonwebtoken');
   const token = jwt.sign(payload, secret, {
       expiresIn: '1h',
       algorithm: 'HS256'
   });

   // Bad: No token expiration
   const token = jwt.sign(payload, secret); // WARNING

   // Bad: Predictable session IDs
   const sessionId = Date.now().toString(); // CRITICAL
   ```

8. **A08: Software and Data Integrity Failures**
   - Review package-lock.json integrity
   - Check for package signature verification
   - Assess deserialization security
   ```javascript
   // Bad: eval() is dangerous
   eval(userInput); // CRITICAL

   // Bad: Function constructor
   new Function(userCode)(); // CRITICAL

   // Bad: Unsafe deserialization
   JSON.parse(untrustedData); // Should validate first

   // Bad: Using vm module with untrusted code
   vm.runInThisContext(userCode); // CRITICAL
   ```

9. **A09: Security Logging and Monitoring Failures**
   - Assess logging comprehensiveness
   - Check for sensitive data in logs
   ```javascript
   // Bad: Logging sensitive data
   logger.info('User login', { password: req.body.password }); // CRITICAL
   logger.error('Error', { creditCard: user.creditCard }); // CRITICAL

   // Good: Sanitized logging
   logger.info('User login', { userId: user.id });
   ```

10. **A10: Server-Side Request Forgery (SSRF)**
    ```javascript
    // Bad: Unvalidated URL requests
    const response = await fetch(userProvidedUrl); // CRITICAL

    // Good: Validate and whitelist URLs
    if (allowedDomains.includes(new URL(url).hostname)) {
        const response = await fetch(url);
    }
    ```

## Phase 3: Authentication & Authorization Deep Dive

1. **Password Security**
   ```javascript
   // Search for password handling:

   // Good: bcrypt or argon2
   const bcrypt = require('bcrypt');
   const hash = await bcrypt.hash(password, 10);
   const isValid = await bcrypt.compare(password, hash);

   // Good: argon2 (recommended)
   const argon2 = require('argon2');
   const hash = await argon2.hash(password);
   const isValid = await argon2.verify(hash, password);

   // Bad: Plain text or weak hashing
   crypto.createHash('md5').update(password).digest('hex'); // CRITICAL
   ```

2. **JWT Security**
   ```javascript
   // Check JWT implementation:

   // Good: Proper JWT configuration
   jwt.sign(payload, process.env.JWT_SECRET, {
       expiresIn: '1h',
       algorithm: 'HS256',
       audience: 'myapp',
       issuer: 'myapp-auth'
   });

   // Bad: Weak or no secret
   jwt.sign(payload, 'secret'); // CRITICAL: weak secret

   // Bad: No expiration
   jwt.sign(payload, secret); // WARNING: no expiresIn

   // Good: Verify with options
   jwt.verify(token, secret, {
       algorithms: ['HS256'],
       audience: 'myapp'
   });
   ```

3. **Session Management**
   ```javascript
   // Express session configuration:

   // Good: Secure session config
   app.use(session({
       secret: process.env.SESSION_SECRET,
       resave: false,
       saveUninitialized: false,
       cookie: {
           secure: true, // HTTPS only
           httpOnly: true, // Prevent XSS
           maxAge: 3600000, // 1 hour
           sameSite: 'strict' // CSRF protection
       }
   }));

   // Bad: Insecure session config
   app.use(session({
       secret: 'keyboard cat', // CRITICAL: hardcoded
       cookie: { secure: false } // WARNING: not HTTPS-only
   }));
   ```

## Phase 4: Data Protection Review

1. **Sensitive Data Identification**
   - Identify PII (names, emails, addresses, phone numbers)
   - Locate financial data (credit cards, bank accounts)
   - Find authentication credentials (passwords, tokens, API keys)
   - Document sensitive business data

2. **Encryption Assessment**
   ```javascript
   // Good: Using crypto properly
   const crypto = require('crypto');
   const algorithm = 'aes-256-gcm';
   const key = crypto.scryptSync(password, salt, 32);
   const iv = crypto.randomBytes(16);
   const cipher = crypto.createCipheriv(algorithm, key, iv);

   // Bad: Weak encryption
   const cipher = crypto.createCipher('des', key); // WARNING: DES is weak

   // Bad: Base64 is not encryption!
   const "encrypted" = Buffer.from(data).toString('base64'); // NOT SECURE
   ```

3. **Data Exposure Risks**
   ```javascript
   // Check for data exposure in:

   // 1. Error responses
   res.status(500).json({ error: err.stack }); // CRITICAL

   // 2. Logs
   console.log('User data:', userData); // May contain PII

   // 3. API responses
   res.json(user); // May expose sensitive fields like password hash

   // Good: Filter sensitive fields
   const { password, ssn, ...safeUser } = user;
   res.json(safeUser);
   ```

## Phase 5: Input Validation & Sanitization

1. **Input Validation**
   ```javascript
   // Good: Using validation library
   const Joi = require('joi');
   const schema = Joi.object({
       email: Joi.string().email().required(),
       age: Joi.number().integer().min(0).max(120)
   });
   const { error, value } = schema.validate(req.body);

   // Good: Express-validator
   const { body, validationResult } = require('express-validator');
   app.post('/user', [
       body('email').isEmail(),
       body('password').isLength({ min: 8 })
   ], (req, res) => {
       const errors = validationResult(req);
       if (!errors.isEmpty()) {
           return res.status(400).json({ errors: errors.array() });
       }
   });
   ```

2. **XSS Prevention**
   ```javascript
   // Good: HTML sanitization
   const DOMPurify = require('isomorphic-dompurify');
   const clean = DOMPurify.sanitize(dirty);

   // Good: Escaping user input
   const escape = require('escape-html');
   const safe = escape(userInput);

   // React: Good (auto-escaped by default)
   <div>{userInput}</div>

   // Bad: Directly rendering user input
   element.innerHTML = userInput; // CRITICAL
   ```

3. **File Upload Security**
   ```javascript
   // Good: File upload with validation
   const multer = require('multer');
   const upload = multer({
       limits: { fileSize: 5 * 1024 * 1024 }, // 5MB
       fileFilter: (req, file, cb) => {
           const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
           if (allowedTypes.includes(file.mimetype)) {
               cb(null, true);
           } else {
               cb(new Error('Invalid file type'));
           }
       }
   });

   // Bad: No validation
   app.post('/upload', upload.any(), (req, res) => {
       // No file type or size checking!
   });
   ```

## Phase 6: Secrets Management

1. **Hardcoded Secrets Search**
   ```bash
   # Search for secret patterns
   grep -r "password\s*=\s*['\"][^'\"]\+['\"]" src/
   grep -r "api_key\s*=\s*['\"][^'\"]\+['\"]" src/
   grep -r "secret\s*=\s*['\"][^'\"]\+['\"]" src/
   grep -r "token\s*=\s*['\"][^'\"]\+['\"]" src/
   ```

2. **Environment Variable Usage**
   ```javascript
   // Good: Using environment variables
   const apiKey = process.env.API_KEY;
   const dbPassword = process.env.DB_PASSWORD;

   // Bad: Hardcoded secrets
   const apiKey = 'sk_live_1234567890abcdef'; // CRITICAL
   const dbPassword = 'mypassword123'; // CRITICAL

   // Good: Validating required env vars
   const requiredEnvVars = ['DB_HOST', 'DB_PASSWORD', 'JWT_SECRET'];
   for (const envVar of requiredEnvVars) {
       if (!process.env[envVar]) {
           throw new Error(`Missing required env var: ${envVar}`);
       }
   }
   ```

3. **Configuration File Security**
   - Check .env files not in version control
   - Verify .gitignore includes sensitive files
   - Review config file permissions
   - Check for default/example secrets

## Phase 7: Frontend-Specific Security (if applicable)

1. **XSS Prevention**
   - Verify Content Security Policy (CSP) headers
   - Check for dangerouslySetInnerHTML usage
   - Review third-party script inclusion
   - Assess inline script usage

2. **CSRF Protection**
   ```javascript
   // Good: CSRF token middleware
   const csrf = require('csurf');
   app.use(csrf({ cookie: true }));

   app.get('/form', (req, res) => {
       res.render('form', { csrfToken: req.csrfToken() });
   });
   ```

3. **Client-Side Storage**
   ```javascript
   // Bad: Storing sensitive data in localStorage
   localStorage.setItem('token', jwt); // WARNING: vulnerable to XSS

   // Better: httpOnly cookie (set server-side)
   res.cookie('token', jwt, { httpOnly: true, secure: true });
   ```

## Output Format

Please provide a comprehensive security report with the following structure:

### Executive Summary
- **Overall Security Risk**: [Critical/High/Medium/Low]
- **Critical Vulnerabilities**: [count]
- **High-Risk Issues**: [count]
- **Dependency Vulnerabilities**: [count]
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
| A03: Injection | [Pass/Fail] | [count] | [High/Med/Low] |
| A04: Insecure Design | [Pass/Fail] | [count] | [High/Med/Low] |
| A05: Security Misconfiguration | [Pass/Fail] | [count] | [High/Med/Low] |
| A06: Vulnerable Components | [Pass/Fail] | [count] | [High/Med/Low] |
| A07: Auth Failures | [Pass/Fail] | [count] | [High/Med/Low] |
| A08: Integrity Failures | [Pass/Fail] | [count] | [High/Med/Low] |
| A09: Logging Failures | [Pass/Fail] | [count] | [High/Med/Low] |
| A10: SSRF | [Pass/Fail] | [count] | [High/Med/Low] |

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
- **JWT Implementation**: [secure/issues found]
- **Session Management**: [secure/issues found]
- **Authorization Coverage**: [percentage of endpoints protected]

### Data Protection
- **Sensitive Data Inventory**: [types and locations]
- **Encryption**: [properly implemented/issues found]
- **PII Exposure Risks**: [high/medium/low and locations]
- **Logging Security**: [secure/leaks sensitive data]

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
```json
{
  "dependencies": {
    "helmet": "^7.0.0",
    "express-rate-limit": "^6.0.0",
    "express-validator": "^7.0.0",
    "bcrypt": "^5.1.0",
    "jsonwebtoken": "^9.0.0",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "eslint-plugin-security": "^1.7.1",
    "eslint-plugin-no-secrets": "^0.8.9",
    "snyk": "^1.1000.0"
  },
  "scripts": {
    "audit": "npm audit",
    "audit:fix": "npm audit fix",
    "security:scan": "snyk test",
    "security:secrets": "detect-secrets-launcher --baseline .secrets.baseline"
  }
}
```

### Positive Security Practices
Acknowledge what's done well:
- [Good practice observed]
- [Effective security measure implemented]

### Next Steps
- [ ] Remediate all critical vulnerabilities immediately
- [ ] Update vulnerable dependencies
- [ ] Implement security headers (helmet.js)
- [ ] Add rate limiting
- [ ] Set up automated security scanning in CI/CD
- [ ] Conduct penetration testing after fixes
- [ ] Establish security code review process
- [ ] Provide security training for development team

## Notes
- **Confidentiality**: This security report contains sensitive information
- **Responsible Disclosure**: Follow responsible disclosure for third-party vulnerabilities
- **Retest**: After remediation, rerun security scans to verify fixes
- **Continuous Monitoring**: Implement Snyk or Dependabot for ongoing dependency monitoring

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
