---
template_id: compliance_governance_gdpr_compliance_javascript
template_name: GDPR Compliance - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - privacy_protection/README.md
  - compliance_frameworks/javascript_iso27001_implementation.md
related_templates:
  - incident_response/javascript_breach_protocols.md
  - governance_policies/javascript_access_control.md
tools:
  - joi (validation)
  - node-anonymizer (PII anonymization)
tags:
  - gdpr
  - privacy
  - data-protection
  - javascript
  - nodejs
---

# GDPR Compliance - JavaScript

**General Data Protection Regulation implementation for Node.js**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### GDPR Key Requirements

**8 Data Subject Rights**:
1. Right to Access (Article 15)
2. Right to Rectification (Article 16)
3. Right to Erasure (Article 17)
4. Right to Restriction (Article 18)
5. Right to Data Portability (Article 20)
6. Right to Object (Article 21)
7. Rights related to automated decision-making (Article 22)
8. Right to be informed (Articles 13-14)

**Breach Notification**: 72 hours to supervisory authority (Article 33)

---

## Right to Access (Article 15)

```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'gdpr-compliance.log' })
  ]
});

class GDPRDataAccessManager {
  /**
   * Process data subject access request (DSAR).
   *
   * GDPR Article 15: Right of access
   * Response deadline: 1 month
   */
  async processAccessRequest(dataSubjectId, requestDetails) {
    const requestId = uuidv4();
    const deadline = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days

    // Create DSAR record
    await db.collection('dsar_requests').insertOne({
      requestId,
      dataSubjectId,
      requestType: 'access',
      requestDate: new Date(),
      deadline,
      status: 'processing',
      verificationCompleted: false
    });

    logger.info('DSAR received', {
      event: 'dsar_received',
      requestId,
      requestType: 'access',
      dataSubjectId,
      deadline: deadline.toISOString()
    });

    // Verify identity before processing
    await this.initiateIdentityVerification(requestId, dataSubjectId);

    return { requestId, deadline };
  }

  /**
   * Generate complete data export for data subject.
   *
   * GDPR Article 15: Provide copy of personal data
   */
  async generateDataExport(dataSubjectId) {
    const exportData = {
      exportId: uuidv4(),
      dataSubjectId,
      exportDate: new Date(),

      // Personal data categories
      profileData: await this.getProfileData(dataSubjectId),
      accountData: await this.getAccountData(dataSubjectId),
      transactionData: await this.getTransactionData(dataSubjectId),
      communicationData: await this.getCommunicationData(dataSubjectId),
      behavioralData: await this.getBehavioralData(dataSubjectId),

      // Processing information
      processingPurposes: await this.getProcessingPurposes(dataSubjectId),
      dataRecipients: await this.getDataRecipients(dataSubjectId),
      retentionPeriods: await this.getRetentionPeriods(dataSubjectId),

      // International transfers
      internationalTransfers: await this.getInternationalTransfers(dataSubjectId)
    };

    // Store export for audit trail
    await db.collection('data_exports').insertOne(exportData);

    logger.info('Data export generated', {
      event: 'data_export_generated',
      exportId: exportData.exportId,
      dataSubjectId,
      categoriesIncluded: Object.keys(exportData).length
    });

    return exportData;
  }

  async getProfileData(dataSubjectId) {
    const user = await db.collection('users').findOne({ userId: dataSubjectId });

    if (!user) return null;

    return {
      userId: user.userId,
      email: user.email,
      name: user.name,
      dateOfBirth: user.dateOfBirth,
      address: user.address,
      phoneNumber: user.phoneNumber,
      accountCreated: user.createdAt
    };
  }

  async getAccountData(dataSubjectId) {
    return {
      accountStatus: 'active',
      subscriptionTier: 'premium',
      preferences: await db.collection('user_preferences').findOne({ userId: dataSubjectId })
    };
  }

  async getTransactionData(dataSubjectId) {
    return await db.collection('transactions')
      .find({ userId: dataSubjectId })
      .toArray();
  }

  async getCommunicationData(dataSubjectId) {
    return await db.collection('communications')
      .find({ userId: dataSubjectId })
      .toArray();
  }

  async getBehavioralData(dataSubjectId) {
    return await db.collection('activity_logs')
      .find({ userId: dataSubjectId })
      .limit(1000)
      .toArray();
  }

  async getProcessingPurposes(dataSubjectId) {
    return [
      {
        purpose: 'Contract performance',
        legalBasis: 'Article 6(1)(b) - Contract',
        dataCategories: ['profile', 'account', 'transaction']
      },
      {
        purpose: 'Marketing communications',
        legalBasis: 'Article 6(1)(a) - Consent',
        dataCategories: ['email', 'preferences']
      }
    ];
  }

  async getDataRecipients(dataSubjectId) {
    return [
      {
        recipient: 'Payment Processor (Stripe)',
        purpose: 'Payment processing',
        safeguards: 'Standard Contractual Clauses'
      },
      {
        recipient: 'Email Service (SendGrid)',
        purpose: 'Transactional emails',
        safeguards: 'Data Processing Agreement'
      }
    ];
  }

  async getRetentionPeriods(dataSubjectId) {
    return {
      profileData: '7 years after account closure',
      transactionData: '10 years (tax requirements)',
      communicationData: '2 years',
      behavioralData: '1 year'
    };
  }

  async getInternationalTransfers(dataSubjectId) {
    return [
      {
        country: 'United States',
        safeguard: 'Standard Contractual Clauses',
        recipient: 'Cloud hosting provider (AWS)'
      }
    ];
  }

  async initiateIdentityVerification(requestId, dataSubjectId) {
    // Send verification email/SMS
    await db.collection('dsar_requests').updateOne(
      { requestId },
      {
        $set: {
          verificationInitiated: new Date(),
          verificationMethod: 'email'
        }
      }
    );
  }
}

module.exports = GDPRDataAccessManager;
```

---

## Right to Erasure (Article 17)

```javascript
class GDPRErasureManager {
  /**
   * Process right to erasure request ("right to be forgotten").
   *
   * GDPR Article 17: Right to erasure
   */
  async processErasureRequest(dataSubjectId, reason) {
    const requestId = uuidv4();

    // Check for erasure exceptions
    const exceptions = await this.checkErasureExceptions(dataSubjectId);

    if (exceptions.length > 0) {
      logger.info('Erasure request denied - exceptions apply', {
        event: 'erasure_denied',
        requestId,
        dataSubjectId,
        exceptions
      });

      return {
        status: 'denied',
        reason: 'Legal obligations require data retention',
        exceptions
      };
    }

    // Process erasure
    const deletionId = uuidv4();

    await this.erasePersonalData(dataSubjectId, deletionId);

    logger.warn('Personal data erased', {
      event: 'data_erased',
      deletionId,
      dataSubjectId,
      reason,
      timestamp: new Date().toISOString()
    });

    return { status: 'completed', deletionId };
  }

  /**
   * Check for exceptions to right to erasure.
   *
   * GDPR Article 17(3): Exceptions
   */
  async checkErasureExceptions(dataSubjectId) {
    const exceptions = [];

    // Check for legal obligations
    const activeContracts = await db.collection('contracts')
      .countDocuments({ userId: dataSubjectId, status: 'active' });

    if (activeContracts > 0) {
      exceptions.push({
        type: 'contract_performance',
        article: '17(3)(b)',
        description: 'Active contractual obligations'
      });
    }

    // Check for legal claims
    const legalClaims = await db.collection('legal_claims')
      .countDocuments({ userId: dataSubjectId, status: 'open' });

    if (legalClaims > 0) {
      exceptions.push({
        type: 'legal_claims',
        article: '17(3)(e)',
        description: 'Establishment or defense of legal claims'
      });
    }

    // Check tax/accounting obligations
    const recentTransactions = await db.collection('transactions')
      .countDocuments({
        userId: dataSubjectId,
        date: { $gte: new Date(Date.now() - 10 * 365 * 24 * 60 * 60 * 1000) }
      });

    if (recentTransactions > 0) {
      exceptions.push({
        type: 'legal_obligation',
        article: '17(3)(b)',
        description: 'Tax and accounting record retention (10 years)'
      });
    }

    return exceptions;
  }

  /**
   * Erase all personal data for data subject.
   */
  async erasePersonalData(dataSubjectId, deletionId) {
    const collections = [
      'users',
      'user_preferences',
      'communications',
      'activity_logs',
      'sessions'
    ];

    for (const collection of collections) {
      await db.collection(collection).deleteMany({ userId: dataSubjectId });
    }

    // Pseudonymize transaction data (cannot fully delete due to legal requirements)
    await db.collection('transactions').updateMany(
      { userId: dataSubjectId },
      {
        $set: {
          userId: `DELETED_${deletionId}`,
          userEmail: '[REDACTED]',
          userName: '[REDACTED]',
          deletionDate: new Date()
        }
      }
    );

    // Store erasure record (without personal data)
    await db.collection('erasure_records').insertOne({
      deletionId,
      dataSubjectIdHash: require('crypto')
        .createHash('sha256')
        .update(dataSubjectId)
        .digest('hex'),
      erasureDate: new Date(),
      collectionsErased: collections
    });
  }
}

module.exports = GDPRErasureManager;
```

---

## Right to Data Portability (Article 20)

```javascript
class GDPRDataPortabilityManager {
  /**
   * Generate portable data export.
   *
   * GDPR Article 20: Right to data portability
   * Format: Machine-readable (JSON)
   */
  async generatePortableExport(dataSubjectId) {
    const exportData = {
      exportMetadata: {
        exportId: uuidv4(),
        dataSubjectId,
        exportDate: new Date().toISOString(),
        format: 'JSON',
        version: '1.0'
      },

      // Only data provided by or generated from data subject
      personalData: {
        profile: await this.getPortableProfile(dataSubjectId),
        preferences: await this.getPortablePreferences(dataSubjectId),
        content: await this.getPortableContent(dataSubjectId),
        interactions: await this.getPortableInteractions(dataSubjectId)
      }
    };

    logger.info('Portable data export generated', {
      event: 'portable_export_generated',
      exportId: exportData.exportMetadata.exportId,
      dataSubjectId
    });

    return exportData;
  }

  async getPortableProfile(dataSubjectId) {
    const user = await db.collection('users').findOne({ userId: dataSubjectId });

    return {
      email: user.email,
      name: user.name,
      dateOfBirth: user.dateOfBirth,
      phoneNumber: user.phoneNumber,
      accountCreated: user.createdAt.toISOString()
    };
  }

  async getPortablePreferences(dataSubjectId) {
    return await db.collection('user_preferences').findOne({ userId: dataSubjectId });
  }

  async getPortableContent(dataSubjectId) {
    return await db.collection('user_content')
      .find({ userId: dataSubjectId })
      .toArray();
  }

  async getPortableInteractions(dataSubjectId) {
    return await db.collection('interactions')
      .find({ userId: dataSubjectId })
      .toArray();
  }

  /**
   * Transmit data directly to another controller.
   *
   * GDPR Article 20(2): Direct transmission
   */
  async transmitToAnotherController(dataSubjectId, targetEndpoint, apiKey) {
    const portableData = await this.generatePortableExport(dataSubjectId);

    const axios = require('axios');

    try {
      const response = await axios.post(targetEndpoint, portableData, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        }
      });

      logger.info('Data transmitted to another controller', {
        event: 'data_portability_transmission',
        dataSubjectId,
        targetEndpoint,
        status: response.status
      });

      return { status: 'transmitted', response: response.status };
    } catch (error) {
      logger.error('Data transmission failed', {
        event: 'transmission_failed',
        dataSubjectId,
        error: error.message
      });

      throw error;
    }
  }
}

module.exports = GDPRDataPortabilityManager;
```

---

## Consent Management (Article 7)

```javascript
class GDPRConsentManager {
  /**
   * Record explicit consent.
   *
   * GDPR Article 7: Conditions for consent
   */
  async recordConsent(dataSubjectId, consentDetails) {
    const consentId = uuidv4();

    const consentRecord = {
      consentId,
      dataSubjectId,
      purpose: consentDetails.purpose,
      dataCategories: consentDetails.dataCategories,

      // Consent must be explicit
      consentGiven: true,
      consentMethod: consentDetails.method, // 'checkbox', 'signature', 'verbal'
      consentText: consentDetails.text,

      // Timestamp
      consentDate: new Date(),

      // Withdrawal information
      withdrawalInstructions: consentDetails.withdrawalInstructions,
      withdrawn: false,
      withdrawalDate: null
    };

    await db.collection('consent_records').insertOne(consentRecord);

    logger.info('Consent recorded', {
      event: 'consent_recorded',
      consentId,
      dataSubjectId,
      purpose: consentDetails.purpose
    });

    return consentId;
  }

  /**
   * Withdraw consent.
   *
   * GDPR Article 7(3): Right to withdraw consent
   */
  async withdrawConsent(consentId, dataSubjectId) {
    const result = await db.collection('consent_records').findOneAndUpdate(
      { consentId, dataSubjectId },
      {
        $set: {
          withdrawn: true,
          withdrawalDate: new Date()
        }
      },
      { returnDocument: 'after' }
    );

    if (!result.value) {
      throw new Error('Consent record not found');
    }

    logger.warn('Consent withdrawn', {
      event: 'consent_withdrawn',
      consentId,
      dataSubjectId,
      purpose: result.value.purpose
    });

    // Stop processing based on withdrawn consent
    await this.stopConsentBasedProcessing(dataSubjectId, result.value.purpose);

    return { status: 'withdrawn', consentId };
  }

  /**
   * Check if valid consent exists.
   */
  async hasValidConsent(dataSubjectId, purpose) {
    const consent = await db.collection('consent_records').findOne({
      dataSubjectId,
      purpose,
      withdrawn: false
    });

    return consent !== null;
  }

  async stopConsentBasedProcessing(dataSubjectId, purpose) {
    // Implementation depends on purpose
    if (purpose === 'marketing') {
      await db.collection('marketing_lists').deleteMany({ userId: dataSubjectId });
    }
  }
}

module.exports = GDPRConsentManager;
```

---

## Privacy by Design (Article 25)

```javascript
class PrivacyByDesignManager {
  /**
   * Implement data minimization.
   *
   * GDPR Article 5(1)(c): Data minimization
   */
  validateDataCollection(collectedData, purpose) {
    const necessaryFields = this.getNecessaryFields(purpose);

    const unnecessaryFields = Object.keys(collectedData)
      .filter(field => !necessaryFields.includes(field));

    if (unnecessaryFields.length > 0) {
      logger.warn('Data minimization violation', {
        event: 'data_minimization_violation',
        purpose,
        unnecessaryFields
      });

      throw new Error(`Collecting unnecessary data: ${unnecessaryFields.join(', ')}`);
    }

    return true;
  }

  getNecessaryFields(purpose) {
    const fieldMappings = {
      'account_creation': ['email', 'password', 'name'],
      'purchase': ['email', 'paymentMethod', 'shippingAddress'],
      'newsletter': ['email']
    };

    return fieldMappings[purpose] || [];
  }

  /**
   * Pseudonymization of personal data.
   *
   * GDPR Article 25(1): Data protection by design
   */
  async pseudonymizeData(personalData) {
    const crypto = require('crypto');

    const pseudonymizationKey = process.env.PSEUDONYMIZATION_KEY;

    const pseudonymized = {};

    for (const [field, value] of Object.entries(personalData)) {
      if (this.isPII(field)) {
        const hmac = crypto.createHmac('sha256', pseudonymizationKey);
        hmac.update(value.toString());
        pseudonymized[field] = hmac.digest('hex');
      } else {
        pseudonymized[field] = value;
      }
    }

    return pseudonymized;
  }

  isPII(fieldName) {
    const piiFields = ['email', 'name', 'phoneNumber', 'address', 'ssn', 'dateOfBirth'];
    return piiFields.includes(fieldName);
  }
}

module.exports = PrivacyByDesignManager;
```

---

## Success Criteria

- [ ] All 8 data subject rights implemented
- [ ] DSAR response within 30 days
- [ ] Erasure requests processed (with exception handling)
- [ ] Data portability in machine-readable format
- [ ] Consent recorded with explicit opt-in
- [ ] Consent withdrawal processed immediately
- [ ] Privacy by design principles enforced
- [ ] Data minimization validated
- [ ] Breach notification within 72 hours

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
