### Step 8: Prevent Common Vulnerabilities

**CSRF Protection**:

```typescript
import csrf from 'csurf';

// For cookie-based sessions, use double-submit cookie pattern
app.use(csrf({
  cookie: {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
  },
}));

// Include CSRF token in responses for forms/SPAs
app.get('/api/csrf-token', (req, res) => {
  res.json({ csrfToken: req.csrfToken() });
});
```

**Session Fixation Prevention**:

```typescript
// Always regenerate session ID after authentication state changes
app.post('/login', async (req, res) => {
  const user = await authenticate(req.body);
  if (!user) return res.status(401).json({ error: 'Invalid credentials' });

  // Destroy old session and create new one
  const oldSession = { ...req.session };
  req.session.regenerate((err) => {
    if (err) return res.status(500).json({ error: 'Session error' });
    // Copy non-sensitive data from old session if needed
    req.session.userId = user.id;
    req.session.role = user.role;
    res.json({ message: 'Authenticated' });
  });
});
```

**Token Theft Mitigation**:

```typescript
// Bind tokens to client fingerprint
function createBoundToken(userId: string, clientFingerprint: string): string {
  return jwt.sign(
    {
      sub: userId,
      fpt: crypto.createHash('sha256').update(clientFingerprint).digest('hex'),
    },
    PRIVATE_KEY,
    { algorithm: 'RS256', expiresIn: '15m' }
  );
}

// Validate fingerprint on each request
function validateBoundToken(token: string, clientFingerprint: string): boolean {
  const decoded = jwt.verify(token, PUBLIC_KEY) as any;
  const expectedFpt = crypto.createHash('sha256').update(clientFingerprint).digest('hex');
  return decoded.fpt === expectedFpt;
}
```
