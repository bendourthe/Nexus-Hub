---
template_id: compliance_governance_ccpa_python
template_name: CCPA Compliance - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - privacy_protection/python_gdpr_compliance.md
  - governance_policies/python_security_policies.md
related_templates:
  - compliance_frameworks/python_soc2_compliance.md
tools:
  - presidio (PII detection)
tags:
  - ccpa
  - privacy
  - california-consumer-privacy-act
  - data-protection
  - python
---

# CCPA Compliance - Python

**California Consumer Privacy Act (CCPA) compliance for data privacy**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### What is CCPA?

The **California Consumer Privacy Act (CCPA)** is California's comprehensive privacy law effective January 1, 2020. Updated by the California Privacy Rights Act (CPRA) effective January 1, 2023.

**Key Facts**:
- **Scope**: Applies to businesses serving California residents
- **Threshold**: $25M+ revenue, 100K+ consumers, or 50%+ revenue from selling personal info
- **Penalties**: Up to $7,500 per intentional violation
- **Rights**: Similar to GDPR but with key differences

### CCPA vs GDPR

| Aspect | CCPA | GDPR |
|--------|------|------|
| **Scope** | California residents | EU residents (global) |
| **Opt-in/out** | Opt-out of sale | Opt-in for processing |
| **Right to deletion** | Yes | Yes |
| **Right to portability** | Yes | Yes |
| **Breach notification** | No specific timeline | 72 hours |
| **Penalties** | $2.5K-$7.5K per violation | Up to 4% revenue |

### Consumer Rights under CCPA

1. **Right to Know** - What personal information is collected
2. **Right to Delete** - Request deletion of personal information
3. **Right to Opt-Out** - Opt-out of sale of personal information
4. **Right to Non-Discrimination** - No discrimination for exercising rights
5. **Right to Correct** (CPRA 2023) - Correct inaccurate information
6. **Right to Limit** (CPRA 2023) - Limit use of sensitive personal information

---

## CCPA Categories of Personal Information

**CCPA defines 11 categories**:

1. Identifiers (name, email, IP address)
2. Personal information (CA Customer Records statute)
3. Protected classifications (race, religion, gender)
4. Commercial information (purchase history)
5. Biometric information
6. Internet/network activity (browsing history)
7. Geolocation data
8. Sensory information (audio, video)
9. Professional/employment information
10. Education information
11. Inferences (profiles, preferences)

**CPRA adds "Sensitive Personal Information"**:
- SSN, driver's license, passport
- Financial account credentials
- Precise geolocation
- Race, ethnicity, religion
- Health data
- Sex life, sexual orientation
- Contents of mail/email/text (unless business is recipient)

---

## Implementation Roadmap

### Phase 1: Data Inventory (Week 1)

**Deliverables**:
1. Personal information categories collected
2. Sources of personal information
3. Business purposes for collection
4. Third parties receiving data
5. Data retention periods

### Phase 2: Consumer Rights (Week 2-3)

**Deliverables**:
1. "Do Not Sell My Personal Information" mechanism
2. Right to know request handling
3. Right to delete request handling
4. Right to correct implementation (CPRA)

### Phase 3: Disclosures and Notices (Week 4)

**Deliverables**:
1. Privacy policy updates
2. Notice at collection
3. Financial incentive disclosures
4. Service provider agreements

---

## CCPA Rights Implementation

### Right to Know

**CCPA §1798.100**: Disclose categories and specific pieces of PI

**Implementation** (reuses GDPR code):

```python
# Right to know (similar to GDPR right of access)
from datetime import datetime, timedelta
from typing import Dict, List

class CCPARightToKnow:
    """
    Handle CCPA "Right to Know" requests.

    CCPA §1798.100: Right to know what PI is collected
    Response deadline: 45 days (extendable to 90 days)
    """

    RESPONSE_DEADLINE_DAYS = 45

    def process_right_to_know_request(self, consumer_id: str) -> Dict:
        """
        Process consumer's right to know request.

        Must disclose:
        - Categories of PI collected
        - Categories of sources
        - Business purposes
        - Categories of third parties
        - Specific pieces of PI
        """
        request_id = generate_uuid()
        deadline = datetime.utcnow() + timedelta(days=self.RESPONSE_DEADLINE_DAYS)

        # Create request
        db.ccpa_requests.insert_one({
            "request_id": request_id,
            "consumer_id": consumer_id,
            "request_type": "right_to_know",
            "status": "pending",
            "created_date": datetime.utcnow(),
            "deadline": deadline
        })

        # Generate response
        response = {
            "request_id": request_id,
            "consumer_id": consumer_id,

            # Categories of PI collected (12 months)
            "categories_collected": self._get_categories_collected(consumer_id),

            # Categories of PI sold/shared
            "categories_sold": self._get_categories_sold(consumer_id),

            # Categories of PI disclosed
            "categories_disclosed": self._get_categories_disclosed(consumer_id),

            # Business purposes
            "business_purposes": self._get_business_purposes(),

            # Specific pieces of PI
            "personal_information": self._get_specific_pi(consumer_id)
        }

        logger.info("Right to know request processed", extra={
            "request_id": request_id,
            "consumer_id": consumer_id
        })

        return response

    def _get_categories_collected(self, consumer_id: str) -> List[str]:
        """
        Get categories of PI collected (past 12 months).

        CCPA categories (1-11).
        """
        consumer = db.consumers.find_one({"consumer_id": consumer_id})

        categories = []

        if consumer.get("name") or consumer.get("email"):
            categories.append("Identifiers")

        if consumer.get("purchase_history"):
            categories.append("Commercial information")

        if consumer.get("browsing_history"):
            categories.append("Internet or network activity")

        if consumer.get("geolocation"):
            categories.append("Geolocation data")

        return categories

    def _get_business_purposes(self) -> List[str]:
        """
        Disclose business purposes for PI collection.

        CCPA requires clear disclosure of why data is collected.
        """
        return [
            "Fulfilling orders and providing services",
            "Customer support and communication",
            "Marketing and advertising (with opt-out option)",
            "Security and fraud prevention",
            "Analytics and service improvement",
            "Legal compliance"
        ]
```

### Right to Delete

**CCPA §1798.105**: Delete personal information

**Implementation**:

```python
# Right to delete
class CCPARightToDelete:
    """
    Handle CCPA deletion requests.

    CCPA §1798.105: Right to deletion
    Response deadline: 45 days
    """

    # Exceptions to deletion (CCPA §1798.105(d))
    DELETION_EXCEPTIONS = [
        "complete_transaction",
        "detect_security_incidents",
        "debug_errors",
        "free_speech",
        "comply_with_california_electronic_communications_privacy_act",
        "research",
        "internal_use",
        "comply_with_legal_obligation"
    ]

    def process_deletion_request(self, consumer_id: str) -> Dict:
        """
        Process consumer's right to deletion request.

        Must delete PI unless exception applies.
        """
        request_id = generate_uuid()

        # Check if exceptions apply
        exceptions = self._check_deletion_exceptions(consumer_id)

        if exceptions:
            logger.warning("Deletion request has exceptions", extra={
                "consumer_id": consumer_id,
                "exceptions": exceptions
            })

            return {
                "request_id": request_id,
                "status": "partial_deletion",
                "exceptions": exceptions
            }

        # Delete personal information
        deletion_id = generate_uuid()
        self._delete_consumer_data(consumer_id, deletion_id)

        # Notify service providers to delete
        self._notify_service_providers_to_delete(consumer_id)

        logger.warning("Deletion request processed", extra={
            "request_id": request_id,
            "consumer_id": consumer_id,
            "deletion_id": deletion_id
        })

        return {
            "request_id": request_id,
            "status": "completed",
            "deletion_date": datetime.utcnow().isoformat()
        }

    def _check_deletion_exceptions(self, consumer_id: str) -> List[str]:
        """
        Check if CCPA deletion exceptions apply.

        CCPA §1798.105(d): Business need not comply if necessary for...
        """
        exceptions = []

        # Check ongoing transactions
        active_transactions = db.transactions.find({
            "consumer_id": consumer_id,
            "status": "pending"
        }).count()

        if active_transactions > 0:
            exceptions.append({
                "exception": "complete_transaction",
                "description": "Deletion delayed until transaction completion"
            })

        # Check legal hold
        legal_holds = db.legal_holds.find({
            "consumer_id": consumer_id,
            "status": "active"
        }).count()

        if legal_holds > 0:
            exceptions.append({
                "exception": "comply_with_legal_obligation",
                "description": "Data subject to legal hold"
            })

        return exceptions
```

### Right to Opt-Out of Sale

**CCPA §1798.120**: Opt-out of sale of PI

**Implementation**:

```python
# Right to opt-out of sale
class CCPAOptOut:
    """
    Handle opt-out of sale requests.

    CCPA §1798.120: Right to opt-out of sale
    Must provide "Do Not Sell My Personal Information" link
    """

    def process_opt_out(self, consumer_id: str) -> Dict:
        """
        Process opt-out of sale request.

        CCPA: Must honor immediately, no verification required.
        """
        # Set opt-out flag
        db.consumers.update_one(
            {"consumer_id": consumer_id},
            {"$set": {
                "ccpa_opt_out_sale": True,
                "opt_out_date": datetime.utcnow()
            }}
        )

        # Notify third parties to stop selling
        self._notify_third_parties_opt_out(consumer_id)

        logger.warning("Consumer opted out of sale", extra={
            "event": "ccpa_opt_out",
            "consumer_id": consumer_id
        })

        return {
            "status": "opted_out",
            "message": "You have successfully opted out of the sale of your personal information"
        }

    def check_opt_out_status(self, consumer_id: str) -> bool:
        """
        Check if consumer has opted out.

        Must respect opt-out across all data collection points.
        """
        consumer = db.consumers.find_one({"consumer_id": consumer_id})
        return consumer.get("ccpa_opt_out_sale", False)

    def process_opt_in(self, consumer_id: str, affirmative_consent: bool) -> Dict:
        """
        Process opt-in to sale (after opt-out).

        CCPA: Requires affirmative action from consumer.
        """
        if not affirmative_consent:
            raise ValueError("Opt-in requires affirmative consent")

        db.consumers.update_one(
            {"consumer_id": consumer_id},
            {"$set": {
                "ccpa_opt_out_sale": False,
                "opt_in_date": datetime.utcnow()
            }}
        )

        logger.info("Consumer opted in to sale", extra={
            "event": "ccpa_opt_in",
            "consumer_id": consumer_id
        })

        return {"status": "opted_in"}
```

### Right to Correct (CPRA 2023)

**CPRA §1798.106**: Correct inaccurate PI

**Implementation**:

```python
# Right to correct (CPRA 2023)
class CPRARightToCorrect:
    """
    Handle right to correction requests (CPRA 2023).

    CPRA §1798.106: Right to correct inaccurate PI
    New right as of January 1, 2023
    """

    def process_correction_request(
        self,
        consumer_id: str,
        field_to_correct: str,
        current_value: str,
        corrected_value: str
    ) -> Dict:
        """
        Process consumer's right to correction.

        Must correct inaccurate PI, taking into account nature and purposes.
        """
        request_id = generate_uuid()

        # Validate correction request
        if not self._is_correction_valid(field_to_correct, corrected_value):
            return {
                "request_id": request_id,
                "status": "rejected",
                "reason": "Correction not valid or verifiable"
            }

        # Make correction
        db.consumers.update_one(
            {"consumer_id": consumer_id},
            {"$set": {field_to_correct: corrected_value}}
        )

        # Log correction
        db.correction_log.insert_one({
            "request_id": request_id,
            "consumer_id": consumer_id,
            "field": field_to_correct,
            "old_value": current_value,
            "new_value": corrected_value,
            "corrected_date": datetime.utcnow()
        })

        logger.info("Correction request processed", extra={
            "request_id": request_id,
            "consumer_id": consumer_id,
            "field": field_to_correct
        })

        return {
            "request_id": request_id,
            "status": "completed"
        }
```

---

## CCPA Disclosure Requirements

### Privacy Policy

**CCPA §1798.130**: Privacy policy must include...

```python
# Privacy policy disclosures
class CCPAPrivacyPolicy:
    """
    Generate CCPA-compliant privacy policy disclosures.

    CCPA §1798.130: Required disclosures
    """

    def generate_privacy_policy_disclosure(self) -> Dict:
        """
        Generate CCPA privacy policy disclosure.

        Must update at least once every 12 months.
        """
        disclosure = {
            # Categories of PI collected
            "categories_collected": [
                "Identifiers (name, email, IP address)",
                "Commercial information (purchase history)",
                "Internet activity (browsing history)",
                "Geolocation data"
            ],

            # Business purposes
            "business_purposes": [
                "Providing services",
                "Customer support",
                "Marketing (opt-out available)",
                "Security and fraud prevention"
            ],

            # Categories sold/shared
            "categories_sold": [
                "Internet activity (to advertising partners)"
            ],

            # Consumer rights
            "consumer_rights": {
                "right_to_know": "You have the right to know what personal information we collect",
                "right_to_delete": "You have the right to request deletion of your personal information",
                "right_to_opt_out": "You have the right to opt-out of sale of your personal information",
                "right_to_non_discrimination": "We will not discriminate against you for exercising your rights",
                "right_to_correct": "You have the right to correct inaccurate personal information (effective 2023)"
            },

            # How to exercise rights
            "exercise_rights": {
                "methods": ["Toll-free number: 1-800-XXX-XXXX", "Web form: www.example.com/ccpa"],
                "verification": "We will verify your identity before processing requests",
                "authorized_agents": "You may designate an authorized agent to make requests on your behalf"
            }
        }

        return disclosure

    def generate_do_not_sell_link(self) -> str:
        """
        Generate "Do Not Sell My Personal Information" link.

        CCPA §1798.135: Required link on homepage
        """
        return '<a href="/ccpa/do-not-sell">Do Not Sell My Personal Information</a>'
```

---

## Success Criteria

### Consumer Rights Implemented

- [ ] Right to know request handling (45-day response)
- [ ] Right to delete request handling
- [ ] Right to opt-out of sale mechanism
- [ ] Right to correct (CPRA) implemented
- [ ] Right to non-discrimination enforced

### Disclosures Complete

- [ ] Privacy policy updated with CCPA disclosures
- [ ] "Do Not Sell" link on homepage
- [ ] Notice at collection provided
- [ ] Categories of PI disclosed
- [ ] Business purposes disclosed

### Compliance Documentation

- [ ] Data inventory completed
- [ ] Service provider agreements reviewed
- [ ] Consumer request logs maintained
- [ ] Opt-out mechanism documented

---

## Common Pitfalls

### ❌ Ignoring "Sale" Definition

**Problem**: Not realizing data sharing with advertisers counts as "sale".

**Solution**: CCPA defines "sale" broadly. Provide opt-out for all sharing that benefits business.

### ❌ No Verification Process

**Problem**: Deleting data without verifying requestor identity.

**Solution**: Implement verification (matching 2-3 data points).

### ❌ Assuming GDPR Compliance = CCPA Compliance

**Problem**: GDPR and CCPA have differences (opt-in vs opt-out).

**Solution**: Implement both separately, don't assume equivalence.

---

## Resources

### Official CCPA/CPRA Resources

- [California Attorney General - CCPA](https://oag.ca.gov/privacy/ccpa)
- [CPRA Full Text](https://leginfo.legislature.ca.gov/)
- [CCPA Regulations](https://www.oag.ca.gov/privacy/ccpa/regs)

### Tools

- **OneTrust** - Privacy management platform
- **TrustArc** - CCPA compliance automation
- **BigID** - Data discovery for CCPA

---

## Changelog

### Version 1.0.0 - 2025-12-05

**Added**:
- Complete CCPA compliance implementation
- Right to know (§1798.100)
- Right to delete (§1798.105)
- Right to opt-out of sale (§1798.120)
- Right to correct (CPRA §1798.106)
- Privacy policy disclosures
- Do Not Sell mechanism

**Framework Coverage**:
- CCPA (effective 2020)
- CPRA amendments (effective 2023)

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
