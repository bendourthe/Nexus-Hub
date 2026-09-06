import { existsSync } from "node:fs";
import type { ProviderResult } from "../types";
import { providerError } from "./errors";

/**
 * The single key the adapter is permitted to ask for. The authorization boundary
 * in `cursor-usage-auth-probe.md` allows an allowlisted key name only, so this
 * list is the machine-readable form of that permit.
 */
export const ALLOWLISTED_SESSION_KEYS: readonly string[] = [
  "cursorAuth/accessToken"
];

export const DEFAULT_SESSION_KEY = "cursorAuth/accessToken";

/**
 * One key, bound as a parameter, with an explicit row cap. Written as a constant
 * so a review can see at a glance that no table or key enumeration is possible.
 */
const SESSION_QUERY = "SELECT value FROM ItemTable WHERE key = ? LIMIT 1";

const MIN_SESSION_LENGTH = 16;
const MAX_SESSION_LENGTH = 8192;

/**
 * Minimal structural view of `node:sqlite`. Declared locally rather than imported
 * from the runtime typings because Node documents that surface as experimental
 * and subject to change; only these three members are relied on.
 */
export interface StatementLike {
  get(...params: readonly unknown[]): unknown;
}

export interface DatabaseLike {
  prepare(sql: string): StatementLike;
  close(): void;
}

export interface SqliteModuleLike {
  DatabaseSync: new (
    path: string,
    options?: { readonly readOnly?: boolean }
  ) => DatabaseLike;
}

export type SqliteLoader = () => Promise<SqliteModuleLike | null>;

export type SessionUnavailableReason =
  | "sqlite-unavailable"
  | "state-path-missing"
  | "key-not-allowlisted";

export type SessionCapability =
  | { available: true }
  | { available: false; reason: SessionUnavailableReason };

export interface SessionAdapterDependencies {
  statePath: string;
  allowlistedKey?: string;
  loadSqlite?: SqliteLoader;
  pathExists?: (path: string) => boolean;
}

const NODE_SQLITE_SPECIFIER = "node:sqlite";

/**
 * Feature-detects the built-in SQLite module. Returns null rather than throwing
 * when the extension host predates it, so an older Cursor degrades to the
 * cache/manual posture instead of surfacing a module-resolution crash.
 */
export async function loadNodeSqlite(): Promise<SqliteModuleLike | null> {
  try {
    const loaded: unknown = await import(NODE_SQLITE_SPECIFIER);
    return asSqliteModule(loaded);
  } catch {
    return null;
  }
}

export class CursorSessionAdapter {
  private readonly statePath: string;
  private readonly allowlistedKey: string;
  private readonly loadSqlite: SqliteLoader;
  private readonly pathExists: (path: string) => boolean;

  public constructor(dependencies: SessionAdapterDependencies) {
    this.statePath = dependencies.statePath;
    this.allowlistedKey = dependencies.allowlistedKey ?? DEFAULT_SESSION_KEY;
    this.loadSqlite = dependencies.loadSqlite ?? loadNodeSqlite;
    this.pathExists = dependencies.pathExists ?? existsSync;
  }

  /**
   * Reports whether a live read could succeed at all, without opening anything.
   * This is what turns `liveTransportCapable` into a real check.
   */
  public async capability(): Promise<SessionCapability> {
    if (!ALLOWLISTED_SESSION_KEYS.includes(this.allowlistedKey)) {
      return { available: false, reason: "key-not-allowlisted" };
    }
    if (this.statePath.trim().length === 0 || !this.pathExists(this.statePath)) {
      return { available: false, reason: "state-path-missing" };
    }
    if ((await this.loadSqlite()) === null) {
      return { available: false, reason: "sqlite-unavailable" };
    }
    return { available: true };
  }

  /**
   * Reads the allowlisted key and hands the value to `operation` for the life of
   * one call. The value is never returned to the caller, stored, or logged; an
   * exception raised by `operation` is replaced with a fixed safe error so a
   * stack trace cannot carry the session value out.
   */
  public async withSession<T>(
    operation: (session: string) => Promise<ProviderResult<T>>
  ): Promise<ProviderResult<T>> {
    const capability = await this.capability();
    if (!capability.available) {
      return {
        ok: false,
        error: providerError(
          capability.reason === "key-not-allowlisted"
            ? "authorization-required"
            : "credential-adapter-unavailable",
          "credential-api"
        )
      };
    }

    const session = await this.readAllowlistedKey();
    if (!session.ok) {
      return session;
    }
    try {
      return await operation(session.value);
    } catch {
      return {
        ok: false,
        error: providerError("credential-adapter-unavailable", "credential-api")
      };
    }
  }

  private async readAllowlistedKey(): Promise<ProviderResult<string>> {
    const sqlite = await this.loadSqlite();
    if (sqlite === null) {
      return {
        ok: false,
        error: providerError("credential-adapter-unavailable", "credential-api")
      };
    }

    let database: DatabaseLike | undefined;
    let row: unknown;
    try {
      database = new sqlite.DatabaseSync(this.statePath, { readOnly: true });
      row = database.prepare(SESSION_QUERY).get(this.allowlistedKey);
    } catch {
      // Locked, encrypted, absent, or a schema without ItemTable. Fail closed
      // rather than widening the search.
      return {
        ok: false,
        error: providerError("credential-adapter-unavailable", "credential-api")
      };
    } finally {
      closeQuietly(database);
    }

    const session = extractSessionValue(row);
    if (session === null) {
      // The row is missing or malformed. Treated as a cleared or expired session
      // so the caller degrades instead of retrying.
      return {
        ok: false,
        error: providerError("session-expired", "credential-api")
      };
    }
    return { ok: true, value: session };
  }
}

function closeQuietly(database: DatabaseLike | undefined): void {
  if (database === undefined) {
    return;
  }
  try {
    database.close();
  } catch {
    // A close failure carries no usable information and must not mask the read
    // result or surface a path in an error message.
  }
}

export function extractSessionValue(row: unknown): string | null {
  if (typeof row !== "object" || row === null || Array.isArray(row)) {
    return null;
  }
  const text = decodeSessionText((row as Record<string, unknown>).value);
  if (text === null) {
    return null;
  }
  const trimmed = text.trim();
  // The same shape rule the SecretStorage path enforces: long enough to be a real
  // token, and free of control characters that would mark it as a binary blob
  // rather than a session value.
  return trimmed.length >= MIN_SESSION_LENGTH &&
    trimmed.length <= MAX_SESSION_LENGTH &&
    !hasControlCharacter(trimmed)
    ? trimmed
    : null;
}

function hasControlCharacter(value: string): boolean {
  for (const character of value) {
    const code = character.codePointAt(0) ?? 0;
    if (code <= 0x20 || code === 0x7f) {
      return true;
    }
  }
  return false;
}

function decodeSessionText(value: unknown): string | null {
  if (typeof value === "string") {
    return value;
  }
  if (value instanceof Uint8Array) {
    return Buffer.from(value).toString("utf8");
  }
  return null;
}

function asSqliteModule(loaded: unknown): SqliteModuleLike | null {
  const candidate = unwrapModule(loaded);
  if (candidate === null) {
    return null;
  }
  return typeof candidate.DatabaseSync === "function"
    ? (candidate as unknown as SqliteModuleLike)
    : null;
}

function unwrapModule(loaded: unknown): Record<string, unknown> | null {
  if (typeof loaded !== "object" || loaded === null) {
    return null;
  }
  const record = loaded as Record<string, unknown>;
  if (typeof record.DatabaseSync === "function") {
    return record;
  }
  const fallback = record.default;
  return typeof fallback === "object" && fallback !== null
    ? (fallback as Record<string, unknown>)
    : null;
}
