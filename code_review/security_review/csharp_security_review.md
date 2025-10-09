# C# Security Review

## Objective
Systematically identify security vulnerabilities, insecure coding practices, and compliance gaps that could expose the .NET application to attacks, data breaches, or regulatory violations.

## Output Directory Structure

All review outputs should be saved in organized directories:

```
review/
└── security_review/
    ├── security_review_report.md
    ├── security_review_findings.json
    ├── analysis_scripts/
    └── supporting_data/
```

**Directory Setup**:
- Create `review/` directory in repository root if it doesn't exist
- Create `review/security_review/` subdirectory for this review phase
- All reports, scripts, and data files go in the phase-specific directory

**Expected Outputs**:
- `security_review_report.md` - Main findings and recommendations
- `security_review_findings.json` - Structured data for tooling integration
- `analysis_scripts/` - Any scripts generated during analysis
- `supporting_data/` - Raw data, logs, profiling results, scan outputs

## Review Checklist

### Vulnerability Assessment
- [ ] OWASP Top 10 vulnerabilities assessed
- [ ] SQL injection vectors identified
- [ ] XSS (Cross-Site Scripting) vulnerabilities checked
- [ ] CSRF (Cross-Site Request Forgery) protection verified
- [ ] Command injection points evaluated
- [ ] Path traversal vulnerabilities tested
- [ ] Deserialization vulnerabilities checked

### Dependency Security
- [ ] All NuGet packages scanned for known vulnerabilities (CVEs)
- [ ] Outdated packages with security patches identified
- [ ] Dependency chain analyzed for transitive vulnerabilities
- [ ] License compliance verified
- [ ] Supply chain risks assessed

### Authentication & Authorization
- [ ] Authentication mechanisms reviewed (Identity, JWT, OAuth)
- [ ] Password storage security verified (Identity password hasher, BCrypt)
- [ ] Session management evaluated
- [ ] Authorization logic checked for privilege escalation
- [ ] Role-based/policy-based access control implementation reviewed
- [ ] API authentication security assessed

### Data Protection
- [ ] Sensitive data encryption verified (Data Protection API, at rest and in transit)
- [ ] Personally Identifiable Information (PII) handling reviewed
- [ ] Data exposure in logs/errors evaluated
- [ ] Database security assessed (parameterized queries, encryption)
- [ ] File upload security verified
- [ ] Data retention and deletion practices reviewed

### Secrets Management
- [ ] Hardcoded credentials searched and documented
- [ ] API keys and tokens in code identified
- [ ] Configuration sources verified (User Secrets, Azure Key Vault)
- [ ] Secret management system evaluated
- [ ] appsettings.json security checked

### Input Validation & Sanitization
- [ ] User input validation comprehensiveness assessed
- [ ] Input sanitization for SQL/command injection verified
- [ ] Model validation attributes usage checked
- [ ] API input validation evaluated
- [ ] Deserialization security reviewed (JSON.NET, System.Text.Json)

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Security Review

Please perform a comprehensive security review of this C# project following this protocol:

## Phase 1: Automated Vulnerability Scanning

1. **Dependency Vulnerability Scan**
   ```powershell
   # Scan for known vulnerabilities in NuGet packages
   dotnet list package --vulnerable
   dotnet list package --vulnerable --include-transitive

   # Check for outdated packages
   dotnet list package --outdated
   ```

2. **Static Security Analysis**
   ```powershell
   # Add SecurityCodeScan.VS2019 analyzer
   dotnet add package SecurityCodeScan.VS2019

   # Build with security analyzers
   dotnet build

   # Or use SonarAnalyzer for additional security rules
   dotnet add package SonarAnalyzer.CSharp
   ```

3. **Secret Detection**
   ```powershell
   # Check for hardcoded secrets in code
   # Use git-secrets or truffleHog

   # Verify user secrets not committed
   # Check .gitignore includes:
   # appsettings.Development.json (if contains secrets)
   # *.user
   # secrets.json
   ```

## Phase 2: OWASP Top 10 Assessment

For each OWASP vulnerability category, systematically review the codebase:

1. **A01: Broken Access Control**
   - Review authorization attributes on controllers/actions ([Authorize], [AllowAnonymous])
   - Check for missing authorization checks
   - Verify users cannot access resources beyond permissions
   - Test for horizontal/vertical privilege escalation
   - Review policy-based authorization implementation
   - Example locations: API endpoints, MVC actions, Razor Pages

2. **A02: Cryptographic Failures**
   - Search for weak hashing algorithms (MD5, SHA1)
   - Verify HTTPS enforcement (UseHttpsRedirection, RequireHttpsAttribute)
   - Check database encryption for sensitive fields
   - Review password storage (ASP.NET Core Identity uses PBKDF2)
   - Identify sensitive data in logs or error messages
   - Check Data Protection API usage for encrypting sensitive data

3. **A03: Injection**
   - **SQL Injection**: Verify parameterized queries (Entity Framework, Dapper)
   - **Command Injection**: Check Process.Start, CMD execution with user input
   - **LDAP Injection**: Review directory query construction
   - **Expression Injection**: Check dynamic LINQ or expression compilation
   - Search patterns:
     ```csharp
     // Dangerous patterns
     string sql = "SELECT * FROM Users WHERE Id = " + userId; // DON'T
     context.Database.ExecuteSqlRaw($"SELECT * FROM Users WHERE Name = '{name}'"); // DON'T
     Process.Start("cmd.exe", $"/c {userInput}"); // DON'T

     // Safe patterns
     context.Users.Where(u => u.Id == userId); // DO
     context.Database.ExecuteSqlRaw("SELECT * FROM Users WHERE Name = {0}", name); // DO
     ```

4. **A04: Insecure Design**
   - Review architecture for security anti-patterns
   - Assess threat modeling evidence
   - Check security requirements in design docs
   - Evaluate secure development lifecycle integration

5. **A05: Security Misconfiguration**
   - Check for debug mode in production (ASPNETCORE_ENVIRONMENT)
   - Review default configurations
   - Verify error messages don't leak sensitive information (UseDeveloperExceptionPage)
   - Check for exposed admin interfaces
   - Review CORS configuration (UseCors)
   - Assess security headers (HSTS, CSP, X-Frame-Options)
   ```csharp
   // Check for proper configuration
   if (!app.Environment.IsDevelopment())
   {
       app.UseExceptionHandler("/Error");
       app.UseHsts();
   }
   ```

6. **A06: Vulnerable and Outdated Components**
   - Cross-reference NuGet package vulnerabilities from Phase 1
   - Identify packages without security patches
   - Check for deprecated packages
   - Review transitive dependency risks
   - Verify .NET framework/runtime is up to date

7. **A07: Identification and Authentication Failures**
   - Review password complexity requirements (ASP.NET Core Identity options)
   - Check for weak session management
   - Verify multi-factor authentication implementation
   - Assess brute-force protection (account lockout)
   - Check for authentication bypass vulnerabilities
   ```csharp
   // Review Identity configuration
   services.Configure<IdentityOptions>(options =>
   {
       options.Password.RequireDigit = true;
       options.Password.RequiredLength = 8;
       options.Lockout.MaxFailedAccessAttempts = 5;
       options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(15);
   });
   ```

8. **A08: Software and Data Integrity Failures**
   - Review CI/CD pipeline security
   - Check code signing and verification
   - Assess deserialization security (JSON, XML, BinaryFormatter)
   - Verify update mechanisms security
   ```csharp
   // Dangerous: BinaryFormatter
   var formatter = new BinaryFormatter();
   var obj = formatter.Deserialize(stream); // CRITICAL - allows arbitrary code execution

   // Safer: JSON with type handling disabled
   var settings = new JsonSerializerSettings
   {
       TypeNameHandling = TypeNameHandling.None
   };
   ```

9. **A09: Security Logging and Monitoring Failures**
   - Assess logging comprehensiveness (ILogger usage)
   - Check for sensitive data in logs
   - Review log retention and protection
   - Verify alerting on suspicious activities
   - Check audit trail completeness

10. **A10: Server-Side Request Forgery (SSRF)**
    - Review URL handling and validation
    - Check for unvalidated redirects
    - Assess internal service requests (HttpClient usage)
    - Verify allowlist/blocklist for external requests

## Phase 3: Authentication & Authorization Deep Dive

1. **Password Security**
   ```csharp
   // Check ASP.NET Core Identity configuration
   services.Configure<IdentityOptions>(options =>
   {
       // Password settings
       options.Password.RequireDigit = true;
       options.Password.RequireLowercase = true;
       options.Password.RequireUppercase = true;
       options.Password.RequireNonAlphanumeric = true;
       options.Password.RequiredLength = 8;
   });

   // If custom password hashing, ensure proper algorithm
   // Good: BCrypt.Net, PBKDF2 (used by Identity)
   // Bad: MD5, SHA1, plain text
   ```

2. **JWT Token Security**
   ```csharp
   // Review JWT configuration
   services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
       .AddJwtBearer(options =>
       {
           options.TokenValidationParameters = new TokenValidationParameters
           {
               ValidateIssuer = true,
               ValidateAudience = true,
               ValidateLifetime = true,
               ValidateIssuerSigningKey = true,
               ClockSkew = TimeSpan.Zero // Important: reduces token lifetime tolerance
           };
       });
   ```

3. **Authorization Patterns**
   ```csharp
   // Verify authorization on all protected endpoints
   [Authorize] // Good
   [Authorize(Policy = "AdminOnly")] // Better: policy-based
   [Authorize(Roles = "Admin,Manager")] // Role-based

   // Check for missing authorization
   public IActionResult SensitiveAction() // BAD: No [Authorize]
   {
       // Sensitive operation
   }
   ```

## Phase 4: Data Protection Review

1. **Sensitive Data Identification**
   - Identify PII (names, emails, addresses, phone numbers)
   - Locate financial data (credit cards, bank accounts)
   - Find health information (PHI/medical data)
   - Document authentication credentials

2. **Encryption Assessment**
   ```csharp
   // Check for proper encryption usage
   // Good: ASP.NET Core Data Protection API
   var protector = dataProtectionProvider.CreateProtector("MyPurpose");
   string encrypted = protector.Protect(sensitiveData);

   // Good: Manual encryption with proper algorithm
   using var aes = Aes.Create();
   aes.KeySize = 256;
   aes.GenerateKey();
   aes.GenerateIV();

   // Bad: Weak or custom crypto
   // Base64 is encoding, not encryption!
   Convert.ToBase64String(Encoding.UTF8.GetBytes(secret)); // WARNING

   // Bad: DES, RC2 (deprecated algorithms)
   ```

3. **Data Exposure Risks**
   - Search for sensitive data in:
     - Exception messages and stack traces
     - Log files (ILogger calls)
     - Debug output
     - API responses
     - Connection strings in logs

## Phase 5: Input Validation & Sanitization

1. **SQL Injection Protection**
   ```csharp
   // Review all database queries
   // Good: Entity Framework LINQ
   var user = context.Users.FirstOrDefault(u => u.Id == userId);

   // Good: Parameterized queries
   context.Database.ExecuteSqlRaw("SELECT * FROM Users WHERE Id = {0}", userId);

   // Good: Dapper with parameters
   connection.Query<User>("SELECT * FROM Users WHERE Id = @Id", new { Id = userId });

   // Bad: String concatenation or interpolation
   context.Database.ExecuteSqlRaw($"SELECT * FROM Users WHERE Id = {userId}"); // CRITICAL
   var sql = "SELECT * FROM Users WHERE Name = '" + name + "'"; // CRITICAL
   ```

2. **Command Injection Protection**
   ```csharp
   // Review Process.Start and command execution
   // Bad: Shell execution with user input
   Process.Start("cmd.exe", $"/c {userCommand}"); // CRITICAL

   // Better: Whitelist commands
   var allowedCommands = new[] { "list", "status", "info" };
   if (allowedCommands.Contains(userCommand))
   {
       Process.Start("myapp.exe", userCommand);
   }

   // Best: Avoid shell commands entirely
   ```

3. **Deserialization Security**
   ```csharp
   // Check for unsafe deserialization
   // Critical: BinaryFormatter with untrusted data
   var formatter = new BinaryFormatter();
   var obj = formatter.Deserialize(stream); // CRITICAL - RCE vulnerability

   // Bad: XML deserialization without restrictions
   var serializer = new XmlSerializer(typeof(MyClass));
   var obj = serializer.Deserialize(reader); // Can be exploited

   // Good: JSON with type handling disabled
   var options = new JsonSerializerOptions
   {
       // Don't enable TypeInfoResolver for untrusted data
   };
   var obj = JsonSerializer.Deserialize<MyClass>(json, options);
   ```

4. **Model Validation**
   ```csharp
   // Check for proper validation attributes
   public class UserDto
   {
       [Required]
       [StringLength(100, MinimumLength = 3)]
       public string Username { get; set; }

       [Required]
       [EmailAddress]
       public string Email { get; set; }

       [Range(18, 120)]
       public int Age { get; set; }
   }

   // Verify ModelState is checked
   [HttpPost]
   public IActionResult CreateUser(UserDto dto)
   {
       if (!ModelState.IsValid) // Good: validation check
           return BadRequest(ModelState);

       // Process valid data
   }
   ```

5. **File Upload Security**
   ```csharp
   // Check file upload handling
   [HttpPost]
   public async Task<IActionResult> Upload(IFormFile file)
   {
       // Good: Validate file type (not just extension)
       var allowedTypes = new[] { "image/jpeg", "image/png" };
       if (!allowedTypes.Contains(file.ContentType))
           return BadRequest("Invalid file type");

       // Good: Validate file size
       if (file.Length > 5 * 1024 * 1024) // 5MB
           return BadRequest("File too large");

       // Good: Sanitize filename
       var filename = Path.GetRandomFileName();

       // Good: Store outside web root
       var path = Path.Combine(_secureStoragePath, filename);

       await using var stream = System.IO.File.Create(path);
       await file.CopyToAsync(stream);
   }
   ```

## Phase 6: Secrets Management

1. **Hardcoded Secrets Search**
   ```powershell
   # Search for common secret patterns in code
   findstr /S /I "password.*=" *.cs
   findstr /S /I "apikey.*=" *.cs
   findstr /S /I "connectionstring.*=" *.cs
   ```

2. **Configuration Security Review**
   ```csharp
   // Bad: Secrets in appsettings.json committed to git
   {
     "ConnectionStrings": {
       "Default": "Server=prod;Password=secret123;" // DON'T
     }
   }

   // Good: Use User Secrets (development)
   // dotnet user-secrets set "ConnectionStrings:Default" "..."

   // Good: Use Azure Key Vault (production)
   builder.Configuration.AddAzureKeyVault(
       new Uri("https://myvault.vault.azure.net/"),
       new DefaultAzureCredential());

   // Good: Environment variables
   var connectionString = Environment.GetEnvironmentVariable("DB_CONNECTION");
   ```

3. **Configuration File Review**
   - Check appsettings.json for secrets
   - Verify sensitive config in appsettings.Development.json
   - Check .gitignore includes sensitive files
   - Review connection string storage

## Phase 7: ASP.NET Core Specific Security

1. **Cross-Site Request Forgery (CSRF)**
   ```csharp
   // Verify anti-forgery tokens on state-changing operations
   [HttpPost]
   [ValidateAntiForgeryToken] // Good
   public IActionResult Update(Model model)
   {
       // Process update
   }

   // For APIs, verify proper CORS configuration
   services.AddCors(options =>
   {
       options.AddPolicy("MyPolicy", builder =>
       {
           builder.WithOrigins("https://trusted-origin.com") // Specific origins
                  .AllowAnyMethod()
                  .AllowAnyHeader();
       });
   });
   ```

2. **Cross-Site Scripting (XSS)**
   ```csharp
   // Razor automatically HTML-encodes output
   <p>@Model.UserInput</p> // Good: auto-encoded

   // Bad: Bypassing encoding
   <p>@Html.Raw(Model.UserInput)</p> // Dangerous!

   // For APIs, ensure proper content-type headers
   return Json(data); // Good: application/json
   ```

3. **Security Headers**
   ```csharp
   // Configure security headers
   app.UseHsts();
   app.UseHttpsRedirection();

   // Add custom security headers
   app.Use(async (context, next) =>
   {
       context.Response.Headers.Add("X-Content-Type-Options", "nosniff");
       context.Response.Headers.Add("X-Frame-Options", "DENY");
       context.Response.Headers.Add("X-XSS-Protection", "1; mode=block");
       context.Response.Headers.Add("Referrer-Policy", "no-referrer");
       context.Response.Headers.Add("Content-Security-Policy",
           "default-src 'self'; script-src 'self'");
       await next();
   });
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

### NuGet Package Vulnerabilities
| Package | Current Version | Vulnerable | CVE | Severity | Fixed Version |
|---------|----------------|------------|-----|----------|---------------|
| [name] | [version] | [Yes/No] | [CVE-ID] | [Critical/High/Med/Low] | [version] |

### Secrets & Credentials Exposure
- **Hardcoded Secrets Found**: [count]
- **Locations**: [list of files and lines]
- **Types**: [API keys, passwords, connection strings, etc.]
- **Git History Scan**: [secrets in commit history: yes/no]

### Authentication & Authorization
- **Password Storage**: [secure/insecure and method]
- **Session Management**: [secure/issues found]
- **Authorization Coverage**: [percentage of endpoints protected]
- **JWT Security**: [proper/issues found]
- **Issues Identified**: [list of specific problems]

### Data Protection
- **Sensitive Data Inventory**: [types and locations]
- **Encryption at Rest**: [implemented/missing]
- **Encryption in Transit**: [TLS/HTTPS status]
- **PII Exposure Risks**: [high/medium/low and locations]
- **Data Protection API Usage**: [proper/not used]

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
```xml
<!-- Add to Directory.Build.props -->
<ItemGroup>
  <PackageReference Include="SecurityCodeScan.VS2019" Version="5.6.7" PrivateAssets="all" />
  <PackageReference Include="SonarAnalyzer.CSharp" Version="9.12.0" PrivateAssets="all" />
</ItemGroup>
```

```yaml
# CI/CD integration (GitHub Actions example)
- name: Security scan
  run: dotnet list package --vulnerable --include-transitive

- name: Dependency check
  uses: dependency-check/Dependency-Check_Action@main
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
- [ ] Configure Azure Security Center or similar monitoring

## Notes
- **Confidentiality**: This security report contains sensitive information - handle appropriately
- **Responsible Disclosure**: If third-party vulnerabilities found, follow responsible disclosure
- **Retest**: After remediation, rerun security scans to verify fixes
- **Continuous Monitoring**: Implement ongoing security scanning (dotnet list package --vulnerable in CI)
~~~
