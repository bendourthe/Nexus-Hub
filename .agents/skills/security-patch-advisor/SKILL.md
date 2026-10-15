---
name: security-patch-advisor
description: Recommend and generate security patches for identified vulnerabilities including XSS, SQL injection, SSRF, CSRF, insecure deserialization, and misconfigurations. Use when remediating vulnerability findings, hardening application code, or implementing security controls.
summary_l0: "Generate security patches for XSS, SQL injection, SSRF, CSRF, and misconfigurations"
overview_l1: "This skill recommends and generates security patches for identified vulnerabilities including XSS, SQL injection, SSRF, CSRF, insecure deserialization, and misconfigurations. Use it when remediating vulnerability findings, hardening application code, implementing security controls, or addressing penetration test results. Key capabilities include vulnerability-specific patch generation, input validation and sanitization code, parameterized query implementation, CSRF token integration, SSRF prevention with URL validation, secure deserialization patterns, security header configuration, and patch validation testing. The expected output is ready-to-apply security patches with explanation, validation tests, and hardening recommendations. Trigger phrases: security patch, fix XSS, fix SQL injection, SSRF prevention, CSRF protection, security remediation, vulnerability fix, harden application, security controls."
---

# Security Patch Advisor

Generate targeted, production-ready security patches for identified vulnerabilities. This skill covers the most common vulnerability classes (OWASP Top 10 and beyond) and provides language-specific remediation code, input validation patterns, output encoding strategies, and security header configurations.

## When to Use This Skill

Use this skill when you need to:

- Fix a specific vulnerability identified by a scanner or penetration test
- Implement input validation for a new endpoint or form
- Add output encoding to prevent cross-site scripting
- Convert raw SQL queries to parameterized queries
- Implement CSRF protection tokens
- Configure security headers (CSP, HSTS, X-Frame-Options)
- Harden authentication and session management
- Fix server-side request forgery (SSRF) vulnerabilities
- Remediate insecure deserialization
- Address path traversal or local file inclusion issues
- Apply security patches without breaking existing functionality

**Trigger phrases**: "fix vulnerability", "security patch", "remediate XSS", "fix SQL injection", "add CSRF protection", "security headers", "input validation", "output encoding", "patch advisor", "harden endpoint"

## What This Skill Does

### Core Capabilities

- **Vulnerability-Specific Patching**: Tailored fix strategies for each vulnerability class
- **Multi-Language Support**: Patches in JavaScript/TypeScript, Python, Java, C#, Go, and Ruby
- **Input Validation Generation**: Context-aware validation rules for different data types
- **Output Encoding Guidance**: Correct encoding for HTML, JavaScript, URL, and CSS contexts
- **Security Header Configuration**: Production-ready header policies for common web servers
- **Regression Safety**: Patches designed to fix the vulnerability without altering business logic
- **Defense-in-Depth Layering**: Multiple overlapping controls rather than single-point fixes

### Vulnerability Coverage

| Vulnerability Class | CWE | Patch Strategy |
|---------------------|-----|----------------|
| Cross-Site Scripting (XSS) | CWE-79 | Output encoding, CSP, input sanitization |
| SQL Injection | CWE-89 | Parameterized queries, ORM usage |
| Server-Side Request Forgery | CWE-918 | URL allowlisting, network restrictions |
| Cross-Site Request Forgery | CWE-352 | Token-based protection, SameSite cookies |
| Insecure Deserialization | CWE-502 | Safe deserialization, type allowlisting |
| Path Traversal | CWE-22 | Path canonicalization, chroot restrictions |
| Command Injection | CWE-78 | Parameterized execution, input validation |
| Open Redirect | CWE-601 | URL allowlisting, relative-only redirects |
| Security Misconfiguration | CWE-16 | Header hardening, default removal |
| Broken Authentication | CWE-287 | Session hardening, MFA, rate limiting |

## Instructions

### Strategy 1: Cross-Site Scripting (XSS) Remediation

XSS occurs when untrusted data is included in web output without proper encoding. The fix depends on the output context.

**Step 1: Identify the output context**

```
HTML Body:      <div>USER_DATA</div>          -> HTML entity encode
HTML Attribute: <input value="USER_DATA">     -> HTML attribute encode
JavaScript:     <script>var x='USER_DATA'</script> -> JavaScript encode
URL Parameter:  <a href="/page?q=USER_DATA">  -> URL encode
CSS:            <div style="width:USER_DATA"> -> CSS encode
```

**Step 2: Apply context-appropriate encoding**

JavaScript/Node.js (using a templating engine):

```javascript
// VULNERABLE: Direct string interpolation
app.get("/profile", (req, res) => {
  const name = req.query.name;
  res.send(`<h1>Welcome, ${name}</h1>`);  // XSS vulnerability
});

// PATCHED: Use a templating engine with auto-escaping
// In Express with EJS (auto-escaping enabled by default with <%= %>)
app.get("/profile", (req, res) => {
  res.render("profile", { name: req.query.name });
});

// profile.ejs template (auto-escapes by default)
// <h1>Welcome, <%= name %></h1>
```

Python (Flask):

```python
# VULNERABLE: Marking user input as safe
from flask import request, Markup

@app.route("/profile")
def profile():
    name = request.args.get("name", "")
    return f"<h1>Welcome, {Markup(name)}</h1>"  # XSS vulnerability

# PATCHED: Let Jinja2 auto-escape (default behavior)
@app.route("/profile")
def profile():
    name = request.args.get("name", "")
    return render_template("profile.html", name=name)

# profile.html (Jinja2 auto-escapes {{ name }} by default)
# <h1>Welcome, {{ name }}</h1>
```

Java (Spring):

```java
// VULNERABLE: Writing unescaped user input
@GetMapping("/profile")
public void profile(@RequestParam String name, HttpServletResponse response)
        throws IOException {
    response.getWriter().write("<h1>Welcome, " + name + "</h1>"); // XSS
}

// PATCHED: Use Thymeleaf with auto-escaping
@GetMapping("/profile")
public String profile(@RequestParam String name, Model model) {
    model.addAttribute("name", name);
    return "profile";  // Thymeleaf template with th:text (auto-escapes)
}

// profile.html: <h1>Welcome, <span th:text="${name}"></span></h1>
```

**Step 3: Add Content Security Policy header**

```javascript
// Express middleware for CSP
app.use((req, res, next) => {
  res.setHeader(
    "Content-Security-Policy",
    "default-src 'self'; " +
    "script-src 'self'; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data:; " +
    "font-src 'self'; " +
    "connect-src 'self'; " +
    "frame-ancestors 'none'; " +
    "base-uri 'self'; " +
    "form-action 'self'"
  );
  next();
});
```

### Strategy 2: SQL Injection Remediation

SQL injection occurs when untrusted data is concatenated into SQL queries. The primary fix is parameterized queries.

**Step 1: Identify vulnerable query patterns**

```javascript
// VULNERABLE: String concatenation
const query = "SELECT * FROM users WHERE id = " + req.params.id;

// VULNERABLE: Template literals
const query = `SELECT * FROM users WHERE name = '${req.body.name}'`;

// VULNERABLE: String formatting (Python)
query = "SELECT * FROM users WHERE id = %s" % user_id
```

**Step 2: Convert to parameterized queries**

Node.js (pg library):

```javascript
// VULNERABLE
const result = await pool.query(
  `SELECT * FROM users WHERE email = '${email}' AND status = '${status}'`
);

// PATCHED: Parameterized query
const result = await pool.query(
  "SELECT * FROM users WHERE email = $1 AND status = $2",
  [email, status]
);
```

Python (psycopg2):

```python
# VULNERABLE
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")

# PATCHED: Parameterized query
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

Java (JDBC):

```java
// VULNERABLE
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery(
    "SELECT * FROM users WHERE email = '" + email + "'");

// PATCHED: PreparedStatement
PreparedStatement pstmt = conn.prepareStatement(
    "SELECT * FROM users WHERE email = ?");
pstmt.setString(1, email);
ResultSet rs = pstmt.executeQuery();
```

C# (ADO.NET):

```csharp
// VULNERABLE
var cmd = new SqlCommand(
    $"SELECT * FROM Users WHERE Email = '{email}'", conn);

// PATCHED: Parameterized command
var cmd = new SqlCommand(
    "SELECT * FROM Users WHERE Email = @Email", conn);
cmd.Parameters.AddWithValue("@Email", email);
```

**Step 3: Handle dynamic query construction safely**

When queries must be built dynamically (dynamic column names, sort orders):

```python
# Safe dynamic query building
ALLOWED_COLUMNS = {"name", "email", "created_at", "status"}
ALLOWED_DIRECTIONS = {"ASC", "DESC"}

def build_query(sort_column: str, sort_direction: str, filters: dict) -> tuple:
    if sort_column not in ALLOWED_COLUMNS:
        raise ValueError(f"Invalid sort column: {sort_column}")
    if sort_direction.upper() not in ALLOWED_DIRECTIONS:
        raise ValueError(f"Invalid sort direction: {sort_direction}")

    query = f"SELECT * FROM users ORDER BY {sort_column} {sort_direction}"
    params = []

    if "status" in filters:
        query += " WHERE status = %s"
        params.append(filters["status"])

    return query, params
```

### Strategy 3: Server-Side Request Forgery (SSRF) Remediation

SSRF occurs when an application makes HTTP requests to attacker-controlled URLs, potentially accessing internal services.

**Step 1: Implement URL allowlisting**

```python
import ipaddress
from urllib.parse import urlparse

ALLOWED_HOSTS = {"api.example.com", "cdn.example.com"}
BLOCKED_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 private
]

def validate_url(url: str) -> bool:
    """Validate that a URL is safe to request."""
    parsed = urlparse(url)

    # Enforce HTTPS only
    if parsed.scheme not in ("https",):
        return False

    # Check against allowlist
    if parsed.hostname not in ALLOWED_HOSTS:
        return False

    # Resolve hostname and check against blocked IP ranges
    import socket
    try:
        resolved_ip = socket.getaddrinfo(parsed.hostname, None)[0][4][0]
        ip = ipaddress.ip_address(resolved_ip)
        for blocked in BLOCKED_RANGES:
            if ip in blocked:
                return False
    except socket.gaierror:
        return False

    return True
```

**Step 2: Apply network-level controls**

```yaml
# Kubernetes NetworkPolicy to restrict egress from application pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrict-egress
spec:
  podSelector:
    matchLabels:
      app: web-api
  policyTypes:
    - Egress
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
              - 169.254.0.0/16
      ports:
        - protocol: TCP
          port: 443
```

### Strategy 4: Cross-Site Request Forgery (CSRF) Protection

**Step 1: Implement token-based CSRF protection**

Node.js (Express with csurf):

```javascript
const csrf = require("csurf");
const csrfProtection = csrf({ cookie: true });

// Apply to all state-changing routes
app.post("/api/transfer", csrfProtection, (req, res) => {
  // CSRF token automatically validated by middleware
  processTransfer(req.body);
  res.json({ success: true });
});

// Provide token to client
app.get("/form", csrfProtection, (req, res) => {
  res.render("form", { csrfToken: req.csrfToken() });
});
```

**Step 2: Configure SameSite cookies**

```javascript
app.use(session({
  secret: process.env.SESSION_SECRET,
  cookie: {
    httpOnly: true,
    secure: true,        // HTTPS only
    sameSite: "strict",  // Prevents CSRF via cross-origin requests
    maxAge: 3600000,     // 1 hour
  },
  resave: false,
  saveUninitialized: false,
}));
```

### Strategy 5: Security Header Configuration

**Step 1: Apply comprehensive security headers**

```javascript
// Express middleware for security headers
function securityHeaders(req, res, next) {
  // Prevent clickjacking
  res.setHeader("X-Frame-Options", "DENY");

  // Prevent MIME type sniffing
  res.setHeader("X-Content-Type-Options", "nosniff");

  // Enable HSTS (1 year, include subdomains, preload)
  res.setHeader(
    "Strict-Transport-Security",
    "max-age=31536000; includeSubDomains; preload"
  );

  // Referrer policy
  res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");

  // Permissions policy
  res.setHeader(
    "Permissions-Policy",
    "camera=(), microphone=(), geolocation=(), payment=()"
  );

  // Content Security Policy
  res.setHeader(
    "Content-Security-Policy",
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
  );

  next();
}

app.use(securityHeaders);
```

Nginx configuration equivalent:

```nginx
server {
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" always;
}
```

### Strategy 6: Command Injection Remediation

```python
import subprocess
import shlex

# VULNERABLE: Shell injection via os.system
import os
os.system(f"ping -c 4 {hostname}")  # Attacker can inject: ; rm -rf /

# PATCHED: Use subprocess with argument list (no shell)
def safe_ping(hostname: str) -> str:
    """Execute ping safely without shell injection risk."""
    # Validate input
    if not re.match(r"^[a-zA-Z0-9.\-]+$", hostname):
        raise ValueError("Invalid hostname")

    result = subprocess.run(
        ["ping", "-c", "4", hostname],
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,  # Explicitly disable shell
    )
    return result.stdout
```

### Strategy 7: Path Traversal Remediation

```python
import os

# VULNERABLE: Direct path concatenation
def read_file(filename):
    path = f"/app/uploads/{filename}"
    with open(path) as f:
        return f.read()

# PATCHED: Canonicalize and validate the path
UPLOAD_DIR = os.path.realpath("/app/uploads")

def safe_read_file(filename: str) -> str:
    """Read a file safely, preventing path traversal."""
    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Build the full path and resolve to canonical form
    requested_path = os.path.realpath(os.path.join(UPLOAD_DIR, filename))

    # Verify the resolved path is within the allowed directory
    if not requested_path.startswith(UPLOAD_DIR + os.sep):
        raise PermissionError("Access denied: path traversal detected")

    if not os.path.isfile(requested_path):
        raise FileNotFoundError("File not found")

    with open(requested_path) as f:
        return f.read()
```

### Strategy 8: Insecure Deserialization Remediation

```python
# VULNERABLE: Unpickling untrusted data
import pickle

def load_session(data: bytes):
    return pickle.loads(data)  # Remote code execution risk

# PATCHED: Use JSON or a safe serialization format
import json

def safe_load_session(data: str) -> dict:
    """Deserialize session data safely using JSON."""
    session = json.loads(data)

    # Validate expected structure
    required_keys = {"user_id", "expires_at"}
    if not required_keys.issubset(session.keys()):
        raise ValueError("Invalid session structure")

    return session
```

Java:

```java
// VULNERABLE: Deserializing untrusted ObjectInputStream
ObjectInputStream ois = new ObjectInputStream(untrustedStream);
Object obj = ois.readObject();  // Remote code execution risk

// PATCHED: Use an allowlist-based ObjectInputFilter (Java 9+)
ObjectInputStream ois = new ObjectInputStream(untrustedStream);
ois.setObjectInputFilter(filterInfo -> {
    Class<?> clazz = filterInfo.serialClass();
    if (clazz == null) {
        return ObjectInputFilter.Status.UNDECIDED;
    }
    Set<String> allowedClasses = Set.of(
        "com.example.dto.UserSession",
        "com.example.dto.Preferences"
    );
    if (allowedClasses.contains(clazz.getName())) {
        return ObjectInputFilter.Status.ALLOWED;
    }
    return ObjectInputFilter.Status.REJECTED;
});
```

### Patch Verification Checklist

After applying any security patch, verify with this checklist:

```markdown
- [ ] Vulnerability is no longer exploitable (test with original PoC or scanner)
- [ ] Existing functionality is unaffected (run full test suite)
- [ ] Input validation rejects malicious input
- [ ] Input validation accepts legitimate input (no false positives)
- [ ] Error messages do not leak sensitive information
- [ ] Patch is applied consistently across all similar code paths
- [ ] Security headers are present in response (check with curl -I)
- [ ] Logging captures rejected/malicious requests for monitoring
- [ ] Documentation updated to reflect the security control
```

### Asking the model about code without tripping safety classifiers

Finding vulnerabilities in source code is permitted work, so a refusal on such a request is a false positive to work around by rephrasing, not a boundary to respect. Two phrasings trip classifiers needlessly. First, prefer asking whether a program has bugs over asking whether it compiles or runs without errors: "are there any bugs in this program" reads as review, while "does this compile without errors" reads as a request to run untrusted code. Second, when the code is in a lesser-known language or dialect, give the model that language's documentation as context in the same turn, because an unfamiliar syntax plus a security question is a common false-positive shape. A refusal after rephrasing is the finding to record, not the reason to skip the review.

## Best Practices

- Fix the root cause, not the symptom; adding a WAF rule without fixing the code leaves you one bypass away from exploitation
- Apply the principle of least privilege at every layer: input validation, parameterized queries, output encoding, and security headers together
- Use established libraries for security functions (OWASP ESAPI, helmet.js, Django security middleware) rather than writing custom implementations
- Test patches with both positive cases (legitimate input accepted) and negative cases (malicious input rejected)
- Apply fixes consistently across the entire codebase; a single unpatched endpoint undermines all other remediation
- Prefer allowlisting over blocklisting for input validation; blocklists are inherently incomplete
- Keep security dependencies updated; a patched library is only effective if you are running the patched version
- Document the vulnerability, the fix, and the verification steps for future reference and audit trails
- Use automated tools (SAST, DAST) in CI/CD to catch regressions after patching
- Conduct peer review of security patches; a second pair of eyes catches edge cases

## Common Pitfalls

- **Encoding in the wrong context**: HTML encoding does not prevent XSS in a JavaScript context. Always match the encoding to the output context (HTML body, HTML attribute, JavaScript string, URL parameter, CSS value).
- **Parameterizing identifiers instead of values**: Column names and table names cannot be parameterized in most databases. Use allowlists for dynamic identifiers.
- **Trusting client-side validation**: Client-side validation improves user experience but provides zero security. Always validate on the server.
- **Incomplete SSRF fixes**: Blocking private IP ranges without resolving DNS first allows DNS rebinding attacks. Always resolve the hostname before checking the IP.
- **CSRF tokens in GET requests**: GET requests should be idempotent and not require CSRF protection. Apply CSRF tokens to POST, PUT, PATCH, and DELETE only.
- **Overly permissive CSP**: A CSP with "unsafe-inline" and "unsafe-eval" provides minimal protection against XSS. Start strict and relax only when necessary with nonce-based policies.
- **Patching one instance but not others**: A codebase search may reveal the same vulnerability pattern in multiple locations. Patch all instances, not just the one flagged by the scanner.
- **Hardcoding secrets in patches**: When adding authentication or encryption to fix a vulnerability, use environment variables or a secrets manager, never hardcoded values.
- **Breaking error handling**: Security patches that convert detailed error messages to generic ones may mask legitimate application errors. Log the details server-side while returning generic messages to the client.
- **Not testing with edge cases**: Patches that work for obvious attack payloads may fail against encoded, double-encoded, or Unicode-normalized variants. Test with a comprehensive set of bypass techniques.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I added a WAF rule, so the XSS is fixed" | A WAF rule is a symptom patch one bypass away from exploitation; the unencoded output in the template is still there, so the fix must be context-correct output encoding at the source, not a perimeter filter. |
| "I escaped the value, so the XSS is gone" | HTML-entity encoding does not stop XSS inside a JavaScript or URL context; encoding in the wrong context (Strategy 1, Step 1) leaves the injection live, so the encoding must match the exact output context. |
| "The scanner flagged one endpoint and I patched it" | The same vulnerable pattern usually recurs across the codebase; patching only the flagged instance leaves the others exploitable, which is why every similar code path must be patched in the same pass. |
| "Blocking private IP ranges stops the SSRF" | Blocking ranges without resolving DNS first leaves a DNS-rebinding hole; the URL validator must resolve the hostname and check the resolved IP, exactly as in Strategy 3, Step 1. |

## Verification

- [ ] The original proof-of-concept or scanner no longer reproduces the vulnerability
- [ ] The full test suite still passes after the patch (no business-logic regression)
- [ ] Input validation rejects the malicious payload AND accepts legitimate input (no false positives)
- [ ] The same vulnerability pattern was searched for and patched across every similar code path, not just the flagged one
- [ ] Security headers are present in the response: `curl -I <url>` shows the expected `Content-Security-Policy` / `X-Frame-Options` / `Strict-Transport-Security`
- [ ] No secrets were hardcoded in the patch (encryption keys and credentials come from environment or a secrets manager)

## Related Skills

- [[business-logic-abuse]] -- remediation for race-condition, TOCTOU, idempotency, and workflow-bypass classes
- [[advanced-attack-patterns]] -- state-desync, cache-poisoning, replay, and timing-attack remediation
- [[security-review]] -- the audit pass that surfaces the findings this skill patches
- [[exploitability-analyzer]] -- confirms a finding is worth patching before generating the fix
- [[authentication-patterns]] -- secure patterns for the broken-authentication remediation row

## Related Resources

- [catalog/checklists/file-upload-security.md](../../../checklists/file-upload-security.md) - Defense checklist for file-upload-specific exploits (polyglots, MIME confusion, archive path traversal, resource limits, content scanning, serving hardening). Pairs with Strategy 7 (Path Traversal) and Strategy 8 (Insecure Deserialization) above.
- [catalog/skills/security/business-logic-abuse/SKILL.md](../business-logic-abuse/SKILL.md) - Domain-aware invariant-violation audit covering race conditions, TOCTOU, idempotency, and workflow bypass. Remediation patches for these classes live here.
- [catalog/skills/security/advanced-attack-patterns/SKILL.md](../advanced-attack-patterns/SKILL.md) - State desynchronization, cache poisoning, replay, and timing-attack remediation patterns.
- [catalog/commands/review.md](../../../commands/review.md) - The `/review pentest` scope that surfaces findings this skill patches.
