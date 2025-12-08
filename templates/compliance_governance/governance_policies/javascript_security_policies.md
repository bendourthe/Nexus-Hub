---
template_id: compliance_governance_security_policies_javascript
template_name: Security Policies - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: governance_policies
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - governance_policies/README.md
  - compliance_frameworks/javascript_iso27001_implementation.md
related_templates:
  - governance_policies/javascript_access_control.md
tools:
  - joi (validation)
tags:
  - security-policies
  - policy-as-code
  - javascript
  - nodejs
---

# Security Policies - JavaScript

**Policy-as-code enforcement for security standards**

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Policy-as-Code

Convert security policies into executable code that automatically enforces compliance

### Key Policies

1. **Password Policy**
2. **Data Classification Policy**
3. **Access Control Policy**
4. **Encryption Policy**
5. **Acceptable Use Policy**

---

## Implementation

```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');
const Joi = require('joi');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'security-policies.log' })
  ]
});

class SecurityPolicyEnforcement {
  /**
   * Enforce password policy.
   *
   * ISO 27001 Control 5.17: Authentication information
   */
  enforcePasswordPolicy(password, user) {
    const violations = [];

    // Minimum length
    if (password.length < 12) {
      violations.push('Password must be at least 12 characters');
    }

    // Complexity requirements
    if (!/[A-Z]/.test(password)) {
      violations.push('Password must contain at least one uppercase letter');
    }

    if (!/[a-z]/.test(password)) {
      violations.push('Password must contain at least one lowercase letter');
    }

    if (!/[0-9]/.test(password)) {
      violations.push('Password must contain at least one number');
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      violations.push('Password must contain at least one special character');
    }

    // Check against common passwords
    if (this.isCommonPassword(password)) {
      violations.push('Password is too common');
    }

    // Check password history (prevent reuse)
    if (user.passwordHistory?.includes(this.hashPassword(password))) {
      violations.push('Cannot reuse previous 5 passwords');
    }

    const compliant = violations.length === 0;

    if (!compliant) {
      logger.warn('Password policy violation', {
        event: 'password_policy_violation',
        userId: user.userId,
        violations,
        timestamp: new Date().toISOString()
      });
    }

    return { compliant, violations };
  }

  /**
   * Check if password is in common password list.
   */
  isCommonPassword(password) {
    const commonPasswords = [
      'password', '123456', '12345678', 'qwerty', 'abc123',
      'password123', 'admin', 'letmein', 'welcome'
    ];

    return commonPasswords.includes(password.toLowerCase());
  }

  /**
   * Hash password for history comparison.
   */
  hashPassword(password) {
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(password).digest('hex');
  }

  /**
   * Enforce data classification policy.
   *
   * ISO 27001 Control 5.12: Classification of information
   */
  async enforceDataClassification(data, metadata) {
    const classification = this.classifyData(data);

    const requiredControls = this.getRequiredControls(classification);

    // Validate that required controls are applied
    const appliedControls = metadata.securityControls || [];

    const missingControls = requiredControls.filter(
      control => !appliedControls.includes(control)
    );

    if (missingControls.length > 0) {
      logger.warn('Data classification policy violation', {
        event: 'classification_violation',
        classification,
        missingControls,
        timestamp: new Date().toISOString()
      });

      throw new Error(
        `Data classified as ${classification} requires controls: ${missingControls.join(', ')}`
      );
    }

    return { classification, compliant: true };
  }

  /**
   * Classify data based on sensitivity.
   */
  classifyData(data) {
    const dataString = JSON.stringify(data).toLowerCase();

    // Check for highly sensitive data
    if (this.containsPII(dataString) || this.containsFinancialData(dataString)) {
      return 'confidential';
    }

    // Check for internal data
    if (this.containsBusinessData(dataString)) {
      return 'internal';
    }

    return 'public';
  }

  containsPII(dataString) {
    const piiPatterns = [
      /ssn|social security/,
      /passport/,
      /driver'?s? license/,
      /credit card/,
      /date of birth|dob/
    ];

    return piiPatterns.some(pattern => pattern.test(dataString));
  }

  containsFinancialData(dataString) {
    const financialPatterns = [
      /account number/,
      /routing number/,
      /bank account/,
      /payment/
    ];

    return financialPatterns.some(pattern => pattern.test(dataString));
  }

  containsBusinessData(dataString) {
    const businessPatterns = [
      /proprietary/,
      /confidential/,
      /internal use only/
    ];

    return businessPatterns.some(pattern => pattern.test(dataString));
  }

  /**
   * Get required security controls for classification level.
   */
  getRequiredControls(classification) {
    const controlMappings = {
      'public': [],
      'internal': ['access_control', 'audit_logging'],
      'confidential': ['encryption', 'access_control', 'audit_logging', 'mfa']
    };

    return controlMappings[classification] || [];
  }

  /**
   * Enforce encryption policy.
   *
   * ISO 27001 Control 8.24: Use of cryptography
   */
  validateEncryptionCompliance(data, encryptionMetadata) {
    const schema = Joi.object({
      algorithm: Joi.string().valid('AES-256-GCM', 'AES-256-CBC').required(),
      keyLength: Joi.number().min(256).required(),
      ivLength: Joi.number().min(128).required()
    });

    const validation = schema.validate(encryptionMetadata);

    if (validation.error) {
      logger.warn('Encryption policy violation', {
        event: 'encryption_violation',
        errors: validation.error.details,
        timestamp: new Date().toISOString()
      });

      return {
        compliant: false,
        violations: validation.error.details.map(d => d.message)
      };
    }

    return { compliant: true };
  }

  /**
   * Enforce acceptable use policy.
   *
   * ISO 27001 Control 5.10: Acceptable use of assets
   */
  async enforceAcceptableUse(userId, action, resource) {
    const prohibitedActions = [
      'cryptocurrency_mining',
      'unauthorized_data_export',
      'personal_use_excessive',
      'malware_distribution'
    ];

    if (prohibitedActions.includes(action)) {
      logger.error('Acceptable use policy violation', {
        event: 'acceptable_use_violation',
        userId,
        action,
        resource,
        timestamp: new Date().toISOString()
      });

      // Create policy violation record
      await this.createPolicyViolation(userId, 'acceptable_use', action);

      throw new Error(`Action ${action} violates acceptable use policy`);
    }

    return { compliant: true };
  }

  /**
   * Create policy violation record.
   */
  async createPolicyViolation(userId, policyType, details) {
    const violationId = uuidv4();

    await db.collection('policy_violations').insertOne({
      violationId,
      userId,
      policyType,
      details,
      createdDate: new Date(),
      status: 'open',
      reviewRequired: true
    });

    // Notify security team
    await this.notifySecurityTeam(violationId, userId, policyType);

    return violationId;
  }

  async notifySecurityTeam(violationId, userId, policyType) {
    // Implementation: Send alert to security team
    console.log(`Security alert: Policy violation ${violationId} by user ${userId}`);
  }

  /**
   * Generate policy compliance report.
   */
  async generateComplianceReport(startDate, endDate) {
    const violations = await db.collection('policy_violations')
      .find({
        createdDate: { $gte: startDate, $lte: endDate }
      })
      .toArray();

    const report = {
      reportId: uuidv4(),
      period: { startDate, endDate },
      generatedDate: new Date(),
      totalViolations: violations.length,
      violationsByType: this.groupBy(violations, 'policyType'),
      violationsByUser: this.groupBy(violations, 'userId'),
      topViolators: this.getTopViolators(violations, 10)
    };

    await db.collection('compliance_reports').insertOne(report);

    return report;
  }

  groupBy(array, key) {
    return array.reduce((result, item) => {
      const groupKey = item[key];
      result[groupKey] = (result[groupKey] || 0) + 1;
      return result;
    }, {});
  }

  getTopViolators(violations, limit) {
    const userCounts = {};

    violations.forEach(v => {
      userCounts[v.userId] = (userCounts[v.userId] || 0) + 1;
    });

    return Object.entries(userCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, limit)
      .map(([userId, count]) => ({ userId, violationCount: count }));
  }
}

module.exports = SecurityPolicyEnforcement;
```

---

## Success Criteria

- [ ] Password policy enforced automatically
- [ ] Data classification policy operational
- [ ] Encryption policy validated
- [ ] Acceptable use policy monitored
- [ ] Policy violations tracked and remediated
- [ ] Compliance reports generated monthly

---

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
