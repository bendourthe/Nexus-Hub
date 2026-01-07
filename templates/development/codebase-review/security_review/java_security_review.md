---
template_id: java_security_review
template_name: Security Review - Java
version: 1.0.0
last_updated: 2025-12-03
language: Java
category: code_review
phase: security_review
phase_number: 3
difficulty: advanced
estimated_time_hours: 2-3
prerequisites:

  - code_review/code_quality/java_code_quality.md
related_templates:

  - code_review/code_quality/java_code_quality.md
tools:

  - junit (5.11.3)

  - maven

  - gradle
tags:

  - code-review

  - security

  - code-review

  - java
---
# Java Security Review

## Objective
Systematically identify security vulnerabilities, insecure coding practices, and compliance gaps that could expose the Java application to attacks, data breaches, or regulatory violations.

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

- [ ] XML External Entity (XXE) vulnerabilities checked

- [ ] Deserialization vulnerabilities evaluated

- [ ] LDAP injection points assessed

- [ ] Path traversal vulnerabilities tested

### Dependency Security

- [ ] All dependencies scanned for known vulnerabilities (CVEs)

- [ ] Outdated libraries with security patches identified

- [ ] Transitive dependency vulnerabilities analyzed

- [ ] License compliance verified

- [ ] Supply chain risks assessed

### Authentication & Authorization

- [ ] Authentication mechanisms reviewed (JWT, OAuth2, SAML)

- [ ] Password storage security verified (BCrypt, Argon2)

- [ ] Session management evaluated

- [ ] Spring Security configuration reviewed (if applicable)

- [ ] Role-based access control (RBAC) implementation checked

- [ ] API authentication security assessed

### Data Protection

- [ ] Sensitive data encryption verified (at rest and in transit)

- [ ] Personally Identifiable Information (PII) handling reviewed

- [ ] Data exposure in logs/errors evaluated

- [ ] Database security assessed (prepared statements, encryption)

- [ ] File upload security verified

- [ ] Data retention and deletion practices reviewed

### Secrets Management

- [ ] Hardcoded credentials searched and documented

- [ ] API keys and tokens in code identified

- [ ] Environment variable usage verified

- [ ] Secrets management system evaluated (Vault, AWS Secrets Manager)

- [ ] Configuration file security checked

### Input Validation & Sanitization

- [ ] User input validation comprehensiveness assessed

- [ ] Input sanitization for SQL/LDAP injection verified

- [ ] Bean Validation (JSR-380) usage reviewed

- [ ] API input validation checked

- [ ] Deserialization security reviewed

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
# Java Security Review

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

Please perform a comprehensive security review of this Java project following this protocol:

## Phase 1: Automated Vulnerability Scanning

1. **Dependency Vulnerability Scan**
   ```bash
   # OWASP Dependency-Check (Maven)
   mvn org.owasp:dependency-check-maven:check

   # For Gradle
   ./gradlew dependencyCheckAnalyze

   # Snyk scanning (if available)
   snyk test --all-projects

   # Check for outdated dependencies
   mvn versions:display-dependency-updates
   ```

2. **Static Security Analysis**
   ```bash
   # SpotBugs with security plugin (Find Security Bugs)
   mvn spotbugs:check

   # SonarQube security analysis
   mvn sonar:sonar -Dsonar.qualitygate.wait=true

   # Semgrep for security patterns
   semgrep --config=auto src/
   ```

3. **Secret Detection**
   ```bash
   # Scan for hardcoded secrets using gitleaks
   gitleaks detect --source . --verbose

   # Or use truffleHog
   truffleHog filesystem . --json

   # Check for API keys and credentials
   grep -r "password\s*=" src/
   grep -r "apiKey\s*=" src/
   ```

## Phase 2: OWASP Top 10 Assessment

For each OWASP vulnerability category, systematically review the codebase:

1. **A01: Broken Access Control**

   - Review authorization logic in all endpoints/controllers

   - Check Spring Security @PreAuthorize, @Secured annotations

   - Verify user cannot access resources beyond permissions

   - Test for horizontal/vertical privilege escalation

   - Example locations: @RestController methods, service layer

2. **A02: Cryptographic Failures**
   ```java
   // Search for weak cryptography:

   // BAD: Weak algorithms
   MessageDigest md5 = MessageDigest.getInstance("MD5");  // CRITICAL
   MessageDigest sha1 = MessageDigest.getInstance("SHA1");  // CRITICAL
   Cipher des = Cipher.getInstance("DES");  // CRITICAL

   // GOOD: Strong algorithms
   MessageDigest sha256 = MessageDigest.getInstance("SHA-256");
   Cipher aes = Cipher.getInstance("AES/GCM/NoPadding");

   // BAD: Hardcoded keys
   byte[] key = "hardcodedkey123".getBytes();  // CRITICAL

   // GOOD: Key from secure source
   SecretKey key = KeyGenerator.getInstance("AES").generateKey();
   ```

   - Verify HTTPS/TLS usage for sensitive data transmission

   - Check database encryption for sensitive fields

   - Review password storage (should use BCrypt, Argon2, SCrypt)

   - Identify sensitive data in logs or error messages

3. **A03: Injection**

   **SQL Injection**:
   ```java
   // BAD: String concatenation (CRITICAL)
   String query = "SELECT * FROM users WHERE id = " + userId;
   Statement stmt = connection.createStatement();
   ResultSet rs = stmt.executeQuery(query);

   // GOOD: Prepared statements
   String query = "SELECT * FROM users WHERE id = ?";
   PreparedStatement stmt = connection.prepareStatement(query);
   stmt.setLong(1, userId);
   ResultSet rs = stmt.executeQuery();

   // GOOD: JPA/Hibernate
   User user = entityManager.find(User.class, userId);
   // Or with query
   TypedQuery<User> query = em.createQuery(
       "SELECT u FROM User u WHERE u.id = :id", User.class);
   query.setParameter("id", userId);
   ```

   **LDAP Injection**:
   ```java
   // BAD: Direct string concatenation
   String filter = "(uid=" + username + ")";  // CRITICAL

   // GOOD: Escape LDAP special characters
   String filter = "(uid=" + escapeLdap(username) + ")";
   ```

   **Command Injection**:
   ```java
   // BAD: User input in command execution
   Runtime.getRuntime().exec("ping " + userInput);  // CRITICAL
   ProcessBuilder pb = new ProcessBuilder("sh", "-c", userCommand);  // CRITICAL

   // GOOD: Validate and sanitize input, use array form
   if (!userInput.matches("[a-zA-Z0-9.]+")) {
       throw new IllegalArgumentException("Invalid input");
   }
   ProcessBuilder pb = new ProcessBuilder("ping", "-c", "1", userInput);
   ```

   **OGNL/EL Injection**:
   ```java
   // BAD: User input in expression evaluation
   Ognl.getValue(userExpression, context);  // CRITICAL
   ```

4. **A04: Insecure Design**

   - Review architecture for security anti-patterns

   - Assess threat modeling evidence

   - Check security requirements in design docs

   - Evaluate rate limiting and throttling

   - Review multi-factor authentication implementation

5. **A05: Security Misconfiguration**
   ```java
   // Check application.properties/yml for:

   // BAD configurations:
   spring.datasource.url=jdbc:mysql://localhost/db?useSSL=false  // Warning
   server.error.include-stacktrace=always  // CRITICAL in production
   spring.jpa.show-sql=true  // Warning in production
   management.endpoints.web.exposure.include=*  // CRITICAL

   // GOOD configurations:
   spring.datasource.url=jdbc:mysql://localhost/db?useSSL=true
   server.error.include-stacktrace=never
   spring.jpa.show-sql=false
   management.endpoints.web.exposure.include=health,info
   ```

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

   - Assess Java version (outdated JDK versions have vulnerabilities)

7. **A07: Identification and Authentication Failures**
   ```java
   // Review Spring Security configuration:

   @Configuration
   @EnableWebSecurity
   public class SecurityConfig {
       @Bean
       public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
           http
               .authorizeHttpRequests(auth -> auth
                   .requestMatchers("/public/**").permitAll()
                   .anyRequest().authenticated()
               )
               .formLogin(form -> form
                   .loginPage("/login")
                   .permitAll()
               )
               .sessionManagement(session -> session
                   .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                   .maximumSessions(1)
                   .expiredUrl("/login?expired")
               );
           return http.build();
       }

       @Bean
       public PasswordEncoder passwordEncoder() {
           // GOOD: Use BCrypt
           return new BCryptPasswordEncoder();
           // BAD: Never use NoOpPasswordEncoder in production
       }
   }
   ```

   - Review password complexity requirements

   - Check for weak session management

   - Verify multi-factor authentication implementation

   - Assess brute-force protection (rate limiting)

   - Check for authentication bypass vulnerabilities

8. **A08: Software and Data Integrity Failures**
   ```java
   // CRITICAL: Insecure deserialization

   // BAD: Deserializing untrusted data
   ObjectInputStream ois = new ObjectInputStream(untrustedInput);
   Object obj = ois.readObject();  // CRITICAL

   // BETTER: Use safe serialization formats (JSON, XML with validation)
   ObjectMapper mapper = new ObjectMapper();
   MyObject obj = mapper.readValue(jsonString, MyObject.class);

   // BAD: YAML unsafe loading
   Yaml yaml = new Yaml();
   Object obj = yaml.load(untrustedInput);  // CRITICAL

   // GOOD: Safe YAML loading
   Yaml yaml = new Yaml(new SafeConstructor());
   Object obj = yaml.load(trustedInput);
   ```

   - Review CI/CD pipeline security

   - Check Maven/Gradle artifact verification

   - Assess deserialization security

   - Verify update mechanisms security

9. **A09: Security Logging and Monitoring Failures**
   ```java
   // Check logging practices:

   // BAD: Logging sensitive data
   logger.info("User logged in with password: " + password);  // CRITICAL
   logger.debug("Credit card: " + creditCard);  // CRITICAL

   // GOOD: Log events without sensitive data
   logger.info("User {} logged in successfully", userId);
   logger.warn("Failed login attempt for user {}", username);

   // Security event logging
   logger.warn("Unauthorized access attempt to {} by user {}",
       resource, userId);
   ```

   - Assess logging comprehensiveness

   - Check for sensitive data in logs

   - Review log retention and protection

   - Verify alerting on suspicious activities

   - Check audit trail completeness

10. **A10: Server-Side Request Forgery (SSRF)**
    ```java
    // BAD: Unvalidated URL requests
    @GetMapping("/fetch")
    public String fetchUrl(@RequestParam String url) {
        URL target = new URL(url);  // CRITICAL: User-controlled URL
        return IOUtils.toString(target.openStream());
    }

    // GOOD: Validate and whitelist URLs
    @GetMapping("/fetch")
    public String fetchUrl(@RequestParam String url) {
        if (!isAllowedDomain(url)) {
            throw new SecurityException("Domain not allowed");
        }
        URL target = new URL(url);
        return IOUtils.toString(target.openStream());
    }
    ```

    - Review URL handling and validation

    - Check for unvalidated redirects

    - Assess internal service requests

    - Verify allowlist/blocklist for external requests

## Phase 3: Java-Specific Vulnerabilities

1. **XML External Entity (XXE) Attacks**
   ```java
   // BAD: Default XML parsing (vulnerable to XXE)
   DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
   DocumentBuilder builder = factory.newDocumentBuilder();
   Document doc = builder.parse(untrustedXml);  // CRITICAL

   // GOOD: Disable external entities
   DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
   factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
   factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
   factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
   factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
   factory.setXIncludeAware(false);
   factory.setExpandEntityReferences(false);
   ```

2. **Deserialization Vulnerabilities**
   ```java
   // BAD: Unrestricted deserialization
   ObjectInputStream ois = new ObjectInputStream(socket.getInputStream());
   MyObject obj = (MyObject) ois.readObject();  // CRITICAL

   // BETTER: Use ObjectInputFilter (Java 9+)
   ObjectInputStream ois = new ObjectInputStream(socket.getInputStream());
   ois.setObjectInputFilter(info -> {
       if (info.serialClass() != null) {
           if (!MyObject.class.equals(info.serialClass())) {
               return ObjectInputFilter.Status.REJECTED;
           }
       }
       return ObjectInputFilter.Status.ALLOWED;
   });

   // BEST: Avoid Java serialization, use JSON/Protocol Buffers
   ```

3. **Path Traversal**
   ```java
   // BAD: Unsanitized file paths
   @GetMapping("/download")
   public void downloadFile(@RequestParam String filename, HttpServletResponse response) {
       File file = new File("/uploads/" + filename);  // CRITICAL
       Files.copy(file.toPath(), response.getOutputStream());
   }

   // GOOD: Validate and canonicalize paths
   @GetMapping("/download")
   public void downloadFile(@RequestParam String filename, HttpServletResponse response) {
       Path basePath = Paths.get("/uploads").toRealPath();
       Path filePath = basePath.resolve(filename).normalize();

       if (!filePath.startsWith(basePath)) {
           throw new SecurityException("Path traversal attempt detected");
       }

       Files.copy(filePath, response.getOutputStream());
   }
   ```

4. **Reflection and Dynamic Class Loading**
   ```java
   // BAD: User-controlled class loading
   String className = request.getParameter("class");
   Class<?> clazz = Class.forName(className);  // CRITICAL
   Object instance = clazz.newInstance();

   // GOOD: Whitelist allowed classes
   if (!ALLOWED_CLASSES.contains(className)) {
       throw new SecurityException("Class not allowed");
   }
   ```

## Phase 4: Spring Security Review (if applicable)

1. **Security Configuration Assessment**
   ```java
   // Review Spring Security setup:

   // Check for CSRF protection
   http.csrf().disable();  // WARNING: Only disable if using JWT/stateless

   // Review authorization rules
   http.authorizeHttpRequests()
       .requestMatchers("/admin/**").hasRole("ADMIN")
       .requestMatchers("/api/**").authenticated()
       .anyRequest().permitAll();  // WARNING: Check if correct

   // Check CORS configuration
   http.cors().configurationSource(request -> {
       CorsConfiguration config = new CorsConfiguration();
       config.setAllowedOrigins(List.of("*"));  // CRITICAL: Too permissive
       return config;
   });
   ```

2. **JWT Security** (if using JWT)
   ```java
   // Check JWT implementation:

   // BAD: Weak signing key
   String secret = "secret";  // CRITICAL: Too weak

   // GOOD: Strong, randomly generated key
   SecretKey key = Keys.secretKeyFor(SignatureAlgorithm.HS256);

   // Check token validation
   Claims claims = Jwts.parserBuilder()
       .setSigningKey(key)
       .build()
       .parseClaimsJws(token)
       .getBody();

   // Verify expiration is checked
   if (claims.getExpiration().before(new Date())) {
       throw new JwtException("Token expired");
   }
   ```

3. **Method Security**
   ```java
   // Check for method-level security:

   @PreAuthorize("hasRole('ADMIN')")
   public void deleteUser(Long userId) { }

   @PreAuthorize("#userId == authentication.principal.id")
   public User getUser(Long userId) { }

   // Verify security annotations are consistently applied
   ```

## Phase 5: Data Protection Review

1. **Sensitive Data Identification**

   - Identify PII (names, emails, addresses, SSN)

   - Locate financial data (credit cards, bank accounts)

   - Find health information (PHI/medical data)

   - Document authentication credentials

2. **Encryption Assessment**
   ```java
   // Check for proper encryption:

   // GOOD: Using standard encryption
   Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
   SecretKey key = KeyGenerator.getInstance("AES").generateKey();

   // BAD: Custom/weak encryption
   byte[] encrypted = Base64.getEncoder().encode(data);  // WARNING: Not encryption!

   // BAD: Hardcoded encryption keys
   byte[] key = "1234567890123456".getBytes();  // CRITICAL
   ```

3. **Database Security**
   ```java
   // Check for SQL injection prevention:

   // JPA Named Parameters (GOOD)
   @Query("SELECT u FROM User u WHERE u.email = :email")
   User findByEmail(@Param("email") String email);

   // Native query with parameters (GOOD)
   @Query(value = "SELECT * FROM users WHERE status = ?1", nativeQuery = true)
   List<User> findByStatus(String status);

   // String concatenation (BAD - CRITICAL)
   String query = "SELECT * FROM users WHERE name = '" + name + "'";
   ```

## Phase 6: Secrets Management

1. **Hardcoded Secrets Search**
   ```bash
   # Search for common secret patterns
   grep -rn "password\s*=" src/
   grep -rn "api[_-]?key\s*=" src/
   grep -rn "secret\s*=" src/
   grep -rn "token\s*=" src/
   grep -rn "jdbc:.*password=" src/
   ```

2. **Configuration File Review**

   - Check application.properties/yml for secrets

   - Review environment-specific configurations

   - Verify secrets not in version control

   - Check .gitignore includes sensitive files

3. **Environment Variable Usage**
   ```java
   // GOOD: Load from environment
   @Value("${database.password:#{environment.DB_PASSWORD}}")
   private String dbPassword;

   // BAD: Hardcoded in code
   String password = "hardcoded123";  // CRITICAL
   ```

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
| [vulnerability] | [class:method] | [score] | [details] | [fix steps] |

### High-Risk Findings (Severity: HIGH)
| Issue | Location | Risk Level | Description | Remediation |
|-------|----------|------------|-------------|-------------|
| [vulnerability] | [class:method] | [High] | [details] | [fix steps] |

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
| Dependency | Current Version | CVE | Severity | Fixed Version | Exploitability |
|------------|----------------|-----|----------|---------------|----------------|
| [group:artifact] | [version] | [CVE-ID] | [Critical/High/Med/Low] | [version] | [High/Med/Low] |

### Java-Specific Vulnerabilities

- **XXE Vulnerabilities**: [count and locations]

- **Deserialization Issues**: [count and locations]

- **Path Traversal**: [count and locations]

- **Reflection Abuse**: [count and locations]

### Spring Security Assessment** (if applicable)

- **Configuration**: [secure/issues found]

- **Authentication**: [strong/weak - details]

- **Authorization**: [properly enforced/gaps found]

- **CSRF Protection**: [enabled/disabled - appropriate?]

- **CORS Configuration**: [secure/too permissive]

### Secrets & Credentials Exposure

- **Hardcoded Secrets Found**: [count]

- **Locations**: [list of classes and lines]

- **Types**: [database passwords, API keys, tokens, etc.]

- **Git History Scan**: [secrets in commit history: yes/no]

### Authentication & Authorization

- **Password Storage**: [BCrypt/Argon2/weak method]

- **Session Management**: [secure/issues found]

- **JWT Implementation**: [secure/vulnerable] (if applicable)

- **Authorization Coverage**: [percentage of endpoints protected]

- **Issues Identified**: [list of specific problems]

### Data Protection

- **Sensitive Data Inventory**: [types and locations]

- **Encryption at Rest**: [implemented/missing]

- **Encryption in Transit**: [TLS/HTTPS status]

- **PII Exposure Risks**: [high/medium/low and locations]

- **Database Security**: [prepared statements/vulnerable queries]

### Compliance Assessment

- **OWASP ASVS**: [level achieved]

- **GDPR**: [areas of concern]

- **HIPAA**: [if applicable, compliance status]

- **PCI DSS**: [if applicable, compliance status]

- **SOC 2**: [relevant findings]

### Immediate Action Items (Priority 1)
1. **[Critical Issue]**

   - **Location**: [class:method]

   - **Fix**: [specific remediation steps with code examples]

   - **Time Estimate**: [hours]

   - **Risk if Not Fixed**: [consequences]

### Short-term Actions (Priority 2 - within 1 week)
[List of high-priority items with remediation guidance]

### Medium-term Actions (Priority 3 - within 1 month)
[List of medium-priority improvements]

### Long-term Improvements (Priority 4 - strategic)
[List of systematic security enhancements]

### Security Tools Recommendations
```xml
<!-- Maven pom.xml -->
<build>
    <plugins>
        <plugin>
            <groupId>org.owasp</groupId>
            <artifactId>dependency-check-maven</artifactId>
            <version>8.4.0</version>
            <executions>
                <execution>
                    <goals>
                        <goal>check</goal>
                    </goals>
                </execution>
            </executions>
        </plugin>

        <plugin>
            <groupId>com.github.spotbugs</groupId>
            <artifactId>spotbugs-maven-plugin</artifactId>
            <version>4.7.3.6</version>
            <configuration>
                <plugins>
                    <plugin>
                        <groupId>com.h3xstream.findsecbugs</groupId>
                        <artifactId>findsecbugs-plugin</artifactId>
                        <version>1.12.0</version>
                    </plugin>
                </plugins>
            </configuration>
        </plugin>
    </plugins>
</build>
```

### Positive Security Practices
Acknowledge what's done well:

- [Good practice observed]

- [Effective security measure implemented]

### Next Steps

- [ ] Remediate all critical vulnerabilities immediately

- [ ] Plan remediation sprints for high-risk issues

- [ ] Implement automated security scanning in CI/CD

- [ ] Configure OWASP Dependency-Check in build pipeline

- [ ] Set up Find Security Bugs integration

- [ ] Conduct penetration testing after fixes

- [ ] Establish security code review process

- [ ] Provide security training for development team (OWASP Top 10, secure coding)

## Notes

- **Confidentiality**: This security report contains sensitive information - handle appropriately

- **Responsible Disclosure**: If third-party vulnerabilities found, follow responsible disclosure

- **Retest**: After remediation, rerun security scans to verify fixes

- **Continuous Monitoring**: Implement ongoing security scanning and monitoring

- **Java-Specific**: Pay special attention to deserialization, XXE, and reflection vulnerabilities

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
