---
template_id: compliance_governance_gdpr_java
template_name: GDPR Compliance - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - compliance_frameworks/java_soc2_compliance.md
  - governance_policies/java_security_policies.md
related_templates:
  - privacy_protection/java_ccpa_compliance.md
  - compliance_frameworks/java_iso27001_implementation.md
tools:
  - Spring Boot
  - Hibernate
  - Apache Tika (PII detection)
tags:
  - gdpr
  - privacy
  - data-protection
  - eu-compliance
  - data-subject-rights
  - java
---

# GDPR Compliance - Java

**Implement EU General Data Protection Regulation (GDPR) compliance for data privacy**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

The **General Data Protection Regulation (GDPR)** is the EU's comprehensive data protection law.

**Key Facts**:
- **Territorial Scope**: Applies to any organization processing EU residents' data
- **Penalties**: Up to €20 million or 4% of global annual revenue
- **Data Subject Rights**: 8 fundamental rights for individuals
- **Breach Notification**: 72-hour mandatory reporting

**GDPR Principles (Article 5)**:
1. Lawfulness, Fairness, Transparency
2. Purpose Limitation
3. Data Minimization
4. Accuracy
5. Storage Limitation
6. Integrity and Confidentiality
7. Accountability

---

## Data Subject Rights Implementation

```java
package com.organization.gdpr;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Service
public class DataSubjectRightsService {

    private static final Logger logger = LoggerFactory.getLogger(DataSubjectRightsService.class);
    private static final int RESPONSE_DEADLINE_DAYS = 30;

    public enum RequestType {
        ACCESS,           // Article 15
        RECTIFICATION,    // Article 16
        ERASURE,          // Article 17
        RESTRICTION,      // Article 18
        PORTABILITY,      // Article 20
        OBJECTION         // Article 21
    }

    public enum RequestStatus {
        PENDING,
        IN_PROGRESS,
        COMPLETED,
        REJECTED
    }

    public static class DataSubjectRequest {
        private String requestId;
        private String dataSubjectId;
        private String email;
        private RequestType requestType;
        private RequestStatus status;
        private Instant submittedAt;
        private Instant deadline;
        private Instant completedAt;
        private String rejectionReason;

        // Getters and setters
        public String getRequestId() { return requestId; }
        public void setRequestId(String requestId) { this.requestId = requestId; }

        public RequestType getRequestType() { return requestType; }
        public void setRequestType(RequestType requestType) { this.requestType = requestType; }

        public RequestStatus getStatus() { return status; }
        public void setStatus(RequestStatus status) { this.status = status; }

        public Instant getDeadline() { return deadline; }
        public void setDeadline(Instant deadline) { this.deadline = deadline; }
    }

    public String submitAccessRequest(String dataSubjectId, String email) {
        // Article 15: Right of Access
        String requestId = UUID.randomUUID().toString();

        DataSubjectRequest request = new DataSubjectRequest();
        request.setRequestId(requestId);
        // request.setDataSubjectId(dataSubjectId);
        // request.setEmail(email);
        request.setRequestType(RequestType.ACCESS);
        request.setStatus(RequestStatus.PENDING);
        // request.setSubmittedAt(Instant.now());
        request.setDeadline(Instant.now().plus(RESPONSE_DEADLINE_DAYS, ChronoUnit.DAYS));

        // Save request
        // requestRepository.save(request);

        // Verify identity (2-factor authentication required)
        sendVerificationEmail(email, requestId);

        logger.info("Access request submitted: request_id={}, email={}, deadline={}",
                requestId, email, request.getDeadline());

        return requestId;
    }

    public Map<String, Object> processAccessRequest(String requestId) {
        // Article 15: Provide copy of personal data

        // DataSubjectRequest request = requestRepository.findById(requestId).orElseThrow();

        // Simulated request
        DataSubjectRequest request = new DataSubjectRequest();
        request.setRequestId(requestId);
        request.setRequestType(RequestType.ACCESS);
        request.setStatus(RequestStatus.PENDING);

        if (request.getRequestType() != RequestType.ACCESS) {
            throw new IllegalStateException("Invalid request type");
        }

        // Gather all personal data
        Map<String, Object> personalData = new HashMap<>();
        personalData.put("profile", getUserProfile(requestId));
        personalData.put("transactions", getUserTransactions(requestId));
        personalData.put("communications", getUserCommunications(requestId));
        personalData.put("consent_records", getUserConsents(requestId));

        // Article 15(1) information
        Map<String, Object> response = new HashMap<>();
        response.put("request_id", requestId);
        response.put("personal_data", personalData);
        response.put("purposes_of_processing", Arrays.asList(
            "Service delivery",
            "Customer support",
            "Marketing (with consent)"
        ));
        response.put("categories_of_data", Arrays.asList(
            "Identity data",
            "Contact data",
            "Transaction data",
            "Technical data"
        ));
        response.put("recipients", Arrays.asList(
            "Payment processors",
            "Email service providers",
            "Analytics providers"
        ));
        response.put("retention_period", "7 years (legal requirement)");
        response.put("right_to_lodge_complaint", "Contact your local Data Protection Authority");

        // Update request status
        request.setStatus(RequestStatus.COMPLETED);
        // request.setCompletedAt(Instant.now());

        // requestRepository.save(request);

        logger.info("Access request completed: request_id={}", requestId);

        return response;
    }

    public String submitErasureRequest(String dataSubjectId, String email, String reason) {
        // Article 17: Right to Erasure ("Right to be Forgotten")
        String requestId = UUID.randomUUID().toString();

        DataSubjectRequest request = new DataSubjectRequest();
        request.setRequestId(requestId);
        request.setRequestType(RequestType.ERASURE);
        request.setStatus(RequestStatus.PENDING);
        request.setDeadline(Instant.now().plus(RESPONSE_DEADLINE_DAYS, ChronoUnit.DAYS));

        // Save request
        // requestRepository.save(request);

        logger.info("Erasure request submitted: request_id={}, email={}, reason={}",
                requestId, email, reason);

        return requestId;
    }

    public Map<String, Object> processErasureRequest(String requestId) {
        // Article 17: Right to Erasure

        // Check exceptions (Article 17(3))
        List<String> exceptions = checkErasureExceptions(requestId);

        if (!exceptions.isEmpty()) {
            logger.warn("Erasure request rejected: request_id={}, exceptions={}",
                    requestId, exceptions);

            Map<String, Object> rejection = new HashMap<>();
            rejection.put("status", "rejected");
            rejection.put("reason", "Legal obligations prevent erasure");
            rejection.put("exceptions", exceptions);
            return rejection;
        }

        // Perform erasure
        deletePersonalData(requestId);
        notifyThirdParties(requestId, "erasure");

        logger.info("Erasure request completed: request_id={}", requestId);

        Map<String, Object> response = new HashMap<>();
        response.put("status", "completed");
        response.put("request_id", requestId);
        response.put("erasure_date", Instant.now());
        response.put("data_deleted", Arrays.asList(
            "Profile information",
            "Transaction history",
            "Communication records"
        ));
        return response;
    }

    public String submitPortabilityRequest(String dataSubjectId, String email, String format) {
        // Article 20: Right to Data Portability
        String requestId = UUID.randomUUID().toString();

        DataSubjectRequest request = new DataSubjectRequest();
        request.setRequestId(requestId);
        request.setRequestType(RequestType.PORTABILITY);
        request.setStatus(RequestStatus.PENDING);
        request.setDeadline(Instant.now().plus(RESPONSE_DEADLINE_DAYS, ChronoUnit.DAYS));

        // Save request
        // requestRepository.save(request);

        logger.info("Portability request submitted: request_id={}, email={}, format={}",
                requestId, email, format);

        return requestId;
    }

    public Map<String, Object> processPortabilityRequest(String requestId, String format) {
        // Article 20: Provide data in structured, machine-readable format

        Map<String, Object> portableData = gatherPortableData(requestId);

        // Export in requested format (JSON, CSV, XML)
        String exportFile = exportData(portableData, format);

        logger.info("Portability request completed: request_id={}, format={}, file={}",
                requestId, format, exportFile);

        Map<String, Object> response = new HashMap<>();
        response.put("status", "completed");
        response.put("request_id", requestId);
        response.put("export_format", format);
        response.put("download_url", "/downloads/" + exportFile);
        response.put("expires_at", Instant.now().plus(7, ChronoUnit.DAYS));
        return response;
    }

    private void sendVerificationEmail(String email, String requestId) {
        logger.info("Sending verification email: email={}, request_id={}", email, requestId);
        // Email logic
    }

    private Map<String, Object> getUserProfile(String userId) {
        return Map.of("name", "John Doe", "email", "john@example.com");
    }

    private List<Map<String, Object>> getUserTransactions(String userId) {
        return List.of(Map.of("transaction_id", "TX123", "amount", 100.0));
    }

    private List<Map<String, Object>> getUserCommunications(String userId) {
        return List.of(Map.of("message_id", "MSG456", "date", Instant.now()));
    }

    private List<Map<String, Object>> getUserConsents(String userId) {
        return List.of(Map.of("consent_type", "marketing", "granted", true));
    }

    private List<String> checkErasureExceptions(String userId) {
        List<String> exceptions = new ArrayList<>();

        // Article 17(3) exceptions
        // if (hasActiveContract(userId)) {
        //     exceptions.add("Ongoing contract obligations");
        // }
        // if (hasLegalObligations(userId)) {
        //     exceptions.add("Legal retention requirements (7 years)");
        // }

        return exceptions;
    }

    private void deletePersonalData(String userId) {
        logger.info("Deleting personal data: user_id={}", userId);
        // Deletion logic
    }

    private void notifyThirdParties(String userId, String action) {
        logger.info("Notifying third parties: user_id={}, action={}", userId, action);
        // Notification logic
    }

    private Map<String, Object> gatherPortableData(String userId) {
        Map<String, Object> data = new HashMap<>();
        data.put("profile", getUserProfile(userId));
        data.put("transactions", getUserTransactions(userId));
        return data;
    }

    private String exportData(Map<String, Object> data, String format) {
        String filename = "export_" + UUID.randomUUID() + "." + format.toLowerCase();
        // Export logic
        return filename;
    }
}
```

---

## Consent Management

```java
package com.organization.gdpr;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.*;

@Service
public class ConsentManagementService {

    private static final Logger logger = LoggerFactory.getLogger(ConsentManagementService.class);

    public enum ConsentPurpose {
        MARKETING,
        ANALYTICS,
        THIRD_PARTY_SHARING,
        PROFILING
    }

    public static class ConsentRecord {
        private String consentId;
        private String dataSubjectId;
        private ConsentPurpose purpose;
        private boolean granted;
        private Instant grantedAt;
        private Instant revokedAt;
        private String version;
        private String legalBasis;

        // Getters and setters
        public String getConsentId() { return consentId; }
        public void setConsentId(String consentId) { this.consentId = consentId; }

        public ConsentPurpose getPurpose() { return purpose; }
        public void setPurpose(ConsentPurpose purpose) { this.purpose = purpose; }

        public boolean isGranted() { return granted; }
        public void setGranted(boolean granted) { this.granted = granted; }
    }

    public String recordConsent(
            String dataSubjectId,
            ConsentPurpose purpose,
            boolean granted,
            String consentText) {

        // Article 7: Conditions for consent
        // Must be: freely given, specific, informed, unambiguous

        String consentId = UUID.randomUUID().toString();

        ConsentRecord record = new ConsentRecord();
        record.setConsentId(consentId);
        // record.setDataSubjectId(dataSubjectId);
        record.setPurpose(purpose);
        record.setGranted(granted);
        // record.setGrantedAt(Instant.now());
        // record.setVersion("1.0");
        // record.setLegalBasis("consent");

        // Store consent record with full audit trail
        // consentRepository.save(record);

        logger.info("Consent recorded: consent_id={}, data_subject={}, purpose={}, granted={}",
                consentId, dataSubjectId, purpose, granted);

        return consentId;
    }

    public void revokeConsent(String dataSubjectId, ConsentPurpose purpose) {
        // Article 7(3): Right to withdraw consent at any time

        // ConsentRecord record = consentRepository.findByDataSubjectAndPurpose(
        //     dataSubjectId, purpose);

        ConsentRecord record = new ConsentRecord();
        record.setConsentId(UUID.randomUUID().toString());
        record.setPurpose(purpose);
        record.setGranted(true);

        if (!record.isGranted()) {
            throw new IllegalStateException("Consent not granted");
        }

        record.setGranted(false);
        // record.setRevokedAt(Instant.now());

        // consentRepository.save(record);

        // Stop processing based on revoked consent
        stopProcessingForPurpose(dataSubjectId, purpose);

        logger.info("Consent revoked: data_subject={}, purpose={}", dataSubjectId, purpose);
    }

    public boolean hasValidConsent(String dataSubjectId, ConsentPurpose purpose) {
        // Check if valid consent exists

        // ConsentRecord record = consentRepository.findByDataSubjectAndPurpose(
        //     dataSubjectId, purpose);

        // Simulated
        boolean hasConsent = true; // Check database

        logger.info("Consent checked: data_subject={}, purpose={}, valid={}",
                dataSubjectId, purpose, hasConsent);

        return hasConsent;
    }

    private void stopProcessingForPurpose(String dataSubjectId, ConsentPurpose purpose) {
        logger.info("Stopping processing: data_subject={}, purpose={}", dataSubjectId, purpose);
        // Stop marketing emails, analytics tracking, etc.
    }
}
```

---

## Breach Notification

```java
package com.organization.gdpr;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Service
public class BreachNotificationService {

    private static final Logger logger = LoggerFactory.getLogger(BreachNotificationService.class);
    private static final int NOTIFICATION_DEADLINE_HOURS = 72; // Article 33

    public enum BreachSeverity {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    public static class DataBreach {
        private String breachId;
        private Instant detectedAt;
        private Instant notificationDeadline;
        private BreachSeverity severity;
        private String description;
        private int affectedDataSubjects;
        private List<String> dataCategories;
        private boolean supervisoryAuthorityNotified;
        private boolean dataSubjectsNotified;

        // Getters and setters
        public String getBreachId() { return breachId; }
        public void setBreachId(String breachId) { this.breachId = breachId; }

        public BreachSeverity getSeverity() { return severity; }
        public void setSeverity(BreachSeverity severity) { this.severity = severity; }

        public Instant getNotificationDeadline() { return notificationDeadline; }
        public void setNotificationDeadline(Instant deadline) { this.notificationDeadline = deadline; }
    }

    public String reportBreach(
            String description,
            BreachSeverity severity,
            int affectedDataSubjects,
            List<String> dataCategories) {

        // Article 33: Notification to supervisory authority (72 hours)
        String breachId = UUID.randomUUID().toString();
        Instant detectedAt = Instant.now();
        Instant deadline = detectedAt.plus(NOTIFICATION_DEADLINE_HOURS, ChronoUnit.HOURS);

        DataBreach breach = new DataBreach();
        breach.setBreachId(breachId);
        // breach.setDetectedAt(detectedAt);
        breach.setNotificationDeadline(deadline);
        breach.setSeverity(severity);
        // breach.setDescription(description);
        // breach.setAffectedDataSubjects(affectedDataSubjects);
        // breach.setDataCategories(dataCategories);
        // breach.setSupervisoryAuthorityNotified(false);
        // breach.setDataSubjectsNotified(false);

        // Save breach record
        // breachRepository.save(breach);

        // Assess if notification required
        if (requiresSupervisoryNotification(severity)) {
            notifySupervisoryAuthority(breachId);
        }

        if (requiresDataSubjectNotification(severity, affectedDataSubjects)) {
            notifyDataSubjects(breachId);
        }

        logger.warn("Data breach reported: breach_id={}, severity={}, affected={}, deadline={}",
                breachId, severity, affectedDataSubjects, deadline);

        return breachId;
    }

    private boolean requiresSupervisoryNotification(BreachSeverity severity) {
        // Article 33: Notify unless unlikely to result in risk
        return severity != BreachSeverity.LOW;
    }

    private boolean requiresDataSubjectNotification(BreachSeverity severity, int affected) {
        // Article 34: Notify if likely to result in high risk
        return severity == BreachSeverity.HIGH || severity == BreachSeverity.CRITICAL;
    }

    private void notifySupervisoryAuthority(String breachId) {
        logger.warn("Notifying supervisory authority: breach_id={}", breachId);
        // Send notification to DPA
    }

    private void notifyDataSubjects(String breachId) {
        logger.warn("Notifying affected data subjects: breach_id={}", breachId);
        // Send notifications to affected individuals
    }
}
```

---

## Success Criteria

- [ ] Data inventory completed
- [ ] Data subject rights portal operational
- [ ] 30-day response automation functional
- [ ] Consent management implemented
- [ ] 72-hour breach notification process
- [ ] Privacy by design principles applied
- [ ] DPIA conducted for high-risk processing

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
