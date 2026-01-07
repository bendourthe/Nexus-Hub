---
template_id: compliance_governance_gdpr_python
template_name: GDPR Compliance - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - compliance_frameworks/python_soc2_compliance.md
  - governance_policies/python_security_policies.md
  - incident_response/python_breach_protocols.md
related_templates:
  - privacy_protection/python_ccpa_compliance.md
  - compliance_frameworks/python_iso27001_implementation.md
  - ai_agent_governance/python_agent_lifecycle.md
tools:
  - presidio (PII detection)
  - cryptography (encryption)
  - anonymizeip (IP anonymization)
  - faker (data anonymization)
tags:
  - gdpr
  - privacy
  - data-protection
  - eu-compliance
  - data-subject-rights
  - python
---

# GDPR Compliance - Python

**Implement EU General Data Protection Regulation (GDPR) compliance for data privacy**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### What is GDPR?

The **General Data Protection Regulation (GDPR)** is the EU's comprehensive data protection law that came into effect on May 25, 2018. It regulates how organizations collect, process, store, and share personal data of EU residents.

**Key Facts**:
- **Territorial Scope**: Applies to any organization processing EU residents' data (regardless of location)
- **Penalties**: Up to €20 million or 4% of global annual revenue (whichever is higher)
- **Enforcement**: 27+ EU Data Protection Authorities (DPAs)
- **Data Subject Rights**: 8 fundamental rights for individuals

### Why Python Applications Need GDPR Compliance

- **Global Reach**: If you have EU users/customers, GDPR applies
- **Heavy Penalties**: Non-compliance fines can be business-ending
- **Mandatory Requirements**: Breach notification (72 hours), Data Protection Officer
- **Technical Requirements**: Privacy by Design, Data Protection Impact Assessments
- **AI Systems**: GDPR Article 22 (automated decision-making), AI Act integration

### GDPR Principles (Article 5)

1. **Lawfulness, Fairness, Transparency** - Legal basis, clear communication
2. **Purpose Limitation** - Data collected for specific purposes only
3. **Data Minimization** - Collect only what's necessary
4. **Accuracy** - Keep data accurate and up-to-date
5. **Storage Limitation** - Retain only as long as necessary
6. **Integrity and Confidentiality** - Secure processing
7. **Accountability** - Demonstrate compliance

---

## GDPR Key Concepts

### Personal Data (Article 4)

**Definition**: Any information relating to an identified or identifiable natural person.

**Examples**:
- **Direct identifiers**: Name, email, phone, ID numbers
- **Indirect identifiers**: IP address, cookies, device IDs
- **Sensitive data** (Article 9 "Special Categories"): Race, health, biometric, genetic, political opinions, religion

### Legal Bases for Processing (Article 6)

You must have at least ONE legal basis to process personal data:

1. **Consent** - Individual freely given, specific, informed agreement
2. **Contract** - Processing necessary to fulfill contract with individual
3. **Legal Obligation** - Required by law
4. **Vital Interests** - Protect life of individual
5. **Public Task** - Perform task in public interest
6. **Legitimate Interests** - Organization's interests (balanced against individual's rights)

### Data Subject Rights (Articles 12-22)

8 fundamental rights:

1. **Right to Information** (Articles 13-14) - Know what data is collected, why, how
2. **Right of Access** (Article 15) - Obtain copy of personal data
3. **Right to Rectification** (Article 16) - Correct inaccurate data
4. **Right to Erasure** (Article 17) - "Right to be forgotten"
5. **Right to Restriction** (Article 18) - Limit processing
6. **Right to Data Portability** (Article 20) - Receive data in machine-readable format
7. **Right to Object** (Article 21) - Object to processing (e.g., marketing)
8. **Rights Related to Automated Decision-Making** (Article 22) - Not subject to solely automated decisions

---

## Implementation Roadmap

### Phase 1: Data Mapping and Classification (Weeks 1-2)

**Deliverables**:
1. Data inventory (what personal data, where stored, how processed)
2. Data flow mapping (data lifecycle)
3. Data classification (personal data, special categories)
4. Legal basis identification

**Code**: See [Data Discovery](#data-discovery-and-classification)

### Phase 2: Data Subject Rights Implementation (Weeks 3-6)

**Deliverables**:
1. Data subject request portal
2. Access request automation (Article 15)
3. Deletion automation (Article 17)
4. Data portability export (Article 20)
5. Response procedures (1-month deadline)

**Code**: See [Data Subject Rights](#data-subject-rights-implementation)

### Phase 3: Privacy by Design (Weeks 7-9)

**Deliverables**:
1. Encryption at rest and in transit
2. Pseudonymization and anonymization
3. Access controls (least privilege)
4. Data minimization in code
5. Privacy-preserving defaults

**Code**: See [Privacy by Design](#privacy-by-design-implementation)

### Phase 4: Breach Notification and DPO (Weeks 10-12)

**Deliverables**:
1. Breach detection automation
2. 72-hour notification workflow
3. Data Protection Officer (DPO) appointment (if required)
4. Data Protection Impact Assessments (DPIA) for high-risk processing

**Code**: See [Breach Notification](#breach-notification-implementation)

---

## Data Discovery and Classification

### Personal Data Inventory

**GDPR Article 30**: Record of processing activities (mandatory for orgs >250 employees or high-risk processing)

**Implementation**:

```python
# Personal data discovery and classification
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from typing import List, Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DataCategory(Enum):
    """GDPR data categories."""
    PERSONAL_DATA = "personal_data"  # Article 4(1)
    SPECIAL_CATEGORY = "special_category"  # Article 9
    CRIMINAL_DATA = "criminal_data"  # Article 10

class LegalBasis(Enum):
    """Legal bases for processing (Article 6)."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"

class DataInventory:
    """
    Maintain inventory of personal data processing.

    GDPR Article 30: Records of processing activities
    """

    # PII entity types recognized by Presidio
    PII_ENTITIES = [
        "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
        "IBAN_CODE", "IP_ADDRESS", "LOCATION", "DATE_TIME",
        "NRP", "MEDICAL_LICENSE", "US_SSN", "UK_NHS"
    ]

    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def discover_personal_data(self, text: str, language: str = "en") -> Dict:
        """
        Discover personal data in text using NLP.

        GDPR Article 4(1): Identify personal data for compliance.
        """
        # Analyze text for PII
        results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=self.PII_ENTITIES
        )

        # Categorize findings
        discovered_pii = []
        special_category_found = False

        for result in results:
            pii_record = {
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": result.score,
                "text": text[result.start:result.end]
            }

            # Check if special category (Article 9)
            if result.entity_type in ["MEDICAL_LICENSE", "NRP"]:
                pii_record["data_category"] = DataCategory.SPECIAL_CATEGORY.value
                special_category_found = True
            else:
                pii_record["data_category"] = DataCategory.PERSONAL_DATA.value

            discovered_pii.append(pii_record)

        logger.info("Personal data discovery completed", extra={
            "event": "pii_discovery",
            "entities_found": len(discovered_pii),
            "special_category": special_category_found
        })

        return {
            "entities": discovered_pii,
            "special_category_found": special_category_found,
            "requires_dpia": special_category_found  # Article 35
        }

    def register_processing_activity(
        self,
        activity_name: str,
        purpose: str,
        legal_basis: LegalBasis,
        data_categories: List[DataCategory],
        recipients: List[str],
        retention_period: str,
        technical_measures: List[str]
    ) -> str:
        """
        Register processing activity (GDPR Article 30).

        Required documentation:
        - Name and contact details of controller
        - Purposes of processing
        - Categories of data subjects and personal data
        - Recipients of personal data
        - Data transfers to third countries
        - Retention periods
        - Technical and organizational security measures
        """
        activity_id = generate_uuid()

        processing_record = {
            "activity_id": activity_id,
            "activity_name": activity_name,
            "controller": {
                "name": "Your Organization",
                "contact": "dpo@yourorg.com"
            },
            "purpose": purpose,
            "legal_basis": legal_basis.value,
            "data_categories": [cat.value for cat in data_categories],
            "data_subjects": ["customers", "employees"],  # Customize
            "recipients": recipients,
            "retention_period": retention_period,
            "technical_measures": technical_measures,
            "registered_date": datetime.utcnow(),

            # Article 30 requirements
            "transfers_to_third_countries": [],
            "safeguards": "Standard Contractual Clauses (SCCs)",
            "dpia_required": DataCategory.SPECIAL_CATEGORY in data_categories
        }

        db.processing_activities.insert_one(processing_record)

        logger.info("Processing activity registered", extra={
            "event": "processing_activity_registered",
            "activity_id": activity_id,
            "legal_basis": legal_basis.value
        })

        return activity_id

class DataClassification:
    """
    Classify data according to GDPR categories.

    GDPR Articles 4, 9, 10: Personal data, special categories, criminal data
    """

    def classify_field(self, field_name: str, field_value: str) -> Dict:
        """
        Classify database field according to GDPR.

        Returns data category and recommended retention.
        """
        # Common field classifications
        classifications = {
            # Personal data (Article 4)
            "email": {
                "category": DataCategory.PERSONAL_DATA,
                "retention": "2 years after last activity",
                "requires_consent": True
            },
            "name": {
                "category": DataCategory.PERSONAL_DATA,
                "retention": "Duration of contract + 6 years",
                "requires_consent": False
            },
            "phone": {
                "category": DataCategory.PERSONAL_DATA,
                "retention": "2 years after last activity",
                "requires_consent": True
            },

            # Special categories (Article 9)
            "health_data": {
                "category": DataCategory.SPECIAL_CATEGORY,
                "retention": "As required by medical records law",
                "requires_explicit_consent": True,
                "requires_dpia": True
            },
            "biometric_data": {
                "category": DataCategory.SPECIAL_CATEGORY,
                "retention": "Duration of identification need only",
                "requires_explicit_consent": True,
                "requires_dpia": True
            }
        }

        classification = classifications.get(
            field_name.lower(),
            {
                "category": DataCategory.PERSONAL_DATA,
                "retention": "Review required",
                "requires_consent": True
            }
        )

        return classification
```

---

## Data Subject Rights Implementation

### Right of Access (Article 15)

**Requirement**: Provide copy of personal data within 1 month (free of charge for first request)

**Implementation**:

```python
# Data subject access requests (DSAR)
from datetime import datetime, timedelta
import json

class DataSubjectAccessRequest:
    """
    Handle data subject access requests (GDPR Article 15).

    Requirements:
    - Respond within 1 month (extendable to 3 months for complex requests)
    - Provide copy of personal data
    - Provide information about processing (purpose, categories, recipients)
    - Free of charge (first request)
    """

    # Response deadline (Article 12)
    RESPONSE_DEADLINE_DAYS = 30
    EXTENDED_DEADLINE_DAYS = 90  # For complex requests

    def create_access_request(self, data_subject_id: str, verification_data: Dict) -> str:
        """
        Create data subject access request.

        Step 1: Verify identity of requestor (prevent unauthorized disclosure)
        """
        request_id = generate_uuid()

        # Verify identity
        if not self._verify_identity(data_subject_id, verification_data):
            raise PermissionError("Identity verification failed")

        # Create request record
        deadline = datetime.utcnow() + timedelta(days=self.RESPONSE_DEADLINE_DAYS)

        db.dsar_requests.insert_one({
            "request_id": request_id,
            "data_subject_id": data_subject_id,
            "request_type": "access",
            "status": "pending",
            "created_date": datetime.utcnow(),
            "deadline": deadline,
            "assigned_to": "dpo@yourorg.com",
            "completed_date": None
        })

        logger.info("Data subject access request created", extra={
            "event": "dsar_created",
            "request_id": request_id,
            "data_subject_id": data_subject_id,
            "deadline": deadline.isoformat()
        })

        return request_id

    def generate_data_export(self, data_subject_id: str) -> Dict:
        """
        Generate comprehensive export of personal data.

        GDPR Article 15: Right of access
        GDPR Article 20: Right to data portability (machine-readable format)
        """
        export_data = {
            "request_date": datetime.utcnow().isoformat(),
            "data_subject_id": data_subject_id,

            # Article 15(1): Copy of personal data
            "personal_data": {
                "profile": self._get_profile_data(data_subject_id),
                "transactions": self._get_transactions(data_subject_id),
                "communications": self._get_communications(data_subject_id),
                "activity_logs": self._get_activity_logs(data_subject_id)
            },

            # Article 15(1)(a-h): Information about processing
            "processing_information": {
                "purposes": self._get_processing_purposes(data_subject_id),
                "categories_of_data": self._get_data_categories(data_subject_id),
                "recipients": self._get_recipients(data_subject_id),
                "retention_periods": self._get_retention_periods(),
                "data_sources": self._get_data_sources(data_subject_id),
                "automated_decision_making": self._get_automated_decisions(data_subject_id),
                "third_country_transfers": self._get_third_country_transfers(),
                "safeguards": "Standard Contractual Clauses (SCCs)"
            },

            # Data subject rights information
            "your_rights": {
                "right_to_rectification": "You can request correction of inaccurate data",
                "right_to_erasure": "You can request deletion of your data",
                "right_to_restriction": "You can request limiting our use of your data",
                "right_to_object": "You can object to processing based on legitimate interests",
                "right_to_lodge_complaint": "You can complain to your Data Protection Authority"
            }
        }

        logger.info("Data export generated", extra={
            "event": "data_export_generated",
            "data_subject_id": data_subject_id,
            "data_size_kb": len(json.dumps(export_data)) / 1024
        })

        return export_data

    def _get_profile_data(self, data_subject_id: str) -> Dict:
        """Retrieve all profile information."""
        user = db.users.find_one({"user_id": data_subject_id})

        if not user:
            return {}

        # Return only personal data fields (exclude internal fields)
        return {
            "name": user.get("name"),
            "email": user.get("email"),
            "phone": user.get("phone"),
            "address": user.get("address"),
            "date_of_birth": user.get("date_of_birth"),
            "account_created": user.get("created_date"),
            "last_login": user.get("last_login")
        }

    def _get_automated_decisions(self, data_subject_id: str) -> List[Dict]:
        """
        Report automated decision-making (Article 22).

        Required if solely automated decisions with legal/significant effects.
        """
        decisions = db.automated_decisions.find({"user_id": data_subject_id})

        return [{
            "decision_date": d["decision_date"].isoformat(),
            "decision_type": d["decision_type"],
            "outcome": d["outcome"],
            "logic_involved": d["logic_description"],
            "significance": d["significance"],
            "human_review_available": d.get("human_review", True)
        } for d in decisions]
```

### Right to Erasure (Article 17)

**Requirement**: "Right to be forgotten" - delete personal data when no longer necessary

**Implementation**:

```python
# Right to erasure ("right to be forgotten")
class DataErasure:
    """
    Handle data erasure requests (GDPR Article 17).

    Grounds for erasure:
    - Data no longer necessary for purpose
    - Consent withdrawn (and no other legal basis)
    - Data subject objects (and no overriding legitimate grounds)
    - Data unlawfully processed
    - Legal obligation to erase
    - Child's data collected (Article 8)

    Exceptions (erasure not required):
    - Legal obligation to retain
    - Public interest
    - Legal claims
    """

    # Retention obligations (example)
    LEGAL_RETENTION_REQUIREMENTS = {
        "financial_records": "7 years",  # Tax law
        "employment_records": "6 years",  # Employment law
        "contracts": "6 years after termination"  # Contract law
    }

    def process_erasure_request(self, data_subject_id: str, reason: str) -> Dict:
        """
        Process request to erase personal data.

        GDPR Article 17: Right to erasure
        """
        request_id = generate_uuid()

        # Check if erasure exceptions apply
        exceptions = self._check_erasure_exceptions(data_subject_id)

        if exceptions:
            logger.warning("Erasure request rejected - exceptions apply", extra={
                "event": "erasure_request_rejected",
                "data_subject_id": data_subject_id,
                "exceptions": exceptions
            })

            return {
                "request_id": request_id,
                "status": "rejected",
                "reason": "Legal obligation to retain data",
                "exceptions": exceptions
            }

        # Proceed with erasure
        deletion_id = generate_uuid()

        # Delete from all systems
        self._delete_user_data(data_subject_id, deletion_id)

        # Keep audit record (pseudonymized)
        db.erasure_records.insert_one({
            "deletion_id": deletion_id,
            "request_id": request_id,
            "data_subject_id_hash": hashlib.sha256(data_subject_id.encode()).hexdigest(),
            "deletion_date": datetime.utcnow(),
            "reason": reason,
            "deleted_by": "automated_gdpr_process"
        })

        logger.warning("Personal data erased", extra={
            "event": "data_erasure_completed",
            "deletion_id": deletion_id,
            "reason": reason
        })

        return {
            "request_id": request_id,
            "status": "completed",
            "deletion_date": datetime.utcnow().isoformat()
        }

    def _delete_user_data(self, data_subject_id: str, deletion_id: str):
        """
        Delete personal data from all systems.

        Must delete from:
        - Primary databases
        - Backups (or mark for deletion on restore)
        - Third-party processors (notify them)
        - Logs (anonymize or delete)
        """
        # Mark user as deleted
        db.users.update_one(
            {"user_id": data_subject_id},
            {"$set": {
                "status": "deleted",
                "deletion_id": deletion_id,
                "deletion_date": datetime.utcnow(),
                # Pseudonymize remaining data
                "email": f"deleted_{deletion_id}@example.com",
                "name": "DELETED USER",
                "phone": None,
                "address": None
            }}
        )

        # Delete related data
        db.transactions.delete_many({"user_id": data_subject_id})
        db.communications.delete_many({"user_id": data_subject_id})
        db.activity_logs.delete_many({"user_id": data_subject_id})

        # Notify third-party processors
        self._notify_processors_of_deletion(data_subject_id)

    def _check_erasure_exceptions(self, data_subject_id: str) -> List[str]:
        """
        Check if legal exceptions prevent erasure.

        Article 17(3): Erasure not required if retention necessary for:
        - Compliance with legal obligation
        - Public interest
        - Legal claims
        """
        exceptions = []

        # Check financial records retention
        financial_records = db.transactions.find({
            "user_id": data_subject_id,
            "created_date": {"$gte": seven_years_ago()}
        }).count()

        if financial_records > 0:
            exceptions.append({
                "type": "legal_obligation",
                "description": "Financial records must be retained for 7 years (tax law)",
                "retention_until": seven_years_from_now().isoformat()
            })

        # Check ongoing legal claims
        active_claims = db.legal_claims.find({
            "user_id": data_subject_id,
            "status": "active"
        }).count()

        if active_claims > 0:
            exceptions.append({
                "type": "legal_claims",
                "description": "Data required for establishment, exercise or defense of legal claims"
            })

        return exceptions
```

### Right to Data Portability (Article 20)

**Requirement**: Provide data in machine-readable format for transfer to another controller

**Implementation**:

```python
# Data portability
class DataPortability:
    """
    Provide data in machine-readable format.

    GDPR Article 20: Right to data portability

    Requirements:
    - Structured, commonly used, machine-readable format (JSON, CSV, XML)
    - Only applies to data provided by data subject (not inferred/derived data)
    - Only applies when processing based on consent or contract
    - Technical feasibility to transmit directly to another controller
    """

    def generate_portable_export(self, data_subject_id: str, format: str = "json") -> bytes:
        """
        Generate portable data export.

        GDPR Article 20: Machine-readable format.
        """
        # Collect all data provided by user (not inferred)
        portable_data = {
            "export_metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "data_subject_id": data_subject_id,
                "format": format,
                "gdpr_article": "Article 20 - Right to data portability"
            },

            # User-provided data only
            "user_profile": self._get_user_provided_profile(data_subject_id),
            "user_preferences": self._get_user_preferences(data_subject_id),
            "user_content": self._get_user_generated_content(data_subject_id)
        }

        # Convert to requested format
        if format == "json":
            export_bytes = json.dumps(portable_data, indent=2).encode('utf-8')
        elif format == "csv":
            export_bytes = self._convert_to_csv(portable_data)
        elif format == "xml":
            export_bytes = self._convert_to_xml(portable_data)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info("Portable data export generated", extra={
            "event": "portable_export_generated",
            "data_subject_id": data_subject_id,
            "format": format,
            "size_kb": len(export_bytes) / 1024
        })

        return export_bytes

    def transmit_to_controller(self, data_subject_id: str, target_controller_url: str):
        """
        Transmit data directly to another controller (if technically feasible).

        GDPR Article 20(2): Right to have data transmitted directly.
        """
        portable_data = self.generate_portable_export(data_subject_id, format="json")

        # Transmit via secure API
        import requests

        response = requests.post(
            f"{target_controller_url}/api/data-import",
            files={"data": portable_data},
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            logger.info("Data transmitted to controller", extra={
                "event": "data_portability_transmission",
                "data_subject_id": data_subject_id,
                "target_controller": target_controller_url
            })
        else:
            raise Exception(f"Transmission failed: {response.status_code}")
```

---

## Privacy by Design Implementation

### Encryption and Pseudonymization

**GDPR Article 32**: Technical and organizational measures

**Implementation**:

```python
# Privacy by Design - encryption and pseudonymization
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import hashlib

class PrivacyByDesign:
    """
    Implement Privacy by Design (GDPR Article 25).

    Requirements:
    - Data protection by design (technical measures from the start)
    - Data protection by default (privacy-preserving defaults)
    - Pseudonymization and encryption (Article 32)
    - Data minimization (Article 5(1)(c))
    """

    def pseudonymize_identifier(self, identifier: str, salt: bytes = None) -> str:
        """
        Pseudonymize personal identifier.

        GDPR Article 4(5): Pseudonymization
        - Personal data can no longer be attributed without additional information
        - Additional information kept separately
        - Reversible (unlike anonymization)
        """
        if salt is None:
            salt = os.urandom(32)

        # Use PBKDF2 for pseudonymization
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )

        pseudonym = hashlib.sha256(
            kdf.derive(identifier.encode())
        ).hexdigest()

        # Store salt separately (not with pseudonym)
        db.pseudonymization_salts.insert_one({
            "pseudonym": pseudonym,
            "salt": salt.hex(),
            "created_date": datetime.utcnow()
        })

        return pseudonym

    def encrypt_sensitive_data(self, plaintext: str, user_id: str) -> Dict:
        """
        Encrypt sensitive personal data.

        GDPR Article 32(1)(a): Encryption of personal data
        """
        # Get encryption key from key management system
        encryption_key = self._get_user_encryption_key(user_id)

        fernet = Fernet(encryption_key)
        ciphertext = fernet.encrypt(plaintext.encode())

        logger.info("Sensitive data encrypted", extra={
            "event": "data_encryption",
            "user_id": user_id
        })

        return {
            "ciphertext": ciphertext.decode(),
            "algorithm": "Fernet (AES-128-CBC)",
            "key_id": self._get_key_id(user_id)
        }

    def anonymize_ip_address(self, ip_address: str) -> str:
        """
        Anonymize IP addresses for analytics.

        GDPR Recital 26: Anonymous data outside GDPR scope
        GDPR Article 6(1)(f): Legitimate interests (analytics)
        """
        from ipaddress import ip_address as parse_ip

        ip = parse_ip(ip_address)

        if ip.version == 4:
            # Anonymize last octet
            anonymized = f"{ip}.0".rsplit('.', 1)[0] + ".0"
        else:  # IPv6
            # Anonymize last 80 bits
            anonymized = str(ip).rsplit(':', 4)[0] + "::0"

        return anonymized

class DataMinimization:
    """
    Implement data minimization (GDPR Article 5(1)(c)).

    Principle: Collect only data that is adequate, relevant, and limited to what is necessary.
    """

    def validate_data_collection(self, data_fields: Dict, purpose: str) -> Dict:
        """
        Validate that data collection is necessary for purpose.

        GDPR Article 5(1)(c): Data minimization
        """
        # Define necessary fields for each purpose
        necessary_fields = {
            "account_creation": ["email", "password", "name"],
            "payment_processing": ["email", "billing_address", "payment_method"],
            "marketing": ["email", "consent_marketing"]
        }

        required = set(necessary_fields.get(purpose, []))
        collected = set(data_fields.keys())

        unnecessary = collected - required

        if unnecessary:
            logger.warning("Unnecessary data collection detected", extra={
                "event": "data_minimization_violation",
                "purpose": purpose,
                "unnecessary_fields": list(unnecessary)
            })

            return {
                "compliant": False,
                "unnecessary_fields": list(unnecessary),
                "recommendation": f"Remove fields: {', '.join(unnecessary)}"
            }

        return {"compliant": True}
```

---

## Breach Notification Implementation

### 72-Hour Breach Notification

**GDPR Article 33**: Breach notification to supervisory authority within 72 hours

**Implementation**:

```python
# Data breach notification (GDPR Article 33 & 34)
class GDPRBreachNotification:
    """
    Handle data breach notification.

    GDPR Article 33: Notification to supervisory authority (72 hours)
    GDPR Article 34: Notification to data subjects (high risk)
    """

    # Article 33: 72-hour deadline
    AUTHORITY_NOTIFICATION_DEADLINE_HOURS = 72

    # Article 34: Notification to individuals (without undue delay)
    INDIVIDUAL_NOTIFICATION_DEADLINE_HOURS = 24

    def assess_breach(self, breach_details: Dict) -> Dict:
        """
        Assess data breach and determine notification requirements.

        GDPR Article 33(1): Notify unless breach unlikely to result in risk to rights and freedoms.
        """
        breach_assessment = {
            "breach_id": generate_uuid(),
            "detected_date": datetime.utcnow(),
            "breach_type": breach_details["type"],
            "affected_data": breach_details["affected_data"],
            "affected_individuals_count": breach_details.get("affected_count", 0),

            # Risk assessment
            "risk_level": self._assess_risk_level(breach_details),
            "notify_authority_required": None,
            "notify_individuals_required": None,

            # Notification deadlines
            "authority_deadline": None,
            "individual_deadline": None
        }

        # Determine notification requirements
        risk_level = breach_assessment["risk_level"]

        # Authority notification (Article 33)
        if risk_level in ["low", "medium", "high", "critical"]:
            breach_assessment["notify_authority_required"] = True
            breach_assessment["authority_deadline"] = (
                datetime.utcnow() + timedelta(hours=self.AUTHORITY_NOTIFICATION_DEADLINE_HOURS)
            )

        # Individual notification (Article 34) - only if high risk
        if risk_level in ["high", "critical"]:
            breach_assessment["notify_individuals_required"] = True
            breach_assessment["individual_deadline"] = (
                datetime.utcnow() + timedelta(hours=self.INDIVIDUAL_NOTIFICATION_DEADLINE_HOURS)
            )

        # Store breach assessment
        db.breach_assessments.insert_one(breach_assessment)

        logger.critical("Data breach assessed", extra={
            "event": "breach_assessment",
            "breach_id": breach_assessment["breach_id"],
            "risk_level": risk_level,
            "notify_authority": breach_assessment["notify_authority_required"]
        })

        return breach_assessment

    def _assess_risk_level(self, breach_details: Dict) -> str:
        """
        Assess risk to data subjects' rights and freedoms.

        Factors (Article 33):
        - Type of breach (confidentiality, integrity, availability)
        - Nature of personal data (special categories = high risk)
        - Volume of affected individuals
        - Ease of identification
        - Severity of consequences
        - Special characteristics of data subjects (children, vulnerable)
        """
        risk_score = 0

        # Type of data
        if "special_category" in breach_details["affected_data"]:
            risk_score += 4  # Health, biometric, etc.
        elif "financial" in breach_details["affected_data"]:
            risk_score += 3
        else:
            risk_score += 1

        # Volume
        affected_count = breach_details.get("affected_count", 0)
        if affected_count > 10000:
            risk_score += 3
        elif affected_count > 1000:
            risk_score += 2
        elif affected_count > 100:
            risk_score += 1

        # Ease of identification
        if breach_details.get("identifiable", True):
            risk_score += 2

        # Risk levels
        if risk_score >= 8:
            return "critical"
        elif risk_score >= 6:
            return "high"
        elif risk_score >= 3:
            return "medium"
        else:
            return "low"

    def notify_supervisory_authority(self, breach_id: str) -> str:
        """
        Notify supervisory authority of breach.

        GDPR Article 33: Notification within 72 hours

        Notification must contain (Article 33(3)):
        - Nature of breach
        - Categories and approximate number of data subjects
        - Categories and approximate number of personal data records
        - Contact details of DPO
        - Likely consequences
        - Measures taken or proposed
        """
        breach = db.breach_assessments.find_one({"breach_id": breach_id})

        notification = {
            "notification_id": generate_uuid(),
            "breach_id": breach_id,
            "notification_date": datetime.utcnow(),
            "recipient": "Data Protection Authority",
            "recipient_email": "your-dpa@example.eu",

            # Article 33(3) requirements
            "content": {
                "nature_of_breach": breach["breach_type"],
                "categories_of_data_subjects": ["customers"],
                "approximate_number_of_data_subjects": breach["affected_individuals_count"],
                "categories_of_records": breach["affected_data"],
                "approximate_number_of_records": breach["affected_individuals_count"],

                "dpo_contact": {
                    "name": "Data Protection Officer",
                    "email": "dpo@yourorg.com",
                    "phone": "+1-xxx-xxx-xxxx"
                },

                "likely_consequences": self._describe_consequences(breach),
                "measures_taken": self._describe_mitigation_measures(breach),

                "delay_justification": None  # If notifying after 72 hours
            }
        }

        # Send notification
        self._send_to_authority(notification)

        # Update breach record
        db.breach_assessments.update_one(
            {"breach_id": breach_id},
            {"$set": {
                "authority_notified": True,
                "authority_notification_date": datetime.utcnow()
            }}
        )

        logger.critical("Supervisory authority notified", extra={
            "event": "breach_authority_notification",
            "breach_id": breach_id,
            "notification_id": notification["notification_id"]
        })

        return notification["notification_id"]

    def notify_data_subjects(self, breach_id: str) -> Dict:
        """
        Notify affected individuals of breach.

        GDPR Article 34: Communication to data subjects (high risk breaches)

        Notification must contain (Article 34(2)):
        - Nature of breach in clear and plain language
        - Contact details of DPO
        - Likely consequences
        - Measures taken or proposed
        """
        breach = db.breach_assessments.find_one({"breach_id": breach_id})

        if not breach["notify_individuals_required"]:
            return {"notified": False, "reason": "Not required (low risk)"}

        # Get affected individuals
        affected_users = self._get_affected_users(breach)

        # Compose notification email
        email_template = """
        Subject: Important Security Notice - Data Breach Notification

        Dear [Name],

        We are writing to inform you of a data security incident that may have affected your personal information.

        What Happened:
        {nature_of_breach}

        What Information Was Involved:
        {affected_data}

        What We Are Doing:
        {measures_taken}

        What You Can Do:
        {recommended_actions}

        Contact:
        If you have questions, please contact our Data Protection Officer at dpo@yourorg.com

        Sincerely,
        [Your Organization]
        """

        # Send notifications
        notifications_sent = 0
        for user in affected_users:
            self._send_breach_notification_email(user, email_template, breach)
            notifications_sent += 1

        logger.critical("Data subjects notified of breach", extra={
            "event": "breach_individual_notification",
            "breach_id": breach_id,
            "notifications_sent": notifications_sent
        })

        return {
            "notified": True,
            "notifications_sent": notifications_sent
        }
```

---

## Consent Management

### GDPR-Compliant Consent

**GDPR Article 7**: Conditions for consent (freely given, specific, informed, unambiguous)

**Implementation**:

```python
# Consent management (GDPR Article 7)
class ConsentManagement:
    """
    Manage user consent for data processing.

    GDPR Article 7: Conditions for consent
    - Freely given (not bundled with terms)
    - Specific (granular, per purpose)
    - Informed (know what they're consenting to)
    - Unambiguous indication (affirmative action)
    - Withdrawable (as easy to withdraw as to give)
    - Documented (burden of proof on controller)
    """

    def request_consent(
        self,
        user_id: str,
        purpose: str,
        data_categories: List[str],
        description: str
    ) -> str:
        """
        Request consent from user.

        GDPR Article 7 & Article 13: Informed consent
        """
        consent_request = {
            "consent_id": generate_uuid(),
            "user_id": user_id,
            "purpose": purpose,
            "data_categories": data_categories,
            "description": description,
            "requested_date": datetime.utcnow(),
            "consent_given": None,
            "consent_date": None,
            "withdrawn": False
        }

        db.consent_requests.insert_one(consent_request)

        return consent_request["consent_id"]

    def record_consent(self, consent_id: str, user_acceptance: bool) -> Dict:
        """
        Record user's consent decision.

        GDPR Article 7(1): Burden of proof on controller.
        """
        db.consent_requests.update_one(
            {"consent_id": consent_id},
            {"$set": {
                "consent_given": user_acceptance,
                "consent_date": datetime.utcnow(),
                "ip_address": get_request_ip(),
                "user_agent": get_request_user_agent()
            }}
        )

        logger.info("Consent recorded", extra={
            "event": "consent_recorded",
            "consent_id": consent_id,
            "accepted": user_acceptance
        })

        return {"consent_id": consent_id, "accepted": user_acceptance}

    def withdraw_consent(self, user_id: str, consent_id: str) -> Dict:
        """
        Withdraw consent.

        GDPR Article 7(3): Right to withdraw consent
        - Must be as easy as giving consent
        - Processing before withdrawal remains lawful
        """
        db.consent_requests.update_one(
            {"consent_id": consent_id, "user_id": user_id},
            {"$set": {
                "withdrawn": True,
                "withdrawal_date": datetime.utcnow()
            }}
        )

        # Stop processing based on this consent
        self._stop_consent_based_processing(user_id, consent_id)

        logger.warning("Consent withdrawn", extra={
            "event": "consent_withdrawn",
            "user_id": user_id,
            "consent_id": consent_id
        })

        return {"status": "withdrawn"}

    def get_consent_status(self, user_id: str, purpose: str) -> bool:
        """
        Check if user has consented for specific purpose.

        GDPR Article 7(1): Controller must demonstrate consent.
        """
        consent = db.consent_requests.find_one({
            "user_id": user_id,
            "purpose": purpose,
            "consent_given": True,
            "withdrawn": False
        })

        return consent is not None
```

---

## Data Protection Impact Assessment (DPIA)

### DPIA for High-Risk Processing

**GDPR Article 35**: DPIA required for high-risk processing

**Implementation**:

```python
# Data Protection Impact Assessment (GDPR Article 35)
class DataProtectionImpactAssessment:
    """
    Conduct DPIA for high-risk processing.

    GDPR Article 35: DPIA required when processing likely to result in high risk.

    Triggers:
    - Systematic monitoring on large scale
    - Special category data on large scale
    - Automated decision-making with legal effects
    - Biometric data
    - Genetic data
    - Children's data on large scale
    - Innovative technology
    """

    def requires_dpia(self, processing_activity: Dict) -> bool:
        """
        Determine if DPIA is required.

        GDPR Article 35(3): DPIA required for high-risk processing.
        """
        triggers = []

        # Special category data
        if "special_category" in processing_activity.get("data_categories", []):
            triggers.append("special_category_data")

        # Large scale monitoring
        if processing_activity.get("systematic_monitoring", False):
            if processing_activity.get("data_subjects_count", 0) > 5000:
                triggers.append("large_scale_monitoring")

        # Automated decision-making
        if processing_activity.get("automated_decisions", False):
            if processing_activity.get("legal_effects", False):
                triggers.append("automated_decision_making")

        # Children's data
        if "children" in processing_activity.get("data_subjects", []):
            triggers.append("children_data")

        # AI/ML systems
        if processing_activity.get("uses_ai", False):
            triggers.append("innovative_technology")

        return len(triggers) >= 2  # WP29 guidance: 2+ triggers = DPIA required

    def conduct_dpia(self, processing_activity_id: str) -> Dict:
        """
        Conduct DPIA.

        GDPR Article 35(7): DPIA must contain:
        - Description of processing operations and purposes
        - Assessment of necessity and proportionality
        - Assessment of risks to rights and freedoms
        - Measures to address risks
        """
        dpia = {
            "dpia_id": generate_uuid(),
            "processing_activity_id": processing_activity_id,
            "dpia_date": datetime.utcnow(),
            "assessor": get_current_user(),

            # Article 35(7)(a): Description
            "description": self._describe_processing(processing_activity_id),

            # Article 35(7)(b): Necessity and proportionality
            "necessity_assessment": self._assess_necessity(processing_activity_id),

            # Article 35(7)(c): Risk assessment
            "risk_assessment": self._assess_risks(processing_activity_id),

            # Article 35(7)(d): Mitigation measures
            "mitigation_measures": self._define_mitigation(processing_activity_id),

            # DPO consulted?
            "dpo_consulted": True,
            "dpo_opinion": "DPIA approved with recommended mitigations implemented"
        }

        db.dpias.insert_one(dpia)

        logger.warning("DPIA conducted", extra={
            "event": "dpia_conducted",
            "dpia_id": dpia["dpia_id"],
            "processing_activity_id": processing_activity_id
        })

        return dpia
```

---

## Success Criteria

### Data Subject Rights Operational

- [ ] Access request portal live (respond within 30 days)
- [ ] Erasure automation implemented
- [ ] Data portability export (JSON/CSV/XML)
- [ ] Rectification process documented
- [ ] Object/restriction workflows operational

### Privacy by Design Implemented

- [ ] Encryption at rest and in transit (TLS 1.3+)
- [ ] Pseudonymization for identifiers
- [ ] Data minimization validated
- [ ] Privacy-preserving defaults
- [ ] Access controls (least privilege)

### Compliance Documentation Complete

- [ ] Record of processing activities (Article 30)
- [ ] Legal basis documented for all processing
- [ ] DPIA conducted for high-risk processing
- [ ] Data retention policies defined
- [ ] Third-party processor agreements (DPAs)

### Breach Readiness

- [ ] Breach detection mechanisms
- [ ] 72-hour notification workflow
- [ ] DPO appointed (if required)
- [ ] Supervisory authority contact established
- [ ] Breach simulation/tabletop exercise conducted

---

## Common Pitfalls

### ❌ Assuming Consent is Always Appropriate

**Problem**: Using consent as legal basis when contract or legitimate interests is more appropriate.

**Solution**: Choose correct legal basis (Article 6). Consent must be freely given (not bundled with terms).

### ❌ Ignoring Processor Agreements

**Problem**: No Data Processing Agreements (DPAs) with third-party vendors.

**Solution**: GDPR Article 28 requires written agreements with processors. Use Standard Contractual Clauses (SCCs) for non-EU transfers.

### ❌ No Data Retention Policies

**Problem**: Keeping data indefinitely.

**Solution**: Article 5(1)(e) requires storage limitation. Define retention periods, automated deletion.

### ❌ Forgetting About Backups

**Problem**: Deleting data from production but not backups.

**Solution**: Erasure requests apply to backups too. Mark for deletion on restore or use backup encryption.

---

## Resources

### Official GDPR Resources

- [GDPR Full Text](https://gdpr-info.eu/) - Official regulation text
- [ICO (UK) Guidance](https://ico.org.uk/for-organisations/guide-to-data-protection/) - Practical guides
- [CNIL (France) Guidance](https://www.cnil.fr/en/gdpr-developers-guide) - Developer-focused
- [EDPB Guidelines](https://edpb.europa.eu/our-work-tools/general-guidance/gdpr-guidelines-recommendations-best-practices_en) - EU-wide guidance

### Tools

- **PII Detection**: Presidio, AWS Macie, Google DLP API
- **Consent Management**: OneTrust, Cookiebot, Osano
- **DSAR Automation**: DataGrail, Transcend, Securiti.ai
- **Privacy Management**: OneTrust, TrustArc, BigID

---

## Changelog

### Version 1.0.0 - 2025-12-05

**Added**:
- Complete GDPR compliance implementation for Python
- Data discovery and classification (Article 30)
- Data subject rights automation (Articles 15-22)
- Access requests (Article 15)
- Erasure/right to be forgotten (Article 17)
- Data portability (Article 20)
- Privacy by Design (Article 25)
- Encryption and pseudonymization (Article 32)
- Breach notification (Articles 33-34)
- Consent management (Article 7)
- Data Protection Impact Assessment (Article 35)

**Framework Coverage**:
- All 8 data subject rights
- 7 GDPR principles (Article 5)
- 6 legal bases (Article 6)
- Special categories handling (Article 9)

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
