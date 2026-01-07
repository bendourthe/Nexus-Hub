---
template_id: compliance_governance_gdpr_compliance_java
template_name: GDPR Compliance - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - privacy_protection/README.md
related_templates:
  - compliance_frameworks/java_iso27001_implementation.md
tools:
  - spring-data-jpa (data access)
tags:
  - gdpr
  - privacy
  - data-protection
  - java
  - spring-boot
---

# GDPR Compliance - Java

**General Data Protection Regulation implementation for Spring Boot**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### GDPR Key Requirements

**8 Data Subject Rights**: Access, Rectification, Erasure, Restriction, Portability, Object, Automated Decision-making, Informed

**Breach Notification**: 72 hours to supervisory authority (Article 33)

---

## Right to Access (Article 15)

```java
package com.company.compliance.gdpr;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

/**
 * GDPR Data Access Manager.
 *
 * GDPR Article 15: Right of access
 */
@Service
public class GDPRDataAccessManager {
    private static final Logger logger = LoggerFactory.getLogger(GDPRDataAccessManager.class);
    private static final int RESPONSE_DEADLINE_DAYS = 30;

    /**
     * Process data subject access request (DSAR).
     *
     * @param dataSubjectId Data subject identifier
     * @param requestDetails Request details
     * @return Request ID and deadline
     */
    public DSARResponse processAccessRequest(String dataSubjectId,
                                            Map<String, Object> requestDetails) {
        String requestId = UUID.randomUUID().toString();
        Instant deadline = Instant.now().plus(RESPONSE_DEADLINE_DAYS, ChronoUnit.DAYS);

        logger.info("DSAR received: requestId={}, dataSubjectId={}, deadline={}, timestamp={}",
            requestId, dataSubjectId, deadline, Instant.now());

        // Initiate identity verification
        initiateIdentityVerification(requestId, dataSubjectId);

        return new DSARResponse(requestId, deadline);
    }

    /**
     * Generate complete data export for data subject.
     */
    public DataExport generateDataExport(String dataSubjectId) {
        String exportId = UUID.randomUUID().toString();

        DataExport export = new DataExport();
        export.setExportId(exportId);
        export.setDataSubjectId(dataSubjectId);
        export.setExportDate(Instant.now());

        // Collect all personal data categories
        export.setProfileData(getProfileData(dataSubjectId));
        export.setAccountData(getAccountData(dataSubjectId));
        export.setTransactionData(getTransactionData(dataSubjectId));

        logger.info("Data export generated: exportId={}, dataSubjectId={}, timestamp={}",
            exportId, dataSubjectId, Instant.now());

        return export;
    }

    private void initiateIdentityVerification(String requestId, String dataSubjectId) {
        // Send verification email/SMS
        logger.info("Identity verification initiated: requestId={}", requestId);
    }

    private Map<String, Object> getProfileData(String dataSubjectId) {
        // Query profile data
        return new HashMap<>();
    }

    private Map<String, Object> getAccountData(String dataSubjectId) {
        // Query account data
        return new HashMap<>();
    }

    private List<Map<String, Object>> getTransactionData(String dataSubjectId) {
        // Query transaction data
        return new ArrayList<>();
    }

    public static class DSARResponse {
        private final String requestId;
        private final Instant deadline;

        public DSARResponse(String requestId, Instant deadline) {
            this.requestId = requestId;
            this.deadline = deadline;
        }

        public String getRequestId() { return requestId; }
        public Instant getDeadline() { return deadline; }
    }

    public static class DataExport {
        private String exportId;
        private String dataSubjectId;
        private Instant exportDate;
        private Map<String, Object> profileData;
        private Map<String, Object> accountData;
        private List<Map<String, Object>> transactionData;

        // Getters and setters
        public String getExportId() { return exportId; }
        public void setExportId(String exportId) { this.exportId = exportId; }

        public String getDataSubjectId() { return dataSubjectId; }
        public void setDataSubjectId(String dataSubjectId) {
            this.dataSubjectId = dataSubjectId;
        }

        public Instant getExportDate() { return exportDate; }
        public void setExportDate(Instant exportDate) { this.exportDate = exportDate; }

        public Map<String, Object> getProfileData() { return profileData; }
        public void setProfileData(Map<String, Object> profileData) {
            this.profileData = profileData;
        }

        public Map<String, Object> getAccountData() { return accountData; }
        public void setAccountData(Map<String, Object> accountData) {
            this.accountData = accountData;
        }

        public List<Map<String, Object>> getTransactionData() { return transactionData; }
        public void setTransactionData(List<Map<String, Object>> transactionData) {
            this.transactionData = transactionData;
        }
    }
}
```

## Right to Erasure (Article 17)

```java
package com.company.compliance.gdpr;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * GDPR Erasure Manager.
 *
 * GDPR Article 17: Right to erasure ("right to be forgotten")
 */
@Service
public class GDPRErasureManager {
    private static final Logger logger = LoggerFactory.getLogger(GDPRErasureManager.class);

    /**
     * Process right to erasure request.
     */
    public ErasureResult processErasureRequest(String dataSubjectId, String reason) {
        String requestId = UUID.randomUUID().toString();

        // Check for erasure exceptions
        List<ErasureException> exceptions = checkErasureExceptions(dataSubjectId);

        if (!exceptions.isEmpty()) {
            logger.info("Erasure request denied: requestId={}, dataSubjectId={}, " +
                       "exceptions={}", requestId, dataSubjectId, exceptions);

            return new ErasureResult("denied", "Legal obligations require data retention",
                                    exceptions);
        }

        // Process erasure
        String deletionId = UUID.randomUUID().toString();
        erasePersonalData(dataSubjectId, deletionId);

        logger.warn("Personal data erased: deletionId={}, dataSubjectId={}, " +
                   "reason={}, timestamp={}",
            deletionId, dataSubjectId, reason, Instant.now());

        return new ErasureResult("completed", "Data erased", new ArrayList<>());
    }

    private List<ErasureException> checkErasureExceptions(String dataSubjectId) {
        List<ErasureException> exceptions = new ArrayList<>();

        // Check for legal obligations (simplified)
        // In production: Check contracts, legal claims, tax retention, etc.

        return exceptions;
    }

    private void erasePersonalData(String dataSubjectId, String deletionId) {
        // Delete from all collections
        // Pseudonymize transaction data (cannot fully delete)
        // Store erasure record
    }

    public static class ErasureResult {
        private final String status;
        private final String message;
        private final List<ErasureException> exceptions;

        public ErasureResult(String status, String message,
                           List<ErasureException> exceptions) {
            this.status = status;
            this.message = message;
            this.exceptions = exceptions;
        }

        public String getStatus() { return status; }
        public String getMessage() { return message; }
        public List<ErasureException> getExceptions() { return exceptions; }
    }

    public static class ErasureException {
        private final String type;
        private final String description;

        public ErasureException(String type, String description) {
            this.type = type;
            this.description = description;
        }

        public String getType() { return type; }
        public String getDescription() { return description; }
    }
}
```

---

## Success Criteria

- [ ] All 8 data subject rights implemented
- [ ] DSAR response within 30 days
- [ ] Erasure requests processed (with exception handling)
- [ ] Data portability in machine-readable format
- [ ] Breach notification within 72 hours

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
