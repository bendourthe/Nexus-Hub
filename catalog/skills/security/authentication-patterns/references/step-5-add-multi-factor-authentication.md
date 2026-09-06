### Step 5: Add Multi-Factor Authentication

**TOTP Implementation (Google Authenticator compatible)**:

```typescript
import { authenticator } from 'otplib';
import QRCode from 'qrcode';

// ── TOTP Setup ────────────────────────────────────────────────────

async function enableTOTP(userId: string, email: string) {
  // Generate a secret for this user
  const secret = authenticator.generateSecret(20);  // 160-bit secret

  // Store secret (encrypted) in database, marked as unverified
  await db.users.update(userId, {
    totp_secret: encrypt(secret),
    totp_verified: false,
  });

  // Generate QR code for authenticator app
  const otpauthUrl = authenticator.keyuri(email, 'MyApp', secret);
  const qrCodeDataUrl = await QRCode.toDataURL(otpauthUrl);

  return {
    secret,        // Show to user as backup
    qrCode: qrCodeDataUrl,
  };
}

// ── TOTP Verification ─────────────────────────────────────────────

async function verifyTOTP(userId: string, token: string): Promise<boolean> {
  const user = await db.users.findById(userId);
  const secret = decrypt(user.totp_secret);

  // Validate with a 1-step window (allows 30s clock drift)
  const isValid = authenticator.check(token, secret);

  if (isValid && !user.totp_verified) {
    await db.users.update(userId, { totp_verified: true });
  }

  return isValid;
}
```

**WebAuthn/Passkeys Registration (using SimpleWebAuthn)**:

```typescript
import {
  generateRegistrationOptions,
  verifyRegistrationResponse,
  generateAuthenticationOptions,
  verifyAuthenticationResponse,
} from '@simplewebauthn/server';

const RP_NAME = 'MyApp';
const RP_ID = 'example.com';
const ORIGIN = 'https://example.com';

// ── Passkey Registration ──────────────────────────────────────────

async function startPasskeyRegistration(userId: string, email: string) {
  const existingCredentials = await db.credentials.findByUser(userId);

  const options = await generateRegistrationOptions({
    rpName: RP_NAME,
    rpID: RP_ID,
    userName: email,
    userDisplayName: email,
    attestationType: 'none',       // Skip attestation for simpler flow
    excludeCredentials: existingCredentials.map(cred => ({
      id: cred.credentialId,
      type: 'public-key',
    })),
    authenticatorSelection: {
      residentKey: 'preferred',    // Enable discoverable credentials (passkeys)
      userVerification: 'preferred',
    },
  });

  // Store challenge in session for verification
  await sessionStore.set(userId, { challenge: options.challenge });

  return options;
}

async function finishPasskeyRegistration(userId: string, response: any) {
  const session = await sessionStore.get(userId);

  const verification = await verifyRegistrationResponse({
    response,
    expectedChallenge: session.challenge,
    expectedOrigin: ORIGIN,
    expectedRPID: RP_ID,
  });

  if (verification.verified && verification.registrationInfo) {
    await db.credentials.create({
      userId,
      credentialId: verification.registrationInfo.credentialID,
      publicKey: verification.registrationInfo.credentialPublicKey,
      counter: verification.registrationInfo.counter,
    });
  }

  return verification.verified;
}
```
