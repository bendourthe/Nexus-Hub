## Common Patterns

### Pattern 1: API Key with Rate Limiting

```typescript
// API key middleware with per-key rate limiting
const rateLimiter = new Map<string, { count: number; resetAt: number }>();

function apiKeyAuth(req: Request, res: Response, next: NextFunction) {
  const apiKey = req.headers['x-api-key'] as string;
  if (!apiKey) return res.status(401).json({ error: 'API key required' });

  // Validate key and get associated client
  const client = await db.apiKeys.findByKey(hashApiKey(apiKey));
  if (!client) return res.status(401).json({ error: 'Invalid API key' });

  // Rate limiting per key
  const now = Date.now();
  const limit = rateLimiter.get(client.id) || { count: 0, resetAt: now + 60000 };
  if (now > limit.resetAt) {
    limit.count = 0;
    limit.resetAt = now + 60000;
  }
  limit.count++;
  rateLimiter.set(client.id, limit);

  if (limit.count > client.rateLimit) {
    return res.status(429).json({ error: 'Rate limit exceeded' });
  }

  req.client = client;
  next();
}
```

### Pattern 2: Scope-Based Authorization for APIs

```typescript
function requireScope(...requiredScopes: string[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) return res.status(401).json({ error: 'Token required' });

    try {
      const decoded = await validateAccessToken(token);
      const tokenScopes = (decoded.scope || '').split(' ');

      const hasScope = requiredScopes.every(s => tokenScopes.includes(s));
      if (!hasScope) {
        return res.status(403).json({
          error: 'insufficient_scope',
          required: requiredScopes,
          provided: tokenScopes,
        });
      }

      req.user = decoded;
      next();
    } catch (err) {
      return res.status(401).json({ error: 'Invalid token' });
    }
  };
}

// Usage
app.get('/api/orders', requireScope('orders:read'), getOrders);
app.post('/api/orders', requireScope('orders:write'), createOrder);
```
