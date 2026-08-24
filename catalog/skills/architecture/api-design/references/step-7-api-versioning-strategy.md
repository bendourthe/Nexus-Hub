### Step 7: API Versioning Strategy

**Comparison of Versioning Approaches**:

| Strategy | Example | Pros | Cons |
|----------|---------|------|------|
| URL path | `/v1/orders` | Simple, explicit, cacheable | Breaks client URLs on version bump |
| Custom header | `X-API-Version: 2` | URLs stay stable | Easy to forget, not cacheable by URL |
| Content negotiation | `Accept: application/vnd.example.v2+json` | Semantically correct | Complex, poor tooling support |
| Query parameter | `/orders?version=2` | Simple to test | Pollutes query string, caching issues |

**Recommended: URL Path Versioning with Sunset Headers**:

```
# Current version
GET /v2/orders HTTP/1.1

# Response for deprecated version
HTTP/1.1 200 OK
Sunset: Sat, 01 Jun 2026 00:00:00 GMT
Deprecation: true
Link: <https://api.example.com/v2/orders>; rel="successor-version"
```

**Rate Limiting Headers**:

```
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 742
X-RateLimit-Reset: 1709510400

# When rate limited:
HTTP/1.1 429 Too Many Requests
Retry-After: 30
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1709510400
```
