### Step 2: Implement JWT Lifecycle

**JWT Structure**:

```
Header.Payload.Signature

Header:  { "alg": "RS256", "typ": "JWT", "kid": "key-2026-03" }
Payload: { "sub": "user-123", "iss": "https://auth.example.com",
           "aud": "https://api.example.com", "exp": 1709500800,
           "iat": 1709497200, "scope": "read write" }
Signature: RS256(base64url(header) + "." + base64url(payload), privateKey)
```

**JWT Signing and Validation (Node.js)**:

```typescript
import jwt from 'jsonwebtoken';
import jwksClient from 'jwks-rsa';

// ── Token Creation (auth server side) ─────────────────────────────

const PRIVATE_KEY = process.env.JWT_PRIVATE_KEY!;

function createAccessToken(userId: string, scopes: string[]): string {
  return jwt.sign(
    {
      sub: userId,
      scope: scopes.join(' '),
    },
    PRIVATE_KEY,
    {
      algorithm: 'RS256',
      issuer: 'https://auth.example.com',
      audience: 'https://api.example.com',
      expiresIn: '15m',   // Short-lived access tokens
      keyid: 'key-2026-03',
    }
  );
}

function createRefreshToken(userId: string, tokenFamily: string): string {
  return jwt.sign(
    {
      sub: userId,
      family: tokenFamily,  // For rotation detection
    },
    PRIVATE_KEY,
    {
      algorithm: 'RS256',
      issuer: 'https://auth.example.com',
      expiresIn: '7d',
      jwtid: crypto.randomUUID(),  // Unique token ID for revocation
    }
  );
}

// ── Token Validation (resource server side) ───────────────────────

const client = jwksClient({
  jwksUri: 'https://auth.example.com/.well-known/jwks.json',
  cache: true,
  rateLimit: true,
  jwksRequestsPerMinute: 5,
});

function getSigningKey(header: jwt.JwtHeader, callback: jwt.SigningKeyCallback): void {
  client.getSigningKey(header.kid, (err, key) => {
    if (err) return callback(err);
    callback(null, key?.getPublicKey());
  });
}

function validateAccessToken(token: string): Promise<jwt.JwtPayload> {
  return new Promise((resolve, reject) => {
    jwt.verify(
      token,
      getSigningKey,
      {
        algorithms: ['RS256'],
        issuer: 'https://auth.example.com',
        audience: 'https://api.example.com',
        clockTolerance: 30,  // 30-second clock skew tolerance
      },
      (err, decoded) => {
        if (err) return reject(err);
        resolve(decoded as jwt.JwtPayload);
      }
    );
  });
}
```

**Refresh Token Rotation** (prevents token theft):

```typescript
async function refreshTokens(refreshToken: string): Promise<TokenResponse> {
  // 1. Validate the refresh token
  const decoded = await validateRefreshToken(refreshToken);

  // 2. Check if token has been revoked (detect reuse attacks)
  const isRevoked = await tokenStore.isRevoked(decoded.jti);
  if (isRevoked) {
    // Token reuse detected: revoke the entire token family
    await tokenStore.revokeFamily(decoded.family);
    throw new Error('Refresh token reuse detected. All sessions revoked.');
  }

  // 3. Revoke the old refresh token
  await tokenStore.revoke(decoded.jti);

  // 4. Issue new token pair
  const newAccessToken = createAccessToken(decoded.sub, decoded.scope);
  const newRefreshToken = createRefreshToken(decoded.sub, decoded.family);

  return {
    access_token: newAccessToken,
    refresh_token: newRefreshToken,
    token_type: 'Bearer',
    expires_in: 900,
  };
}
```
