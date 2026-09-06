### Step 7: Configure Security Headers

```typescript
import helmet from 'helmet';

app.use(helmet({
  // Content Security Policy: prevent XSS and data injection
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'strict-dynamic'"],
      styleSrc: ["'self'", "'unsafe-inline'"],  // Consider nonces for stricter CSP
      imgSrc: ["'self'", "data:", "https://cdn.example.com"],
      connectSrc: ["'self'", "https://api.example.com"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      objectSrc: ["'none'"],
      frameAncestors: ["'none'"],          // Prevent clickjacking
      baseUri: ["'self'"],
      formAction: ["'self'"],
      upgradeInsecureRequests: [],
    },
  },

  // HSTS: force HTTPS for 1 year including subdomains
  strictTransportSecurity: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },

  // Prevent MIME type sniffing
  xContentTypeOptions: true,   // X-Content-Type-Options: nosniff

  // Referrer policy
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },

  // Permissions policy
  permittedCrossDomainPolicies: { permittedPolicies: 'none' },
}));

// ── CORS Configuration ────────────────────────────────────────────

import cors from 'cors';

app.use(cors({
  origin: ['https://app.example.com', 'https://admin.example.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,             // Allow cookies in cross-origin requests
  maxAge: 86400,                 // Cache preflight for 24 hours
}));
```
