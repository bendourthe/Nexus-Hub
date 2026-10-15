### Step 1: Design VPC and Subnet Architecture

**CIDR Planning Principles**:

Plan your IP address space before creating any resources. Use RFC 1918 private ranges and leave room for growth. A common mistake is allocating overlapping CIDRs across VPCs, which prevents peering and transit gateway connectivity later.

| Range | Total IPs | Typical Use |
|-------|-----------|-------------|
| `10.0.0.0/8` | 16.7M | Enterprise backbone (subdivide into /16 per VPC) |
| `172.16.0.0/12` | 1M | Secondary environments, staging |
| `192.168.0.0/16` | 65K | Small VPCs, development |

**Three-Tier Subnet Layout (Multi-AZ)**:

```
                    ┌──────────────────────────────────────────────────────────┐
                    │                  VPC: 10.0.0.0/16                        │
                    │                                                          │
                    │   AZ-a              AZ-b              AZ-c              │
                    │  ┌──────────┐     ┌──────────┐     ┌──────────┐        │
                    │  │ Public   │     │ Public   │     │ Public   │        │
                    │  │10.0.1/24│     │10.0.2/24│     │10.0.3/24│        │
                    │  │ NAT GW  │     │ NAT GW  │     │ NAT GW  │        │
                    │  │ ALB     │     │ ALB     │     │ ALB     │        │
                    │  └────┬─────┘     └────┬─────┘     └────┬─────┘        │
                    │       │                │                │               │
                    │  ┌────▼─────┐     ┌────▼─────┐     ┌────▼─────┐        │
                    │  │ Private  │     │ Private  │     │ Private  │        │
                    │  │10.0.11/24│    │10.0.12/24│    │10.0.13/24│       │
                    │  │ App Tier │     │ App Tier │     │ App Tier │        │
                    │  │ ECS/EKS │     │ ECS/EKS │     │ ECS/EKS │        │
                    │  └────┬─────┘     └────┬─────┘     └────┬─────┘        │
                    │       │                │                │               │
                    │  ┌────▼─────┐     ┌────▼─────┐     ┌────▼─────┐        │
                    │  │ Isolated │     │ Isolated │     │ Isolated │        │
                    │  │10.0.21/24│    │10.0.22/24│    │10.0.23/24│       │
                    │  │ RDS     │     │ RDS     │     │ RDS     │        │
                    │  │ No IGW  │     │ No IGW  │     │ No IGW  │        │
                    │  └──────────┘     └──────────┘     └──────────┘        │
                    └──────────────────────────────────────────────────────────┘
```

- **Public subnets**: Internet Gateway attached, NAT Gateways, ALB nodes, bastion hosts
- **Private subnets**: Application workloads with outbound internet via NAT Gateway
- **Isolated subnets**: Databases, caches with no route to the internet (only VPC endpoints)

**VPC Terraform Configuration**:

```hcl
# VPC with DNS support and IPv6
resource "aws_vpc" "main" {
  cidr_block                       = "10.0.0.0/16"
  enable_dns_hostnames             = true
  enable_dns_support               = true
  assign_generated_ipv6_cidr_block = true

  tags = { Name = "production-vpc" }
}

# Public subnets across three AZs
resource "aws_subnet" "public" {
  count                           = 3
  vpc_id                          = aws_vpc.main.id
  cidr_block                      = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 1)
  ipv6_cidr_block                 = cidrsubnet(aws_vpc.main.ipv6_cidr_block, 8, count.index + 1)
  availability_zone               = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch         = true
  assign_ipv6_address_on_creation = true

  tags = { Name = "public-${count.index + 1}", Tier = "public" }
}

# Private subnets (application tier)
resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 11)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = { Name = "private-${count.index + 1}", Tier = "private" }
}

# Isolated subnets (database tier, no NAT route)
resource "aws_subnet" "isolated" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 21)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = { Name = "isolated-${count.index + 1}", Tier = "isolated" }
}

# NAT Gateway per AZ for high availability
resource "aws_nat_gateway" "main" {
  count         = 3
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = { Name = "nat-${count.index + 1}" }
}
```

**Transit Gateway for Multi-VPC Connectivity**:

```
                         ┌─────────────────────┐
                         │   Transit Gateway    │
                         │   (Hub)              │
                         └──┬──────┬──────┬────┘
                            │      │      │
               ┌────────────┘      │      └────────────┐
               │                   │                    │
        ┌──────▼──────┐    ┌──────▼──────┐     ┌───────▼─────┐
        │ Production  │    │  Staging    │     │  Shared     │
        │ VPC         │    │  VPC        │     │  Services   │
        │ 10.1.0.0/16 │    │ 10.2.0.0/16│     │  10.0.0.0/16│
        └─────────────┘    └─────────────┘     └─────────────┘
```

Use Transit Gateway instead of VPC peering when you have more than two or three VPCs. Transit Gateway supports transitive routing, centralized route management, and inter-region peering. VPC peering is simpler but creates a full mesh that becomes unmanageable at scale.

**IPv6 Dual-Stack Considerations**:

- Enable `assign_generated_ipv6_cidr_block` on the VPC for automatic /56 allocation
- Add IPv6 CIDR blocks to each subnet (/64 per subnet)
- Use egress-only internet gateways for IPv6 outbound from private subnets (replaces NAT for IPv6)
- Update security groups and NACLs to include IPv6 rules
- Not all AWS services support IPv6; verify compatibility before enabling dual-stack on application subnets
