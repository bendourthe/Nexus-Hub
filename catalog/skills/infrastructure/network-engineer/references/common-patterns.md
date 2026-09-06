## Common Patterns

### Pattern 1: Hub-and-Spoke with Transit Gateway

```
On-Premises ──VPN──► Transit GW ──► Production VPC
                          │──► Staging VPC
                          │──► Shared Services VPC (DNS, logging, CI/CD)
```

### Pattern 2: Global Application with Latency Routing

```
Route 53 (Latency) ──► US: CloudFront ──► ALB us-east-1
                   ──► EU: CloudFront ──► ALB eu-west-1
                   ──► AP: CloudFront ──► ALB ap-southeast-1
```

### Pattern 3: Zero-Trust Service Connectivity

```
Client ──► Verified Access (identity check) ──► Private ALB ──► App (mTLS mesh)
```
