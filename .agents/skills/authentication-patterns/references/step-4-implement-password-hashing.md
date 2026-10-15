### Step 4: Implement Password Hashing

```typescript
import bcrypt from 'bcrypt';
import argon2 from 'argon2';

// ── bcrypt (widely supported, proven) ─────────────────────────────

const BCRYPT_ROUNDS = 12;  // Aim for ~250ms hash time

async function hashPasswordBcrypt(password: string): Promise<string> {
  return bcrypt.hash(password, BCRYPT_ROUNDS);
}

async function verifyPasswordBcrypt(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

// ── Argon2id (recommended for new projects, OWASP preferred) ──────

async function hashPasswordArgon2(password: string): Promise<string> {
  return argon2.hash(password, {
    type: argon2.argon2id,    // Hybrid: resistant to side-channel + GPU attacks
    memoryCost: 65536,        // 64 MB
    timeCost: 3,              // 3 iterations
    parallelism: 4,           // 4 threads
  });
}

async function verifyPasswordArgon2(password: string, hash: string): Promise<boolean> {
  return argon2.verify(hash, password);
}

// ── Password policy enforcement ───────────────────────────────────

function validatePasswordPolicy(password: string): string[] {
  const errors: string[] = [];
  if (password.length < 12) errors.push('Minimum 12 characters');
  if (password.length > 128) errors.push('Maximum 128 characters');
  // Check against common breached passwords (use a bloom filter or k-anonymity API)
  // Do NOT enforce complex character rules (NIST SP 800-63B guidance)
  return errors;
}
```
