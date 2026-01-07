---
template_id: compliance_governance_ccpa_compliance_javascript
template_name: CCPA Compliance - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - privacy_protection/README.md
  - privacy_protection/javascript_gdpr_compliance.md
related_templates:
  - governance_policies/javascript_access_control.md
tools:
  - joi (validation)
tags:
  - ccpa
  - privacy
  - california
  - javascript
  - nodejs
---

# CCPA Compliance - JavaScript

**California Consumer Privacy Act implementation**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### CCPA/CPRA Key Rights

1. **Right to Know** - What personal information is collected
2. **Right to Delete** - Request deletion of personal information
3. **Right to Opt-Out** - Opt-out of sale of personal information
4. **Right to Non-Discrimination** - Equal service regardless of privacy choices
5. **Right to Correct** - Correct inaccurate personal information (CPRA)

### Key Definitions

**Consumer**: California resident
**Personal Information**: Information that identifies, relates to, or could be linked to a consumer
**Sale**: Sharing personal information for monetary or other valuable consideration

---

## Implementation

```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'ccpa-compliance.log' })
  ]
});

class CCPAComplianceManager {
  /**
   * Process Right to Know request.
   *
   * CCPA §1798.100: Right to know what personal information is collected
   */
  async processRightToKnow(consumerId) {
    const requestId = uuidv4();

    // Collect all personal information
    const personalInfo = await this.collectPersonalInformation(consumerId);

    // Collect business purposes
    const businessPurposes = await this.getBusinessPurposes(consumerId);

    // Collect categories of third parties
    const thirdParties = await this.getThirdParties(consumerId);

    const disclosure = {
      requestId,
      consumerId,
      requestDate: new Date(),
      responseDeadline: new Date(Date.now() + 45 * 24 * 60 * 60 * 1000), // 45 days

      // Categories of personal information collected
      categoriesCollected: this.categorizePersonalInfo(personalInfo),

      // Specific pieces of personal information
      personalInformation: personalInfo,

      // Business purposes for collection
      businessPurposes,

      // Categories of third parties
      thirdParties
    };

    await db.collection('ccpa_disclosures').insertOne(disclosure);

    logger.info('CCPA Right to Know request processed', {
      event: 'ccpa_right_to_know',
      requestId,
      consumerId,
      timestamp: new Date().toISOString()
    });

    return disclosure;
  }

  async collectPersonalInformation(consumerId) {
    const consumer = await db.collection('users').findOne({ userId: consumerId });

    return {
      identifiers: {
        name: consumer.name,
        email: consumer.email,
        phoneNumber: consumer.phoneNumber,
        address: consumer.address
      },
      commercialInfo: await this.getCommercialInfo(consumerId),
      internetActivity: await this.getInternetActivity(consumerId),
      geolocationData: await this.getGeolocationData(consumerId)
    };
  }

  async getCommercialInfo(consumerId) {
    const transactions = await db.collection('transactions')
      .find({ userId: consumerId })
      .toArray();

    return {
      purchaseHistory: transactions,
      preferences: await db.collection('preferences').findOne({ userId: consumerId })
    };
  }

  async getInternetActivity(consumerId) {
    return await db.collection('activity_logs')
      .find({ userId: consumerId })
      .limit(1000)
      .toArray();
  }

  async getGeolocationData(consumerId) {
    return await db.collection('location_data')
      .find({ userId: consumerId })
      .toArray();
  }

  categorizePersonalInfo(personalInfo) {
    return [
      'Identifiers',
      'Commercial information',
      'Internet or other electronic network activity',
      'Geolocation data'
    ];
  }

  async getBusinessPurposes(consumerId) {
    return [
      {
        purpose: 'Providing services',
        description: 'To provide the products and services you request'
      },
      {
        purpose: 'Improving services',
        description: 'To understand how you use our services and improve them'
      },
      {
        purpose: 'Marketing',
        description: 'To send you marketing communications (with consent)'
      }
    ];
  }

  async getThirdParties(consumerId) {
    return [
      {
        category: 'Service providers',
        purpose: 'Payment processing, hosting',
        examples: ['Stripe', 'AWS']
      },
      {
        category: 'Analytics providers',
        purpose: 'Usage analytics',
        examples: ['Google Analytics']
      }
    ];
  }

  /**
   * Process Right to Delete request.
   *
   * CCPA §1798.105: Right to deletion
   */
  async processRightToDelete(consumerId, verificationToken) {
    // Verify consumer identity
    const verified = await this.verifyConsumerIdentity(consumerId, verificationToken);

    if (!verified) {
      throw new Error('Identity verification failed');
    }

    const requestId = uuidv4();

    // Check for deletion exceptions
    const exceptions = await this.checkDeletionExceptions(consumerId);

    if (exceptions.length > 0) {
      logger.info('Deletion request denied - exceptions apply', {
        event: 'ccpa_deletion_denied',
        requestId,
        consumerId,
        exceptions,
        timestamp: new Date().toISOString()
      });

      return {
        status: 'denied',
        reason: 'Legal obligations require data retention',
        exceptions
      };
    }

    // Delete personal information
    await this.deleteConsumerData(consumerId, requestId);

    logger.warn('Consumer data deleted', {
      event: 'ccpa_data_deleted',
      requestId,
      consumerId,
      timestamp: new Date().toISOString()
    });

    return { status: 'completed', requestId };
  }

  async verifyConsumerIdentity(consumerId, verificationToken) {
    // Implementation: Multi-factor verification
    return true;
  }

  async checkDeletionExceptions(consumerId) {
    const exceptions = [];

    // Check for ongoing transactions
    const activeOrders = await db.collection('orders')
      .countDocuments({ userId: consumerId, status: 'pending' });

    if (activeOrders > 0) {
      exceptions.push({
        type: 'complete_transaction',
        description: 'Active orders pending completion'
      });
    }

    // Check for legal obligations
    const recentTransactions = await db.collection('transactions')
      .countDocuments({
        userId: consumerId,
        date: { $gte: new Date(Date.now() - 7 * 365 * 24 * 60 * 60 * 1000) }
      });

    if (recentTransactions > 0) {
      exceptions.push({
        type: 'legal_obligation',
        description: 'Tax and accounting retention (7 years)'
      });
    }

    return exceptions;
  }

  async deleteConsumerData(consumerId, requestId) {
    const collections = [
      'users',
      'preferences',
      'activity_logs',
      'location_data'
    ];

    for (const collection of collections) {
      await db.collection(collection).deleteMany({ userId: consumerId });
    }

    // Pseudonymize transaction data
    await db.collection('transactions').updateMany(
      { userId: consumerId },
      {
        $set: {
          userId: `DELETED_${requestId}`,
          userName: '[REDACTED]',
          userEmail: '[REDACTED]',
          deletionDate: new Date()
        }
      }
    );

    // Store deletion record
    await db.collection('ccpa_deletions').insertOne({
      requestId,
      consumerIdHash: require('crypto')
        .createHash('sha256')
        .update(consumerId)
        .digest('hex'),
      deletionDate: new Date(),
      collectionsDeleted: collections
    });
  }

  /**
   * Process Right to Opt-Out of Sale.
   *
   * CCPA §1798.120: Right to opt-out of sale
   */
  async processOptOutOfSale(consumerId) {
    await db.collection('users').updateOne(
      { userId: consumerId },
      {
        $set: {
          ccpaOptOutSale: true,
          optOutDate: new Date()
        }
      }
    );

    // Notify third parties to stop selling data
    await this.notifyThirdPartiesOptOut(consumerId);

    logger.info('Consumer opted out of sale', {
      event: 'ccpa_opt_out_sale',
      consumerId,
      timestamp: new Date().toISOString()
    });

    return { status: 'completed', optOutDate: new Date() };
  }

  async notifyThirdPartiesOptOut(consumerId) {
    const thirdParties = ['analytics_provider', 'ad_network'];

    for (const party of thirdParties) {
      // Implementation: API call to third party
      console.log(`Notifying ${party} of opt-out for consumer ${consumerId}`);
    }
  }

  /**
   * Implement "Do Not Sell My Personal Information" link.
   *
   * CCPA requirement: Provide clear opt-out mechanism
   */
  async handleDoNotSellRequest(consumerId, ipAddress) {
    // Log request
    logger.info('Do Not Sell request received', {
      event: 'do_not_sell_request',
      consumerId,
      ipAddress,
      timestamp: new Date().toISOString()
    });

    // Process opt-out
    await this.processOptOutOfSale(consumerId);

    // Set opt-out cookie
    return {
      optOutCookie: this.generateOptOutCookie(consumerId),
      message: 'You have been opted out of the sale of personal information'
    };
  }

  generateOptOutCookie(consumerId) {
    return {
      name: 'ccpa_opt_out',
      value: 'true',
      expires: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000), // 1 year
      httpOnly: true,
      secure: true
    };
  }

  /**
   * Process Right to Correct (CPRA).
   *
   * CPRA: Right to correct inaccurate personal information
   */
  async processRightToCorrect(consumerId, corrections) {
    const requestId = uuidv4();

    // Validate corrections
    const validatedCorrections = await this.validateCorrections(corrections);

    // Apply corrections
    for (const correction of validatedCorrections) {
      await db.collection('users').updateOne(
        { userId: consumerId },
        { $set: { [correction.field]: correction.newValue } }
      );
    }

    // Log correction
    await db.collection('ccpa_corrections').insertOne({
      requestId,
      consumerId,
      corrections: validatedCorrections,
      correctionDate: new Date()
    });

    logger.info('Personal information corrected', {
      event: 'ccpa_correction',
      requestId,
      consumerId,
      fieldCount: validatedCorrections.length,
      timestamp: new Date().toISOString()
    });

    return { requestId, status: 'completed' };
  }

  async validateCorrections(corrections) {
    // Validate correction requests
    return corrections.filter(c => c.field && c.newValue);
  }

  /**
   * Generate CCPA compliance report.
   */
  async generateComplianceReport(startDate, endDate) {
    const report = {
      reportId: uuidv4(),
      period: { startDate, endDate },
      generatedDate: new Date(),

      // Request statistics
      rightToKnowRequests: await db.collection('ccpa_disclosures')
        .countDocuments({ requestDate: { $gte: startDate, $lte: endDate } }),

      deletionRequests: await db.collection('ccpa_deletions')
        .countDocuments({ deletionDate: { $gte: startDate, $lte: endDate } }),

      optOutRequests: await db.collection('users')
        .countDocuments({
          ccpaOptOutSale: true,
          optOutDate: { $gte: startDate, $lte: endDate }
        }),

      correctionRequests: await db.collection('ccpa_corrections')
        .countDocuments({ correctionDate: { $gte: startDate, $lte: endDate } }),

      // Response times
      averageResponseTime: await this.calculateAverageResponseTime(startDate, endDate)
    };

    await db.collection('ccpa_reports').insertOne(report);

    return report;
  }

  async calculateAverageResponseTime(startDate, endDate) {
    // Implementation: Calculate average response time
    return 30; // days
  }
}

module.exports = CCPAComplianceManager;
```

---

## Success Criteria

- [ ] Right to Know requests processed within 45 days
- [ ] Right to Delete requests honored
- [ ] Opt-out mechanism operational
- [ ] "Do Not Sell" link prominently displayed
- [ ] Non-discrimination enforced
- [ ] CPRA corrections implemented

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
