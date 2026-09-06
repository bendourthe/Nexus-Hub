---
name: advanced-attack-patterns
description: Advanced and web-application attack classes beyond the OWASP Top 10 baseline -- architectural classes (state desynchronization, cache poisoning, replay, timing side channels) plus the attacker-perspective injection and access-control vectors that baseline reviews under-test (SSRF, SSTI, XXE, insecure deserialization, HTTP request smuggling, IDOR). Each class is gated on an applicability check so the audit only engages where the attack surface exists, and every vector is framed to strengthen `/review security` and `/run-penetration-test --depth=deep`. Use when extending a baseline security review, auditing distributed / cache-heavy architectures, or red-teaming a web application under authorization. SKIP, do NOT use for, generic input-validation lint (use security-review), business-rule abuse such as pricing or refund manipulation (use business-logic-abuse), or any test without documented authorization and scope.
summary_l0: "Advanced and web-app attack surfaces: state desync, cache poisoning, SSRF, XXE, deserialization, request smuggling, IDOR"
overview_l1: "This skill covers advanced and web-application attack classes that generic OWASP Top 10 reviews under-test. The first family is architectural -- distributed-state divergence, HTTP cache manipulation, protocol-level replay, and timing side channels -- which input-validation scanners never inspect. The second family is the attacker-perspective injection and access-control surface: server-side request forgery, server-side template injection, XML external entities, insecure deserialization, HTTP request smuggling, and insecure direct object reference. Each class opens with an applicability check so the audit stays high-signal, and every web-app vector is framed to strengthen `/review security` and the `/run-penetration-test --depth=deep` advanced-attacks hunter. Deep per-vector payloads live in `references/web-appsec-methodology.md`. The expected output is a findings table keyed by attack class with applicability verdict, exploit sketch, and remediation. Trigger phrases: advanced attacks, state desync, cache poisoning, replay attack, timing attack, SSRF, SSTI, XXE, insecure deserialization, request smuggling, HTTP desync, IDOR, broken access control, WSTG deep pass."
---

# Advanced Attack Patterns

Two families of attack classes that a baseline OWASP Top 10 review routinely under-tests. The **architectural** family (Steps 1-4) depends on system properties - distributed state, HTTP caching, protocol guarantees, observable timing - that input-validation scanners never inspect. The **injection and access-control** family (Step 5) is the attacker-perspective web-application surface - SSRF, SSTI, XXE, insecure deserialization, HTTP request smuggling, and IDOR - where a scanner flags the easy cases but a human auditor probes the bypass conditions. Each class is gated on an applicability check: if the precondition is absent, skip the class and document why. The goal is a high-signal findings table, not a scripted walkthrough.

This skill is offensive knowledge in service of defense: the same understanding that lets you reach an internal endpoint via SSRF or smuggle a request past a front-end is what lets you write the control that blocks it. Run it only inside an authorized engagement with documented scope, keep payloads benign and pointed at reserved placeholder destinations such as `attacker.example`, and treat the remediation as the deliverable.

## When to Use This Skill

Use this skill when:

- Running `/run-penetration-test --depth=deep` (this skill is half of the Business Logic & Advanced Attacks hunter)
- Reviewing distributed systems with eventual consistency, event sourcing, or multi-service state
- Auditing HTTP caching architectures (CDNs, reverse proxies, application-layer caches)
- Assessing authentication or high-value endpoints where replay semantics matter
- Investigating user-enumeration or timing-leak reports
- Red-teaming a web application's injection and access-control surface (SSRF, SSTI, XXE, deserialization, request smuggling, IDOR) under authorization, or hardening `/review security` against those vectors
- Auditing any endpoint that fetches a user-supplied URL, renders a template from user input, parses XML, deserializes a request body, sits behind a front-end/back-end proxy pair, or exposes object identifiers in its API

Do NOT use this skill for:
- Generic input-validation bugs with no advanced angle (use `security-review` or baseline `/run-penetration-test`).
- Business-logic rule violations - pricing/refund abuse, anti-fraud defeat, workflow-step bypass (use `business-logic-abuse`; it partners with this skill but covers a different axis).
- Any engagement without documented authorization, scope, and rules of engagement - stop and obtain them first.

**Trigger phrases**: "state desync", "state desynchronization", "cache poisoning", "cache deception", "replay attack", "nonce validation", "idempotency replay", "timing attack", "user enumeration", "token binding", "side channel", "Vary header", "CDN cache", "SSRF", "server-side request forgery", "cloud metadata", "SSTI", "template injection", "XXE", "XML external entity", "insecure deserialization", "gadget chain", "request smuggling", "HTTP desync", "CL.TE", "TE.CL", "IDOR", "broken object level authorization", "WSTG deep".

## What This Skill Does

Provides a two-family advanced-attack audit procedure.

**Architectural family (Steps 1-4):**

- **State Desynchronization**: Client/server divergence, cache-vs-DB divergence, step-skip via direct endpoints.
- **Cache Poisoning**: Unkeyed inputs, missing Vary entries, header-injection into cache keys, cache deception via path confusion.
- **Replay Attacks**: Missing nonces, absent timestamp windows, absent token binding, idempotency replay outside the intended window.
- **Timing Attack Surfaces**: Enumeration via response-time delta, token-lookup timing, crypto branch timing beyond the classic `==` password comparison.

**Injection and access-control family (Step 5):**

- **SSRF**: Coercing the server to make attacker-chosen requests - internal services, cloud metadata, port scanning, and the filter bypasses (DNS rebinding, redirects, alternate IP encodings) that defeat naive allow/deny lists.
- **SSTI**: Reaching a template engine with user input, escalating from expression evaluation to object traversal and command execution.
- **XXE**: Abusing an XML parser's external-entity resolution for file read, blind out-of-band exfiltration, and denial of service.
- **Insecure Deserialization**: Turning an untrusted serialized payload into code execution via language-specific gadget chains (pickle, `readObject`, `unserialize`, `BinaryFormatter`).
- **HTTP Request Smuggling**: Front-end/back-end length-parsing disagreement (CL.TE / TE.CL / TE.TE) to poison the connection and hijack adjacent requests.
- **IDOR**: Object identifiers accepted without an ownership check, enabling horizontal and vertical access to other tenants' data.

Each section starts with an **applicability check**. If the precondition does not hold, the class is skipped with a one-line justification in the output. This keeps the audit high-signal and avoids false-positive noise on surfaces the class cannot reach. Deep per-vector payloads and engine-specific probes for the Step 5 family live in [`references/web-appsec-methodology.md`](references/web-appsec-methodology.md), kept out of this body so it stays within the size norm.

## Instructions

### Step 1: State Desynchronization

**Applicability check**: Does the system have any of the following?
- Distributed components (multiple services, microservices, or separate read/write stores)
- Eventual-consistency stores (DynamoDB, Cassandra, eventually-consistent Redis replication, cross-region databases)
- Multi-step workflows where client and server each track state
- Caching layers that hold state that can diverge from the source of truth

If all answers are no, skip to Step 2 with justification "No distributed-state surface."

**Attack patterns**:

- **Client/server state divergence**: The client shows one state (e.g., "cart has 3 items") while the server records another. Attack path: the client re-submits state-carrying requests that the server trusts without corroborating against the server-side authoritative state. Classic example: client hides the "already applied discount" flag, re-applies the discount, and the server does not check.
- **Cache vs DB divergence**: A cached view lags the database. Attack path: an attacker reads from the cache a permission that has just been revoked, or writes through a stale cache that later overwrites a newer DB value. Includes the "thundering herd" pattern where cache eviction produces a window of DB-hitting requests that see inconsistent state.
- **Step-skip via direct endpoint**: The UI walks the user through A -> B -> C but each step is its own endpoint. A direct POST to C from a state where only A has been completed succeeds if the server does not re-verify the state-machine position. (This pattern also lives in the `business-logic-abuse` skill's workflow-bypass section - cross-reference both when auditing a multi-step flow.)

**Indicators in code**:
- State carried in the request payload that the server trusts without re-reading from persistence.
- Cache-first reads with long TTLs on authorization-sensitive data (permissions, roles, feature flags).
- Write-through caches without invalidation on related entities (user role change invalidates only `/users/:id`, not `/teams/:team/members`).
- Conditional UPDATE based on an in-memory read rather than a DB read (`UPDATE ... WHERE version = $stale_version`).

**Remediation**:
- Establish server-authoritative state for all authorization and financial decisions. Do not trust client-carried state beyond display.
- Use strong-consistency reads on the paths that make authorization decisions; weak consistency is acceptable only for display.
- Keep transactional boundaries tight: the read, the check, and the write for a single decision should be in one transaction.
- Cache invalidation must be driven by events, not TTL, for authorization-sensitive data.

### Step 2: Cache Poisoning

**Applicability check**: Does the system have any HTTP caching layer? This includes:
- CDNs (Cloudflare, Fastly, CloudFront, Akamai)
- Reverse proxies (nginx, HAProxy, Varnish)
- Application-layer caches that serve cached HTTP responses

If no HTTP caching layer exists, skip to Step 3 with justification "No HTTP cache surface."

**Attack patterns**:

- **Unkeyed inputs in the cache key**: A request header (e.g., `X-Forwarded-Host`, `X-Original-URL`) influences the response body but is NOT part of the cache key. Attacker sends a request that causes the origin to generate a malicious response, which the cache stores and serves to later victims who do not send the header.
- **Incorrect `Vary` headers**: The response varies by a header (e.g., `Accept-Language`, `Authorization`) but `Vary` does not list it. Cache serves one user's personalized response to another.
- **Cache-injection via header manipulation**: The origin reflects a header into the response body without encoding. If the cache keys on the URL only, a malicious header value ends up in responses to victims. Classic vector: `X-Host` reflected into absolute URLs or link tags.
- **Cache deception**: The attacker requests a URL that looks static (`/profile.css`) but the backend serves dynamic personalized content because the routing does not enforce extension-vs-route separation. The CDN caches the personalized response. Famously applied against Paypal.
- **Path normalization differences**: The cache and the origin normalize paths differently (e.g., `/foo/./bar` vs `/foo/bar`). An attacker crafts a path that the cache treats as distinct from the origin's interpretation, causing the wrong response to be stored under the attacker-controlled key.

**Indicators in code and config**:
- Responses that read request headers and include header-derived content without the header appearing in `Vary`.
- CDN / reverse-proxy configs that cache responses without an explicit allow-list of keyed headers.
- Application routes that serve dynamic content from paths with static-looking extensions.
- Absent or too-permissive `Cache-Control: private` / `no-store` on personalized endpoints.
- Frontends that expect a CDN-set header (`X-Original-URL`) but do not strip the client-sent version.

**Remediation**:
- Enumerate every input that influences the response body. Every one must be in the cache key or explicitly marked non-cacheable.
- `Vary` header must include every request header that changes the response. For authenticated responses: `Vary: Cookie, Authorization` at minimum, or `Cache-Control: private, no-store`.
- Strip client-sent headers that the origin interprets as trusted (`X-Forwarded-For`, `X-Original-URL`, `X-Rewrite-URL`) at the CDN/proxy boundary.
- Enforce route-to-extension separation: dynamic routes reject `/profile.css`-style paths.
- Normalize paths identically at the cache and origin (or disable caching for paths that could be interpreted differently).

### Step 3: Replay Attacks

**Applicability check**: Does the system accept requests that carry authentication or state-changing semantics? If the only endpoints are anonymous read-only, skip to Step 4 with justification "No state-changing request surface."

**Attack patterns**:

- **Missing nonce**: A signed request (e.g., OAuth, OIDC, webhook, SAML) does not carry a server-enforced one-time value, so capturing and replaying the request succeeds indefinitely.
- **Missing idempotency key (within window)**: Distinct from the business-logic double-spend: here the attacker replays a captured request to produce a second effect. Without an idempotency key, the server cannot tell the replay from a legitimate retry.
- **No timestamp window validation**: A signed request includes a timestamp but the server does not check `|now - timestamp| < skew`, or checks with an implausibly wide skew (hours or days). Attacker replays the request weeks later.
- **Token binding absent**: An access token is bearer-only (not bound to the client's TLS session, device, or channel). A leaked token from any transport can be replayed from anywhere.
- **Response replay**: Less common but worth checking - the server's response is signed/attested but the client does not bind the response to the original request, allowing cross-request confusion.

**Indicators in code**:
- Signature validation present but no nonce check.
- Timestamp fields in signed payloads that are logged but never validated.
- Bearer tokens with long expiry (days or weeks) and no DPoP / mTLS / per-request binding.
- Webhook handlers that verify signatures but do not dedup on `(event_id, event_version)`.
- Auth servers that accept any valid signature regardless of which endpoint the token was issued for (token audience not checked).

**Remediation**:
- Require a server-enforced nonce on every signed request. Store nonces with a TTL long enough to cover the signature validity window.
- Validate `timestamp` against a small skew (e.g., +/- 5 minutes). Reject outside the window.
- For high-value sessions, use token binding (DPoP, mTLS client certs, or per-request signatures over a server-issued challenge). Bearer-only tokens are a last resort.
- Webhooks: dedup at the boundary on `(event_id, event_version)`. Reject replays.
- Audience-check every token: the token's `aud` claim must match the endpoint's expected audience.

### Step 4: Timing Attack Surfaces

**Applicability check**: Does the system have any branch whose duration depends on a secret or a user-enumeration-sensitive input? If the only comparisons against secrets are already constant-time (bcrypt/scrypt/argon2 password comparisons using verify functions) and there are no user-existence-revealing code paths, skip with justification "No observable timing leak surface."

**Attack patterns beyond classic password `==`**:

- **User enumeration via login-response timing**: The login endpoint takes measurably longer when the username exists (because the password hash is computed) than when it does not. Attacker enumerates valid usernames by timing.
- **User enumeration via password-reset timing**: The password-reset endpoint takes longer when the email exists (DB write + email send) than when it does not. Same attack, different endpoint.
- **Token-lookup timing**: Session or API tokens are looked up in a data structure that short-circuits on the first mismatched byte. Attacker measures timing to reconstruct the token byte by byte.
- **Cryptographic side channels**: RSA decryption, ECDSA signing, or AES operations implemented without constant-time primitives leak the secret through observable timing variance. Applies mostly to custom crypto code; less common with vetted libraries but still present when libraries are misused (e.g., manual CBC-HMAC instead of AEAD).
- **Directory-traversal timing**: An endpoint that reads filesystem content takes longer when a path exists than when it does not; attacker enumerates filesystem via timing.
- **Regex-engine timing**: A regex with catastrophic backtracking gives the attacker observable timing differences for inputs that trigger backtracking; usable for both DoS and enumeration.

**Indicators in code**:
- `if user == known_username: bcrypt.check(password)` where the bcrypt call runs conditionally.
- `if user_exists(email): send_reset_email(...)` with an early return on absence.
- Token comparison using `==` rather than a constant-time comparator (`hmac.compare_digest` in Python, `crypto.timingSafeEqual` in Node).
- Any regex applied to user input that includes unbounded backtracking (`(a+)+$` pattern family).
- Paths that call `os.path.exists` or `os.stat` on user-controlled paths and branch on the result.

**Remediation**:
- For user enumeration: always perform the expensive work regardless of user existence. Run a dummy bcrypt check with a constant hash for missing users. Reply with a uniform response body and uniform latency.
- For token lookups: use `hmac.compare_digest` (Python), `crypto.timingSafeEqual` (Node), or `subtle.ConstantTimeCompare` (Go). Never compare secrets with `==`.
- For password-reset enumeration: reply with a uniform success message regardless of email existence; perform a no-op delay if absent; send the email asynchronously so the sync response time does not leak existence.
- For custom crypto: use vetted libraries (`libsodium`, `cryptography`, `tink`) exclusively; do not implement RSA or AES primitives in application code.
- For regex: bound backtracking with atomic groups, possessive quantifiers, or a bounded-backtracking engine (Rust's `regex`, Go's `regexp`, `re2`).

### Step 5: Injection and Access-Control Attack Surfaces

The web-application family. Where Steps 1-4 hinge on architecture, these hinge on a sink that trusts attacker-influenced input. For each vector below: run the applicability check, take the attacker's approach to confirm reachability, then convert the confirmed reach into the defensive control. Full engine-specific probes, filter-bypass catalogs, and language-specific gadget notes are in [`references/web-appsec-methodology.md`](references/web-appsec-methodology.md) - keep payloads fenced and pointed at reserved placeholders (`attacker.example`, internal RFC-1918 ranges) so the engagement stays benign.

#### 5a. Server-Side Request Forgery (SSRF)

**Applicability check**: Does any endpoint fetch a URL, hostname, or file path that the user can influence (webhooks, link previews, PDF/image renderers, import-from-URL, document converters, SSO metadata fetch, server-side `fetch`/`curl`)? If no server-initiated request depends on user input, skip with "No server-side fetch surface."

**Attacker approach**: Point the fetch at what the server can reach but the attacker cannot - internal services, the cloud metadata endpoint, and localhost admin ports. The high-value target is cloud instance metadata for credential theft.

```text
http://169.254.169.254/latest/meta-data/iam/security-credentials/   # cloud metadata (IMDSv1)
http://localhost:6379/   gopher://127.0.0.1:6379/_<redis-command>   # internal service / protocol smuggling
```

When a naive allow/deny list is present, the finding is the *bypass*: DNS rebinding, a `30x` redirect from an allowed host to an internal one, alternate IP encodings (decimal/octal/IPv6-mapped), or `@`-confusion in the authority. See the references file for the bypass catalog.

**Indicators in code**: user-supplied URL passed to an HTTP client with no host allowlist; allowlist checked against the *pre-redirect* host only; SSRF "protection" that blocks `localhost` literally but not `127.0.0.1`, `0.0.0.0`, or a rebinding domain.

**Remediation**: allowlist destination hosts and resolve-then-pin the IP (re-validate after every redirect); block link-local/loopback/RFC-1918 ranges at the egress layer; require IMDSv2 (token-bound) on cloud hosts; disable unused URL schemes (`gopher://`, `file://`, `dict://`).

#### 5b. Server-Side Template Injection (SSTI)

**Applicability check**: Is user input ever concatenated into a server-side template (email/report generators, themable pages, "custom message" fields rendered by Jinja2, Twig, Freemarker, Velocity, ERB, Handlebars)? If templates are always rendered from static files with data passed as bound context, skip with "No user-controlled template source."

**Attacker approach**: Send an arithmetic probe and observe whether it is evaluated rather than echoed.

```text
${7*7}   {{7*7}}   #{7*7}   <%= 7*7 %>     # 49 in the response confirms evaluation
```

Confirmed evaluation escalates to object-graph traversal and, on most engines, command execution. Treat reaching evaluation as the finding; demonstrate escalation only as far as the rules of engagement allow, using a benign marker (e.g. printing a fixed string) rather than a live system command.

**Indicators in code**: `render_template_string(user_input)`, f-string/`+` concatenation into a template, a CMS "custom template" feature without a sandbox.

**Remediation**: never compile templates from user input - pass user data as bound context to a static template; use a logic-less engine (Mustache) or a sandboxed environment where available; treat SSTI as RCE-class severity.

#### 5c. XML External Entity (XXE)

**Applicability check**: Does the app parse XML from any untrusted source (SOAP, SAML, SVG upload, DOCX/XLSX, RSS, XML APIs)? If no XML is parsed from untrusted input, skip with "No XML parse surface."

**Attacker approach**: Define an external entity and observe whether the parser resolves it - file disclosure inline, or blind/out-of-band exfiltration via an external DTD fetched from `attacker.example` when the response body does not reflect the entity. A recursive-entity payload tests for denial of service.

**Indicators in code**: an XML parser constructed without disabling DTDs/external entities (`libxml` with `noent`, Java `DocumentBuilderFactory` defaults on old runtimes, .NET `XmlResolver` set).

**Remediation**: disable DOCTYPE/DTD processing and external-entity resolution on every parser; prefer a parser that is secure by default; for SVG/Office uploads, parse with entity resolution off and validate against a schema.

#### 5d. Insecure Deserialization

**Applicability check**: Does the app deserialize untrusted bytes into objects (Python `pickle`, Java native `readObject`, PHP `unserialize`, .NET `BinaryFormatter`, Ruby `Marshal`, YAML with implicit object tags)? JSON-into-DTO with explicit field binding does NOT qualify. If only safe formats are deserialized, skip with "No native-object deserialization of untrusted input."

**Attacker approach**: The exploit is a *gadget chain* - existing classes whose deserialization side effects compose into code execution. Confirm the vulnerable sink and the presence of a known gadget library on the classpath rather than shipping a weaponized chain; the references file describes the per-language sinks conceptually.

**Indicators in code**: `pickle.loads`, `yaml.load` without `SafeLoader`, `ObjectInputStream.readObject` on request data, `BinaryFormatter.Deserialize`, `Marshal.load` on user input.

**Remediation**: do not deserialize native objects from untrusted input - use a data-only format (JSON/Protobuf) with explicit schema binding; if unavoidable, enforce a strict type allowlist and run the parser with least privilege.

#### 5e. HTTP Request Smuggling

**Applicability check**: Is there a front-end/back-end pair (CDN, reverse proxy, load balancer in front of an app server) that may parse request boundaries differently? If a single server terminates the connection with no intermediary, skip with "No proxy chain to desynchronize."

**Attacker approach**: Send a request where `Content-Length` and `Transfer-Encoding` disagree (CL.TE, TE.CL) or `Transfer-Encoding` is obfuscated so one hop ignores it (TE.TE). The desync leaves a prefix in the connection buffer that gets prepended to the next user's request - enabling request hijack, cache poisoning, and control bypass. Confirm with timing-based detection before any exploit attempt.

**Indicators in config**: a proxy and an origin running different HTTP stacks; HTTP/1.1 keep-alive to the back-end; ambiguous header handling not normalized at the edge.

**Remediation**: normalize/reject ambiguous requests at the front-end (reject messages with both `CL` and `TE`); use HTTP/2 end-to-end where possible; disable back-end connection reuse for upstream pools that face untrusted input.

#### 5f. Insecure Direct Object Reference (IDOR) / Broken Object-Level Authorization

**Applicability check**: Do any endpoints accept an object identifier (numeric ID, UUID, filename, account number) and return or mutate that object? If every data access is implicitly scoped to the authenticated principal, skip with "No client-supplied object reference."

**Attacker approach**: Authenticate as a low-privilege user, then substitute another principal's identifier and observe whether the object is returned or mutated. Probe horizontal access (another user, same role) and vertical access (an admin-only object). Mass-assignment is the write-side sibling: submit fields the UI never exposes (`role`, `is_admin`, `owner_id`).

**Indicators in code**: a handler that loads `Object.get(id)` from the request without a `WHERE owner = current_user` predicate; authorization enforced only by hiding the link in the UI; sequential or guessable identifiers.

**Remediation**: enforce object-level authorization at the data layer on every access - scope every query to the authenticated principal, not just the route guard; bind writes to an explicit field allowlist; prefer unguessable identifiers as defense-in-depth (not as the control).

### Step 6: Output Format

Produce findings as a table. Include applicability decisions for classes that were skipped so the operator sees the complete audit shape:

| Attack Class | Applicability | Finding Severity | Code Reference | Exploit Sketch | Remediation |
|--------------|---------------|------------------|----------------|----------------|-------------|
| State desynchronization | YES (multi-service) | HIGH | `src/cart/discount.py:42-58` | Client re-applies discount by re-sending cart state with discount flag cleared | Re-read discount state from DB before applying |
| Cache poisoning | YES (Cloudflare CDN) | CRITICAL | `nginx.conf + src/views/home.py:88` | `X-Forwarded-Host` reflected into absolute URLs; not in cache key | Strip `X-Forwarded-Host` at CDN, add to cache key, switch to relative URLs |
| Replay attacks | NO | - | - | - | No signed requests outside webhooks; webhooks already dedup on event_id |
| Timing attacks | YES (login endpoint) | MEDIUM | `src/auth/login.py:31-49` | Timing delta ~120ms reveals valid usernames | Run dummy bcrypt for missing users |
| SSRF | YES (link-preview fetch) | CRITICAL | `src/preview/fetch.py:22` | User URL fetched with no allowlist; reaches the cloud metadata endpoint for IAM role credentials | Allowlist + resolve-and-pin host, block link-local at egress, require IMDSv2 |
| IDOR | YES (invoice endpoint) | HIGH | `src/billing/invoice.py:60` | `GET /invoices/{id}` loads by id with no owner check; another tenant's invoice returned | Scope the query to `current_user`, enforce object-level authz at the data layer |

Severity guidance:
- CRITICAL: attack is exploitable in default config, gives code execution, session hijack, or bulk data exposure.
- HIGH: attack is exploitable but requires a specific (common) precondition, gives account takeover or privilege escalation.
- MEDIUM: attack gives information disclosure, enumeration, or partial secret exposure.
- LOW: attack is theoretical or requires co-located attacker; defense-in-depth gap.

## Best Practices

- **Apply the applicability check first.** A five-line "not applicable" justification is better than a three-page false-positive write-up.
- **Trust the libraries, verify the usage.** Constant-time comparators exist in every mainstream language. Find the place `==` is used on a secret.
- **Every `Vary` header audit needs a test.** Cache bugs are invisible until someone else requests the same URL and gets the wrong response.
- **Replay-attack defenses stack.** Nonce + timestamp window + token binding is strictly stronger than any one defense.
- **User enumeration is the most common timing leak.** Always audit `/login`, `/register`, `/forgot-password`, and `/resend-verification` for timing differences.

## Common Patterns

### Pattern 1: Uniform-timing login

```python
# Constant-time login: run bcrypt for both existing and missing users
DUMMY_HASH = "$2b$12$" + "X" * 53  # valid bcrypt hash structure, matches no password

def login(email: str, password: str) -> Optional[User]:
    user = db.query(User).filter_by(email=email).one_or_none()
    stored_hash = user.password_hash if user else DUMMY_HASH
    # Always runs bcrypt; no branch on user existence
    if bcrypt.checkpw(password.encode(), stored_hash.encode()) and user is not None:
        return user
    return None  # uniform response path for both "no user" and "wrong password"
```

### Pattern 2: Nonce-enforced signed request

```python
def verify_signed_request(req, signature, timestamp, nonce) -> bool:
    # Window check
    if abs(time.time() - timestamp) > 300:  # 5 minutes
        return False
    # Nonce check (Redis with TTL covering the window + grace period)
    if not redis.set(f"nonce:{nonce}", "1", nx=True, ex=600):
        return False  # already used
    # Signature verification (timing-safe)
    expected = hmac.new(SECRET, f"{timestamp}:{nonce}:{req.body}".encode(), "sha256").hexdigest()
    return hmac.compare_digest(signature, expected)
```

### Pattern 3: Cache-safe personalized response

```python
# Correct headers for a personalized authenticated response
response.headers["Cache-Control"] = "private, no-store, max-age=0"
response.headers["Vary"] = "Cookie, Authorization"
# Or for a response that may be cached per-user at a shared CDN:
response.headers["Cache-Control"] = "private, max-age=60"
response.headers["Vary"] = "Cookie"  # Cookie includes the session
```

## Verification

- [ ] Written authorization, scope, and rules of engagement are documented before any probe was run; targets are in scope and the data is synthetic or marked test data
- [ ] Every payload used during the assessment was benign and pointed at a reserved placeholder (`attacker.example`) or an in-scope internal host - no real data was moved off the target
- [ ] For each cache-poisoning finding, attempt the exploit from a second client to confirm cross-user impact
- [ ] For each timing finding, measure the timing delta from an unprivileged network position to confirm observability
- [ ] For each replay finding, capture and re-send the request; confirm rejection after the fix
- [ ] For each state-desync finding, write an integration test that triggers the divergence and asserts the post-fix invariant
- [ ] Confirm `Vary` headers by requesting the same URL with and without the relevant header from a CDN-adjacent tool (e.g., `curl -I` against the CDN, then the origin)
- [ ] For each SSRF finding, confirm the server reached an attacker-chosen internal/metadata destination, then re-test after the allowlist + egress fix to confirm the reach is closed
- [ ] For each SSTI/deserialization finding, demonstrate only as far as the rules of engagement allow (a benign marker, not a live system command) and confirm the sink rejects untrusted input after the fix
- [ ] For each XXE finding, confirm external-entity resolution is disabled on the parser after the fix
- [ ] For each request-smuggling finding, confirm the front-end now rejects ambiguous `CL`/`TE` requests
- [ ] For each IDOR finding, re-test object access as a different principal and confirm the data-layer authorization check rejects it
- [ ] Each finding maps to a concrete defensive control (allowlist, parser config, authz predicate) handed to `security-review` / `security-patch-advisor`

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The baseline OWASP review already covered this, so the deep pass is redundant" | Cache poisoning and state desync depend on architecture, not input shape; a baseline review that grep-checks for SQL-i and XSS never inspects the `Vary` header or the read/write store split, so the `X-Forwarded-Host`-into-cache-key bug ships unfound. |
| "We use a vetted crypto library, so there is no timing-attack surface" | The most common timing leak is user enumeration on `/login` and `/forgot-password`, where the secret-dependent branch is your own `if user_exists` early return, not anything inside the crypto library. |
| "Replay does not matter because our tokens expire" | A bearer token with a multi-day expiry can be replayed from any network for its whole lifetime; expiry is not a nonce, and without timestamp-window plus nonce a captured signed webhook replays indefinitely. |
| "This architecture is too simple to have distributed state" | A single read-replica or a Redis cache in front of the DB is enough to serve a just-revoked permission from a stale cache, which is exactly the cache-vs-DB divergence in Step 1. |
| "The SSRF fetch only hits an internal allowlist, so it is safe" | An allowlist that checks the pre-redirect host is bypassed by a `30x` to an internal target, and one that blocks `localhost` literally still resolves `127.0.0.1`, a decimal-encoded IP, or a rebinding domain; the durable control is resolve-and-pin plus egress filtering, not a hostname string match. |
| "Object IDs are UUIDs, so IDOR is not exploitable" | Unguessable identifiers are defense-in-depth, not authorization; UUIDs leak through referrers, logs, shared links, and prior responses, and once an attacker has one, an endpoint with no `WHERE owner = current_user` predicate hands over the object regardless of how random the id was. |
| "We pass user data into the template, but it is just for a custom message" | If user input reaches a server-side template compiler at all, `{{7*7}}` returning `49` proves expression evaluation, which on most engines escalates to object traversal and command execution; the fix is to pass data as bound context, never to compile a template from user input. |

## Related Skills

- [[business-logic-abuse]] -- companion skill; state-desynchronization step-skip and workflow-bypass overlap heavily, and its attacker playbooks pair with the Step 5 injection family
- [[security-patch-advisor]] -- patch generation for the SSRF / SSTI / XXE / deserialization fixes referenced in remediation
- [[security-review]] -- baseline OWASP Top 10 pass that owns the target denominator, altitude ledger, and proven-dirty sink sweep this deep method must satisfy
- [[authentication-patterns]] -- token binding, session management, and the JWT/OAuth attack methodology referenced in replay attacks
- [[jwt-header-and-key-confusion-attacks]] -- header-level JWT forgeries (alg=none, key confusion) that sit beside this skill's replay and token-binding steps
- [[api-object-level-authorization-flaws]] -- BOLA/IDOR object-level access, which this skill's authorization-bypass family must not re-teach
- [[pentest-reporting]] -- writes up the findings this skill produces (CVSS, evidence, executive summary, retest)
- [[exploitability-analyzer]] -- scores and prioritizes the confirmed findings for the report
- [[fintech-engineer]] -- financial replay and double-spend coverage in payment-specific contexts

---

**Version**: 1.1.0
**Last Updated**: June 2026

### Iterative Refinement Strategy

This skill is optimized for an iterative approach:
1. **Execute**: Apply each class's applicability check, audit where applicable, produce the findings table.
2. **Review**: For each "not applicable" decision, verify the precondition really is absent. For each finding, confirm severity against real exploit effort.
3. **Refine**: Downgrade theoretical findings; escalate any that carry a pre-auth exploit path.
4. **Loop**: Continue until every applicable class has a high-signal verdict (finding with exploit sketch, or documented clean audit).
