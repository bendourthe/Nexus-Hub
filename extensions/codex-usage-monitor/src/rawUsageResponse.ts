import * as fs from "fs";
import * as path from "path";

/**
 * The opt-in "Save Raw Usage Response" command writes one redacted copy of the
 * usage response so a maintainer can see which fields the vendor serves (for
 * example whether resets are reported) without sharing anything identifying.
 *
 * Kept: every key, every number and boolean, ISO dates, and short lowercase
 * enum-like words. Replaced with a placeholder: every other string, any value
 * under an identity-shaped key (ids, emails, names, accounts, organizations,
 * tokens), and any key that itself looks like an id or an email.
 */

const DATE = /^\d{4}-\d{2}-\d{2}([T ][0-9:.]+(Z|[+-]\d{2}:?\d{2})?)?$/;
const ENUM_WORD = /^[a-z][a-z_-]{0,31}$/;
const IDENTITY_KEY = /(^|_)(id|ids|email|name|login|user|account|org|organization|workspace|token|key|secret|url|uri)(_|$)/i;
const ID_SHAPED_KEY = /(^[0-9a-f-]{16,}$)|(\d{5,})|@/i;

export const RAW_RESPONSE_FILE = "raw-usage-response.json";

function placeholder(value: string): string {
  return `<redacted string, ${value.length} chars>`;
}

function redactScalar(value: unknown, identityKey: boolean): unknown {
  if (value === null || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return identityKey ? "<redacted number>" : value;
  }
  if (typeof value === "string") {
    if (!identityKey && (DATE.test(value) || ENUM_WORD.test(value))) {
      return value;
    }
    return placeholder(value);
  }
  return `<${typeof value}>`;
}

/** A redacted deep copy of a decoded JSON response. */
export function redactUsagePayload(value: unknown, identityKey = false): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => redactUsagePayload(item, identityKey));
  }
  if (value !== null && typeof value === "object") {
    const out: Record<string, unknown> = {};
    let index = 0;
    for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
      const safeKey = ID_SHAPED_KEY.test(key) ? `<key ${index}>` : key;
      out[safeKey] = redactUsagePayload(child, identityKey || IDENTITY_KEY.test(key));
      index += 1;
    }
    return out;
  }
  return redactScalar(value, identityKey);
}

/**
 * Write the redacted response to `<storageDir>/raw-usage-response.json`,
 * replacing any earlier copy, and return the file path. Nothing is sent anywhere.
 */
export function saveRawUsageResponse(storageDir: string, endpoint: string, raw: unknown, now = new Date()): string {
  fs.mkdirSync(storageDir, { recursive: true });
  const file = path.join(storageDir, RAW_RESPONSE_FILE);
  const document = {
    note: "Redacted copy of one usage response, saved by the Save Raw Usage Response command. Strings other than dates and short enum words are replaced.",
    endpoint,
    savedAt: now.toISOString(),
    response: redactUsagePayload(raw),
  };
  fs.writeFileSync(file, `${JSON.stringify(document, null, 2)}\n`, { encoding: "utf8", mode: 0o600 });
  return file;
}
