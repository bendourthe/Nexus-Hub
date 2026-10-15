### Step 6: Implement Role-Based Access Control (RBAC)

**RBAC Middleware (Express.js)**:

```typescript
// ── Permission Model ──────────────────────────────────────────────

interface Role {
  name: string;
  permissions: string[];
}

const ROLES: Record<string, Role> = {
  admin: {
    name: 'admin',
    permissions: ['users:read', 'users:write', 'users:delete',
                  'orders:read', 'orders:write', 'orders:delete',
                  'reports:read', 'settings:write'],
  },
  manager: {
    name: 'manager',
    permissions: ['users:read', 'orders:read', 'orders:write', 'reports:read'],
  },
  viewer: {
    name: 'viewer',
    permissions: ['orders:read', 'reports:read'],
  },
};

// ── Authorization Middleware ──────────────────────────────────────

function requirePermission(...requiredPermissions: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    const userRole = req.session?.role;

    if (!userRole) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const role = ROLES[userRole];
    if (!role) {
      return res.status(403).json({ error: 'Unknown role' });
    }

    const hasPermission = requiredPermissions.every(
      perm => role.permissions.includes(perm)
    );

    if (!hasPermission) {
      return res.status(403).json({
        error: 'Insufficient permissions',
        required: requiredPermissions,
      });
    }

    next();
  };
}

// ── Route Usage ───────────────────────────────────────────────────

app.get('/api/orders', requirePermission('orders:read'), getOrders);
app.post('/api/orders', requirePermission('orders:write'), createOrder);
app.delete('/api/orders/:id', requirePermission('orders:delete'), deleteOrder);
app.get('/api/reports', requirePermission('reports:read'), getReports);
app.delete('/api/users/:id', requirePermission('users:delete'), deleteUser);
```

**Attribute-Based Access Control (ABAC) Example**:

```typescript
interface PolicyContext {
  user: { id: string; role: string; department: string };
  resource: { ownerId: string; type: string; classification: string };
  action: string;
  environment: { time: Date; ipAddress: string };
}

function evaluatePolicy(ctx: PolicyContext): boolean {
  const policies = [
    // Admins can do anything
    (c: PolicyContext) => c.user.role === 'admin',

    // Users can read their own resources
    (c: PolicyContext) =>
      c.action === 'read' && c.resource.ownerId === c.user.id,

    // Managers can write resources in their department
    (c: PolicyContext) =>
      c.user.role === 'manager' &&
      c.action === 'write' &&
      c.resource.classification !== 'confidential',

    // No access to confidential resources outside business hours
    (c: PolicyContext) => {
      if (c.resource.classification === 'confidential') {
        const hour = c.environment.time.getHours();
        return hour >= 8 && hour <= 18;
      }
      return true;
    },
  ];

  return policies.some(policy => policy(ctx));
}
```
