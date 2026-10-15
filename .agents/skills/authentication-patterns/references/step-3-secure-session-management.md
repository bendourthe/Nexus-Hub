### Step 3: Secure Session Management

**Cookie-Based Sessions (Express.js)**:

```typescript
import express from 'express';
import session from 'express-session';
import RedisStore from 'connect-redis';
import { createClient } from 'redis';

const redisClient = createClient({ url: process.env.REDIS_URL });
await redisClient.connect();

const app = express();

app.use(session({
  store: new RedisStore({ client: redisClient }),
  name: '__Host-session',           // __Host- prefix enforces Secure + no Domain
  secret: process.env.SESSION_SECRET!,
  resave: false,
  saveUninitialized: false,
  rolling: true,                    // Reset expiry on each request
  cookie: {
    secure: true,                   // HTTPS only
    httpOnly: true,                 // Not accessible via JavaScript
    sameSite: 'lax',                // CSRF protection
    maxAge: 30 * 60 * 1000,        // 30 minutes
    path: '/',
  },
}));

// Session fixation prevention: regenerate session ID after login
app.post('/login', async (req, res) => {
  const user = await authenticateUser(req.body.email, req.body.password);
  if (!user) return res.status(401).json({ error: 'Invalid credentials' });

  // Regenerate session to prevent fixation attacks
  req.session.regenerate((err) => {
    if (err) return res.status(500).json({ error: 'Session error' });
    req.session.userId = user.id;
    req.session.role = user.role;
    res.json({ message: 'Logged in' });
  });
});

// Logout: destroy session and clear cookie
app.post('/logout', (req, res) => {
  req.session.destroy(() => {
    res.clearCookie('__Host-session');
    res.json({ message: 'Logged out' });
  });
});
```

**Token Storage in SPAs** (security comparison):

| Storage | XSS Risk | CSRF Risk | Recommendation |
|---------|----------|-----------|----------------|
| localStorage | High (JS accessible) | None | Avoid for tokens |
| sessionStorage | High (JS accessible) | None | Avoid for tokens |
| HttpOnly cookie | None (not JS accessible) | Medium | Preferred with SameSite |
| In-memory variable | Low (lost on refresh) | None | Good for access tokens |
