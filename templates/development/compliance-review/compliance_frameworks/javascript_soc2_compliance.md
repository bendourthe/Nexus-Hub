---
template_id: compliance_governance_soc2_compliance_javascript
template_name: SOC 2 Type II Compliance - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - compliance_frameworks/README.md
related_templates:
  - compliance_frameworks/javascript_iso27001_implementation.md
  - ai_agent_governance/javascript_agent_observability.md
tools:
  - helmet (security headers)
  - winston (logging)
  - passport (authentication)
tags:
  - soc2
  - trust-service-criteria
  - compliance
  - javascript
  - nodejs
---

# SOC 2 Type II Compliance - JavaScript

**Implement Trust Service Criteria for Node.js applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### What is SOC 2 Type II?

**SOC 2** = Service Organization Control 2 report demonstrating security controls

**Type II** = Auditor tests controls over time (6-12 months), not just design

### Trust Service Criteria

1. **Security (CC)** - Common Criteria (required)
2. **Availability** - System uptime/performance
3. **Confidentiality** - Sensitive data protection
4. **Processing Integrity** - Accurate processing
5. **Privacy** - Personal information protection

### Why Node.js Applications Need SOC 2

- **Customer Requirements**: Enterprise contracts require SOC 2
- **Risk Management**: Demonstrates security maturity
- **Competitive Advantage**: Trust signal for B2B SaaS
- **Insurance**: Lower cyber insurance premiums

---

## Common Criteria Implementation

### CC6.1: Logical Access Controls

**Control Objective**: Restrict logical access through authentication and authorization

#### Multi-Factor Authentication

```javascript
// Multi-factor authentication with TOTP
const speakeasy = require('speakeasy');
const QRCode = require('qrcode');
const winston = require('winston');

// Configure audit logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'audit.log' })
  ]
});

class MFAManager {
  /**
   * Generate MFA secret for user enrollment.
   *
   * SOC 2 Control: CC6.1 - Multi-factor authentication
   */
  async enrollUser(userId, userEmail) {
    const secret = speakeasy.generateSecret({
      name: `YourApp (${userEmail})`,
      length: 32
    });

    // Store secret encrypted in database
    await db.collection('users').updateOne(
      { userId },
      {
        $set: {
          mfaSecret: this.encryptSecret(secret.base32),
          mfaEnabled: false,
          mfaEnrolledAt: new Date()
        }
      }
    );

    // Generate QR code for authenticator app
    const qrCodeUrl = await QRCode.toDataURL(secret.otpauth_url);

    logger.info('MFA enrollment initiated', {
      event: 'mfa_enrollment',
      userId,
      timestamp: new Date().toISOString()
    });

    return {
      secret: secret.base32,
      qrCode: qrCodeUrl
    };
  }

  /**
   * Verify MFA token during login.
   *
   * SOC 2 Control: CC6.1 - Authentication verification
   */
  async verifyToken(userId, token) {
    const user = await db.collection('users').findOne({ userId });

    if (!user || !user.mfaEnabled) {
      return { valid: false, reason: 'MFA not enabled' };
    }

    const decryptedSecret = this.decryptSecret(user.mfaSecret);

    const isValid = speakeasy.totp.verify({
      secret: decryptedSecret,
      encoding: 'base32',
      token: token,
      window: 1 // Allow 30 seconds time drift
    });

    logger.info('MFA verification attempt', {
      event: 'mfa_verification',
      userId,
      success: isValid,
      timestamp: new Date().toISOString(),
      ipAddress: this.getCurrentIP()
    });

    // Track failed attempts
    if (!isValid) {
      await this.recordFailedAttempt(userId);
    }

    return { valid: isValid };
  }

  /**
   * Encrypt MFA secret for storage.
   */
  encryptSecret(secret) {
    const crypto = require('crypto');
    const algorithm = 'aes-256-gcm';
    const key = Buffer.from(process.env.ENCRYPTION_KEY, 'hex');
    const iv = crypto.randomBytes(16);

    const cipher = crypto.createCipheriv(algorithm, key, iv);
    let encrypted = cipher.update(secret, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    return {
      encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex')
    };
  }

  /**
   * Decrypt MFA secret from storage.
   */
  decryptSecret(encryptedData) {
    const crypto = require('crypto');
    const algorithm = 'aes-256-gcm';
    const key = Buffer.from(process.env.ENCRYPTION_KEY, 'hex');

    const decipher = crypto.createDecipheriv(
      algorithm,
      key,
      Buffer.from(encryptedData.iv, 'hex')
    );

    decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));

    let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }

  /**
   * Track failed MFA attempts for security monitoring.
   */
  async recordFailedAttempt(userId) {
    await db.collection('failed_mfa_attempts').insertOne({
      userId,
      timestamp: new Date(),
      ipAddress: this.getCurrentIP()
    });

    // Check for brute force attack
    const recentAttempts = await db.collection('failed_mfa_attempts')
      .countDocuments({
        userId,
        timestamp: { $gte: new Date(Date.now() - 15 * 60 * 1000) }
      });

    if (recentAttempts >= 5) {
      logger.warn('Potential MFA brute force attack', {
        event: 'mfa_brute_force',
        userId,
        attemptCount: recentAttempts
      });

      // Lock account temporarily
      await this.lockAccount(userId, 30); // 30 minutes
    }
  }

  getCurrentIP() {
    // Implementation depends on Express/Fastify context
    return '0.0.0.0';
  }

  async lockAccount(userId, minutes) {
    await db.collection('users').updateOne(
      { userId },
      {
        $set: {
          accountLocked: true,
          lockedUntil: new Date(Date.now() + minutes * 60 * 1000)
        }
      }
    );
  }
}

module.exports = MFAManager;
```

### CC6.7: Encryption of Confidential Data

**Control Objective**: Protect confidential data at rest and in transit

#### Data Encryption Manager

```javascript
const crypto = require('crypto');

class DataEncryptionManager {
  /**
   * Encrypt sensitive data at rest.
   *
   * SOC 2 Control: CC6.7 - Data encryption at rest
   * Standard: AES-256-GCM
   */
  encryptData(plaintext, context = {}) {
    const algorithm = 'aes-256-gcm';
    const key = Buffer.from(process.env.DATA_ENCRYPTION_KEY, 'hex');
    const iv = crypto.randomBytes(16);

    // Add context for authenticated encryption
    const aad = Buffer.from(JSON.stringify(context));

    const cipher = crypto.createCipheriv(algorithm, key, iv);
    cipher.setAAD(aad);

    let encrypted = cipher.update(plaintext, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    logger.info('Data encrypted', {
      event: 'data_encryption',
      context,
      algorithm: 'AES-256-GCM',
      timestamp: new Date().toISOString()
    });

    return {
      ciphertext: encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex'),
      algorithm,
      context
    };
  }

  /**
   * Decrypt sensitive data.
   *
   * SOC 2 Control: CC6.7 - Secure decryption
   */
  decryptData(encryptedData) {
    const key = Buffer.from(process.env.DATA_ENCRYPTION_KEY, 'hex');
    const iv = Buffer.from(encryptedData.iv, 'hex');

    const aad = Buffer.from(JSON.stringify(encryptedData.context || {}));

    const decipher = crypto.createDecipheriv(encryptedData.algorithm, key, iv);
    decipher.setAAD(aad);
    decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));

    let decrypted = decipher.update(encryptedData.ciphertext, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    logger.info('Data decrypted', {
      event: 'data_decryption',
      context: encryptedData.context,
      timestamp: new Date().toISOString()
    });

    return decrypted;
  }

  /**
   * Encrypt database fields automatically.
   */
  async encryptDatabaseField(collection, documentId, fieldName, value) {
    const context = {
      collection,
      documentId,
      fieldName
    };

    const encrypted = this.encryptData(value, context);

    await db.collection(collection).updateOne(
      { _id: documentId },
      {
        $set: {
          [fieldName]: encrypted,
          [`${fieldName}_encrypted`]: true
        }
      }
    );

    return encrypted;
  }
}

module.exports = DataEncryptionManager;
```

### CC7.2: System Monitoring

**Control Objective**: Monitor system components and security events

#### Security Event Monitoring

```javascript
const winston = require('winston');
const prometheus = require('prom-client');

class SecurityMonitoring {
  constructor() {
    // Prometheus metrics
    this.securityEventsCounter = new prometheus.Counter({
      name: 'security_events_total',
      help: 'Total security events by type',
      labelNames: ['event_type', 'severity']
    });

    this.authenticationAttemptsCounter = new prometheus.Counter({
      name: 'authentication_attempts_total',
      help: 'Total authentication attempts',
      labelNames: ['result']
    });

    // Winston structured logging
    this.logger = winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      ),
      transports: [
        new winston.transports.File({ filename: 'security-events.log' }),
        new winston.transports.File({
          filename: 'critical-security.log',
          level: 'error'
        })
      ]
    });
  }

  /**
   * Log security event with structured data.
   *
   * SOC 2 Control: CC7.2 - Security event logging
   */
  logSecurityEvent(eventType, severity, details) {
    const event = {
      event: eventType,
      severity,
      timestamp: new Date().toISOString(),
      ...details
    };

    this.logger.log(severity, `Security event: ${eventType}`, event);

    this.securityEventsCounter.inc({
      event_type: eventType,
      severity
    });

    // Alert on critical events
    if (severity === 'critical') {
      this.sendSecurityAlert(event);
    }
  }

  /**
   * Monitor authentication attempts.
   *
   * SOC 2 Control: CC6.1 - Authentication monitoring
   */
  logAuthenticationAttempt(userId, result, details = {}) {
    const event = {
      event: 'authentication_attempt',
      userId,
      result, // 'success' | 'failure'
      timestamp: new Date().toISOString(),
      ipAddress: details.ipAddress,
      userAgent: details.userAgent,
      mfaUsed: details.mfaUsed || false
    };

    this.logger.info('Authentication attempt', event);

    this.authenticationAttemptsCounter.inc({ result });

    // Detect suspicious patterns
    if (result === 'failure') {
      this.checkForBruteForce(userId, details.ipAddress);
    }
  }

  /**
   * Detect brute force attacks.
   */
  async checkForBruteForce(userId, ipAddress) {
    const timeWindow = 15 * 60 * 1000; // 15 minutes

    const recentFailures = await db.collection('auth_logs')
      .countDocuments({
        userId,
        result: 'failure',
        timestamp: { $gte: new Date(Date.now() - timeWindow) }
      });

    if (recentFailures >= 5) {
      this.logSecurityEvent('brute_force_detected', 'critical', {
        userId,
        ipAddress,
        failureCount: recentFailures
      });

      // Auto-remediation: Lock account
      await this.lockAccount(userId);
    }
  }

  /**
   * Send critical security alerts.
   */
  async sendSecurityAlert(event) {
    // Integration with PagerDuty, Slack, etc.
    console.error('CRITICAL SECURITY ALERT:', event);

    // Store in incidents database
    await db.collection('security_incidents').insertOne({
      ...event,
      status: 'open',
      createdAt: new Date()
    });
  }

  /**
   * Generate compliance report for auditors.
   *
   * SOC 2 Control: CC7.2 - Monitoring evidence
   */
  async generateMonitoringReport(startDate, endDate) {
    const events = await db.collection('security_events')
      .find({
        timestamp: {
          $gte: startDate,
          $lte: endDate
        }
      })
      .toArray();

    const report = {
      period: { startDate, endDate },
      totalEvents: events.length,
      eventsByType: this.groupBy(events, 'event'),
      eventsBySeverity: this.groupBy(events, 'severity'),
      criticalIncidents: events.filter(e => e.severity === 'critical'),
      authenticationStats: await this.getAuthenticationStats(startDate, endDate)
    };

    return report;
  }

  groupBy(array, key) {
    return array.reduce((result, item) => {
      const groupKey = item[key];
      result[groupKey] = (result[groupKey] || 0) + 1;
      return result;
    }, {});
  }

  async getAuthenticationStats(startDate, endDate) {
    const results = await db.collection('auth_logs').aggregate([
      {
        $match: {
          timestamp: { $gte: startDate, $lte: endDate }
        }
      },
      {
        $group: {
          _id: '$result',
          count: { $sum: 1 }
        }
      }
    ]).toArray();

    return {
      success: results.find(r => r._id === 'success')?.count || 0,
      failure: results.find(r => r._id === 'failure')?.count || 0
    };
  }
}

module.exports = SecurityMonitoring;
```

### CC6.6: Logical Access - Removal

**Control Objective**: Remove access when no longer required

```javascript
class AccessLifecycleManager {
  /**
   * Offboard user and revoke all access.
   *
   * SOC 2 Control: CC6.6 - Access removal
   */
  async offboardUser(userId, reason) {
    const offboardingId = require('uuid').v4();

    logger.info('User offboarding initiated', {
      event: 'offboarding_initiated',
      userId,
      offboardingId,
      reason,
      timestamp: new Date().toISOString()
    });

    // 1. Disable user account
    await db.collection('users').updateOne(
      { userId },
      {
        $set: {
          accountDisabled: true,
          disabledAt: new Date(),
          disabledReason: reason,
          offboardingId
        }
      }
    );

    // 2. Revoke all active sessions
    await this.revokeAllSessions(userId);

    // 3. Revoke API keys
    await this.revokeAPIKeys(userId);

    // 4. Remove from groups and roles
    await this.removeAllPermissions(userId);

    // 5. Archive user data
    await this.archiveUserData(userId, offboardingId);

    logger.warn('User offboarded', {
      event: 'offboarding_completed',
      userId,
      offboardingId,
      timestamp: new Date().toISOString()
    });

    return { offboardingId, status: 'completed' };
  }

  /**
   * Revoke all active sessions.
   */
  async revokeAllSessions(userId) {
    const sessions = await db.collection('sessions')
      .find({ userId, active: true })
      .toArray();

    for (const session of sessions) {
      await db.collection('sessions').updateOne(
        { _id: session._id },
        {
          $set: {
            active: false,
            revokedAt: new Date(),
            revokedReason: 'user_offboarding'
          }
        }
      );
    }

    logger.info('Sessions revoked', {
      event: 'sessions_revoked',
      userId,
      sessionCount: sessions.length
    });
  }

  /**
   * Revoke API keys.
   */
  async revokeAPIKeys(userId) {
    await db.collection('api_keys').updateMany(
      { userId, active: true },
      {
        $set: {
          active: false,
          revokedAt: new Date(),
          revokedReason: 'user_offboarding'
        }
      }
    );
  }

  /**
   * Remove all permissions.
   */
  async removeAllPermissions(userId) {
    // Remove from all groups
    await db.collection('group_members').deleteMany({ userId });

    // Clear user roles
    await db.collection('users').updateOne(
      { userId },
      { $set: { roles: [] } }
    );
  }

  /**
   * Archive user data for compliance retention.
   */
  async archiveUserData(userId, offboardingId) {
    const userData = await db.collection('users').findOne({ userId });
    const userActivity = await db.collection('activity_logs')
      .find({ userId })
      .toArray();

    await db.collection('archived_users').insertOne({
      offboardingId,
      originalUserId: userId,
      userData,
      activityLogs: userActivity,
      archivedAt: new Date(),
      retentionUntil: new Date(Date.now() + 7 * 365 * 24 * 60 * 60 * 1000) // 7 years
    });
  }
}

module.exports = AccessLifecycleManager;
```

---

## Availability Controls

### Monitor System Uptime

```javascript
const prometheus = require('prom-client');

class AvailabilityMonitoring {
  constructor() {
    this.uptimeGauge = new prometheus.Gauge({
      name: 'system_uptime_seconds',
      help: 'System uptime in seconds'
    });

    this.healthCheckGauge = new prometheus.Gauge({
      name: 'health_check_status',
      help: 'Health check status (1=healthy, 0=unhealthy)',
      labelNames: ['service']
    });

    // Track uptime
    this.startTime = Date.now();
    setInterval(() => {
      this.uptimeGauge.set((Date.now() - this.startTime) / 1000);
    }, 10000);
  }

  /**
   * Health check endpoint.
   *
   * SOC 2 Availability: System health monitoring
   */
  async performHealthCheck() {
    const checks = {
      database: await this.checkDatabase(),
      cache: await this.checkCache(),
      externalAPI: await this.checkExternalAPI()
    };

    const allHealthy = Object.values(checks).every(c => c.healthy);

    // Update Prometheus metrics
    Object.entries(checks).forEach(([service, result]) => {
      this.healthCheckGauge.set({ service }, result.healthy ? 1 : 0);
    });

    return {
      status: allHealthy ? 'healthy' : 'degraded',
      checks,
      uptime: (Date.now() - this.startTime) / 1000
    };
  }

  async checkDatabase() {
    try {
      await db.admin().ping();
      return { healthy: true, latency: 10 };
    } catch (error) {
      return { healthy: false, error: error.message };
    }
  }

  async checkCache() {
    try {
      // Redis health check
      return { healthy: true };
    } catch (error) {
      return { healthy: false, error: error.message };
    }
  }

  async checkExternalAPI() {
    try {
      // External dependency check
      return { healthy: true };
    } catch (error) {
      return { healthy: false, error: error.message };
    }
  }
}

module.exports = AvailabilityMonitoring;
```

---

## Success Criteria

- [ ] Multi-factor authentication enforced for all users
- [ ] All sensitive data encrypted at rest (AES-256-GCM)
- [ ] HTTPS enforced with TLS 1.3
- [ ] Security events logged with structured data
- [ ] Failed authentication attempts monitored
- [ ] User access removed within 24 hours of offboarding
- [ ] System health monitoring operational
- [ ] Compliance reports generated monthly

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
