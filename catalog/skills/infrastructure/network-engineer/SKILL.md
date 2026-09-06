---
name: network-engineer
description: Network engineering expertise for designing and troubleshooting modern network architectures. Use when configuring VPCs, subnets, and routing tables, designing DNS and load balancing strategies, implementing network security with firewalls and NACLs, troubleshooting connectivity issues, or optimizing network performance.
summary_l0: "Design and troubleshoot network architectures with VPCs, DNS, and load balancing"
overview_l1: "This skill provides specialized expertise in network architecture and operations across cloud and hybrid environments, covering VPC design, DNS architecture, load balancing, network security, troubleshooting methodology, service mesh networking, and CDN/edge networking. Use it when configuring VPCs, subnets, and routing tables, designing DNS and load balancing strategies, implementing network security with firewalls and NACLs, troubleshooting connectivity issues, optimizing network performance, or designing service mesh topologies. Key capabilities include VPC and subnet architecture design, DNS resolution strategy, load balancer configuration (ALB, NLB, Envoy), firewall and NACL rule design, connectivity troubleshooting methodology, service mesh networking (Istio, Linkerd), CDN and edge networking, and network performance optimization. The expected output is network architecture diagrams, configuration files, security rules, and troubleshooting runbooks. Trigger phrases: VPC, subnet, routing, DNS, load balancer, firewall, NACL, network security, connectivity, service mesh, CDN, network troubleshooting."
---

# Network Engineer

Specialized expertise in network architecture and operations across cloud and hybrid environments, providing guidance on VPC design, DNS architecture, load balancing, network security, troubleshooting methodology, service mesh networking, and CDN/edge networking.

## When to Use This Skill

Use this skill for:

- Designing VPC layouts with proper CIDR planning and subnet tiers
- Configuring DNS resolution, failover routing, and service discovery
- Selecting and configuring load balancers (ALB, NLB, GLB)
- Implementing network security with security groups, NACLs, WAF, and DDoS protection
- Troubleshooting connectivity issues using TCP/IP layer analysis
- Designing service mesh networking with Envoy, mTLS, and traffic management
- Configuring CDN and edge networking for global content delivery

**Trigger phrases**: "VPC design", "subnet layout", "CIDR planning", "DNS routing", "load balancer", "security group", "NACL", "WAF", "traceroute", "packet capture", "service mesh", "CDN", "CloudFront", "network troubleshooting", "VPN", "Direct Connect", "transit gateway"

## What This Skill Does

Provides production-ready network patterns including:

- **VPC Design**: Multi-AZ subnet tiers, CIDR allocation, peering, transit gateway
- **DNS Architecture**: Route 53 patterns, failover, latency-based routing, DNSSEC
- **Load Balancing**: ALB/NLB/GLB selection, health checks, weighted routing
- **Network Security**: Defense in depth with SGs, NACLs, WAF, Shield, zero-trust
- **Troubleshooting**: Systematic layer-by-layer diagnosis with practical CLI tools
- **Service Mesh**: Envoy, mTLS, traffic splitting, fault injection, observability
- **CDN/Edge**: Cache strategies, origin shield, edge functions, HTTP/3

## Instructions

### Step 1: Design VPC and Subnet Architecture

Full walkthrough: [step-1-design-vpc-and-subnet-architecture.md](references/step-1-design-vpc-and-subnet-architecture.md) (load this step when you reach it).

### Step 2: Architect DNS Solutions

Full walkthrough: [step-2-architect-dns-solutions.md](references/step-2-architect-dns-solutions.md) (load this step when you reach it).

### Step 3: Configure Load Balancing

Full walkthrough: [step-3-configure-load-balancing.md](references/step-3-configure-load-balancing.md) (load this step when you reach it).

### Step 4: Implement Network Security

Full walkthrough: [step-4-implement-network-security.md](references/step-4-implement-network-security.md) (load this step when you reach it).

### Step 5: Apply Troubleshooting Methodology

Full walkthrough: [step-5-apply-troubleshooting-methodology.md](references/step-5-apply-troubleshooting-methodology.md) (load this step when you reach it).

### Step 6: Design Service Mesh Networking

Full walkthrough: [step-6-design-service-mesh-networking.md](references/step-6-design-service-mesh-networking.md) (load this step when you reach it).

### Step 7: Configure CDN and Edge Networking

Full walkthrough: [step-7-configure-cdn-and-edge-networking.md](references/step-7-configure-cdn-and-edge-networking.md) (load this step when you reach it).

## Best Practices

- **Plan CIDR allocation upfront**: Overlapping address spaces prevent peering and transit gateway connectivity. Document all allocations in a central IPAM tool.
- **Use three AZs minimum**: Two AZs is not enough for production. A single AZ failure with two-AZ deployment leaves you at 50% capacity, while three-AZ deployment retains 66%.
- **Automate DNS with IaC**: Manual DNS changes are the leading cause of outages. Manage all records through Terraform or CloudFormation.
- **Layer your defenses**: Never rely on a single security control. Combine WAF, security groups, NACLs, and application-level validation.
- **Enable flow logs everywhere**: They cost very little and are invaluable during incident response. Send them to S3 for long-term retention and CloudWatch for real-time queries.
- **Monitor certificate expiry**: Use ACM for automatic renewal where possible. For non-ACM certificates, set CloudWatch alarms at 30 and 7 days before expiry.
- **Test failover regularly**: DNS failover, AZ failover, and region failover should be tested quarterly. Untested failover is not failover.
- **Use origin shield**: For high-traffic distributions, origin shield reduces origin load by 50-90% by adding a centralized cache tier.
- **Prefer versioned URLs over invalidation**: Content-hash filenames give instant, free cache busting with no propagation delay.
- **Document network topology**: Maintain up-to-date architecture diagrams. Network issues are nearly impossible to diagnose without understanding the topology.

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll use a /16 everywhere, CIDR planning is premature" | Overlapping or oversized CIDR blocks make VPC peering and transit-gateway routing impossible to add later without re-IP-ing the whole environment; a planned non-overlapping allocation up front is the cheap moment to get it right. |
| "Open the security group to 0.0.0.0/0 so it just works" | A wildcard ingress rule exposes the service to the entire internet; least-privilege source ranges and a defense-in-depth NACL layer are what keep an open SG from being the breach vector. |
| "The connection is failing, I'll just restart the load balancer" | Restarting without layer-by-layer diagnosis (DNS, routing, SG/NACL, health check) treats a symptom; the actual failure (a failing health check or a missing route) recurs immediately after the restart. |
| "DNS TTLs do not matter for failover" | A long TTL means clients cache a dead endpoint long after failover; the TTL is the floor on your failover recovery time, and it must be set deliberately for any record on the failover path. |

## Verification

- [ ] VPC CIDR blocks are non-overlapping and sized to a documented allocation plan that allows for peering/transit.
- [ ] Security group and NACL rules use least-privilege source ranges; no unintended 0.0.0.0/0 ingress on private tiers.
- [ ] Load balancer health checks are configured and verified to fail over correctly on an unhealthy target.
- [ ] DNS records on the failover path have a TTL set to meet the documented recovery-time target.
- [ ] Connectivity issues were diagnosed layer by layer (DNS, routing, firewall, health check) before any change was applied.

## Related Skills

- [[cloud-architect]] -- cloud infrastructure design and Well-Architected Framework
- [[terraform-specialist]] -- Infrastructure as Code provisioning
- [[kubernetes-expert]] -- container orchestration and cluster networking
- [[security-review]] -- security assessment and compliance

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: AWS networking best practices, cloud-architect skill patterns


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets are not met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
