### Step 4: Implement Network Security

**Defense in Depth Model**:

```
Internet
    │
    ▼
┌──────────────┐
│  AWS Shield  │  ← DDoS protection (L3/L4)
│  (Advanced)  │
└──────┬───────┘
       │
┌──────▼───────┐
│     WAF      │  ← L7 filtering (SQL injection, XSS, rate limiting)
└──────┬───────┘
       │
┌──────▼───────┐
│    NACLs     │  ← Stateless subnet-level rules (L3/L4)
└──────┬───────┘
       │
┌──────▼───────┐
│  Security    │  ← Stateful instance-level rules (L3/L4)
│  Groups      │
└──────┬───────┘
       │
┌──────▼───────┐
│  Application │  ← App-level auth, TLS, input validation
└──────────────┘
```

**Security Groups vs NACLs**:

| Aspect | Security Groups | NACLs |
|--------|----------------|-------|
| **Level** | Instance/ENI | Subnet |
| **State** | Stateful (return traffic auto-allowed) | Stateless (must allow both directions) |
| **Rules** | Allow only | Allow and Deny |
| **Evaluation** | All rules evaluated | Rules evaluated in order by number |
| **Default** | Deny all inbound, allow all outbound | Allow all inbound and outbound |

```hcl
# Security group: application tier
resource "aws_security_group" "app" {
  name_prefix = "app-"
  vpc_id      = aws_vpc.main.id
  description = "Application tier - accepts traffic from ALB only"

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "HTTP from ALB"
  }

  egress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.db.id]
    description     = "PostgreSQL to database tier"
  }

  egress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    prefix_list_ids = [aws_vpc_endpoint.s3.prefix_list_id]
    description     = "HTTPS to S3 via VPC endpoint"
  }
}

# NACL: isolated subnet (database tier)
resource "aws_network_acl" "isolated" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.isolated[*].id

  # Allow inbound PostgreSQL from private subnets only
  ingress {
    rule_no    = 100
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "10.0.11.0/24"
    from_port  = 5432
    to_port    = 5432
  }

  ingress {
    rule_no    = 110
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "10.0.12.0/24"
    from_port  = 5432
    to_port    = 5432
  }

  ingress {
    rule_no    = 120
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "10.0.13.0/24"
    from_port  = 5432
    to_port    = 5432
  }

  # Allow ephemeral return traffic
  ingress {
    rule_no    = 200
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "10.0.0.0/16"
    from_port  = 1024
    to_port    = 65535
  }

  # Deny all other inbound
  ingress {
    rule_no    = 999
    protocol   = "-1"
    action     = "deny"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  # Allow outbound ephemeral ports to private subnets
  egress {
    rule_no    = 100
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "10.0.0.0/16"
    from_port  = 1024
    to_port    = 65535
  }

  egress {
    rule_no    = 999
    protocol   = "-1"
    action     = "deny"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }
}
```

**WAF Rules for Common Attacks**:

```hcl
resource "aws_wafv2_web_acl" "main" {
  name        = "app-waf"
  scope       = "REGIONAL"
  description = "WAF for application ALB"

  default_action { allow {} }

  # AWS Managed Rules: Common Rule Set
  rule {
    name     = "aws-managed-common"
    priority = 1
    override_action { none {} }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "aws-common-rules"
    }
  }

  # Rate limiting
  rule {
    name     = "rate-limit"
    priority = 2
    action { block {} }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "rate-limit"
    }
  }

  visibility_config {
    sampled_requests_enabled   = true
    cloudwatch_metrics_enabled = true
    metric_name                = "app-waf"
  }
}
```

**VPN and Direct Connect**:

- **Site-to-Site VPN**: Encrypted tunnel over the internet. Use for quick connectivity with up to 1.25 Gbps per tunnel. Deploy two tunnels per connection for redundancy. Combine with Transit Gateway for hub-and-spoke topology.
- **Direct Connect**: Dedicated physical connection (1 Gbps or 10 Gbps). Use when you need consistent latency, high throughput, or reduced data transfer costs. Always pair with a VPN backup for failover.
- **Zero-Trust Network Architecture**: Replace perimeter-based security with identity-verified, least-privilege access at every hop. Use AWS Verified Access or Google BeyondCorp for application-level access without VPN. Combine with mTLS between services and short-lived certificates from a private CA.
