---
template_id: compliance_governance_pci_dss_javascript
template_name: PCI-DSS Compliance - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - compliance_frameworks/javascript_iso27001_implementation.md
related_templates:
  - governance_policies/javascript_security_policies.md
tools:
  - helmet (security headers)
  - express-rate-limit (rate limiting)
tags:
  - pci-dss
  - payment-security
  - cardholder-data
  - javascript
  - nodejs
---

# PCI-DSS v4.0 Compliance - JavaScript

**Payment Card Industry Data Security Standard implementation**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### PCI-DSS Requirements

**12 Requirements across 6 Goals**:

1. Install and maintain network security controls
2. Apply secure configurations
3. Protect stored cardholder data
4. Protect cardholder data with strong cryptography in transit
5. Protect systems from malware
6. Develop and maintain secure systems
7. Restrict access to cardholder data
8. Identify users and authenticate access
9. Restrict physical access
10. Log and monitor access
11. Test security systems regularly
12. Support information security with policies

**Key Principle**: Minimize cardholder data storage

---

## Implementation

```javascript
const { v4: uuidv4 } = require('uuid');
const crypto = require('crypto');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'pci-dss-audit.log' })
  ]
});

class PCIDSSCompliance {
  /**
   * Requirement 3: Protect stored cardholder data
   *
   * NOTE: Best practice is to NOT store cardholder data
   * Use tokenization instead (Stripe, PayPal tokens)
   */

  /**
   * Tokenize payment card (DO NOT store actual PAN).
   *
   * PCI-DSS 3.4: Render PAN unreadable
   */
  async tokenizePaymentCard(customerId, cardDetails) {
    // In production: Use payment processor (Stripe, Adyen)
    // This is a simplified example

    const tokenId = uuidv4();

    // Hash PAN for lookup (one-way hash, not encryption)
    const panHash = crypto
      .createHash('sha256')
      .update(cardDetails.pan)
      .digest('hex');

    // Store only: token, last 4 digits, brand, expiry
    const tokenRecord = {
      tokenId,
      customerId,
      panHash,         // For duplicate detection
      last4: cardDetails.pan.slice(-4),
      brand: cardDetails.brand,
      expiryMonth: cardDetails.expiryMonth,
      expiryYear: cardDetails.expiryYear,
      createdDate: new Date(),

      // NEVER store: full PAN, CVV, PIN
      // fullPAN: cardDetails.pan  ← NEVER DO THIS
    };

    await db.collection('payment_tokens').insertOne(tokenRecord);

    logger.info('Payment card tokenized', {
      event: 'card_tokenized',
      tokenId,
      customerId,
      last4: tokenRecord.last4,
      timestamp: new Date().toISOString()
    });

    return tokenId;
  }

  /**
   * Requirement 8: Identify users and authenticate access.
   *
   * PCI-DSS 8.3: Secure all individual non-console admin access
   */
  async enforceAdminMFA(userId, action) {
    const user = await db.collection('users').findOne({ userId });

    // Check if user is admin accessing cardholder data environment
    if (this.isAdminUser(user) && this.accessesCDE(action)) {
      if (!user.mfaEnabled) {
        logger.error('MFA required for admin access', {
          event: 'mfa_required',
          userId,
          action,
          timestamp: new Date().toISOString()
        });

        throw new Error('Multi-factor authentication required for admin access to CDE');
      }

      // Verify MFA token
      const mfaVerified = await this.verifyMFAToken(userId);

      if (!mfaVerified) {
        throw new Error('MFA verification failed');
      }
    }

    return true;
  }

  isAdminUser(user) {
    return user.roles?.includes('admin') || user.roles?.includes('superadmin');
  }

  accessesCDE(action) {
    // Cardholder Data Environment actions
    const cdeActions = [
      'access_payment_data',
      'access_transaction_logs',
      'manage_payment_tokens'
    ];

    return cdeActions.includes(action);
  }

  async verifyMFAToken(userId) {
    // Implementation: Verify TOTP token
    return true;
  }

  /**
   * Requirement 10: Log and monitor all access.
   *
   * PCI-DSS 10.2: Implement automated audit trails
   */
  async logCardholderDataAccess(userId, action, resourceId, result) {
    const auditLog = {
      logId: uuidv4(),
      timestamp: new Date(),
      userId,
      action,
      resourceId,
      result, // 'success' | 'failure'
      ipAddress: this.getCurrentIP(),
      userAgent: this.getCurrentUserAgent(),

      // PCI-DSS 10.2 required fields
      userIdentification: userId,
      typeOfEvent: action,
      dateAndTime: new Date(),
      successOrFailure: result,
      originationOfEvent: 'application',
      identityOfAffectedData: resourceId
    };

    await db.collection('pci_audit_logs').insertOne(auditLog);

    logger.info('Cardholder data access logged', {
      event: 'chd_access_logged',
      logId: auditLog.logId,
      userId,
      action,
      result,
      timestamp: new Date().toISOString()
    });

    // Alert on failed access
    if (result === 'failure') {
      await this.alertSecurityTeam(auditLog);
    }
  }

  getCurrentIP() {
    // Implementation: Get client IP
    return '0.0.0.0';
  }

  getCurrentUserAgent() {
    // Implementation: Get user agent
    return 'Node.js Application';
  }

  async alertSecurityTeam(auditLog) {
    // Implementation: Send alert for failed access
    console.log(`Security alert: Failed CDE access by ${auditLog.userId}`);
  }

  /**
   * Requirement 11: Test security regularly.
   *
   * PCI-DSS 11.3.1: Perform external penetration testing
   */
  async scheduleSecurityTesting() {
    const testId = uuidv4();

    const securityTest = {
      testId,
      testType: 'penetration_test',
      scheduledDate: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000), // 90 days
      frequency: 'quarterly',
      scope: 'Cardholder Data Environment',
      status: 'scheduled'
    };

    await db.collection('security_tests').insertOne(securityTest);

    logger.info('Security test scheduled', {
      event: 'security_test_scheduled',
      testId,
      testType: securityTest.testType,
      scheduledDate: securityTest.scheduledDate.toISOString(),
      timestamp: new Date().toISOString()
    });

    return testId;
  }

  /**
   * Requirement 6: Develop and maintain secure systems.
   *
   * PCI-DSS 6.2: Protect public-facing web applications
   */
  applySecurityHeaders() {
    // Express.js middleware for security headers
    const helmet = require('helmet');

    return helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          imgSrc: ["'self'", 'data:', 'https:'],
          connectSrc: ["'self'"],
          fontSrc: ["'self'"],
          objectSrc: ["'none'"],
          mediaSrc: ["'self'"],
          frameSrc: ["'none'"]
        }
      },
      hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true
      },
      noSniff: true,
      xssFilter: true,
      hidePoweredBy: true
    });
  }

  /**
   * Implement rate limiting to prevent brute force.
   *
   * PCI-DSS 8.2.5: Do not allow invalid authentication after 6 attempts
   */
  applyRateLimiting() {
    const rateLimit = require('express-rate-limit');

    return rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 6, // 6 attempts
      message: 'Too many authentication attempts, please try again later',
      standardHeaders: true,
      legacyHeaders: false,
      handler: (req, res) => {
        logger.warn('Rate limit exceeded', {
          event: 'rate_limit_exceeded',
          ip: req.ip,
          timestamp: new Date().toISOString()
        });

        res.status(429).json({
          error: 'Too many requests',
          message: 'Account locked for 15 minutes due to multiple failed attempts'
        });
      }
    });
  }

  /**
   * Generate PCI-DSS compliance report.
   */
  async generateComplianceReport(quarter, year) {
    const startDate = new Date(year, (quarter - 1) * 3, 1);
    const endDate = new Date(year, quarter * 3, 0);

    const report = {
      reportId: uuidv4(),
      quarter,
      year,
      generatedDate: new Date(),

      // Requirement 10: Audit logs
      totalAuditLogs: await db.collection('pci_audit_logs')
        .countDocuments({ timestamp: { $gte: startDate, $lte: endDate } }),

      failedAccessAttempts: await db.collection('pci_audit_logs')
        .countDocuments({
          timestamp: { $gte: startDate, $lte: endDate },
          result: 'failure'
        }),

      // Requirement 11: Security testing
      securityTestsCompleted: await db.collection('security_tests')
        .countDocuments({
          scheduledDate: { $gte: startDate, $lte: endDate },
          status: 'completed'
        }),

      // Requirement 8: User access
      adminMFAEnrollment: await this.calculateMFAEnrollment(),

      // Compliance status
      compliant: true,
      nonCompliantItems: []
    };

    await db.collection('pci_compliance_reports').insertOne(report);

    return report;
  }

  async calculateMFAEnrollment() {
    const admins = await db.collection('users')
      .find({ roles: { $in: ['admin', 'superadmin'] } })
      .toArray();

    const mfaEnabled = admins.filter(u => u.mfaEnabled).length;

    return {
      total: admins.length,
      enrolled: mfaEnabled,
      percentage: (mfaEnabled / admins.length * 100).toFixed(2)
    };
  }
}

module.exports = PCIDSSCompliance;
```

---

## Success Criteria

- [ ] Cardholder data NOT stored (use tokenization)
- [ ] Admin MFA enforced for CDE access
- [ ] All cardholder data access logged
- [ ] Security headers implemented
- [ ] Rate limiting prevents brute force
- [ ] Quarterly penetration tests scheduled
- [ ] Compliance reports generated

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
