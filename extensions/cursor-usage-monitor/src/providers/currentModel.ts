import { loadNodeSqlite, type DatabaseLike, type SqliteLoader } from "./session";

/**
 * Cursor's settings record in its state database. The selected agent model sits
 * at `aiSettings.modelConfig.composer` inside it (verified on a local install,
 * 2026-10-19). This is the only key the model read asks for, and only the model
 * name is kept; the rest of the record is parsed and dropped.
 */
export const MODEL_SETTINGS_KEY =
  "src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl.persistentStorage.applicationUser";

const MODEL_QUERY = "SELECT value FROM ItemTable WHERE key = ? LIMIT 1";

/** A model id as Cursor writes it ("grok-4.7", "claude-4.5-sonnet", "default"). */
const MODEL_ID = /^[A-Za-z0-9][A-Za-z0-9._:\-]{0,63}$/;

/**
 * Read the agent model selected in Cursor, read-only. Returns undefined when the
 * database, the key, or a well-formed model name is absent; never throws, and
 * never returns anything from the record besides the model name.
 */
export async function readCursorSelectedModel(
  statePath: string,
  loadSqlite: SqliteLoader = loadNodeSqlite
): Promise<string | undefined> {
  if (statePath.trim().length === 0) {
    return undefined;
  }
  const sqlite = await loadSqlite();
  if (sqlite === null) {
    return undefined;
  }
  let database: DatabaseLike | undefined;
  let row: unknown;
  try {
    database = new sqlite.DatabaseSync(statePath, { readOnly: true });
    row = database.prepare(MODEL_QUERY).get(MODEL_SETTINGS_KEY);
  } catch {
    return undefined;
  } finally {
    try {
      database?.close();
    } catch {
      // Nothing useful to report; the read result stands.
    }
  }
  return extractSelectedModel(row);
}

/** The composer model name from a settings row, or undefined. Exported for tests. */
export function extractSelectedModel(row: unknown): string | undefined {
  const raw = record(row)?.value;
  const text = typeof raw === "string" ? raw : raw instanceof Uint8Array ? Buffer.from(raw).toString("utf8") : undefined;
  if (text === undefined) {
    return undefined;
  }
  let settings: unknown;
  try {
    settings = JSON.parse(text);
  } catch {
    return undefined;
  }
  const composer = record(record(record(record(settings)?.aiSettings)?.modelConfig)?.composer);
  const selected = Array.isArray(composer?.selectedModels) ? record(composer?.selectedModels[0])?.modelId : undefined;
  const name = typeof composer?.modelName === "string" ? composer.modelName : selected;
  return typeof name === "string" && MODEL_ID.test(name) ? name : undefined;
}

function record(value: unknown): Record<string, unknown> | undefined {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}
