### Step 2: Architect DNS Solutions

**Route 53 Routing Policies**:

| Policy | Use Case | How It Works |
|--------|----------|--------------|
| **Simple** | Single resource | Returns one or more values at random |
| **Weighted** | A/B testing, blue-green | Distributes traffic by weight percentage |
| **Latency** | Global users | Routes to the lowest-latency region |
| **Failover** | Active-passive DR | Health-checked primary with standby secondary |
| **Geolocation** | Compliance, localization | Routes by user continent/country |
| **Multi-value** | Simple load distribution | Returns up to 8 healthy records |

**Split-Horizon DNS Configuration**:

Split-horizon DNS returns different answers depending on whether the query originates from inside or outside your network. This is critical for hybrid environments where internal services should resolve to private IPs internally and public IPs externally.

```hcl
# Private hosted zone (resolves inside VPC)
resource "aws_route53_zone" "private" {
  name = "app.example.com"

  vpc {
    vpc_id = aws_vpc.main.id
  }
}

resource "aws_route53_record" "api_private" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "api.app.example.com"
  type    = "A"
  ttl     = 60
  records = ["10.0.11.50"]  # Private IP
}

# Public hosted zone (resolves from internet)
resource "aws_route53_zone" "public" {
  name = "app.example.com"
}

resource "aws_route53_record" "api_public" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "api.app.example.com"
  type    = "A"

  alias {
    name                   = aws_lb.api.dns_name
    zone_id                = aws_lb.api.zone_id
    evaluate_target_health = true
  }
}
```

**Failover Routing with Health Checks**:

```hcl
resource "aws_route53_health_check" "primary" {
  fqdn              = "api-primary.example.com"
  port               = 443
  type               = "HTTPS"
  resource_path      = "/health"
  failure_threshold  = 3
  request_interval   = 10

  tags = { Name = "primary-health-check" }
}

resource "aws_route53_record" "api_primary" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "api.example.com"
  type    = "A"

  alias {
    name                   = aws_lb.primary.dns_name
    zone_id                = aws_lb.primary.zone_id
    evaluate_target_health = true
  }

  failover_routing_policy {
    type = "PRIMARY"
  }

  set_identifier  = "primary"
  health_check_id = aws_route53_health_check.primary.id
}

resource "aws_route53_record" "api_secondary" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "api.example.com"
  type    = "A"

  alias {
    name                   = aws_lb.secondary.dns_name
    zone_id                = aws_lb.secondary.zone_id
    evaluate_target_health = true
  }

  failover_routing_policy {
    type = "SECONDARY"
  }

  set_identifier = "secondary"
}
```

**Service Discovery with Cloud Map**:

```hcl
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "internal.local"
  description = "Service discovery namespace"
  vpc         = aws_vpc.main.id
}

resource "aws_service_discovery_service" "api" {
  name = "api"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}
```

ECS and Kubernetes services register automatically with Cloud Map, enabling DNS-based service discovery at `api.internal.local` without external service registries.

**DNSSEC**: Enable DNSSEC signing on Route 53 public hosted zones to protect against DNS spoofing. Create a KMS key with the `SIGN_VERIFY` usage and `ECC_NIST_P256` spec, then enable DNSSEC signing on the zone. Establish a chain of trust by adding a DS record to the parent zone (your domain registrar).
