### Step 5: Apply Troubleshooting Methodology

**TCP/IP Layer Diagnosis Model**:

When troubleshooting connectivity issues, work from the bottom of the stack upward. Most network problems are at Layer 3 (routing) or Layer 4 (firewall/security group rules).

| Layer | What to Check | Tools |
|-------|--------------|-------|
| **L1 Physical** | Cable, NIC, ENI status | `ethtool`, AWS console (ENI status) |
| **L2 Data Link** | ARP, MAC table, VLAN | `arp -a`, `ip link show` |
| **L3 Network** | IP addressing, routing | `ip route`, `traceroute`, `mtr` |
| **L4 Transport** | Ports, firewalls, SGs | `ss -tlnp`, `telnet`, `nmap`, VPC Flow Logs |
| **L7 Application** | HTTP status, TLS, DNS | `curl -v`, `dig`, `openssl s_client` |

**Essential CLI Commands**:

```bash
# DNS resolution check
dig +short api.example.com
dig @8.8.8.8 api.example.com    # bypass local resolver
dig +trace api.example.com       # full delegation chain

# Path analysis with MTR (combines ping and traceroute)
mtr --report --report-cycles=10 api.example.com

# TCP connectivity test
nc -zv api.example.com 443       # quick port check
curl -v --connect-timeout 5 https://api.example.com/health

# Packet capture for deep analysis
tcpdump -i eth0 -nn host 10.0.11.50 and port 5432 -w capture.pcap
tcpdump -i any -nn 'tcp[tcpflags] & (tcp-syn|tcp-rst) != 0'  # SYN and RST only

# TLS certificate inspection
openssl s_client -connect api.example.com:443 -servername api.example.com </dev/null 2>/dev/null | openssl x509 -noout -dates -subject

# Network socket analysis
ss -tlnp          # listening TCP sockets with process info
ss -s             # socket summary statistics

# MTU path discovery (detect MTU black holes)
ping -M do -s 1472 api.example.com   # 1472 + 28 byte header = 1500
tracepath api.example.com             # discovers MTU along the path
```

**VPC Flow Logs Analysis**:

Enable VPC Flow Logs on all production VPCs. Use the following query in CloudWatch Logs Insights to find rejected traffic (the most common indicator of security group or NACL misconfiguration):

```
fields @timestamp, srcAddr, dstAddr, srcPort, dstPort, protocol, action
| filter action = "REJECT"
| sort @timestamp desc
| limit 50
```

To find traffic patterns for a specific destination:

```
fields @timestamp, srcAddr, dstPort, packets, bytes, action
| filter dstAddr = "10.0.11.50"
| stats sum(bytes) as totalBytes, count(*) as flowCount by srcAddr, dstPort, action
| sort totalBytes desc
```

**Common Failure Patterns**:

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Connection timeout | Security group missing inbound rule | Add inbound rule for the source SG or CIDR |
| Connection refused | Service not listening on port | Check service status, verify port binding |
| Intermittent drops | Asymmetric routing or NAT table exhaustion | Check route tables, scale NAT Gateways |
| TLS handshake failure | Certificate mismatch or expired cert | Verify SNI, check ACM certificate status |
| DNS resolution failure | Wrong VPC DHCP options, missing private zone | Verify DHCP option set, check zone VPC association |
| Path MTU black hole | Jumbo frames across VPN or internet | Set `DF` bit and reduce MSS; use `tracepath` to find the bottleneck |
