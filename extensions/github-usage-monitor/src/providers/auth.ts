import type { ProviderError, ProviderResult, RateMetadata } from "../types";

const DEFAULT_SECRET_KEY = "githubUsage.token";

export interface SecretStorageLike {
  get(key: string): Thenable<string | undefined>;
  store(key: string, value: string): Thenable<void>;
  delete(key: string): Thenable<void>;
}

export type TokenValidator = (token: string) => Promise<ProviderResult<void>>;

export type TokenMutationResult =
  | { ok: true }
  | { ok: false; error: ProviderError };

const EMPTY_RATE: RateMetadata = {
  remaining: null,
  resetAt: null,
  retryAfterMs: null
};

export class GitHubTokenStore {
  public constructor(
    private readonly secrets: SecretStorageLike,
    private readonly secretKey = DEFAULT_SECRET_KEY
  ) {}

  public async hasToken(): Promise<boolean> {
    return (await this.secrets.get(this.secretKey)) !== undefined;
  }

  public async withToken<T>(operation: (token: string) => Promise<T>): Promise<ProviderResult<T>> {
    const token = await this.secrets.get(this.secretKey);
    if (token === undefined) {
      return {
        ok: false,
        error: missingTokenError(),
        rate: EMPTY_RATE
      };
    }
    return {
      ok: true,
      value: await operation(token),
      rate: EMPTY_RATE
    };
  }

  public async setToken(token: string, validator: TokenValidator): Promise<TokenMutationResult> {
    const syntaxError = validateTokenSyntax(token);
    if (syntaxError !== null) {
      return { ok: false, error: syntaxError };
    }

    const normalized = token.trim();
    const validation = await validator(normalized);
    if (!validation.ok) {
      return { ok: false, error: validation.error };
    }
    await this.secrets.store(this.secretKey, normalized);
    return { ok: true };
  }

  public async rotateToken(token: string, validator: TokenValidator): Promise<TokenMutationResult> {
    return this.setToken(token, validator);
  }

  public async validateToken(validator: TokenValidator): Promise<TokenMutationResult> {
    const result = await this.withToken(validator);
    if (!result.ok) {
      return { ok: false, error: result.error };
    }
    return result.value.ok ? { ok: true } : { ok: false, error: result.value.error };
  }

  public async clearToken(): Promise<void> {
    await this.secrets.delete(this.secretKey);
  }
}

export function validateTokenSyntax(token: string): ProviderError | null {
  const normalized = token.trim();
  if (
    normalized.length < 20 ||
    /[\u0000-\u001f\u007f]/u.test(token) ||
    /\s/u.test(normalized)
  ) {
    return {
      code: "invalid-token",
      message: "Enter a non-empty GitHub token without whitespace or control characters."
    };
  }
  return null;
}

export function vscodeGitHubSessionProbe(): { supported: false; reason: string } {
  return {
    supported: false,
    reason: "Phase 1 did not prove that VS Code GitHub sessions are accepted by the billing endpoints; use SecretStorage."
  };
}

function missingTokenError(): ProviderError {
  return {
    code: "missing-token",
    message: "No GitHub billing token is stored. Run 'GitHub Usage: Set Token'."
  };
}
