### Step 7: Configure CDN and Edge Networking

**CloudFront Distribution Architecture**:

```
Users (Global)
    │
    ▼
┌──────────────────┐
│  Edge Locations  │  ← 400+ PoPs worldwide
│  (Cache + TLS)   │
└────────┬─────────┘
         │ Cache miss
┌────────▼─────────┐
│  Regional Edge   │  ← Mid-tier cache (13 locations)
│  Cache           │
└────────┬─────────┘
         │ Cache miss
┌────────▼─────────┐
│  Origin Shield   │  ← Single cache layer before origin (optional)
│  (1 location)    │
└────────┬─────────┘
         │ Cache miss
┌────────▼─────────┐
│  Origin Server   │  ← ALB, S3, or custom origin
└──────────────────┘
```

**CloudFront Terraform Configuration**:

```hcl
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  http_version        = "http3"
  price_class         = "PriceClass_100"  # US, Canada, Europe only
  aliases             = ["cdn.example.com"]
  default_root_object = "index.html"

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "alb-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
      origin_read_timeout    = 30
    }

    origin_shield {
      enabled              = true
      origin_shield_region = "us-east-1"
    }
  }

  # Static assets: aggressive caching
  ordered_cache_behavior {
    path_pattern     = "/static/*"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "alb-origin"
    compress         = true

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 86400
    default_ttl            = 604800    # 7 days
    max_ttl                = 31536000  # 1 year
  }

  # API: no caching, pass all headers
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "alb-origin"
    compress         = true

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Origin", "Accept"]
      cookies { forward = "all" }
    }

    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
  }

  # Default behavior
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "alb-origin"
    compress         = true

    forwarded_values {
      query_string = true
      cookies { forward = "none" }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.cdn.arn
    minimum_protocol_version = "TLSv1.2_2021"
    ssl_support_method       = "sni-only"
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }
}
```

**Cache Invalidation Strategies**:

| Strategy | When to Use | How |
|----------|------------|-----|
| **Versioned URLs** | Static assets (JS, CSS, images) | Include content hash in filename: `app.a1b2c3.js` |
| **Path invalidation** | Emergency content updates | `aws cloudfront create-invalidation --paths "/page/*"` |
| **TTL tuning** | API responses, dynamic content | Set `Cache-Control: max-age=60, s-maxage=300` |
| **Stale-while-revalidate** | Balance freshness and performance | `Cache-Control: max-age=60, stale-while-revalidate=300` |

Versioned URLs are always preferred over path invalidation. Invalidation requests cost money (first 1,000/month free, then $0.005 each) and take time to propagate. Versioned URLs give instant cache busting with zero cost.

**Edge Functions (CloudFront Functions vs Lambda@Edge)**:

| Feature | CloudFront Functions | Lambda@Edge |
|---------|---------------------|-------------|
| **Runtime** | JavaScript (ES 5.1) | Node.js, Python |
| **Execution time** | < 1ms | Up to 30s (origin events) |
| **Memory** | 2 MB | 128-10240 MB |
| **Network access** | No | Yes |
| **Use cases** | URL rewrites, header manipulation, simple auth | A/B testing, image optimization, SSR |
| **Cost** | $0.10/million | $0.60/million + duration |

```javascript
// CloudFront Function: Add security headers
function handler(event) {
    var response = event.response;
    var headers = response.headers;

    headers['strict-transport-security'] = { value: 'max-age=63072000; includeSubDomains; preload' };
    headers['x-content-type-options']    = { value: 'nosniff' };
    headers['x-frame-options']           = { value: 'DENY' };
    headers['x-xss-protection']          = { value: '1; mode=block' };
    headers['referrer-policy']           = { value: 'strict-origin-when-cross-origin' };

    return response;
}
```

**WebSocket Support**: ALB natively supports WebSocket connections (upgrade from HTTP). CloudFront supports WebSocket via the `wss://` protocol when the origin supports it. Set the origin protocol policy to `https-only` and ensure the cache behavior forwards the `Upgrade`, `Sec-WebSocket-Key`, `Sec-WebSocket-Version`, and `Sec-WebSocket-Protocol` headers.

**HTTP/3 and QUIC**: Enable HTTP/3 on CloudFront distributions with `http_version = "http3"`. QUIC reduces connection establishment latency (0-RTT), handles packet loss better than TCP, and supports connection migration (seamless handoff when a mobile user switches from Wi-Fi to cellular). HTTP/3 is backward-compatible; clients that do not support QUIC fall back to HTTP/2 automatically.
