# Privacy Protection

**Ensure compliance with global privacy regulations (GDPR, CCPA) and data lifecycle management**

[← Back to Compliance & Governance](../README.md) | [← Back to Main README](../../../README.md)

---

## Overview

This sub-phase provides comprehensive templates for compliance with major privacy regulations: **GDPR** (EU) and **CCPA** (California), including data subject rights, consent management, and data lifecycle processes.

### Available Templates

1. **GDPR Compliance** - EU General Data Protection Regulation (data subject rights, DPIAs, breach notification)
2. **CCPA Compliance** - California Consumer Privacy Act (consumer rights, opt-out, data deletion)

---

## Privacy Regulations Comparison

| Aspect | GDPR | CCPA |
|--------|------|------|
| **Jurisdiction** | European Union (extraterritorial) | California residents |
| **Scope** | Personal data of EU residents | Personal information of CA residents |
| **Consent** | Opt-in (explicit consent required) | Opt-out (notice + ability to opt out) |
| **Data Subject Rights** | Access, rectification, erasure, portability, restrict processing, object | Access, deletion, opt-out of sale, non-discrimination |
| **Penalties** | Up to €20M or 4% global revenue | Up to $7,500 per intentional violation |
| **Breach Notification** | 72 hours to authority | "Without unreasonable delay" |
| **DPO Required?** | Yes (certain cases) | No |
| **Effective Date** | May 25, 2018 | January 1, 2020 (amended July 1, 2023) |

---

## Quick Start

### Step 1: Determine Applicability

**GDPR Applies If**:
- You offer goods/services to EU residents, OR
- You monitor behavior of EU residents

**CCPA Applies If** (all 3 criteria):
1. You do business in California, AND
2. You collect personal information of CA residents, AND
3. You meet threshold:
   - Annual revenue > $25M, OR
   - Buy/sell/share PI of 100,000+ CA residents/households, OR
   - Derive 50%+ revenue from selling PI

### Step 2: Assess Data Processing

**Map Your Data**:
- What personal data do you collect?
- Why do you collect it (purpose)?
- Where is it stored?
- Who has access?
- How long do you retain it?
- Do you share it with third parties?

**Common Personal Data**:
- Contact information (email, phone, address)
- Account credentials
- Payment information
- IP addresses, cookies, device IDs
- Usage data, behavioral data
- Special categories (health, biometric, etc.)

### Step 3: Choose Your Template

| Language | GDPR Compliance | CCPA Compliance |
|----------|-----------------|-----------------|
| **Python** | [View](./python_gdpr_compliance.md) | [View](./python_ccpa_compliance.md) |
| **JavaScript** | [View](./javascript_gdpr_compliance.md) | [View](./javascript_ccpa_compliance.md) |
| **Java** | [View](./java_gdpr_compliance.md) | [View](./java_ccpa_compliance.md) |
| **C#** | [View](./csharp_gdpr_compliance.md) | [View](./csharp_ccpa_compliance.md) |
| **Go** | [View](./go_gdpr_compliance.md) | [View](./go_ccpa_compliance.md) |
| **C** | [View](./c_gdpr_compliance.md) | [View](./c_ccpa_compliance.md) |
| **C++** | [View](./cpp_gdpr_compliance.md) | [View](./cpp_ccpa_compliance.md) |

---

## Template Deep Dives

### GDPR Compliance Templates

**Purpose**: Ensure compliance with EU General Data Protection Regulation.

**Key Requirements**:

1. **Lawful Basis for Processing**
   - Consent
   - Contract performance
   - Legal obligation
   - Vital interests
   - Public task
   - Legitimate interests

2. **Data Subject Rights** (7 Rights)
   - **Right to Access**: Provide copy of personal data

   - **Right to Rectification**: Correct inaccurate data

   - **Right to Erasure**: Delete data ("right to be forgotten")

   - **Right to Portability**: Export data in machine-readable format

   - **Right to Restrict Processing**: Temporarily halt processing

   - **Right to Object**: Object to processing

   - **Rights Related to Automated Decision-Making**: Opt-out of profiling

3. **Privacy by Design and Default**
   - Minimal data collection
   - Pseudonymization/anonymization
   - Encryption
   - Access controls

4. **Data Protection Impact Assessments (DPIA)**
   - Required for high-risk processing
   - Assess necessity and proportionality
   - Identify and mitigate risks

5. **Breach Notification**
   - Notify supervisory authority within 72 hours
   - Notify affected individuals if high risk
   - Document all breaches

6. **International Transfers**
   - Adequacy decisions
   - Standard contractual clauses (SCCs)
   - Binding corporate rules (BCRs)

7. **Data Processing Agreements (DPAs)**
   - Required for all processors
   - GDPR-compliant clauses
   - Sub-processor requirements

**Code Examples Include**:
- Consent management systems
- Data subject request automation (SAR portal)
- Data deletion procedures ("right to be forgotten")
- Data export (portability) in JSON format
- Breach notification workflows
- DPIA templates and automation

**Time Investment**: 5-7 hours per language

**Use Cases**:
- EU market operations
- Global SaaS products
- Processing EU resident data
- Marketing to EU audiences

### CCPA Compliance Templates

**Purpose**: Ensure compliance with California Consumer Privacy Act (and CPRA amendments).

**Key Requirements**:

1. **Consumer Rights** (4 Primary Rights)
   - **Right to Know**: What personal information is collected, used, shared, sold

   - **Right to Delete**: Request deletion of personal information

   - **Right to Opt-Out**: Opt out of sale/sharing of personal information

   - **Right to Non-Discrimination**: No discrimination for exercising rights

2. **Notice Requirements**
   - Privacy policy at collection
   - "Do Not Sell or Share My Personal Information" link
   - Notice of financial incentive (if applicable)

3. **Verifiable Consumer Requests**
   - Authenticate requestor
   - Respond within 45 days (90-day extension allowed)
   - Free of charge (limited exceptions)

4. **Data Minimization**
   - Collect only necessary data
   - Retention limits
   - Purpose specification

5. **Security Requirements**
   - Reasonable security procedures
   - Protect against unauthorized access

6. **Service Provider Contracts**
   - CCPA-compliant clauses
   - Restrictions on data use
   - Sub-contractor requirements

**Code Examples Include**:
- "Do Not Sell" opt-out mechanism
- Consumer request portal (know, delete, opt-out)
- Request verification (2-step)
- Data deletion automation
- Privacy policy generators
- Opt-out preference signals (Global Privacy Control)

**Time Investment**: 4-6 hours per language

**Use Cases**:
- California operations
- US-based businesses
- E-commerce selling to CA
- Advertising/marketing platforms

---

## Data Subject/Consumer Rights Implementation

### Right to Access (GDPR + CCPA)

**Requirement**: Provide copy of all personal data held about the individual.

**Implementation**:

```python
# Data subject access request (DSAR) implementation
import json
from datetime import datetime

class DataSubjectAccessRequest:
    """Handle GDPR/CCPA access requests."""

    def generate_data_export(self, user_id):
        """
        Generate comprehensive data export for user.

        Includes all personal data across systems.
        Format: Machine-readable JSON (GDPR requirement).
        """
        export_data = {
            "request_date": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "profile": self._get_profile_data(user_id),
            "account_history": self._get_account_history(user_id),
            "transactions": self._get_transactions(user_id),
            "support_tickets": self._get_support_tickets(user_id),
            "logs": self._get_user_logs(user_id),  # Anonymized
            "third_party_sharing": self._get_third_party_sharing(user_id)
        }

        # Audit log
        logger.info("Data export generated", extra={
            "event": "dsar_export",
            "user_id": user_id,
            "data_categories": list(export_data.keys()),
            "timestamp": datetime.utcnow().isoformat()
        })

        return export_data

    def _get_profile_data(self, user_id):
        """Retrieve user profile data."""
        return db.users.find_one({"user_id": user_id}, {
            "_id": 0,  # Exclude internal IDs
            "email": 1,
            "name": 1,
            "phone": 1,
            "address": 1,
            "date_of_birth": 1,
            "created_date": 1,
            "last_login": 1
        })

    def _get_third_party_sharing(self, user_id):
        """Document third-party data sharing (GDPR/CCPA requirement)."""
        return {
            "analytics_providers": ["Google Analytics", "Mixpanel"],
            "advertising_partners": ["Facebook", "Google Ads"],
            "payment_processors": ["Stripe"],
            "data_shared": ["Email (hashed)", "Usage data", "Payment data"]
        }
```

### Right to Deletion / Erasure (GDPR + CCPA)

**Requirement**: Delete all personal data upon request (with exceptions).

**Exceptions** (GDPR):
- Compliance with legal obligation
- Public interest / official authority
- Archiving / research / statistical purposes
- Legal claims

**Exceptions** (CCPA):
- Complete transaction
- Detect security incidents
- Comply with legal obligation
- Internal use reasonably aligned with expectations

**Implementation**:

```python
# Right to deletion implementation
from enum import Enum

class DeletionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"

class DataDeletionRequest:
    """Handle GDPR right to erasure / CCPA right to deletion."""

    def process_deletion_request(self, user_id, regulation="GDPR"):
        """
        Process deletion request with compliance checks.

        Args:
            user_id: User requesting deletion
            regulation: "GDPR" or "CCPA"
        """
        # Check for exceptions
        exceptions = self._check_deletion_exceptions(user_id)

        if exceptions:
            logger.warning("Deletion request rejected", extra={
                "user_id": user_id,
                "regulation": regulation,
                "exceptions": exceptions
            })
            return {
                "status": DeletionStatus.REJECTED,
                "reason": "Legal obligation to retain data",
                "exceptions": exceptions
            }

        # Create deletion task
        deletion_id = self._create_deletion_task(user_id, regulation)

        # Execute deletion across all systems
        self._delete_user_data(user_id, deletion_id)

        # Notify user
        self._send_deletion_confirmation(user_id)

        logger.info("Data deletion completed", extra={
            "event": "data_deletion",
            "user_id": user_id,
            "deletion_id": deletion_id,
            "regulation": regulation,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {
            "status": DeletionStatus.COMPLETED,
            "deletion_id": deletion_id,
            "completed_date": datetime.utcnow()
        }

    def _delete_user_data(self, user_id, deletion_id):
        """
        Delete user data across all systems.

        Hard delete vs. soft delete considerations:
        - Hard delete: Permanent removal
        - Soft delete: Mark as deleted, retain for legal/audit
        """
        # Primary database
        db.users.delete_one({"user_id": user_id})

        # Backup systems (must delete here too!)
        self._delete_from_backups(user_id)

        # Analytics systems
        self._request_analytics_deletion(user_id)

        # Third-party processors (DPAs require deletion)
        self._notify_processors_for_deletion(user_id)

        # Logs (anonymize personal data, retain for security)
        self._anonymize_user_logs(user_id)

        # Audit trail (retain deletion record for compliance)
        db.deletion_audit.insert_one({
            "deletion_id": deletion_id,
            "user_id": user_id,  # Retain for audit only
            "deleted_date": datetime.utcnow(),
            "systems_deleted_from": [
                "primary_db", "backups", "analytics", "logs"
            ]
        })

    def _check_deletion_exceptions(self, user_id):
        """Check if legal exceptions prevent deletion."""
        exceptions = []

        # Active legal hold?
        if self._has_legal_hold(user_id):
            exceptions.append("Legal hold active")

        # Ongoing transaction?
        if self._has_pending_transactions(user_id):
            exceptions.append("Pending transaction must complete")

        # Tax/accounting retention requirement?
        if self._requires_tax_retention(user_id):
            exceptions.append("Tax records must be retained (7 years)")

        return exceptions
```

### Right to Opt-Out of Sale (CCPA-Specific)

**Requirement**: Allow consumers to opt out of sale of personal information.

**Implementation**:

```python
# CCPA opt-out implementation
class CCPAOptOut:
    """Handle CCPA opt-out of sale requests."""

    def process_opt_out(self, user_id, opt_out_type="sale"):
        """
        Process CCPA opt-out request.

        Types:
        - "sale": Opt out of selling personal information
        - "sharing": Opt out of sharing for cross-context behavioral advertising
        """
        # Record opt-out preference
        db.privacy_preferences.update_one(
            {"user_id": user_id},
            {"$set": {
                f"ccpa_opt_out_{opt_out_type}": True,
                f"ccpa_opt_out_{opt_out_type}_date": datetime.utcnow()
            }},
            upsert=True
        )

        # Stop data sharing immediately
        self._stop_data_sharing(user_id, opt_out_type)

        # Notify advertising partners
        self._notify_partners_opt_out(user_id)

        # Set cookie for "Do Not Sell" preference
        set_cookie("ccpa_opt_out", "true", max_age=years(1))

        logger.info("CCPA opt-out processed", extra={
            "event": "ccpa_opt_out",
            "user_id": user_id,
            "opt_out_type": opt_out_type,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {"status": "opted_out", "type": opt_out_type}

    def check_opt_out_status(self, user_id):
        """Check if user has opted out (before sharing data)."""
        prefs = db.privacy_preferences.find_one({"user_id": user_id})

        if prefs and prefs.get("ccpa_opt_out_sale"):
            # User opted out - do not sell/share
            return {"opted_out": True, "since": prefs.get("ccpa_opt_out_sale_date")}

        # Check Global Privacy Control (GPC) signal
        if request.headers.get("Sec-GPC") == "1":
            # Browser indicates opt-out preference
            self.process_opt_out(user_id, "sale")
            return {"opted_out": True, "via": "GPC"}

        return {"opted_out": False}
```

---

## Consent Management

### GDPR Consent Requirements

**Valid Consent Must Be**:
- **Freely given**: No coercion

- **Specific**: Purpose-specific

- **Informed**: Clear explanation

- **Unambiguous**: Clear affirmative action

- **Withdrawable**: Easy to withdraw as to give

**Implementation**:

```python
# GDPR-compliant consent management
class ConsentManager:
    """Manage GDPR consent for data processing."""

    CONSENT_PURPOSES = {
        "essential": "Essential site functionality (no consent required)",
        "analytics": "Anonymous analytics to improve service",
        "marketing": "Personalized marketing communications",
        "advertising": "Targeted advertising",
        "third_party": "Sharing with third-party partners"
    }

    def request_consent(self, user_id, purposes):
        """
        Request consent for specific purposes.

        Displays clear, specific consent requests.
        """
        consent_request_id = generate_uuid()

        for purpose in purposes:
            db.consent_requests.insert_one({
                "request_id": consent_request_id,
                "user_id": user_id,
                "purpose": purpose,
                "purpose_description": self.CONSENT_PURPOSES[purpose],
                "requested_date": datetime.utcnow(),
                "status": "pending"
            })

        return consent_request_id

    def record_consent(self, user_id, purpose, granted):
        """
        Record user consent decision.

        Maintains audit trail of all consent actions.
        """
        db.consent_records.insert_one({
            "user_id": user_id,
            "purpose": purpose,
            "granted": granted,
            "consent_date": datetime.utcnow(),
            "consent_method": "explicit_opt_in",  # GDPR requirement
            "ip_address": get_request_ip(),
            "user_agent": get_user_agent()
        })

        logger.info("Consent recorded", extra={
            "event": "consent_recorded",
            "user_id": user_id,
            "purpose": purpose,
            "granted": granted
        })

        if not granted:
            # User declined - do not process for this purpose
            self._stop_processing_for_purpose(user_id, purpose)

    def withdraw_consent(self, user_id, purpose):
        """
        Allow user to withdraw consent (GDPR requirement).

        Must be as easy to withdraw as to give.
        """
        # Mark consent as withdrawn
        db.consent_records.update_many(
            {"user_id": user_id, "purpose": purpose, "granted": True},
            {"$set": {
                "withdrawn": True,
                "withdrawn_date": datetime.utcnow()
            }}
        )

        # Stop processing immediately
        self._stop_processing_for_purpose(user_id, purpose)

        logger.info("Consent withdrawn", extra={
            "event": "consent_withdrawn",
            "user_id": user_id,
            "purpose": purpose
        })
```

---

## Breach Notification

### GDPR: 72-Hour Rule

**Requirement**: Notify supervisory authority within 72 hours of becoming aware of a breach.

**Notification Must Include**:
- Nature of the breach
- Categories and approximate number of affected data subjects
- Categories and approximate number of affected personal data records
- Contact point (DPO)
- Likely consequences
- Measures taken or proposed

### CCPA: Reasonable Timeframe

**Requirement**: Notify affected individuals "without unreasonable delay."

**Best Practice**: Follow GDPR 72-hour standard.

**Implementation**:

```python
# Breach notification automation
class BreachNotification:
    """Handle GDPR/CCPA breach notifications."""

    def declare_breach(self, incident_id, affected_users, data_categories):
        """
        Declare data breach and initiate notification workflow.

        Automatically calculates 72-hour deadline.
        """
        breach_id = generate_uuid()
        deadline = datetime.utcnow() + timedelta(hours=72)

        db.breaches.insert_one({
            "breach_id": breach_id,
            "incident_id": incident_id,
            "declared_date": datetime.utcnow(),
            "notification_deadline": deadline,
            "affected_user_count": len(affected_users),
            "data_categories": data_categories,
            "status": "declared"
        })

        # Alert security team
        send_alert("CRITICAL: Data breach declared", {
            "breach_id": breach_id,
            "deadline": deadline,
            "affected_users": len(affected_users)
        })

        # Initiate notification workflow
        self._prepare_authority_notification(breach_id)
        if self._is_high_risk(data_categories):
            self._prepare_user_notifications(breach_id, affected_users)

        logger.critical("Data breach declared", extra={
            "breach_id": breach_id,
            "affected_users": len(affected_users),
            "deadline": deadline.isoformat()
        })

        return breach_id

    def notify_supervisory_authority(self, breach_id):
        """
        Notify supervisory authority (GDPR requirement).

        Must include all required information.
        """
        breach = db.breaches.find_one({"breach_id": breach_id})

        notification = {
            "breach_id": breach_id,
            "nature_of_breach": breach["description"],
            "affected_data_subjects": breach["affected_user_count"],
            "affected_records": breach["affected_record_count"],
            "data_categories": breach["data_categories"],
            "contact_dpo": get_dpo_contact(),
            "likely_consequences": breach["impact_assessment"],
            "measures_taken": breach["remediation_actions"]
        }

        # Submit to authority portal (automated)
        response = submit_to_gdpr_authority(notification)

        db.breaches.update_one(
            {"breach_id": breach_id},
            {"$set": {
                "authority_notified": True,
                "authority_notification_date": datetime.utcnow(),
                "authority_reference": response["reference_number"]
            }}
        )

        logger.critical("Supervisory authority notified", extra={
            "breach_id": breach_id,
            "reference": response["reference_number"]
        })
```

---

## Integration with Compliance Frameworks

### SOC 2 Integration

Privacy controls support SOC 2:
- **Privacy (P)**: If Privacy TSC is in scope

- **CC6.7**: Encryption of personal data

- **CC7.4**: Data management and retention

### ISO 27001 Integration

Maps to:
- **Control 5.33**: Protection of records

- **Control 5.34**: Privacy and protection of PII

- **Control 5.36**: Compliance with internal policies and external requirements

### ISO 42001 (AI Systems) Integration

For AI/ML systems processing personal data:
- Training data privacy
- Model outputs containing personal data
- Automated decision-making (GDPR Article 22)

---

## Success Criteria

### GDPR Compliance

- [ ] Lawful basis documented for all processing
- [ ] Privacy policy published and accessible
- [ ] Data subject request portal operational
- [ ] Consent management system implemented
- [ ] DPIA completed for high-risk processing
- [ ] DPO appointed (if required)
- [ ] Breach notification procedures tested
- [ ] International transfer mechanisms in place

### CCPA Compliance

- [ ] Privacy policy includes CCPA disclosures
- [ ] "Do Not Sell" link on homepage
- [ ] Consumer request portal operational
- [ ] Request verification process (2-step)
- [ ] Service provider agreements updated
- [ ] Privacy practices audit completed

---

## Resources

### Official Guidance

- [GDPR Official Text](https://gdpr-info.eu/)
- [CCPA Official Text](https://oag.ca.gov/privacy/ccpa)
- [EDPB Guidelines](https://edpb.europa.eu/our-work-tools/general-guidance/gdpr-guidelines-recommendations-best-practices_en)
- [California AG CCPA Regulations](https://oag.ca.gov/privacy/ccpa/regs)

### Tools

- **Consent Management**: OneTrust, Cookiebot, Osano

- **Data Mapping**: OneTrust, BigID, Collibra

- **DSAR Automation**: OneTrust, DataGrail, Transcend

- **Cookie Scanning**: Cookiebot, OneTrust

---

## Time Estimates

| Template | Research | Implementation | Testing | Total |
|----------|----------|----------------|---------|-------|
| GDPR Compliance | 2 hours | 3-4 hours | 1 hour | 5-7 hours |
| CCPA Compliance | 1 hour | 2-3 hours | 1 hour | 4-6 hours |

**Total per language**: 9-13 hours for both templates

---

[← Back to Compliance & Governance](../README.md) | [← Back to Main README](../../../README.md)
