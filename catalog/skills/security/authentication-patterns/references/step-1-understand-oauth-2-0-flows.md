### Step 1: Understand OAuth 2.0 Flows

**Flow Selection Guide**:

| Flow | Use Case | Client Type |
|------|----------|-------------|
| Authorization Code + PKCE | Web apps, SPAs, mobile | Public clients |
| Client Credentials | Machine-to-machine | Confidential clients |
| Device Authorization | Smart TVs, CLI tools | Input-constrained devices |
| Refresh Token | Extend sessions without re-auth | Any client with refresh grant |

**Authorization Code Flow with PKCE** (recommended for all user-facing apps):

```
┌──────┐     1. Auth Request + code_verifier     ┌──────────────┐
│      │────────────────────────────────────────▶│              │
│      │                                         │ Authorization│
│ App  │◀────────────────────────────────────────│   Server     │
│      │     2. Authorization Code               │              │
│      │                                         └──────┬───────┘
│      │     3. Token Request + code_verifier            │
│      │────────────────────────────────────────▶        │
│      │                                                 │
│      │◀────────────────────────────────────────        │
│      │     4. Access Token + Refresh Token             │
└──────┘                                         ┌──────┴───────┐
   │                                             │   Resource   │
   │         5. API Request + Access Token       │   Server     │
   │────────────────────────────────────────────▶│              │
   │                                             └──────────────┘
```

**PKCE Implementation (Node.js)**:

```typescript
import crypto from 'crypto';

// Step 1: Generate PKCE code verifier and challenge
function generatePKCE(): { verifier: string; challenge: string } {
  // Code verifier: 43-128 character random string
  const verifier = crypto.randomBytes(32).toString('base64url');

  // Code challenge: SHA-256 hash of verifier, base64url encoded
  const challenge = crypto
    .createHash('sha256')
    .update(verifier)
    .digest('base64url');

  return { verifier, challenge };
}

// Step 2: Build authorization URL
function buildAuthUrl(clientId: string, redirectUri: string, challenge: string): string {
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: clientId,
    redirect_uri: redirectUri,
    scope: 'openid profile email',
    state: crypto.randomBytes(16).toString('hex'),  // CSRF protection
    code_challenge: challenge,
    code_challenge_method: 'S256',
  });
  return `https://auth.example.com/authorize?${params}`;
}

// Step 3: Exchange authorization code for tokens
async function exchangeCode(
  code: string,
  verifier: string,
  clientId: string,
  redirectUri: string
): Promise<TokenResponse> {
  const response = await fetch('https://auth.example.com/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      redirect_uri: redirectUri,
      client_id: clientId,
      code_verifier: verifier,  // Prove we initiated the request
    }),
  });

  if (!response.ok) {
    throw new Error(`Token exchange failed: ${response.status}`);
  }

  return response.json();
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  id_token: string;     // Present with OIDC
  token_type: 'Bearer';
  expires_in: number;
}
```

**Client Credentials Flow** (service-to-service):

```typescript
async function getServiceToken(clientId: string, clientSecret: string): Promise<string> {
  const response = await fetch('https://auth.example.com/oauth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Authorization': `Basic ${Buffer.from(`${clientId}:${clientSecret}`).toString('base64')}`,
    },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      scope: 'orders:read orders:write',
    }),
  });

  const data = await response.json();
  return data.access_token;
}
```
