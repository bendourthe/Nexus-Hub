# Incident Response

**Prepare for security incidents with documented response procedures and recovery plans**

[← Back to Compliance & Governance](../README.md) | [← Back to Main README](../../../README.md)

---

## Overview

This sub-phase provides comprehensive incident response templates for detecting, containing, eradicating, recovering from, and learning from security incidents and data breaches.

### Available Templates

1. **Incident Response Plans** - Detection, containment, eradication, recovery, lessons learned
2. **Breach Protocols** - Notification procedures, regulatory reporting, stakeholder communication

---

## Incident Response Lifecycle

### The 6 Phases

```
1. PREPARATION
   ↓
2. IDENTIFICATION & DETECTION
   ↓
3. CONTAINMENT
   ↓
4. ERADICATION
   ↓
5. RECOVERY
   ↓
6. LESSONS LEARNED
```

---

## Quick Start

### Step 1: Assess Incident Response Readiness

**Questions to Ask**:
- Do you have a documented incident response plan?
- Is there an incident response team assigned?
- Are escalation procedures defined?
- Have you conducted tabletop exercises?
- Are runbooks documented for common incidents?

**Common Gap**: Plan exists but team hasn't practiced (untested procedures fail under pressure).

### Step 2: Choose Your Template

| Language | Incident Response Plan | Breach Protocols |
|----------|------------------------|------------------|
| **Python** | [View](./python_incident_response_plan.md) | [View](./python_breach_protocols.md) |
| **JavaScript** | [View](./javascript_incident_response_plan.md) | [View](./javascript_breach_protocols.md) |
| **Java** | [View](./java_incident_response_plan.md) | [View](./java_breach_protocols.md) |
| **C#** | [View](./csharp_incident_response_plan.md) | [View](./csharp_breach_protocols.md) |
| **Go** | [View](./go_incident_response_plan.md) | [View](./go_breach_protocols.md) |
| **C** | [View](./c_incident_response_plan.md) | [View](./c_breach_protocols.md) |
| **C++** | [View](./cpp_incident_response_plan.md) | [View](./cpp_breach_protocols.md) |

### Step 3: Build Your Incident Response Team

**Core Roles**:
- **Incident Commander**: Overall coordination, decisions
- **Security Lead**: Technical investigation, forensics
- **Engineering**: System access, technical remediation
- **Legal**: Regulatory requirements, liability
- **Communications**: Internal/external messaging
- **Executive Sponsor**: Authority for major decisions

---

## Template Deep Dives

### Incident Response Plan Templates

**Purpose**: Comprehensive procedures for responding to security incidents.

**Included Procedures**:

1. **Incident Classification**
   - Severity levels (P1-P4)
   - Incident types (intrusion, malware, DDoS, data breach, etc.)
   - Escalation criteria

2. **Detection & Identification**
   - Security monitoring and alerting
   - Incident reporting channels
   - Initial triage
   - Scope assessment

3. **Containment Strategies**
   - Short-term containment (isolate affected systems)
   - Long-term containment (temporary fixes while maintaining operations)
   - Evidence preservation
   - System backups

4. **Eradication**
   - Root cause analysis
   - Remove threat actor access
   - Patch vulnerabilities
   - Malware removal
   - Credential rotation

5. **Recovery**
   - System restoration from clean backups
   - Verification and validation
   - Enhanced monitoring
   - Return to normal operations

6. **Post-Incident Activities**
   - Incident documentation
   - Lessons learned meeting
   - Update procedures and controls
   - Training and awareness

**Code Examples Include**:
- Automated incident detection
- Forensics data collection
- System isolation procedures
- Automated remediation scripts
- Incident tracking and documentation

**Time Investment**: 4-6 hours per language

**Use Cases**:
- SOC 2 CC7.5 (Detect and respond to security incidents)
- ISO 27001 Control 5.24 (Information security incident management)
- GDPR breach response
- Business continuity requirements

### Breach Protocol Templates

**Purpose**: Specific procedures for data breach incidents (subset of incident response).

**Regulatory Requirements**:
- **GDPR**: Notify supervisory authority within 72 hours
- **CCPA**: Notify affected individuals "without unreasonable delay"
- **State breach laws**: Varies by state (often 30-60 days)
- **Sector-specific**: HIPAA (60 days), PCI-DSS (immediately)

**Breach Response Phases**:

1. **Breach Declaration**
   - Determine if personal data compromised
   - Assess severity and scope
   - Activate breach response team

2. **Investigation**
   - What data was accessed?
   - How many individuals affected?
   - How did breach occur?
   - Has data been exfiltrated?

3. **Notification Decision Tree**
   - Authority notification required? (GDPR: Yes within 72 hours)
   - Individual notification required? (High risk to individuals)
   - Media/public notification required? (Large-scale breach)
   - Credit monitoring offered? (SSN/financial data)

4. **Notification Execution**
   - Draft notifications (legal review)
   - Notify supervisory authorities
   - Notify affected individuals (email, postal, substitute notice)
   - Notify business partners/customers
   - Media statement (if public)

5. **Remediation & Monitoring**
   - Implement additional controls
   - Enhanced monitoring
   - Victim support (credit monitoring, hotline)

**Code Examples Include**:
- Breach detection triggers
- Affected user identification
- Automated notification workflows
- Regulatory reporting automation
- Post-breach monitoring

**Time Investment**: 4-6 hours per language

---

## Incident Severity Classification

### Severity Levels

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **P1 (Critical)** | Immediate threat, active incident, data breach | Immediate (< 15 min) | Active ransomware, ongoing data exfiltration, credential compromise |
| **P2 (High)** | Serious security issue, potential for escalation | 1 hour | Failed intrusion attempt, malware detected, vulnerability exploitation |
| **P3 (Medium)** | Security concern, limited impact | 4 hours | Suspicious activity, policy violation, phishing attempt |
| **P4 (Low)** | Minor security issue, informational | 24 hours | Security scan finding, minor configuration issue |

---

## Code Implementation Examples

### Incident Detection & Alerting

```python
# Automated incident detection
from enum import Enum

class IncidentSeverity(Enum):
    P1_CRITICAL = "P1"
    P2_HIGH = "P2"
    P3_MEDIUM = "P3"
    P4_LOW = "P4"

class IncidentDetection:
    """Automated incident detection and alerting."""

    def detect_brute_force_attack(self):
        """Detect brute force authentication attacks."""
        # Query failed logins in last 15 minutes
        failed_logins = db.auth_logs.aggregate([
            {"$match": {
                "success": False,
                "timestamp": {"$gte": fifteen_minutes_ago()}
            }},
            {"$group": {
                "_id": "$user_id",
                "attempts": {"$sum": 1},
                "ip_addresses": {"$addToSet": "$ip_address"}
            }},
            {"$match": {"attempts": {"$gte": 10}}}
        ])

        for user in failed_logins:
            incident_id = self.create_incident(
                incident_type="brute_force_attack",
                severity=IncidentSeverity.P2_HIGH,
                affected_user=user["_id"],
                evidence={
                    "failed_attempts": user["attempts"],
                    "source_ips": user["ip_addresses"]
                }
            )

            # Automatic containment
            self.block_ip_addresses(user["ip_addresses"])
            self.lock_user_account(user["_id"])

            # Alert incident response team
            self.send_incident_alert(incident_id)

    def detect_data_exfiltration(self):
        """Detect unusual data download patterns."""
        # Monitor for large data transfers
        large_downloads = db.access_logs.find({
            "action": "download",
            "bytes_transferred": {"$gt": 100 * 1024 * 1024},  # 100 MB
            "timestamp": {"$gte": one_hour_ago()}
        })

        for download in large_downloads:
            # Check if normal for this user
            if not self._is_normal_behavior(download["user_id"], download["bytes_transferred"]):
                incident_id = self.create_incident(
                    incident_type="potential_data_exfiltration",
                    severity=IncidentSeverity.P1_CRITICAL,
                    affected_user=download["user_id"],
                    evidence=download
                )

                # Alert security team immediately (P1)
                self.page_security_team(incident_id)

    def create_incident(self, incident_type, severity, affected_user, evidence):
        """Create incident ticket with automatic routing."""
        incident_id = generate_uuid()

        db.incidents.insert_one({
            "incident_id": incident_id,
            "type": incident_type,
            "severity": severity.value,
            "status": "detected",
            "affected_user": affected_user,
            "detected_date": datetime.utcnow(),
            "evidence": evidence,
            "assigned_to": self._get_on_call_engineer(severity)
        })

        logger.critical(f"Security incident detected: {incident_type}", extra={
            "incident_id": incident_id,
            "severity": severity.value,
            "affected_user": affected_user
        })

        return incident_id
```

### Incident Response Automation

```python
# Automated incident response actions
class IncidentResponse:
    """Automate common incident response actions."""

    def isolate_compromised_system(self, system_id):
        """
        Isolate system from network (containment).

        Preserves evidence while preventing spread.
        """
        # Remove from network
        security_groups.revoke_all_ingress(system_id)
        security_groups.revoke_all_egress(system_id, except_ports=[22])  # Keep SSH for investigation

        # Tag for investigation
        ec2.create_tags(system_id, [{"Key": "Status", "Value": "Quarantined"}])

        # Snapshot for forensics (evidence preservation)
        snapshot_id = ec2.create_snapshot(system_id, description="Forensic snapshot")

        logger.warning(f"System isolated: {system_id}", extra={
            "system_id": system_id,
            "snapshot_id": snapshot_id,
            "action": "quarantine"
        })

        return {"isolated": True, "snapshot_id": snapshot_id}

    def rotate_compromised_credentials(self, credential_type, credential_id):
        """
        Rotate compromised credentials immediately.

        Eradication step: remove attacker access.
        """
        if credential_type == "api_key":
            # Revoke old key
            api_keys.revoke(credential_id)

            # Generate new key
            new_key = api_keys.create()

            # Notify owner
            send_notification(
                to=get_key_owner(credential_id),
                subject="Security Alert: API Key Rotated",
                body=f"Your API key was rotated due to potential compromise. New key: {new_key['id']}"
            )

        elif credential_type == "password":
            # Force password reset
            users.force_password_reset(credential_id)

            # Invalidate all sessions
            sessions.invalidate_all(credential_id)

        logger.warning(f"Credentials rotated: {credential_type}/{credential_id}", extra={
            "credential_type": credential_type,
            "credential_id": credential_id,
            "action": "credential_rotation"
        })

    def collect_forensic_evidence(self, system_id):
        """
        Collect forensic evidence (must be preserved intact).

        Chain of custody maintained for legal proceedings.
        """
        evidence = {
            "collection_date": datetime.utcnow(),
            "collector": get_current_user(),
            "system_id": system_id,
            "evidence_items": []
        }

        # Memory dump
        memory_dump = self._collect_memory_dump(system_id)
        evidence["evidence_items"].append({
            "type": "memory_dump",
            "location": memory_dump["s3_url"],
            "hash": memory_dump["sha256"]
        })

        # Disk snapshot
        snapshot = ec2.create_snapshot(system_id)
        evidence["evidence_items"].append({
            "type": "disk_snapshot",
            "snapshot_id": snapshot["id"],
            "hash": snapshot["sha256"]
        })

        # Logs (last 7 days)
        logs = self._export_logs(system_id, days=7)
        evidence["evidence_items"].append({
            "type": "system_logs",
            "location": logs["s3_url"],
            "hash": logs["sha256"]
        })

        # Store evidence in tamper-proof storage
        evidence_id = self._store_evidence(evidence)

        logger.info(f"Forensic evidence collected: {system_id}", extra={
            "evidence_id": evidence_id,
            "items_collected": len(evidence["evidence_items"])
        })

        return evidence_id
```

### Breach Notification Automation

```python
# Automate breach notifications
class BreachNotification:
    """Automate data breach notification workflows."""

    def assess_breach_notification_requirements(self, incident_id):
        """
        Determine notification requirements based on regulations.

        Returns which authorities and individuals must be notified.
        """
        incident = db.incidents.find_one({"incident_id": incident_id})

        affected_users = self._identify_affected_users(incident)
        data_types = self._classify_compromised_data(incident)

        requirements = {
            "authority_notification": [],
            "individual_notification": False,
            "deadlines": {}
        }

        # GDPR assessment
        if self._affects_eu_residents(affected_users):
            requirements["authority_notification"].append("GDPR_DPA")
            requirements["deadlines"]["GDPR_DPA"] = datetime.utcnow() + timedelta(hours=72)

            if self._is_high_risk_gdpr(data_types):
                requirements["individual_notification"] = True

        # CCPA assessment
        if self._affects_california_residents(affected_users):
            if self._requires_ccpa_notification(data_types):
                requirements["individual_notification"] = True
                requirements["deadlines"]["CCPA"] = "without_unreasonable_delay"

        # State breach laws
        affected_states = self._get_affected_states(affected_users)
        for state in affected_states:
            if self._requires_state_notification(state, data_types):
                requirements["authority_notification"].append(f"{state}_AG")
                requirements["individual_notification"] = True

        return requirements

    def send_breach_notifications(self, incident_id, requirements):
        """Execute breach notification plan."""
        incident = db.incidents.find_one({"incident_id": incident_id})

        # Notify authorities
        for authority in requirements["authority_notification"]:
            notification_id = self._notify_authority(
                authority=authority,
                incident=incident,
                deadline=requirements["deadlines"].get(authority)
            )

            logger.critical(f"Authority notified: {authority}", extra={
                "incident_id": incident_id,
                "authority": authority,
                "notification_id": notification_id
            })

        # Notify affected individuals
        if requirements["individual_notification"]:
            affected_users = self._identify_affected_users(incident)

            for user in affected_users:
                self._send_user_notification(
                    user_id=user["id"],
                    incident_id=incident_id,
                    breach_details=self._prepare_user_notice(incident)
                )

            logger.critical(f"Individual notifications sent: {len(affected_users)}", extra={
                "incident_id": incident_id,
                "notification_count": len(affected_users)
            })

    def _prepare_user_notice(self, incident):
        """
        Prepare breach notification for affected individuals.

        Must include (varies by regulation):
        - What happened
        - What data was compromised
        - What we're doing about it
        - What you should do
        - Contact information
        """
        return {
            "incident_date": incident["detected_date"],
            "incident_description": "Unauthorized access to database",
            "data_compromised": ["Name", "Email", "Phone", "Address"],
            "actions_taken": [
                "Vulnerability patched",
                "Systems secured",
                "Law enforcement notified"
            ],
            "recommended_actions": [
                "Monitor your accounts for suspicious activity",
                "Consider placing fraud alert",
                "We're offering 2 years of free credit monitoring"
            ],
            "contact": {
                "email": "security@company.com",
                "phone": "1-800-XXX-XXXX",
                "hours": "24/7"
            }
        }
```

---

## Integration with Compliance Frameworks

### SOC 2 Integration

Incident response supports:
- **CC7.3**: Incident detection, management, and resolution
- **CC7.5**: Detect and respond to security incidents
- **CC9.2**: Monitor vendor/partner incidents

Documented IR plan and incident records serve as audit evidence.

### ISO 27001 Integration

Maps to:
- **Control 5.24**: Information security incident management planning and preparation
- **Control 5.25**: Assessment and decision on information security events
- **Control 5.26**: Response to information security incidents
- **Control 5.27**: Learning from information security incidents

### GDPR/CCPA Integration

Breach protocols ensure:
- Timely notification (GDPR 72 hours)
- Complete breach documentation
- Affected individual notification
- Regulatory reporting

---

## Tabletop Exercise Template

**Purpose**: Practice incident response without actual incident.

**Scenario**: Ransomware attack encrypts production database.

**Exercise Flow**:
1. **Inject** (9:00 AM): "Production database encrypted, ransom note displayed"
2. **Detect** (9:05 AM): How do we detect? Who gets alerted?
3. **Assess** (9:15 AM): What's the severity? What data is affected?
4. **Contain** (9:30 AM): How do we stop spread? Isolate systems?
5. **Eradicate** (10:00 AM): How do we remove ransomware? Root cause?
6. **Recover** (10:30 AM): Restore from backups? Validate data integrity?
7. **Communicate** (11:00 AM): Who do we notify? What do we say?
8. **Debrief** (11:30 AM): What went well? What needs improvement?

**Conduct annually** and after any significant system changes.

---

## Success Criteria

### Incident Response Plan Complete

- [ ] IR plan documented and approved
- [ ] IR team assigned (with backups)
- [ ] Escalation procedures defined
- [ ] Runbooks created for common incidents
- [ ] Contact lists maintained (24/7)
- [ ] Tabletop exercise conducted annually

### Breach Protocol Complete

- [ ] Breach notification procedures documented
- [ ] Authority notification contacts verified
- [ ] User notification templates prepared
- [ ] Legal review completed
- [ ] Breach notification tested (tabletop)

### Technical Capabilities

- [ ] Incident detection automated
- [ ] Forensic tools available
- [ ] Isolation procedures tested
- [ ] Backup restoration tested
- [ ] Monitoring and alerting operational

---

## Common Pitfalls

### ❌ Untested Procedures

**Problem**: IR plan documented but never practiced. Fails during real incident.

**Solution**: Conduct tabletop exercises annually. Test backup restoration quarterly.

### ❌ Missing Contact Information

**Problem**: Can't reach team members during incident (outdated contact lists).

**Solution**: Maintain 24/7 contact lists, test escalation procedures.

### ❌ No Legal Review

**Problem**: Breach notifications sent without legal review, expose to liability.

**Solution**: Involve legal from the start. Pre-approved templates help speed response.

### ❌ Slow Detection

**Problem**: Incident happened weeks ago but only discovered today (dwell time).

**Solution**: Implement automated detection, continuous monitoring, threat hunting.

---

## Resources

### Frameworks

- [NIST SP 800-61](https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final) - Computer Security Incident Handling Guide
- [SANS Incident Response](https://www.sans.org/white-papers/33901/) - Incident Handler's Handbook
- [ISO 27035](https://www.iso.org/standard/78973.html) - Information security incident management

### Tools

- **SIEM**: Splunk, ELK Stack, Datadog, Sumo Logic
- **Forensics**: Autopsy, Volatility, The Sleuth Kit
- **Orchestration**: Cortex XSOAR, Splunk Phantom, IBM Resilient
- **Communication**: PagerDuty, Opsgenie, Slack

---

## Time Estimates

| Template | Research | Implementation | Testing | Total |
|----------|----------|----------------|---------|-------|
| Incident Response Plan | 1-2 hours | 2-3 hours | 1-2 hours | 4-6 hours |
| Breach Protocols | 1-2 hours | 2-3 hours | 1 hour | 4-6 hours |

**Total per language**: 8-12 hours for both templates

---

[← Back to Compliance & Governance](../README.md) | [← Back to Main README](../../../README.md)
