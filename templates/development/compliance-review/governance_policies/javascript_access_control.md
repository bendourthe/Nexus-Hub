---
template_id: compliance_governance_access_control_javascript
template_name: Access Control - JavaScript
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
  - governance_policies/javascript_security_policies.md
tools:
  - jsonwebtoken (JWT)
  - passport (authentication)
tags:
  - access-control
  - rbac
  - least-privilege
  - javascript
  - nodejs
---

# Access Control - JavaScript

**Role-Based Access Control (RBAC) implementation**

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Access Control Models

**RBAC**: Role-Based Access Control
- Users assigned to roles
- Roles have permissions
- Least privilege principle

**Key Concepts**:
- **Authentication**: Verify identity
- **Authorization**: Check permissions
- **Least Privilege**: Minimum necessary access

---

## Implementation

```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'access-control.log' })
  ]
});

const Role = {
  GUEST: 'guest',
  USER: 'user',
  MANAGER: 'manager',
  ADMIN: 'admin',
  SUPERADMIN: 'superadmin'
};

const Permission = {
  // Read permissions
  READ_PUBLIC: 'read:public',
  READ_INTERNAL: 'read:internal',
  READ_CONFIDENTIAL: 'read:confidential',

  // Write permissions
  WRITE_PUBLIC: 'write:public',
  WRITE_INTERNAL: 'write:internal',
  WRITE_CONFIDENTIAL: 'write:confidential',

  // Admin permissions
  MANAGE_USERS: 'manage:users',
  MANAGE_ROLES: 'manage:roles',
  MANAGE_SYSTEM: 'manage:system'
};

class AccessControlManager {
  constructor() {
    // Define role-permission mappings
    this.ROLE_PERMISSIONS = {
      [Role.GUEST]: new Set([
        Permission.READ_PUBLIC
      ]),
      [Role.USER]: new Set([
        Permission.READ_PUBLIC,
        Permission.READ_INTERNAL,
        Permission.WRITE_PUBLIC
      ]),
      [Role.MANAGER]: new Set([
        Permission.READ_PUBLIC,
        Permission.READ_INTERNAL,
        Permission.READ_CONFIDENTIAL,
        Permission.WRITE_PUBLIC,
        Permission.WRITE_INTERNAL,
        Permission.MANAGE_USERS
      ]),
      [Role.ADMIN]: new Set([
        Permission.READ_PUBLIC,
        Permission.READ_INTERNAL,
        Permission.READ_CONFIDENTIAL,
        Permission.WRITE_PUBLIC,
        Permission.WRITE_INTERNAL,
        Permission.WRITE_CONFIDENTIAL,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ROLES
      ]),
      [Role.SUPERADMIN]: new Set(Object.values(Permission))
    };
  }

  /**
   * Check if user has required permission.
   *
   * ISO 27001 Control 5.15: Access control
   * Principle: Least Privilege
   */
  async hasPermission(userId, permission) {
    const user = await db.collection('users').findOne({ userId });

    if (!user) {
      logger.warn('Permission check failed - user not found', {
        event: 'permission_check_failed',
        userId,
        permission,
        reason: 'user_not_found',
        timestamp: new Date().toISOString()
      });
      return false;
    }

    // Get user's roles
    const userRoles = user.roles || [Role.GUEST];

    // Collect all permissions from all roles
    const userPermissions = new Set();

    for (const role of userRoles) {
      const rolePermissions = this.ROLE_PERMISSIONS[role] || new Set();
      rolePermissions.forEach(perm => userPermissions.add(perm));
    }

    const hasAccess = userPermissions.has(permission);

    logger.info('Permission check', {
      event: 'permission_check',
      userId,
      permission,
      granted: hasAccess,
      roles: userRoles,
      timestamp: new Date().toISOString()
    });

    return hasAccess;
  }

  /**
   * Assign role to user.
   *
   * ISO 27001 Control 5.16: Identity management
   */
  async assignRole(userId, role, assignedBy) {
    // Verify assigner has permission to assign roles
    const canAssign = await this.hasPermission(assignedBy, Permission.MANAGE_ROLES);

    if (!canAssign) {
      throw new Error('Insufficient permissions to assign roles');
    }

    await db.collection('users').updateOne(
      { userId },
      { $addToSet: { roles: role } }
    );

    logger.warn('Role assigned', {
      event: 'role_assigned',
      userId,
      role,
      assignedBy,
      timestamp: new Date().toISOString()
    });

    return { userId, role, status: 'assigned' };
  }

  /**
   * Revoke role from user.
   */
  async revokeRole(userId, role, revokedBy) {
    const canRevoke = await this.hasPermission(revokedBy, Permission.MANAGE_ROLES);

    if (!canRevoke) {
      throw new Error('Insufficient permissions to revoke roles');
    }

    await db.collection('users').updateOne(
      { userId },
      { $pull: { roles: role } }
    );

    logger.warn('Role revoked', {
      event: 'role_revoked',
      userId,
      role,
      revokedBy,
      timestamp: new Date().toISOString()
    });

    return { userId, role, status: 'revoked' };
  }

  /**
   * Create custom permission for fine-grained access control.
   */
  async createCustomPermission(permissionName, description, createdBy) {
    const permissionId = uuidv4();

    const permission = {
      permissionId,
      permissionName,
      description,
      createdBy,
      createdDate: new Date(),
      active: true
    };

    await db.collection('custom_permissions').insertOne(permission);

    logger.info('Custom permission created', {
      event: 'permission_created',
      permissionId,
      permissionName,
      createdBy,
      timestamp: new Date().toISOString()
    });

    return permissionId;
  }

  /**
   * Implement Just-In-Time (JIT) access.
   *
   * Temporary elevated access for specific tasks
   */
  async grantTemporaryAccess(userId, permission, durationMinutes, justification) {
    const accessId = uuidv4();
    const expiresAt = new Date(Date.now() + durationMinutes * 60 * 1000);

    const tempAccess = {
      accessId,
      userId,
      permission,
      justification,
      grantedAt: new Date(),
      expiresAt,
      active: true
    };

    await db.collection('temporary_access').insertOne(tempAccess);

    logger.warn('Temporary access granted', {
      event: 'temporary_access_granted',
      accessId,
      userId,
      permission,
      expiresAt: expiresAt.toISOString(),
      timestamp: new Date().toISOString()
    });

    // Schedule automatic revocation
    setTimeout(() => {
      this.revokeTemporaryAccess(accessId);
    }, durationMinutes * 60 * 1000);

    return accessId;
  }

  /**
   * Revoke temporary access.
   */
  async revokeTemporaryAccess(accessId) {
    await db.collection('temporary_access').updateOne(
      { accessId },
      { $set: { active: false, revokedAt: new Date() } }
    );

    logger.info('Temporary access revoked', {
      event: 'temporary_access_revoked',
      accessId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Check temporary access.
   */
  async hasTemporaryAccess(userId, permission) {
    const tempAccess = await db.collection('temporary_access').findOne({
      userId,
      permission,
      active: true,
      expiresAt: { $gt: new Date() }
    });

    return tempAccess !== null;
  }

  /**
   * Audit access patterns for anomalies.
   *
   * Detect unauthorized access attempts
   */
  async auditAccessPatterns(userId, timeWindowHours = 24) {
    const since = new Date(Date.now() - timeWindowHours * 60 * 60 * 1000);

    const accessLogs = await db.collection('access_logs')
      .find({
        userId,
        timestamp: { $gte: since }
      })
      .toArray();

    const anomalies = [];

    // Check for excessive failed access attempts
    const failedAttempts = accessLogs.filter(log => !log.granted);
    if (failedAttempts.length > 10) {
      anomalies.push({
        type: 'excessive_failed_attempts',
        count: failedAttempts.length,
        severity: 'high'
      });
    }

    // Check for unusual access times
    const nightAccess = accessLogs.filter(log => {
      const hour = new Date(log.timestamp).getHours();
      return hour >= 2 && hour <= 5;
    });

    if (nightAccess.length > 5) {
      anomalies.push({
        type: 'unusual_access_time',
        count: nightAccess.length,
        severity: 'medium'
      });
    }

    if (anomalies.length > 0) {
      logger.warn('Access anomalies detected', {
        event: 'access_anomalies',
        userId,
        anomalies,
        timestamp: new Date().toISOString()
      });
    }

    return { anomaliesDetected: anomalies.length > 0, anomalies };
  }

  /**
   * Generate access control report.
   */
  async generateAccessReport() {
    const users = await db.collection('users').find({}).toArray();

    const report = {
      reportId: uuidv4(),
      generatedDate: new Date(),
      totalUsers: users.length,
      usersByRole: this.groupBy(
        users.flatMap(u => u.roles || [Role.GUEST])
      ),
      usersWithMultipleRoles: users.filter(u => u.roles?.length > 1).length,
      activeTemporaryAccess: await db.collection('temporary_access')
        .countDocuments({ active: true, expiresAt: { $gt: new Date() } })
    };

    return report;
  }

  groupBy(array) {
    return array.reduce((result, item) => {
      result[item] = (result[item] || 0) + 1;
      return result;
    }, {});
  }
}

module.exports = { AccessControlManager, Role, Permission };
```

---

## Success Criteria

- [ ] RBAC implemented with role hierarchy
- [ ] Least privilege principle enforced
- [ ] Just-In-Time access operational
- [ ] Access logs audited for anomalies
- [ ] Temporary access auto-revoked
- [ ] Access control reports generated

---

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
