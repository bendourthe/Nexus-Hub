---
template_id: compliance_governance_ccpa_java
template_name: CCPA Compliance - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - privacy_protection/README.md
related_templates:
  - compliance_frameworks/java_gdpr_compliance.md
tools:
  - spring-boot (web framework)
  - logback (logging)
tags:
  - ccpa
  - privacy
  - california
  - java
---

# CCPA Compliance - Java

**California Consumer Privacy Act for Spring Boot applications**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**5 Key Rights**: Right to Know, Right to Delete, Right to Opt-Out, Right to Non-Discrimination, Right to Correct

---

## Right to Know

```java
package com.company.compliance.ccpa;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.*;

@Service
public class CCPADataDisclosureService {
    private static final Logger logger = LoggerFactory.getLogger(CCPADataDisclosureService.class);

    public DisclosureResponse processRightToKnow(String consumerId) {
        String requestId = UUID.randomUUID().toString();
        Instant deadline = Instant.now().plusSeconds(45 * 24 * 60 * 60); // 45 days

        var disclosure = new DisclosureResponse();
        disclosure.setRequestId(requestId);
        disclosure.setConsumerId(consumerId);
        disclosure.setRequestDate(Instant.now());
        disclosure.setResponseDeadline(deadline);
        disclosure.setCategoriesCollected(Arrays.asList(
            "Identifiers",
            "Commercial information",
            "Internet activity",
            "Geolocation data"
        ));
        disclosure.setBusinessPurposes(Arrays.asList(
            "Providing services",
            "Improving services",
            "Marketing (with consent)"
        ));
        disclosure.setThirdParties(Arrays.asList(
            "Service providers (Stripe, AWS)",
            "Analytics providers"
        ));

        logger.info("CCPA right to know processed: requestId={}, consumerId={}",
            requestId, consumerId);

        return disclosure;
    }

    public static class DisclosureResponse {
        private String requestId;
        private String consumerId;
        private Instant requestDate;
        private Instant responseDeadline;
        private List<String> categoriesCollected;
        private List<String> businessPurposes;
        private List<String> thirdParties;

        // Getters and setters
        public String getRequestId() { return requestId; }
        public void setRequestId(String requestId) { this.requestId = requestId; }
        public String getConsumerId() { return consumerId; }
        public void setConsumerId(String consumerId) { this.consumerId = consumerId; }
        public Instant getRequestDate() { return requestDate; }
        public void setRequestDate(Instant requestDate) { this.requestDate = requestDate; }
        public Instant getResponseDeadline() { return responseDeadline; }
        public void setResponseDeadline(Instant deadline) { this.responseDeadline = deadline; }
        public List<String> getCategoriesCollected() { return categoriesCollected; }
        public void setCategoriesCollected(List<String> categories) { this.categoriesCollected = categories; }
        public List<String> getBusinessPurposes() { return businessPurposes; }
        public void setBusinessPurposes(List<String> purposes) { this.businessPurposes = purposes; }
        public List<String> getThirdParties() { return thirdParties; }
        public void setThirdParties(List<String> parties) { this.thirdParties = parties; }
    }
}
```

---

## Right to Delete

```java
package com.company.compliance.ccpa;

@Service
public class CCPADeletionService {
    private static final Logger logger = LoggerFactory.getLogger(CCPADeletionService.class);

    public DeletionResult processRightToDelete(String consumerId) {
        String requestId = UUID.randomUUID().toString();

        // Check for deletion exceptions
        List<String> exceptions = checkDeletionExceptions(consumerId);

        if (!exceptions.isEmpty()) {
            logger.warn("Deletion denied: requestId={}, exceptions={}", requestId, exceptions);

            return new DeletionResult("Denied",
                "Legal obligations require data retention", exceptions);
        }

        // Perform deletion
        deleteConsumerData(consumerId, requestId);

        logger.warn("Consumer data deleted: requestId={}, consumerId={}", requestId, consumerId);

        return new DeletionResult("Completed", requestId);
    }

    private List<String> checkDeletionExceptions(String consumerId) {
        List<String> exceptions = new ArrayList<>();

        // Check for ongoing transactions
        boolean hasActiveOrders = false; // Query database
        if (hasActiveOrders) {
            exceptions.add("Active orders pending completion");
        }

        // Check for legal obligations (7 years for tax records)
        boolean hasRecentTransactions = false; // Query database
        if (hasRecentTransactions) {
            exceptions.add("Tax and accounting retention (7 years)");
        }

        return exceptions;
    }

    private void deleteConsumerData(String consumerId, String requestId) {
        // Delete from all collections
        // Pseudonymize transaction data
        logger.warn("Data deletion executed: consumerId={}, requestId={}", consumerId, requestId);
    }

    public static class DeletionResult {
        private String status;
        private String reason;
        private List<String> exceptions;
        private String requestId;

        public DeletionResult(String status, String reason, List<String> exceptions) {
            this.status = status;
            this.reason = reason;
            this.exceptions = exceptions;
        }

        public DeletionResult(String status, String requestId) {
            this.status = status;
            this.requestId = requestId;
        }

        public String getStatus() { return status; }
        public String getReason() { return reason; }
        public List<String> getExceptions() { return exceptions; }
        public String getRequestId() { return requestId; }
    }
}
```

---

## Right to Opt-Out of Sale

```java
package com.company.compliance.ccpa;

@Service
public class CCPAOptOutService {
    private static final Logger logger = LoggerFactory.getLogger(CCPAOptOutService.class);

    public OptOutResult processOptOut(String consumerId) {
        // Update consumer opt-out preference
        // Notify third parties

        logger.info("Consumer opted out of sale: consumerId={}", consumerId);

        return new OptOutResult("Completed", Instant.now());
    }

    public static class OptOutResult {
        private String status;
        private Instant optOutDate;

        public OptOutResult(String status, Instant optOutDate) {
            this.status = status;
            this.optOutDate = optOutDate;
        }

        public String getStatus() { return status; }
        public Instant getOptOutDate() { return optOutDate; }
    }
}
```

---

## Success Criteria

- [ ] Right to Know requests processed within 45 days
- [ ] Right to Delete honored with exception handling
- [ ] Opt-out mechanism operational
- [ ] "Do Not Sell" link prominently displayed
- [ ] Non-discrimination enforced

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
