---
template_id: compliance_governance_iso27001_javascript
template_name: ISO 27001 Implementation - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/javascript_soc2_compliance.md
related_templates:
  - risk_management/javascript_risk_assessment.md
  - governance_policies/javascript_security_policies.md
tools:
  - helmet (security headers)
  - express-rate-limit (rate limiting)
  - jsonwebtoken (JWT)
tags:
  - iso27001
  - isms
  - information-security
  - javascript
  - nodejs
---

# ISO 27001:2022 Implementation - JavaScript

**Information Security Management System for Node.js applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### ISO 27001:2022 Structure

**4 Themes**:
1. **Organizational Controls** (37 controls)
2. **People Controls** (8 controls)
3. **Physical Controls** (14 controls)
4. **Technological Controls** (34 controls)

**Total**: 93 controls (previously 114 in Annex A)

### Implementation Approach

This template focuses on **Technological Controls** implementable in Node.js code.

---

## Control 8.2: Privileged Access Rights

**Objective**: Restrict and control privileged access

```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'privileged-access.log' })
  ]
});

const PrivilegeLevel = {
  STANDARD: 'standard',
  ELEVATED: 'elevated',
  ADMIN: 'admin',
  SUPERADMIN: 'superadmin'
};

class PrivilegedAccessManager {
  /**
   * Request temporary privilege elevation (Just-in-Time access).
   *
   * ISO 27001 Control 8.2: Privileged access management
   */
  async requestPrivilegeElevation(userId, requestedLevel, justification, durationHours = 4) {
    if (durationHours > 8) {
      throw new Error('Maximum elevation period is 8 hours');
    }

    const requestId = uuidv4();
    const expiresAt = new Date(Date.now() + durationHours * 60 * 60 * 1000);

    await db.collection('privilege_requests').insertOne({
      requestId,
      userId,
      requestedLevel,
      justification,
      requestedAt: new Date(),
      expiresAt,
      status: 'pending_approval',
      approvedBy: null
    });

    logger.warn('Privilege elevation requested', {
      event: 'privilege_elevation_request',
      requestId,
      userId,
      requestedLevel,
      justification,
      durationHours,
      timestamp: new Date().toISOString()
    });

    // Notify approvers
    await this.notifyApprovers(requestId, userId, requestedLevel);

    return { requestId, status: 'pending_approval' };
  }

  /**
   * Approve privilege elevation request.
   *
   * ISO 27001 Control 8.2: Approval workflow
   */
  async approveElevation(requestId, approverId) {
    const request = await db.collection('privilege_requests').findOne({ requestId });

    if (!request) {
      throw new Error('Request not found');
    }

    if (request.status !== 'pending_approval') {
      throw new Error('Request already processed');
    }

    // Grant temporary privileges
    await db.collection('privilege_requests').updateOne(
      { requestId },
      {
        $set: {
          status: 'approved',
          approvedBy: approverId,
          approvedAt: new Date()
        }
      }
    );

    await db.collection('users').updateOne(
      { userId: request.userId },
      {
        $set: {
          temporaryPrivilege: request.requestedLevel,
          privilegeExpiresAt: request.expiresAt
        }
      }
    );

    logger.warn('Privilege elevation approved', {
      event: 'privilege_elevation_approved',
      requestId,
      userId: request.userId,
      requestedLevel: request.requestedLevel,
      approverId,
      expiresAt: request.expiresAt.toISOString()
    });

    return { status: 'approved', expiresAt: request.expiresAt };
  }

  /**
   * Automatically revoke expired privileges.
   *
   * ISO 27001 Control 8.2: Time-limited access
   */
  async revokeExpiredPrivileges() {
    const expiredUsers = await db.collection('users').find({
      privilegeExpiresAt: { $lte: new Date() },
      temporaryPrivilege: { $exists: true }
    }).toArray();

    for (const user of expiredUsers) {
      await db.collection('users').updateOne(
        { userId: user.userId },
        {
          $unset: {
            temporaryPrivilege: '',
            privilegeExpiresAt: ''
          }
        }
      );

      logger.info('Temporary privilege revoked', {
        event: 'privilege_revoked',
        userId: user.userId,
        previousLevel: user.temporaryPrivilege
      });
    }

    return { revokedCount: expiredUsers.length };
  }

  /**
   * Check if user has required privilege level.
   */
  async hasPrivilege(userId, requiredLevel) {
    const user = await db.collection('users').findOne({ userId });

    if (!user) return false;

    // Check permanent role
    const privilegeLevels = [
      PrivilegeLevel.STANDARD,
      PrivilegeLevel.ELEVATED,
      PrivilegeLevel.ADMIN,
      PrivilegeLevel.SUPERADMIN
    ];

    const userPermanentLevel = privilegeLevels.indexOf(user.role || PrivilegeLevel.STANDARD);
    const requiredLevelIndex = privilegeLevels.indexOf(requiredLevel);

    if (userPermanentLevel >= requiredLevelIndex) {
      return true;
    }

    // Check temporary elevation
    if (user.temporaryPrivilege && user.privilegeExpiresAt > new Date()) {
      const tempLevelIndex = privilegeLevels.indexOf(user.temporaryPrivilege);
      return tempLevelIndex >= requiredLevelIndex;
    }

    return false;
  }

  async notifyApprovers(requestId, userId, requestedLevel) {
    // Implementation: Send notifications to managers/admins
    const approvers = await db.collection('users').find({
      role: { $in: [PrivilegeLevel.ADMIN, PrivilegeLevel.SUPERADMIN] }
    }).toArray();

    // Send email/Slack notifications
    console.log(`Notifying ${approvers.length} approvers for request ${requestId}`);
  }
}

module.exports = PrivilegedAccessManager;
```

---

## Control 8.5: Secure Authentication

**Objective**: Implement secure authentication mechanisms

```javascript
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

class SecureAuthenticationManager {
  constructor() {
    this.SALT_ROUNDS = 12;
    this.JWT_SECRET = process.env.JWT_SECRET;
    this.JWT_EXPIRY = '1h';
    this.REFRESH_TOKEN_EXPIRY = '7d';
  }

  /**
   * Register user with secure password hashing.
   *
   * ISO 27001 Control 8.5: Password protection
   */
  async registerUser(email, password) {
    // Validate password strength
    this.validatePasswordStrength(password);

    // Hash password with bcrypt
    const passwordHash = await bcrypt.hash(password, this.SALT_ROUNDS);

    const userId = uuidv4();

    await db.collection('users').insertOne({
      userId,
      email,
      passwordHash,
      mfaEnabled: false,
      accountLocked: false,
      failedLoginAttempts: 0,
      createdAt: new Date()
    });

    logger.info('User registered', {
      event: 'user_registration',
      userId,
      email,
      timestamp: new Date().toISOString()
    });

    return { userId, email };
  }

  /**
   * Authenticate user with secure password verification.
   *
   * ISO 27001 Control 8.5: Authentication
   */
  async authenticateUser(email, password) {
    const user = await db.collection('users').findOne({ email });

    if (!user) {
      logger.warn('Authentication failed - user not found', {
        event: 'authentication_failed',
        email,
        reason: 'user_not_found'
      });
      // Return generic error to prevent user enumeration
      throw new Error('Invalid credentials');
    }

    // Check if account is locked
    if (user.accountLocked) {
      logger.warn('Authentication blocked - account locked', {
        event: 'authentication_blocked',
        userId: user.userId,
        reason: 'account_locked'
      });
      throw new Error('Account locked due to security reasons');
    }

    // Verify password
    const passwordValid = await bcrypt.compare(password, user.passwordHash);

    if (!passwordValid) {
      // Increment failed attempts
      await this.recordFailedLogin(user.userId);

      logger.warn('Authentication failed - invalid password', {
        event: 'authentication_failed',
        userId: user.userId,
        failedAttempts: user.failedLoginAttempts + 1
      });

      throw new Error('Invalid credentials');
    }

    // Reset failed attempts on successful login
    await db.collection('users').updateOne(
      { userId: user.userId },
      {
        $set: {
          failedLoginAttempts: 0,
          lastLoginAt: new Date()
        }
      }
    );

    // Generate JWT tokens
    const accessToken = this.generateAccessToken(user.userId, user.email);
    const refreshToken = this.generateRefreshToken(user.userId);

    // Store refresh token
    await this.storeRefreshToken(user.userId, refreshToken);

    logger.info('Authentication successful', {
      event: 'authentication_success',
      userId: user.userId
    });

    return {
      accessToken,
      refreshToken,
      userId: user.userId,
      mfaRequired: user.mfaEnabled
    };
  }

  /**
   * Validate password strength.
   *
   * ISO 27001 Control 8.5: Password policy
   */
  validatePasswordStrength(password) {
    const errors = [];

    if (password.length < 12) {
      errors.push('Password must be at least 12 characters');
    }

    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain uppercase letter');
    }

    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain lowercase letter');
    }

    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain number');
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      errors.push('Password must contain special character');
    }

    if (errors.length > 0) {
      throw new Error(`Password requirements not met: ${errors.join(', ')}`);
    }
  }

  /**
   * Record failed login attempt.
   */
  async recordFailedLogin(userId) {
    const result = await db.collection('users').findOneAndUpdate(
      { userId },
      { $inc: { failedLoginAttempts: 1 } },
      { returnDocument: 'after' }
    );

    // Lock account after 5 failed attempts
    if (result.value.failedLoginAttempts >= 5) {
      await db.collection('users').updateOne(
        { userId },
        {
          $set: {
            accountLocked: true,
            lockedAt: new Date()
          }
        }
      );

      logger.warn('Account locked due to failed attempts', {
        event: 'account_locked',
        userId,
        failedAttempts: result.value.failedLoginAttempts
      });
    }
  }

  /**
   * Generate JWT access token.
   */
  generateAccessToken(userId, email) {
    return jwt.sign(
      { userId, email, type: 'access' },
      this.JWT_SECRET,
      { expiresIn: this.JWT_EXPIRY }
    );
  }

  /**
   * Generate refresh token.
   */
  generateRefreshToken(userId) {
    return jwt.sign(
      { userId, type: 'refresh' },
      this.JWT_SECRET,
      { expiresIn: this.REFRESH_TOKEN_EXPIRY }
    );
  }

  /**
   * Store refresh token in database.
   */
  async storeRefreshToken(userId, token) {
    const tokenHash = require('crypto')
      .createHash('sha256')
      .update(token)
      .digest('hex');

    await db.collection('refresh_tokens').insertOne({
      tokenId: uuidv4(),
      userId,
      tokenHash,
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
    });
  }
}

module.exports = SecureAuthenticationManager;
```

---

## Control 8.9: Configuration Management

**Objective**: Manage and control system configurations

```javascript
class ConfigurationManager {
  /**
   * Track configuration changes.
   *
   * ISO 27001 Control 8.9: Configuration management
   */
  async updateConfiguration(configKey, newValue, changedBy) {
    const currentConfig = await db.collection('configurations').findOne({ key: configKey });

    const changeId = uuidv4();

    // Record change history
    await db.collection('config_history').insertOne({
      changeId,
      configKey,
      oldValue: currentConfig?.value,
      newValue,
      changedBy,
      changedAt: new Date(),
      reason: 'Configuration update'
    });

    // Update configuration
    await db.collection('configurations').updateOne(
      { key: configKey },
      {
        $set: {
          value: newValue,
          lastModifiedBy: changedBy,
          lastModifiedAt: new Date()
        }
      },
      { upsert: true }
    );

    logger.warn('Configuration changed', {
      event: 'configuration_change',
      changeId,
      configKey,
      changedBy,
      timestamp: new Date().toISOString()
    });

    return { changeId, status: 'applied' };
  }

  /**
   * Audit configuration baseline.
   *
   * ISO 27001 Control 8.9: Configuration auditing
   */
  async auditConfiguration() {
    const expectedConfig = this.getExpectedConfiguration();
    const currentConfig = await this.getCurrentConfiguration();

    const deviations = [];

    for (const [key, expectedValue] of Object.entries(expectedConfig)) {
      const currentValue = currentConfig[key];

      if (currentValue !== expectedValue) {
        deviations.push({
          configKey: key,
          expected: expectedValue,
          actual: currentValue,
          severity: this.assessDeviation(key, expectedValue, currentValue)
        });
      }
    }

    if (deviations.length > 0) {
      logger.warn('Configuration deviations detected', {
        event: 'configuration_drift',
        deviationCount: deviations.length,
        deviations
      });
    }

    return {
      compliant: deviations.length === 0,
      deviations
    };
  }

  getExpectedConfiguration() {
    return {
      'security.mfa_required': true,
      'security.session_timeout_minutes': 30,
      'security.password_min_length': 12,
      'security.tls_version': '1.3'
    };
  }

  async getCurrentConfiguration() {
    const configs = await db.collection('configurations').find({}).toArray();
    return configs.reduce((acc, config) => {
      acc[config.key] = config.value;
      return acc;
    }, {});
  }

  assessDeviation(key, expected, actual) {
    if (key.startsWith('security.')) {
      return 'high';
    }
    return 'medium';
  }
}

module.exports = ConfigurationManager;
```

---

## Control 8.16: Monitoring Activities

**Objective**: Monitor networks, systems, and applications for anomalous behavior

```javascript
const prometheus = require('prom-client');

class SecurityMonitoringManager {
  constructor() {
    this.anomalyCounter = new prometheus.Counter({
      name: 'security_anomalies_total',
      help: 'Total security anomalies detected',
      labelNames: ['anomaly_type']
    });
  }

  /**
   * Detect anomalous authentication patterns.
   *
   * ISO 27001 Control 8.16: Anomaly detection
   */
  async detectAuthenticationAnomalies(userId) {
    const recentLogins = await db.collection('auth_logs')
      .find({ userId })
      .sort({ timestamp: -1 })
      .limit(10)
      .toArray();

    const anomalies = [];

    // Check for unusual login times
    const unusualTime = this.detectUnusualLoginTime(recentLogins);
    if (unusualTime) {
      anomalies.push(unusualTime);
    }

    // Check for geolocation anomalies
    const geoAnomaly = this.detectGeolocationAnomaly(recentLogins);
    if (geoAnomaly) {
      anomalies.push(geoAnomaly);
    }

    // Check for rapid successive logins
    const rapidLogins = this.detectRapidLogins(recentLogins);
    if (rapidLogins) {
      anomalies.push(rapidLogins);
    }

    if (anomalies.length > 0) {
      logger.warn('Authentication anomalies detected', {
        event: 'authentication_anomaly',
        userId,
        anomalies,
        timestamp: new Date().toISOString()
      });

      this.anomalyCounter.inc({ anomaly_type: 'authentication' });

      // Create security incident
      await this.createSecurityIncident(userId, 'authentication_anomaly', anomalies);
    }

    return { anomaliesDetected: anomalies.length > 0, anomalies };
  }

  detectUnusualLoginTime(logins) {
    if (logins.length < 5) return null;

    const currentLogin = logins[0];
    const hour = new Date(currentLogin.timestamp).getHours();

    // Unusual if login between 2 AM - 5 AM
    if (hour >= 2 && hour <= 5) {
      return {
        type: 'unusual_time',
        description: 'Login during unusual hours',
        hour
      };
    }

    return null;
  }

  detectGeolocationAnomaly(logins) {
    if (logins.length < 2) return null;

    const [current, previous] = logins;

    // Check if location changed significantly
    const distance = this.calculateDistance(
      current.location,
      previous.location
    );

    const timeDiff = (new Date(current.timestamp) - new Date(previous.timestamp)) / 1000 / 60; // minutes

    // Impossible travel: 500km in less than 1 hour
    if (distance > 500 && timeDiff < 60) {
      return {
        type: 'impossible_travel',
        description: 'Login from geographically distant location',
        distance,
        timeDiff
      };
    }

    return null;
  }

  detectRapidLogins(logins) {
    if (logins.length < 3) return null;

    const [first, second, third] = logins;

    const diff1 = (new Date(first.timestamp) - new Date(second.timestamp)) / 1000;
    const diff2 = (new Date(second.timestamp) - new Date(third.timestamp)) / 1000;

    // 3 logins within 10 seconds
    if (diff1 < 10 && diff2 < 10) {
      return {
        type: 'rapid_logins',
        description: 'Multiple rapid login attempts',
        count: 3,
        timeWindow: diff1 + diff2
      };
    }

    return null;
  }

  calculateDistance(loc1, loc2) {
    // Haversine formula for distance calculation
    // Simplified for demonstration
    return 100; // km
  }

  async createSecurityIncident(userId, incidentType, details) {
    const incidentId = uuidv4();

    await db.collection('security_incidents').insertOne({
      incidentId,
      userId,
      incidentType,
      details,
      severity: 'medium',
      status: 'open',
      createdAt: new Date()
    });

    return incidentId;
  }
}

module.exports = SecurityMonitoringManager;
```

---

## Success Criteria

- [ ] Privileged access requires justification and approval
- [ ] Temporary privileges automatically revoked after expiration
- [ ] Password policy enforced (12+ chars, complexity)
- [ ] Account lockout after 5 failed login attempts
- [ ] Configuration changes audited and logged
- [ ] Authentication anomalies detected and alerted
- [ ] All security events logged with structured data
- [ ] Compliance reports generated for auditors

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
