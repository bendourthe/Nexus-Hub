import { posix, win32 } from "node:path";
import type {
  ProviderError,
  ProviderResult
} from "../types";
import { providerError } from "./errors";

const DEFAULT_SECRET_KEY = "cursorUsage.credential";

export interface SecretStorageLike {
  get(key: string): Thenable<string | undefined>;
  store(key: string, value: string): Thenable<void>;
  delete(key: string): Thenable<void>;
}

export interface AuthorizedSessionProbe {
  statePath: string;
  allowlistedKey: string;
  authorizationId: string;
}

export type CursorAuthPlan =
  | {
      kind: "none";
      reason: "not-configured" | "authorization-required";
    }
  | { kind: "secret-storage"; secretKey: string }
  | ({ kind: "authorized-session-probe" } & AuthorizedSessionProbe);

export type CredentialMutationResult =
  | { ok: true }
  | { ok: false; error: ProviderError };

export class CursorCredentialStore {
  public constructor(
    private readonly secrets: SecretStorageLike,
    private readonly secretKey = DEFAULT_SECRET_KEY
  ) {}

  public async hasCredential(): Promise<ProviderResult<boolean>> {
    try {
      return {
        ok: true,
        value: (await this.secrets.get(this.secretKey)) !== undefined
      };
    } catch {
      return {
        ok: false,
        error: providerError("credential-store-error", null)
      };
    }
  }

  public async withCredential<T>(
    operation: (credential: string) => Promise<ProviderResult<T>>
  ): Promise<ProviderResult<T>> {
    let credential: string | undefined;
    try {
      credential = await this.secrets.get(this.secretKey);
    } catch {
      return {
        ok: false,
        error: providerError("credential-store-error", null)
      };
    }
    if (credential === undefined) {
      return {
        ok: false,
        error: providerError("missing-credential", null)
      };
    }
    try {
      return await operation(credential);
    } catch {
      return {
        ok: false,
        error: providerError(
          "credential-adapter-unavailable",
          "credential-api"
        )
      };
    }
  }

  public async setCredential(
    credential: string
  ): Promise<CredentialMutationResult> {
    const normalized = credential.trim();
    if (!isValidCredential(normalized)) {
      return {
        ok: false,
        error: providerError("invalid-credential", null, {
          recoverable: false
        })
      };
    }
    try {
      await this.secrets.store(this.secretKey, normalized);
      return { ok: true };
    } catch {
      return {
        ok: false,
        error: providerError("credential-store-error", null)
      };
    }
  }

  public async clearCredential(): Promise<CredentialMutationResult> {
    try {
      await this.secrets.delete(this.secretKey);
      return { ok: true };
    } catch {
      return {
        ok: false,
        error: providerError("credential-store-error", null)
      };
    }
  }
}

export function resolveAuthPlan(options: {
  hasStoredCredential: boolean;
  authorizedProbe?: AuthorizedSessionProbe;
}): CursorAuthPlan {
  if (options.hasStoredCredential) {
    return { kind: "secret-storage", secretKey: DEFAULT_SECRET_KEY };
  }
  if (isValidAuthorizedProbe(options.authorizedProbe)) {
    return { kind: "authorized-session-probe", ...options.authorizedProbe };
  }
  return {
    kind: "none",
    reason:
      options.authorizedProbe === undefined
        ? "authorization-required"
        : "not-configured"
  };
}

export function resolveCursorStatePath(
  platform: NodeJS.Platform,
  options: {
    home: string;
    appData?: string;
    xdgConfigHome?: string;
  }
): string | null {
  if (platform === "win32") {
    return options.appData === undefined
      ? null
      : win32.join(
          options.appData,
          "Cursor",
          "User",
          "globalStorage",
          "state.vscdb"
        );
  }
  if (platform === "darwin") {
    return posix.join(
      options.home,
      "Library",
      "Application Support",
      "Cursor",
      "User",
      "globalStorage",
      "state.vscdb"
    );
  }
  if (platform === "linux") {
    return posix.join(
      options.xdgConfigHome ?? posix.join(options.home, ".config"),
      "Cursor",
      "User",
      "globalStorage",
      "state.vscdb"
    );
  }
  return null;
}

export function automaticSessionProbe(): ProviderResult<never> {
  return {
    ok: false,
    error: providerError("authorization-required", "credential-api")
  };
}

function isValidCredential(value: string): boolean {
  return (
    value.length >= 16 &&
    value.length <= 8192 &&
    !/[\u0000-\u0020\u007f]/u.test(value)
  );
}

function isValidAuthorizedProbe(
  value: AuthorizedSessionProbe | undefined
): value is AuthorizedSessionProbe {
  return (
    value !== undefined &&
    value.statePath.trim().length > 0 &&
    value.allowlistedKey.trim().length > 0 &&
    value.authorizationId.trim().length > 0
  );
}
