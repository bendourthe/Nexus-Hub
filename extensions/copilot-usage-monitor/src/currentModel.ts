import * as path from "path";

/**
 * The one key the model read asks VS Code's state database for: the model picked
 * in the Chat view (value e.g. "copilot/claude-opus-5.5", verified on a local
 * install 2026-10-19). Approved 2026-10-19 as the single exception to decision
 * (1b)'s no-file-read rule; it carries no login, account, or repository data.
 */
export const CHAT_MODEL_KEY = "chat.currentLanguageModel.panel";

const MODEL_QUERY = "SELECT value FROM ItemTable WHERE key = ? LIMIT 1";

/** A picker value as VS Code writes it: an optional vendor prefix and a model id. */
const MODEL_VALUE = /^(?:[a-z0-9-]{1,32}\/)?[A-Za-z0-9][A-Za-z0-9._:\-]{0,63}$/;

interface Statement {
  get(...params: readonly unknown[]): unknown;
}
interface Database {
  prepare(sql: string): Statement;
  close(): void;
}
export interface SqliteModule {
  DatabaseSync: new (file: string, options?: { readonly readOnly?: boolean }) => Database;
}
export type SqliteLoader = () => Promise<SqliteModule | null>;

/** The built-in SQLite module, or null on a host that predates it. Never throws. */
export async function loadNodeSqlite(): Promise<SqliteModule | null> {
  try {
    const loaded = (await import("node:sqlite")) as Record<string, unknown>;
    const candidate = typeof loaded.DatabaseSync === "function" ? loaded : (loaded.default as Record<string, unknown> | undefined);
    return typeof candidate?.DatabaseSync === "function" ? (candidate as unknown as SqliteModule) : null;
  } catch {
    return null;
  }
}

/**
 * The editor's state database sits beside every extension's global storage
 * folder (`User/globalStorage/state.vscdb`), so it is found from the extension's
 * own storage URI rather than by searching the filesystem.
 */
export function stateDatabasePath(globalStorageFsPath: string): string {
  return path.join(path.dirname(globalStorageFsPath), "state.vscdb");
}

/**
 * Read the Chat view's selected model, read-only, from one named key. Returns
 * undefined when the database, the key, or a well-formed value is absent; never
 * throws. A leading "copilot/" vendor prefix is dropped for display.
 */
export async function readChatModel(statePath: string, loadSqlite: SqliteLoader = loadNodeSqlite): Promise<string | undefined> {
  const sqlite = await loadSqlite();
  if (sqlite === null) {
    return undefined;
  }
  let database: Database | undefined;
  let row: unknown;
  try {
    database = new sqlite.DatabaseSync(statePath, { readOnly: true });
    row = database.prepare(MODEL_QUERY).get(CHAT_MODEL_KEY);
  } catch {
    return undefined;
  } finally {
    try {
      database?.close();
    } catch {
      // Nothing useful to report; the read result stands.
    }
  }
  const raw = typeof row === "object" && row !== null ? (row as { value?: unknown }).value : undefined;
  const text = typeof raw === "string" ? raw : raw instanceof Uint8Array ? Buffer.from(raw).toString("utf8") : undefined;
  const value = text?.trim();
  return value !== undefined && MODEL_VALUE.test(value) ? value.replace(/^copilot\//, "") : undefined;
}
