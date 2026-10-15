### Step 3: Configure Load Balancing

**Load Balancer Selection Guide**:

| Feature | ALB (Layer 7) | NLB (Layer 4) | GLB (Layer 3) |
|---------|---------------|----------------|----------------|
| **Protocol** | HTTP, HTTPS, gRPC, WebSocket | TCP, UDP, TLS | IP (GENEVE encapsulation) |
| **Latency** | ~400ms added | ~100us added | ~100us added |
| **Static IP** | No (use Global Accelerator) | Yes, Elastic IP per AZ | Yes |
| **Use case** | Web apps, APIs, microservices | High throughput, gaming, IoT | Firewalls, IDS/IPS, DPI |
| **TLS termination** | Yes (with ACM certs) | Yes (passthrough or terminate) | No |
| **Target types** | Instance, IP, Lambda | Instance, IP, ALB | Instance, IP |

**ALB with Path-Based Routing and gRPC**:

```hcl
resource "aws_lb" "main" {
  name               = "app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_cross_zone_load_balancing = true
  enable_deletion_protection       = true
  drop_invalid_header_fields       = true

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "alb"
    enabled = true
  }
}

# HTTPS listener with default action
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

# Path-based routing: /api/* to API service
resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern { values = ["/api/*"] }
  }
}

# gRPC target group
resource "aws_lb_target_group" "grpc" {
  name             = "grpc-targets"
  port             = 50051
  protocol         = "HTTP"
  protocol_version = "GRPC"
  vpc_id           = aws_vpc.main.id
  target_type      = "ip"

  health_check {
    enabled             = true
    path                = "/grpc.health.v1.Health/Check"
    protocol            = "HTTP"
    matcher             = "0"  # gRPC status OK
    interval            = 15
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}
```

**Health Check Best Practices**:

- Use a dedicated `/health` endpoint that checks downstream dependencies (database, cache, external APIs)
- Set `healthy_threshold` to 2 and `unhealthy_threshold` to 3 for a balance between speed and stability
- Use `interval` of 10-15 seconds; shorter intervals increase cost and load
- For gRPC services, implement the gRPC Health Checking Protocol and set matcher to "0" (OK status)
- Enable cross-zone load balancing to distribute traffic evenly when AZ capacity is asymmetric

**Weighted Target Groups for Canary Deployments**:

```hcl
resource "aws_lb_listener_rule" "canary" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 50

  action {
    type = "forward"
    forward {
      target_group {
        arn    = aws_lb_target_group.stable.arn
        weight = 90
      }
      target_group {
        arn    = aws_lb_target_group.canary.arn
        weight = 10
      }

      stickiness {
        enabled  = true
        duration = 3600
      }
    }
  }

  condition {
    path_pattern { values = ["/*"] }
  }
}
```
